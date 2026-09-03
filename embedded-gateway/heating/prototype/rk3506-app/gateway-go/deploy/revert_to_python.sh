#!/bin/sh
# 一键回退到 Python-only 拓扑(nexus 内嵌核心)——生产切换的安全网。
# 停 gatewayc-核心拓扑,恢复并起回旧 Python S99(install_go.sh 备份的 .python.bak)。
set -u
APP=/userdata/rk3506-app

echo "[revert] 停 gatewayc-核心拓扑"
[ -x "$APP/S99zz-gateway-go" ] && "$APP/S99zz-gateway-go" stop 2>/dev/null
# 先反复杀 supervisor(含 gatewayc_loop/nexus_loop 子 shell)直到没有,否则子 shell 会
# 在杀 gatewayc 的窗口里把它 respawn 回来(实测残留过)。再反复杀 gatewayc/nexus/LCD。
i=0; while [ $i -lt 6 ]; do
  sup=$(ps 2>/dev/null | grep 'supervisor\.sh' | grep -v grep | awk '{print $1}')
  [ -z "$sup" ] && break
  for p in $sup; do kill -9 "$p" 2>/dev/null; done
  sleep 1; i=$((i+1))
done
i=0; while [ $i -lt 3 ]; do
  for p in $(ps 2>/dev/null | grep -E 'gatewayc run|gatewayc ui|nexus_server\.py|drm_hmi' | grep -v grep | awk '{print $1}'); do
    kill -9 "$p" 2>/dev/null
  done
  sleep 1; i=$((i+1))
done

echo "[revert] 恢复 Python init"
if [ -f "$APP/S99zz-gateway.python.bak" ]; then
  cp -f "$APP/S99zz-gateway.python.bak" /etc/init.d/S99zz-gateway && chmod +x /etc/init.d/S99zz-gateway
elif [ -f "$APP/S99zz-gateway" ]; then
  : # /etc 已是 Python 版,无需动
else
  echo "[revert] ⚠ 找不到 Python init 备份;请重跑 Python install.sh 恢复"; exit 1
fi
/etc/init.d/S99zz-gateway restart 2>/dev/null || /etc/init.d/S99zz-gateway start 2>/dev/null || true
sleep 2
ps 2>/dev/null | grep -E 'nexus_server' | grep -v grep >/dev/null && echo "[revert] 已回退,nexus(Python 内嵌)在跑" || echo "[revert] ⚠ 未见 nexus,请人工确认"
