#!/usr/bin/env python3
import argparse
import json
import re
import zipfile
from pathlib import Path


DEVICE_UUID = "stm328s003_mcu_8pin"
SYMBOL_UUID = "stm328s003_sym_8pin"
TARGET_BOARD = "主控板"


def next_entity_id(records, start=1):
    max_id = start - 1
    pattern = re.compile(r"^e(\d+)$")
    for record in records:
        if len(record) > 1 and isinstance(record[1], str):
            match = pattern.match(record[1])
            if match:
                max_id = max(max_id, int(match.group(1)))
        if len(record) > 2 and isinstance(record[2], str):
            match = pattern.match(record[2])
            if match:
                max_id = max(max_id, int(match.group(1)))
    current = max_id

    def alloc():
        nonlocal current
        current += 1
        return f"e{current}"

    return alloc


def next_unique_id(records):
    max_id = 0
    pattern = re.compile(r"^gge(\d+)$")
    for record in records:
        if record and record[0] == "ATTR" and len(record) > 4 and record[3] == "Unique ID":
            match = pattern.match(str(record[4]))
            if match:
                max_id = max(max_id, int(match.group(1)))
    return f"gge{max_id + 1}"


def make_attr(alloc, component_id, key, value, visible=0, x=None, y=None, style="st1"):
    return [
        "ATTR",
        alloc(),
        component_id,
        key,
        value,
        0,
        visible,
        x,
        y,
        0,
        style,
        0,
    ]


def load_records(raw):
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def dump_records(records):
    return ("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n").encode(
        "utf-8"
    )


def place_component(input_path: Path, output_path: Path, x: int, y: int):
    with zipfile.ZipFile(input_path) as source:
        project = json.loads(source.read("project.json").decode("utf-8"))
        if DEVICE_UUID not in project.get("devices", {}):
            raise ValueError(f"{DEVICE_UUID} is not present in project.json")
        if SYMBOL_UUID not in project.get("symbols", {}):
            raise ValueError(f"{SYMBOL_UUID} is not present in project.json")

        board = project["boards"][TARGET_BOARD]
        sheet_path = f"SHEET/{board['schematic']}/1.esch"
        records = load_records(source.read(sheet_path))

        for record in records:
            if record and record[0] == "ATTR" and len(record) > 4 and record[4] == DEVICE_UUID:
                raise ValueError(f"{DEVICE_UUID} already appears to be placed in {sheet_path}")

        alloc = next_entity_id(records)
        component_id = alloc()
        unique_id = next_unique_id(records)
        placed = [
            ["COMPONENT", component_id, "STM328S003.1", x, y, 0, 0, {}, 0],
            make_attr(alloc, component_id, "Device", DEVICE_UUID),
            make_attr(alloc, component_id, "Symbol", SYMBOL_UUID),
            make_attr(alloc, component_id, "Footprint", ""),
            make_attr(alloc, component_id, "Unique ID", unique_id),
            make_attr(alloc, component_id, "Add into BOM", "yes"),
            make_attr(alloc, component_id, "Convert to PCB", "no"),
            make_attr(alloc, component_id, "Designator", "U99", visible=1, x=x - 95, y=y + 62),
            make_attr(alloc, component_id, "Name", "STM328S003", visible=1, x=x - 45, y=y + 62),
            make_attr(alloc, component_id, "Manufacturer Part", "STM328S003"),
            make_attr(alloc, component_id, "Manufacturer", "TBD"),
            make_attr(alloc, component_id, "Description", "8-pin MCU placeholder; footprint TBD"),
            make_attr(alloc, component_id, "Reuse Block", ""),
            make_attr(alloc, component_id, "Group ID", ""),
            make_attr(alloc, component_id, "Channel ID", ""),
        ]

        insert_at = 2
        records[insert_at:insert_at] = placed

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for info in source.infolist():
                zip_info = zipfile.ZipInfo(info.filename)
                zip_info.date_time = info.date_time
                zip_info.external_attr = info.external_attr
                zip_info.compress_type = zipfile.ZIP_DEFLATED
                if info.is_dir():
                    target.writestr(zip_info, b"")
                elif info.filename == sheet_path:
                    target.writestr(zip_info, dump_records(records))
                else:
                    target.writestr(zip_info, source.read(info.filename))

    return {"sheet": sheet_path, "component_id": component_id, "unique_id": unique_id, "x": x, "y": y}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--x", type=int, default=1170)
    parser.add_argument("--y", type=int, default=835)
    args = parser.parse_args()
    result = place_component(args.input, args.output, args.x, args.y)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
