#!/usr/bin/env python3
import argparse
import json
import zipfile
from pathlib import Path


DEVICE_UUID = "3280030000000001"
SHEET_PATH = "SHEET/12aaf30d1f2f6473/1.esch"


def load_records(raw):
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def dump_records(records):
    return ("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n").encode("utf-8")


def move(records, x, y):
    component_id = None
    for record in records:
        if record and record[0] == "ATTR" and len(record) > 4:
            if record[3] == "Device" and record[4] == DEVICE_UUID:
                component_id = record[2]
                break
    if component_id is None:
        raise ValueError(f"Could not find STM328S003 device {DEVICE_UUID} in {SHEET_PATH}")

    for record in records:
        if record and record[0] == "COMPONENT" and record[1] == component_id:
            record[3] = x
            record[4] = y
        elif record and record[0] == "ATTR" and len(record) > 4 and record[2] == component_id:
            if record[3] == "Designator":
                record[6] = 1
                record[7] = x - 95
                record[8] = y + 62
            elif record[3] == "Name":
                record[6] = 1
                record[7] = x - 45
                record[8] = y + 62
    return component_id


def patch(input_path: Path, output_path: Path, x, y):
    with zipfile.ZipFile(input_path) as source:
        records = load_records(source.read(SHEET_PATH))
        component_id = move(records, x, y)
        patched_sheet = dump_records(records)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for info in source.infolist():
                zip_info = zipfile.ZipInfo(info.filename)
                zip_info.date_time = info.date_time
                zip_info.external_attr = info.external_attr
                zip_info.compress_type = zipfile.ZIP_DEFLATED
                if info.is_dir():
                    payload = b""
                elif info.filename == SHEET_PATH:
                    payload = patched_sheet
                else:
                    payload = source.read(info.filename)
                target.writestr(zip_info, payload)
    return component_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--x", type=int, default=780)
    parser.add_argument("--y", type=int, default=1010)
    args = parser.parse_args()
    component_id = patch(args.input, args.output, args.x, args.y)
    print(json.dumps({"component_id": component_id, "x": args.x, "y": args.y}, indent=2))


if __name__ == "__main__":
    main()
