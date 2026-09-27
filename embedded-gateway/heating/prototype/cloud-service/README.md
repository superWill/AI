# 云端测试机 · 上报→落库→出图（一台 2核2G ECS 跑通）

把网关 MQTT 上行接进云、落 PostgreSQL、Grafana 出图的**最小可跑**栈。
消费已定的 [数据接口契约](../../docs/protocols/upstream-platform-data-contract.md)，
不另造 HTTP。目标机型：阿里云 `ecs.e-c1m1.large`（2核2G / 3M / 40G，Alibaba Cloud Linux 3）。

```
RK3506 网关 ──MQTT──► mosquitto ──► ingest_worker.py ──► PostgreSQL ──► Grafana
   (现场)            (broker,~5MB)   (paho 订阅 station/#)   (窄表+小时聚合)   (看板)
```

> ⚠️ 测试机定位：跑通链路、压测、点亮看板。**别长期存真实数据**（40G 会满），
> 别拿它扛客户。生产要 4核8G + 独立数据盘 + 独立 RDS。

---

## 0. 安全组（先做，否则要么连不上要么被扫）

阿里云控制台 → 该 ECS → 安全组 → 入方向，只放这几条：

| 端口 | 来源 | 用途 |
|---|---|---|
| 22 | **你的办公 IP** | SSH，别对 0.0.0.0 开 |
| 1883 | 网关出口 IP / 测试期你的 IP | MQTT |
| 3000 | **你的 IP** | Grafana 后台 |

**5432(PostgreSQL) 一律不开公网**——只走本机 127.0.0.1。上线再考虑 8883(MQTT over TLS)。

---

## 1. swap（2G 内存的兜底，5 分钟）

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h          # 确认 Swap 那行出来了
```

## 2. PostgreSQL

```bash
sudo dnf install -y postgresql-server postgresql
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql

# 建库 + 用户（把 CHANGE_ME 换成强密码）
sudo -u postgres psql <<'SQL'
CREATE USER heating WITH PASSWORD 'CHANGE_ME';
CREATE DATABASE heating OWNER heating;
SQL

# 压内存调参：把 deploy/postgresql-2g.conf 内容追加进 postgresql.conf
sudo bash -c 'cat /opt/heating-cloud/deploy/postgresql-2g.conf >> /var/lib/pgsql/data/postgresql.conf'
sudo systemctl restart postgresql

# 建表
psql "host=127.0.0.1 dbname=heating user=heating" -f /opt/heating-cloud/schema.sql
```

> 假设代码放在 `/opt/heating-cloud/`（把本目录传上去即可）。

## 3. mosquitto（broker）

```bash
sudo dnf install -y mosquitto
# 测试期可先开匿名跑通；联调后再加账号密码：
sudo bash -c 'echo "listener 1883 0.0.0.0
allow_anonymous true" > /etc/mosquitto/conf.d/heating.conf'
sudo systemctl enable --now mosquitto
```

加账号密码（联调通过后再做）：
```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd heating   # 设密码
sudo bash -c 'echo "listener 1883 0.0.0.0
allow_anonymous false
password_file /etc/mosquitto/passwd" > /etc/mosquitto/conf.d/heating.conf'
sudo systemctl restart mosquitto
# 然后把账号填进 config.json 和网关 config.json
```

## 4. ingest worker

```bash
sudo dnf install -y python3 python3-pip
sudo useradd -r -s /sbin/nologin heating || true
cd /opt/heating-cloud
sudo pip3 install -r requirements.txt

cp config.example.json config.json     # 改 dsn 密码 / broker 账号
# 装成常驻服务
sudo cp deploy/ingest-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ingest-worker
journalctl -u ingest-worker -f         # 看日志，应显示 MQTT connected / PostgreSQL connected
```

## 5. 定时维护（小时聚合 + 留存清理）

```bash
sudo cp deploy/cloud-maintenance.cron /etc/cron.d/cloud-maintenance
# .pgpass 让 cron 免密连库（PGPASSFILE 已在 cron 文件里指定到此路径）
sudo mkdir -p /var/lib/heating
echo '127.0.0.1:5432:heating:heating:CHANGE_ME' | sudo tee /var/lib/heating/.pgpass
sudo chown -R heating /var/lib/heating && sudo chmod 600 /var/lib/heating/.pgpass
```

## 6. Grafana

> 官方源 `rpm.grafana.com` 在国内拉不动（海外/Cloudflare），用清华 TUNA 镜像：

```bash
sudo tee /etc/yum.repos.d/grafana.repo >/dev/null <<'REPO'
[grafana]
name=grafana
baseurl=https://mirrors.tuna.tsinghua.edu.cn/grafana/yum/rpm
gpgcheck=0
enabled=1
REPO
sudo dnf install -y grafana
sudo systemctl enable --now grafana-server
```

> 数据源和仪表盘已由 `bootstrap.sh` 自动配置（provisioning），无需手动 import。
浏览器开 `http://<ECS公网IP>:3000`（默认 admin/admin，首次改密）即可看到"供热站监控（测试）"看板。

---

## 7. 验证闭环（不用等真实网关）

测试机上造数据：
```bash
cd /opt/heating-cloud
python3 simulate_station.py --stations 10 --interval 5
```
然后：
- `journalctl -u ingest-worker -f` 应持续收帧入库；
- `psql ... -c "SELECT count(*) FROM telemetry;"` 数字在涨；
- Grafana 看板 `station` 下拉出现 stn-001..010，曲线在动。

接**真实网关**：把 `cloud-gateway-mqtt/config.json` 的 `broker_host` 改成本 ECS 公网 IP
（加了账号就填 username/password），跑 `gateway_mqtt.py` 即可。

---

## 验收清单
- [ ] `free -h` 有 swap；`journalctl -u ingest-worker` 无反复重启
- [ ] simulator 跑起来后 `telemetry` 行数持续增长
- [ ] 断开 simulator 再连，补传帧不产生重复行（靠 `(device_id,seq,metric)` 唯一键）
- [ ] 整点后 `telemetry_hourly` 有聚合行
- [ ] Grafana 三个面板都出数（曲线/在线状态/报警）

## 文件一览
| 文件 | 作用 |
|---|---|
| `schema.sql` | 建表 |
| `ingest_worker.py` | MQTT→PostgreSQL 落库 worker |
| `maintenance.sql` | 小时聚合 + 留存清理（cron 调） |
| `simulate_station.py` | 多站点数据模拟器 |
| `config.example.json` | worker 配置样例 |
| `deploy/` | systemd / cron / PG 调参 / Grafana 数据源与看板 |
