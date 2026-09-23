#!/usr/bin/env python3
"""RK3506 板上 L3：PTY 从站对拍 Python/Go 真实 Modbus 写寄存器路径。

用法:
  python3 controller_l3_board.py ./gatewayc-arm ../app.py

只创建临时 PTY；不会打开 /dev/ttyS*，不会触碰现场设备。
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATEWAYC = Path(sys.argv[1]).resolve()
APP = Path(sys.argv[2]).resolve()
POINT_ID = "valve_open_sp"
VALUE = "12.25"
ADDR = "3"
REG = "120"
SCALE = "0.1"


def wait_for_path(path: Path) -> str:
    for _ in range(100):
        if path.exists() and path.read_text().strip():
            return path.read_text().strip()
        time.sleep(0.02)
    raise RuntimeError("PTY slave path 未生成")


def run_json(command):
    output = subprocess.check_output(command, text=True)
    return json.loads(output)


def main() -> None:
    if not GATEWAYC.is_file() or not APP.is_file():
        raise SystemExit("gatewayc 或 app.py 不存在")
    with tempfile.TemporaryDirectory(prefix="controller-l3-") as temp:
        temp_dir = Path(temp)
        path_file = Path("/tmp/pty_slave_path")
        if path_file.exists():
            path_file.unlink()
        write_log = temp_dir / "writes.jsonl"
        config = temp_dir / "slave.json"
        config.write_text(json.dumps({
            "regs": {ADDR: [0] * 121},
            "write_log": str(write_log),
        }))
        slave = subprocess.Popen(
            [sys.executable, str(HERE / "pty_modbus_slave.py"), str(config)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            dev = wait_for_path(path_file)
            python_result = run_json([
                sys.executable,
                str(HERE / "modbus_write_harness.py"),
                dev, "9600", POINT_ID, VALUE, ADDR, REG, SCALE, str(APP),
            ])
            go_result = run_json([
                str(GATEWAYC), "modbuswrite",
                dev, "9600", POINT_ID, VALUE, ADDR, REG, SCALE,
            ])
        finally:
            slave.terminate()
            try:
                slave.wait(timeout=2)
            except subprocess.TimeoutExpired:
                slave.kill()
                slave.wait()

        writes = [
            json.loads(line)
            for line in write_log.read_text().splitlines()
            if line.strip()
        ]
        expected_frame = "03060078007a89d2"
        checks = {
            "python_go_result_equal": python_result == go_result,
            "both_writes_seen": len(writes) == 2,
            "register_mapping_equal": all(
                item.get("addr") == 3
                and item.get("reg") == 120
                and item.get("value") == 122
                for item in writes
            ),
            "wire_frame_equal": all(
                item.get("frame") == expected_frame for item in writes
            ),
            "write_ack_success": python_result.get("ok") and go_result.get("ok"),
        }
        print(json.dumps({
            "python": python_result,
            "go": go_result,
            "wire_writes": writes,
            "checks": checks,
        }, ensure_ascii=False, indent=2))
        if not all(checks.values()):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
