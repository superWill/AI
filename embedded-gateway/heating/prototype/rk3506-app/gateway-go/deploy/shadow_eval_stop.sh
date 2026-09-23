#!/usr/bin/env bash
# 轨 B 阶段一 · 板上影子 eval 还原(Mac 侧执行)。
# 停 Go 影子 + 停 app.py + 用真实 init 脚本重启生产 nexus_server。
# 零生产副作用:影子不在控制回路;/userdata 全程未被写。
set -euo pipefail

BOARD="${BOARD:-root@192.168.1.10}"
REMOTE="/tmp/gw-shadow"

say(){ printf '\n==> %s\n' "$*"; }

ssh -o ConnectTimeout=5 "$BOARD" 'true' 2>/dev/null || { echo "[停] ssh 不通,无法还原" >&2; exit 1; }

say "停 Go 影子 + app.py"
ssh "$BOARD" "REMOTE=$REMOTE bash -s" <<'REMOTE_EOF'
set -e
for f in shadow app broker; do
  if [ -f "$REMOTE/run/$f.pid" ]; then
    kill "$(cat "$REMOTE/run/$f.pid")" 2>/dev/null || true
    rm -f "$REMOTE/run/$f.pid"
  fi
done
for pid in $(ps 2>/dev/null | grep -E 'gatewayc-shadow|app\.py --source|mqtt_broker\.py' | grep -v grep | awk '{print $1}'); do
  kill "$pid" 2>/dev/null || true
done
rm -f "$REMOTE/run/EVAL_ACTIVE"
echo "影子 + app.py 已停"
REMOTE_EOF

say "重启生产 nexus_server(板上自启脚本 S99zz-gateway)"
ssh "$BOARD" 'bash -s' <<'REMOTE_EOF'
set -e
if [ -x /etc/init.d/S99zz-gateway ]; then
  /etc/init.d/S99zz-gateway start 2>/dev/null || /etc/init.d/S99zz-gateway restart 2>/dev/null || true
  echo "已用 S99zz-gateway 拉起生产"
elif [ -f /userdata/rk3506-app/nexus_server.py ]; then
  cd /userdata/rk3506-app
  nohup python3 nexus_server.py --config app_config.json >/tmp/nexus.log 2>&1 &
  echo "已手动拉起 nexus_server(/userdata/rk3506-app)"
else
  echo "[注意] 未找到 S99zz-gateway 或 nexus_server.py——请手动还原生产网关" >&2
fi
sleep 2
ps 2>/dev/null | grep -E 'nexus_server' | grep -v grep || echo "[注意] 未见 nexus_server 进程,请人工确认"
REMOTE_EOF

say "还原完成。确认板子 LCD/edge-os UI 恢复后,eval 收尾。"
