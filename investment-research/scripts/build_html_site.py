from __future__ import annotations

import html
import os
import re
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
  --bg: #f2ede3;
  --bg-2: #ebe3d4;
  --paper: #fffdf8;
  --ink: #1f1c17;
  --muted: #6c665b;
  --line: #ded5c6;
  --line-2: #efe8dd;
  --accent: #8f2d14;
  --accent-2: #b94f1d;
  --accent-soft: #f4e3da;
  --good: #1f6a4a;
  --warn: #9d6411;
  --navy: #1d2b45;
  --shadow: 0 22px 60px rgba(54, 40, 19, 0.08);
  --shadow-soft: 0 10px 24px rgba(54, 40, 19, 0.05);
  --radius-xl: 26px;
  --radius-lg: 20px;
  --radius-md: 14px;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: "Iowan Old Style", "Palatino Linotype", "Times New Roman", serif;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(143, 45, 20, 0.10), transparent 24%),
    radial-gradient(circle at top right, rgba(29, 43, 69, 0.06), transparent 22%),
    linear-gradient(180deg, #f7f3ea 0%, var(--bg) 55%, var(--bg-2) 100%);
}
a {
  color: inherit;
  text-decoration: none;
}
.site-shell {
  min-height: 100vh;
}
.page {
  max-width: 1260px;
  margin: 0 auto;
  padding: 20px 18px 64px;
}
.topbar {
  position: sticky;
  top: 10px;
  z-index: 20;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  padding: 12px 14px;
  background: rgba(255, 253, 248, 0.82);
  border: 1px solid rgba(222, 213, 198, 0.8);
  border-radius: 16px;
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(14px);
}
.nav-cluster {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.back, .home-link, .nav-link {
  color: var(--accent);
  font-weight: 700;
  font-size: 14px;
}
.nav-link.secondary {
  color: var(--navy);
}
.hero {
  background:
    linear-gradient(135deg, rgba(29, 43, 69, 0.96), rgba(143, 45, 20, 0.94));
  color: #fff9f3;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius-xl);
  padding: 28px;
  box-shadow: var(--shadow);
  margin-bottom: 22px;
  position: relative;
  overflow: hidden;
}
.hero::before,
.hero::after {
  content: "";
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.06);
}
.hero::before {
  width: 220px;
  height: 220px;
  right: -40px;
  top: -60px;
}
.hero::after {
  width: 320px;
  height: 320px;
  right: 10%;
  bottom: -180px;
}
.hero > * {
  position: relative;
  z-index: 1;
}
.eyebrow {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: rgba(255, 249, 243, 0.72);
  margin-bottom: 10px;
}
h1 {
  margin: 0 0 10px;
  font-size: clamp(32px, 5vw, 54px);
  line-height: 0.96;
}
.hero p {
  margin: 0;
  color: rgba(255, 249, 243, 0.84);
  line-height: 1.7;
  max-width: 780px;
  font-size: 16px;
}
.hero-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}
.hero-stat {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.10);
}
.hero-stat-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255,249,243,0.68);
  margin-bottom: 6px;
}
.hero-stat-value {
  font-size: 24px;
  font-weight: 700;
}
.doc {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow);
  padding: 30px 28px;
}
.doc-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 290px;
  gap: 20px;
}
.doc-main {
  min-width: 0;
}
.doc-sidebar {
  display: grid;
  gap: 14px;
  align-self: start;
  position: sticky;
  top: 86px;
}
.sidebar-card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 18px;
  box-shadow: var(--shadow-soft);
  padding: 16px;
}
.sidebar-title {
  margin: 0 0 10px;
  font-size: 14px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}
