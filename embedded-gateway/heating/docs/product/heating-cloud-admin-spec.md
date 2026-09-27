# 供热云服务 + 运营后管 · 详细方案（含流程）

> 用途：定义"网关上报 → 云端落库 → 后台整理优化 → 出报表"的完整方案。
> 交付对象：**供热公司运营**（单租户）。形态：**轻 Web 后管**。
> 版本：2026-06-22（草案）
> 关联：[数据接口契约](../protocols/upstream-platform-data-contract.md) · [云端 ingest 原型](../../prototype/cloud-service/README.md) · [行业语义网关定位](industry-semantic-gateway-positioning.md) · [设备接入两种路径](../architecture/device-onboarding-paths.md)

---

## 0. 设计原则

1. **口径先行**：报表数值口径在纯 SQL 层验对，再做前端。前端只摆"已验对的数字"，不在前端算业务。
2. **预聚合分层**：原始遥测只留近 N 天；报表读"聚合层"（小时/日/结算），不实时扫原始表。
3. **元数据是报表前置**：供热面积、设计参数、改造日期等不在遥测流里，必须后管维护；缺元数据的报表降级/置灰，不出错数。
4. **质量码贯穿**：所有统计只采信 `good` 点，并暴露有效覆盖率——"数据可信"是语义网关的卖点，报表要体现。

---

## 1. 角色与权限（单租户，按站点域授权）

| 角色 | 范围 | 能干什么 |
|---|---|---|
| 管理员 admin | 全部 | 用户管理、站点增删、元数据、全部报表与导出 |
| 运营主管 | 本公司全部站 | 站点元数据维护、报表/导出、报警处理 |
| 值班员 | 授权站点 | 查看监控/运行日报、报警确认 |

> 单租户即"一个供热公司一套"。多公司先用多部署隔离，不做多租户（那是产品化阶段，不在本方案）。

---

## 2. 端到端数据流（全局）

```
 现场 PLC/表计
     │ Modbus/M-Bus
     ▼
 RK3506 网关 ──MQTT(station/#)──► mosquitto ──► ingest_worker ──► PostgreSQL
 (本地控制+采集)   telemetry/alarm/        (broker)     (落原始表)      │
                  heartbeat/reply                                       │
                                                                        ▼
                                              ┌──────────── 聚合层（cron 定时）─────────────┐
                                              │ telemetry_hourly  小时均/极值（已有）        │
                                              │ daily_summary     按日 工况 + 设备状态聚合     │
                                              │ meter_daily       累计量首尾差分（热量/补水）│
                                              │ weather_daily     室外温日均 + 度日数 HDD    │
                                              └──────────────────────┬───────────────────────┘
                                                                     ▼
                                              轻 Web 后管（FastAPI + Vue/Ant Design Pro）
                                              查询聚合 → 报表页 → 导出 Excel/PDF
```

**关键分界**：`ingest_worker` 只负责"忠实落库"；一切业务口径（差分、HDD、设备状态派生、归一化）都在**聚合层 cron**里算，后管只查不算。这样口径改一处（SQL），全后管生效。

---

## 3. 数据模型（在现有 schema 上的增量）

现有 `station / telemetry / telemetry_hourly / alarm / heartbeat` 保留。**新增/扩展**如下：

### 3.1 站点元数据 `station_meta`（报表前置，运营在后管维护）
| 字段 | 含义 | 报表用途 |
|---|---|---|
| device_id | 关联 station | — |
| heat_area_m2 | **供热面积(㎡)** | 单位面积耗热（结算/节能） |
| building_count / household_count | 楼栋数/户数 | 分摊、报表表头 |
| design_pri/sec_supply/return_temp | 设计供回温 | 工况偏离度 |
| design_load_kw | 设计热负荷 | 负荷率 |
| report_interval_s | 上送周期(默认30) | **应收帧基准**（数据完整率） |
| retrofit_date | 改造日期(可空) | 节能"改造前后"基线 |
| commissioned_date | 投运日期 | — |

### 3.2 指标字典 `metric_def`（区分瞬时/累计 + 单位标签）
| 字段 | 说明 |
|---|---|
| metric | point_id，如 pri_supply_temp |
| kind | `instant`（温度/压力/流量瞬时）/ `accumulator`（热量/补水累计） |
| unit / label_cn | 单位、中文名（后管显示 + 报表表头） |

> `kind=accumulator` 的点（如 `heat_total`、`bldg_heat_meter`）走**差分**口径，绝不求平均。

### 3.3 累计量日结 `meter_daily`（cron 生成）
`(device_id, day, metric, first_val, last_val, delta, rollover)` —— 取当日首末 good 读数差分；`delta<0` 判为换表/回零，置 `rollover=true` 并按规则续接。

