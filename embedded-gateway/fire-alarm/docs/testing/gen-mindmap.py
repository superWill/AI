#!/usr/bin/env python3
"""从 test-cases-mindmap.md 生成 .mm 和 .xmind。
附录 A.2 的条款原文（gb4717-gb16806-test-cases.md）会按用例号自动挂到对应叶子的备注里。
用法：python3 gen-mindmap.py（在本目录执行）
"""
import re, html, zipfile, uuid, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "test-cases-mindmap.md")
CASES = os.path.join(HERE, "gb4717-gb16806-test-cases.md")
TS = "1781577512189"

# ---------- 解析附录 A.2 原文摘录：条款号 → (原文, [用例ID]) ----------
def parse_quotes():
    quotes = {}  # case_id -> list of (clause, text)
    txt = open(CASES, encoding="utf-8").read()
    for m in re.finditer(r'^> \*\*([\d.]+)\*\* (.+?)〔(.+?)〕\s*$', txt, re.M):
        clause, body, tag = m.group(1), m.group(2).strip(), m.group(3)
        ids = []
        for idm in re.finditer(r'([A-Z]{2})-(\d{2})((?:/\d{2})*)', tag):
            prefix, first, rest = idm.group(1), idm.group(2), idm.group(3)
            ids.append(f"{prefix}-{first}")
            for suf in re.findall(r'/(\d{2})', rest):
                ids.append(f"{prefix}-{suf}")
        for cid in ids:
            quotes.setdefault(cid, []).append((clause, body))
    return quotes

# ---------- 解析大纲 ----------
class N:
    def __init__(self, t): self.t = t; self.c = []; self.note = None

def parse_outline():
    nodes = []
    for ln in open(SRC, encoding="utf-8").read().splitlines():
        if ln.startswith('> ') or not ln.strip(): continue
        m = re.match(r'^(#{1,3})\s+(.*)', ln)
        if m: nodes.append((len(m.group(1)), m.group(2).strip())); continue
        m = re.match(r'^-\s+(.*)', ln)
        if m: nodes.append((4, m.group(1).strip()))
    root, path = None, []
    for d, text in nodes:
        n = N(text)
        if d == 1: root, path = n, [(1, n)]; continue
        while path and path[-1][0] >= d: path.pop()
        path[-1][1].c.append(n); path.append((d, n))
    return root

def attach_notes(root, quotes):
    def walk(n):
        ids = re.findall(r'[A-Z]{2}-\d{2}', n.t)
        parts, seen = [], set()
        for cid in ids:
            for clause, body in quotes.get(cid, []):
                if clause in seen: continue
                seen.add(clause)
                parts.append(f"【{clause} 原文】{body}")
        if parts: n.note = "\n\n".join(parts)
        for c in n.c: walk(c)
    walk(root)

def esc(t): return html.escape(t, quote=True)
def nid(): return uuid.uuid4().hex

# ---------- 输出 .mm（FreeMind，备注用 richcontent NOTE）----------
def emit_mm(n):
    s = f'<node TEXT="{esc(n.t)}">'
    if n.note:
        paras = ''.join(f'<p>{esc(p)}</p>' for p in n.note.split("\n\n"))
        s += f'<richcontent TYPE="NOTE"><html><head/><body>{paras}</body></html></richcontent>'
    for c in n.c: s += emit_mm(c)
    return s + '</node>'

# ---------- 输出 .xmind（XMind 8 经典格式，备注用 notes/plain）----------
def emit_xmind(n, first=False):
    extra = ' structure-class="org.xmind.ui.map.clockwise"' if first else ''
    s = f'<topic id="{nid()}" timestamp="{TS}"{extra}><title>{esc(n.t)}</title>'
    if n.note:
        s += f'<notes><plain>{esc(n.note)}</plain></notes>'
    if n.c:
        s += '<children><topics type="attached">'
        for c in n.c: s += emit_xmind(c)
        s += '</topics></children>'
    return s + '</topic>'

def main():
    quotes = parse_quotes()
    root = parse_outline()
    attach_notes(root, quotes)

    mm = '<map version="1.0.1">\n' + emit_mm(root) + '\n</map>'
    open(os.path.join(HERE, "test-cases-mindmap.mm"), 'w', encoding="utf-8").write(mm)

    content = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0" '
        f'xmlns:fo="http://www.w3.org/1999/XSL/Format" xmlns:svg="http://www.w3.org/2000/svg" '
        f'xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'version="2.0" timestamp="{TS}">\n'
        f'  <sheet id="{nid()}" timestamp="{TS}">\n    <title>共控机测试用例</title>\n'
        f'    {emit_xmind(root, first=True)}\n  </sheet>\n</xmap-content>')
    manifest = ('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0">\n'
        '  <file-entry full-path="content.xml" media-type="text/xml"/>\n'
        '  <file-entry full-path="meta.xml" media-type="text/xml"/>\n</manifest>')
    meta = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">'
        f'<Creator><Name>Claude</Name></Creator><Created>{TS}</Created><Modified>{TS}</Modified></meta>')
    out = os.path.join(HERE, "test-cases-mindmap.xmind")
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/vnd.xmind.workbook')
        z.writestr('content.xml', content)
        z.writestr('meta.xml', meta)
        z.writestr('META-INF/manifest.xml', manifest)

    noted = sum(1 for _ in re.finditer('<notes>', content))
    print(f"quotes for {len(quotes)} case-ids; topics {content.count('<topic ')}"
          f"={content.count('</topic>')} balanced; {noted} nodes carry 原文备注")

if __name__ == '__main__':
    main()