.toc-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}
.toc-list li a {
  color: var(--navy);
  font-size: 14px;
  line-height: 1.45;
}
.summary-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}
.summary-list li {
  display: grid;
  gap: 2px;
}
.summary-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}
.summary-value {
  font-size: 14px;
  line-height: 1.5;
  color: var(--ink);
}
.doc h1, .doc h2, .doc h3, .doc h4, .doc h5, .doc h6 { line-height: 1.16; margin-top: 1.55em; margin-bottom: 0.55em; }
.doc h1:first-child, .doc h2:first-child { margin-top: 0; }
.doc h2 {
  font-size: 28px;
  padding-top: 8px;
  border-top: 1px solid var(--line-2);
}
.doc h3 {
  font-size: 22px;
}
.doc h4 {
  font-size: 18px;
}
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
  background: #1b212c;
  color: #f8f3ea;
  padding: 16px;
  border-radius: 14px;
  overflow-x: auto;
  margin: 0 0 1.2em;
  border: 1px solid rgba(255,255,255,0.05);
}
.doc pre code { background: transparent; padding: 0; color: inherit; }
.doc hr { border: 0; border-top: 1px solid var(--line); margin: 1.6em 0; }
.doc blockquote {
  margin: 0 0 1.2em;
  padding: 0.8em 1em;
  border-left: 4px solid var(--accent-2);
  background: #faf4ed;
  color: #514b41;
  border-radius: 0 14px 14px 0;
}
.doc table {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 1.2em;
  display: block;
  overflow-x: auto;
  box-shadow: inset 0 0 0 1px var(--line);
  border-radius: 12px;
}
.doc th, .doc td {
  border: 1px solid var(--line);
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
  white-space: nowrap;
}
.doc th {
  background: #f5efe6;
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
  gap: 16px;
}
.section-card {
  grid-column: span 6;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 20px;
  box-shadow: var(--shadow);
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}
.section-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 44px rgba(54, 40, 19, 0.1);
  border-color: #d5c4ab;
}
.section-card h3 { margin: 0 0 12px; }
.section-card ul { margin: 0; padding-left: 18px; }
.section-card li { margin: 10px 0; line-height: 1.55; }
.section-card a { color: var(--accent); }
.doc-link-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 16px;
}
.doc-link-card {
  grid-column: span 4;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 20px;
  box-shadow: var(--shadow-soft);
  padding: 18px;
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}
.doc-link-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 44px rgba(54, 40, 19, 0.1);
  border-color: #d5c4ab;
}
.doc-link-card h3 {
  margin: 0 0 10px;
  font-size: 20px;
}
.doc-link-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
}
.section-kicker {
  display: inline-flex;
  margin-bottom: 10px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #f4eee4;
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border: 1px solid var(--line);
}
.doc-header-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 240px;
  gap: 18px;
  align-items: end;
}
.doc-stat-stack {
  display: grid;
  gap: 10px;
}
.doc-stat {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.1);
  padding: 12px 14px;
  border-radius: 16px;
}
.doc-stat-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255,249,243,0.68);
  margin-bottom: 4px;
}
.doc-stat-value {
  font-size: 16px;
  color: #fff9f3;
}
.footer {
  margin-top: 20px;
  color: var(--muted);
  font-size: 13px;
  text-align: center;
}
@media (max-width: 1080px) {
  .doc-layout {
    grid-template-columns: 1fr;
  }
  .doc-sidebar {
    position: static;
  }
}
@media (max-width: 900px) {
  .hero-grid,
  .doc-link-grid,
  .section-list {
    grid-template-columns: 1fr 1fr;
  }
  .doc-link-card,
  .section-card {
    grid-column: span 1;
  }
  .doc-header-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .page {
    padding: 16px 12px 40px;
  }
  .topbar {
    top: 6px;
    padding: 10px 12px;
  }
  .hero {
    padding: 22px 18px;
  }
  .hero-grid,
  .doc-link-grid,
  .section-list { grid-template-columns: 1fr; }
  .section-card,
  .doc-link-card { grid-column: span 1; }
  .doc {
    padding: 22px 18px;
  }
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


def slugify(text: str) -> str:
    slug = re.sub(r"<[^>]+>", "", text)
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff\s-]", "", slug).strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    return slug or "section"


def html_href_for_markdown(target_href: str, current_html_rel: Path) -> str:
    target = target_href.split("#", 1)[0]
    fragment = ""
    if "#" in target_href:
        fragment = "#" + target_href.split("#", 1)[1]
    if target.startswith(("http://", "https://", "mailto:")):
        return target_href
    root_resolved = ROOT.resolve()
    if target.startswith("/"):
        resolved_target = (ROOT / target.lstrip("/")).resolve()
    else:
        resolved_target = (ROOT / current_html_rel.parent / target).resolve()
        if not str(resolved_target).startswith(str(root_resolved)):
            resolved_target = (ROOT / target.lstrip("./")).resolve()
    try:
        target_path = resolved_target.relative_to(root_resolved)
    except ValueError:
        return target_href
    target_parts = list(target_path.parts)
    if any(part in IGNORE_DIRS for part in target_parts):
        return target_href
    if target_path.suffix == ".md":
        target_path = target_path.with_suffix(".html")
    return os.path.relpath(SITE / target_path, (SITE / current_html_rel).parent).replace(os.sep, "/") + fragment


