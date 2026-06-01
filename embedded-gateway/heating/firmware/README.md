# Firmware Architecture

This firmware tree is organized around safety-first station control.

## Current State

No MCU/RTOS has been selected yet, so this folder is **interfaces-only**:

```text
firmware/
  include/   Public C headers (tec_control / tec_safety / tec_mqtt / tec_state_machine / tec_ota / tec_point)
  README.md  This file
```

The implementation tree is **not** scaffolded yet — concrete sub-folders are added
only when the hardware decision is in. Until then, prototypes for the same
behavior live under `../prototype/`.

## Target Layers (post-hardware-selection)

```text
firmware/
  app/       Product behavior: safety, state machine, control, MQTT, HMI, OTA
  core/      Shared models: point table, validation, config, logging
  drivers/   Device access: IO, sensors, valves, pumps, network, storage
  platform/  BSP, HAL, RTOS adaptation
  include/   Public interfaces (already present)
```

Module responsibilities for each of the above are spelled out in
`../docs/architecture/module-responsibilities.md`.

## Build System

After hardware selection, add the concrete build system under this folder —
CMake, PlatformIO, ESP-IDF, STM32Cube, or vendor SDK project files.

## Hardware Candidates

Candidate evaluations live under `../docs/hardware/`:

- `rk3506-som-candidate.md` — 厚德 HD-RK3506-CORE (Rockchip RK3506B/J, Cortex-A7 ×3 + M0 AMP)
- *(more SoM / MCU candidates to be added)*
