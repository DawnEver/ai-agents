# Literature-Review

Claude Code agent for systematic literature reviews — discover, screen, acquire, and read academic papers (Zotero sync planned).

## Setup

```bash
# 1. Clone this repo
git clone <this-repo-url>
cd literature-review

# 2. Install in editable mode
pip install -e .

# 3. Install Playwright browser binaries (required for IEEE search + PDF acquisition)
python -m playwright install chromium
```

## Commands

| Command | Description |
|---------|-------------|
| `/literature-review:new <topic>` | Main pipeline. Re-invoking resumes from the latest artifact. |
| `/literature-review:rerun <step> <topic>` | Re-run any single step. |

## Pipeline

`/literature-review:new <topic>` walks a 10-step pipeline with progressive disclosure — `.claude/skills/literature-review/SKILL.md` is the map, each sub-file under `.claude/skills/literature-review/` is the playbook:

| Step | File | What happens |
|------|------|--------------|
| 0 | `00-workspace.md` | ⭐ Create workspace → `workspace.yaml` |
| 1 | `01-brief.md` | ⭐ Research brief + concept taxonomy → user gate |
| 2 | `02-queries.md` | ⭐ Query planning → user gate (SHA-256 binding) |
| 3 | `03-search-screen.md` | Multi-provider probe → search → dedupe → agent screen |
| 4 | `04-acquire.md` | ⭐ Download queue → user gate → browser PDF acquire |
| 5 | `05-ingest.md` | PDF decomposition via paper_pdf_ingest (explicit confirm) |
| 6 | `06-triage.md` | Portfolio triage — rank papers → reading queue (Phase 2) |
| 7 | `07-read.md` | Deep reading + domain lens → paper cards (Phase 2) |
| 8 | `08-synthesis.md` | Cross-paper comparison → synthesis, optional (Phase 2) |
| 9 | `09-zotero.md` | Zotero bridge bidirectional sync (Phase 3) |

**Core principle**: Brief before query. Query before search. Gate before acquire. Ingest requires explicit confirm. No opinion without reading the paper.

## References

This project builds on and integrates ideas from:

- [github.com/FENGSY1/_literture_review](https://github.com/FENGSY1/_literture_review) — Original IEEE literature scout prototype, approval-gate pattern, SHA-256 provenance chain
- [github.com/DawnEver/review-agent](https://github.com/DawnEver/review-agent) — AI-powered batch literature review: PDF extraction → litellm → structured CSV output
- [github.com/DawnEver/paper_pdf_ingest](https://github.com/DawnEver/paper_pdf_ingest) — PDF-to-markdown decomposition engine used by the ingest step
