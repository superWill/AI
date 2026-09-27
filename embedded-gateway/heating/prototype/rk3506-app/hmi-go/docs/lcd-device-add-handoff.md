# 交接执行方案:LCD 模板化设备接入(保存即发布)

> 交接对象:任何无本会话上下文的执行代理。所有契约/坑/验收门都在本文档内,
> 不依赖外部记忆。**动手前通读一遍,尤其 §2 红线与 §8 陷阱。**

## 1. 目标与产品裁定(用户已拍板,不要重新讨论)

现场无手机/电脑,LCD 触摸屏是唯一配置入口。在 LCD 上新增「设备接入」页:
**选型号(模板) + 选总线 + 拨从站地址 → 点「保存并发布」→ 设备直接出现在设备列表**。

三条已定的产品决策:
1. 只做 LCD,不做扫码/手机方案。
2. 第一批只带模拟设备模板(source=sim:),机制先行;真设备模板等 datasheet 到货再加。
3. **保存即发布**:用户视角没有"草稿→发布"两段。保存动作自动串完
   `devices→compile→activate` 全链路,靠 activate 自带健康门+失败自动回滚兜底。

## 2. 红线(违反=返工)

- **不臆造硬件事实**:寄存器号/功能码/量程只能来自模板库;LCD 上绝不出现寄存器输入。
  模板库每条必须有 `source` 字段(`sim:`/`datasheet:`/`capture:` 前缀),加载时强制校验。
- **金帧纪律**:所有 LCD 渲染改动,`dashboard.py`(Python)是唯一事实源。
  流程固定:改 dashboard.py → `python3 tools/gen_golden_frames.py` 重生成基准 →
  Go 侧渲染改到 `go test ./internal/render/ -run TestGolden` **逐字节**全过。禁止只改 Go。
- **双端实现**:渲染和编排在 Python(drm_hmi_v4.py,回退实现)与 Go(hmi-go,主实现)都要做。
- 提交规范:`feat(heating): ...`,只在本分支提交,不混其他 scope。

## 3. 工作环境

- **工作目录(唯一)**:`/Users/songzijian/Coding/AI/_wt-hmi-go/embedded-gateway/heating/prototype/rk3506-app/`
  (git worktree,分支 `feat/hmi-go`,已有 7 个提交)。
- **绝对不要碰** `/Users/songzijian/Coding/AI/embedded-gateway/`(主工作区,有其他会话的未提交 WIP)。
- Go 1.23(注意:装不了 x/sys@latest,已钉 v0.30.0);Python 3.14 纯标准库。
- 交叉编译:`sh hmi-go/build.sh` → 产物 `../hmic`(armv7 静态,~5.2MB,gitignored)。

## 4. 当前状态

### 已提交(feat/hmi-go,main..HEAD 共 7 个)
hmi-go 是 drm_hmi_v4.py 的 Go 移植(金帧逐字节对齐);ui_config_proxy 已退役,
gatewayc ui 直连 8092;LCD 旧设备配置页已退役;主题/亮度设置已收编。

### 未提交(本任务已完成的部分,起点就在这)
| 文件 | 状态 |
|---|---|
| `device_templates.json` | 3 个 sim 模板(温度采集/循环泵变频器/安全IO),已过真编译器冒烟 |
| `device_templates.py` | Python 加载+展开($ID/$BUS/$SLAVE 占位符) |
| `hmi-go/internal/templates/templates.go` | Go 加载+展开(与 Python 逐语义对齐,**尚未编译/测试**) |
| `tools/gen_template_fixture.py` | 展开一致性 fixture 生成器(**尚未运行**) |
| `tests/test_compiler.py` | 新增 `test_device_templates_expand_and_validate`,38 passed |

## 5. API 契约(gatewayc ui :8092;nexus_server.py 是对拍规格源码,行号可查)

所有 config 端点要 Bearer:`POST /api/login {"username":"lcd","password":"x"}` → `{"token"}`
(任意账号都发 token,板上已实测)。

