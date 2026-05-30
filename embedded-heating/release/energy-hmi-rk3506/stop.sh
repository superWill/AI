#!/bin/sh
set -eu

APP_ROOT="${APP_ROOT:-/userdata/energy-hmi}"

if [ -f "$APP_ROOT/env.sh" ]; then
  . "$APP_ROOT/env.sh"
fi

PID_FILE="$APP_ROOT/run/energy-hmi.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "Energy HMI is not running"
  exit 0
fi

pid=$(cat "$PID_FILE")
if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
  kill "$pid"
  echo "Energy HMI stopped: pid $pid"
else
  echo "Energy HMI pid is stale: $pid"
fi

rm -f "$PID_FILE"
