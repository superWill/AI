#!/usr/bin/env python3
"""RK3506 side UART reader for the fire bus MCU protocol."""

from __future__ import annotations

import argparse
import struct
import time

MAGIC = b"\xAA\x55"
VERSION = 0x01
HEADER_LEN = 10
MAX_PAYLOAD = 128

CMD_HEARTBEAT = 0x01
CMD_EVENT_REPORT = 0x10
CMD_BUS_FAULT = 0x12
CMD_ACK = 0x80
CMD_GET_SNAPSHOT = 0x81
CMD_RESET_LOOP = 0x82

EVENT_NAMES = {
    1: "alarm",
    2: "fault",
    3: "restore",
    4: "feedback",
    5: "offline",
}

DEVICE_NAMES = {
    1: "smoke_detector",
    2: "heat_detector",
    3: "manual_call_point",
    4: "io_module",
}


def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def encode_frame(cmd: int, seq: int, payload: bytes = b"") -> bytes:
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("payload too large")

    header = MAGIC + bytes([VERSION, cmd]) + struct.pack("<IH", seq, len(payload))
    body = header + payload
    return body + struct.pack("<H", crc16_ccitt(body))


def decode_frame(frame: bytes) -> tuple[int, int, bytes]:
    if len(frame) < HEADER_LEN + 2:
        raise ValueError("frame too short")
    if frame[0:2] != MAGIC:
        raise ValueError("bad magic")
    if frame[2] != VERSION:
        raise ValueError(f"unsupported version {frame[2]}")

    cmd = frame[3]
    seq, payload_len = struct.unpack_from("<IH", frame, 4)
    expected_len = HEADER_LEN + payload_len + 2
    if payload_len > MAX_PAYLOAD or len(frame) != expected_len:
        raise ValueError("bad length")

    expected_crc = struct.unpack_from("<H", frame, HEADER_LEN + payload_len)[0]
    actual_crc = crc16_ccitt(frame[: HEADER_LEN + payload_len])
    if expected_crc != actual_crc:
        raise ValueError("bad crc")

    return cmd, seq, frame[HEADER_LEN : HEADER_LEN + payload_len]


def read_frame(port) -> bytes:
    while True:
        byte = port.read(1)
        if byte != MAGIC[:1]:
            continue
        if port.read(1) != MAGIC[1:]:
            continue

        rest = port.read(HEADER_LEN - 2)
        if len(rest) != HEADER_LEN - 2:
            raise TimeoutError("timeout while reading header")

        payload_len = struct.unpack_from("<H", rest, 6)[0]
        if payload_len > MAX_PAYLOAD:
            continue

        tail = port.read(payload_len + 2)
        if len(tail) != payload_len + 2:
            raise TimeoutError("timeout while reading payload")

        return MAGIC + rest + tail


def ack(port, seq: int) -> None:
    port.write(encode_frame(CMD_ACK, seq))


def handle_event(payload: bytes) -> None:
    if len(payload) < 10:
        raise ValueError("event payload too short")

    address, device_type, event_type, flags, bus_time_ms = struct.unpack_from("<HBBHI", payload)
    device = DEVICE_NAMES.get(device_type, f"device_{device_type}")
    event = EVENT_NAMES.get(event_type, f"event_{event_type}")

    # Real product code should write this into the event queue/database first,
    # then update HMI and platform upload independently.
    print(
        f"event addr={address:03d} device={device} type={event} "
        f"flags=0x{flags:04X} bus_time_ms={bus_time_ms}"
    )


def handle_heartbeat(payload: bytes) -> None:
    if len(payload) < 8:
        raise ValueError("heartbeat payload too short")

    poll_start, poll_end, pending_events, bus_state, rk_online = struct.unpack_from("<HHHBB", payload)
    print(
        f"heartbeat poll={poll_start}-{poll_end} pending={pending_events} "
        f"bus_state={bus_state} rk_online={rk_online}"
    )


def run(port_name: str, baud: int) -> None:
    import serial

    with serial.Serial(port_name, baudrate=baud, timeout=1.0) as port:
        print(f"listening on {port_name} at {baud} bps")
        last_snapshot_request = 0.0

        while True:
            now = time.monotonic()
            if now - last_snapshot_request > 10.0:
                port.write(encode_frame(CMD_GET_SNAPSHOT, 1))
                last_snapshot_request = now

            frame = read_frame(port)
            cmd, seq, payload = decode_frame(frame)

            if cmd == CMD_HEARTBEAT:
                handle_heartbeat(payload)
                ack(port, seq)
            elif cmd == CMD_EVENT_REPORT:
                handle_event(payload)
                ack(port, seq)
            elif cmd == CMD_BUS_FAULT:
                print(f"bus fault payload={payload.hex()}")
                ack(port, seq)
            else:
                print(f"unknown cmd=0x{cmd:02X} seq={seq} payload={payload.hex()}")
                ack(port, seq)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttyS4")
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()
    run(args.port, args.baud)


if __name__ == "__main__":
    main()

