#!/usr/bin/env python3
"""Round-trip an EasyEDA/JLCEDA standard JSON schematic through Excel.

This intentionally stores each shape's original raw string. That keeps the
first workflow lossless while still exposing parsed columns for inspection.
"""

from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import zipfile
from pathlib import Path


NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def split_shape(raw: str) -> tuple[str, list[str]]:
    parts = raw.split("~")
    return parts[0], parts[1:]


def col_name(index: int) -> str:
    name = ""
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def sheet_xml(rows: list[list[object]]) -> str:
    out = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        f'<worksheet xmlns="{NS_MAIN}" xmlns:r="{NS_REL}"><sheetData>',
    ]
    for r_idx, row in enumerate(rows, 1):
        out.append(f'<row r="{r_idx}">')
        for c_idx, value in enumerate(row, 1):
            ref = f"{col_name(c_idx)}{r_idx}"
            text = "" if value is None else str(value)
            out.append(f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(text)}</t></is></c>')
        out.append("</row>")
    out.append("</sheetData></worksheet>")
    return "".join(out)


def write_xlsx(path: Path, sheets: dict[str, list[list[object]]]) -> None:
    workbook_sheets = []
    workbook_rels = []
    content_overrides = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{NS_PKG_REL}">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
            "</Relationships>",
        )
        zf.writestr("docProps/core.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"/>')
        zf.writestr("docProps/app.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"/>')
        for idx, (name, rows) in enumerate(sheets.items(), 1):
            sheet_path = f"xl/worksheets/sheet{idx}.xml"
            workbook_sheets.append(f'<sheet name="{html.escape(name)}" sheetId="{idx}" r:id="rId{idx}"/>')
            workbook_rels.append(
                f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>'
            )
            content_overrides.append(
                f'<Override PartName="/{sheet_path}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            )
            zf.writestr(sheet_path, sheet_xml(rows))
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            + "".join(content_overrides)
            + "</Types>",
        )
        zf.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<workbook xmlns="{NS_MAIN}" xmlns:r="{NS_REL}"><sheets>'
            + "".join(workbook_sheets)
            + "</sheets></workbook>",
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{NS_PKG_REL}">'
            + "".join(workbook_rels)
            + "</Relationships>",
        )


def read_xlsx(path: Path) -> dict[str, list[list[str]]]:
    with zipfile.ZipFile(path) as zf:
        workbook = zf.read("xl/workbook.xml").decode("utf-8")
        rels = zf.read("xl/_rels/workbook.xml.rels").decode("utf-8")
        rel_targets = dict(re.findall(r'<Relationship[^>]*Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
        sheets = {}
        for sheet_match in re.finditer(r"<sheet\b([^>]*)/>", workbook):
            attrs = dict(re.findall(r'([A-Za-z_:]+)="([^"]*)"', sheet_match.group(1)))
            name = html.unescape(attrs["name"])
            rel_id = attrs["r:id"]
            target = rel_targets[rel_id]
            xml_path = posixpath.normpath(posixpath.join("xl", target))
            root = zf.read(xml_path).decode("utf-8")
            rows = []
            for row_match in re.finditer(r"<row\b[^>]*>(.*?)</row>", root):
                row_xml = row_match.group(1)
                cells = {}
                max_col = 0
                for cell_match in re.finditer(r"<c\b([^>]*)>(.*?)</c>", row_xml):
                    attrs = dict(re.findall(r'([A-Za-z_:]+)="([^"]*)"', cell_match.group(1)))
                    match = re.match(r"([A-Z]+)", attrs.get("r", ""))
                    if not match:
                        continue
                    col = 0
                    for char in match.group(1):
                        col = col * 26 + ord(char) - 64
                    max_col = max(max_col, col)
                    body = cell_match.group(2)
                    text_match = re.search(r"<t[^>]*>(.*?)</t>", body, flags=re.S)
                    value_match = re.search(r"<v[^>]*>(.*?)</v>", body, flags=re.S)
                    text = text_match.group(1) if text_match else value_match.group(1) if value_match else ""
                    cells[col] = html.unescape(text)
                rows.append([cells.get(i, "") for i in range(1, max_col + 1)])
            sheets[name] = rows
        return sheets


def export_excel(eda_json: Path, excel_path: Path) -> None:
    data = json.loads(eda_json.read_text(encoding="utf-8"))
    if isinstance(data.get("shape"), list):
        export_shape_excel(data, excel_path)
    else:
        export_object_excel(data, excel_path)


def export_shape_excel(data: dict, excel_path: Path) -> None:
    meta_rows = [["key", "json_value"]]
    for key, value in data.items():
        if key != "shape":
            meta_rows.append([key, json.dumps(value, ensure_ascii=False, separators=(",", ":"))])
    shape_rows = [["index", "type", "raw", "fields_json"]]
    for idx, raw in enumerate(data.get("shape", [])):
        shape_type, fields = split_shape(raw)
        shape_rows.append([idx, shape_type, raw, json.dumps(fields, ensure_ascii=False)])
    write_xlsx(excel_path, {"meta": meta_rows, "shape": shape_rows})


def is_object_item_section(value: object) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    return all(isinstance(item, dict) for item in value.values()) and any(str(key).startswith("gge") for key in value)


def export_object_excel(data: dict, excel_path: Path) -> None:
    meta_rows = [["key", "json_value"]]
    item_rows = [["section", "id", "raw_json"]]
    for key, value in data.items():
        if is_object_item_section(value):
            for item_id, item_value in value.items():
                item_rows.append([key, item_id, json.dumps(item_value, ensure_ascii=False, separators=(",", ":"))])
        else:
            meta_rows.append([key, json.dumps(value, ensure_ascii=False, separators=(",", ":"))])
    write_xlsx(excel_path, {"meta": meta_rows, "object_items": item_rows})


def import_excel(excel_path: Path, eda_json: Path) -> None:
    sheets = read_xlsx(excel_path)
    meta = {}
    for row in sheets.get("meta", [])[1:]:
        if len(row) >= 2 and row[0]:
            meta[row[0]] = json.loads(row[1])
    if "object_items" in sheets:
        for row in sheets.get("object_items", [])[1:]:
            if len(row) >= 3 and row[0] and row[1]:
                meta.setdefault(row[0], {})[row[1]] = json.loads(row[2])
        eda_json.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    shapes = []
    shape_rows = sheets.get("shape", [])
    headers = shape_rows[0] if shape_rows else []
    raw_index = headers.index("raw") if "raw" in headers else -1
    fields_index = headers.index("fields_json") if "fields_json" in headers else -1
    type_index = headers.index("type") if "type" in headers else -1
    for row in shape_rows[1:]:
        raw = row[raw_index] if raw_index >= 0 and raw_index < len(row) else ""
        if raw:
            shapes.append(raw)
            continue
        shape_type = row[type_index] if type_index >= 0 and type_index < len(row) else ""
        fields = json.loads(row[fields_index]) if fields_index >= 0 and fields_index < len(row) and row[fields_index] else []
        shapes.append("~".join([shape_type, *fields]))
    meta["shape"] = shapes
    eda_json.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_export = sub.add_parser("export")
    p_export.add_argument("eda_json", type=Path)
    p_export.add_argument("excel", type=Path)
    p_import = sub.add_parser("import")
    p_import.add_argument("excel", type=Path)
    p_import.add_argument("eda_json", type=Path)
    args = parser.parse_args()
    if args.command == "export":
        export_excel(args.eda_json, args.excel)
    else:
        import_excel(args.excel, args.eda_json)


if __name__ == "__main__":
    main()
