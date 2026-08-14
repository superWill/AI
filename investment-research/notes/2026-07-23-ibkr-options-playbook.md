---
date: 2026-07-23
type: playbook（工具纪律）
status: active
purpose: 期权权限确认后的完整纪律——只走两条正道,禁区清单,段永平系统重构,IBKR 机制要点
holder_context: 2026-07-23 用户确认账户有期权权限、可卖 put(此前"不能做期权"硬约束作废,CLAUDE.md 已同步)。触发事件:段永平 7/23 雪球帖(加GOOG/BRK·NVDA体量靠滚动卖put维持·AAPL被call走进T-bill·卖MU/SpaceX/TSLA/PLTR put)
related: ../portfolios/2026-07-23-put-selling-plan.md（执行计划）· 2026-06-25-top-signals-and-panic-discipline.md（为什么禁区是禁区）
memory: ibkr-options-playbook · no-options-trading(已解除)
---

# IBKR 期权 playbook：只有两条正道（2026-07）

## 一句话

**期权在这本书里只是两件工具：cash-secured put = 收钱的限价单，covered call = 收钱的减仓单。判据只有一个——被行权你高不高兴？不高兴就不该卖。** 其他一切玩法（买虚值博方向、裸卖、价差、IV 交易）都在禁区。

## 一、正道两条

### 1. Cash-secured put（收钱的限价单）
- **只对「既定计划本来就要加仓」的票卖**——行权 = 完成计划，不是事故。
- 行权价 = 「今天现金买也乐意」的价，**不是 premium 最厚的价**。想 roll 的冲动 = 当初行权价定错了。
- 现金 100% 担保，担保金买短期 T-bill（双收益：T-bill 利息 + premium；IBKR 现金利息低于 T-bill，别懒）。
- **有底仓的人卖 put 两个结局都是赢**（飞了在车上、跌了折价加仓）；没底仓的人卖 put，踏空是真踏空。

### 2. Covered call（收钱的减仓单）
- 用于**趁强减仓**的既定批次——被 call 走 = 完成减仓，落袋进 T-bill（段永平 AAPL 模板）。
- **克制用**：对右尾肥的票（NVDA 类）卖 call 等于把持有理由卖掉了。只对"本来就要减"的部分卖。
- 权限推定同级可用，首笔前在 IBKR 确认。

## 二、禁区（写死，含理由）

| 禁区 | 为什么 |
|---|---|
| **对正在减仓的内存/SOXX 腿（MU/SKHY/NVDA/TSM）卖 put** | 方向与批 2/3 减仓计划打架;且**行权日 = 组合最痛日**(betaSOXX 0.89,put 被指派的场景就是 SOX 崩的场景,相关性=1 的日子)。段永平能卖 MU put 因为他书里半导体≈0——同一动作两本书两种风险 |
| 半导体高 IV 的 premium 诱惑 | SOX -20% 的 tape 里肥 premium 就是市场为顶部信号 note 追踪的尾部开的价——赚它=给自家火灾卖保险 |
| 买短期虚值博方向 | theta 磨损,赌场业务 |
| 裸卖 call / 用期权放大 SOXX 敞口 | 上尾无限风险 / 组合已 0.89 不需要更多 |

## 三、段永平系统重构（2026-07-23 帖 + 多年雪球帖 `[KNOWN]`）

| 环节 | 他的习惯 |
|---|---|
| 定量 | 行权义务 ≤ 想加的量("保持 NVDA 体量"=put 名义量对应目标敞口) |
| 行权价 | 乐意买入价(GOOG 例:他 Q1 成本 ~$314 一带),不猜底 |
| 担保 | 100% 现金,买成 T-bill |
| 时机 | **恐慌日出手**(2025-04-08 暴跌日单日卖 $8000 万 put),绝不追涨时卖;客观效果=总在 IV 肥时卖但他不是波动率交易者 |
| 期限 | 无教条;用过 1 月年度周期(LEAPS 循环)`[INFERRED MED]`,也有事件驱动短期 |
| 管理 | 不止损、不防御 roll,只接受两个结局:到期作废→继续卖 / 被行权→接货结束 |
| 出场 | 备兑 call 趁强减(AAPL"水果成熟被 call 走→T-bill→现价不接回") |

**13F 盲区提醒**：13F 不披露短 put——他的真实敞口比 13F 大。同理,**自己的短 put 义务必须记 `portfolios/`,否则低估自身敞口**。

## 四、IBKR 机制要点 `[MED,用前核实]`

- 权限:Client Portal→Trading Permissions,按问卷给等级(L1 备兑→L4 裸卖);cash-secured put 现金账户可做,spread/裸卖需 margin。
- 佣金 ~$0.15–0.65/合约;行权/被指派免费。
- 卖方警惕:除息日前深度实值 call 提前指派。
- 工具:TWS OptionTrader / Strategy Builder;挂单用 bid-ask 中间价限价,不追。
- 首笔用 1 张单一标的跑通被行权/保证金全流程再上量。

## 五、与组合的接口

- 执行顺序锁死:**先内存腿批 2/3 趁强减 → 所得进 T-bill → 再对计划内标的卖 put**。卖 put 不是新策略,是既定加仓计划的执行方式升级。
- 每笔短 put 当天记入 [卖 put 计划](../portfolios/2026-07-23-put-selling-plan.md) 的记账表。
