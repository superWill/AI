# BL410 Energy HMI Prototype Deploy

部署原型 HMI（含设备插拔 → 在线/离线联动）到 BL410，**与 release 版（8092）并存**。

| 角色 | 端口 | 安装路径 | nginx site |
|---|---|---|---|
| release（完整产品 HMI）| 8092 | `/opt/energy-hmi` | `energy-hmi` |
| **prototype（本包）** | **8094** | `/opt/energy-hmi-prototype` | `energy-hmi-prototype` |

## 安装

```bash
cd /tmp/energy-hmi-prototype-bl410
chmod +x install.sh uninstall.sh
sudo ./install.sh
```

## 验证

```bash
curl -I http://127.0.0.1:8094/
```

浏览器：`http://192.168.1.110:8094/`

## 卸载

```bash
sudo ./uninstall.sh
```

Release 版（8092）不受影响。
