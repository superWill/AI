#!/usr/bin/env python3
"""用 app.py 真实 ModbusSource 读串口(参照)。用法: <dev> <baud> <addr> <start> <count>"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import app
src = app.ModbusSource(sys.argv[1], int(sys.argv[2]), [], timeout=1.0)
regs, err = src.read_holding(int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
print(json.dumps({"regs": regs, "err": err or ""}))
