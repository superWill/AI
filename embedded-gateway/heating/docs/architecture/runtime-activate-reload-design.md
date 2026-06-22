# 运行时激活 / 重载设计(activate / reload)

> [INFERRED][HIGH] 本文是 activate/reload 的**设计先行**文档,只回答"怎么做才安全",**不含实现**。  
> [INFERRED][HIGH] 评审要求:实现前必须先把版本状态机、事务边界、回滚、旧 runtime 保持策略、API 形状写清楚。  
> [INFERRED][HIGH] 适用:RK3506 供热网关 `heating/prototype/rk3506-app/`(app.py / nexus_server.py 共用内核)。  
> [INFERRED][HIGH] 前置已完成:config_draft → compiler(validate/compile)→ point_registry/poll_plan/display_model/safety_policy → loader → app/nexus/HMI;后台 `/config` 已能编辑草稿/校验/编译/添加设备(只写草稿,不切运行时)。

## 0. 范围与非目标

[INFERRED][HIGH] 目标:把"已编译的某个配置版本"**安全地切成正在运行的配置**,失败可回滚,且不让正在采集的旧 runtime 中断。  
[INFERRED][HIGH] 非目标(P0 不做):双 runtime 长期并行;在线热补丁单设备;跨进程协调;无人值守自动激活。  
[INFERRED][HIGH] 原则:**写文件 ≠ 影响 runtime ≠ 提交成功**,三者必须是分开的、可观察的步骤。

## 1. 版本状态机

```text
draft -> validated -> compiled -> loadable_checked -> activating -> active
                                                          |            |
                                                          +-> failed   +-> rolled_back
```

| 状态 | [INFERRED][HIGH] 含义 | [INFERRED][HIGH] 触碰 runtime? |
|---|---|---|
| `draft` | [INFERRED][HIGH] 草稿落盘(current_draft.json),可继续编辑。 | 否 |
| `validated` | [INFERRED][HIGH] `compiler.validate` 通过,无结构/约束错误。 | 否 |
| `compiled` | [INFERRED][HIGH] `compiler.compile` 产出四件产物 + app_config.generated,写入版本目录。 | 否 |
| `loadable_checked` | [INFERRED][HIGH] 产物能被 loader 读、能构造 source、能生成快照骨架(干跑,不切)。 | 否(只读/构造,不替换) |
| `activating` | [INFERRED][HIGH] 正在把 runtime 输入一次性替换为新版本。 | **是(唯一真正切换点)** |
| `active` | [INFERRED][HIGH] 新版本已成为当前运行配置,旧版本保留为回滚点。 | 是(已切换) |
| `failed` | [INFERRED][HIGH] validate/compile/loadable_check 任一失败;未触碰 runtime。 | 否 |
| `rolled_back` | [INFERRED][HIGH] activating 中途失败,已恢复旧版本继续运行。 | 是(回到旧版本) |

[INFERRED][HIGH] `failed` 与 `rolled_back` 必须分开:前者在切换前失败(runtime 从未变),后者在切换中失败(runtime 动过、已恢复)。

## 2. 事务边界

[INFERRED][HIGH] 把流水线切成三段,边界清晰可观察:

```text
[纯文件阶段]            [干跑阶段]              [切换阶段]
draft/validate/compile  loadable_check          activate
  → 只读写磁盘            → 只构造内存对象         → 替换 runtime 输入
  → 失败 = failed         → 失败 = failed          → 失败 = rolled_back
  → runtime 完全不知情     → runtime 完全不知情      → 唯一影响 runtime 的步骤
```

| 步骤 | [INFERRED][HIGH] 动作 | [INFERRED][HIGH] 是否影响 runtime | [INFERRED][HIGH] 算"提交成功"? |
|---|---|---|---|
| validate | [INFERRED][HIGH] 校验草稿 | 否 | 否 |
| compile | [INFERRED][HIGH] 写 `build/versions/N/*.json` | 否 | 否 |
| loadable_check | [INFERRED][HIGH] loader 读产物 + 构造 source + 生成快照骨架 | 否 | 否 |
| activate(切换) | [INFERRED][HIGH] 在锁内一次性替换 source/控制输入/派生映射 | **是** | 否(还在观察) |
| activate 成功落定 | [INFERRED][HIGH] 更新 `build/active` 指针指向 N,旧版本保留 | 是 | **是(此刻才算提交)** |

