#!/usr/bin/env python3
import argparse
import json
import zipfile
from pathlib import Path


DEVICE_UUID = "3280030000000001"
SYMBOL_UUID = "3280030000000002"
SYMBOL_PATH = f"SYMBOL/{SYMBOL_UUID}.esym"
SHEET_PATH = "SHEET/12aaf30d1f2f6473/1.esch"


def load_records(raw):
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def dump_records(records):
    return ("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n").encode("utf-8")


def patch_project(project):
    device = project["devices"][DEVICE_UUID]
    device["title"] = "STM8S003"
    device["description"] = "8-pin STM8S003 MCU placeholder added from customer request"
    attrs = device.setdefault("attributes", {})
    attrs["Manufacturer Part"] = "STM8S003"
    attrs["Name"] = "STM8S003"
    attrs["Description"] = "8-pin STM8S003 MCU; footprint TBD"

    symbol = project["symbols"][SYMBOL_UUID]
    symbol["title"] = "STM8S003"
    symbol["display_title"] = "STM8S003"
    symbol["description"] = "8-pin STM8S003 MCU placeholder symbol"
    symbol["desc"] = "8-pin STM8S003 MCU placeholder symbol"


def patch_records(records):
    for record in records:
        if record and record[0] == "PART" and record[1] == "STM328S003.1":
            record[1] = "STM8S003.1"
        elif record and record[0] == "ATTR" and len(record) > 4:
            if record[2] == "STM328S003.1":
                record[2] = "STM8S003.1"
            if record[4] == "STM328S003":
                record[4] = "STM8S003"
            elif record[4] == "8-pin MCU placeholder; footprint TBD":
                record[4] = "8-pin STM8S003 MCU; footprint TBD"


def patch_sheet(records):
    component_id = None
    for record in records:
        if record and record[0] == "ATTR" and len(record) > 4:
            if record[3] == "Device" and record[4] == DEVICE_UUID:
                component_id = record[2]
                break
    if component_id is None:
        raise ValueError("STM8S003 target component was not found in schematic")

    for record in records:
        if record and record[0] == "COMPONENT" and record[1] == component_id:
            record[2] = "STM8S003.1"
        elif record and record[0] == "ATTR" and len(record) > 4 and record[2] == component_id:
            if record[3] == "Name":
                record[4] = "STM8S003"
            elif record[3] == "Manufacturer Part":
                record[4] = "STM8S003"
            elif record[3] == "Description":
                record[4] = "8-pin STM8S003 MCU; footprint TBD"
    return component_id


def patch(input_path: Path, output_path: Path):
    with zipfile.ZipFile(input_path) as source:
        project = json.loads(source.read("project.json").decode("utf-8"))
        patch_project(project)

        symbol_records = load_records(source.read(SYMBOL_PATH))
        patch_records(symbol_records)

        sheet_records = load_records(source.read(SHEET_PATH))
        component_id = patch_sheet(sheet_records)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for info in source.infolist():
                zip_info = zipfile.ZipInfo(info.filename)
                zip_info.date_time = info.date_time
                zip_info.external_attr = info.external_attr
                zip_info.compress_type = zipfile.ZIP_DEFLATED
                if info.is_dir():
                    payload = b""
                elif info.filename == "project.json":
                    payload = json.dumps(project, ensure_ascii=False, indent=2).encode("utf-8")
                elif info.filename == SYMBOL_PATH:
                    payload = dump_records(symbol_records)
                elif info.filename == SHEET_PATH:
                    payload = dump_records(sheet_records)
                else:
                    payload = source.read(info.filename)
                target.writestr(zip_info, payload)
    return component_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    component_id = patch(args.input, args.output)
    print(json.dumps({"component_id": component_id, "name": "STM8S003"}, indent=2))


if __name__ == "__main__":
    main()
