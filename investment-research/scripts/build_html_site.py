from __future__ import annotations

import html
import os
import re
import shutil
from pathlib import Path


ROOT = Path("/Users/songzijian/Coding/AI/investment-research")
SITE = ROOT / "site"
ASSETS = SITE / "_assets"

IGNORE_DIRS = {
    ".git",
    ".venv",
    "data",
    "scripts",
    "site",
}

SECTION_ORDER = [
    "notes",
    "dashboards",
    "agents",
    "portfolios",
    "tickers",
]

CSS = """
:root {
  --bg: #f5f1e8;
  --paper: #fffdf8;
  --ink: #1f1e1a;
  --muted: #6d685d;
  --line: #ddd3c2;
  --accent: #8f2d14;
  --accent-soft: #f2dfd7;
  --shadow: 0 18px 50px rgba(54, 40, 19, 0.08);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Iowan Old Style", "Palatino Linotype", "Times New Roman", serif;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(143, 45, 20, 0.08), transparent 28%),
    linear-gradient(180deg, #f7f3ea 0%, #f2ece0 100%);
}
a { color: inherit; text-decoration: none; }
.page { max-width: 1100px; margin: 0 auto; padding: 24px 18px 56px; }
.topbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 18px; }
.back, .home-link { color: var(--accent); font-weight: 700; font-size: 14px; }
.hero {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 22px;
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}
.eyebrow { font-size: 12px; text-transform: uppercase; letter-spacing: 0.16em; color: var(--muted); margin-bottom: 10px; }
h1 { margin: 0 0 8px; font-size: clamp(28px, 5vw, 48px); line-height: 0.98; }
.hero p { margin: 0; color: var(--muted); line-height: 1.65; max-width: 760px; }
.doc {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 22px;
  box-shadow: var(--shadow);
  padding: 28px 24px;
}
.doc h1, .doc h2, .doc h3, .doc h4, .doc h5, .doc h6 { line-height: 1.16; margin-top: 1.55em; margin-bottom: 0.55em; }
.doc h1:first-child, .doc h2:first-child { margin-top: 0; }
.doc p, .doc li, .doc blockquote { line-height: 1.72; font-size: 16px; }
.doc p { margin: 0 0 1em; }
.doc ul, .doc ol { margin: 0 0 1em 1.4em; padding: 0; }
.doc li { margin: 0.32em 0; }
.doc code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background: #f3eee5;
  padding: 0.15em 0.38em;
  border-radius: 6px;
  font-size: 0.92em;
}
.doc pre {
  background: #1f1e1a;
  color: #f7f2e9;
  padding: 16px;
  border-radius: 14px;
  overflow-x: auto;
  margin: 0 0 1.2em;
}
.doc pre code { background: transparent; padding: 0; color: inherit; }
.doc hr { border: 0; border-top: 1px solid var(--line); margin: 1.6em 0; }
.doc blockquote {
  margin: 0 0 1.2em;
  padding: 0.2em 1em;
  border-left: 4px solid var(--accent);
  background: #faf5ee;
  color: #514b41;
}
.doc table {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 1.2em;
  display: block;
  overflow-x: auto;
}
.doc th, .doc td {
  border: 1px solid var(--line);
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
  white-space: nowrap;
}
.doc th {
  background: #f3eee5;
  font-weight: 700;
}
.doc strong { font-weight: 700; }
.doc em { font-style: italic; }
.doc a { color: var(--accent); text-decoration: underline; text-underline-offset: 2px; }
.meta-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}
.pill {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: #f3eee5;
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 12px;
}
.section-list {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 14px;
}
.section-card {
  grid-column: span 6;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 18px;
  box-shadow: var(--shadow);
}
.section-card h3 { margin: 0 0 12px; }
.section-card ul { margin: 0; padding-left: 18px; }
.section-card li { margin: 8px 0; }
.section-card a { color: var(--accent); }
.footer {
  margin-top: 20px;
  color: var(--muted);
  font-size: 13px;
  text-align: center;
}
@media (max-width: 840px) {
  .section-list { grid-template-columns: 1fr; }
  .section-card { grid-column: span 1; }
}
"""


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        rel = path.relative_to(ROOT)
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue
        files.append(path)
    return sorted(files)


