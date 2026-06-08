#!/usr/bin/env python3
"""Modbus RTU 主站↔从站 演示(纯标准库,无需 pymodbus / 无需硬件)。

目的:在"串口能连通"之上,讲清 Modbus 多做了什么——
  从站地址 + 功能码 + 寄存器 + CRC + 请求/响应/异常码。

做法:用 os.openpty() 造一对"虚拟串口",从站跑在一头(线程),主站跑在另一头;
     数据真的过一条串口通道。把每一帧字节打印出来,看清"线上"长什么样。

真接现场时:把这套主站逻辑搬到 /dev/ttyS1(接 RS485 转换器 → 真表),
           build_read_holding()/parse 一行不用改,只把读写 fd 换成真串口。
"""
import os
import select
import struct
import termios
import threading
import time
import tty


def crc16(data: bytes) -> bytes:
    """Modbus RTU CRC16(多项式 0xA001,初值 0xFFFF),返回 2 字节(低字节在前)。"""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    return struct.pack("<H", crc)


def hx(b: bytes) -> str:
    return " ".join("%02X" % x for x in b)


# ---------- 主站:构造请求 / 解析响应 ----------

def build_read_holding(slave, start, count):
    """功能码 0x03 读保持寄存器。帧 = 地址 功能码 起始(2) 数量(2) CRC(2)。"""
    body = struct.pack(">BBHH", slave, 0x03, start, count)
    return body + crc16(body)


def parse_response(frame):
    if len(frame) < 5:
        raise ValueError("帧太短")
    if crc16(frame[:-2]) != frame[-2:]:
        raise ValueError("CRC 校验失败")
    slave, func = frame[0], frame[1]
    if func & 0x80:                       # 异常响应:功能码最高位置 1
        exc = frame[2]
        names = {1: "非法功能码", 2: "非法寄存器地址", 3: "非法数据值", 4: "从站故障"}
        raise ValueError("从站返回异常码 %d(%s)" % (exc, names.get(exc, "?")))
    nbyte = frame[2]
    regs = [struct.unpack(">H", frame[3 + i:5 + i])[0] for i in range(0, nbyte, 2)]
    return regs


# ---------- 从站:维护寄存器表 / 应答 ----------

class Slave:
    def __init__(self, addr):
        self.addr = addr
        # 模拟一个温湿度变送器:寄存器 0=温度×10, 1=湿度×10, 2=状态
        self.regs = {0: 235, 1: 486, 2: 1}      # 23.5℃, 48.6%RH, 正常

    def handle(self, frame):
        if crc16(frame[:-2]) != frame[-2:]:
            return None                          # CRC 错,真从站直接丢弃不回
        slave, func = frame[0], frame[1]
        if slave != self.addr:
            return None                          # 不是叫我,不回
        if func != 0x03:
            return self._exc(func, 1)            # 只支持 0x03,其余回"非法功能码"
        start, count = struct.unpack(">HH", frame[2:6])
        if any((start + i) not in self.regs for i in range(count)):
            return self._exc(func, 2)            # 寄存器不存在 → 非法地址
        vals = b"".join(struct.pack(">H", self.regs[start + i]) for i in range(count))
        body = struct.pack(">BBB", slave, func, len(vals)) + vals
        return body + crc16(body)

    def _exc(self, func, code):
        body = struct.pack(">BBB", self.addr, func | 0x80, code)
        return body + crc16(body)


def make_raw(fd):
    tty.setraw(fd)
    a = termios.tcgetattr(fd)
    a[1] = a[3] = 0                              # 关输出处理/回显/规范模式
    termios.tcsetattr(fd, termios.TCSANOW, a)


def slave_thread(fd, slave, stop):
    while not stop.is_set():
        r, _, _ = select.select([fd], [], [], 0.2)   # 等数据,没有就继续等(不退出)
        if not r:
            continue
        try:
            buf = os.read(fd, 256)
        except OSError:
            continue
        if not buf:
            continue
        time.sleep(0.02)                             # 等一帧收齐(RTU 靠帧间静默分帧)
        r2, _, _ = select.select([fd], [], [], 0)
        if r2:
            try:
                buf += os.read(fd, 256)
            except OSError:
                pass
        resp = slave.handle(buf)
        print("  [从站] 收到: %s" % hx(buf))
        if resp:
            print("  [从站] 应答: %s" % hx(resp))
            os.write(fd, resp)


def master_request(fd, req, desc, timeout=1.0):
    print("\n>>> 主站请求(%s)" % desc)
    print("  [主站] 发送: %s" % hx(req))
    os.write(fd, req)
    r, _, _ = select.select([fd], [], [], timeout)   # 带超时,没响应不死等
    resp = os.read(fd, 256) if r else b""
    print("  [主站] 收到: %s" % (hx(resp) if resp else "(超时,无响应)"))
    return resp


def main():
    m_fd, s_fd = os.openpty()                    # 一对"虚拟串口"
    make_raw(m_fd); make_raw(s_fd)               # 用 select 守,阻塞 fd 即可

    slave = Slave(addr=1)
    stop = threading.Event()
    t = threading.Thread(target=slave_thread, args=(s_fd, slave, stop), daemon=True)
    t.start()

    print("=" * 56)
    print("Modbus RTU 演示:主站(/dev/虚拟) ←→ 从站(地址1,模拟温湿度变送器)")
    print("帧格式: [从站地址][功能码][数据...][CRC低][CRC高]")
    print("=" * 56)

    # ① 正常读:读从站1 的寄存器 0~1(温度、湿度)
    resp = master_request(m_fd, build_read_holding(1, 0, 2), "读从站1 寄存器0~1")
    try:
        regs = parse_response(resp)
        print("  ✅ 解析: 温度=%.1f℃  湿度=%.1f%%RH" % (regs[0] / 10, regs[1] / 10))
    except ValueError as e:
        print("  ❌ %s" % e)

    # ② 读不存在的寄存器 → 看从站回"异常码"
    resp = master_request(m_fd, build_read_holding(1, 100, 1), "读不存在的寄存器100")
    try:
        parse_response(resp)
    except ValueError as e:
        print("  ⚠️ 预期内的异常: %s" % e)

    # ③ 发给地址2(没这个从站)→ 无人应答(超时)
    resp = master_request(m_fd, build_read_holding(2, 0, 1), "读从站2(不存在)")
    print("  ⚠️ %s" % ("无响应(从站不存在,真总线上就是超时)" if not resp else "收到:" + hx(resp)))

    stop.set()
    print("\n演示结束。换到真串口只需把 os.read/os.write 的 fd 指向 /dev/ttyS1。")


if __name__ == "__main__":
    main()
