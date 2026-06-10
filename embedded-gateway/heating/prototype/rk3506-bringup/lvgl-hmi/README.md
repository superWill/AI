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
> `build.sh` 会从 `lv_conf_template.h` 生成 lv_conf.h 并设 `LV_COLOR_DEPTH=32`(配 DRM XRGB8888)+ 启用 montserrat 28/48 字体。链接 `main.c + cJSON.c + cjk20.c`。

### 中文字体 cjk20.c(已随仓库,如需改字重新生成)
LVGL 字体要预先烘焙成 .c。用 `lv_font_conv`(node)从 Noto Sans CJK SC 子集生成:
```bash
sudo apt-get install -y nodejs npm python3-fonttools
npm i lv_font_conv
# .ttc 是字体集合,先抽出 SC 单字面:
python3 -c "from fontTools.ttLib import TTCollection; c=TTCollection('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'); [f.save('noto_sc.ttf') for f in c.fonts if (f['name'].getDebugName(1) or '').endswith('SC')][:1]"
./node_modules/.bin/lv_font_conv --font noto_sc.ttf --size 20 --bpp 2 --format lvgl --no-compress \
  --range 0x20-0x7F --symbols "温度湿压力流量供回水…(你要用的汉字)" --lv-include lvgl/lvgl.h -o cjk20.c
```
> 标签/页签用 `&cjk20`,大数值仍用 montserrat(数字)。要支持任意中文就把 `--symbols` 换成 GB2312 全集(字体会大些)。

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
- `main.c` — 全部逻辑(DRM/触摸/Modbus/LVGL/cJSON 配置解析/采集线程)
- `cjk20.c` — 中文字体(Noto Sans CJK SC 子集,lv_font_conv 生成)
- `build.sh` — 交叉编译脚本
- `S99zzhmi` / `hmi_start.sh` — 开机自启 + 崩溃重启(启动前 killall 防多实例黑屏)
- `../panel_config.json` — 面板配置(显示/控制哪些点,支持中文标签)
- `../panel-backend/` — 网页配置后台(`config_server.py` + `config.html`,改配置即重载)
- `../sim_config.json` + `../modbus_sim.py` — 陪练:8 设备 Modbus 模拟器(按帧长分帧、支持写)

## 资源占用(实测,RK3506 3核/224MB)
面板 `hmi_lvgl` 仅 **RSS 2.7MB、CPU 近 0**;整机空闲内存 134MB、CPU 96% 空闲。
(对比:kiosk 浏览器要 100MB+ 内存并跑满 CPU,这块低端核扛不住 —— 故选 LVGL 原生。)

## 已完成 ✓
显示(DRM/LVGL)· 触摸(Goodix)· Modbus 读/写 · 配置驱动多页(tabview)·
采集/UI 解耦 · 数据缓存 + 质量色 · 开机自启 + 崩溃重启 · 网页配置后台 · 中文字体

## 待办(按优先级)
- ⭐⭐⭐ **控制写入加限值/联锁**:小屏点错设定值不能出事(安全,目前直接写)。
- ⭐⭐ **配置后台加鉴权**:现在裸开在网络上。
- ⭐⭐ 接**真实 Modbus 表**替换模拟器;拆分"设备配置 vs 面板显示"两段。
- ⭐ 看门狗 `/dev/watchdog`;WiFi/配置后台开机自启;触摸校准;面板热重载(免重启黑屏)。
