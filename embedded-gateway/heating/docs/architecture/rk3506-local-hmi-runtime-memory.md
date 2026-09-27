# RK3506 本地 HMI 运行记忆

> 更新时间：2026-07-23  
> 适用代码：`heating/prototype/rk3506-app/dashboard.py`、`drm_hmi_v4.py`

## 当前实现

- [KNOWN][HIGH] RK3506 的 800×480 本地触摸屏由 `drm_hmi_v4.py` 直接写 DRM，不依赖浏览器、云端或管理后台。
- [KNOWN][HIGH] 底部导航包含总览、监控、设备、控制和设置；设备页提供独立的“设备接入”和“设备配置”入口。
- [KNOWN][HIGH] “设备接入”建立本机通信配置草稿，保存后以蓝色“配置”卡片显示；没有精确型号通信手册时不得自动启用寄存器采集或写控制。
- [KNOWN][HIGH] 界面采用浅色 EdgeAgent 风格，但运行信息、离线配置和本机控制优先于装饰性图片。
- [KNOWN][HIGH] 正式板端拓扑为 `gatewayc core:8091 + gatewayc ui:8093 + ui_config_proxy:8092 + drm_hmi_v4`。

## 切页卡顿复盘

- [COMPUTED][HIGH] 优化前板端完整渲染中位耗时：总览 1.86s、设备 1.74s、监控 0.88s、控制 0.88s、设置 0.52s。
- [COMPUTED][HIGH] 同期快照请求中位约 18ms，RGB 到 DRM 像素格式转换约 23–29ms，因此网络和颜色转换不是主瓶颈。
- [KNOWN][HIGH] 原因一是 `round_rect()` 对圆角逐像素循环并反复创建字节对象。
- [KNOWN][HIGH] 原因二是 `char()` 对点阵字体逐点调用矩形绘制。
- [KNOWN][HIGH] 原因三是导航点击后同步等待当前页面完成整帧重绘。

## 已实施修复

- [KNOWN][HIGH] 圆角改为水平扫描线批量绘制。
- [KNOWN][HIGH] 字符改为缓存连续像素段，再按段批量绘制。
- [KNOWN][HIGH] 五个导航页面在取得真实设备快照后预热为 XRGB DRM 帧。
- [KNOWN][HIGH] 点击导航时先直接显示缓存帧，随后后台重绘实时数据。
- [KNOWN][HIGH] 页面重绘开始后发生新点击时，旧页面完成的帧不得覆盖新页面。
- [KNOWN][HIGH] 缓存同时保存对应页面的触摸命中区，避免画面与按钮区域错配。

## 修复后基准

| 路径 | RK3506 中位耗时 |
|---|---:|
| 总览完整重绘 | [COMPUTED][HIGH] 513.11ms |
| 监控完整重绘 | [COMPUTED][HIGH] 283.22ms |
| 设备完整重绘 | [COMPUTED][HIGH] 329.83ms |
| 控制完整重绘 | [COMPUTED][HIGH] 222.43ms |
| 设置完整重绘 | [COMPUTED][HIGH] 232.87ms |
| 已缓存帧读取并复制 | [COMPUTED][HIGH] 7.59ms，中位；8.58ms，P95 |

- [INFERRED][HIGH] 用户可见切页响应主要由触摸松手识别、缓存查找和 DRM 帧复制组成，不再等待完整重绘。
- [KNOWN][HIGH] 2026-07-15 部署后板端健康接口为 `ok: true`，LCD 日志能连续收到五个导航页的点击事件。

## 后续修改的硬性检查项

1. [COMMON][HIGH] 不要在触摸回调或切页关键路径中执行网络、串口、文件写入或完整页面渲染。
2. [KNOWN][HIGH] 新增导航页时必须加入帧缓存预热，并缓存与画面匹配的触摸区域。
3. [COMMON][HIGH] DRM 热路径禁止逐像素 Python 循环；圆角、字体、图标和进度条应使用扫描线、连续内存复制或预生成位图。
4. [COMMON][HIGH] 页面渲染必须捕获开始时的页面 ID，提交前再次检查当前页面，防止旧帧覆盖新帧。
5. [COMMON][HIGH] 性能结论必须在 RK3506 实机测量，不能用 Mac 渲染时间代替。
6. [KNOWN][HIGH] 回归测试至少运行 `python3 tests/test_hmi_frames.py`、`python3 tests/test_compiler.py` 和六页 800×480 边界检查。
7. [COMMON][HIGH] 如果已缓存切页再次明显卡顿，先分别测量触摸事件、缓存命中、DRM 写入和后台重绘，不要先归因于网络。

## 当前边界

- [KNOWN][HIGH] 缓存页先显示最近一帧，再由活动页刷新；因此快速切页时允许短暂显示最近数据，而不是阻塞等待最新快照。
- [KNOWN][HIGH] 本地 HMI 仍是纯 Python DRM 原型，不是 LVGL/RGA 硬件加速实现。
- [INFERRED][MED] 如果后续动画、趋势曲线或复杂图片显著增加，应评估 LVGL、RGA 或原生渲染，而不是继续堆叠逐像素 Python 逻辑。

## 三维空间监控 UI 决策