### 3.4 天气日表 `weather_daily`（cron 生成）
`(device_id, day, outdoor_avg, hdd)` —— `hdd = max(0, 18 − outdoor_avg)`（基准温度可配）。

### 3.5 报警生命周期扩展（在 alarm 表加列）
`status`（active/acked/cleared）、`acked_at/acked_by`、`cleared_at`、`cleared_ts`。
处理时长 = `cleared_ts − ts`。解除来源：① 网关上报 alarm-clear；② 后管人工解除。

### 3.6 设备状态 `device_event` + 派生（**核心维度**）
契约里 `station/{id}/event`（状态突变/快变）此前 ingest **未接**，本期补上——设备状态主要靠它 + 遥测阈值派生：

- **事件表** `device_event(device_id, ts, equip, from_state, to_state, source)`：泵/阀启停、网关上下线、传感器故障等状态翻转。来源 = event 主题 + 由 telemetry 阈值派生（如 `circ_pump_freq_fb` 由 0→>0 判为"泵启动"）。
- **设备清单**（station_meta 关联或约定 point 前缀）：循环泵、补水泵、电动阀、网关本身。
- **派生指标**（进 daily_summary）：各设备 当日 **运行时长 / 启停次数 / 故障次数 / 当前状态**。

> ingest_worker 需新增 `event` 主题处理（现有只接 telemetry/heartbeat/alarm/reply）。

---

## 4. 报表 · 详细口径与生成流程

> 通用过滤：瞬时统计只取 `quality='good'`；每张报表附**有效覆盖率**（good点/应有点）。

### 4.1 运行工况 + 设备状态日报（**核心报表**）
- **维度**：单站 × 日（**不分班次**——按需选时段即可，不做固定班制）。
- **工况字段**：一/二次供回温、**温差 Δt=供−回（计算列）**、流量、压力、阀位、泵频、室外温。
  - 统计：各字段 当日 均值 / 最大 / 最小 / 样本数；偏离度 = 实际供温 − 设计供温。
- **设备状态字段**（来自 §3.6）：循环泵/补水泵/电动阀/网关 各自的
  **当前状态、当日运行时长、启停次数、故障次数**；附当日状态时间线。
- **生成流程**：
  ```
  telemetry ─(每小时 cron)─► telemetry_hourly ─┐
  event + 阈值派生 ─► device_event ────────────┤(每日 cron) daily_summary(工况+设备状态)
                                                ▼
                          运行日报（工况表 + 设备状态卡 + ECharts 曲线/状态时间线）──► 导出 Excel
  ```

### 4.2 热量 / 能耗结算
- **期间供热量** = `期末 heat_total − 期初 heat_total`（meter_daily 差分求和，跨换表用 rollover 续接）。
- **单位面积耗热** = 期间GJ ÷ `heat_area_m2`（GJ/㎡·月，或折 W/㎡）。**缺面积则该指标置灰**。
- **补水量** = 补水累计差分；补水率异常用于漏点预警。
- **生成流程**：
  ```
  telemetry(accumulator点) ──(每日 cron)──► meter_daily(first/last/delta)
                                                │ 后管按月 SUM(delta) ÷ station_meta.heat_area
                                                ▼
                                          结算报表 ──► 导出 Excel/PDF
  ```

### 4.3 节能效果对比
- **气候归一耗热** = 期间GJ ÷ (面积 × Σ HDD)，消除冷暖年差异。
- **对比基线（默认两种都给）**：① 去年同期同比；② 改造前后（以 `retrofit_date` 切分，空则只同比）。
- **生成流程**：
  ```
  meter_daily ─┐
  weather_daily├─► 后管：归一化耗热(现期) vs (基期) ──► 对比图 + 节能率% ──► 导出 PDF
  station_meta─┘
  ```

### 4.4 报警与数据质量统计
- **在线率** = 心跳在线时长 ÷ 总时长（heartbeat）。
- **数据完整率** = 实收帧 ÷ 应收帧；应收 = 时长 ÷ `report_interval_s`；丢帧由 seq 跳变累计。
- **坏点率** = 非good点 ÷ 总点，按 metric 分。
- **报警**：次数 / 按类型 / **平均处理时长**（cleared_ts − ts）。
- **生成流程**：
  ```
  heartbeat ─► 在线率
  telemetry.seq ─► 丢帧/完整率   ──► 数据质量报表 ──► 导出 Excel
  telemetry.quality ─► 坏点率
  alarm(生命周期) ─► 报警统计
  ```

---

## 5. 后管模块与页面

| 模块 | 页面 | 关键操作 |
|---|---|---|
| 登录鉴权 | 登录 | JWT；角色加载 |
| **站点管理** | 站点列表 / 元数据编辑 | 维护面积/设计参数/改造日期/上送周期（报表前置） |
| 实时监控 | 站点总览 / 单站详情 | 嵌 Grafana 或自绘 ECharts；在线状态 |
| 报表中心 | 4 类报表页 | 选站点+周期+类型 → 预览 → 导出 Excel/PDF |
| 报警中心 | 报警列表 | 确认 / 解除 / 备注；按状态过滤 |
| 数据质量 | 质量看板 | 在线率/完整率/坏点率排行 |
| 系统 | 用户管理 | admin 建号、分配站点域 |

