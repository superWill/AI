#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
import zipfile
from pathlib import Path


TEXT_RECORD_SUFFIXES = {".esch", ".epcb", ".esym", ".efoo"}


def parse_text_records(raw: bytes, name: str):
    text = raw.decode("utf-8")
    records = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{name}:{line_no}: invalid JSON record: {exc}") from exc
    return records


def convert_epro(input_path: Path):
    output = {
        "source": {
            "path": str(input_path),
            "sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        },
        "format": {
            "container": "zip",
            "eda": "EasyEDA/JLCEDA Pro project package",
            "conversion": "project.json plus parsed line-delimited JSON design files",
        },
        "manifest": [],
        "project": None,
        "files": {},
    }

    with zipfile.ZipFile(input_path) as zf:
        for info in sorted(zf.infolist(), key=lambda item: item.filename):
            if info.is_dir():
                output["manifest"].append(
                    {
                        "path": info.filename,
                        "type": "directory",
                        "size": 0,
                        "compressed_size": info.compress_size,
                    }
                )
                continue

            raw = zf.read(info.filename)
            suffix = Path(info.filename).suffix.lower()
            entry = {
                "path": info.filename,
                "type": "file",
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
            output["manifest"].append(entry)

            if info.filename == "project.json":
                output["project"] = json.loads(raw.decode("utf-8"))
            elif suffix in TEXT_RECORD_SUFFIXES:
                output["files"][info.filename] = {
                    "encoding": "line-delimited-json",
                    "records": parse_text_records(raw, info.filename),
                }
            else:
                output["files"][info.filename] = {
                    "encoding": "base64",
                    "data": base64.b64encode(raw).decode("ascii"),
                }

    if output["project"] is None:
        raise ValueError("project.json not found in .epro archive")

    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    converted = convert_epro(args.input)
    args.output.write_text(
        json.dumps(converted, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
