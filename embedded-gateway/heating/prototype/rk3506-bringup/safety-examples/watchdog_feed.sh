#!/bin/sh
# 硬件看门狗喂狗:周期性写 /dev/watchdog;本进程一旦卡死/被杀(停止喂狗)→ 硬件自动复位整机。
# 放 /root/ 并由 init 在主程序里调用;喂狗点应靠近"主循环健康"处,别单独线程喂(那样主逻辑死了它还在喂=白搭)。
WDT=/dev/watchdog
[ -e "$WDT" ] || { echo "无 $WDT —— 内核没开看门狗,先确认设备树/驱动"; exit 1; }
exec 3>"$WDT"                         # 打开即"上膛";保持 fd 不关
trap 'echo V >&3 2>/dev/null; exec 3>&-; exit 0' INT TERM   # 干净退出:写 V 关看门狗(不复位)
echo "喂狗开始(每 5s)。超时未喂将硬复位。Ctrl-C 干净停止。"
while true; do
  echo -n "." >&3                    # 喂狗
  sleep 5                            # 间隔必须 < 看门狗超时;先 'cat /sys/class/watchdog/watchdog0/timeout' 确认
done
