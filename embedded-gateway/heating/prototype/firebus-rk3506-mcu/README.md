# RK3506 + MCU Fire Bus Prototype

This prototype shows a small, reliable protocol between:

- a low-cost MCU that owns the fire two-wire bus timing and event latch
- an RK3506 Linux application that owns UI, database, logs, and platform upload

It is intentionally hardware-neutral. The MCU sample only needs a UART send
function and can be moved to PY32, CH32, GD32E230, MM32, or another small MCU.

## Responsibilities

```text
Fire two-wire bus
  |
Analog front-end and protection
  |
Small MCU
  - poll device addresses
  - verify frames
  - detect bus fault
  - latch alarm/fault/restore events
  - cache events while RK3506 is offline
  |
UART protocol
  |
RK3506
  - point database
  - HMI display
  - history log
  - platform protocol
  - user operations
```

## Protocol

Frame layout:

```text
AA 55 | version | command | seq_le32 | length_le16 | payload | crc16_le
```

Commands:

| Command | Direction | Meaning |
|---|---|---|
| `0x01 HEARTBEAT` | MCU -> RK3506 | MCU is alive and reports queue/bus state |
| `0x10 EVENT_REPORT` | MCU -> RK3506 | Alarm/fault/restore/feedback event |
| `0x11 STATUS_SNAPSHOT` | MCU -> RK3506 | Full or partial device status snapshot |
| `0x12 BUS_FAULT` | MCU -> RK3506 | Short/open/over-current bus fault |
| `0x80 ACK` | both | Acknowledge a sequence number |
| `0x81 GET_SNAPSHOT` | RK3506 -> MCU | Ask MCU for current state |
| `0x82 RESET_LOOP` | RK3506 -> MCU | Run fire bus reset timing |
| `0x83 SET_CONFIG` | RK3506 -> MCU | Set poll range and behavior |

## Build the MCU host demo

```sh
cd prototype/firebus-rk3506-mcu
cc -Wall -Wextra -std=c99 -o mcu_demo mcu_example.c
./mcu_demo
```

The demo prints UART frames as hex. On real hardware, replace
`uart_send_bytes()` with the MCU UART driver.

## Run the RK3506 serial reader

Install `pyserial` on the RK3506 rootfs if it is not present:

```sh
python3 -m pip install pyserial
```

Then run:

```sh
python3 rk3506_firebus_gateway.py --port /dev/ttyS4 --baud 115200
```

Use `460800` if full snapshots or batch configuration are too slow in testing.