- [KNOWN][HIGH] 2026-07-23 的 Three.js 空间监控评审选定“楼层堆叠”方案，用于同时表达楼层、设备位置和设备状态。
- [KNOWN][HIGH] 原型中的“建筑剖面”和深色“数字孪生”方案已经放弃，底部 A/B/C 方案切换器及键盘左右切换逻辑已经删除，避免用户将其误认为楼层导航。
- [KNOWN][HIGH] 保留的交互包括三维旋转、滚轮缩放、楼层展开、点击设备进入独立详情页和模拟报警定位。
- [KNOWN][HIGH] 设备模型及其“名称＋状态”标签都应能进入同一个设备详情页；详情页的设备 ID 保存在 URL 中，刷新后应保持当前设备。
- [KNOWN][HIGH] 当前原型位置为 `heating/prototype/threejs-building-status-prototype/`，评审结论同时记录在该目录的 `README.md`。
- [KNOWN][HIGH] 当前 Three.js 页面是桌面浏览器原型，不是现有 256MB RAM + 256MB NAND RK3506 DRM HMI 的已实现功能。
- [INFERRED][HIGH] 若将该方案产品化，应面向带浏览器和足够 GPU/内存资源的平台，或按目标硬件能力重新实现；不能直接把桌面浏览器原型部署结论套用到当前 RK3506。

## `/userdata` 持久化存储记忆

### 板端现状与清理记录

- [KNOWN][HIGH] 当前 HD-RK3506-IOT 使用约 256MB SPI NAND，`/userdata` 是独立 UBIFS 持久化分区，总容量仅 16.7MB。
- [COMPUTED][HIGH] 2026-07-15 清理前占用 15.2MB/91%，剩余 1.5MB。
- [KNOWN][HIGH] 清理对象包括部署暂存目录 `_stage`、旧版 `nexus-edge-os-ui`、旧版 `energy-hmi`、厂商测试媒体、旧启动脚本和 Python 缓存。
- [COMPUTED][HIGH] 清理后占用 7.4MB/45%，剩余 9.3MB，共释放约 7.8MB NAND 空间。
- [KNOWN][HIGH] 清理时保留了当前 `rk3506-app`、`gatewayc`、Web前端、设备配置、编译版本、控制令牌、必要日志和蓝牙配对数据。
- [KNOWN][HIGH] 清理后 `gatewayc core`、`gatewayc ui`、`ui_config_proxy` 和 `drm_hmi_v4` 均正常，健康接口为 `ok: true`。

### `/userdata` 准入规则

- [COMMON][HIGH] `/userdata` 只存放运行时会变化、断电后必须保留的数据。
- [COMMON][HIGH] 允许保存设备和网络配置、激活版本指针、控制状态、有限审计日志、容量受控的断网队列、校准数据、证书和当前/上一运行版本。
- [COMMON][HIGH] 不允许长期保存源代码、测试代码、设计截图、QA资源、完整设备手册、重复前端、备用构建二进制、无限增长日志或未设上限的历史数据。
- [COMMON][HIGH] 临时升级和部署文件必须在成功、失败或超时后清理，不能把 `_stage` 当作版本仓库。
- [COMMON][HIGH] 任何新增持久化文件都必须说明所有者、最大尺寸、保留时间、清理条件和掉电恢复行为。

### 推荐目录职责

```text
/userdata/
├── config/       设备、串口、网络和业务配置
├── state/        当前版本、激活指针和运行状态
├── data/         少量必须持久化的数据
├── queue/        有硬上限的断网上传队列
├── log/          有轮转的审计和故障日志
├── versions/     当前版本和上一回滚版本
└── update/       升级临时目录，结束后必须清空
```

### 其他文件的去向

- [COMMON][HIGH] 源代码、测试、设计图和QA文件放在 Mac 项目仓库或远程Git仓库。
- [COMMON][HIGH] 构建包和正式发布制品放在 GitHub Releases 或制品服务器。
- [INFERRED][HIGH] `gatewayc`、静态Web前端、字库和固定词库应优先制作进 Buildroot rootfs 的 `/opt/rk3506-app`，不作为可变用户数据反复部署。
- [COMMON][HIGH] 板型默认配置、开机Logo和OEM固定资源放在 `/oem` 或固件只读区。
- [COMMON][HIGH] 临时解压、截图和中间文件放在 `/tmp`；普通调试日志放在 `/var/log` tmpfs。
- [COMMON][HIGH] 长期遥测、历史曲线和大日志放在云端数据库、TF卡或外接存储。
- [INFERRED][HIGH] 完整设备手册保存在项目文档库；板内只保留经过证据校验的设备模板、必要来源信息和运行映射。

### 已实施的防复发机制

- [KNOWN][HIGH] `deploy/push.sh` 排除测试目录、`gateway-go`备用构建、设计截图、板端截图和设计QA文件。
- [KNOWN][HIGH] 部署成功后自动删除 `/userdata/_stage` 内容。
- [KNOWN][HIGH] `S99gateway-go` 对持久日志采用 64KB 阈值轮转，每个日志最多保留当前文件和一个旧文件。
- [KNOWN][HIGH] 部署过程排除 `data/` 和 `run/`，不得覆盖设备配置或运行数据。
- [COMMON][HIGH] 修改部署、日志、离线队列、OTA或历史存储时，必须检查 `df -h /userdata` 并验证重启后服务和配置完整性。
