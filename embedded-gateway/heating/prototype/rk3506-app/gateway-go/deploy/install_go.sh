#!/bin/sh
# 安装 gatewayc-核心拓扑到 /userdata/rk3506-app —— **staging,不自启、不替换现有 Python S99**。
#
# ⚠ 这是「生产切换」的准备。真正切到 Go 核心需:轨B影子浸泡通过 + 单站灰度授权。
#   本脚本只把文件就位 + 放好新 init(S99zz-gateway-go)在 $APP,不挂到 /etc/init.d、不启动。
#   切换那一刻(授权后)再:停旧 S99 → 安装新 init → 起 supervisor(见末尾提示)。
#
# 前置:gateway-go/deploy/gatewayc-arm(交叉编译 armv7:
#   GOOS=linux GOARCH=arm GOARM=7 go build -ldflags="-s -w" -o deploy/gatewayc-arm .)
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)         # gateway-go/deploy
GO=$HERE
APP_SRC=$(CDPATH= cd -- "$HERE/../.." && pwd)             # rk3506-app(python 源)
APP=/userdata/rk3506-app

[ -f "$GO/gatewayc-arm" ] || { echo "[install-go] 缺 $GO/gatewayc-arm,先交叉编译 armv7"; exit 1; }

echo "[install-go] 源: go=$GO python=$APP_SRC  目标=$APP(staging,不自启)"
mkdir -p "$APP/run" "$APP/build"

# 核心二进制(同一 gatewayc:含 run/health/shadow)+ supervisor
cp -f "$GO/gatewayc-arm" "$APP/gatewayc"; chmod +x "$APP/gatewayc"
cp -f "$GO/supervisor.sh" "$APP/supervisor.sh"; chmod +x "$APP/supervisor.sh"

# nexus 适配层 + 内核 + 配置工具 + LCD + 配置
cp -f "$APP_SRC/app.py" "$APP_SRC/nexus_server.py" "$APP_SRC/compiler.py" "$APP_SRC/loader.py" \
      "$APP_SRC/drm_hmi_v4.py" "$APP_SRC/dashboard.py" "$APP_SRC/cjk_font.py" \
      "$APP_SRC/app_config.json" "$APP/"
rm -rf "$APP/nexus-dist"; mkdir -p "$APP/nexus-dist"; cp -Rf "$APP_SRC/nexus-dist/." "$APP/nexus-dist/"

# 新 init 放到 $APP(**不**挂 /etc/init.d,不动正在跑的 Python S99zz-gateway)
cp -f "$GO/S99zz-gateway-go" "$APP/S99zz-gateway-go"; chmod +x "$APP/S99zz-gateway-go"

# 备份现有 Python init(供 revert_to_python.sh 自包含回退,不依赖源码树在板上)
[ -f /etc/init.d/S99zz-gateway ] && cp -f /etc/init.d/S99zz-gateway "$APP/S99zz-gateway.python.bak" || true

echo "[install-go] 文件就位完成。当前生产仍是 Python(nexus 内嵌),未改动。"
echo
echo "  >>> 生产切换(仅在浸泡+灰度授权后执行):"
echo "      /etc/init.d/S99zz-gateway stop        # 停旧 Python 拓扑"
echo "      cp $APP/S99zz-gateway-go /etc/init.d/S99zz-gateway && chmod +x /etc/init.d/S99zz-gateway"
echo "      /etc/init.d/S99zz-gateway start       # 起 gatewayc 核心 + nexus 客户端 + LCD→8091"
echo "  >>> 回退:$GO/revert_to_python.sh(板上)"
