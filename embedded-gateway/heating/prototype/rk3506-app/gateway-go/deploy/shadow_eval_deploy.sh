#!/usr/bin/env bash
# 轨 B 阶段一 · 板上影子 eval 部署(Mac 侧执行)。
# eval 期把板子网关切到 app.py --source modbus --shadow-tap,并行起只读 Go 影子。
# app.py + 影子都从 /tmp(tmpfs)跑、--config 指生产配置——/userdata 零写入,还原最干净。
# 还原用 shadow_eval_stop.sh。设计与前提见 shadow_eval.md。
set -euo pipefail

BOARD="${BOARD:-root@192.168.1.10}"
BOARD_HTTP="${BOARD_HTTP:-http://192.168.1.10:8092}"
SRC="${SRC:-modbus}"                       # 现场用 modbus;无设备时 SRC=sim 仅冒烟
PROD_APP="${PROD_APP:-/userdata/rk3506-app}"  # 生产安装目录(install.sh APP)
PROD_CFG="$PROD_APP/app_config.json"          # 复用生产配置(不覆盖)
REMOTE="/tmp/gw-shadow"
HERE="$(cd "$(dirname "$0")" && pwd)"
APPDIR="$(cd "$HERE/../.." && pwd)"           # rk3506-app/

say(){ printf '\n==> %s\n' "$*"; }
die(){ printf '\n[停] %s\n' "$*" >&2; exit 1; }

# ---- 0 预检(不满足即停,不臆造)----
say "预检 $BOARD"
ssh -o ConnectTimeout=5 "$BOARD" 'true' 2>/dev/null || die "ssh 不通。先接板子 + 跑 scripts/setup_rk3506_macos_route.sh"
ssh "$BOARD" 'command -v python3 >/dev/null' || die "板上无 python3"
ssh "$BOARD" "test -f $PROD_CFG" || die "板上生产配置不在:$PROD_CFG"
[ -f "$HERE/gatewayc-shadow-arm" ] || die "缺 gatewayc-shadow-arm,先在 gateway-go/ 跑:GOOS=linux GOARCH=arm GOARM=7 go build -ldflags=\"-s -w\" -o deploy/gatewayc-shadow-arm ."
# 始终 MQTT 全功能:有系统 mosquitto 用它,否则带上纯 python mqtt_broker.py(零依赖,板载 python3 跑)。
MODE=mqtt
if ssh "$BOARD" 'command -v mosquitto >/dev/null || pgrep -x mosquitto >/dev/null'; then
  BROKER=system; echo "  预检通过:ssh / python3 / 系统 mosquitto / 生产配置 / 二进制"
else
  BROKER=python; [ -f "$APPDIR/mqtt_broker.py" ] || die "缺 mqtt_broker.py"
  echo "  预检通过:ssh / python3 / 生产配置 / 二进制;板上无 mosquitto → 带 python mqtt_broker.py(仍 MQTT 全功能)"
fi

# ---- 1 推文件到 tmpfs(不碰 /userdata)----
say "推文件到 $BOARD:$REMOTE(tmpfs)"
ssh "$BOARD" "mkdir -p $REMOTE/run"
scp "$APPDIR/app.py" "$HERE/gatewayc-shadow-arm" "$BOARD:$REMOTE/"
[ "$BROKER" = python ] && scp "$APPDIR/mqtt_broker.py" "$BOARD:$REMOTE/"
ssh "$BOARD" "chmod +x $REMOTE/gatewayc-shadow-arm"

# ---- 2 停生产 nexus(用真实 init 脚本),起 app.py + 影子 ----
say "停生产(S99zz-gateway stop)+(必要时起 python broker)+ 起 app.py --shadow-tap + Go 影子"
ssh "$BOARD" "SRC=$SRC REMOTE=$REMOTE PROD_CFG=$PROD_CFG BROKER=$BROKER bash -s" <<'REMOTE_EOF'
set -e
echo "$(date) BROKER=$BROKER" > "$REMOTE/run/EVAL_ACTIVE"
# 用板上自启脚本干净停生产网关(nexus + LCD);找不到则按名兜底。
if [ -x /etc/init.d/S99zz-gateway ]; then
  /etc/init.d/S99zz-gateway stop 2>/dev/null || true
else
  for pid in $(ps 2>/dev/null | grep -E 'nexus_server\.py' | grep -v grep | awk '{print $1}'); do
    kill "$pid" 2>/dev/null || true
  done
fi
sleep 1
cd "$REMOTE"
# 无系统 mosquitto 时起自带 python broker(零依赖),保证 MQTT 全功能。
if [ "$BROKER" = python ]; then
  nohup python3 mqtt_broker.py --host 127.0.0.1 --port 1883 >"$REMOTE/run/broker.log" 2>&1 &
  echo $! > "$REMOTE/run/broker.pid"
  sleep 1
fi
nohup "$REMOTE/gatewayc-shadow-arm" shadow --config "$PROD_CFG" >"$REMOTE/run/shadow.log" 2>&1 &
echo $! > "$REMOTE/run/shadow.pid"
sleep 1
# app.py:单一 RS485 主站 + 旁路 tap(--config 指生产配置)
nohup python3 app.py --source "$SRC" --shadow-tap --config "$PROD_CFG" >"$REMOTE/run/app.log" 2>&1 &
echo $! > "$REMOTE/run/app.pid"
sleep 2
echo "--- app.py 启动尾 ---"; tail -3 "$REMOTE/run/app.log" 2>/dev/null || true
echo "--- 影子启动尾 ---"; tail -4 "$REMOTE/run/shadow.log" 2>/dev/null || true
echo "--- 进程 ---"; ps 2>/dev/null | grep -E 'app\.py --source|gatewayc-shadow' | grep -v grep || true
REMOTE_EOF

say "部署完成(MQTT 全功能,broker=$BROKER)。板外起比对器观测(长期挂着):"
cat <<EOF

  cd "$APPDIR/gateway-go"
  python3 shadow_compare.py --broker ${BOARD#*@} --port 1883 \\
      --device rk3506-gw-01 --http $BOARD_HTTP \\
      --tol 0.5 --summary-every 60 --out shadow_diff.jsonl

  注:decision_diffs 是真正的判据(Go 与 Python 逻辑分歧);pending_go 多为 app.py
  自写 MQTT 客户端偶发漏收命令(已知,broker 无关,Go/paho 不漏)——见 shadow_eval.md。
  还原(eval 结束):$HERE/shadow_eval_stop.sh
EOF
