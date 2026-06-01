#!/bin/sh
set -eu

APP_ROOT="${APP_ROOT:-/userdata/energy-hmi}"
PORT="${PORT:-8092}"

if [ -f "$APP_ROOT/env.sh" ]; then
  . "$APP_ROOT/env.sh"
fi

PID_FILE="$APP_ROOT/run/energy-hmi.pid"
LOG_FILE="$APP_ROOT/log/energy-hmi.log"

mkdir -p "$APP_ROOT/run" "$APP_ROOT/log"

if [ -f "$PID_FILE" ]; then
  old_pid=$(cat "$PID_FILE")
  if [ -n "$old_pid" ] && kill -0 "$old_pid" >/dev/null 2>&1; then
    echo "Energy HMI is already running: pid $old_pid"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

nohup python3 "$APP_ROOT/bin/serve_hmi.py" \
  --root "$APP_ROOT/html" \
  --host 0.0.0.0 \
  --port "$PORT" \
  >> "$LOG_FILE" 2>&1 &

echo "$!" > "$PID_FILE"
echo "Energy HMI started: pid $(cat "$PID_FILE"), port $PORT"
