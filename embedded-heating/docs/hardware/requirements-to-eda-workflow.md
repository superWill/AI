# 客户需求到 EDA 工程的半自动生成流程

这套流程用于把客户的自然语言需求，整理成结构化文档和 CSV，再用脚本生成可编辑的 EDA 工程骨架。推荐目标格式优先使用 KiCad，因为 KiCad 文件是文本格式，适合脚本生成、版本管理和人工复核。

## 目标

把客户需求转换为：

- `requirements.md`：需求规格说明
- `bom.csv`：器件清单
- `nets.csv`：网络连接表
- `connectors.csv`：接口/端子定义
- `placement.csv`：可选，元件初始摆放或区域约束
- KiCad 工程骨架：`.kicad_pro`、`.kicad_sch`、`.kicad_pcb`

这不是一键生成可投产 PCB。自动化结果应作为工程初稿，后续必须由硬件工程师做 ERC、DRC、选型、封装核对、安规、EMC、热设计和布线检查。

## 推荐工作流

1. 收集客户原始需求
2. 整理成 `requirements.md`
3. 从需求中提取模块、接口、电源、通信、传感器、执行器、尺寸、环境约束
4. 生成 `bom.csv`
5. 生成 `connectors.csv`
6. 生成 `nets.csv`
7. 如有机械尺寸或布局要求，生成 `placement.csv`
8. 用脚本生成 KiCad 工程骨架
9. 打开 KiCad 检查原理图、封装、网络和 PCB 初始布局
10. 工程师补全细节并完成布线、校验、生产文件导出

## 给 Codex/Claude 的任务提示词

可以把下面这段直接交给另一个 Codex/Claude 使用：

```text
你是硬件工程助理。请根据客户需求生成一套结构化 EDA 输入文件。

输出文件：
1. requirements.md
2. bom.csv
3. connectors.csv
4. nets.csv
5. placement.csv，如果需求里没有布局信息则生成空模板

要求：
- 不要凭空确定高风险器件；不确定的器件在 notes 字段标注 TBD。
- 所有接口必须列出信号名、方向、电气标准、电压等级和保护建议。
- 所有电源轨必须列出输入范围、输出电压、电流估算和保护需求。
- nets.csv 只写需求中明确或工程常识非常确定的连接；不确定连接放到 requirements.md 的 open_questions。
- 使用 CSV 表头严格遵守我给出的格式。
- 最后给出风险点、待确认问题和下一步建议。

客户需求如下：
[把客户原始需求粘贴在这里]
```

## `requirements.md` 建议结构

```md
# 项目需求规格

## 背景

## 功能需求

## 电源需求

## 通信接口

## 输入输出接口

## 传感器与执行器

## 机械与安装约束

## 环境与可靠性

## 安规与 EMC

## 生产与测试需求

## 初步模块划分

## 待确认问题

## 风险点
```

## `bom.csv` 格式

```csv
ref,value,footprint,mpn,manufacturer,lcsc,quantity,description,notes
U1,STM32F103C8T6,LQFP-48,STM32F103C8T6,ST,C8734,1,主控 MCU,TBD 可替换
C1,100nF,C_0603,,,C14663,1,MCU 去耦,
J1,RS485 Terminal,TerminalBlock_2P,,,C8465,1,RS485 接口,
```

字段说明：

- `ref`：位号，例如 `U1`、`R1`、`J1`
- `value`：阻值、容值、芯片型号或功能名
- `footprint`：封装名，优先使用 KiCad footprint 名称或内部库名称
- `mpn`：制造商型号
- `manufacturer`：制造商
- `lcsc`：立创商城编号，可为空
- `quantity`：数量
- `description`：用途说明
- `notes`：不确定项、替代料、风险说明

## `connectors.csv` 格式

```csv
connector,pin,signal,direction,voltage,standard,description,protection,notes
J1,1,RS485_A,bidirectional,5V,RS485,RS485 A 线,TVS + 共模电感,TBD
J1,2,RS485_B,bidirectional,5V,RS485,RS485 B 线,TVS + 共模电感,TBD
J2,1,24V_IN,input,24V,DC,电源输入正极,保险丝 + TVS + 反接保护,
J2,2,GND,power,0V,GND,电源地,,
```

## `nets.csv` 格式

推荐使用“一行一个引脚”的长表格式，最适合脚本处理。

```csv
net,ref,pin,role,notes
3V3,U1,VDD,power,
3V3,C1,1,power,
GND,U1,VSS,power,
GND,C1,2,power,
RS485_A,U1,PA9,signal,TBD MCU 管脚
RS485_A,J1,1,signal,
RS485_B,U1,PA10,signal,TBD MCU 管脚
RS485_B,J1,2,signal,
```

字段说明：

- `net`：网络名
- `ref`：器件位号
- `pin`：器件引脚名或引脚号
- `role`：`power`、`ground`、`signal`、`shield`、`mount`
- `notes`：不确定连接或设计说明

## `placement.csv` 格式

没有明确布局时可以只生成表头。

```csv
ref,x_mm,y_mm,rotation_deg,side,zone,locked,notes
J1,10,20,0,front,edge,true,靠近外壳端子开孔
U1,50,40,0,front,logic,false,
```

字段说明：

- `x_mm`、`y_mm`：PCB 坐标，单位 mm
- `rotation_deg`：旋转角度
- `side`：`front` 或 `back`
- `zone`：布局区域，例如 `power`、`logic`、`io`、`edge`
- `locked`：是否固定位置

## 脚本生成 EDA 的建议能力

第一阶段脚本只需要生成 KiCad 工程骨架：

- 创建工程目录
- 根据 `bom.csv` 生成器件实例
- 根据 `nets.csv` 生成网络连接
- 根据 `placement.csv` 设置初始位置
- 生成基础板框
- 生成 ERC/DRC 前的待检查清单

不要在第一阶段尝试自动完成高质量 PCB 布线。布线、阻抗控制、隔离间距、铺铜、电源完整性和 EMC 仍应人工处理。

## 生成后的校验清单

- 所有 `nets.csv` 中的 `ref` 是否都存在于 `bom.csv`
- 所有器件是否有封装
- 电源网络是否包含输入保护、稳压、去耦
- 所有外部接口是否有保护器件
- MCU 管脚是否可用，是否冲突
- 通信接口电平是否匹配
- 高压/强电/继电器/电机回路是否与弱电隔离
- 原理图 ERC 是否通过
- PCB DRC 是否通过
- BOM 中停产、扩展库、交期长器件是否标注

## 常见限制

- 只有 BOM 不能生成完整 EDA 工程，只能生成器件清单。
- 只有接口表可以生成连接器和部分网络，但不能确定完整电路。
- 没有封装信息时，只能生成原理图或占位封装。
- 没有坐标和板框时，PCB 只能生成初始摆放，不能得到可生产布局。
- 客户自然语言需求中的“不明确”不能靠脚本硬猜，应进入待确认问题。

## 推荐目录结构

```text
project-name/
  input/
    customer-requirements.md
    bom.csv
    connectors.csv
    nets.csv
    placement.csv
  generated/
    kicad/
      project-name.kicad_pro
      project-name.kicad_sch
      project-name.kicad_pcb
  scripts/
    generate_kicad_from_csv.py
  review/
    open_questions.md
    validation_report.md
```

## 给工程师的交付说明

自动生成的 EDA 文件只代表需求到工程文件的初稿转换。交付给硬件工程师时，必须同时交付：

- 原始客户需求
- 结构化 `requirements.md`
- CSV 输入文件
- 生成脚本
- 生成的 KiCad 工程
- 校验报告
- 待确认问题