def convert_inline(text: str, current_html_rel: Path) -> str:
    linebreak_token = "__HTML_BR__"
    text = text.replace("<br />", linebreak_token)
    escaped = html.escape(text)
    escaped = re.sub(
        r"&lt;(https?://[^&]+)&gt;",
        lambda m: f'<a href="{html.escape(m.group(1), quote=True)}">{html.escape(m.group(1))}</a>',
        escaped,
    )
    escaped = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)

    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        href = html.unescape(match.group(2))
        final_href = html_href_for_markdown(href, current_html_rel)
        return f'<a href="{html.escape(final_href, quote=True)}">{label}</a>'

    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, escaped)
    escaped = escaped.replace(linebreak_token, "<br />")
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
            heading_text = convert_inline(heading_match.group(2), current_html_rel)
            heading_id = slugify(heading_match.group(2))
            out.append(f'<h{level} id="{heading_id}">{heading_text}</h{level}>')
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
            continuation: list[str] = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                next_stripped = next_line.strip()
                if not next_stripped:
                    break
                if re.match(r"^(#{1,6})\s+", next_stripped):
                    break
                if re.match(r"^[-*]\s+", next_stripped) or re.match(r"^\d+\.\s+", next_stripped):
                    break
                if next_stripped.startswith("|") and j + 1 < len(lines) and re.match(r"^\s*\|?[-:\s|]+\|?\s*$", lines[j + 1]):
                    break
                if next_stripped.startswith(">") or next_stripped.startswith("```") or next_stripped == "---":
                    break
                if next_line.startswith("  ") or next_line.startswith("\t") or next_stripped.startswith("<http"):
                    continuation.append(next_stripped)
                    j += 1
                    continue
                break
            if continuation:
                content = content + "<br />" + "<br />".join(continuation)
            if not in_list or list_tag != tag:
                close_list()
                out.append(f"<{tag}>")
                in_list = True
                list_tag = tag
            out.append(f"<li>{convert_inline(content, current_html_rel)}</li>")
            i = j if continuation else i + 1
            continue

        paragraph.append(line)
        i += 1

    flush_paragraph()
    close_list()
    return "\n".join(out)


def extract_headings(md_text: str) -> list[tuple[int, str, str]]:
    headings: list[tuple[int, str, str]] = []
    seen: dict[str, int] = {}
    for line in md_text.replace("\r\n", "\n").split("\n"):
        match = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
        if not match:
            continue
        level = len(match.group(1))
        text = match.group(2).strip()
        if level < 2 or not text:
            continue
        slug = slugify(text)
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        if count:
            slug = f"{slug}-{count + 1}"
        headings.append((level, text, slug))
    return headings


def count_words(md_text: str) -> int:
    plain = re.sub(r"`[^`]+`", " ", md_text)
    plain = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", plain)
    plain = re.sub(r"[#>*|`-]", " ", plain)
    plain = re.sub(r"\s+", " ", plain)
    return len(plain.strip().split())


def summarize_doc(md_path: Path, md_text: str) -> tuple[str, str]:
    rel = md_path.relative_to(ROOT)
    section = rel.parts[0] if len(rel.parts) > 1 else "root"
    summary_map = {
        "notes": "市场、公司或主题研究的阶段性结论。",
        "dashboards": "持续跟踪的候选池、评分规则和日更日志。",
        "agents": "Agent 提示词、跨平台使用方法和自动化模板。",
        "portfolios": "组合、仓位和执行层面的判断。",
        "tickers": "单只股票的研究卡、跟踪信号和估值框架。",
        "root": "仓库入口与使用说明。",
    }
    return section, summary_map.get(section, "研究文档。")


