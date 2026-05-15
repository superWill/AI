# BL410 Embedded Device Network Bring-up

> 状态：开发前置流程  
> 设备：BL410-bliiot / 目标设备 `192.168.1.110`  
> 主机：macOS 开发机  
> 记录日期：2026-05-15  
> 用途：整理嵌入式开发前的网络连通、ARP 清理、SSH 登录和 Web 页面检查流程。

## 1. 使用场景

当开发机通过网口直连或接入同一二层网络调试 BL410 设备时，先把开发机网口配置到与设备同一网段，再确认路由、ARP、Ping、SSH 和 Web 页面访问。

当前约定：

| 项目 | 值 | 说明 |
|---|---|---|
| 开发机网口 | `en12` | macOS 上的目标以太网接口 |
| 开发机 IP | `192.168.1.20` | 手动配置到 `192.168.1.0/24` 网段 |
| 设备 IP | `192.168.1.110` | BL410 设备地址 |
| 子网掩码 | `255.255.255.0` | 对应 `/24` |
| SSH 用户 | `root` | 当前可登录账户 |

## 2. 启动前检查

1. 确认网线已连接到开发机对应网口和 BL410 设备。
2. 确认设备已上电，网口灯有 Link / Activity 状态。
3. 确认 `en12` 是当前要使用的网口：

```bash
ifconfig en12
```

如果接口名变化，先用下面命令查找实际网口：

```bash
networksetup -listallhardwareports
ifconfig
```

## 3. 配置开发机网络

给开发机网口 `en12` 配置静态 IP：

```bash
sudo ifconfig en12 inet 192.168.1.20 netmask 255.255.255.0 up
```

添加到设备 IP 的主机路由，强制 `192.168.1.110` 走 `en12`：

```bash
sudo route -n add -host 192.168.1.110 -interface en12
```

检查路由是否生效：

```bash
route -n get 192.168.1.110
```

重点看输出中的 `interface` 是否为 `en12`。

## 4. 清理 ARP 并验证链路

清理旧 ARP 记录，避免 macOS 使用之前缓存的 MAC 地址：

```bash
sudo arp -d 192.168.1.110 2>/dev/null
```

如果不确定是否清理成功，可以重复执行一次：

```bash
sudo arp -d 192.168.1.110 2>/dev/null
```

再次检查路由：

```bash
route -n get 192.168.1.110
```

Ping 设备：

```bash
ping -c 3 192.168.1.110
```

检查 ARP 表中是否出现设备：

```bash
arp -a | grep 192.168.1.110
```

预期结果：

- `ping` 有响应，说明 IP 层连通。
- `arp -a` 能看到 `192.168.1.110` 对应的 MAC 地址，说明二层解析正常。

## 5. SSH 登录设备

登录 BL410：

```bash
ssh root@192.168.1.110
```

成功后 shell 提示符类似：

```text
root@BL410-bliiot:~#
```

登录后建议先记录基础信息：

```bash
hostname
ip addr
ip route
cat /etc/os-release 2>/dev/null
uname -a
df -h
```

## 6. 检查是否有 Web 页面

设备能 SSH 不代表一定有 Web 页面。需要确认设备是否开启了 HTTP / HTTPS 服务。

当前已确认：

```text
nc -vz 192.168.1.110 80
Connection to 192.168.1.110 80 port [tcp/http] succeeded!

curl -I http://192.168.1.110/
HTTP/1.1 200 OK
Server: Apache/2.4.41 (Ubuntu)
Content-Type: text/html
```

结论：设备已启动 HTTP Web 服务，浏览器应访问 `http://192.168.1.110/`。

### 6.1 从开发机检查端口

先检查常见 Web 端口：

```bash
nc -vz 192.168.1.110 80
nc -vz 192.168.1.110 443
nc -vz 192.168.1.110 8080
```

如果端口打开，再用浏览器访问：

```text
http://192.168.1.110/
https://192.168.1.110/
http://192.168.1.110:8080/
```

