# MVP Device Display

这个 MVP 的目标是：采集换热站设备信息，并在嵌入式平台/本地屏上显示。

它暂时不做真实泵阀控制，先完成“看得见、采得到、状态清楚”的第一版产品。

## What It Contains

- `hmi/index.html`：本地屏显示原型，可直接用浏览器打开，支持添加设备和切换监控。
- `data/sample-device-data.json`：模拟采集数据。
- `docs/device-display-mvp.md`：产品说明。
- `docs/device-templates.md`：设备类型和默认采集点模板。
- `src/collector_pseudocode.c`：嵌入式采集程序伪代码。

## MVP Flow

```text
Sensors / Meters / Device Feedback
        |
        v
Acquisition Drivers
        |
        v
Point Table
        |
        v
Data Validation
        |
        v
HMI Snapshot
        |
        v
Embedded Screen Display
```

## Open the HMI

Open:

```text
hmi/index.html
```

In this local prototype, the page uses built-in simulated acquisition data so it can be opened directly. Added devices are saved in browser `localStorage`.
