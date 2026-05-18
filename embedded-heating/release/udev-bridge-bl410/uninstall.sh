#!/usr/bin/env bash
set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "请使用 root 运行: sudo $0"
  exit 1
fi

systemctl stop udev-bridge.service 2>/dev/null || true
systemctl disable udev-bridge.service 2>/dev/null || true
rm -f /etc/systemd/system/udev-bridge.service
systemctl daemon-reload

echo "已停止并移除 udev-bridge.service。"
echo "脚本文件仍在 /opt/udev-bridge/，可按需手动删除。"
