# RK3506 Migration Research

本目录用于调研“用 RK3506 嵌入式平台替代原 GD32F407VET6 单片机消防主机方案”的业务、产品、技术和合规问题。

核心问题不是简单换主控，而是判断：

1. 原单片机承担的采集、报警、联动、显示、按键、通信职责，哪些可以迁移到 RK3506。
2. 哪些职责必须保留实时、安全、可认证的独立链路。
3. 嵌入式平台带来的可定制 HMI、联网、日志、远程维护、AI 安防扩展，如何不破坏消防主机的认证边界。

## Current Hypothesis

RK3506 适合作为“消防主机的新一代嵌入式平台”，但不应把所有安全关键逻辑都放在普通 Linux 用户态里。

更稳的方向：

- RK3506 Cortex-A7/Linux：HMI、配置、日志、联网、Web/图形界面、远程维护、AI 扩展。
- RK3506 Cortex-M0 或外置低成本 MCU/FPGA：二总线时序、关键采集、联动输出、看门狗、安全退化。
- 独立硬件保护：总线短路保护、继电器输出保护、主备电切换、硬件钥匙/急停/手动优先链路。

## Documents

- `01-user-notes.md`：当前访谈/现场信息原始整理。
- `02-expert-analysis.md`：从消防产品专家角度拆解业务、产品和架构。
- `03-rk3506-vs-gd32f407-checklist.md`：RK3506 替代 GD32F407VET6 的资源和风险核查表。
- `04-next-research-questions.md`：下一轮需要问客户/硬件/认证机构的问题。

## Source References To Verify

- Rockchip RK3506 官方产品页：`https://www.rock-chips.com/a/cn/product/RK35xilie/2025/1208/2125.html`
- 国家标准全文公开系统 GB 4717-2024：`https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=275D6E9A825C05AC86D4B2E4396E36DC`
- GB 4717-2024 发布说明：`https://hxcccf.com/index.php/show/1.html`
- 本项目既有合规文档：`../business/compliance.md`
