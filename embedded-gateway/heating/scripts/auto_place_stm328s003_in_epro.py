#!/usr/bin/env python3
import argparse
import json
import zipfile
from pathlib import Path


DEVICE_UUID = "3280030000000001"
SHEET_PATH = "SHEET/12aaf30d1f2f6473/1.esch"
STM_BBOX = [-120, -60, 120, 60]


def load_records(raw):
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def dump_records(records):
    return ("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n").encode("utf-8")


def intersects(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def symbol_bbox(zf, symbol_id, cache):
    if not symbol_id:
        return [-20, -20, 20, 20]
    if symbol_id in cache:
        return cache[symbol_id]
    try:
        records = load_records(zf.read(f"SYMBOL/{symbol_id}.esym"))
    except KeyError:
        return [-20, -20, 20, 20]
    for record in records:
        if record and record[0] == "PART" and isinstance(record[2], dict):
            bbox = record[2].get("BBOX", [-20, -20, 20, 20])
            cache[symbol_id] = bbox
            return bbox
    return [-20, -20, 20, 20]


def collect_component_data(records):
    attrs = {}
    components = []
    for record in records:
        if record and record[0] == "ATTR" and len(record) > 4:
            attrs.setdefault(record[2], {})[record[3]] = record[4]
        elif record and record[0] == "COMPONENT":
            components.append(record)
    return components, attrs


def occupied_boxes(zf, components, attrs):
    cache = {}
    boxes = []
    for component in components:
        component_id = component[1]
        component_attrs = attrs.get(component_id, {})
        if component_attrs.get("Device") == DEVICE_UUID:
            continue
        bbox = symbol_bbox(zf, component_attrs.get("Symbol"), cache)

        # Ignore sheet frame/title-block symbols. They cover the whole page and
        # are not obstacles for placing actual schematic parts.
        if bbox[2] - bbox[0] > 500 or bbox[3] - bbox[1] > 500:
            continue

        x, y = component[3], component[4]
        boxes.append(
            (
                x + bbox[0] - 10,
                y + bbox[1] - 10,
                x + bbox[2] + 10,
                y + bbox[3] + 10,
            )
        )
    return boxes


def find_position(boxes):
    candidates = []
    for x in range(180, 1540, 10):
        for y in range(160, 1110, 10):
            box = (
                x + STM_BBOX[0] - 20,
                y + STM_BBOX[1] - 20,
                x + STM_BBOX[2] + 20,
                y + STM_BBOX[3] + 20,
            )

            # Keep inside the A4 drawing frame and avoid the title-block area.
            if box[0] < 70 or box[2] > 1630 or box[1] < 70 or box[3] > 1130:
                continue
            if x > 900 and y < 360:
                continue
            if any(intersects(box, occupied) for occupied in boxes):
                continue

            # Prefer the existing central blank area near the integrated
            # controller section, but let collision detection decide validity.
            score = abs(x - 780) * 0.5 + abs(y - 910) * 0.7
            candidates.append((score, x, y))

    if not candidates:
        raise ValueError("No collision-free placement candidate found")
    _, x, y = min(candidates)
    return x, y


def move_component(records, attrs, components, x, y):
    component_id = None
    for component in components:
        if attrs.get(component[1], {}).get("Device") == DEVICE_UUID:
            component_id = component[1]
            component[3] = x
            component[4] = y
            break
    if component_id is None:
        raise ValueError(f"Could not find STM328S003 device {DEVICE_UUID}")

    for record in records:
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


def patch(input_path: Path, output_path: Path):
    with zipfile.ZipFile(input_path) as source:
        records = load_records(source.read(SHEET_PATH))
        components, attrs = collect_component_data(records)
        boxes = occupied_boxes(source, components, attrs)
        x, y = find_position(boxes)
        component_id = move_component(records, attrs, components, x, y)
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
    return {"component_id": component_id, "x": x, "y": y, "obstacles": len(boxes)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(patch(args.input, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
