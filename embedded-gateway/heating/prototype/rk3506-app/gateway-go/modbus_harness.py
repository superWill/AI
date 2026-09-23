#!/usr/bin/env python3
"""ModbusSource 协议核心对拍 harness：调用 app.py 真实代码(stub _txn)。
  crc <hex> | req <addr> <start> <count> | write <addr> <reg> <value> | parse <resp_hex>"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import app
M = app.ModbusSource

def new():
    s = M.__new__(M); s.timeout = 1.0; return s

a = sys.argv[1]
if a == "crc":
    print(M._crc(bytes.fromhex(sys.argv[2])).hex())
elif a == "req":
    s = new(); cap = {}
    s._txn = lambda body, t: (cap.__setitem__('b', body + M._crc(body)), b"")[1]
    s.read_holding(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    print(cap['b'].hex())
elif a == "write":
    s = new(); cap = {}
    s._txn = lambda body, t: (cap.__setitem__('b', body + M._crc(body)), b"")[1]
    s.write_register(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    print(cap['b'].hex())
elif a == "parse":
    s = new(); resp = bytes.fromhex(sys.argv[2])
    s._txn = lambda body, t: resp
    regs, err = s.read_holding(0, 0, 0)
    print(json.dumps({"regs": regs, "err": err or ""}))
