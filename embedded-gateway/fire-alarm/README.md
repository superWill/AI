# Fire-alarm Co-controller Embedded Project

消防共控机（火灾报警控制器 + 联动控制器一体机）嵌入式项目，用于工业与民用建筑的火灾自动报警和消防设备联动控制。

参考机型：北京利达华信 LD128E / LD5800 系列、海湾 GST 系列、北大青鸟 JB-QB-GK 系列、鼎信 NT8001。

## Confirmed Scope

- 控制对象：火灾自动报警系统（FAAS）+ 消防联动控制系统。
- 输入侧：感烟 / 感温 / 火焰 / 可燃气体探测器、手动报警按钮、消火栓按钮、输入模块（监视水流指示器、信号阀、压力开关等）。
- 输出侧：输入/输出模块、声光警报器、消防电话、消防广播、防火门、防火卷帘、排烟风机、送风机、消防水泵、喷淋泵、稳压泵、防火阀、电梯迫降等。
- 现场总线：二总线（私有协议、极性无关、电源+数据复用）。
- 上行接口：与"消防控制室图形显示装置"对接，GB 16806 规定接口（RS-232 / RS-485 / Ethernet，厂商私有应用层）。
- 本地交互：大尺寸 LCD + 数字键盘 + 指示灯阵列 + 内置打印机 + 接警话筒 + 录音。
- 离线能力：失去上行链路时，所有报警判定与联动控制必须独立完成。
- 控制优先级：安全优先 → 报警与联动指令不可被远程或屏蔽逻辑绕过。
- 法规优先：所有功能、外观、试验都受国标 + CCCF 强制认证约束。

## Directory Layout

```text
embedded-gateway/fire-alarm/
  README.md
  .gitignore
  config/                Default runtime configuration
  docs/
    architecture/        System architecture, module responsibilities
    business/            Market reference, compliance / certification notes
    point-table/         Loop point-table data model (detectors / modules / zones)
    protocols/           Loop bus draft + CRT (graphics-workstation) link draft
    rk3506-migration/    GD32F407VET6 -> RK3506 migration research
    safety/              Interlock rules per GB 50116
  firmware/
    include/             Public C headers (fac_loop / fac_alarm / fac_interlock / fac_link / fac_panel / fac_point)
    README.md            Firmware-layer design notes
```

## Architecture Rule

安全优先级最高。联动控制矩阵的触发条件一旦满足，必须直接输出动作信号，不受手动屏蔽、远程隔离或自动控制策略的覆盖。"手动允许" 仅允许由消防控制室人员在硬件钥匙开关启用后短时启动/停止设备，不允许屏蔽自动联动。

## Core Standards

| Code | Scope |
| --- | --- |
| GB 50116-2013 | 火灾自动报警系统设计规范 |
| GB 50166-2019 | 火灾自动报警系统施工及验收标准 |
| GB 4717-2024 | 火灾报警控制器（技术要求） |
| GB 16806-2006 | 消防联动控制系统（技术要求 + 接口规范） |
| GB 12978-2003 | 消防电子产品环境试验方法及严酷等级 |
| GA/T 671-2006 | 消防控制室通用技术要求 |
| CCCF | 消防产品强制性认证（取得认证证书才能销售）|

## First Development Target

第一阶段聚焦"单台主机 + 单回路"的最小可用产品：

1. 二总线驱动（一条 200 点回路，私有帧编解码 + 轮询 + 短路/开路诊断）。
2. 点表模型（探测器/模块/区域三层）。
3. 报警判定（单点报警、同区域多点交叉、延时确认）。
4. 联动矩阵的子集（声光警报、防火门释放、电梯迫降这三类先打通）。
5. 本地 HMI（LCD + 键盘 + 报警 LED 阵列）。
6. CRT 上行（按 GB 16806 接口上报报警/动作/故障，下发查询/复位/手动启动）。
7. 后备电池切换 + 故障自检。

后续再扩：多回路、广播话筒、防火卷帘联动、风机水泵控制、双机热备、CCCF 试验剧本。