def rel_html_path(md_path: Path) -> Path:
    return md_path.relative_to(ROOT).with_suffix(".html")


def html_href_for_markdown(target_href: str, current_html_rel: Path) -> str:
    target = target_href.split("#", 1)[0]
    fragment = ""
    if "#" in target_href:
        fragment = "#" + target_href.split("#", 1)[1]
    if target.startswith(("http://", "https://", "mailto:")):
        return target_href
    target_path = (current_html_rel.parent / target).resolve().relative_to(ROOT.resolve())
    target_parts = list(target_path.parts)
    if any(part in IGNORE_DIRS for part in target_parts):
        return target_href
    if target_path.suffix == ".md":
        target_path = target_path.with_suffix(".html")
    return os.path.relpath(SITE / target_path, (SITE / current_html_rel).parent).replace(os.sep, "/") + fragment


def convert_inline(text: str, current_html_rel: Path) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)

    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        href = html.unescape(match.group(2))
        final_href = html_href_for_markdown(href, current_html_rel)
        return f'<a href="{html.escape(final_href, quote=True)}">{label}</a>'

    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, escaped)
    return escaped


def table_html(lines: list[str], current_html_rel: Path) -> str:
    rows = []
    for raw in lines:
        row = raw.strip().strip("|")
        cells = [cell.strip() for cell in row.split("|")]
        rows.append(cells)
    if len(rows) < 2:
        return "".join(f"<p>{convert_inline(line, current_html_rel)}</p>" for line in lines)
    header = rows[0]
    body = [r for r in rows[2:]]
    thead = "".join(f"<th>{convert_inline(cell, current_html_rel)}</th>" for cell in header)
    tbody = ""
    for row in body:
        tbody += "<tr>" + "".join(f"<td>{convert_inline(cell, current_html_rel)}</td>" for cell in row) + "</tr>"
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>"


