#!/usr/bin/env python3
"""串口自环回测（纯标准库，无需 pyserial）。

原理：把某个串口的 TXD 和 RXD 物理短接后，自己发的字节会原样回到自己的 RX。
本脚本对每个串口：配成 raw 8N1 + 指定波特率 → 发一段唯一标记 → 限时读回 → 比对。

用法：
    python3 loopback_test.py                  # 默认轮测 ttyS1..ttyS4 @115200
    python3 loopback_test.py /dev/ttyS3       # 只测 ttyS3
    python3 loopback_test.py /dev/ttyUSB0 9600  # 指定口和波特率

判读：
    ✅自环通过  = 这个口 TXD↔RXD 短接着，硬件+驱动都通
    ❌无回读     = 没短接(正常，没跳线的口都这样) 或 这个口坏/没引出
    ⚠️回读不一致 = 通是通了，但字节错了 → 波特率不对 / 干扰 / 接触不良
"""
import os, sys, time, termios, select

BAUD = {2400: termios.B2400, 4800: termios.B4800, 9600: termios.B9600,
        19200: termios.B19200, 38400: termios.B38400, 57600: termios.B57600,
        115200: termios.B115200}


def open_raw(dev, baud):
    fd = os.open(dev, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    a = termios.tcgetattr(fd)              # [iflag,oflag,cflag,lflag,ispeed,ospeed,cc]
    a[0] = 0                               # 关掉所有输入处理（不要 CR/LF 转换等）
    a[1] = 0                               # 关掉所有输出处理
    a[2] = termios.CS8 | termios.CLOCAL | termios.CREAD   # 8 数据位, 忽略调制解调线, 允许收
    a[3] = 0                               # 非规范模式, 无回显
    a[4] = a[5] = BAUD[baud]               # 收发波特率
    a[6][termios.VMIN] = 0
    a[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, a)
    termios.tcflush(fd, termios.TCIOFLUSH)  # 清掉残留
    return fd


def test(dev, baud=115200, timeout=1.0):
    try:
        fd = open_raw(dev, baud)
    except (OSError, KeyError) as e:
        return f"{dev:14} @ {baud}: 打开失败 {e}"
    msg = b"LOOPBACK-%05d\n" % (int(time.time() * 1000) % 100000)
    termios.tcflush(fd, termios.TCIOFLUSH)
    os.write(fd, msg)
    got, deadline = b"", time.time() + timeout
    while time.time() < deadline and len(got) < len(msg):
        r, _, _ = select.select([fd], [], [], max(0, deadline - time.time()))
        if r:
            got += os.read(fd, 256)
    os.close(fd)
    if got.strip() == msg.strip():
        st = "✅自环通过"
    elif not got:
        st = "❌无回读(超时)"
    else:
        st = "⚠️回读不一致"
    return f"{dev:14} @ {baud}: {st}  发={msg.strip()!r} 收={got.strip()!r}"


if __name__ == "__main__":
    args = sys.argv[1:]
    baud = 115200
    if args and args[-1].isdigit():
        baud = int(args.pop())
    devs = args or ["/dev/ttyS1", "/dev/ttyS2", "/dev/ttyS3", "/dev/ttyS4"]
    print(f"=== 串口自环测试 @ {baud} 8N1 ===")
    for d in devs:
        print(test(d, baud))
