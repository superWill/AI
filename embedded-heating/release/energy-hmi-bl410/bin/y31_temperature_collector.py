#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone


def read_ma(channel):
    output = subprocess.check_output(
        ["/usr/sbin/ioy", "get", channel],
        text=True,
        stderr=subprocess.STDOUT,
        timeout=2,
    )
    return float(output.strip())


def convert_temperature(ma, ma_min, ma_max, temp_min, temp_max):
    ratio = (ma - ma_min) / (ma_max - ma_min)
    return temp_min + ratio * (temp_max - temp_min)


def write_json(path, payload):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp_path, path)


def main():
    parser = argparse.ArgumentParser(description="Publish BL412B Y31 AI temperature as JSON.")
    parser.add_argument("--channel", default="1.1", help="ioy slot.channel, for example 1.1")
    parser.add_argument("--output", default="/opt/energy-hmi/html/data/y31-ai1-temperature.json")
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--ma-min", type=float, default=4.0)
    parser.add_argument("--ma-max", type=float, default=20.0)
    parser.add_argument("--temp-min", type=float, default=0.0)
    parser.add_argument("--temp-max", type=float, default=100.0)
    args = parser.parse_args()

    while True:
        try:
            ma = read_ma(args.channel)
            temp_c = convert_temperature(ma, args.ma_min, args.ma_max, args.temp_min, args.temp_max)
            payload = {
                "ok": True,
                "source": "Y31 AI1",
                "channel": args.channel,
                "raw_ma": round(ma, 6),
                "temperature_c": round(temp_c, 2),
                "range": {
                    "ma_min": args.ma_min,
                    "ma_max": args.ma_max,
                    "temp_min": args.temp_min,
                    "temp_max": args.temp_max,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            payload = {
                "ok": False,
                "source": "Y31 AI1",
                "channel": args.channel,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        write_json(args.output, payload)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
