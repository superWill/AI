# Go↔Nexus 边界 + nexus 重构方案(设计稿,未实施)

> 目标:Go(`gatewayc`)接管网关核心后,`nexus_server.py` 从「内嵌核心」重构成「gatewayc 的客户端」。
> 范围背景见 [`replacement-scope-and-gaps.md`](replacement-scope-and-gaps.md) §1a。**仅设计,待评审后实施。**

## 1. 当前耦合(要解开的)
`nexus_server.py` 现在把核心**内嵌在同进程**:
- `from app import Runtime, SimSource, ModbusSource, Controller`(L26);
- `collect()`:`runtime.update(src.poll())`(L901)——**自己当 RS485 主站轮询**;
- `make_handler(runtime, live_ctx, hub, dist, endpoint, tokens)`——HTTP 直接读内嵌 runtime、写内嵌 controller;
- `build_nodes_tags(view, endpoint)`(L520)——把 runtime `view` 译成 edge-os nodes/tags;
- `try_activate(live_ctx, ...)`——运行中**热切内嵌** source/controller/safety_policy + active 指针。

## 2. 目标拓扑
```
        ┌─────────── gatewayc run (Go,核心) ───────────┐
RS485 ──┤ 唯一总线主站:采集/控制/安全/Runtime/MQTT      │
        │ HTTP(:8091):/api/snapshot ·/api/stream(SSE) │
        │            ·/api/command ·/api/health         │
        └───────▲───────────────▲───────────────────────┘
   读快照(SSE/poll)│         │下发控制(POST /api/command)
        ┌───────┴───────────────┴──── nexus_server.py(Python,适配层,:8092) ───┐
        │ 不再 import app、不再轮询总线;消费 gatewayc                          │
        │ 保留:edge-os socket.io · 登录/Bearer · 配置 draft/compile/版本管理   │
        │       · /api/tags/write→gatewayc · /api/init · /config UI            │
        └──────────────────────────────────────────────────────────────────────┘
   LCD(drm_hmi_v4)──读 gatewayc:8091/api/snapshot(本地直连,少一跳)
```
**单一总线主站 = gatewayc**;nexus 不再 poll source,故**无双主冲突**(这正是重构的目的)。

## 3. 集成点 × 选定方案
| 集成点 | 现状(内嵌) | 重构后 |
|---|---|---|
| **快照/遥测**(北向读) | nexus collect 轮询 source → runtime.view() | nexus 消费 **gatewayc `/api/stream`(SSE 推送)** 或 poll `/api/snapshot`;把得到的 view 喂现成的 `build_nodes_tags(view)`(几乎不改) |
| **控制**(北向写) | `/api/tags/write`·`/api/command` → controller.apply(内嵌) | → **POST gatewayc `/api/command`**(Go controller 做安全/决策/写);nexus 只转发 + 译错误 |
| **配置 draft/compile** | nexus compile_draft 写 build/versions/N(纯文件) | **不变,仍 Python**(compiler.py/loader.py 已对拍一致;产物含 app_config.generated.json) |
| **配置 activate/rollback** | try_activate 热切内嵌 live_ctx | **见 §4(关键决策)** |
| **LCD** | 读 nexus:8092/api/snapshot | 读 **gatewayc:8091/api/snapshot**(本地直连) |
| **登录/鉴权/edge-os UI** | nexus 自有 | **不变,仍 Python** |

## 4. 关键决策:配置激活怎么落到 Go 核心(D1)
现 activate 是「运行中热切**内嵌 Python** 的 source/controller/safety」。Go 当核心后,activate 必须作用到 **gatewayc**。两条路:

- **方案 A(推荐):active 指针翻转 + 受监督的 gatewayc 重启 + 启动健康门 + 回退。**
  nexus 仍管 draft→compile→versions/N→写 active 指针(复用已建的 Step1–5 版本化机制);
  activate = 原子翻 active 指针 → 通知 supervisor 用新 active 版本**重启 gatewayc** → 启动健康门(采集/HTTP/MQTT/关键设备就绪)过了才算成功,不过则回退到上一 active 重启。
  - 代价:配置变更时 gatewayc 重启 ~1–2s 采集间隙 + 丢内存态(seq/缓存)。配置变更**低频**,可接受。
  - 好处:**几乎零新 Go 代码**;复用 supervisor + 健康门(本就要建);回退 = 重启上一版,简单可靠。
- **方案 B:把 RuntimeContext 热切移植到 Go**(gatewayc 加 activate/rollback/status 端点,锁内换 source/controller/safety,零间隙)。
  - 代价:把 nexus 的 §8 方案B 热切逻辑用 Go 重写一遍,工作量大、风险高。
  - 好处:配置变更零采集间隙。

> **建议 A**:配置变更罕见,1–2s 间隙换「几乎不写新 Go 核心代码 + 复用监督/回退」非常划算;真有零间隙硬需求再上 B。

## 5. nexus 重构 delta
- **删**:`from app import ...`;`collect()` 轮询;内嵌 Controller/RuntimeContext/source;`try_activate` 的进程内热切。
- **加**:gatewayc 客户端(SSE/poll 取 view + POST /api/command);`build_nodes_tags`/`configure_maps`/socket.io hub/登录/config UI **原样复用**(它们本就只吃 view/产物文件)。
- **改 activate**:从「热切内嵌」改成「翻 active 指针 + 请 supervisor 重启 gatewayc(方案 A)」。
- **端口**:nexus 留 :8092(edge-os URL 不变),gatewayc 用 :8091(核心)。

## 6. 增量实施步骤(每步可验证,不大爆炸)
1. gatewayc 固定核心端口 :8091;确认 `/api/snapshot`·`/api/stream`·`/api/command` 满足 nexus 所需字段。
2. nexus 加「gatewayc 客户端」取数模式(开关切换:内嵌 vs 远程);先**并行对账**——同一 view 两路 build_nodes_tags 应一致。
3. 切 nexus 取数到 gatewayc(SSE),停用内嵌 collect;`/api/tags/write`·`/api/command` 转发到 gatewayc。**此时 nexus 不再当总线主站**。
4. 实施 supervisor + 启动健康门 + active 指针重启(方案 A),把 activate/rollback 改成「翻指针 + 重启 gatewayc」。
5. LCD 指向 gatewayc:8091。
6. S99 改为:supervisor 起 gatewayc(读 active 版本)+ nexus(:8092)+ LCD。

## 7. 待你拍板
- **D1**:激活机制 = 方案 A(指针+重启+健康门,推荐)还是 B(Go 热切零间隙)?
- **D2**:端口 = gatewayc:8091 / nexus:8092(推荐,edge-os URL 不变)?还是别的分配?
- **D3**:配置编译留 Python(compiler.py/loader.py,推荐)还是改用 `gatewayc compile/load`?
- 注:本重构**不接真实设备、不替换控制器**——只是把 nexus 从内嵌核心改成 gatewayc 客户端;真正切生产仍走影子→灰度→验收。
