# BL410 Interface Debugging Runbook

> 状态：调试手册  
> 设备：BL410-bliiot  
> 设备 IP：`192.168.1.110`  
> 开发机 IP：`192.168.1.20`  
> 场景：设备无法访问外网，只能通过开发机和局域网直连调试。

## 1. 调试分层

调试设备接口时，不要一上来就怀疑业务代码。建议按下面顺序排查：

```text
物理连接 / IP
        |
        v
端口监听 / 进程状态
        |
        v
Nginx / Web 页面
        |
        v
后端 API / WebSocket
        |
        v
本地数据库 / 配置文件 / 日志
        |
        v
串口 / RS485 / TCP / 现场设备
```

## 2. 基础连接检查

在 Mac 上：

```bash
route -n get 192.168.1.110
ping -c 3 192.168.1.110
ssh root@192.168.1.110
```

在设备上：

```bash
hostname
ip addr
ip route
date
df -h
free -h
```

设备时间如果明显不对，日志时间会混乱。当前设备曾出现系统时间落后于 Mac 的情况，调试时要留意。

## 3. 看端口和进程

在设备上看监听端口：

```bash
ss -lntp
```

重点端口：

| 端口 | 当前用途 | 说明 |
|---|---|---|
| `80` | Apache 默认页 | 还未切默认应用时占用 |
| `8090` | CRT 应用 | Nginx 入口 |
| `8091` | CRT FastAPI 后端 | 只监听 `127.0.0.1` |
| `8092` | 能源管控 HMI | Nginx 静态页面入口 |
| `22` | SSH | 远程 shell / scp |

快速确认：

```bash
ss -lntp | grep -E ':(22|80|8090|8091|8092)'
```

看关键服务：

```bash
systemctl status nginx --no-pager -l
systemctl status apache2 --no-pager -l
systemctl status crt --no-pager -l
systemctl status energy-hmi-kiosk --no-pager -l
```

## 4. 调 Web 页面

从 Mac 调：

```bash
curl -I http://192.168.1.110/
curl -I http://192.168.1.110:8090/
curl -I http://192.168.1.110:8092/
```

从设备本机调：

```bash
curl -I http://127.0.0.1/
curl -I http://127.0.0.1:8090/
curl -I http://127.0.0.1:8092/
```

判断：

| 返回 | 含义 |
|---|---|
| `200 OK` | 页面入口正常 |
| `404 {"detail":"Not Found"}` | 多半是 Nginx 把 `/` 转给了 FastAPI |
| `Connection refused` | 端口没服务监听 |
| `Operation timed out` | 路由、防火墙、服务绑定地址或网线问题 |

## 5. 调后端 API

CRT 后端当前监听：

```text
127.0.0.1:8091
```

在设备上直接调：

```bash
curl http://127.0.0.1:8091/api/v1/health
```

预期：

```json
{"ok":true}
```

通过 Nginx 调：

```bash
curl http://127.0.0.1:8090/api/v1/health
curl http://192.168.1.110:8090/api/v1/health
```

如果直连 `8091` 正常，但 `8090/api` 不正常，问题在 Nginx 反向代理。看配置：

```bash
cat /etc/nginx/sites-available/crt
nginx -t
systemctl reload nginx
```

## 6. 调 WebSocket

如果页面实时数据不刷新，需要确认 `/ws`。

设备上如果有 `websocat` 可用：

```bash
websocat ws://127.0.0.1:8091/ws
websocat ws://127.0.0.1:8090/ws
```

没有 `websocat` 时，可先看后端日志：

```bash
journalctl -u crt -f
```

然后刷新浏览器页面，观察是否有 WebSocket 连接和报错。

Mac 浏览器侧：

1. 打开 `http://192.168.1.110:8090/`。
2. 打开开发者工具。
3. 看 `Network -> WS`。
4. 确认 `/ws` 是否连接成功。

## 7. 看日志

服务日志：

```bash
journalctl -u crt -f
journalctl -u nginx -f
journalctl -u energy-hmi-kiosk -f
```

最近 100 行：

```bash
journalctl -u crt -n 100 --no-pager
journalctl -u nginx -n 100 --no-pager
```

Nginx 访问和错误日志：

