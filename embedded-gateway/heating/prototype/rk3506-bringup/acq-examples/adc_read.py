#!/usr/bin/env python3
"""读 ADC 模拟量(IIO 子系统,纯标准库)。板子上 root 跑。
原始值 → 电压(mV) → 物理量(两点标定)。
用法:  python3 adc_read.py [通道号] [iio设备号]
  例:  python3 adc_read.py 3        # 读 in_voltage3_raw
"""
import sys, time, glob, os

ch = sys.argv[1] if len(sys.argv) > 1 else "3"
dev = sys.argv[2] if len(sys.argv) > 2 else None
base = ("/sys/bus/iio/devices/iio:device%s" % dev) if dev else \
       (sorted(glob.glob("/sys/bus/iio/devices/iio:device*")) or ["/sys/bus/iio/devices/iio:device0"])[0]

raw_f = "%s/in_voltage%s_raw" % (base, ch)
scale_f = "%s/in_voltage_scale" % base
if not os.path.exists(raw_f):
    print("找不到 %s —— 先跑 io_probe.sh 看有哪些通道" % raw_f); sys.exit(1)
scale = float(open(scale_f).read()) if os.path.exists(scale_f) else 1.0   # mV/LSB

# 两点标定示例(按你的传感器改):raw_lo→phys_lo, raw_hi→phys_hi
CAL = {"raw_lo": 0, "phys_lo": 0.0, "raw_hi": 4095, "phys_hi": 100.0}  # 占位:0~满量程→0~100
def to_phys(raw):
    k = (CAL["phys_hi"] - CAL["phys_lo"]) / (CAL["raw_hi"] - CAL["raw_lo"])
    return CAL["phys_lo"] + k * (raw - CAL["raw_lo"])

print("读 %s  (scale=%.4f mV/LSB)。Ctrl-C 退出。" % (raw_f, scale))
try:
    while True:
        raw = int(open(raw_f).read())
        mv = raw * scale
        print("raw=%5d   电压=%7.1f mV   物理量(标定后)=%.2f" % (raw, mv, to_phys(raw)))
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
