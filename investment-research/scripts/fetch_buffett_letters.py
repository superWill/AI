#!/usr/bin/env python3
"""下载伯克希尔 1977–1997 年致股东信（HTML → 纯文本），补齐本地语料。

1998 年起的年报全文（含股东信）已在 data/brk-annual-reports/txt/<年>.txt。
本脚本只补早年的信，输出到 data/brk-annual-reports/letters/<年>.txt。
该目录在 .gitignore 里：原文有版权，只留本机，不进仓库。

用法：.venv/bin/python scripts/fetch_buffett_letters.py [--force]
"""
from __future__ import annotations

import html
import re
import sys
import time
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "brk-annual-reports" / "letters"
UA = "Mozilla/5.0 (research-script)"
BASE = "https://www.berkshirehathaway.com/letters/{name}.html"


def url_names(year: int) -> list[str]:
    # 1977–1997 的文件名是 <年>.html；个别年份另有 <年>ltr 变体，依次尝试
    return [str(year), f"{year}ltr", f"{year}htm"]


def to_text(raw: bytes) -> str:
    s = raw.decode("latin-1")
    s = re.sub(r"(?is)<(script|style).*?</\1>", "", s)
    s = re.sub(r"(?i)<br\s*/?>|</p>|</tr>|</h\d>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\r", "")
    s = re.sub(r"[ \t]+\n", "\n", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip() + "\n"


def main() -> int:
    force = "--force" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    failed = []
    for year in range(1977, 1998):
        dst = OUT / f"{year}.txt"
        if dst.exists() and not force:
            continue
        for name in url_names(year):
            try:
                req = urllib.request.Request(BASE.format(name=name), headers={"User-Agent": UA})
                raw = urllib.request.urlopen(req, timeout=30).read()
            except Exception:
                continue
            text = to_text(raw)
            if len(text) > 5000:
                dst.write_text(text, encoding="utf-8")
                print(f"{year}: {len(text):,} 字符")
                break
        else:
            failed.append(year)
        time.sleep(0.5)
    if failed:
        print("失败：", failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
