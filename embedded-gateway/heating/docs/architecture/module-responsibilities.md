# Module Responsibilities

## firmware/app

| Module | Responsibility |
| --- | --- |
| `control` | Temperature, pressure differential, and refill control algorithms. |
| `safety` | Highest-priority protection rules and safety action generation. |
| `state_machine` | System state transitions and action permissions. |
| `communication` | MQTT telemetry, alarms, commands, parameters, and heartbeat. |
| `hmi` | Local screen data model, pages, permissions, and manual commands. |
| `ota` | Remote upgrade download, verification, switching, and rollback. |

## firmware/core

| Module | Responsibility |
| --- | --- |
| `point_table` | Unified runtime data model for sensors, devices, parameters, and MQTT mapping. |
| `data_validation` | Filtering, range checks, jump detection, and data quality flags. |
| `config` | Default parameters, persistent parameters, and factory reset. |
| `logging` | Events, alarms, operation logs, and offline cache. |

## firmware/drivers

| Module | Responsibility |
| --- | --- |
| `io` | AI, AO, DI, DO abstraction. |
| `sensor` | Temperature, pressure, flow, heat meter, and level inputs. |
| `valve` | Primary-side regulating valve and auxiliary valve control. |
| `pump` | Circulation pump and refill pump control. |
| `network` | MQTT transport dependency, Ethernet, cellular, or Wi-Fi adapter. |
| `storage` | Parameter storage, logs, OTA package storage. |

## firmware/platform

| Module | Responsibility |
| --- | --- |
| `bsp` | Board-specific pin mapping and startup. |
| `hal` | MCU or SoC hardware abstraction. |
| `rtos` | Task, timer, queue, and mutex adaptation if an RTOS is used. |

## Initial Control Loops (`app/control`)

控制算法模块负责生成普通运行指令，但不能绕过安全保护层。

- Secondary supply temperature → primary-side regulating valve opening.
- Secondary pressure differential → circulation pump frequency.
- Refill pressure → refill pump start/stop.

## State Machine States (`app/state_machine`)

Recommended initial states:

- `POWER_ON`
- `SELF_CHECK`
- `STANDBY`
- `STARTING`
- `RUNNING`
- `ADJUSTING`
- `ALARM`
- `EMERGENCY_STOP`
- `MAINTENANCE`
- `OTA_UPDATING`

