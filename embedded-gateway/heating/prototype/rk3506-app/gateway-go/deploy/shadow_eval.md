# 轨 B 阶段一 · 板上影子 eval 运行手册

> 参照决策:**eval 期间板子网关 = `app.py --source modbus --shadow-tap`**(Go 对拍的参照)。
> 期间 edge-os(nexus_server)UI 下线;eval 结束 `shadow_eval_stop.sh` 一键还原。
> 不变量见 [`../docs/track-b-shadow-plan.md`](../docs/track-b-shadow-plan.md):Go 不写寄存器、不接管控制。

## 前提(脚本会预检,不满足即停)
1. 板子已物理接上本机 USB 网卡,Mac 上先跑:`embedded-gateway/heating/scripts/setup_rk3506_macos_route.sh`(需 sudo)。
2. `ssh root@192.168.1.10` 通(vendor 口令 `root`)。多次 ssh/scp 会反复要口令——建议先 `ssh-copy-id` 把公钥推上去免密。
3. **MQTT broker 可选**:
   - 有 `mosquitto`(127.0.0.1:1883)→ 部署脚本走 **MQTT 全功能**:采样 + 命令对账(Go 决策 vs Python command_reply)+ 板外比对器。
   - **无 broker → 自动退 unix-socket 模式**:app.py `--shadow-sock` 把采样经 unix datagram 喂 Go 影子(`--samples-sock`),仅做 **view/资源对比**(无命令流→无决策对账);观测靠 `ssh tail` 影子 stdout 的 30s 摘要。要决策对账就在板上起 mosquitto 后重跑脚本(自动转 MQTT)。
4. 真实 RS485 设备已接好(`--source modbus` 才有现场数据;否则退化成 sim,失去 eval 意义)。

## 部署(Mac 侧,板子接好后)
```sh
cd embedded-gateway/heating/prototype/rk3506-app/gateway-go/deploy
./shadow_eval_deploy.sh            # 预检→推文件→停 nexus→起 app.py --shadow-tap + 影子
```
脚本做的事(**`/userdata` 全程零写入**,app.py + 影子都从 `/tmp` tmpfs 跑):
- 预检:ssh 通 / python3 / broker / 生产配置 `/userdata/rk3506-app/app_config.json` 在 / 二进制架构。
- 推 `app.py gatewayc-shadow-arm` 到板上 `/tmp/gw-shadow/`(tmpfs,断电即清)。
- `/etc/init.d/S99zz-gateway stop` 干净停生产网关(nexus + LCD),启:
  - `python3 app.py --source modbus --shadow-tap --config /userdata/rk3506-app/app_config.json`(单一 RS485 主站,复用生产配置)
  - `gatewayc-shadow-arm shadow --config /userdata/rk3506-app/app_config.json`(只读,写已封死)
- 打印板外比对器启动命令。

## 观测(Mac 侧,长期挂着)
```sh
python3 shadow_compare.py --broker 192.168.1.10 --port 1883 \
    --device rk3506-gw-01 --http http://192.168.1.10:8092 \
    --tol 0.5 --summary-every 60 --out shadow_diff.jsonl
```
- 每 60s 一行 summary:`decision_diffs` / `view_diffs` / `go_rss_kb` / `pending_*`。
- 命中停止条件(track-b §4)即停:**任一 decision_diff**、view 分歧率 >0.1%、告警集合分歧、Go RSS 超阈/崩溃、发现任何 Go→执行器路径。
- `shadow_diff.jsonl` 只在分歧/摘要时落盘(在 **Mac** 上,不写板子 NAND)。

## 还原(一键回滚,零生产副作用)
```sh
./shadow_eval_stop.sh             # 停影子 + 停 app.py + S99zz-gateway start 还原生产
```
因影子不在控制回路,停它不影响供热;app.py↔nexus 切换是网关进程级,collector 重新接管。
`/userdata` 全程未写,tmpfs 上的 app.py/影子断电即清——还原无残留。

## 浸泡周期
连续 ≥14 天,覆盖工作日/周末、昼夜温度循环、≥1 次现场设定值调整与 ≥1 次设备离线事件。期间无未解释 diff 方可进入下一阶段评审(灰度,另行授权)。