def markdown_to_html(md_text: str, current_html_rel: Path) -> str:
    lines = md_text.replace("\r\n", "\n").split("\n")
    i = 0
    out: list[str] = []
    in_list = False
    list_tag = ""
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(item.strip() for item in paragraph).strip()
            if text:
                out.append(f"<p>{convert_inline(text, current_html_rel)}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal in_list, list_tag
        if in_list:
            out.append(f"</{list_tag}>")
            in_list = False
            list_tag = ""

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            close_list()
            fence = stripped[:3]
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith(fence):
                code_lines.append(lines[i])
                i += 1
            out.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            close_list()
            i += 1
            continue

        if stripped == "---":
            flush_paragraph()
            close_list()
            out.append("<hr />")
            i += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            close_list()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            quote_text = " ".join(quote_lines)
            out.append(f"<blockquote>{convert_inline(quote_text, current_html_rel)}</blockquote>")
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            close_list()
            level = len(heading_match.group(1))
            out.append(f"<h{level}>{convert_inline(heading_match.group(2), current_html_rel)}</h{level}>")
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?[-:\s|]+\|?\s*$", lines[i + 1]):
            flush_paragraph()
            close_list()
            table_lines = [line]
            i += 1
            table_lines.append(lines[i])
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            out.append(table_html(table_lines, current_html_rel))
            continue

        ul_match = re.match(r"^[-*]\s+(.*)$", stripped)
        ol_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if ul_match or ol_match:
            flush_paragraph()
            tag = "ul" if ul_match else "ol"
            content = ul_match.group(1) if ul_match else ol_match.group(1)
            if not in_list or list_tag != tag:
                close_list()
                out.append(f"<{tag}>")
                in_list = True
                list_tag = tag
            out.append(f"<li>{convert_inline(content, current_html_rel)}</li>")
            i += 1
            continue

        paragraph.append(line)
        i += 1

    flush_paragraph()
    close_list()
    return "\n".join(out)


def render_doc(md_path: Path, all_md: list[Path]) -> str:
    rel = md_path.relative_to(ROOT)
    current_html_rel = rel.with_suffix(".html")
    title = md_path.stem.replace("-", " ")
    body = markdown_to_html(md_path.read_text(encoding="utf-8"), current_html_rel)
    section = rel.parts[0] if len(rel.parts) > 1 else "root"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{html.escape(os.path.relpath(ASSETS / 'style.css', (SITE / current_html_rel).parent).replace(os.sep, '/'))}" />
</head>
<body>
  <div class="page">
    <div class="topbar">
      <a class="back" href="{html.escape(os.path.relpath(SITE / 'index.html', (SITE / current_html_rel).parent).replace(os.sep, '/'))}">← 返回投研首页</a>
      <a class="home-link" href="{html.escape(os.path.relpath(SITE / 'all-docs.html', (SITE / current_html_rel).parent).replace(os.sep, '/'))}">全部文档</a>
    </div>
    <section class="hero">
      <div class="eyebrow">{html.escape(section)}</div>
      <h1>{html.escape(md_path.stem)}</h1>
      <p>{html.escape(str(rel))}</p>
    </section>
    <article class="doc">
{body}
    </article>
    <div class="footer">该页面由 Markdown 自动生成。原始文件：{html.escape(str(rel))}</div>
  </div>
</body>
</html>
"""


def render_all_docs(md_files: list[Path]) -> str:
    grouped: dict[str, list[Path]] = {key: [] for key in SECTION_ORDER}
    grouped["root"] = []
    for path in md_files:
        rel = path.relative_to(ROOT)
        section = rel.parts[0] if len(rel.parts) > 1 else "root"
        grouped.setdefault(section, []).append(path)

    cards = []
    for section in ["root"] + SECTION_ORDER:
        items = grouped.get(section, [])
        if not items:
            continue
        lis = []
        for item in items:
            rel = item.relative_to(ROOT)
            href = rel.with_suffix(".html").as_posix()
            lis.append(f'<li><a href="{html.escape(href)}">{html.escape(item.stem)}</a></li>')
        cards.append(
            f"""<section class="section-card">
  <h3>{html.escape(section)}</h3>
  <ul>
    {''.join(lis)}
  </ul>
</section>"""
        )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>All Research Docs</title>
  <link rel="stylesheet" href="_assets/style.css" />
</head>
<body>
  <div class="page">
    <div class="topbar">
      <a class="back" href="index.html">← 返回投研首页</a>
    </div>
    <section class="hero">
      <div class="eyebrow">Library</div>
      <h1>全部文档</h1>
      <p>这里按目录列出所有已经生成 HTML 的研究文档。后续新增 Markdown，只要重新运行一次脚本，就会自动补进来。</p>
    </section>
    <div class="section-list">
      {''.join(cards)}
    </div>
    <div class="footer">当前共生成 {len(md_files)} 个 Markdown 文档的 HTML 镜像。</div>
  </div>
</body>
</html>
"""


def rewrite_root_html(content: str) -> str:
    content = re.sub(r'href="([^"]+)\.md"', r'href="\1.html"', content)
    content = re.sub(r"href='([^']+)\.md'", r"href='\1.html'", content)
    return content


def build() -> None:
    SITE.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "style.css").write_text(CSS, encoding="utf-8")

    md_files = iter_markdown_files()
    for md in md_files:
        rel_html = rel_html_path(md)
        output = SITE / rel_html
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_doc(md, md_files), encoding="utf-8")

    for html_name in ["index.html", "notes.html", "candidates.html", "tickers.html"]:
        src = ROOT / html_name
        if src.exists():
            content = src.read_text(encoding="utf-8")
            (SITE / html_name).write_text(rewrite_root_html(content), encoding="utf-8")

    (SITE / "all-docs.html").write_text(render_all_docs(md_files), encoding="utf-8")


if __name__ == "__main__":
    build()