也可以用命令直接看 HTTP 响应：

```bash
curl -I http://192.168.1.110/
curl -I http://192.168.1.110:8080/
```

判断方式：

| 现象 | 结论 |
|---|---|
| 浏览器能打开登录页 / 管理页 | 设备 Web 服务已运行 |
| `curl -I` 返回 `HTTP/1.1 200`、`301`、`302`、`401` 或 `403` | 有 Web 服务，但可能需要登录或跳转 |
| `Connection refused` | 设备在线，但目标端口没有服务监听 |
| `Operation timed out` | 路由、防火墙、网线、设备服务或 IP 配置需要继续排查 |

### 6.2 登录设备后检查服务

在 SSH shell 里查看监听端口：

```bash
ss -lntp
```

如果系统没有 `ss`，尝试：

```bash
netstat -lntp
```

重点看是否有 `:80`、`:443`、`:8080` 等端口。

常见 Web 服务进程名：

- `nginx`
- `lighttpd`
- `uhttpd`
- `boa`
- `httpd`
- 设备厂商自带的 Web 管理进程

可用下面命令辅助查找：

```bash
ps | grep -Ei 'nginx|lighttpd|uhttpd|boa|httpd|web'
```

## 7. 推荐执行顺序

每次重新接板或换网口后，按下面顺序执行：

```bash
sudo ifconfig en12 inet 192.168.1.20 netmask 255.255.255.0 up
sudo route -n add -host 192.168.1.110 -interface en12
sudo arp -d 192.168.1.110 2>/dev/null
route -n get 192.168.1.110
ping -c 3 192.168.1.110
arp -a | grep 192.168.1.110
ssh root@192.168.1.110
```

如果只想快速确认能不能打开页面：

```bash
ping -c 3 192.168.1.110
nc -vz 192.168.1.110 80
curl -I http://192.168.1.110/
```

## 8. 部署 CRT 应用

项目路径：

```text
/Users/songzijian/Coding/crt-app-skeleton
```

目标：先让 CRT 应用跑在 `http://192.168.1.110:8090/`，验证通过后再切到默认 `80` 端口。

### 8.1 在 Mac 上构建发布包

```bash
cd /Users/songzijian/Coding/crt-app-skeleton
pnpm install --reporter=append-only
pnpm build
pnpm run release:linux-arm64
cd release
COPYFILE_DISABLE=1 tar -czf crt-linux-arm64.tar.gz crt-linux-arm64
scp crt-linux-arm64.tar.gz root@192.168.1.110:/tmp/
```

说明：

- `COPYFILE_DISABLE=1` 用于避免 macOS 打包时生成 `._xxx` AppleDouble 元数据文件。
- 如果设备解压时提示 `time stamp ... is ... in the future`，通常是设备系统时间落后于 Mac；不影响文件解压，但建议后续修正设备时间或配置 NTP。

### 8.2 在设备上安装

```bash
ssh root@192.168.1.110
cd /tmp
tar -xzf crt-linux-arm64.tar.gz
cd crt-linux-arm64
chmod +x install.sh uninstall.sh
./install.sh
```

安装脚本会：

- 将程序安装到 `/opt/crt`。
- 将配置写入 `/etc/crt/config.json`。
- 安装并启动 `crt.service`。
- 配置 Nginx 作为外部访问入口。

如果设备无法解析外网域名，可能看到类似：

```text
Temporary failure resolving 'ports.ubuntu.com'
Temporary failure in name resolution
```

这表示设备当前不能访问外部 apt / pip 源。若依赖已经安装或已有缓存，脚本仍可能继续完成；新设备首次部署时建议先解决 DNS / 默认网关 / 外网访问问题。

### 8.3 验证服务

在设备上执行：

```bash
systemctl status crt --no-pager
systemctl status nginx --no-pager
curl http://127.0.0.1:8091/api/v1/health
curl -I http://127.0.0.1:8090/
```