def render_doc(md_path: Path, all_md: list[Path]) -> str:
    rel = md_path.relative_to(ROOT)
    current_html_rel = rel.with_suffix(".html")
    title = md_path.stem.replace("-", " ")
    md_text = md_path.read_text(encoding="utf-8")
    body = markdown_to_html(md_text, current_html_rel)
    section, section_summary = summarize_doc(md_path, md_text)
    headings = extract_headings(md_text)
    words = count_words(md_text)
    toc_items = ""
    for level, text, slug in headings[:14]:
      indent = " style=\"padding-left:{}px\"".format((level - 2) * 14) if level > 2 else ""
      toc_items += f'<li{indent}><a href="#{html.escape(slug)}">{html.escape(text)}</a></li>'
    toc_html = f'<ul class="toc-list">{toc_items}</ul>' if toc_items else "<p>这篇文档没有二级目录。</p>"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{html.escape(os.path.relpath(ASSETS / 'style.css', (SITE / current_html_rel).parent).replace(os.sep, '/'))}" />
</head>
<body>
  <div class="site-shell">
  <div class="page">
    <div class="topbar">
      <div class="nav-cluster">
        <a class="back" href="{html.escape(os.path.relpath(SITE / 'index.html', (SITE / current_html_rel).parent).replace(os.sep, '/'))}">← 返回投研首页</a>
        <a class="nav-link secondary" href="{html.escape(os.path.relpath(SITE / 'all-docs.html', (SITE / current_html_rel).parent).replace(os.sep, '/'))}">全部文档</a>
      </div>
      <div class="nav-cluster">
        <a class="home-link" href="{html.escape(os.path.relpath(SITE / 'notes.html', (SITE / current_html_rel).parent).replace(os.sep, '/'))}">Notes</a>
        <a class="home-link" href="{html.escape(os.path.relpath(SITE / 'candidates.html', (SITE / current_html_rel).parent).replace(os.sep, '/'))}">Candidates</a>
        <a class="home-link" href="{html.escape(os.path.relpath(SITE / 'tickers.html', (SITE / current_html_rel).parent).replace(os.sep, '/'))}">Tickers</a>
      </div>
    </div>
    <section class="hero">
      <div class="doc-header-grid">
        <div>
          <div class="eyebrow">{html.escape(section)}</div>
          <h1>{html.escape(md_path.stem)}</h1>
          <p>{html.escape(section_summary)}</p>
          <div class="meta-row">
            <span class="pill">{html.escape(str(rel))}</span>
            <span class="pill">{words} words</span>
            <span class="pill">{len(headings)} sections</span>
          </div>
        </div>
        <div class="doc-stat-stack">
          <div class="doc-stat">
            <div class="doc-stat-label">Document Type</div>
            <div class="doc-stat-value">{html.escape(section.title())}</div>
          </div>
          <div class="doc-stat">
            <div class="doc-stat-label">Reading Mode</div>
            <div class="doc-stat-value">Research Memo</div>
          </div>
        </div>
      </div>
    </section>
    <div class="doc-layout">
      <article class="doc doc-main">
{body}
      </article>
      <aside class="doc-sidebar">
        <section class="sidebar-card">
          <h3 class="sidebar-title">文档导航</h3>
          {toc_html}
        </section>
        <section class="sidebar-card">
          <h3 class="sidebar-title">阅读提示</h3>
          <ul class="summary-list">
            <li><span class="summary-label">先看什么</span><span class="summary-value">先读一段话结论，再看表格和风险点。</span></li>
            <li><span class="summary-label">适合用途</span><span class="summary-value">复盘、比较、回查研究底稿。</span></li>
            <li><span class="summary-label">建议动作</span><span class="summary-value">如果文档内容改变了 thesis，再回到候选池或组合页更新判断。</span></li>
          </ul>
        </section>
      </aside>
    </div>
    <div class="footer">该页面由 Markdown 自动生成。原始文件：{html.escape(str(rel))}</div>
  </div>
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
  <span class="section-kicker">{html.escape(section)}</span>
  <h3>{html.escape(section.title())}</h3>
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
      <div class="hero-grid">
        <div class="hero-stat"><div class="hero-stat-label">Documents</div><div class="hero-stat-value">{len(md_files)}</div></div>
        <div class="hero-stat"><div class="hero-stat-label">Sections</div><div class="hero-stat-value">{len([k for k in grouped if grouped[k]])}</div></div>
        <div class="hero-stat"><div class="hero-stat-label">Primary</div><div class="hero-stat-value">Notes</div></div>
        <div class="hero-stat"><div class="hero-stat-label">Workflow</div><div class="hero-stat-value">Markdown → HTML</div></div>
      </div>
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
