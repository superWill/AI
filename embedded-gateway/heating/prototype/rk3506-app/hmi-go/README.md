# hmi-go — RK3506 本地 LCD HMI(drm_hmi_v4.py 的 Go 移植)

板端 LCD 的 Go 实现。目标是把运行时收敛为单个静态二进制 `hmic`；设备接入页、
触摸状态机和保存即发布编排只在 Go 中实现，不再新增 Python 运行时回退功能。

## 构建 / 测试

```sh
# 开发机跑全部测试(渲染层跨平台,无需板子)
cd hmi-go && go test ./...

# 交叉编译 → ../hmic(32 位 ARMv7 静态,~5.2MB)
sh build.sh

# 上板(hmic 位于 rk3506-app 根,push.sh 自动带上;hmi-go/ 源码不上板)
sh ../deploy/push.sh
```

启动参数:`hmic 8091 [--products <build目录>] [--templates <模板库.json>]
[--touch /dev/input/event0] [--settings <json>] [--backlight <sysfs目录>]`。
LCD 设备页支持从模板库选型号、选已有总线、选从站地址并保存即发布。
init 链要求 `$APP/hmic` 存在；缺席时明确失败，不再回退 Python HMI。

设置页支持10%～100%背光调节与 Light/Dark 配色，写入
`/userdata/rk3506-app/data/hmi-settings.json`，由板端 backlight sysfs 即时生效，
重启后自动恢复。最低亮度保留10%，避免全黑后无法触摸恢复。

## 渲染验证

`tests/golden/` 是防意外变化的回归快照，不是 Go-only 页面正确性的独立证明。
正确性由按钮契约、布局边界、忙碌态和完整字形覆盖等结构测试承担；快照负责发现
未预期的像素变化。

生成候选不会改基准：

```sh
go run ./cmd/golden --case devadd_new
# 先人工检查 /tmp/hmi-golden-candidate/devadd_new.png，再显式接受：
go run ./cmd/golden --case devadd_new --accept --reviewed
go test ./internal/render/ -run TestGolden
```

禁止在 `go test` 内更新 expected；测试路径必须只读。Python 金帧生成器已经正式
退役并会直接失败，避免它覆盖 Go-only 页面的回归快照。

- 比对基于裸 RGB888 缓冲(`.rgb.gz`),不比 PNG 字节(zlib 实现差异)。
- 按钮列表(`.buttons.json`)同帧一起比对。
- 帧不一致时测试输出 diff 像素数/坐标,并写 got/want/diff PNG 到临时目录。
- `ring` 的 atan2 末位 ulp 风险实测未出现(全用例逐字节过);若未来出现,
  按方案启用「环带允差名单」(仅 overview,≤32 像素,坐标限制在已知圆环带)。

## 加字库字形

Go-only 页面新增字形写入独立的 `internal/font/*_glyphs.go`，随后运行
`go test ./internal/font ./internal/render`。不要为了 Go-only 页面修改 Python 字库。

缺字形语义与 Python 一致:不绘制、前进 8×scale 占位。

## 与 Python 版的刻意差异(仅异常路径与存量修复,渲染逐字节一致)

- **控制下发带 X-Control-Token(存量修复,2026-07-16 上板发现):** gatewayc core
  的 /api/command 有控制鉴权,Python 版 post_cmd 从不带 token → 在 Go 核心拓扑下
  LCD 控制一直 401(切 gatewayc 前走 nexus:8092 无此问题,切换后无人发现)。
  hmic 从环境继承 `GATEWAYC_CONTROL_TOKEN`(S99 start() export)并带
  X-Control-Token 头,板上实测 {"ok":true}。

- `config_save` 时 deviceType 不在类型表:Python 会 StopIteration 崩溃,
  Go 用 "设备" 兜底;保存后 id 找不到时 Python 崩溃,Go 保持 slot 不变。
- 控制页点值为非数字字符串时:Python `round()` 抛 TypeError,Go 回退 lo。
- 触摸线程与主循环的共享状态:Python 靠 GIL,Go 用互斥锁 + 渲染输入快照。

## Python 语义陷阱(移植时踩过,改动时注意)

- Python `%` 是地板取模(`floorMod`):slaveId 环绕、slot 环绕、选项环切。
- Python `round()` 是银行家舍入(`math.RoundToEven`)。
- Python 字符串切片按字符(`truncRunes`),Go 原生切片按字节。
- points 的 JSON 对象键序决定像素输出(`Points` 保序解码,勿换成 map)。
- 所有 JSON 解码必须 `UseNumber`(数值原文保真,`fnum`/`str()` 语义依赖)。
- `dict.get(k, def)` 是缺键回退,`d.get(k) or def` 是真值回退,两者不同
  (`nodeGet` vs `orStr`)。
