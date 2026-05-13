# Firmware Architecture

This firmware tree is organized around safety-first station control.

## Layers

```text
app/       Product behavior: safety, state machine, control, MQTT, HMI, OTA
core/      Shared models: point table, validation, config, logging
drivers/   Device access: IO, sensors, valves, pumps, network, storage
platform/  BSP, HAL, RTOS adaptation
include/   Public interfaces
```

## Initial Build Strategy

No MCU/RTOS has been selected yet, so this folder currently defines architecture and interfaces first. After hardware selection, add the concrete build system under this folder, such as CMake, PlatformIO, ESP-IDF, STM32Cube, or vendor SDK project files.

