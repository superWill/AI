#!/bin/sh
set -eu

APP_ROOT="${APP_ROOT:-/userdata/energy-hmi}"

if [ -x "$APP_ROOT/stop.sh" ]; then
  "$APP_ROOT/stop.sh" || true
fi

rm -rf "$APP_ROOT"
echo "Removed $APP_ROOT"