预期结果：

```text
curl http://127.0.0.1:8091/api/v1/health
{"ok":true}

curl -I http://127.0.0.1:8090/
HTTP/1.1 200 OK
```

然后在 Mac 浏览器访问：

```text
http://192.168.1.110:8090/
```

### 8.4 修正 Nginx 前端入口

如果 `curl http://127.0.0.1:8090/` 返回：

```json
{"detail":"Not Found"}
```

说明 Nginx 把 `/` 转发给了 FastAPI，FastAPI 没有根路径页面。应改为：`/` 显示前端静态文件，`/api/` 和 `/ws` 转发给后端。

在设备上执行：

```bash
cat > /etc/nginx/sites-available/crt <<'EOF'
server {
    listen 8090;
    server_name _;

    root /opt/crt/frontend;
    index index.html;

    client_max_body_size 64m;

    location /ws {
        proxy_pass http://127.0.0.1:8091;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8091;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /assets/ {
        try_files $uri @backend_assets;
    }

    location @backend_assets {
        proxy_pass http://127.0.0.1:8091;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

nginx -t
systemctl reload nginx
curl -I http://127.0.0.1:8090/
```

## 9. 切换到默认 80 端口

`8090` 验证通过后，可以让设备默认打开 CRT 应用。

切换前确认：

```bash
curl -I http://127.0.0.1:8090/
systemctl status crt --no-pager
systemctl status nginx --no-pager
```

停用 Apache，避免占用 `80`：

```bash
systemctl stop apache2
systemctl disable apache2
```

把 Nginx 从 `8090` 改为 `80`：

```bash
sed -i 's/listen 8090;/listen 80;/' /etc/nginx/sites-available/crt
nginx -t
systemctl reload nginx
curl -I http://127.0.0.1/
```

预期：

```text
HTTP/1.1 200 OK
Server: nginx/1.18.0 (Ubuntu)
```

之后在 Mac 浏览器访问：

```text
http://192.168.1.110/
```

此时默认显示的就是 CRT 应用，而不是 Apache2 Ubuntu Default Page。

如果需要回退到 Apache 默认页：

```bash
sed -i 's/listen 80;/listen 8090;/' /etc/nginx/sites-available/crt
nginx -t
systemctl reload nginx
systemctl enable apache2
systemctl start apache2
```

## 10. 部署能源管控 HMI

当前能源管控项目位于：

```text
/Users/songzijian/Coding/AI/embedded-heating
```

轻量 HMI 原型入口：

```text
embedded-heating/prototype/hmi/hmi/index.html
```

已准备 BL410 部署包：

```text
embedded-heating/release/energy-hmi-bl410.tar.gz
```

设备安装位置：

```text
/opt/energy-hmi/html
```

Nginx 入口：

```text
/etc/nginx/sites-available/energy-hmi
```

当前访问地址：

```text
http://192.168.1.110:8092/
```

重新部署命令：

```bash
cd /Users/songzijian/Coding/AI/embedded-heating/release
scp energy-hmi-bl410.tar.gz root@192.168.1.110:/tmp/

ssh root@192.168.1.110
cd /tmp
rm -rf energy-hmi-bl410
tar -xzf energy-hmi-bl410.tar.gz
cd energy-hmi-bl410
chmod +x install.sh uninstall.sh
./install.sh
curl -I http://127.0.0.1:8092/
```

验收结果：

```text
curl -I http://127.0.0.1:8092/
HTTP/1.1 200 OK
Server: nginx/1.18.0 (Ubuntu)
Content-Type: text/html

curl -I http://192.168.1.110:8092/
HTTP/1.1 200 OK
Server: nginx/1.18.0 (Ubuntu)
Content-Type: text/html
```

设备监听状态：

```text
0.0.0.0:8092  nginx
```

因此 Mac 浏览器可以访问：

```text
http://192.168.1.110:8092/
```

## 11. 显示器开机默认显示能源管控 HMI

