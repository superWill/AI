#!/usr/bin/env bash
# 云端测试机一键部署：swap + PostgreSQL + mosquitto + ingest worker + cron + Grafana
# 目标：Alibaba Cloud Linux 3 / RHEL 系（dnf）。原型/测试用，匿名 MQTT、自建 PG。
# 用法（在 ECS 上，代码已放 /opt/heating-cloud）：
#     cd /opt/heating-cloud && sudo bash deploy/bootstrap.sh
# 幂等：可重复跑；已存在的东西跳过。PG 密码自动生成，结尾打印。
set -euo pipefail

APP_DIR=/opt/heating-cloud
PGDATA=/var/lib/pgsql/data
DB=heating
DBUSER=heating
# 复用已有密码（重复跑时），否则生成
PASS_FILE=/var/lib/heating/.dbpass
mkdir -p /var/lib/heating
if [[ -f "$PASS_FILE" ]]; then PGPASS=$(cat "$PASS_FILE"); else PGPASS=$(openssl rand -hex 12); echo "$PGPASS" > "$PASS_FILE"; fi
chmod 600 "$PASS_FILE"

say(){ echo -e "\n\033[1;36m== $* ==\033[0m"; }

# --- 1. swap -----------------------------------------------------------------
say "1. swap"
if ! swapon --show | grep -q swapfile; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo "swap on"
else echo "swap 已存在，跳过"; fi

# --- 2. 装包 -----------------------------------------------------------------
say "2. dnf 安装依赖"
# 用 python3.11：系统自带的 3.6 太老（pip 9 抓不到 wheel、不支持 from __future__ import annotations）
dnf install -y postgresql-server postgresql python3.11 python3.11-pip openssl
dnf install -y mosquitto || { dnf install -y epel-release && dnf install -y mosquitto; }

# --- 3. PostgreSQL -----------------------------------------------------------
say "3. PostgreSQL"
if [[ ! -f "$PGDATA/PG_VERSION" ]]; then postgresql-setup --initdb; fi
# 让 127.0.0.1 走密码（默认是 ident，密码连不上 —— 经典坑）
# 用 md5：PG13 默认密码存为 md5；md5 认证法兼容 md5/scram 两种存储，最稳。
sed -ri 's#^(host\s+all\s+all\s+127\.0\.0\.1/32\s+)\S+#\1md5#' "$PGDATA/pg_hba.conf" || true
sed -ri 's#^(host\s+all\s+all\s+::1/128\s+)\S+#\1md5#'        "$PGDATA/pg_hba.conf" || true
# 压内存调参（带标记防重复追加）
if ! grep -q 'heating-tuning' "$PGDATA/postgresql.conf"; then
  { echo "# heating-tuning"; cat "$APP_DIR/deploy/postgresql-2g.conf"; } >> "$PGDATA/postgresql.conf"
fi
systemctl enable --now postgresql
systemctl restart postgresql
# 建库 + 用户（幂等）
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='$DBUSER'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER $DBUSER WITH PASSWORD '$PGPASS';"
sudo -u postgres psql -c "ALTER USER $DBUSER WITH PASSWORD '$PGPASS';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$DB'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE DATABASE $DB OWNER $DBUSER;"
# 建表（基础 + 阶段B 口径层）
PGPASSWORD="$PGPASS" psql "host=127.0.0.1 dbname=$DB user=$DBUSER" -f "$APP_DIR/schema.sql"
PGPASSWORD="$PGPASS" psql "host=127.0.0.1 dbname=$DB user=$DBUSER" -f "$APP_DIR/schema_phase_b.sql"

# --- 4. mosquitto（原型：匿名）----------------------------------------------
say "4. mosquitto"
# 该版默认无 conf.d 且 include_dir 注释掉，先建目录并开启 include
mkdir -p /etc/mosquitto/conf.d
grep -q '^include_dir /etc/mosquitto/conf.d' /etc/mosquitto/mosquitto.conf || \
  echo 'include_dir /etc/mosquitto/conf.d' >> /etc/mosquitto/mosquitto.conf
