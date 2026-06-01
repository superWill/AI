#!/usr/bin/env bash
set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "请使用 root 运行: sudo $0"
  exit 1
fi

rm -f /etc/nginx/sites-enabled/energy-hmi-prototype
rm -f /etc/nginx/sites-available/energy-hmi-prototype

nginx -t
systemctl reload nginx

echo "已移除 energy-hmi-prototype Nginx 入口（端口 8094）。"
echo "页面文件仍保留在 /opt/energy-hmi-prototype，可按需手动删除。"
echo "Release 版（8092）不受影响。"
