#!/bin/sh
# 守护:杀掉厂家 lv_demo,跑控制面板;崩了 2 秒后自动重启。放 /root/。
sleep 3
while true; do
  killall lv_demo 2>/dev/null
  /root/hmi_lvgl /dev/ttyS1 /root/panel_config.json >/root/hmilv.log 2>&1
  sleep 2
done
