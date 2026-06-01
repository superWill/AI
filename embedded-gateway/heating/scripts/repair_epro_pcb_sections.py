#!/usr/bin/env python3
import argparse
import json
import zipfile
from pathlib import Path


def trim_to_pcb_records(raw: bytes, path: str):
    lines = raw.decode("utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        record = json.loads(line)
        if (
            isinstance(record, list)
            and len(record) >= 3
            and record[0] == "DOCTYPE"
            and record[1] == "PCB"
        ):
            if index == 0:
                return raw, 0
            return ("\n".join(lines[index:]) + "\n").encode("utf-8"), index
    raise ValueError(f"{path} does not contain a PCB DOCTYPE record")


def repair(input_path: Path, output_path: Path):
    repaired = []
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(input_path) as source:
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for info in source.infolist():
                raw = source.read(info.filename) if not info.is_dir() else b""
                payload = raw

                if info.filename.startswith("PCB/") and info.filename.endswith(".epcb"):
                    payload, removed_lines = trim_to_pcb_records(raw, info.filename)
                    if removed_lines:
                        repaired.append(
                            {
                                "path": info.filename,
                                "removed_prefix_lines": removed_lines,
                            }
                        )

                zip_info = zipfile.ZipInfo(info.filename)
                zip_info.date_time = info.date_time
                zip_info.external_attr = info.external_attr
                zip_info.compress_type = zipfile.ZIP_DEFLATED
                target.writestr(zip_info, payload)

    return repaired


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    repaired = repair(args.input, args.output)
    print(json.dumps({"repaired": repaired}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
