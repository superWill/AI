#!/usr/bin/env /usr/bin/python3
"""把桌面的 Numbers 工作副本回灌到仓库的 test-cases-execution.xlsx。

    /usr/bin/python3 sync-from-numbers.py            # 只看差异，不写
    /usr/bin/python3 sync-from-numbers.py --apply    # 确认后写入仓库

以 Numbers 那份为准：仓库文件只保留 Excel 侧的东西（下拉、冻结、筛选、统计公式），
测试执行表的单元格内容整列覆盖，序号重排为连续 1..N。

必须用 /usr/bin/python3——Homebrew 的 3.14 pyexpat 坏了，openpyxl 起不来。
"""
import datetime
import os
import subprocess
import sys
import tempfile

from openpyxl import load_workbook

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_XLSX = os.path.join(HERE, "test-cases-execution.xlsx")
NUMBERS = os.path.expanduser("~/Desktop/test-cases-execution.numbers")
SHEET = "测试执行表"


def norm(v):
    """Numbers 会把手打的 2026-09-03 存成日期值，导入的同类值却是纯文本。
    两种存法显示一样，直接比较会产生一整列假差异，所以统一归一化成 YYYY-MM-DD。"""
    if v is None:
        return ""
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.strftime("%Y-%m-%d")
    return str(v).strip()


def export_numbers(dest):
    """让 Numbers 自己导出 xlsx——没有第三方库能读 .numbers。"""
    subprocess.run(["open", "-a", "Numbers", NUMBERS], check=True)
    script = f'''
    tell application "Numbers"
        activate
        delay 1
        export front document to file ((POSIX file "{dest}") as string) as Microsoft Excel
    end tell
    '''
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
    if not os.path.exists(dest):
        sys.exit("导出失败：Numbers 没产出文件（试试先手动把文档切到前台）")


def read(path):
    ws = load_workbook(path, data_only=True)[SHEET]
    hdr = [c.value for c in ws[1]]
    ci = hdr.index("用例号")
    rows = [r for r in ws.iter_rows(min_row=2, values_only=True) if r[ci] is not None]
    return hdr, rows


def main():
    apply = "--apply" in sys.argv
    with tempfile.TemporaryDirectory() as tmp:
        exported = os.path.join(tmp, "desk.xlsx")
        export_numbers(exported)

        hdr_a, rows_a = read(REPO_XLSX)
        hdr_b, rows_b = read(exported)
        if hdr_a != hdr_b:
            sys.exit(f"表头不一致：\n  仓库 {hdr_a}\n  桌面 {hdr_b}")

        ci = hdr_a.index("用例号")
        ids_a = [norm(r[ci]) for r in rows_a]
        ids_b = [norm(r[ci]) for r in rows_b]
        only_a, only_b = set(ids_a) - set(ids_b), set(ids_b) - set(ids_a)
        for cid in ids_a:
            if cid in only_a:
                print(f"  - 桌面已删 {cid}")
        for cid in ids_b:
            if cid in only_b:
                print(f"  + 桌面新增 {cid}")
        if ids_a != ids_b:
            sys.exit("用例号顺序/集合不一致，需人工确认后再同步（上面列出了增删）")

        changes = []
        for x, y in zip(rows_a, rows_b):
            for k, h in enumerate(hdr_a):
                if h == "序号":          # 序号是显示用计数，每次重排，不算差异
                    continue
                if norm(x[k]) != norm(y[k]):
                    changes.append((norm(x[ci]), h, norm(x[k]), norm(y[k])))
        for cid, h, old, new in changes:
            print(f"  {cid} [{h}]: {old!r} -> {new!r}")
        print(f"\n{len(rows_b)} 行，{len(changes)} 处内容变更")

        if not changes:
            print("无需同步")
            return
        if not apply:
            print("（未写入；确认无误后加 --apply）")
            return

        wb = load_workbook(REPO_XLSX)          # 不带 data_only，保住统计页的公式
        ws = wb[SHEET]
        for n, vals in enumerate(rows_b):
            row = n + 2
            ws.cell(row=row, column=1).value = n + 1
            for col in range(2, len(hdr_a) + 1):
                v = vals[col - 1]
                if isinstance(v, (datetime.datetime, datetime.date)):
                    v = norm(v)
                elif isinstance(v, str):
                    v = v.strip() or None
                ws.cell(row=row, column=col).value = v
        for row in range(2 + len(rows_b), ws.max_row + 1):
            for col in range(1, len(hdr_a) + 1):
                ws.cell(row=row, column=col).value = None
        ws.auto_filter.ref = f"A1:N{1 + len(rows_b)}"
        ws.freeze_panes = "C2"
        wb.save(REPO_XLSX)
        print(f"已写入 {REPO_XLSX}")


if __name__ == "__main__":
    main()
