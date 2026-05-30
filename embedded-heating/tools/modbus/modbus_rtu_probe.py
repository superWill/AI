import argparse
import os
import select
import termios
import time


def crc16_modbus(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def build_request(slave, function, address, quantity):
    frame = bytes(
        [
            slave & 0xFF,
            function & 0xFF,
            (address >> 8) & 0xFF,
            address & 0xFF,
            (quantity >> 8) & 0xFF,
            quantity & 0xFF,
        ]
    )
    crc = crc16_modbus(frame)
    return frame + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def check_response(frame):
    if len(frame) < 5:
        return False
    body = frame[:-2]
    got = frame[-2] | (frame[-1] << 8)
    return crc16_modbus(body) == got


def configure_serial(fd, baud):
    attrs = termios.tcgetattr(fd)
    attrs[0] = 0
    attrs[1] = 0
    attrs[2] = termios.CLOCAL | termios.CREAD | termios.CS8
    attrs[3] = 0
    speed = getattr(termios, f"B{baud}")
    attrs[4] = speed
    attrs[5] = speed
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)


def transact(port, baud, request, timeout):
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd, baud)
        termios.tcflush(fd, termios.TCIOFLUSH)
        os.write(fd, request)
        deadline = time.monotonic() + timeout
        chunks = []
        while time.monotonic() < deadline:
            wait = max(0, deadline - time.monotonic())
            readable, _, _ = select.select([fd], [], [], min(0.05, wait))
            if readable:
                chunk = os.read(fd, 256)
                if chunk:
                    chunks.append(chunk)
                    time.sleep(0.02)
        return b"".join(chunks)
    finally:
        os.close(fd)


def bits_from_coil_response(response, quantity):
    if len(response) < 6 or response[1] not in (1, 2):
        return []
    byte_count = response[2]
    data = response[3 : 3 + byte_count]
    bits = []
    for byte in data:
        for bit in range(8):
            bits.append((byte >> bit) & 1)
    return bits[:quantity]


def registers_from_response(response):
    if len(response) < 7 or response[1] not in (3, 4):
        return []
    byte_count = response[2]
    data = response[3 : 3 + byte_count]
    if len(data) != byte_count or byte_count % 2 != 0:
        return []
    registers = []
    for index in range(0, byte_count, 2):
        registers.append((data[index] << 8) | data[index + 1])
    return registers


def main():
    parser = argparse.ArgumentParser(description="Small Modbus RTU probe without external packages.")
    parser.add_argument("--port", default="/dev/ttyS7")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--slave", type=int, default=1)
    parser.add_argument("--function", type=lambda x: int(x, 0), default=2)
    parser.add_argument("--address", type=lambda x: int(x, 0), default=0)
    parser.add_argument("--quantity", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=0.3)
    parser.add_argument("--scan", action="store_true")
    args = parser.parse_args()

    requests = []
    if args.scan:
        for slave in range(1, 33):
            for function in (1, 2):
                for address in (0, 1, 0x0000, 0x0001, 0x0100):
                    requests.append((slave, function, address, args.quantity))
    else:
        requests.append((args.slave, args.function, args.address, args.quantity))

    for slave, function, address, quantity in requests:
        request = build_request(slave, function, address, quantity)
        response = transact(args.port, args.baud, request, args.timeout)
        if not response:
            if not args.scan:
                print(f"no_response request={request.hex(' ')}")
            continue
        ok = check_response(response)
        bits = bits_from_coil_response(response, quantity) if ok else []
        registers = registers_from_response(response) if ok else []
        print(
            "slave={slave} function={function} address={address} request={request} response={response} crc_ok={ok} bits={bits} registers={registers}".format(
                slave=slave,
                function=function,
                address=address,
                request=request.hex(" "),
                response=response.hex(" "),
                ok=ok,
                bits=bits,
                registers=registers,
            )
        )


if __name__ == "__main__":
    main()