[INFERRED][HIGH] "提交成功"的唯一标志 = `build/active` 指针成功指向新版本 N **且** 切换后首轮采集/快照通过最小健康检查。在此之前任何失败都必须回滚。

## 3. 回滚策略

[INFERRED][HIGH] 版本化目录,active 用指针,不就地覆盖:

```text
build/
  versions/
    1/   point_registry.json poll_plan.json display_model.json safety_policy.json app_config.generated.json
    2/
    3/
  active        # 文本文件或软链:内容="2",指向当前生效版本
  current_draft.json
```

| 规则 | [INFERRED][HIGH] 要求 |
|---|---|
| 失败产物隔离 | [INFERRED][HIGH] 新版本始终写到 `versions/N+1/`,**绝不覆盖 `versions/active 所指`**;编译/校验失败的产物留在自己的 N+1 目录,不污染 active。 |
| 切换即换指针 | [INFERRED][HIGH] activate 成功的最后一步才把 `active` 从 N 改成 N+1;改指针是原子写(写临时文件再 rename)。 |
| 回滚 = 反向切换 | [INFERRED][HIGH] rollback 把 runtime 输入换回 `versions/<上一版>`,并把 `active` 指回上一版;复用 activate 的同一套替换逻辑。 |
| 保留窗口 | [INFERRED][MED] 至少保留当前 + 上一版;更早版本可按数量上限清理(RK3506 存储有限)。 |

[INFERRED][HIGH] 任何时刻 `active` 指向的版本必须是"曾经成功跑起来过"的版本;activating 中途崩溃后重启,以 `active` 指针为准恢复旧版本。

## 4. 旧 runtime 保持策略

[INFERRED][HIGH] P0 **不做双 runtime 长期并行**(两套采集线程同时跑会争串口、翻倍负载,RK3506 扛不住也没必要)。  
[INFERRED][HIGH] 采用"旧的继续跑 → 新的先干跑校验 → 通过后一次性替换输入":

```text
t0  旧 source/runtime/controller 正常采集上报
t1  对新版本做 loadable_check(只构造,不替换)——失败则放弃,旧的毫不受影响
t2  activate:在锁内,一次性把 runtime 的"输入引用"换成新版本构造好的对象
t3  观察首轮采集/快照;不健康 → 立即换回旧引用(rolled_back)
```

### 4.1 必须一次性替换的"runtime 输入"(基于现有代码)

[COMPUTED][HIGH] 现状:`collector_loop(source, runtime, interval, stop)` 把 `source` 当**函数参数**捕获(app.py),采集线程持有固定引用;`make_handler` 闭包持有 `controller`,其 `.source/.control_map/.safety_policy` 是可重新赋值的属性;nexus 另有 `configure_maps` 派生的模块级映射(CONTROLLABLE/POINT_LABEL/DISPLAY_*)。

[INFERRED][HIGH] 因此切换必须覆盖这几处,否则会出现"采集用新源、控制用旧限值"的撕裂:

| 输入 | [INFERRED][HIGH] 谁持有 | [INFERRED][HIGH] 切换动作 |
|---|---|---|
| source(设备/轮询) | 采集线程(按参数捕获) | [INFERRED][HIGH] 需经间接层切换(见 4.2),否则要重启线程 |
| control_map / safety_policy | controller 属性 | [INFERRED][HIGH] 锁内重新赋值 controller 的这两个属性 |
| controller.source | controller 属性 | [INFERRED][HIGH] 锁内同步替换 |
| 派生映射(nexus) | 模块级全局 | [INFERRED][HIGH] 锁内重跑 configure_maps(新 point_registry/display_model) |

### 4.2 间接层(RuntimeContext)

[INFERRED][HIGH] 引入一个可变 holder,采集线程与 handler 每轮读它的当前内容,activate 在锁内替换其内容,从而避免重启线程:

