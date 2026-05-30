# EDA JSON Excel Round Trip

This is a minimal validation flow for EasyEDA/JLCEDA Standard-style JSON files.

## Commands

Export EDA JSON to Excel:

```sh
python3 tools/eda_excel/eda_excel_roundtrip.py export \
  samples/eda_excel/easyeda_schematic_sample.json \
  samples/eda_excel/easyeda_schematic_sample.xlsx
```

Import Excel back to EDA JSON:

```sh
python3 tools/eda_excel/eda_excel_roundtrip.py import \
  samples/eda_excel/easyeda_schematic_sample.xlsx \
  samples/eda_excel/easyeda_schematic_sample.roundtrip.json
```

Verify round-trip equality:

```sh
python3 - <<'PY'
import json
from pathlib import Path
orig = json.loads(Path("samples/eda_excel/easyeda_schematic_sample.json").read_text())
rt = json.loads(Path("samples/eda_excel/easyeda_schematic_sample.roundtrip.json").read_text())
print(orig == rt)
PY
```

## Notes

- The workbook contains a `meta` sheet and a `shape` sheet.
- The `shape.raw` column is preserved so the first round trip can be lossless.
- Parsed columns such as `type` and `fields_json` are included for inspection and controlled edits.
- Object-style EasyEDA JSON files are exported to `meta` and `object_items` sheets.
- This validates the data pipeline, not electrical correctness. Real schematic/PCB imports still need EDA-side validation.

## Complex Object Sample

The more complex sample comes from the EasyEDA documentation-linked GitHub Gist:

- https://gist.github.com/dillonHe/fe0bb029c51603077ad9

Round trip:

```sh
python3 tools/eda_excel/eda_excel_roundtrip.py export \
  samples/eda_excel/easyeda_official_complex_object.json \
  samples/eda_excel/easyeda_official_complex_object.xlsx

python3 tools/eda_excel/eda_excel_roundtrip.py import \
  samples/eda_excel/easyeda_official_complex_object.xlsx \
  samples/eda_excel/easyeda_official_complex_object.roundtrip.json
```

The current complex sample round-trips with `equal: True`.
