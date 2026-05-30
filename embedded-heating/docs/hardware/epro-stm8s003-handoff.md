# 智能 CPS EPro 修改交接说明

## 背景

原始工程是嘉立创 EDA 专业版 / EasyEDA Pro 的 `.epro` 工程包。需求是在主控板原理图里新增一个 8 脚 `STM8S003` 单片机符号，并保证导入嘉立创 EDA 专业版后能看见、名称正确、位置不和已有元件重叠。

## 当前最终文件

最终建议导入这个文件：

```text
/Users/songzijian/Downloads/ProPrj_智能CPS_2026-05-25.stm8s003.auto-layout.pcb-fixed.epro
```

这个版本已经确认：

- 包内不包含旧名称 `STM328S003`
- 包内包含 `STM8S003`
- 主控板原理图里有实例 `U99 / STM8S003`
- 位置为 `x=820, y=910`
- 三个 PCB 文件头均为 `["DOCTYPE","PCB","1.8"]`
- ZIP 完整性校验通过

## 关键坑点

### 1. 不能只改 `project.json`

只在工程库里新增器件和符号，嘉立创 EDA 打开后不一定能在原理图页面看到。必须同时在对应 sheet 的 `.esch` 文件里新增 `COMPONENT` 实例。

本次目标 sheet：

```text
SHEET/12aaf30d1f2f6473/1.esch
```

它对应主控板的 `Schematic1 / P1`。

### 2. 自定义 ID 不能随便写

一开始用了类似：

```text
stm328s003_mcu_8pin
stm328s003_sym_8pin
```

嘉立创专业版能导入但会忽略/不显示。后来改成工程里常见的 hex 风格 ID 后才稳定显示：

```text
Device UUID: 3280030000000001
Symbol UUID: 3280030000000002
Symbol file: SYMBOL/3280030000000002.esym
```

### 3. 原始主控板 PCB 文件有坏前缀

原包里主控板 PCB：

```text
PCB/1cc7b6d1a1f45d63e1506124d7c27d1c.epcb
```

文件前面混入了封装段，导致开头是：

```json
["DOCTYPE","FOOTPRINT","1.8"]
```

嘉立创导入时报过：

```text
Cannot read properties of undefined (reading 'uuid')
```

修复方式是裁掉前面的错误封装段，从真正的：

```json
["DOCTYPE","PCB","1.8"]
```

开始保留。

### 4. 没有封装时不要转 PCB

新增 `STM8S003` 目前只是 8 脚原理图符号，封装仍为 TBD，所以实例属性里设置：

```text
Convert to PCB = no
Footprint = ""
```

这样能避免导入时因为空封装触发 PCB 转换错误。

## 主要脚本

脚本都在：

```text
/Users/songzijian/Coding/AI/embedded-heating/scripts/
```

### 反向打包 JSON 到 EPro

```bash
python3 scripts/convert_json_to_epro.py input.converted.json output.epro
```

### 修复 PCB 文件头

```bash
python3 scripts/repair_epro_pcb_sections.py input.epro output.pcb-fixed.epro
```

作用：把 `.epcb` 里误混入的前置 `FOOTPRINT` 段裁掉，确保 PCB 文件以 `DOCTYPE PCB` 开头。

### 自动避让布局

```bash
python3 scripts/auto_place_stm328s003_in_epro.py input.epro output.epro
```

虽然脚本名里还有 `stm328s003`，现在实际处理的是 hex ID：

```text
3280030000000001
```

也就是当前的 `STM8S003` 器件实例。

### 改名为 STM8S003

```bash
python3 scripts/rename_stm328s003_to_stm8s003.py input.epro output.epro
```

作用：把工程库、符号库、原理图实例里的显示名从 `STM328S003` 改成 `STM8S003`。

## 自动布局策略

自动布局脚本读取：

- `COMPONENT` 坐标
- 每个组件引用的 `Symbol`
- 对应 `SYMBOL/*.esym` 中的 `PART BBOX`

然后计算已有元件外接矩形，扫描页面内可用位置。

当前规则：

- 忽略整页图框/标题栏这类超大对象
- 保持在 A4 原理图框内部
- 避开标题栏区域
- 给已有元件和新增器件留安全边距
- 优先选择上中部相对空白区域

当前自动选出位置：

```text
x = 820
y = 910
```

## 行业通用排版建议

新增 MCU 这类控制器件时，推荐遵守：

- 放在相关功能分区内，不要散落到电源、模拟采样、接口区
- 与已有 MCU/调试口/控制器接口保持逻辑邻近
- 左侧优先放电源、复位、输入类信号
- 右侧优先放 GPIO、通信、输出类信号
- 符号周围预留足够空间，方便后续拉线和标注网络名
- 没有确定连线前，不要压住已有网络标号、连接器或分区标题
- 没有确定封装前，先设置 `Convert to PCB = no`

本次 `STM8S003` 放在上中部“接一体式控制器”附近，是为了与控制接口相关，同时避开主控 MCU、调试口、右侧端子和电源区域。

## 交接给小伙伴的最短说明

```text
请导入：
/Users/songzijian/Downloads/ProPrj_智能CPS_2026-05-25.stm8s003.auto-layout.pcb-fixed.epro

目标：
主控板 / Schematic1 / P1 中新增了 U99 / STM8S003，8 脚符号。

注意：
该器件目前未绑定封装，Convert to PCB = no。
如果后续要进 PCB，需要先确认 STM8S003 的具体 8 脚型号、封装和准确 pinout。
```

