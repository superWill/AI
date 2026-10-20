# RKLB 一手数据 · 2026-10-20

> 公司：Rocket Lab Corp · CIK 0001819994 · 生成：`scripts/fetch_primary.py`。
> 数字原样落盘，不调整；流量科目标 `△` 的是「本期 YTD − 上期 YTD」拆出的单季，查原件时注意。

## 一、SEC XBRL 财务（399 个科目可用）

源：https://data.sec.gov/api/xbrl/companyfacts/CIK0001819994.json

| 科目 | 2024-09-30 | 2024-12-31 | 2025-03-31 | 2025-06-30 | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|---|---|---|---|
| 收入 `RevenueFromContractWithCustomerExcludingAssessedTax` | $104.8M | $132.4M △ | $122.6M | $144.5M | $155.1M | $179.7M △ | $200.3M | $234.1M |
| 毛利 `GrossProfit` | $28.0M | $36.8M △ | $35.2M | $46.4M | $57.3M | $68.2M △ | $76.5M | $84.6M |
| 经营利润 `OperatingIncomeLoss` | $-51.9M | $-51.5M △ | $-59.2M | $-59.6M | $-59.0M | $-51.0M △ | $-56.0M | $-57.5M |
| 净利润 `NetIncomeLoss` | $-51.9M | $-52.3M △ | $-60.6M | $-66.4M | $-18.3M | $-52.9M △ | $-45.0M | $-49.3M |
| 经营现金流 `NetCashProvidedByUsedInOperatingActivities` | $-30.9M △ | $-2.4M △ | $-54.2M | $-23.2M △ | $-23.5M △ | $-64.5M △ | $-50.3M | $-84.1M △ |
| 资本开支 `PaymentsToAcquirePropertyPlantAndEquipment` | $11.0M △ | $21.6M △ | $28.7M | $32.0M △ | $45.9M △ | $49.7M △ | $27.1M | $26.0M △ |
| 现金及等价物 `CashAndCashEquivalentsAtCarryingValue` | — | — | $303.1M | $564.1M | $807.9M | $828.7M | $1.21B | $2.13B |
| 长期债务 `LongTermDebt` | — | — | $345.9M | $346.5M | $347.0M | $152.4M | $36.9M | $13.1M |
| 总债务(含流动) `LongTermDebtCurrent` | — | $12.0M | $20.5M | $16.5M | $17.1M | $0 | — | — |
| 股份数 `CommonStockSharesOutstanding` | — | — | 460.5M 股 | 479.3M 股 | 496.2M 股 | 543.6M 股 | 575.8M 股 | 598.2M 股 |
| 股权激励费用 `ShareBasedCompensation` | $12.9M △ | $16.9M △ | $19.2M | $17.9M △ | $15.7M △ | $18.2M △ | $28.1M | $19.6M △ |

**[COMPUTED] 现金流 vs 利润**（信号⑥读数；capex 取绝对值）

- 2024-09-30：FCF = OCF − capex = $-41.9M；净利 $-51.9M → FCF−净利 = $10.0M；capex/收入 = 11%
- 2024-12-31：FCF = OCF − capex = $-23.9M；净利 $-52.3M → FCF−净利 = $28.4M；capex/收入 = 16%
- 2025-03-31：FCF = OCF − capex = $-82.9M；净利 $-60.6M → FCF−净利 = $-22.3M；capex/收入 = 23%
- 2025-06-30：FCF = OCF − capex = $-55.3M；净利 $-66.4M → FCF−净利 = $11.1M；capex/收入 = 22%
- 2025-09-30：FCF = OCF − capex = $-69.4M；净利 $-18.3M → FCF−净利 = $-51.2M；capex/收入 = 30%
- 2025-12-31：FCF = OCF − capex = $-114.2M；净利 $-52.9M → FCF−净利 = $-61.3M；capex/收入 = 28%
- 2026-03-31：FCF = OCF − capex = $-77.4M；净利 $-45.0M → FCF−净利 = $-32.4M；capex/收入 = 14%
- 2026-06-30：FCF = OCF − capex = $-110.1M；净利 $-49.3M → FCF−净利 = $-60.9M；capex/收入 = 11%

## 二、EDGAR 最近申报（谁在报什么）

表单计数：4×12、144×9、425×7、8-K×5、EFFECT×1、424B3×1、S-4/A×1、424B5×1、S-4×1、10-Q×1、SCHEDULE 13G×1

