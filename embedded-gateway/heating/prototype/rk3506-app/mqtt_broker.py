#!/usr/bin/env python3
"""纯标准库 MQTT 3.1.1 mini broker —— 给 buildroot 板子(无包管理器/无 mosquitto)用。

够用范围:多客户端并发、CONNECT/CONNACK、SUBSCRIBE/SUBACK(含 + / # 通配)、
PUBLISH 路由(上行 QoS1 回 PUBACK;下行一律按 QoS0 转发)、PINGREQ/PINGRESP、
UNSUBSCRIBE、DISCONNECT。**仅供本机/内网开发演示(轨B影子 eval),不做鉴权/TLS/持久会话。**

  python3 mqtt_broker.py [--host 127.0.0.1] [--port 1883] [-v]

设计取舍:下行统一 QoS0(不追发包 id、不重传),订阅方即便订 QoS1 也按服务端可降级处理;
publisher 的 QoS1 PUBLISH 回 PUBACK 让其确认。足够 paho / app.py 自写客户端互通。
"""
import argparse, socket, struct, threading, sys

VERBOSE = False


def log(*a):
    if VERBOSE:
        print("[broker]", *a, flush=True)


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def read_remaining_length(sock):
    """MQTT 变长剩余长度(最多 4 字节)。返回 int 或 None(连接断)。"""
    mult, value = 1, 0
    for _ in range(4):
        b = recv_exact(sock, 1)
        if b is None:
            return None
        byte = b[0]
        value += (byte & 0x7F) * mult
        if not (byte & 0x80):
            return value
        mult *= 128
    return value


def encode_remaining_length(n):
    out = b""
    while True:
        byte = n % 128
        n //= 128
        if n > 0:
            byte |= 0x80
        out += bytes([byte])
        if n == 0:
            return out


def topic_matches(filt, topic):
    """MQTT 通配:+ 匹配一层,# 匹配其后所有层。"""
    f, t = filt.split("/"), topic.split("/")
    i = 0
    for i, seg in enumerate(f):
        if seg == "#":
            return True
        if i >= len(t):
            return False
        if seg == "+":
            continue
        if seg != t[i]:
            return False
    return len(f) == len(t)


class Client:
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        self.send_lock = threading.Lock()
        self.cid = "?"

    def send(self, data):
        with self.send_lock:
            try:
                self.sock.sendall(data)
            except OSError:
                pass


class Broker:
    def __init__(self):
        self.subs = {}            # topic_filter -> set(Client)
        self.clients = {}         # client_id -> Client(同 cid 只留最新,合 MQTT 规范)
        self.lock = threading.Lock()

    def register(self, client):
        """MQTT 规范:同 client-id 新连接踢掉旧连接(否则懒连接竞态会留多条连接抢字节)。"""
        old = None
        with self.lock:
            prev = self.clients.get(client.cid)
            if prev is not None and prev is not client:
                old = prev
                for s in self.subs.values():
                    s.discard(prev)
            self.clients[client.cid] = client
        if old is not None:
            try:
                old.sock.close()   # 让旧连接的 recv 返回→其 handler 自行收尾
            except OSError:
                pass

    def subscribe(self, client, filt):
        with self.lock:
            self.subs.setdefault(filt, set()).add(client)

    def unsubscribe(self, client, filt):
        with self.lock:
            if filt in self.subs:
                self.subs[filt].discard(client)

    def drop(self, client):
        with self.lock:
            for s in self.subs.values():
                s.discard(client)
            if self.clients.get(client.cid) is client:
                del self.clients[client.cid]

    def route(self, topic, payload):
        # QoS0 下行:固定头 0x30,变长 = topic_len(2)+topic+payload
        var = struct.pack(">H", len(topic)) + topic.encode() + payload
        pkt = b"\x30" + encode_remaining_length(len(var)) + var
        with self.lock:
            targets = [c for filt, cs in self.subs.items()
                       if topic_matches(filt, topic) for c in cs]
        for c in set(targets):
            c.send(pkt)
        log("PUBLISH", topic, "->", len(set(targets)), "subs")

    def handle(self, sock, addr):
        client = Client(sock, addr)
        try:
            while True:
                hdr = recv_exact(sock, 1)
                if hdr is None:
                    break
                ptype = hdr[0] & 0xF0
                flags = hdr[0] & 0x0F
                rl = read_remaining_length(sock)
                if rl is None:
                    break
                body = recv_exact(sock, rl) if rl else b""
                if body is None:
                    break

                if ptype == 0x10:                       # CONNECT
                    # 跳过协议名/级别/标志/keepalive,取 client id 仅作日志。
                    try:
                        pnl = struct.unpack(">H", body[:2])[0]
                        off = 2 + pnl + 1 + 1 + 2        # name + level + flags + keepalive
                        cidl = struct.unpack(">H", body[off:off + 2])[0]
                        client.cid = body[off + 2:off + 2 + cidl].decode("utf-8", "replace")
                    except Exception:
                        pass
                    self.register(client)                # 同 cid 踢旧连接
                    client.send(b"\x20\x02\x00\x00")     # CONNACK 接受
                    log("CONNECT", client.cid, addr)

                elif ptype == 0x30:                      # PUBLISH
                    qos = (flags >> 1) & 0x03
                    tl = struct.unpack(">H", body[:2])[0]
                    topic = body[2:2 + tl].decode("utf-8", "replace")
                    rest = body[2 + tl:]
                    if qos > 0:
                        pid = rest[:2]
                        payload = rest[2:]
                        client.send(b"\x40\x02" + pid)   # PUBACK
                    else:
                        payload = rest
                    self.route(topic, payload)

                elif ptype == 0x80:                      # SUBSCRIBE
                    pid = body[:2]
                    i, granted = 2, b""
                    while i < len(body):
                        tl = struct.unpack(">H", body[i:i + 2])[0]
                        filt = body[i + 2:i + 2 + tl].decode("utf-8", "replace")
                        i += 2 + tl + 1                  # +1 requested qos
                        self.subscribe(client, filt)
                        granted += b"\x00"               # 授 QoS0
                        log("SUBSCRIBE", client.cid, filt)
                    client.send(b"\x90" + encode_remaining_length(2 + len(granted)) + pid + granted)

                elif ptype == 0xA0:                      # UNSUBSCRIBE
                    pid = body[:2]
                    i = 2
                    while i < len(body):
                        tl = struct.unpack(">H", body[i:i + 2])[0]
                        filt = body[i + 2:i + 2 + tl].decode("utf-8", "replace")
                        i += 2 + tl
                        self.unsubscribe(client, filt)
                    client.send(b"\xb0\x02" + pid)       # UNSUBACK

                elif ptype == 0xC0:                      # PINGREQ
                    client.send(b"\xd0\x00")             # PINGRESP

                elif ptype == 0xE0:                      # DISCONNECT
                    break
                # PUBACK(0x40)等下行确认:忽略(下行按 QoS0,无需追踪)
        except OSError:
            pass
        finally:
            self.drop(client)
            try:
                sock.close()
            except OSError:
                pass
            log("断开", client.cid, addr)


def main():
    global VERBOSE
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    VERBOSE = a.v
    br = Broker()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((a.host, a.port))
    srv.listen(64)
    print("[broker] MQTT 3.1.1 mini broker 监听 %s:%d(纯标准库)" % (a.host, a.port), flush=True)
    try:
        while True:
            sock, addr = srv.accept()
            threading.Thread(target=br.handle, args=(sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[broker] 退出")


if __name__ == "__main__":
    main()