| 端点 | 语义 | 关键点 |
|---|---|---|
| `POST /api/config/devices` | `{hardware, business_devices}` 追加进 current_draft + 全量校验 | **无草稿时 400**(见 §7 基线引导);校验失败返回 `{ok:false, errors:[...]}` 草稿不污染 |
| `GET /api/config/draft` | `{has_draft, draft}` | 读 buses 清单/预检 device_id 重复 |
| `POST /api/config/compile` | **草稿在请求体** → validate→compile→写 versions/N + 存 current_draft | 不热切运行时 |
| `POST /api/config/activate` | `{}` 默认激活 latest_version | 单飞锁(409)/健康门失败自动回滚,响应 `{ok, version, state, errors}` |
| `GET /api/config/activate/status` | `{active, latest, live_active_version, last_activate}` | 轮询确认 |
| `POST /api/config/buses` | `{bus}` upsert 总线 | 本期 LCD 不做建总线,只挂现有 |

**编排序列(保存即发布)**:
`login → devices(POST) → draft(GET,拿回更新后全量草稿) → compile(POST 草稿体) → activate(POST {}) → activate/status 轮询到 state=="active"`。
超时:devices/draft 5s、compile 30s、activate 60s(core 重启+健康门)。

## 6. 执行步骤(每步末尾是验收门,不过门不进下一步)

### R1 收尾模板一致性(半小时)
1. `python3 tools/gen_template_fixture.py` → 生成 `tests/golden/templates_expand.json`。
2. 写 `hmi-go/internal/templates/templates_test.go`:加载 `../../../device_templates.json`,
   对 fixture 每条 case 调 `Expand`,marshal 后与 fixture payload 深度相等
   (数字统一 float64 比较,同 golden_test.go 的按钮比对手法)。
3. 门:`cd hmi-go && go test ./internal/templates/` 绿;`python3 tests/test_compiler.py` 38 passed。

### R2 字库补字(半天)
缺 12 字形:`从站保存并布已滚失败选择`(候选文案:从站地址/保存并发布/已发布/失败/发布中/选择)。
1. 下载 GNU Unifont hex(历史验证可用的源:
   `https://unifoundry.com/pub/unifont/unifont-15.1.05/font-builds/unifont-15.1.05.hex.gz`,
   GNU ftp 镜像 404 别试)。按码点提取 64-hex(16x16)追加进 `cjk_font.py` 的 GLYPHS。
2. `python3 tools/gen_font_go.py` 重生成 `hmi-go/internal/font/glyphs_gen.go`。
3. 检查模板 label 的字形覆盖:`python3 -c "from cjk_font import GLYPHS; print([c for c in '温度采集模块循环泵变频器安全IO' if c not in GLYPHS and ord(c)>127])"` — 缺啥补啥。
4. 门:`go test ./internal/font/` 绿(差分测试自动覆盖新字形);已有金帧不受影响
   (`go test ./internal/render/ -run TestGolden` 仍全过——加字形不改现有页面)。

### R3 渲染双端 + 金帧(1 天)
**dashboard.py 先行**(参考 git 历史里退役前的 `page_device_config` 布局风格,
`git show a92c314:embedded-gateway/heating/prototype/rk3506-app/dashboard.py` 可看原版):
1. 新 `page_device_add(fb, form, message, busy, buttons)`:
   - 顶部返回按钮(rect (16,68,86,30),action `config_back`——复用既有 action 名,状态机已有该分支语义:回 nodes 页)
   - 3 行表单(y=108 起,行高 42,风格同退役前):`型号`(模板 label)/`总线`(bus_id)/`从站地址`(数字)
     每行 −/+ 按钮 action `devadd_change`,field ∈ {template,bus,slave},delta ±1
   - 「保存并发布」按钮(rect 同退役前 save (616,406,168,30)),action `devadd_save`;
     busy=True 时该按钮画成灰色(MUTED 底)且**不 append button**(发布中防重复点)
   - 消息行(24,413):message 非空时显示,"已发布"绿,其余红;busy 时固定显示"发布中…"(AMBER)
   - render() 加 `device_add` 分发(签名加 `add_form=None, add_message="", add_busy=False`);
     PAGE_TITLE 加 `"device_add": "设备接入"`;draw_nav 的 active 判定加
     `page == "device_add" and pid == "nodes"`(接入页高亮"设备"标签,同退役前惯例)
   - `page_nodes` 恢复一个「接入设备」按钮(rect (646,66,138,34),action `open_device_add`)
2. `tools/gen_golden_frames.py` 加用例:`devadd_new`(初始态)/`devadd_busy`(发布中)/
   `devadd_error`(message="device_id 重复: temp8ai_9")+ 更新 `nodes` 用例(按钮回归),重生成。
