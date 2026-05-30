#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


DEVICE_UUID = "stm328s003_mcu_8pin"
SYMBOL_UUID = "stm328s003_sym_8pin"
SYMBOL_PATH = f"SYMBOL/{SYMBOL_UUID}.esym"

PINS = [
    ("1", "VDD", "Power"),
    ("2", "GND", "Power"),
    ("3", "NRST", "Input"),
    ("4", "PA0", "Bidirectional"),
    ("5", "PA1", "Bidirectional"),
    ("6", "PA2", "Bidirectional"),
    ("7", "PA3", "Bidirectional"),
    ("8", "PA4", "Bidirectional"),
]


def symbol_records():
    records = [
        ["DOCTYPE", "SYMBOL", "1.1"],
        ["HEAD", {"originX": 0, "originY": 0, "version": "2", "symbolType": 2}],
        ["PART", "STM328S003.1", {"BBOX": [-120, -60, 120, 60]}],
        ["LINESTYLE", "st1", None, 0, None, 1, 1],
        ["RECT", "e0", -90, 50, 90, -50, 0, 0, 0, "st1", 0],
        ["FONTSTYLE", "st_name", None, None, None, 8, 0, 0, 0, 0, 2, 0],
        ["FONTSTYLE", "st_num", None, None, None, 8, 0, 0, 0, 0, 2, 2],
    ]

    left_y = [35, 15, -5, -25]
    right_y = [35, 15, -5, -25]
    for index, (number, name, pin_type) in enumerate(PINS):
        base = index * 4 + 1
        pin_id = f"e{base}"
        if index < 4:
            x, y, rotation = -110, left_y[index], 0
            name_x, name_y = -88, y - 4.91498
            num_x, num_y = -102, y - 0.91498
        else:
            x, y, rotation = 110, right_y[index - 4], 180
            name_x, name_y = 88, y - 4.91498
            num_x, num_y = 102, y - 0.91498

        records.extend(
            [
                ["PIN", pin_id, 1, None, x, y, 20, rotation, None, 0, 0],
                [
                    "ATTR",
                    f"e{base + 1}",
                    pin_id,
                    "NAME",
                    name,
                    0,
                    1,
                    name_x,
                    name_y,
                    0,
                    "st_name",
                    0,
                ],
                [
                    "ATTR",
                    f"e{base + 2}",
                    pin_id,
                    "NUMBER",
                    number,
                    0,
                    1,
                    num_x,
                    num_y,
                    0,
                    "st_num",
                    0,
                ],
                [
                    "ATTR",
                    f"e{base + 3}",
                    pin_id,
                    "Pin Type",
                    pin_type,
                    0,
                    0,
                    None,
                    None,
                    0,
                    "st_name",
                    0,
                ],
            ]
        )

    records.extend(
        [
            [
                "ATTR",
                "e33",
                "STM328S003.1",
                "NAME",
                "STM328S003",
                0,
                1,
                -45,
                62,
                0,
                "st_name",
                0,
            ],
            [
                "ATTR",
                "e34",
                "STM328S003.1",
                "Designator",
                "U?",
                0,
                1,
                -95,
                62,
                0,
                "st_name",
                0,
            ],
        ]
    )
    return records


def manifest_entry(path, records):
    payload = ("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n").encode(
        "utf-8"
    )
    return {
        "path": path,
        "type": "file",
        "size": len(payload),
        "compressed_size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def add_mcu(path: Path, backup: bool):
    data = json.loads(path.read_text(encoding="utf-8"))
    project = data.setdefault("project", {})

    project.setdefault("devices", {})[DEVICE_UUID] = {
        "uuid": DEVICE_UUID,
        "title": "STM328S003",
        "description": "8-pin MCU placeholder added from customer request",
        "attributes": {
            "Symbol": SYMBOL_UUID,
            "Footprint": "",
            "Manufacturer Part": "STM328S003",
            "Manufacturer": "TBD",
            "Supplier": "TBD",
            "Add into BOM": "yes",
            "Convert to PCB": "yes",
            "Designator": "U?",
            "Number of Pins": "8",
            "Package": "TBD",
            "Name": "STM328S003",
            "Description": "8-pin MCU; pinout defined in symbol records",
            "Pins": "; ".join(f"{number}:{name}:{pin_type}" for number, name, pin_type in PINS),
        },
        "images": None,
        "tag": {},
        "source": "codex-added",
        "version": "20260525",
        "symbol_type": 2,
        "footprint_type": 0,
    }

    project.setdefault("symbols", {})[SYMBOL_UUID] = {
        "uuid": SYMBOL_UUID,
        "title": "STM328S003",
        "display_title": "STM328S003",
        "docType": 2,
        "type": 2,
        "description": "8-pin MCU placeholder symbol",
        "desc": "8-pin MCU placeholder symbol",
        "source": "codex-added",
        "version": "20260525",
    }

    records = symbol_records()
    data.setdefault("files", {})[SYMBOL_PATH] = {
        "encoding": "line-delimited-json",
        "records": records,
    }

    manifest = data.setdefault("manifest", [])
    manifest[:] = [entry for entry in manifest if entry.get("path") != SYMBOL_PATH]
    manifest.append(manifest_entry(SYMBOL_PATH, records))
    manifest.sort(key=lambda entry: entry.get("path", ""))

    if backup:
        backup_path = path.with_suffix(path.suffix + ".bak")
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()
    add_mcu(args.json_file, backup=not args.no_backup)


if __name__ == "__main__":
    main()