目标：BL410 接显示器启动后，自动进入图形界面，并用 Chromium 全屏显示能源管控 HMI。

当前配置：

| 项目 | 值 |
|---|---|
| 图形登录管理器 | LightDM |
| 自动登录用户 | `Bliiot` |
| Kiosk 服务 | `energy-hmi-kiosk.service` |
| 浏览器 | `/usr/bin/chromium` |
| 显示页面 | `http://127.0.0.1:8092/` |
| Chromium profile | `/home/Bliiot/.config/chromium-energy-hmi` |

关键文件：

```text
/usr/local/bin/start-energy-hmi-kiosk.sh
/etc/systemd/system/energy-hmi-kiosk.service
/etc/lightdm/lightdm.conf.d/50-autologin.conf
/usr/local/bin/fix-hdmi-resolution.sh
```

启动脚本：

```bash
cat > /usr/local/bin/start-energy-hmi-kiosk.sh <<'EOF'
#!/bin/bash
set -e

URL="http://127.0.0.1:8092/"
PROFILE="/home/Bliiot/.config/chromium-energy-hmi"
export DISPLAY=:0
export XAUTHORITY=/home/Bliiot/.Xauthority
export HOME=/home/Bliiot

for i in {1..90}; do
  if xset q >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

for i in {1..60}; do
  if curl -fsS -I "$URL" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

pkill -u Bliiot -f chromium || true
mkdir -p "$PROFILE"
rm -rf "$PROFILE/Default/Cache" \
       "$PROFILE/Default/Code Cache" \
       "$PROFILE/Default/Service Worker" \
       "$PROFILE/Default/GPUCache" 2>/dev/null || true

exec /usr/bin/chromium \
  --kiosk \
  --start-fullscreen \
  --no-first-run \
  --no-default-browser-check \
  --disable-session-crashed-bubble \
  --disable-infobars \
  --disable-pinch \
  --disable-gpu \
  --disable-software-rasterizer=false \
  --overscroll-history-navigation=0 \
  --user-data-dir="$PROFILE" \
  "$URL"
EOF

chmod +x /usr/local/bin/start-energy-hmi-kiosk.sh
chown Bliiot:Bliiot /usr/local/bin/start-energy-hmi-kiosk.sh
```

systemd 服务：

```bash
cat > /etc/systemd/system/energy-hmi-kiosk.service <<'EOF'
[Unit]
Description=Energy HMI Kiosk (Chromium)
After=network-online.target nginx.service display-manager.service graphical.target
Wants=network-online.target nginx.service display-manager.service

[Service]
Type=simple
User=Bliiot
Group=Bliiot
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/Bliiot/.Xauthority
Environment=HOME=/home/Bliiot
ExecStartPre=/bin/sleep 5
ExecStart=/usr/local/bin/start-energy-hmi-kiosk.sh
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
EOF
```

LightDM 自动登录：

```bash
cat > /etc/lightdm/lightdm.conf.d/50-autologin.conf <<'EOF'
[Seat:seat0]
autologin-user=Bliiot
autologin-user-timeout=0
user-session=xfce
EOF
```

HDMI 分辨率脚本必须不能阻塞 LightDM 启动。当前做法是尝试设置 `HDMI-1`，失败也返回成功：

```bash
cat > /usr/local/bin/fix-hdmi-resolution.sh <<'EOF'
#!/bin/bash
set +e

export DISPLAY=:0
export XAUTHORITY=/var/run/lightdm/root/:0

for i in {1..30}; do
  if xrandr >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if xrandr | grep -q "^HDMI-1 connected"; then
  xrandr --output HDMI-1 \
         --mode 1280x800 \
         --pos 0x0 \
         --scale 1x1 \
         --fb 1280x800 \
         --panning 1280x800 || true
fi

exit 0
EOF

chmod +x /usr/local/bin/fix-hdmi-resolution.sh
```

启用：

