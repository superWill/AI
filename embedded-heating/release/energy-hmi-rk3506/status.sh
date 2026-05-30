#!/bin/sh
set -eu

APP_ROOT="${APP_ROOT:-/userdata/energy-hmi}"
PORT="${PORT:-8092}"

if [ -f "$APP_ROOT/env.sh" ]; then
  . "$APP_ROOT/env.sh"
fi

PID_FILE="$APP_ROOT/run/energy-hmi.pid"

if [ -f "$PID_FILE" ]; then
  pid=$(cat "$PID_FILE")
  if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
    echo "Energy HMI running: pid $pid, port $PORT"
    exit 0
  fi
fi

echo "Energy HMI stopped"
exit 1
