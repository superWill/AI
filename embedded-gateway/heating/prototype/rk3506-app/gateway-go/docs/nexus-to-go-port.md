# nexus_server.py → Go 移植方案(板上零 Python)

> 目标:消除板上最后一层 Python(nexus = edge-os UI + socket.io + 登录 + 配置管理),
> 板上只剩 `gatewayc`(Go)+ `hmi_lvgl`(C 原生屏)。增量做、每步对拍 Python nexus。

## 架构:`gatewayc ui` 子命令(独立 Go 进程)
新增 `gatewayc ui --core-url http://127.0.0.1:8091 --port 8092`,**替掉 `python nexus_server.py`**:
- 消费 gatewayc 核心:取 `/api/snapshot`(SSE/poll)→ Go 版 build_nodes_tags;控制转发 `/api/command`(带 X-Control-Token)。
- 服务 edge-os:REST + 自实现 socket.io(Engine.IO v4/Socket.IO v5 polling)+ 登录 + 配置 UI + 静态 dist。
- **核心/UI 隔离**(UI 崩不拖垮控制核心)+ 零 Python。supervisor 只把 nexus 那行换成 `gatewayc ui`。

为何不折叠进 gatewayc:核心进程要稳,UI(socket.io/网页)是 attack surface + 易变,隔离更安全;且独立进程便于灰度切换。

## nexus 全表面(1120 行)
| 块 | 端点/职责 | 移植难度 |
|---|---|---|
| 登录/鉴权 | `/api/login`(发 token)、`_authed`(Bearer 校验) | 低 |
| edge-os REST | `/api/init`·`/api/me`·`/api/tags/write`·`/api/nodes`·`/api/snapshot`·`/api/scada`·`/api/history` | 中(含 build_nodes_tags) |
| socket.io | `/socket.io/`(EIO4 polling):new_session/poll/handle_post/broadcast;推 tag-change/node-change/system-metrics | **高**(自实现协议) |
| 配置管理 | `/api/config/{status,products,draft,validate,compile,devices,activate,rollback}` + `/config` 页 | 中(compile/load 已是 gatewayc;activate 已是指针+重启) |
| 静态 | edge-os dist(nexus-dist) | 低 |

## 增量步骤(每步对拍 Python nexus,同请求→同响应)
1. **Go build_nodes_tags + 登录**:Go 版 view→nodes/tags(对拍 Python build_nodes_tags 结构)+ `/api/login`/`_authed`。
2. **edge-os REST**:`gatewayc ui` 服务 /api/init·/api/me·/api/tags/write·/api/nodes·/api/snapshot(取数自 gatewayc,控制转发);curl 对拍 Python nexus 同端点。
3. **socket.io 服务器**:Go 实现 EIO4/SIO5 polling(handshake/poll/post/broadcast)+ broadcaster 推三事件;用 socket.io 客户端对拍握手+收事件。
4. **配置管理 UI**:/api/config/* 接 gatewayc compile/load + active 指针 + activate(指针+重启,复用 supervisor)+ /config 页 + 静态 dist。
5. **切换**:supervisor/S99-go 把 `nexus_server.py` 换成 `gatewayc ui`;板上删 Python。edge-os 浏览器/LCD 指向 `gatewayc ui`。对拍整页可用后,nexus_server.py 退役。

## 对拍方法
每步:同一请求分别打 Python nexus 与 `gatewayc ui`,比响应(结构/值,数字按值、数组多重集——同编译器对拍标准)。socket.io 用真 socket.io 客户端验握手+事件流。CI 加 ui 对拍 job。

## 边界(不变)
- gatewayc 核心(采集/控制/安全/MQTT)不动;`gatewayc ui` 只读核心 + 转发控制。
- hmi_lvgl(C 原生屏)不在本移植范围。
- 控制仍走 gatewayc 强鉴权(token);UI 登录是 edge-os 前端那层。
