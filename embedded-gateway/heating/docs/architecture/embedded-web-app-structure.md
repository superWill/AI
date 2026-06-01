# Embedded Web App Structure

> 状态：架构模板  
> 适用对象：嵌入式 Linux / 工控机 / 本地屏 Web 应用  
> 示例场景：能源管控、消防 CRT、换热站 HMI、设备监控面板  
> 目标：从零开始做一个能安装到设备、开机自启、浏览器默认显示的本地 Web APP。

## 1. 典型运行形态

这类应用本质上是运行在嵌入式 Linux 设备上的本地 Web 系统：

```text
本地屏 / 浏览器
        |
        v
Nginx :80
  - /              -> 前端静态页面
  - /api/          -> 后端 REST API
  - /ws            -> 后端 WebSocket
        |
        v
Backend :8091
  - FastAPI / Node / Go 服务
  - SQLite / 配置文件
  - 设备通信
        |
        v
现场设备 / 采集模块 / 控制器
```

其中：

- 前端负责屏幕上看到的页面。
- 后端负责数据、配置、状态、告警、设备通信。
- Nginx 负责默认入口、静态资源、反向代理。
- systemd 负责开机自启和异常重启。
- install.sh 负责把应用安装到目标设备。

## 2. 推荐目录结构

```text
my-embedded-app/
  README.md
  VERSION
  package.json
  pnpm-workspace.yaml

  frontend/
    package.json
    vite.config.ts
    index.html
    public/
      icons/
    src/
      main.tsx
      App.tsx
      views/
      components/
      store/
      utils/
    dist/

  backend/
    requirements.txt
    run_server.py
    app/
      main.py
      config.py
      api/
      core/
      db/
      services/
      connectors/
      utils/

  assets/
    drawings/
    project/

  config/
    default.json
    production.json

  deploy/
    linux/
      install.sh
      uninstall.sh
      app.service
      app.nginx.conf
      config.prod.json

  docs/
    architecture.md
    deployment.md
    device-network-bringup.md
    api.md

  scripts/
    release-linux-arm64.mjs

  release/
    my-app-linux-arm64/
    my-app-linux-arm64.tar.gz
```

## 3. 前端层

前端通常使用 React / Vue / Svelte + Vite，构建结果是一组静态文件。

最小模块：

| 模块 | 说明 |
|---|---|
| `views/MonitorView` | 主监控画面，默认首屏 |
| `views/DevicesView` | 设备列表、点位状态 |
| `views/EventsView` | 事件和告警 |
| `views/SettingsView` | 网络、设备、阈值、系统参数 |
| `components/` | 通用 UI 组件 |
| `store/` | 前端状态，如当前设备、实时数据、登录状态 |
| `utils/api.ts` | REST API 请求封装 |
| `utils/ws.ts` | WebSocket 连接封装 |

构建命令：

```bash
pnpm install --reporter=append-only
pnpm build
```

生产环境前端目录通常安装到：

```text
/opt/my-app/frontend
```

## 4. 后端层

后端负责本机业务能力，不建议让前端直接访问设备总线或本地数据库。

最小 API：

| API | 用途 |
|---|---|
| `GET /api/v1/health` | 健康检查 |
| `GET /api/v1/devices` | 设备列表 |
| `GET /api/v1/events` | 告警 / 事件 |
| `GET /api/v1/settings` | 系统配置 |
| `PUT /api/v1/settings` | 修改配置 |
| `/ws` | 实时数据推送 |

后端内部建议分层：

```text
api/          HTTP / WebSocket 路由
core/         主流程、状态机、事件管线
db/           SQLite 初始化、DAO、迁移
services/     业务服务、导入解析、算法
connectors/   TCP / RS485 / Modbus / MQTT / 串口
utils/        鉴权、日志、通用工具
```

生产环境后端目录通常安装到：

```text
/opt/my-app/backend
```

数据目录单独放置，升级时保留：

```text
/opt/my-app/data/app.sqlite
```

## 5. Nginx 入口

默认显示应用，关键是 Nginx 监听 `80`，并把 `/` 指向前端静态文件：

```nginx
server {
    listen 80;
    server_name _;

    root /opt/my-app/frontend;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8091;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8091;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

调试阶段建议先监听 `8090` / `8092`，确认页面正常后再切到 `80`。

## 6. systemd 服务

后端用 systemd 托管：

```ini
[Unit]
Description=My Embedded App Backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/my-app
Environment=APP_CONFIG=/etc/my-app/config.json
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=/opt/my-app/backend
ExecStart=/opt/my-app/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8091
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

管理命令：

```bash
systemctl status my-app --no-pager
journalctl -u my-app -f
systemctl restart my-app
```

## 7. 安装脚本职责

`install.sh` 建议完成：

1. 检查 root 权限。
2. 安装系统依赖。
3. 创建系统用户。
4. 创建 `/opt/my-app`、`/opt/my-app/data`、`/etc/my-app`。
5. 备份旧版本，保留 data。
6. 复制 frontend / backend / assets。
7. 初始化数据库。
8. 创建 Python venv 或安装运行时。
9. 写入 config。
10. 安装 systemd service。
11. 安装 Nginx site。
12. `nginx -t`、reload nginx。
13. 输出验证命令。

## 8. 能源管控项目落地建议

当前 `embedded-heating` 先按轻量 HMI 原型落地：

```text
embedded-heating/prototype/hmi/hmi/index.html
```

短期部署方式：

- 作为纯静态页面安装到 `/opt/energy-hmi`。
- Nginx 监听 `8092`。
- 浏览器访问 `http://192.168.1.110:8092/`。
- 不影响 CRT 应用的 `8090`。

后续演进方式：

1. 增加后端服务，采集真实点位。
2. 增加 SQLite 保存设备、阈值、运行记录。
3. 增加 WebSocket 推送实时数据。
4. 增加 MQTT 上报和远程参数下发。
5. 验证稳定后再切到 `80` 作为设备默认页面。

## 9. 最小验收标准

| 项目 | 验收方式 |
|---|---|
| 页面可打开 | `curl -I http://127.0.0.1:8092/` 返回 `200 OK` |
| 浏览器可访问 | Mac 打开 `http://192.168.1.110:8092/` |
| 重启后仍可访问 | `reboot` 后再次访问页面 |
| 不影响 CRT | `http://192.168.1.110:8090/` 仍可打开 |
| 可切默认页面 | Nginx 改 `listen 80;` 后 `http://192.168.1.110/` 显示目标应用 |