```text
class RuntimeContext:
    lock
    source            # 当前数据源
    controller        # 控制器(其 control_map/safety_policy/source 一并更新)
    active_version    # 当前生效版本号

collector_loop:  每轮取 ctx.source.poll()(而非闭包里的旧 source)
activate(ctx, new):  with ctx.lock: 校验新对象就绪 → 原子替换 ctx.source/ctx.controller → 更新 active 指针
```

[COMMON][HIGH] RS485 半双工:采集事务与控制写已共用 `ModbusSource._txn` 锁;切换 source 时必须确保旧 source 没有进行中的事务(在 ctx.lock 与采集间隔之间切,或等当前 poll 返回再换)。  
[INFERRED][HIGH] 切换是"换引用",不是"改正在跑的对象内部",所以旧 source 上的进行中事务能自然收尾;新 source 从下一轮开始被 poll。

### 4.3 loadable_check 与设备通信 dry-run 的分工(重要)

[INFERRED][HIGH] `loadable_check`(第2步)用 SimSource 干跑,只证明:产物能被 loader 读、点位映射完整、能产生快照骨架。  
[INFERRED][HIGH] 它**不证明真串口能打开、Modbus 从站在线**。  
[INFERRED][HIGH] 因此当目标 source 是 modbus 时,activate 在"切换后健康检查"(observe)里必须额外做**设备通信 dry-run**:用新配置实际轮询一两轮,确认关键设备质量码不是 timeout/offline,再提交;否则回滚。  
[INFERRED][HIGH] 即:结构正确性(loadable_check)与现场可达性(comm dry-run)是两件事,前者在切换前、后者在切换后健康检查中。

### 4.4 切换后健康检查的锁粒度(Step 5 接 live 前必须决策)

[INFERRED][HIGH] Step 3 的 `activate` 把 `_post_activate_health(ctx)`(内部 `ctx.source.poll()`)放在 `ctx.lock` 内。  
[INFERRED][HIGH] SimSource 下无碍;但 live modbus 下,这会让全局 ctx 锁覆盖一次串口轮询(可能数百 ms),阻塞 handler 与控制请求。  
[INFERRED][HIGH] Step 5 必须二选一并明确:  
> A. **锁内换引用,锁外做健康检查**:`with lock: 换引用 + 记录旧引用`;释放锁后 poll 健康检查;不健康再 `with lock:` 回滚。窗口期内采集线程可能已用新源采一轮——可接受,但要保证回滚后下一轮恢复。  
> B. **锁内一致性,但缩小锁范围**:只在锁内做"指针交换",健康检查用刚构造好的新 source 的独立实例先 poll(不经 ctx),通过后才进锁交换。  
[INFERRED][HIGH] 另需 **版本 token / 单飞锁** 防止并发 activate:同一时刻只允许一个 activate 在途,后到的拒绝或排队。  
[INFERRED][MED] 倾向方案 B + 单飞:健康检查在进锁前用新 source 独立 poll 完成,锁内只做最短的引用交换,既不阻塞采集也保证一致。

## 5. API 形状

[INFERRED][HIGH] 沿用 `/config` 已有的 Bearer 鉴权;activate/rollback 是会影响 runtime 的写操作,必须鉴权。

| 方法 路径 | [INFERRED][HIGH] 作用 | [INFERRED][HIGH] 返回 |
|---|---|---|
| `POST /api/config/activate` | [INFERRED][HIGH] body 指定要激活的版本号(默认最新 compiled);执行 loadable_check → 切换 → 观察 | [INFERRED][HIGH] `{ok, version, state, errors, status}` |
| `GET /api/config/activate/status` | [INFERRED][HIGH] 当前 active 版本、上一版本、最近一次 activate 的状态机阶段与结果 | [INFERRED][HIGH] `{active, previous, last_activate:{state, version, errors}}` |
| `POST /api/config/rollback` | [INFERRED][HIGH] 切回上一版本 | [INFERRED][HIGH] `{ok, version, state}` |

[INFERRED][HIGH] 现有端点语义不变:validate 只校验、compile 只写版本目录、devices 只写草稿;**activate 是唯一会切 runtime 的端点**。

## 6. 编码顺序(实现时,严格自下而上)

[INFERRED][HIGH] 先把不碰 runtime 的地基铺好,最后一步才真正切换:

