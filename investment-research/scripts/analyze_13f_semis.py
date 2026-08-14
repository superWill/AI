#!/usr/bin/env python3
"""Compare semiconductor positions in two SEC Form 13F data-set archives."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path


TARGETS = {
    "NVDA": "67066G104",
    "TSM": "874039100",
    "MRVL": "573874104",
    "AVGO": "11135F101",
    "AMD": "007903107",
    "MU": "595112103",
    "AMAT": "038222105",
    "LRCX": "512807306",
    "KLAC": "482480100",
    "ASML": "N07059210",
    "QCOM": "747525103",
    "ARM": "042068205",
}


def load_archive(path: Path, period: str):
    with zipfile.ZipFile(path) as archive:
        submissions = {}
        with io.TextIOWrapper(
            archive.open("SUBMISSION.tsv"), encoding="utf-8-sig", newline=""
        ) as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["PERIODOFREPORT"] == period and row["SUBMISSIONTYPE"] == "13F-HR":
                    submissions[row["ACCESSION_NUMBER"]] = row["CIK"]

        manager_names = {}
        with io.TextIOWrapper(
            archive.open("COVERPAGE.tsv"), encoding="utf-8-sig", newline=""
        ) as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                accession = row["ACCESSION_NUMBER"]
                if accession in submissions:
                    manager_names[submissions[accession]] = row["FILINGMANAGER_NAME"]

        positions = {ticker: defaultdict(float) for ticker in TARGETS}
        cusip_to_ticker = {cusip: ticker for ticker, cusip in TARGETS.items()}
        with io.TextIOWrapper(
            archive.open("INFOTABLE.tsv"), encoding="utf-8-sig", newline=""
        ) as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                cik = submissions.get(row["ACCESSION_NUMBER"])
                if not cik or row["SSHPRNAMTTYPE"].upper() != "SH" or row["PUTCALL"].strip():
                    continue
                ticker = cusip_to_ticker.get(row["CUSIP"].upper())
                if ticker:
                    positions[ticker][cik] += float(row["SSHPRNAMT"])

    return set(submissions.values()), manager_names, positions


def main() -> None:
    cache_paths = (
        Path("/private/tmp/13f_semis_q4.json"),
        Path("/private/tmp/13f_semis_q1.json"),
    )
    if all(path.exists() for path in cache_paths):
        cached = [json.loads(path.read_text()) for path in cache_paths]
        q4, q1 = [
            (
                set(item["managers"]),
                item["names"],
                {ticker: defaultdict(float, rows) for ticker, rows in item["positions"].items()},
            )
            for item in cached
        ]
    else:
        q4 = load_archive(Path("/private/tmp/13f_2025q4.zip"), "31-DEC-2025")
        q1 = load_archive(Path("/private/tmp/13f_2026q1.zip"), "31-MAR-2026")
    common_managers = q4[0] & q1[0]
    print(f"UNIVERSE q4={len(q4[0])} q1={len(q1[0])} common={len(common_managers)}", flush=True)
    print(
        "ticker,q4_shares_m,q1_shares_m,total_change_pct,common_change_pct,"
        "holders_q4,holders_q1,add,cut,new,exit",
        flush=True,
    )
    for ticker in TARGETS:
        old, new = q4[2][ticker], q1[2][ticker]
        total_old, total_new = sum(old.values()), sum(new.values())
        comparable = [
            cik for cik in common_managers if old.get(cik, 0) > 0 or new.get(cik, 0) > 0
        ]
        common_old = sum(old.get(cik, 0) for cik in comparable)
        common_new = sum(new.get(cik, 0) for cik in comparable)
        add = sum(new.get(cik, 0) > old.get(cik, 0) > 0 for cik in comparable)
        cut = sum(0 < new.get(cik, 0) < old.get(cik, 0) for cik in comparable)
        opened = sum(old.get(cik, 0) == 0 < new.get(cik, 0) for cik in comparable)
        exited = sum(old.get(cik, 0) > 0 == new.get(cik, 0) for cik in comparable)
        print(
            f"{ticker},{total_old / 1e6:.3f},{total_new / 1e6:.3f},"
            f"{(total_new / total_old - 1) * 100:.2f},"
            f"{(common_new / common_old - 1) * 100:.2f},"
            f"{len(old)},{len(new)},{add},{cut},{opened},{exited}",
            flush=True,
        )

    for ticker in ("NVDA", "TSM", "MRVL"):
        old, new = q4[2][ticker], q1[2][ticker]
        changes = []
        for cik in common_managers:
            change = new.get(cik, 0) - old.get(cik, 0)
            if change:
                name = q1[1].get(cik) or q4[1].get(cik) or cik
                changes.append((change, name, old.get(cik, 0), new.get(cik, 0)))
        print(f"\nTOP_ADDS {ticker}", flush=True)
        for change, name, old_shares, new_shares in sorted(changes, reverse=True)[:5]:
            print(
                f"{name}|{change / 1e6:.3f}m|{old_shares / 1e6:.3f}->{new_shares / 1e6:.3f}",
                flush=True,
            )
        print(f"TOP_CUTS {ticker}", flush=True)
        for change, name, old_shares, new_shares in sorted(changes)[:5]:
            print(
                f"{name}|{change / 1e6:.3f}m|{old_shares / 1e6:.3f}->{new_shares / 1e6:.3f}",
                flush=True,
            )


if __name__ == "__main__":
    main()
