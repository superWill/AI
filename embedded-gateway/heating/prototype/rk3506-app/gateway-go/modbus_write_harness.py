#!/usr/bin/env python3
"""调用 app.py 真实 Controller→ModbusSource 写路径。仅 Linux/RK3506。

用法: modbus_write_harness.py <dev> <baud> <point_id> <value> <addr> <reg> <scale> [app.py]
"""

import importlib.util
import json
import os
import sys

app_path = (
    os.path.abspath(sys.argv[8])
    if len(sys.argv) > 8
    else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app.py")
)
spec = importlib.util.spec_from_file_location("rk3506_app", app_path)
app = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(app)

dev, baud, point_id, value, addr, reg, scale = sys.argv[1:8]
value = float(value)
addr, reg, baud = int(addr), int(reg), int(baud)
scale = float(scale)
source = app.ModbusSource(dev, baud, [], timeout=1.0)
control_map = {point_id: {"addr": addr, "reg": reg, "scale": scale}}
ok = source.write_setpoint(point_id, value, control_map)
register_value = int(round(value / scale))
body = app.struct.pack(">BBHH", addr, 0x06, reg, register_value & 0xFFFF)
print(json.dumps({
    "ok": ok,
    "point_id": point_id,
    "value": value,
    "addr": addr,
    "reg": reg,
    "register_value": register_value,
    "frame": (body + app.ModbusSource._crc(body)).hex(),
}, ensure_ascii=False))