cat > /etc/mosquitto/conf.d/heating.conf <<'EOF'
listener 1883 0.0.0.0
allow_anonymous true
EOF
systemctl enable --now mosquitto
systemctl restart mosquitto

# --- 5. ingest worker --------------------------------------------------------
say "5. ingest worker"
id heating &>/dev/null || useradd -r -s /sbin/nologin heating
python3.11 -m pip install -r "$APP_DIR/requirements.txt"
cat > "$APP_DIR/config.json" <<EOF
{
  "client_id": "cloud-ingest",
  "broker_host": "127.0.0.1", "broker_port": 1883, "keepalive": 60,
  "username": "", "password": "", "tls": false, "ca_certs": null,
  "dsn": "host=127.0.0.1 port=5432 dbname=$DB user=$DBUSER password=$PGPASS"
}
EOF
chown -R heating "$APP_DIR"
cp "$APP_DIR/deploy/ingest-worker.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now ingest-worker
systemctl restart ingest-worker

# --- 6. cron 维护 ------------------------------------------------------------
say "6. cron 维护"
echo "127.0.0.1:5432:$DB:$DBUSER:$PGPASS" > /var/lib/heating/.pgpass
chown -R heating /var/lib/heating && chmod 600 /var/lib/heating/.pgpass
cp "$APP_DIR/deploy/cloud-maintenance.cron" /etc/cron.d/cloud-maintenance

# --- 7. Grafana --------------------------------------------------------------
say "7. Grafana"
# 官方源 rpm.grafana.com 在国内拉不动（海外/Cloudflare），用清华 TUNA 镜像
if ! rpm -q grafana &>/dev/null; then
  cat > /etc/yum.repos.d/grafana.repo <<'EOF'
[grafana]
name=grafana
baseurl=https://mirrors.tuna.tsinghua.edu.cn/grafana/yum/rpm
gpgcheck=0
enabled=1
EOF
  dnf install -y grafana
fi
# 数据源（自动配置）
mkdir -p /etc/grafana/provisioning/datasources
cat > /etc/grafana/provisioning/datasources/heating.yaml <<EOF
apiVersion: 1
datasources:
  - name: HeatingPG
    uid: heating_pg
    type: postgres
    access: proxy
    url: 127.0.0.1:5432
    user: $DBUSER
    jsonData: { database: $DB, sslmode: disable, postgresVersion: 1500, timescaledb: false }
    secureJsonData: { password: "$PGPASS" }
EOF
# 仪表盘（自动装载，免手动 import）
mkdir -p /etc/grafana/provisioning/dashboards /var/lib/grafana/dashboards
cp "$APP_DIR/deploy/grafana-dashboard.json" /var/lib/grafana/dashboards/
chown -R grafana:grafana /var/lib/grafana/dashboards
cat > /etc/grafana/provisioning/dashboards/heating.yaml <<EOF
apiVersion: 1
providers:
  - name: heating
    type: file
    options: { path: /var/lib/grafana/dashboards }
EOF
systemctl enable --now grafana-server
systemctl restart grafana-server

IP=$(curl -s --max-time 3 ifconfig.me || echo "<ECS公网IP>")
say "完成"
cat <<EOF

PG 密码（已写各配置，留底）： $PGPASS

自检：
  systemctl status ingest-worker --no-pager   # 应 active，日志见 journalctl -u ingest-worker -f
  systemctl status mosquitto postgresql grafana-server --no-pager

灌模拟数据（另开一个会话）：
  cd $APP_DIR && python3.11 simulate_station.py --stations 10 --interval 5

看数据：
  PGPASSWORD=$PGPASS psql "host=127.0.0.1 dbname=$DB user=$DBUSER" -c "SELECT count(*) FROM telemetry;"

Grafana：浏览器开 http://$IP:3000 （默认 admin/admin，首次改密）
  → Dashboards → Import → 上传 deploy/grafana-dashboard.json → 数据源选 HeatingPG

注意：安全组要放行 3000(给你的IP) 和 1883；3000/22 别对 0.0.0.0 开。
EOF