```bash
ln -sf /lib/systemd/system/lightdm.service /etc/systemd/system/display-manager.service
systemctl daemon-reload
systemctl set-default graphical.target
systemctl enable energy-hmi-kiosk.service
systemctl restart display-manager.service
systemctl restart energy-hmi-kiosk.service
```

验证：

```bash
systemctl status display-manager.service --no-pager -l
systemctl status energy-hmi-kiosk.service --no-pager -l
pgrep -a -u Bliiot chromium
```

当前验收结果：

```text
energy-hmi-kiosk.service: enabled
energy-hmi-kiosk.service: active (running)
Chromium URL: http://127.0.0.1:8092/
```

如果要临时停止显示器 kiosk：

```bash
systemctl stop energy-hmi-kiosk.service
```

如果要取消开机默认显示：

```bash
systemctl disable --now energy-hmi-kiosk.service
```

## 12. 异常排查

| 问题 | 可能原因 | 处理方式 |
|---|---|---|
| `route: writing to routing socket: File exists` | 主机路由已经存在 | 先执行 `route -n get 192.168.1.110` 确认是否已经走 `en12`；必要时删除旧路由后重加 |
| `ping` 不通，ARP 无记录 | 网线、网口、设备电源、IP 不在同一网段 | 检查 Link 灯、确认设备 IP、确认开发机 IP |
| `ping` 通，SSH 不通 | SSH 服务未启动、防火墙、端口不是 22 | 在串口或其他入口检查 `ss -lntp` |
| SSH 通，Web 不通 | 设备没有开启 Web 服务，或端口不是 80/443/8080 | 登录设备后查监听端口和 Web 进程 |
| 浏览器 HTTPS 报证书错误 | 设备使用自签名证书 | 开发阶段可临时继续访问，量产需配置正式证书或内网信任策略 |
| `8090` 返回 `{"detail":"Not Found"}` | Nginx 将 `/` 反代到 FastAPI | 按“修正 Nginx 前端入口”改为静态文件入口 |
| `80` 仍显示 Apache 默认页 | Apache 仍在监听 `80`，或 Nginx 未切到 `80` | 停用 Apache，确认 `/etc/nginx/sites-available/crt` 中是 `listen 80;` |
| apt / pip 解析失败 | 设备没有外网 DNS 或默认网关 | 配置 DNS、默认路由，或提前准备离线依赖包 |
| 显示器不自动打开页面 | `energy-hmi-kiosk.service` 未运行，或 LightDM 未启动 | 查看 `systemctl status energy-hmi-kiosk.service` 和 `display-manager.service` |
| Chromium 报 `Unable to open X display` | X 会话未准备好或 `XAUTHORITY` 不匹配 | 确认 `xset q` 在 `Bliiot` 用户下可用，确认服务使用 `/home/Bliiot/.Xauthority` |
| LightDM 反复重启 | `display-setup-script` 返回非 0 | 确认 `/usr/local/bin/fix-hdmi-resolution.sh` 最后 `exit 0` |

## 13. 当前结论

1. 这套流程已经能进入设备 shell：`root@BL410-bliiot:~#`。
2. 设备已启动 HTTP Web 服务：`192.168.1.110:80` 可连接，`curl -I http://192.168.1.110/` 返回 `HTTP/1.1 200 OK`。
3. CRT 应用已验证可通过 Nginx 跑通；推荐先使用 `http://192.168.1.110:8090/` 验证，再切换到 `80`。
4. 切换到 `80` 后，只要 Apache 已停用且 Nginx 配置为 `listen 80;`，开发机浏览器访问 `http://192.168.1.110/` 默认显示 CRT 应用。
5. 能源管控 HMI 已部署到 BL410，访问地址为 `http://192.168.1.110:8092/`。
6. 显示器开机默认显示能源管控 HMI 已配置：`energy-hmi-kiosk.service` 已启用并运行，Chromium kiosk 打开 `http://127.0.0.1:8092/`。
