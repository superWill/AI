# BL410 Energy HMI Deploy

这个部署包用于把 `embedded-heating` 的能源管控 HMI 原型安装到 BL410 设备。

默认访问地址：

```text
http://192.168.1.110:8092/
```

安装：

```bash
cd /tmp/energy-hmi-bl410
chmod +x install.sh uninstall.sh
./install.sh
```

验证：

```bash
curl -I http://127.0.0.1:8092/
```

切到默认 80 端口前，应先确认不再需要 Apache 或其他应用占用 `80`。
