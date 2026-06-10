# RK3506 本地 LVGL 控制面板(配置驱动)

替代单片机做 HMI 控板:**显示设备状态 + 触摸控制设备**,开机自启。在 800×480 LCD(DRM/KMS)上跑。
面板内容由 `panel_config.json` 驱动(后台/网页配置的单一真相源),不写死。

## 架构要点
- **显示**:板子无 `/dev/fb0`、无 GUI 库、无浏览器、无编译器 → 裸 DRM ioctl(无 libdrm)建 dumb buffer + LVGL 渲染。
- **触摸**:直接读 `/dev/input/event0`(Goodix),喂给 LVGL 指针设备。
- **数据**:Modbus 主站读 `ttyS1`;控制 = 写寄存器(0x06)。
- **采集/UI 解耦**:Modbus 读在独立线程,控制写走命令队列,**UI 线程永不做阻塞 I/O** → 触摸丝滑。
- **配置驱动**:`panel_config.json` 定义多页(tabview)+ 每页 tile(value/setpoint/switch)。加设备/改显示只改配置,代码不动。

## 交叉编译(在 x86 Ubuntu 上,如 192.168.1.104)
```bash
sudo apt-get install -y gcc-arm-linux-gnueabihf
mkdir -p ~/lvgl_hmi && cd ~/lvgl_hmi
git clone --depth 1 -b release/v9.1 https://gitee.com/mirrors/LVGL.git lvgl   # 国内用 gitee 镜像
git clone --depth 1 https://gitee.com/mirrors/cJSON.git t && cp t/cJSON.[ch] . # cJSON
cp <repo>/lvgl-hmi/main.c <repo>/lvgl-hmi/build.sh .
bash build.sh          # 首次编 LVGL→liblvgl.a(慢),之后改 main 只重链接(秒级)
# 产物 hmi_lvgl:ARM 静态二进制,scp 到板子 /root/
```
> `build.sh` 会从 `lv_conf_template.h` 生成 lv_conf.h 并设 `LV_COLOR_DEPTH=32`(配 DRM XRGB8888)+ 启用 montserrat 28/48 字体。

## 部署到板子
```bash
scp hmi_lvgl root@板子:/root/        # 二进制
scp panel_config.json root@板子:/root/
# 开机自启(busybox init,非 systemd):
scp S99zzhmi root@板子:/etc/init.d/   # 杀厂家 lv_demo + 跑面板
scp hmi_start.sh root@板子:/root/      # 守护:崩了自动重启
chmod +x /etc/init.d/S99zzhmi /root/hmi_start.sh
```
更新运行中的二进制(避免 `Text file busy`):`mv hmi_lvgl hmi_lvgl.old` → 写新文件 → 杀进程 → `S99zzhmi start`。

## 文件
- `main.c` — 全部逻辑(DRM/触摸/Modbus/LVGL/配置解析)
- `build.sh` — 交叉编译脚本
- `S99zzhmi` / `hmi_start.sh` — 开机自启 + 崩溃重启
- `../panel_config.json` — 面板配置(显示/控制哪些点)
- `../sim_config.json` + `../modbus_sim.py` — 陪练:多设备 Modbus 模拟器(支持写)

## 待办
- 中文:生成 CJK 子集字体(目前 Montserrat 仅 ASCII)。
- 触摸校准:若点位偏移,加 Goodix 坐标线性映射。
- 后台配置:把 `panel_config.json` 接到网页(energy-hmi)在线编辑。