```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

LightDM / 显示器：

```bash
tail -n 100 /var/log/lightdm/lightdm.log
tail -n 100 /var/log/lightdm/x-0.log
```

内核和硬件：

```bash
dmesg -T | tail -n 100
journalctl -k -n 100 --no-pager
```

## 8. 调配置文件

CRT 配置：

```bash
cat /etc/crt/config.json
```

常见字段：

```json
{
  "dbPath": "/opt/crt/data/crt.sqlite",
  "staticDir": "/opt/crt/frontend",
  "assetsDir": "/opt/crt/assets",
  "bind": "127.0.0.1",
  "port": 8091
}
```

修改后重启：

```bash
systemctl restart crt
```

能源 HMI Nginx 配置：

```bash
cat /etc/nginx/sites-available/energy-hmi
```

修改后：

```bash
nginx -t
systemctl reload nginx
```

## 9. 调 SQLite 数据

CRT 数据库：

```text
/opt/crt/data/crt.sqlite
```

如果设备有 `sqlite3`：

```bash
sqlite3 /opt/crt/data/crt.sqlite '.tables'
sqlite3 /opt/crt/data/crt.sqlite 'select * from events limit 10;'
```

如果没有 `sqlite3`，可以先拷回 Mac 看：

```bash
scp root@192.168.1.110:/opt/crt/data/crt.sqlite ./crt.sqlite
```

注意：不要在服务运行时随意覆盖数据库。要替换数据库，先停服务：

```bash
systemctl stop crt
# 替换或备份数据库
systemctl start crt
```

## 10. 调串口 / RS485 / TCP 设备接口

### 10.1 找设备节点

```bash
ls -l /dev/tty*
dmesg -T | grep -Ei 'tty|serial|rs485|usb'
```

常见设备名：

| 类型 | 可能节点 |
|---|---|
| 调试串口 | `/dev/ttyFIQ0` |
| USB 转串口 | `/dev/ttyUSB0`、`/dev/ttyACM0` |
| 板载 UART | `/dev/ttyS*`、`/dev/ttyAMA*` |

看占用：

```bash
lsof /dev/ttyUSB0 2>/dev/null
fuser /dev/ttyUSB0 2>/dev/null
```

### 10.2 串口工具

如果设备有 `stty` 和 `cat`，可以做基础测试：

```bash
stty -F /dev/ttyUSB0 9600 cs8 -cstopb -parenb -ixon -ixoff
cat /dev/ttyUSB0
```

另一个 SSH 窗口发送：

```bash
printf 'test\r\n' > /dev/ttyUSB0
```

如果有 `minicom` / `microcom` / `picocom`：

```bash
microcom -s 9600 /dev/ttyUSB0
picocom -b 9600 /dev/ttyUSB0
```

设备不能联网时，缺工具就需要提前准备离线包，或用系统已有命令先做最小验证。

### 10.3 TCP 接口

看本机监听：

```bash
ss -lntp
```

连远端 TCP：

```bash
nc -vz <host> <port>
```

监听测试：

```bash
nc -l -p 9000
```

发送测试：

```bash
printf 'hello\n' | nc 127.0.0.1 9000
```

## 11. 调接口时的推荐工作流

1. 先开两个 SSH 窗口。
2. 一个窗口跑日志：

```bash
journalctl -u crt -f
```

3. 另一个窗口发请求：

```bash
curl -v http://127.0.0.1:8091/api/v1/health
curl -v http://127.0.0.1:8090/api/v1/health
```

4. 如果是页面问题，同时开 Mac 浏览器开发者工具，看 Network / Console。
5. 如果是设备通信问题，同时看 `dmesg -T`、串口节点、后端日志。

## 12. 离线环境注意事项

这台设备当前无法访问外网，因此：

- 不要依赖 `apt install` 临时装工具。
- 不要依赖 `pip install` 在线拉包。
- 需要工具时，优先使用系统已有命令：`curl`、`nc`、`ss`、`journalctl`、`dmesg`、`stty`。
- 必须安装工具时，在 Mac 上准备对应架构的离线包，再 `scp` 到设备。
- 应用发布包尽量包含所有运行所需文件，减少设备端在线安装步骤。

## 13. 常用命令速查

```bash
# 服务
systemctl status crt --no-pager -l
systemctl restart crt
journalctl -u crt -f

# Nginx
nginx -t
systemctl reload nginx
tail -f /var/log/nginx/error.log

# 端口
ss -lntp
nc -vz 192.168.1.110 8092

# API
curl -v http://127.0.0.1:8091/api/v1/health
curl -v http://127.0.0.1:8090/api/v1/health

# 硬件
dmesg -T | tail -n 100
ls -l /dev/tty*
```