| 日期 | 表单 | 说明 | 链接 |
|---|---|---|---|
| 2026-10-14 | **8-K** | Current report | [index](https://www.sec.gov/Archives/edgar/data/1819994/000181999426000067/0001819994-26-000067-index.htm) |
| 2026-10-02 | **4** | Statement of changes in beneficial ownership of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000143/0002001011-26-000143-index.htm) |
| 2026-10-01 | **144** | Report of proposed sale of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000195004726009944/0001950047-26-009944-index.htm) |
| 2026-09-15 | **425** | Prospectuses and communications, business combinations | [index](https://www.sec.gov/Archives/edgar/data/1819994/000175392626001771/0001753926-26-001771-index.htm) |
| 2026-09-15 | **8-K** | Current report | [index](https://www.sec.gov/Archives/edgar/data/1819994/000175392626001769/0001753926-26-001769-index.htm) |
| 2026-09-04 | **4** | Statement of changes in beneficial ownership of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000136/0002001011-26-000136-index.htm) |
| 2026-09-02 | **4** | Statement of changes in beneficial ownership of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000135/0002001011-26-000135-index.htm) |
| 2026-09-02 | **144** | Report of proposed sale of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000195004726009032/0001950047-26-009032-index.htm) |
| 2026-08-28 | **4** | Statement of changes in beneficial ownership of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000133/0002001011-26-000133-index.htm) |
| 2026-08-28 | **4** | Statement of changes in beneficial ownership of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000132/0002001011-26-000132-index.htm) |
| 2026-08-27 | **144** | Report of proposed sale of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000195004726008763/0001950047-26-008763-index.htm) |
| 2026-08-27 | **144** | Report of proposed sale of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000195004726008756/0001950047-26-008756-index.htm) |
| 2026-08-27 | **EFFECT** | Notice of Effectiveness | [index](https://www.sec.gov/Archives/edgar/data/1819994/999999999526002771/9999999995-26-002771-index.htm) |
| 2026-08-26 | **4** | Statement of changes in beneficial ownership of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000129/0002001011-26-000129-index.htm) |
| 2026-08-26 | **4** | Statement of changes in beneficial ownership of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000128/0002001011-26-000128-index.htm) |
| 2026-08-26 | **4** | Statement of changes in beneficial ownership of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000127/0002001011-26-000127-index.htm) |
| 2026-08-26 | **4** | Statement of changes in beneficial ownership of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000126/0002001011-26-000126-index.htm) |
| 2026-08-26 | **4** | Statement of changes in beneficial ownership of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000125/0002001011-26-000125-index.htm) |
| 2026-08-26 | **424B3** | Prospectus [Rule 424(b)(3)] | [index](https://www.sec.gov/Archives/edgar/data/1819994/000175392626001639/0001753926-26-001639-index.htm) |
| 2026-08-24 | **144** | Report of proposed sale of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000124/0002001011-26-000124-index.htm) |
| 2026-08-24 | **144** | Report of proposed sale of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000123/0002001011-26-000123-index.htm) |
| 2026-08-24 | **144** | Report of proposed sale of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000122/0002001011-26-000122-index.htm) |
| 2026-08-24 | **144** | Report of proposed sale of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000121/0002001011-26-000121-index.htm) |
| 2026-08-24 | **S-4/A** | Registration of securities, business combinations | [index](https://www.sec.gov/Archives/edgar/data/1819994/000175392626001606/0001753926-26-001606-index.htm) |
| 2026-08-18 | **4** | Statement of changes in beneficial ownership of securities | [index](https://www.sec.gov/Archives/edgar/data/1819994/000200101126000116/0002001011-26-000116-index.htm) |

读法：Form 4 = 内部人已成交；144 = 内部人**拟**出售申报（受限股，先报后卖）；13G = 5% 以上被动持股；13D = 5% 以上主动持股；8-K = 重大事件（财报在这里）；S-8 = 员工股计划登记（稀释来源）。

## 三、USAspending 联邦合同（检索：ROCKET LAB；窗口 2021-10-01 → 2026-10-20）

前 15 笔合同上限合计 $87.0M。Award Amount = 合同上限/义务额，不是当期收入；Total Outlays = 已实际支付。

| 金额上限 | 已支付 | 机构 | 子机构 | 起 | 止 | 说明 |
|---|---|---|---|---|---|---|
| $51.6M | $25.8M | National Aeronautics and Space Administration | National Aeronautics and Spa | 2023-03-29 | 2032-01-27 | VENTURE-CLASS ACQUISITION OF DEDICATED AND RIDESHARE (VADR) UMBRELLA T |
| $14.5M | — | Department of Defense | Department of the Air Force | 2024-04-08 | 2026-05-08 | THE OBJECTIVE OF THE STP-S30 MISSION IS TO DELIVER SCIENTIFIC RESEARCH |
| $10.1M | $10.1M | National Aeronautics and Space Administration | National Aeronautics and Spa | 2020-02-18 | 2023-08-16 | CISLUNAR AUTONOMOUS POSITIONING SYSTEM TECHNOLOGY OPERATIONS AND NAVIG |
| $5.0M | — | Department of Defense | Department of the Air Force | 2025-03-28 | 2026-03-28 | NATIONAL SECURITY SPACE LAUNCH (NSSL) PHASE 3 LANE 1 LAUNCH SERVICES P |
| $2.6M | $2.6M | National Aeronautics and Space Administration | National Aeronautics and Spa | 2021-09-02 | 2024-06-15 | LOW COST EXPENDABLE LAUNCH TECHNOLOGY |
| $960,000 | — | Department of Defense | Department of the Air Force | 2024-09-09 | 2026-01-21 | DIGITAL ENGINEERING APPROACH FOR ARCHIMEDES ENGINE DEVELOPMENT |
| $625,000 | $625,000 | National Aeronautics and Space Administration | National Aeronautics and Spa | 2024-09-27 | 2024-12-26 | CONTRACTOR TO PROVIDE RAPID STUDIES FOR THE MARS SAMPLE RETURN (MSR) P |
| $546,480 | $546,480 | National Aeronautics and Space Administration | National Aeronautics and Spa | 2025-09-26 | 2026-03-13 | THE CONTRACTOR SHALL DEVELOP GEN 1 SOLAR SAIL MISSION CONCEPTS THAT WI |
| $432,665 | $0 | National Aeronautics and Space Administration | National Aeronautics and Spa | 2026-05-28 | 2026-07-31 | DEVELOP GEOSPACE DYNAMICS CONSTELLATION (GDC) TRAILBLAZER MISSION CONC |
| $390,936 | $390,936 | National Aeronautics and Space Administration | National Aeronautics and Spa | 2026-02-23 | 2026-05-24 | MARS END-TO-END COMMUNICATION SERVICE ARCHITECTURES: STUDIES TO ADVANC |
| $261,500 | — | Department of Defense | Department of the Air Force | 2023-05-04 | 2025-05-16 | ROCKET LAB QUINTESSENTIAL STUDIES |
| $25,000 | $0 | National Aeronautics and Space Administration | National Aeronautics and Spa | 2024-04-25 | 2026-01-31 | MINIMUM GUARANTEED |
| $1,000 | — | Department of Defense | Department of the Air Force | 2025-04-09 | 2025-04-14 | FOURTH ON-RAMP FOR EGLIN WIDE AGILE ACQUISITION CONTRACT (EWAAC) VEHIC |
| $500 | $0 | Department of Defense | Missile Defense Agency | 2025-12-29 | 2035-12-28 | SCALABLE HOMELAND INNOVATIVE ENTERPRISE LAYERED DEFENSE (SHIELD) INITI |
| $0 | $9.1M | National Aeronautics and Space Administration | National Aeronautics and Spa | 2022-11-22 | 2023-09-23 | TIME-RESOLVED OBSERVATIONS OF PRECIPITATION STRUCTURE AND STORM INTENS |

## 四、预测市场

### Polymarket

- **What will Rocket Lab USA, Inc. (RKLB) hit in October 2026?**（到期 2026-11-01，成交 $53,506，流动性 $13,125）
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $100 in October? → Yes 1%
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $96 in October? → Yes 1%
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $92 in October? → Yes 1%
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $88 in October? → Yes 1%
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $84 in October? → Yes 1%
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $80 in October? → Yes 1%
- **Rocket Lab’s Neutron Rocket Launch by December 31?**（到期 2027-01-01，成交 $12,409，流动性 $5,313）
  - Rocket Lab’s Neutron Rocket Launch by December 31? → Yes 3%
- **What will Rocket Lab USA, Inc. (RKLB) hit Week of October 19 2026?**（到期 2026-10-23，成交 $5,063，流动性 $10,666）
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $64 Week of October 19 2026? → Yes 6%
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $62 Week of October 19 2026? → Yes 6%
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $60 Week of October 19 2026? → Yes 5%
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $58 Week of October 19 2026? → Yes 9%
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $56 Week of October 19 2026? → Yes 22%
  - Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $54 Week of October 19 2026? → Yes 42%
  - Will Rocket Lab USA, Inc. (RKLB) hit (LOW) $50 Week of October 19 2026? → Yes 83%
- **Rocket Lab (RKLB) Up or Down on October 20?**（到期 2026-10-20，成交 $1,325，流动性 $676）
  - Rocket Lab (RKLB) Up or Down on October 20? → {'Up': '0.41', 'Down': '0.59'}

Kalshi：无匹配盘口。

盘口价是赔率不是事实；流动性 < $50k 的盘别当数据。

---

浏览器才能看的一手源（脚本抓不了）：
- APNIC 各国用户估计：https://stats.labs.apnic.net/cgi-bin/aspop?as=14593 （Starlink AS14593）
- Space-Track 轨道目录（免费注册）：https://www.space-track.org
- FCC ICFS 卫星许可：https://licensing.fcc.gov/myibfs/ · FAA 商业发射许可：https://www.faa.gov/space/licenses
- Cloudflare Radar（免费 token 后可接 API）：https://radar.cloudflare.com/as14593