3. Go `internal/render/page_device_add.go` 对齐;`Button` 需要 `Field` 字段回归
   (Marshal 分支:`devadd_change` 带 field+delta;`open_device_add`/`devadd_save` 只带 action)。
4. 门:金帧全过(13 用例);`python3 tests/test_hmi_frames.py` OK(需同步更新它对 nodes 页的
   只读断言——现在 nodes 页有一个 action 按钮了)。

### R4 编排双端 + 本地端到端(1.5 天)
**Go**:
1. `internal/api`:加 `Login() error`(缓存 token)、`AddDevice(payload) (ok, errs)`、
   `GetDraft() (map, hasDraft)`、`Compile(draft) (ok, errs)`、`Activate() (ok, state, errs)`、
   `ActivateStatus()`。Bearer 头;超时见 §5。所有解码 UseNumber。
2. `internal/app/state.go`:
   - `AddForm{TplIdx, BusIdx int; Slave int}`、`AddMessage string`、`AddBusy bool`、
     `Buses []string`(open_device_add 时从 GetDraft 刷新)
   - OnTap 分支:`open_device_add`(拉草稿 buses+重置表单+切页)/`devadd_change`
     (template/bus 环切,slave 1-247 **地板模**环绕)/`devadd_save`/`config_back`(回 nodes)
   - `devadd_save`:置 AddBusy → **spawn goroutine** 跑编排(绝不阻塞触摸线程),
     进度/结果经 mutex 写 AddMessage + Dirty;完成后 AddBusy=false;
     成功:invalidate 全部页缓存 + `s.Page="nodes"`(=「加完就在列表里」);
     失败:留在本页,AddMessage=第一条 error(truncRunes 28)
   - 保存前预检:GetDraft 里 device_id 已存在 → 直接上屏"device_id 重复: xxx",不发请求
   - Publishing 期间 OnTap 忽略 devadd_save(按钮本来不渲染,双保险)
3. `cmd/hmi/main.go`:`--templates`(默认 `/userdata/rk3506-app/device_templates.json`);
   模板加载失败→打日志,设备页不出接入按钮(优雅降级,`open_device_add` 按钮由
   templates 数量>0 才渲染?——**不行,渲染层输入必须与 Python 对齐**;正确做法:
   state 层收到 open_device_add 但模板空时上屏"模板库缺失"消息,渲染不特判)。
4. **Python 回退** `drm_hmi_v4.py`:同流程 urllib + threading.Thread,复用 device_templates.py。
5. **本地端到端(关键,不等板子)**:Mac 上起参照后端
   `python3 nexus_server.py --config app_config.json --dist nexus-dist --port 18092`,
   先 POST 一次 compile(body=samples/heating_draft.json)造出草稿基线,再写一个临时 Go
   小驱动(或单测)把编排跑通:AddDevice→Compile→Activate 全链路断言 ok;重复 slave 断言
   error 上浮。nexus 就是 gatewayc 的对拍源,过了它=过了规格。
6. 门:`go vet ./...`(darwin+GOOS=linux GOARCH=arm GOARM=7 双跑)、`go test -count=1 ./...` 全绿、
   本地端到端脚本双端(Go+Python 回退)各跑通一次、`sh hmi-go/build.sh` 出 armv7 产物。

### R5 部署文件(半小时)
- `deploy/install.sh`:拷 `device_templates.json` 和 `device_templates.py` 到 $APP。
- `deploy/S99gateway-go`:hmic 启动行加 `--products $APP/build`(顺手修复监控页卡片分组;
  Python 回退行同样加 `--products "$APP/build"`)。
- 门:三个 deploy 脚本 `sh -n` 过。

### R6 板上步骤0 + 基线引导 + 验收(半天,**前置:跳板可达**)
板子访问见 §7。顺序:
1. **语义复核**(改代码前就该做,若与 §5 不符→回头改 api 层):curl 实测
   无草稿 devices=400 / buses 端点存在 / compile 吃 body / activate 默认 latest。
2. **基线引导**(一次性):`POST /api/config/compile`(body=samples/heating_draft.json)→
   `POST /api/config/activate`。之后 `GET /api/config/draft` 应 has_draft:true。
3. 部署:hmic 二进制走 /tmp 通道(cat > /tmp/xx.new && mv,**直接覆盖运行中二进制会
   Text file busy**),脚本/模板/py 文件直接 cat 覆盖,`/etc/init.d/S99zz-gateway restart`。
