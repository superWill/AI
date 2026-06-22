# 配置发布 / 运行时激活 —— 交接说明(handoff)

> [INFERRED][HIGH] 本文是 config_draft → compiler → 版本化产物 → loadable_check → activate(运行中切 live)+ rollback 这条线的交接说明。  
> [INFERRED][HIGH] 设计依据见 `runtime-activate-reload-design.md`;实现在 `heating/prototype/rk3506-app/`(`compiler.py` / `loader.py` / `nexus_server.py`)。  
> [INFERRED][HIGH] 验证基线:`python3 heating/prototype/rk3506-app/tests/test_compiler.py` = **32 passed**(无端口绑定权限的受限沙箱:31 passed, 1 skipped)。

## 1. 这条线现在能做什么

```text
编辑/添加设备(只写草稿)            校验/编译(写版本目录)          运行中激活(切 live)
config_draft ──validate──► versions/N/{point_registry,poll_plan,
   ▲ /config 三段添加设备向导        display_model,safety_policy,app_config.generated}
   │                                          │
   └──────────────── loadable_check(干跑,不碰 live)────┘
                                              │
                            activate(方案B+单飞)──► 运行中切 live ctx ⇄ rollback
                            启动恢复 + 展示同源(active 指针唯一权威)
```

| 能力 | [INFERRED][HIGH] 状态 |
|---|---|
| 后台对账页 `/config` | [INFERRED][HIGH] 只读 status/products/draft + 校验框 + 三段添加设备向导(只写草稿) |
| 版本化 build | [INFERRED][HIGH] `compile` 写 `build/versions/N/`,递增不覆盖;`active` 指针原子写(active.tmp+os.replace) |
| 干跑校验 | [INFERRED][HIGH] `loadable_check`:产物可被 loader 读、source 可构造、快照骨架点位完整 |
| 运行中激活 | [INFERRED][HIGH] `POST /api/config/activate` 真切 live(不重启),`rollback` 回上一版,并发返 409 |
| 启动恢复 | [INFERRED][HIGH] 有 active 则从 `versions/<active>/app_config.generated.json` 起 live,否则回退 `--config` |
| 展示同源 | [INFERRED][HIGH] `--products build` 解析到 `versions/<active>`,Tag 名/类型/卡片与采集 cfg 同源 |

## 2. **已完成:运行中热切的字段**

[INFERRED][HIGH] `activate`/`rollback` 在不重启进程的前提下,原子替换以下内容(方案B:健康检查锁外、锁内只换引用):

| 热切字段 | [INFERRED][HIGH] 载体 |
|---|---|
| 采集 source(设备/点位/轮询任务) | [INFERRED][HIGH] `live_ctx.source`(collector 每轮从 ctx 取) |
| `control_map`(可控点→设定值) | [INFERRED][HIGH] `live_ctx.controller.control_map` |
| `safety_policy`(限值/速率) | [INFERRED][HIGH] `live_ctx.controller.safety_policy` |
| 展示派生(Tag 名/类型/卡片) | [INFERRED][HIGH] 启动时按 active 派生;activate 后需 `--products` 重启才更新(见 §3) |
| `active` 指针 | [INFERRED][HIGH] `build/active`,= live 真实运行版本 |

## 3. **未完成 / 有意不做:进程级 cfg 字段不热切(P0 边界)**

[INFERRED][HIGH] 以下字段**只在启动时从 cfg 读取,activate 不会运行中改变**;要变更需重启进程:

| 不热切字段 | [COMPUTED][HIGH] 原因(代码事实) |
|---|---|
| `poll_interval_s` | [COMPUTED][HIGH] `collect()` 用启动时 `cfg.get("poll_interval_s")`,未随 ctx 更新 |
| `runtime.cfg` / `device_id` | [COMPUTED][HIGH] `Runtime(cfg)` 在启动建一次;activate 只换 source/controller,不换 runtime;遥测 device_id 仍来自启动 cfg |
| `http_port` / `--dist` / 串口 `serial` | [INFERRED][HIGH] 进程级监听/设备路径,启动时绑定 |
| 展示派生(运行中) | [INFERRED][HIGH] `configure_maps` 仅在 `main()` 启动按 active 跑一次;运行中 activate 后 Tag 名/类型不会自动重派生,需重启带 `--products` |
| `app.py`(简版独立 HMI) | [INFERRED][HIGH] 无 compile/activate 管线,整条线只在 `nexus_server.py`;app.py 不受影响也不需要 |

[INFERRED][HIGH] 结论:**P0 若只要求"设备/点位/控制/安全策略运行中切换",本线已可收口**。  
[INFERRED][HIGH] 若要求"所有配置字段热生效"(含 poll 周期、device_id、展示派生运行中刷新),需另立项补"runtime cfg 字段切换 + 运行中重派生展示"设计,不在当前范围。

## 4. 操作方式

```bash
cd heating/prototype/rk3506-app
python3 nexus_server.py --source sim --products build   # 有 active 则从该版本起 live
# 浏览器 http://127.0.0.1:8092/config  登录任意账号
#   → 三段表单添加设备(写草稿)→ 校验 → 编译(出 versions/N)
# 运行中激活/回滚(Bearer 鉴权):
#   POST /api/config/activate {"version":N}   → 不重启切 live
#   POST /api/config/rollback                 → 回上一激活版
#   GET  /api/config/activate/status          → active / live_active_version / 上次激活
```

## 5. 关键文件 / 函数

| 位置 | [INFERRED][HIGH] 职责 |
|---|---|
| `compiler.py` | [INFERRED][HIGH] `validate`/`compile`(纯函数,零依赖手写校验) |
| `loader.py` | [INFERRED][HIGH] `load_runtime_cfg(version_dir)` 产物→扁平 cfg |
| `nexus_server.py` 版本化 | [INFERRED][HIGH] `compile_draft`/`read_active`/`write_active`/`version_summary`/`config_status` |
| `nexus_server.py` 激活 | [INFERRED][HIGH] `RuntimeContext`/`loadable_check`/`activate_compiled_version`(方案B)/`try_activate`(单飞)/`select_startup_config`/`resolve_products_dir` |
| `tests/test_compiler.py` | [INFERRED][HIGH] 32 用例;HTTP 测试用 `unittest.SkipTest` 兜底无绑定权限沙箱 |

## 6. 已知设计待办(实现时再做,均已在设计文档标注)

| 待办 | [INFERRED][HIGH] 出处 |
|---|---|
| modbus 现场可达性:健康检查里判关键点质量码 | [INFERRED][HIGH] 设计 §4.3(loadable_check 用 SimSource,只验结构) |
| 运行中重派生展示映射(Tag 名/类型) | [INFERRED][HIGH] 本文 §3(现需重启 `--products`) |
| runtime cfg 字段热切(poll 周期/device_id 等) | [INFERRED][HIGH] 本文 §3,若 P0 升级需求才做 |

---

[INFERRED][HIGH] 一句话:**设备/点位/控制/安全策略已可运行中热切并回滚,active 指针是 live 真实版本的唯一权威;进程级字段仍需重启**。后续若要全字段热生效,另立项。
