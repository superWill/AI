#!/bin/sh
set -eu

APP_ROOT="${APP_ROOT:-/userdata/energy-hmi}"
PORT="${PORT:-8092}"
SRC_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found on target"
  exit 1
fi

mkdir -p "$APP_ROOT" "$APP_ROOT/run" "$APP_ROOT/log"

if [ -d "$APP_ROOT/html" ]; then
  backup="$APP_ROOT/html.backup.$(date +%Y%m%d_%H%M%S)"
  mv "$APP_ROOT/html" "$backup"
  mkdir -p "$APP_ROOT/html"
  echo "Previous html backed up to $backup"
fi

mkdir -p "$APP_ROOT/html" "$APP_ROOT/bin"

cp -R "$SRC_ROOT/html/." "$APP_ROOT/html/"
cp -R "$SRC_ROOT/bin/." "$APP_ROOT/bin/"
chmod +x "$APP_ROOT/bin/serve_hmi.py"

cat > "$APP_ROOT/env.sh" <<EOF
APP_ROOT="$APP_ROOT"
PORT="$PORT"
EOF

echo "Installed Energy HMI to $APP_ROOT"
echo "Run: $APP_ROOT/start.sh"
echo "URL: http://192.168.1.10:$PORT/"

cp "$SRC_ROOT/start.sh" "$APP_ROOT/start.sh"
cp "$SRC_ROOT/stop.sh" "$APP_ROOT/stop.sh"
cp "$SRC_ROOT/status.sh" "$APP_ROOT/status.sh"
cp "$SRC_ROOT/uninstall.sh" "$APP_ROOT/uninstall.sh"
chmod +x "$APP_ROOT/start.sh" "$APP_ROOT/stop.sh" "$APP_ROOT/status.sh" "$APP_ROOT/uninstall.sh"