| 顺序 | [INFERRED][HIGH] 交付物 | [INFERRED][HIGH] 是否碰 runtime | [INFERRED][HIGH] 判定 |
|---|---|---|---|
| 1 | [INFERRED][HIGH] build/ 版本化:`versions/N/` + `active` 指针;compile 写到 N+1 | 否 | [INFERRED][HIGH] 多次 compile 产生多版本,active 指针正确 |
| 2 | [INFERRED][HIGH] `loadable_check(products)`:loader 能读、能构造 source、能生成快照骨架 | 否 | [INFERRED][HIGH] 坏产物被拦下,好产物返回"可加载",全程不切 |
| 3 | [INFERRED][HIGH] `activate_compiled_version(version)` 纯/服务函数 + RuntimeContext | 否(先在测试 harness 验) | [INFERRED][HIGH] 用假 ctx 单测:替换引用、失败回滚、active 指针更新 |
| 4 | [INFERRED][HIGH] 接 HTTP:activate / activate/status / rollback | 否(逻辑已在 3) | [INFERRED][HIGH] 鉴权、错误返回、状态查询 |
| 5 | [INFERRED][HIGH] 让 app/nexus 的采集线程与 handler 经 RuntimeContext 读取,真正可切 | **是(最后一步)** | [INFERRED][HIGH] live:activate 后 snapshot 变为新版本设备;失败回滚后仍是旧版本 |

[INFERRED][HIGH] 第 1–4 步可全程在测试套件里验证(对应现有 `tests/test_compiler.py` 的纯函数/handler 风格,HTTP 测试用 SkipTest 兜底无绑定权限沙箱)。  
[INFERRED][HIGH] 第 5 步是唯一改变现有 `collector_loop`/`make_handler` 取数方式的改动,改动面最小化为"从 ctx 取 source/controller",并保留旧 app_config 直跑路径作回退。

## 7. 验收(实现完成时)

| 证明目标 | [INFERRED][HIGH] 用例 |
|---|---|
| 纯文件阶段不碰 runtime | [INFERRED][HIGH] compile/loadable_check 期间 snapshot 不变 |
| 切换原子 | [INFERRED][HIGH] activate 后采集/控制同时用新版本,无"新源旧限值"撕裂 |
| 失败回滚 | [INFERRED][HIGH] 注入 loadable_check 失败 → 状态 failed、runtime 不变;注入切换中失败 → rolled_back、runtime 回旧版 |
| active 权威 | [INFERRED][HIGH] activating 中杀进程重启 → 以 active 指针恢复旧版本 |
| 坏产物隔离 | [INFERRED][HIGH] 失败版本目录不覆盖 active 所指版本 |

---

## 8. Step 5 设计补丁:接 live 的 5 个决策(实现前定稿,本节不含代码)

> [INFERRED][HIGH] Step 1–4 已落地:版本化 / loadable_check / activate 函数 + RuntimeContext / HTTP 端点,但全部对 **隔离 sandbox ctx** 操作,响应恒 `wired_to_runtime=false`。  
> [INFERRED][HIGH] Step 5 是第一次真正切 live。下列 5 个决策必须先定稿,把 Step 4 留下的"active=意图版本"语义债收敛掉。

### 8.1 active 的唯一语义

[INFERRED][HIGH] Step 5 后,`build/active` **唯一表示 live 采集/控制正在运行的版本**,不再是"sandbox 意图版本"。  
[INFERRED][HIGH] 推论:`activate` 必须改成操作 **live ctx**(不再是 `_ACTIVATE_CTX` sandbox);Step 4 的 sandbox ctx 与 `wired_to_runtime` 字段在 Step 5 一并退场(active 即权威,`wired_to_runtime` 恒 true 可删)。  
[INFERRED][HIGH] 写 `active` 的时机收紧:**只有 live 引用交换成功后才写**;交换前/健康检查失败一律不写。即"active 被写 ⇔ live 已在该版本"。

### 8.2 健康检查锁策略(采用方案 B)

[INFERRED][HIGH] 采用 §4.4 的方案 B:**健康检查在锁外、用尚未安装的新 source 独立完成;ctx 锁只罩最短的引用交换**。