4. 验收(注入触摸,方法见 §7):
   a. 设备页出现「接入设备」→ 进入接入页,三行环切正确,总线来自真实草稿
   b. 加 `循环泵变频器 @ rs485_1 slave 9` → 屏显"发布中…"→"已发布"→ 自动回设备页,
      列表出现新设备(sim 源在线带数据);curl 验证:active 版本+1、snapshot 含
      `pumpvfd_9`、draft 含新硬件
   c. 同 slave 再加 → "device_id 重复: pumpvfd_9" 上屏,active 不变
   d. `reboot` → 新设备仍在,hmic 自启
   e. 全套本地测试基线保持绿
5. 提交(3 个):`feat(heating): 设备模板库+跨语言展开一致性` /
   `feat(heating): LCD 设备接入页渲染(双端+金帧)` /
   `feat(heating): 保存即发布编排+部署+上板验收`。**不要 push**(公开仓+密码问题,用户自己处理)。

## 7. 板子访问与注入触摸

- 板子 `root@192.168.1.10`,经小龙虾跳板。ssh 别名 `rk3506board`(ProxyJump)。
- **当前跳板断链**:我们的跳板 `harbor-27fd0e` 失联,`.227` 被另一台 `harbor-b362a2`
  占了(user/user 可登但到不了板子有线段)。**需要用户物理重启我们的小龙虾**,恢复后
  `ssh rk3506board` 应直通;若 IP 又漂,用 `sshpass -p user ssh user@<新IP>` 逐台
  `hostname` 找 harbor-27fd0e。
- 注入触摸(等价物理点按,写 evdev):板上跑
  ```python
  import struct, os, time
  fd = os.open("/dev/input/event0", os.O_WRONLY)
  def ev(t,c,v): os.write(fd, struct.pack("<IIHHi", 0,0,t,c,v))
  def tap(x,y):
      ev(3,0,x); ev(3,1,y); ev(0,0,0); ev(1,0x14a,1); ev(0,0,0); ev(1,0x14a,0); ev(0,0,0)
  ```
  导航条 y≈460,五个标签中心 x≈192/296/400/504/608(总览/监控/设备/控制/设置)。
- 日志:`tail -f /userdata/rk3506-app/run/lcd.log`([nav]/[ctl] 及新增的发布日志)。

## 8. 陷阱清单(全是本项目实踩)

1. **Python 语义**:`%` 是地板取模(Go 用 floorMod);`round()` 银行家舍入
   (`math.RoundToEven`);字符串切片按字符(`truncRunes`);`dict.get(k,def)` 缺键回退 vs
   `x or def` 真值回退是两回事。
2. **JSON**:一切解码 `UseNumber`;points 键序有语义(已有 Points 保序解码,别动)。
3. **金帧比对**基于裸 RGB(`.rgb.gz`),失败时测试会输出 diff 坐标+写调试 PNG 路径。
4. **gofmt**:提交前 `gofmt -l .` 必须无输出;生成器产物也要过 gofmt。
5. 板上 NAND 仅 17MB:二进制更新永远走 /tmp(tmpfs)中转。
6. 文件里有**全角冒号/中文标点**,字符串替换前先精确读原文,别凭假设写 old_string。
7. `hmic` 无 `--config-base` 参数(已随代理退役删除),不要加回。
8. 触摸线程与主循环共享 State 靠 mutex;新增字段一律锁内访问;RenderInputs 返回快照。
9. render 层输入只能来自 Render 参数(纯函数),不要在渲染里读全局可变状态
   (displayCards/主题色是既有例外,有 ConfigureDisplay/ApplyTheme 管理)。
10. activate 期间 core 重启,snapshot 会 502/拒绝几秒——主循环已容忍,别当 bug 修。

## 9. 验证命令速查

```sh
# 全量(在 rk3506-app/)
python3 tests/test_compiler.py          # 期望 38+ passed
python3 tests/test_hmi_frames.py        # OK
python3 tools/gen_golden_frames.py      # 重生成金帧(改 dashboard.py 后)
python3 tools/gen_template_fixture.py   # 重生成模板 fixture(改模板库后)
python3 tools/gen_font_go.py            # 重生成 Go 字库(改 cjk_font.py 后)
cd hmi-go && gofmt -l . && go vet ./... && GOOS=linux GOARCH=arm GOARM=7 go vet ./... \
  && go test -count=1 ./... && sh build.sh
```
