#!/usr/bin/env bash
# 后管后端一键安装（在 ECS 上，backend 已放 /opt/heating-cloud/backend）
#   cd /opt/heating-cloud/backend && sudo bash deploy/install-backend.sh
set -euo pipefail
APP=/opt/heating-cloud/backend

echo "== pip 依赖 =="
python3.11 -m pip install -q -r "$APP/requirements.txt"

echo "== 前端 vendor（国内 staticfile CDN，同源托管）=="
V="$APP/static/vendor"; mkdir -p "$V"
B=https://cdn.staticfile.org
curl -fsSL "$B/vue/3.4.21/vue.global.prod.js"        -o "$V/vue.global.prod.js"
curl -fsSL "$B/element-plus/2.7.3/index.full.min.js" -o "$V/element-plus.full.min.js"
curl -fsSL "$B/element-plus/2.7.3/index.css"         -o "$V/element-plus.css"
curl -fsSL "$B/axios/1.6.8/axios.min.js"             -o "$V/axios.min.js"
ls -l "$V"

echo "== JWT 密钥 =="
[[ -f /var/lib/heating/api.env ]] || echo "HEATING_JWT_SECRET=$(openssl rand -hex 24)" > /var/lib/heating/api.env
chown heating /var/lib/heating/api.env
chown -R heating "$APP"

echo "== systemd 服务 =="
cp "$APP/deploy/admin-api.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now admin-api
systemctl restart admin-api
sleep 3
echo -n "admin-api: "; systemctl is-active admin-api
echo "完成。安全组放行 8000（你的IP）后访问 http://<ECS公网IP>:8000 ，默认 admin/admin"
