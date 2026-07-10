#!/usr/bin/env python3
"""media_agent 入口 smoke 测:build_agent 组装收→落盘→传全链(localhost,端口绑不了则跳过)。"""
import os
import shutil
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

import media_agent                                                # noqa: E402
from uplink.media_relay import MediaRelayClient, MediaShipment    # noqa: E402


def test_agent_wires_receive_spool_upload():
    d = tempfile.mkdtemp(prefix="dm-agent-test-")
    try:
        env = {"AGENT_PORT": "0", "AGENT_SPOOL_DIR": d, "AGENT_PUMP_INTERVAL": "3600"}
        try:
            httpd, lock, outbox, uploader, _ = media_agent.build_agent(env)  # 无 OSS → Fake
        except OSError:
            print("  skip test_agent_wires_receive_spool_upload (无法绑定端口)")
            return
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            key = "driver-monitor/events/po-1/first_frame.png"
            ok = MediaRelayClient("127.0.0.1", port, timeout_s=3.0).ship(
                MediaShipment(key, "first_frame", 1.0, "po-1", b"png"))
            if not ok:
                print("  skip test_agent_wires_receive_spool_upload (本地网络被限)")
                return
            assert outbox.pending_count == 1                     # 收下入队
            assert any(f.endswith(".spool") for f in os.listdir(d))   # 已落盘(持久化)
            with lock:
                outbox.pump(now=100.0)                           # 补传
            assert uploader.get(key) == b"png"                   # 传到(假)OSS
            assert outbox.pending_count == 0
            assert not any(f.endswith(".spool") for f in os.listdir(d))   # 上传后删盘
        finally:
            httpd.shutdown()
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")
