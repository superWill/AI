#!/usr/bin/env python3
import argparse
import base64
import json
import zipfile
from pathlib import Path


def dump_record(record):
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))


def build_epro(input_path: Path, output_path: Path):
    data = json.loads(input_path.read_text(encoding="utf-8"))
    manifest = data.get("manifest") or []
    files = data.get("files") or {}

    if "project" not in data:
        raise ValueError("converted JSON is missing the top-level project object")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for entry in manifest:
            path = entry.get("path")
            if not path:
                continue

            if entry.get("type") == "directory":
                zf.writestr(path if path.endswith("/") else f"{path}/", b"")
                continue

            if path == "project.json":
                payload = json.dumps(
                    data["project"],
                    ensure_ascii=False,
                    indent=2,
                ).encode("utf-8")
            else:
                file_data = files.get(path)
                if file_data is None:
                    raise ValueError(f"converted JSON is missing file payload: {path}")

                encoding = file_data.get("encoding")
                if encoding == "line-delimited-json":
                    payload = (
                        "\n".join(dump_record(record) for record in file_data["records"])
                        + "\n"
                    ).encode("utf-8")
                elif encoding == "base64":
                    payload = base64.b64decode(file_data["data"])
                else:
                    raise ValueError(f"unsupported file encoding for {path}: {encoding}")

            zf.writestr(path, payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    build_epro(args.input, args.output)


if __name__ == "__main__":
    main()
