#!/bin/sh
# 守护:杀掉厂家 lv_demo + 任何残留面板实例(防多实例抢 DRM 黑屏),跑控制面板;崩了自动重启。放 /root/。
sleep 3
while true; do
  killall lv_demo hmi_lvgl 2>/dev/null     # 先清干净,保证全屏只有一个 DRM 客户端
  sleep 1
  /root/hmi_lvgl /dev/ttyS1 /root/panel_config.json >/root/hmilv.log 2>&1
  sleep 2
done
