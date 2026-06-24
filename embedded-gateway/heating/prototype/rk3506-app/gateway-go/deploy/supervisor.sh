#!/bin/sh
# busybox 进程监督 —— 生产拓扑(gatewayc 核心 + nexus 客户端)崩溃自愈 + 启动健康门。
# 替代裸 nohup「退出无人管」。LCD 由 step5 接入,本脚本只管 gatewayc + nexus。
#
# 用法(env 可覆盖):
#   GATEWAYC=/opt/gw/gatewayc NEXUS=/opt/gw/nexus_server.py BUILD=/opt/gw/build \
#   FALLBACK_CFG=/opt/gw/app_config.json CORE=http://127.0.0.1:8091 PORT=8091 \
#   RUN=/tmp/gwsup ./supervisor.sh
set -u

GATEWAYC="${GATEWAYC:-./gatewayc}"
NEXUS="${NEXUS:-./nexus_server.py}"
PY="${PY:-$(command -v python3 || echo /usr/bin/python3)}"
BUILD="${BUILD:-./build}"
FALLBACK_CFG="${FALLBACK_CFG:-./app_config.json}"
CORE="${CORE:-http://127.0.0.1:8091}"
PORT="${PORT:-8091}"
NEXUS_PORT="${NEXUS_PORT:-8092}"
DIST="${DIST:-./nexus-dist}"
RUN="${RUN:-/tmp/gwsup}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-30}"
mkdir -p "$RUN"

log() { echo "$(date '+%H:%M:%S') [sup] $*" | tee -a "$RUN/sup.log"; }

# active 指针 → versions/<active>/app_config.generated.json,否则回退 FALLBACK_CFG(对齐 select_startup_config)。
resolve_cfg() {
  if [ -f "$BUILD/active" ]; then
    av=$(cat "$BUILD/active" 2>/dev/null)
    gen="$BUILD/versions/$av/app_config.generated.json"
    [ -f "$gen" ] && { echo "$gen"; return; }
  fi
  echo "$FALLBACK_CFG"
}

STOP=0
trap 'STOP=1; log "收到停止信号"; kill 0 2>/dev/null' INT TERM

# gatewayc respawn 循环:每次启动都解析 active 配置(激活=翻指针后由本循环带新配置重启)。
gatewayc_loop() {
  while [ "$STOP" = 0 ]; do
    c=$(resolve_cfg)
    log "启动 gatewayc --config $c --port $PORT"
    "$GATEWAYC" run --config "$c" --port "$PORT" >> "$RUN/gatewayc.log" 2>&1 &
    gwpid=$!
    echo "$gwpid" > "$RUN/gatewayc.pid"     # nexus 激活时据此 SIGTERM,触发本循环带新 active 重启
    wait "$gwpid"
    [ "$STOP" = 0 ] && { log "gatewayc 退出(code $?),2s 后重启(active=$(cat "$BUILD/active" 2>/dev/null))"; sleep 2; }
  done
}

nexus_loop() {
  while [ "$STOP" = 0 ]; do
    log "启动 nexus(remote → $CORE)"
    "$PY" "$NEXUS" --core-url "$CORE" --config "$FALLBACK_CFG" --dist "$DIST" \
        --port "$NEXUS_PORT" --products "$BUILD" >> "$RUN/nexus.log" 2>&1
    [ "$STOP" = 0 ] && { log "nexus 退出(code $?),2s 后重启"; sleep 2; }
  done
}

log "supervisor 起步:GATEWAYC=$GATEWAYC NEXUS=$NEXUS BUILD=$BUILD"
gatewayc_loop &
# 启动健康门:gatewayc 就绪(采集新鲜)后才拉起 nexus,避免 nexus 空转报错。
if "$GATEWAYC" health --url "$CORE" --timeout "$HEALTH_TIMEOUT"; then
  log "gatewayc 健康门通过,拉起 nexus"
else
  log "⚠ gatewayc $HEALTH_TIMEOUT s 内未就绪,仍拉起 nexus(它会重试取数)"
fi
nexus_loop &
wait
