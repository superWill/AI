#!/usr/bin/env bash
set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "请使用 root 运行: sudo $0"
  exit 1
fi

RELEASE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="/opt/energy-hmi-prototype"

mkdir -p "${APP_ROOT}"

if [ -d "${APP_ROOT}/html" ]; then
  BACKUP_NAME="energy_hmi_prototype_backup_$(date +%Y%m%d_%H%M%S)"
  tar -czf "/opt/${BACKUP_NAME}.tar.gz" -C "${APP_ROOT}" html 2>/dev/null || true
fi

rm -rf "${APP_ROOT}/html"
mkdir -p "${APP_ROOT}/html"
cp -r "${RELEASE_ROOT}/html/." "${APP_ROOT}/html/"

cp "${RELEASE_ROOT}/energy-hmi-prototype.nginx.conf" /etc/nginx/sites-available/energy-hmi-prototype
ln -sf /etc/nginx/sites-available/energy-hmi-prototype /etc/nginx/sites-enabled/energy-hmi-prototype

nginx -t
systemctl enable nginx
systemctl reload nginx

echo "安装完成。验证命令："
echo "  curl -I http://127.0.0.1:8094/"
echo "  浏览器访问：http://设备IP:8094/"
echo ""
echo "注意：本 prototype 与 release 版（8092）并存，不影响 /opt/energy-hmi。"
