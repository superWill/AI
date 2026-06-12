#!/bin/sh
# 采集层探针:看板子有哪些 GPIO / ADC / I2C / SPI 能玩。板子上 root 跑。
echo "=== GPIO 控制器 ==="; ls /dev/gpiochip* 2>/dev/null; ls /sys/class/gpio 2>/dev/null && echo "(有 sysfs gpio)"
echo "=== libgpiod 工具 ==="; for t in gpiodetect gpioinfo gpioset gpioget; do command -v $t >/dev/null 2>&1 && echo "+ $t" || echo "- $t"; done
command -v gpiodetect >/dev/null && gpiodetect
echo "=== ADC(IIO)==="
for d in /sys/bus/iio/devices/iio:device*; do [ -e "$d" ] || continue
  echo "  $d  name=$(cat $d/name 2>/dev/null)"
  ls $d/in_voltage*_raw 2>/dev/null | sed 's/^/    通道: /'
  cat $d/in_voltage_scale 2>/dev/null | sed 's/^/    scale(mV\/LSB): /'
done
echo "=== I2C / SPI ==="; ls /dev/i2c-* /dev/spidev* 2>/dev/null || echo "(无)"
command -v i2cdetect >/dev/null && for b in /dev/i2c-*; do echo "--- 扫 $b ---"; i2cdetect -y ${b##*-} 2>/dev/null; done
echo "=== 1-Wire ==="; ls /sys/bus/w1/devices/ 2>/dev/null || echo "(无 w1)"
