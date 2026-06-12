#!/bin/sh
# GPIO 输出示例:把某条 gpio 线翻转 10 次(接 LED/继电器模块看效果)。板子上 root 跑。
# 用法: ./gpio_blink.sh gpiochip0 17      (先用 gpioinfo 找到可用的 chip 和 line)
CHIP=${1:-gpiochip0}; LINE=${2:-17}
if command -v gpioset >/dev/null; then
  for i in $(seq 1 10); do gpioset $CHIP $LINE=1; sleep 0.5; gpioset $CHIP $LINE=0; sleep 0.5; echo "blink $i"; done
else   # 退回 sysfs
  N=$LINE
  echo $N > /sys/class/gpio/export 2>/dev/null
  echo out > /sys/class/gpio/gpio$N/direction
  for i in $(seq 1 10); do echo 1 > /sys/class/gpio/gpio$N/value; sleep 0.5; echo 0 > /sys/class/gpio/gpio$N/value; sleep 0.5; echo "blink $i"; done
  echo $N > /sys/class/gpio/unexport
fi