---

## 6. 关键业务流程（带流程）

### 6.1 站点接入 + 元数据维护
```
网关首次上报 ──► ingest 自动注册 station(device_id) ──► 后管"站点管理"出现新站(无元数据,标黄)
   ──► 运营录入 面积/设计参数/改造日期/上送周期 ──► 报表口径生效(置灰指标解锁)
```
> 设计取舍：站点**自动发现**（不用手工建台账），但**报表依赖的元数据必须人工补**——把"自动"和"人工兜底"分清。

### 6.2 报警处理闭环
```
现场异常 ──网关 alarm──► ingest 落 alarm(status=active)
   ──► 后管报警中心红色高亮(+可选短信/钉钉推送)
   ──► 值班员"确认"(acked, 记录人/时刻)
   ──► 现场处置 ──► 网关上报清除 或 运营"解除"(cleared, cleared_ts)
   ──► 进入"报警统计"：次数 + 处理时长
```

### 6.3 报表生成 + 导出
```
[后台]每小时/每日 cron 跑聚合(telemetry_hourly/meter_daily/weather_daily)
[前台]运营选 站点+周期+报表类型 ──► 后端查聚合层(不扫原始表)
   ──► 页面预览(表格+图) ──► 点"导出" ──► 后端生成 xlsx/PDF ──► 下载
```

### 6.4 数据质量核账（运营每日一眼）
```
cron 算 在线率/完整率/坏点率 ──► 质量看板按站排行
   ──► 低于阈值的站标红 ──► 关联到具体 metric/时段 ──► 反推现场传感器/网络问题
```

---

## 7. 技术栈与部署

- **前端**：Vue3 + Ant Design Pro（vue-pure-admin 脚手架）+ ECharts。
- **后端**：FastAPI（复用同一 PostgreSQL），JWT 鉴权；导出用 openpyxl(xlsx) / WeasyPrint 或 LibreOffice headless(PDF)。
- **部署**：测试机阶段与 ingest/PG/Grafana 同机；上线后后端单独进程，PG 迁 RDS。Nginx 反代前端 + API，后管 80/443（备案后）或临时端口（免备案期）。

---

## 8. 分阶段实施（交付物 + 验收）

| 阶段 | 交付物 | 验收 |
|---|---|---|
| **A 地基** ✅ | ingest + PG + Grafana（已建） | 模拟器数据入库、看板出数 |
| **B 口径先行** ✅ | station_meta/metric_def/meter_daily/weather_daily/device_event 表 + aggregate.sql + 四类报表 SQL（`prototype/cloud-service/`） | 已在云端 psql 跑通：四张报表数值核对一致（差分/HDD归一/坏点率2%/Δt 均正确），零前端 |
| **C 轻后管** ✅ | FastAPI（JWT 登录/站点元数据/四类报表/报警确认解除/Excel 导出）+ Vue3+Element Plus 单文件前端（`backend/`），8000 端口同源托管 | 已在云端跑通：登录、站点列表、四类报表接口、前端首页均 200 |
| **D 完善** | 报警生命周期 + 数据质量页 + 推送 | 报警闭环可走通、质量看板排行 |

> 强约束：**B 不验对，不进 C**。口径错时纯 SQL 改一行；前端搭完再改要返工整页。

---

## 9. 待确认口径（当前取默认值，请校正）

| # | 口径 | 默认（本方案采用） | 影响 |
|---|---|---|---|
| 1 | 泵"运行"判据 | `circ_pump_freq_fb > 5Hz` 视为运行（阈值可配） | 3.6 设备状态派生 |
| 2 | 纳管设备清单 | 循环泵、补水泵、电动阀、网关 | 3.6、4.1 设备状态 |
| 3 | 节能对比基线 | **同比 + 改造前后都给**（retrofit_date 空则只同比） | 4.3、station_meta |
| 4 | HDD 基准温度 | **18℃** | 4.3 归一化 |
| 5 | 元数据必填项 | 面积为硬必填；设计参数选填 | 报表置灰逻辑 |
| 6 | 报警解除来源 | 人工解除为主，网关 alarm-clear 为辅 | 6.2、处理时长 |

---

## 10. 不做（划界，防 scope 蔓延）
- 多租户 / 对外品牌 / 计费 —— 属产品化阶段，不在本方案。
- 云端下发控制 —— 设定值闭环走已有 MQTT `property/set` 契约，后管只读不在本期做下发 UI。
- AI 负荷预测 —— 数据打好底座后另立项。
