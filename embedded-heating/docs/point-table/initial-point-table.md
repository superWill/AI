# Initial Point Table

This file is a first draft. It should later become `point-table.xlsx` or a machine-readable configuration file.

## Primary Side

| Point ID | Name | Unit | Type | Purpose |
| --- | --- | --- | --- | --- |
| `pri_supply_temp` | 一次侧供水温度 | degC | AI | 判断热源能力和超温保护 |
| `pri_return_temp` | 一次侧回水温度 | degC | AI | 判断换热效果 |
| `pri_supply_pressure` | 一次侧供水压力 | MPa | AI | 一次侧安全监测 |
| `pri_flow` | 一次侧流量 | m3/h | AI/Meter | 热量和换热能力分析 |
| `pri_valve_cmd` | 一次侧调节阀指令 | % | AO/Bus | 控制进入板换的热量 |
| `pri_valve_feedback` | 一次侧调节阀反馈 | % | AI/Bus | 判断阀门是否执行到位 |

## Secondary Side

| Point ID | Name | Unit | Type | Purpose |
| --- | --- | --- | --- | --- |
| `sec_supply_temp` | 二次侧供水温度 | degC | AI | 供温闭环控制 |
| `sec_return_temp` | 二次侧回水温度 | degC | AI | 回温优化和换热分析 |
| `sec_supply_pressure` | 二次侧供水压力 | MPa | AI | 压差控制和高压保护 |
| `sec_return_pressure` | 二次侧回水压力 | MPa | AI | 压差控制和低压保护 |
| `sec_flow` | 二次侧流量 | m3/h | AI/Meter | 循环状态判断 |

## Pumps and Refill

| Point ID | Name | Unit | Type | Purpose |
| --- | --- | --- | --- | --- |
| `circ_pump_run_cmd` | 循环泵运行指令 | bool | DO/Bus | 控制循环泵启停 |
| `circ_pump_run_fb` | 循环泵运行反馈 | bool | DI/Bus | 判断循环泵运行状态 |
| `circ_pump_fault` | 循环泵故障 | bool | DI/Bus | 触发泵故障保护 |
| `circ_pump_freq_cmd` | 循环泵频率指令 | Hz | AO/Bus | 压差控制输出 |
| `circ_pump_freq_fb` | 循环泵频率反馈 | Hz | AI/Bus | 判断变频器执行情况 |
| `refill_pressure` | 补水压力 | MPa | AI | 补水控制输入 |
| `refill_pump_run_cmd` | 补水泵运行指令 | bool | DO/Bus | 控制补水泵 |
| `refill_pump_fault` | 补水泵故障 | bool | DI/Bus | 补水故障保护 |

## System

| Point ID | Name | Unit | Type | Purpose |
| --- | --- | --- | --- | --- |
| `outdoor_temp` | 室外温度 | degC | AI/MQTT | 目标供温曲线输入 |
| `system_mode` | 系统模式 | enum | Param | 自动、手动、本地、远程、维护 |
| `network_status` | 网络状态 | enum | Internal | MQTT 在线/离线 |
| `alarm_level` | 当前告警等级 | enum | Internal | HMI 和 MQTT 上报 |

