# CHP Literature Review — Session Summary

2026-07-24 | Multi-provider search + Zotero sync

## Achievements

### Multi-Provider Architecture
- Implemented **Semantic Scholar** provider (REST API, API key via `.env`, `adapt_expression` for keyword syntax, 1.5s rate limit)
- Implemented **arXiv** provider (Atom XML API, `adapt_expression` for prefix syntax)
- Implemented **DBLP** provider (JSON API, client-side year filtering)
- Added `BaseProvider.adapt_expression()` — provider-specific Boolean-to-native query translation
- Added `BaseProvider.extract_records()` — provider-specific record envelope extraction (IEEE=`records`, S2=`data`)
- Added `BaseProvider._search_with_retries()` — exponential backoff for transient errors
- Multi-provider dispatch in orchestrator (`run_search` accepts `provider: list[str]`)
- Per-provider probe namespacing (`probe/<provider_name>/`)

### Zotero Sync
- SQLite mode: direct insertion with automatic PDF attachment to Zotero storage
- Better BibTeX CAYW mode: via local HTTP API (Zotero running, no close needed)
- Auto-detection: tries CAYW first, falls back to SQLite
- Integrated into `literature_review/export/zotero.py` → `sync_papers()`

### Paywall Methodology
- Documented decision tree: arXiv → OpenAlex OA check → author preprint search → browser auth
- Publisher-specific tactics: Elsevier, SciTePress, ACM, IEEE, Springer
- Multi-scenario: campus IP, VPN, EZProxy, OpenAthens, off-campus
- Real Chrome (`channel="chrome"`) bypasses CAPTCHA vs headless
- Skill file: `.claude/skills/literature-review/03-acquire-paywall.md`

### CHP Review Results
- 7 papers included from 107 candidates (IEEE 42 + S2 65)
- 5 PDFs acquired (all arXiv), 2 paywall-pending (Elsevier + SciTePress)
- 5 PDFs ingested + synced to Zotero "Enginnering" with PDF attachments
- Deep reading pending (AI model API key needed)

### Key Fixes
- `adapt_expression` hook added to `run_search()` (was only in `run_probe()`)
- Browser profile path → `%LOCALAPPDATA%/literature-review/browser-profiles/`
- TOML top-level keys must precede `[table]` sections (rtoml parsing constraint)
- `fieldsOfStudy` type handling (list of dicts OR strings) in S2 normalize_record

## Files
- `literature_review/providers/semantic_scholar.py` (new)
- `literature_review/providers/arxiv.py` (new)
- `literature_review/providers/dblp.py` (new)
- `literature_review/export/zotero.py` (new)
- `.claude/skills/literature-review/03-acquire-paywall.md` (new)
- Multiple pipeline/provider/CLI updates
