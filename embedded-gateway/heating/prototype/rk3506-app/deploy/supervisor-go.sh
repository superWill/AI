#!/bin/sh
# 生产拓扑监督：gatewayc core:8091 + gatewayc ui:8092(直连,配置代理已退役)。
set -u
GATEWAYC="${GATEWAYC:-./gatewayc}"
PY="${PY:-$(command -v python3 || echo /usr/bin/python3)}"
BUILD="${BUILD:-./build}"
FALLBACK_CFG="${FALLBACK_CFG:-./app_config.json}"
CORE="${CORE:-http://127.0.0.1:8091}"
PORT="${PORT:-8091}"
UI_PORT="${UI_PORT:-8092}"
DIST="${DIST:-./nexus-dist}"
RUN="${RUN:-/tmp/gwsup}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-30}"
mkdir -p "$RUN"

if [ -z "${GATEWAYC_CONTROL_TOKEN:-}" ]; then
  TF="$RUN/control_token"
  [ -s "$TF" ] || (head -c 18 /dev/urandom | base64 | tr -d '\n/+=' > "$TF"; chmod 600 "$TF")
  GATEWAYC_CONTROL_TOKEN=$(cat "$TF")
fi
export GATEWAYC_CONTROL_TOKEN
log() { echo "$(date '+%H:%M:%S') [sup] $*" | tee -a "$RUN/sup.log"; }

resolve_cfg() {
  if [ -f "$BUILD/active" ]; then
    av=$(cat "$BUILD/active" 2>/dev/null); gen="$BUILD/versions/$av/app_config.generated.json"
    [ -f "$gen" ] && { echo "$gen"; return; }
  fi
  echo "$FALLBACK_CFG"
}

STOP=0
trap 'STOP=1; log "收到停止信号"; kill 0 2>/dev/null' INT TERM

gatewayc_loop() {
  while [ "$STOP" = 0 ]; do
    c=$(resolve_cfg); log "启动 gatewayc core:$PORT config=$c"
    "$GATEWAYC" run --config "$c" --port "$PORT" >>"$RUN/gatewayc.log" 2>&1 &
    pid=$!; echo "$pid" > "$RUN/gatewayc.pid"; wait "$pid"
    [ "$STOP" = 0 ] && { log "gatewayc core 退出，2s 后重启"; sleep 2; }
  done
}

ui_loop() {
  while [ "$STOP" = 0 ]; do
    prod=""
    if [ -f "$BUILD/active" ]; then
      av=$(cat "$BUILD/active" 2>/dev/null); vd="$BUILD/versions/$av"
      [ -f "$vd/point_registry.json" ] && prod="--products $vd"
    fi
    log "启动 gatewayc ui:$UI_PORT remote=$CORE"
    "$GATEWAYC" ui --core-url "$CORE" --port "$UI_PORT" --build "$BUILD" \
      --draft "$BUILD/current_draft.json" --gw-pidfile "$RUN/gatewayc.pid" --dist "$DIST" \
      $prod >>"$RUN/ui.log" 2>&1
    [ "$STOP" = 0 ] && { log "gatewayc ui 退出，2s 后重启"; sleep 2; }
  done
}

log "supervisor 起步:core=$PORT ui=$UI_PORT"
gatewayc_loop &
"$GATEWAYC" health --url "$CORE" --timeout "$HEALTH_TIMEOUT" || true
ui_loop &
wait
