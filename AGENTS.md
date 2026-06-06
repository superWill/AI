# Repository Guidelines

## Project Structure & Module Organization

This repository is a personal research workspace. Top-level folders are independent projects and should keep their own `README.md` current.

- `investment-research/`: active US equity research. Key areas are `notes/`, `tickers/`, `portfolios/`, `dashboards/`, `data/`, `site/`, and `scripts/`.
- `investment-research-2007-apple/`: platform-company research with `companies/`, `daily/`, `framework/`, and `agent/` materials.
- `product-research-business-scenarios/`: product research organized by numbered stages from background to output.
- `embedded-gateway/`: embedded gateway research split by domain, including `heating/`, `fire-alarm/`, and shared `docs/`.
- `tech-research/`, `resumes/`, and root scripts are supporting materials.

## Build, Test, and Development Commands

There is no root build system. Run commands from the relevant project directory.

```bash
cd investment-research
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/fetch_quotes.py
.venv/bin/python scripts/fetch_history.py --tickers LITE AEHR --period 1y
.venv/bin/python scripts/audit_notes.py --threshold 20
python3 scripts/build_html_site.py
```

`fetch_quotes.py` writes daily snapshots, `fetch_history.py` writes OHLCV price CSVs, `audit_notes.py` checks stale ticker market-cap notes, and `build_html_site.py` regenerates `investment-research/site/`.

## Coding Style & Naming Conventions

Use Markdown for research artifacts and keep dates in ISO form (`YYYY-MM-DD`). New research projects should use lowercase English directory names with hyphens, for example `market-research-china-evs/`.

Follow existing naming patterns:

- Research notes: `notes/YYYY-MM-<topic>.md`
- Ticker files: `tickers/<TICKER>.md`
- Portfolio decisions: `portfolios/YYYY-MM-<name>.md`

Python scripts target Python 3, use `pathlib`, type hints where helpful, four-space indentation, and concise module docstrings for script usage.

## Testing Guidelines

No formal test suite is configured. For Python changes, run the affected script directly and include a representative command in your handoff. For research-data changes, run `scripts/audit_notes.py` when ticker valuations or snapshots are touched, and rebuild the HTML site when Markdown navigation or generated pages change.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style messages, often with scopes: `feat(heating): ...`, `docs(heating): ...`, `refactor: ...`. Keep commits focused and describe the research area or script changed.

Pull requests should include a short summary, changed directories, validation commands run, and screenshots only when generated HTML or visual artifacts change. Link related issues or source documents when applicable.

## Security & Configuration Tips

Do not commit credentials, API keys, `.env*`, private keys, `secrets/`, virtualenvs, caches, or Hermes personal config. Keep large raw datasets outside git unless they are small, auditable snapshots intentionally used by the research workflow.
