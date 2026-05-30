#!/usr/bin/env python3
import argparse
import json
import zipfile
from pathlib import Path


SYMBOL_PATH = "SYMBOL/stm328s003_sym_8pin.esym"
SHEET_PATH = "SHEET/12aaf30d1f2f6473/1.esch"
DEVICE_UUID = "stm328s003_mcu_8pin"


def symbol_records():
    records = [
        ["DOCTYPE", "SYMBOL", "1.1"],
        ["HEAD", {"originX": 0, "originY": 0, "version": "2", "symbolType": 2}],
        ["PART", "STM328S003.1", {"BBOX": [-120, -60, 120, 60]}],
        ["LINESTYLE", "st1", None, 0, None, 1, 1],
        ["RECT", "e0", -90, 50, 90, -50, 0, 0, 0, "st1", 0],
        ["FONTSTYLE", "st1", None, None, None, 8, 0, 0, 0, 0, 2, 0],
        ["FONTSTYLE", "st2", None, None, None, 8, 0, 0, 0, 0, 2, 2],
    ]
    pins = [
        ("1", "VDD", "Power", -110, 35, 0, -88, 30.08502, -102, 34.08502),
        ("2", "GND", "Power", -110, 15, 0, -88, 10.08502, -102, 14.08502),
        ("3", "NRST", "Input", -110, -5, 0, -88, -9.91498, -102, -5.91498),
        ("4", "PA0", "Bidirectional", -110, -25, 0, -88, -29.91498, -102, -25.91498),
        ("5", "PA1", "Bidirectional", 110, 35, 180, 88, 30.08502, 102, 34.08502),
        ("6", "PA2", "Bidirectional", 110, 15, 180, 88, 10.08502, 102, 14.08502),
        ("7", "PA3", "Bidirectional", 110, -5, 180, 88, -9.91498, 102, -5.91498),
        ("8", "PA4", "Bidirectional", 110, -25, 180, 88, -29.91498, 102, -25.91498),
    ]
    next_id = 1
    for number, name, pin_type, x, y, rotation, name_x, name_y, num_x, num_y in pins:
        pin_id = f"e{next_id}"
        records.extend(
            [
                ["PIN", pin_id, 1, None, x, y, 20, rotation, None, 0, 0],
                ["ATTR", f"e{next_id + 1}", pin_id, "NAME", name, 0, 1, name_x, name_y, 0, "st1", 0],
                ["ATTR", f"e{next_id + 2}", pin_id, "NUMBER", number, 0, 1, num_x, num_y, 0, "st2", 0],
                ["ATTR", f"e{next_id + 3}", pin_id, "Pin Type", pin_type, 0, 0, None, None, 0, "st1", 0],
            ]
        )
        next_id += 4
    records.extend(
        [
            ["ATTR", "e33", "STM328S003.1", "Name", "STM328S003", 0, 1, -45, 62, 0, "st1", 0],
            ["ATTR", "e34", "STM328S003.1", "Designator", "U?", 0, 1, -95, 62, 0, "st1", 0],
        ]
    )
    return records


def load_records(raw):
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def dump_records(records):
    return ("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n").encode("utf-8")


def move_component(records, x, y):
    component_id = None
    for record in records:
        if record and record[0] == "ATTR" and len(record) > 4 and record[3] == "Device" and record[4] == DEVICE_UUID:
            component_id = record[2]
            break
    if component_id is None:
        raise ValueError(f"{DEVICE_UUID} is not placed in {SHEET_PATH}")

    for record in records:
        if record and record[0] == "COMPONENT" and record[1] == component_id:
            record[3] = x
            record[4] = y
        if record and record[0] == "ATTR" and len(record) > 4 and record[2] == component_id:
            if record[3] == "Designator":
                record[6] = 1
                record[7] = x - 95
                record[8] = y + 62
            elif record[3] == "Name":
                record[6] = 1
                record[7] = x - 45
                record[8] = y + 62
    return component_id


def patch(input_path: Path, output_path: Path, x: int, y: int):
    new_symbol = dump_records(symbol_records())
    with zipfile.ZipFile(input_path) as source:
        sheet_records = load_records(source.read(SHEET_PATH))
        component_id = move_component(sheet_records, x, y)
        new_sheet = dump_records(sheet_records)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for info in source.infolist():
                zip_info = zipfile.ZipInfo(info.filename)
                zip_info.date_time = info.date_time
                zip_info.external_attr = info.external_attr
                zip_info.compress_type = zipfile.ZIP_DEFLATED
                if info.is_dir():
                    payload = b""
                elif info.filename == SYMBOL_PATH:
                    payload = new_symbol
                elif info.filename == SHEET_PATH:
                    payload = new_sheet
                else:
                    payload = source.read(info.filename)
                target.writestr(zip_info, payload)
    return component_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--x", type=int, default=520)
    parser.add_argument("--y", type=int, default=1010)
    args = parser.parse_args()
    component_id = patch(args.input, args.output, args.x, args.y)
    print(json.dumps({"component_id": component_id, "x": args.x, "y": args.y}, indent=2))


if __name__ == "__main__":
    main()
