#!/usr/bin/env bash
set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "请使用 root 运行: sudo $0"
  exit 1
fi

rm -f /etc/nginx/sites-enabled/energy-hmi
rm -f /etc/nginx/sites-available/energy-hmi

systemctl disable --now energy-hmi-y31-temperature.service 2>/dev/null || true
rm -f /etc/systemd/system/energy-hmi-y31-temperature.service
systemctl daemon-reload

nginx -t
systemctl reload nginx

echo "已移除 energy-hmi Nginx 入口和 Y31 温度采集服务。页面文件仍保留在 /opt/energy-hmi，可按需手动删除。"