```text
activate(version):
  loadable_check(version)            # 切前结构校验,不碰 ctx
  new = build_runtime_from_version(version)     # 构造新 source/control_map/safety_policy
  health = new.source.poll() 一到两轮            # 锁外健康检查(modbus 在此判质量码,§4.3)
  if not health: return failed                   # 未触碰 live
  with ctx.lock:                                 # 仅引用交换,绝不在锁内 poll
      old = snapshot(ctx)
      install(ctx, new); ctx.active_version = version
  write_active(version)                           # 交换成功后才提交 active
  return active
```

[INFERRED][HIGH] 采集线程读 `ctx.source` 也需在 `ctx.lock` 内取一次引用(取完即释放,poll 在锁外执行),保证交换原子、且不与采集 poll 互相阻塞。  
[INFERRED][HIGH] 回滚路径收窄:健康检查已前移到锁外,故 `rolled_back` 仅用于"引用交换阶段自身抛异常"这种极少数情况;正常失败都在 `failed`(未碰 live)。

### 8.3 并发策略:activate 单飞

[INFERRED][HIGH] 新增 **activate 单飞锁** `_ACTIVATE_INFLIGHT`(与 `ctx.lock` 不同:前者罩整个 activate 操作,后者只罩引用交换)。  
[INFERRED][HIGH] `activate`/`rollback` 入口 **非阻塞 try-acquire**;已有 activate 在途 → 返回 409 `激活进行中,请重试`,**禁止并发 activate/rollback**。  
[INFERRED][HIGH] 避免两次 activate 交叉写 `active` 或交叉换引用造成撕裂。

### 8.4 启动恢复

[INFERRED][HIGH] `main()` 启动时:**若 `build/active` 存在,从 `versions/<active>/app_config.generated.json` 初始化 live**(source/controller/ctx);**否则回退**到 `--config app_config.json`(旧手写配置,向后兼容)。  
[INFERRED][HIGH] 这让 active 在重启后权威恢复,与 §8.1 "active=live 真实版本"自洽;进程在 activating 中途崩溃,重启以 `active` 为准(未提交的新版本不会被误起)。

### 8.5 `--products` 的新语义

[COMPUTED][HIGH] 现状:nexus 启动 `--products DIR` 从 **扁平** `DIR/point_registry.json`/`display_model.json` 派生 `configure_maps`;版本化后这些扁平文件不再产生。  
[INFERRED][HIGH] 新语义:`--products build` **解析 `build/versions/<active>/`** 读 point_registry/display_model;无 active → 不派生(回退硬编码)。  
[INFERRED][HIGH] 与 §8.4 统一:启动时 live cfg 与展示派生都来自 **同一个 active 版本目录**,不再有"采集用一处、展示用另一处"的不一致。

### 8.6 Step 5 验收(实现时)

| 证明目标 | [INFERRED][HIGH] 用例 |
|---|---|
| active=live 真实版本 | [INFERRED][HIGH] activate 成功后 snapshot 设备/点位变为新版本;activate 前 snapshot 不变 |
| 锁不阻塞采集 | [INFERRED][HIGH] activate 期间采集线程不因 ctx 锁卡住一次串口轮询(锁内无 poll) |
| 单飞 | [INFERRED][HIGH] 并发两个 activate,其一得 409;不出现交叉写 active |
| 启动恢复 | [INFERRED][HIGH] 设 active=N 后重启,live 直接起在 versions/N |
| 展示一致 | [INFERRED][HIGH] `--products build` 后,Tag 名/类型/卡片来自 active 版本,与采集同源 |

[INFERRED][HIGH] 编码顺序(Step 5 内部):先 8.4 启动恢复(读 active 起 live,仍不支持运行中切)→ 再 8.5 展示同源 → 最后 8.2/8.3 运行中 activate 真切 + 单飞。每一小步都能用 live smoke 验证 snapshot 是否如预期变化。

---

[INFERRED][HIGH] 本文只定方向与边界;实现按第 6 节自下而上推进,**第 5 步(真正切 runtime)之前的一切都不影响正在运行的采集**。Step 5 自身按 §8.6 末尾的内部顺序推进,把"碰 live"的风险再切成可逐步验证的小步。
