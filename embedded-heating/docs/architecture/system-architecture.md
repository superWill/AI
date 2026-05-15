# System Architecture

## Layered Architecture

```text
MQTT Platform / Local HMI / OTA
        |
        v
Application Services
  - communication
  - hmi
  - ota
        |
        v
Control Layer
  - temperature control
  - pressure differential control
  - refill control
        |
        v
State Machine
        |
        v
Safety Protection Layer
        |
        v
Core Data Layer
  - point table
  - data validation
  - config
  - logging
        |
        v
Drivers and Platform
  - sensors
  - valves
  - pumps
  - network
  - storage
  - HAL / BSP / RTOS
```

## Priority Order

1. Hard emergency input and hardware protection.
2. Safety protection module.
3. State machine permission.
4. Local manual command.
5. Remote MQTT command.
6. Automatic control algorithm.
7. Optimization strategy.

## Key Principle

The controller must continue safe local operation when MQTT is offline. Cloud connectivity improves operation and maintenance, but must not become a runtime dependency for heating safety.

