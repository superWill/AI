# 灯控单片机需求说明

## 目标

在智能 CPS 主控板原理图中增加一个用于灯控制的 8 脚单片机功能块。当前实现为 `STM8S003` 原理图符号，占位用于后续确认准确型号、封装和引脚映射。

## 功能需求

- 支持一路灯开关控制
- 支持一路 PWM 调光控制
- 支持一路灯状态/电流反馈采样
- 支持一路按键或外部触发输入
- 支持一路状态指示灯输出
- 支持复位和调试/烧录接口

## 电源需求

- MCU 工作电源：建议 3.3V 或 5V，最终以具体 STM8S003 型号 datasheet 为准
- 必须就近放置去耦电容，建议 `100nF + 1uF`
- 电源网络需和现有主控板电源命名保持一致

## 引脚定义

当前 8 脚占位定义如下：

```text
1  VDD           Power
2  GND           Power
3  NRST/SWIM     Input
4  LIGHT_PWM     Output
5  LIGHT_EN      Output
6  LIGHT_FB_ADC  Input
7  KEY_IN        Input
8  STATUS_LED    Output
```

## 后续待确认

- 具体器件型号是否确认为 8 脚 `STM8S003`，还是实际应为 `STM8S001/STM8S003` 兼容型号
- 具体封装，例如 SOP-8、TSSOP-8 或其他
- 真实 datasheet pinout 与当前功能分配是否一致
- 灯负载类型：LED、小功率指示灯、MOS 管驱动灯带、继电器灯控或外部驱动模块
- PWM 频率、调光范围和调光方式
- 灯反馈采样是电流、电压还是故障状态
- 是否需要 ESD、过流、短路、反接或浪涌保护

## EDA 实现说明

生成文件：

```text
/Users/songzijian/Downloads/ProPrj_智能CPS_2026-05-25.light-mcu.stm8s003.auto-layout.epro
```

工程修改：

- 主控板 `Schematic1 / P1` 新增 `U99 / STM8S003`
- 符号 ID：`3280030000000002`
- 器件 ID：`3280030000000001`
- 当前未绑定封装
- 当前设置 `Convert to PCB = no`

布局策略：

- 脚本读取已有组件坐标和符号 BBOX
- 忽略图框/标题栏大对象
- 对已有元件占用框做碰撞检测
- 自动选择主控板中上部控制/接口分区附近空位
- 当前位置：`x=820, y=910`

## 工程师检查清单

- 确认 8 脚型号和 pinout
- 确认封装并补充 footprint
- 确认 `LIGHT_PWM` 和 `LIGHT_EN` 是否需要外部 MOS/驱动器
- 确认 `LIGHT_FB_ADC` 的输入范围和保护电路
- 确认 `NRST/SWIM` 调试接口是否需要单独连接器或测试点
- 补齐电源去耦、电平匹配和保护电路
- 确认后再把 `Convert to PCB` 改为 `yes`

