#!/usr/bin/env bash
set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "请使用 root 运行: sudo $0"
  exit 1
fi

RELEASE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="/opt/udev-bridge"

# 1. 部署脚本
mkdir -p "${APP_ROOT}"
cp "${RELEASE_ROOT}/udev_bridge.py" "${APP_ROOT}/udev_bridge.py"
chmod +x "${APP_ROOT}/udev_bridge.py"

# 2. 安装 systemd 单元
cp "${RELEASE_ROOT}/udev-bridge.service" /etc/systemd/system/udev-bridge.service
systemctl daemon-reload
systemctl enable udev-bridge.service
systemctl restart udev-bridge.service

# 3. 给点时间起服务
sleep 1

# 4. 自检
echo
echo "==== 自检 ===="
systemctl status udev-bridge.service --no-pager -l | head -10 || true
echo
curl -sI http://127.0.0.1:8765/health | head -3 || true
echo
echo "完成。"
echo "  健康检查: curl http://127.0.0.1:8765/health"
echo "  事件流:   curl -N http://127.0.0.1:8765/events"
echo "  实时日志: journalctl -u udev-bridge -f"
