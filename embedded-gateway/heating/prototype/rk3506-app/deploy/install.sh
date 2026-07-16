#!/bin/sh
# 在板子(RK3506)上运行:把应用装到 /userdata/rk3506-app 并挂开机自启。
# 由 push.sh 经跳板推送整个目录后自动调用,也可手工跑。
set -eu

SRC=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)   # rk3506-app 源目录
APP=/userdata/rk3506-app

echo "[install] 源=$SRC  目标=$APP"
mkdir -p "$APP/run"

# 厂家旧 HMI 会由 S99zzhmi 启动 /root/hmi_start.sh，后者会无限重启
# hmi_lvgl 并重新抢占 DRM。把启动项移出 /etc/init.d，同时保留可恢复备份。
if [ -e /etc/init.d/S99zzhmi ]; then
  mkdir -p "$APP/disabled-init"
  mv -f /etc/init.d/S99zzhmi "$APP/disabled-init/S99zzhmi"
  echo "[install] 已禁用旧 LCD 自启: /etc/init.d/S99zzhmi"
fi
# 拷应用文件(保留 run/ 下的日志/pid)
cp -f "$SRC/app.py" "$SRC/drm_hmi_v2.py" "$SRC/drm_hmi_v3.py" "$SRC/drm_hmi_v4.py" \
      "$SRC/dashboard.py" "$SRC/cjk_font.py" "$SRC/compiler.py" "$SRC/loader.py" \
      "$SRC/nexus_server.py" "$SRC/app_config.json" "$APP/"
cp -f "$SRC/sim_104.py" "$SRC/sim_104_config.json" "$APP/" 2>/dev/null || true
# Go 版 LCD HMI(hmi-go/build.sh 产物);缺席时 S99 脚本回退 Python drm_hmi_v4
if [ -f "$SRC/hmic" ]; then
  cp -f "$SRC/hmic" "$APP/hmic"
  chmod +x "$APP/hmic"
  echo "[install] 已安装 Go LCD HMI: $APP/hmic"
fi
# nexus-edge-os 前端 dist + 轻量 HMI
rm -rf "$APP/nexus-dist"; mkdir -p "$APP/nexus-dist"
cp -Rf "$SRC/nexus-dist/." "$APP/nexus-dist/"
mkdir -p "$APP/html"
cp -Rf "$SRC/html/." "$APP/html/"
chmod +x "$APP/app.py" "$APP/drm_hmi_v2.py" "$APP/nexus_server.py" 2>/dev/null || true

# 已存在 gatewayc 时保留正式 Go 核心拓扑，并在其 UI 前增加设备配置代理。
if [ -x "$APP/gatewayc" ]; then
  cp -f "$SRC/deploy/supervisor-go.sh" "$APP/supervisor-go.sh"
  cp -f "$SRC/deploy/S99gateway-go" "$APP/S99zz-gateway-go"
  chmod +x "$APP/supervisor-go.sh" "$APP/S99zz-gateway-go"
  cp -f "$APP/S99zz-gateway-go" /etc/init.d/S99zz-gateway
  chmod +x /etc/init.d/S99zz-gateway
  /etc/init.d/S99zz-gateway restart
  echo "[install] 已更新 Go 正式拓扑(core:8091 + ui:8092)"
  exit 0
fi

# 无 gatewayc 时使用 Python 单体拓扑。
# 开机自启:命名 S99zz-gateway 以排在厂家 S99lvgl-test 之后启动(后启动者占屏幕)。
# 清掉旧名 S99gateway,避免开机重复启动。
rm -f /etc/init.d/S99gateway 2>/dev/null
INIT=/etc/init.d/S99zz-gateway
if cp -f "$SRC/deploy/S99gateway" "$INIT" 2>/dev/null; then
  chmod +x "$INIT"
  echo "[install] 已安装自启 $INIT(排在厂家 LVGL 之后)"
else
  cp -f "$SRC/deploy/S99gateway" "$APP/S99gateway"
  chmod +x "$APP/S99gateway"
  INIT="$APP/S99gateway"
  echo "[install] /etc 只读:自启脚本放在 $INIT"
  echo "[install] 请把它挂到厂家启动里(rc.local / 厂商 S?? 脚本),或手动运行:$INIT start"
fi

# 立即(重)启动
"$INIT" restart || "$INIT" start

echo "[install] 完成。"
echo "  Web HMI : http://192.168.1.10:8092/"
echo "  本地LCD : 已接管屏幕(第一屏=应用页)"
echo "  日志    : tail -f $APP/run/app.log $APP/run/lcd.log"
