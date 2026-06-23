#!/usr/bin/env python3
"""pty 上的极简 Modbus RTU 从站(验证串口 _txn 用):master 当从站,slave 路径给主站开。
用法: pty_modbus_slave.py [config.json]   config: {"regs":{"1":[..]},"silent":[addr,...]}"""
import os, sys, struct, tty, select, json
def crc16(d):
    c=0xFFFF
    for b in d:
        c^=b
        for _ in range(8): c=(c>>1)^0xA001 if c&1 else c>>1
    return struct.pack("<H", c)
REGS={1:[310,451,327,600,12], 2:[999]}; SILENT=set()
if len(sys.argv)>1:
    cfg=json.load(open(sys.argv[1])); REGS={int(k):v for k,v in cfg.get("regs",{1:[310,451,327,600,12]}).items()}; SILENT=set(cfg.get("silent",[]))
mfd,sfd=os.openpty(); tty.setraw(mfd); tty.setraw(sfd)
open("/tmp/pty_slave_path","w").write(os.ttyname(sfd))
sys.stderr.write("slave="+os.ttyname(sfd)+"\n"); sys.stderr.flush()
buf=b""
while True:
    r,_,_=select.select([mfd],[],[],60)
    if not r: break
    buf+=os.read(mfd,256)
    while len(buf)>=8:
        f=buf[:8]; buf=buf[8:]
        if crc16(f[:-2])!=f[-2:]: continue
        addr,fc,start,count=struct.unpack(">BBHH",f[:6])
        if addr in SILENT: continue
        if fc==0x03 and addr in REGS:
            vals=REGS[addr][start:start+count]
            body=struct.pack(">BBB",addr,0x03,count*2)+b"".join(struct.pack(">H",v&0xFFFF) for v in vals)
            os.write(mfd, body+crc16(body))
