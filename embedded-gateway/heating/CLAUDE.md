# heating · 工程纪律

> 跨项目纪律见 [`../../CLAUDE.md`](../../CLAUDE.md)。本文件只补**嵌入式特有**的。
> 板子访问 / SSH / 路由见 [`AGENTS.md`](AGENTS.md)；目录与学习路径见 [`README.md`](README.md)。

## 硬件在环，能上板就上板

- 改 `firmware/` 或 `config/` 后，验证的终点不是「编译过」，而是**在 RK3506 上跑通**。
  - SSH 失败先跑 `scripts/setup_rk3506_macos_route.sh`（路由细节见 AGENTS.md，board = `root@192.168.1.10`）。
  - 设备拓扑：`.10` 板子直连，`.104` 是跳板（见 memory `rk3506-gateway-app`）。
- 改配置发布 / 运行时激活这类闭环逻辑，**先 plan**：列出失败回滚路径再动手。

## 不臆造硬件事实

- 寄存器地址、点表寄存器号、私有 MCU 协议字段——**不确定就标「(待核实)」并去查 datasheet / 抓包**，不要猜一个看起来合理的值。错误的寄存器值会写坏设备。
- 协议 / 点表文档（`docs/protocols/`、`docs/point-table/`）里每个具体数值都要可溯源。

## 文档红线

- **永远不写上游平台名**（viHeating / 英集动力 / Engipower）。一律用「平台」泛指（见 memory `docs-no-named-upstream-platform`）。

## 提交 scope

- 本目录的改动用 `feat(heating): ...` / `docs(heating): ...`，**不要**和投研 / iOS 改动混进同一个 commit 或 branch。
