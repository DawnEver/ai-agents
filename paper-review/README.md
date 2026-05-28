# Paper-Review

Claude Code agent for reviewing academic papers. Ingest a PDF, generate a shared summary, fan out multi-angle 锐评 across Codex / Claude / vision agents, then polish a user-written draft into publishable English reviewer comments.

Entry point: `/paper-review:new <path-to.pdf>` — see `CLAUDE.md` for the full pipeline.

## Directory Layout

```
.claude/
  skills/
    paper-review/       — main pipeline (progressive disclosure SKILL.md + 01–08)
    paper-rerun/        — re-run any single step
  agents/               — 4 reviewers + polisher
ongoing/                — papers currently under review
  <slug>/
    0-raw.pdf           — original (gitignored at folder level)
    1-paper-text/       — step 01: ingested text + images
      paper.md          — title + abstract + section index (entry point)
      md/               — per-section markdown
      img/sec*/         — per-section images + rendered figure/table pages
      INDEX.md          — figure/table number ↔ file mapping
      appended/         — if PDF contains multiple papers (e.g. conference versions)
    2-review/           — steps 02–05: review materials
      summary.md        — consensus (every agent reads first, incl. Obvious gaps)
      angles.md         — chosen angles + optional router overrides
      critiques/        — one .md per reviewer agent
      critiques.md      — aggregated, deduped, ranked
    3-response/         — steps 06–07: user draft → publishable response
      draft.md          — user-written draft
      final.md          — polished plain-text review
archived/<slug>/        — completed reviews (mirrors ongoing/ 0-1-2-3 structure)
style/profile.md        — GLOBAL: synthesised voice + 10-slug rolling samples
critiques-library/
  angles.md             — GLOBAL: deduped angle library
templates/              — default-angles, polish-checklist, summary-template, reviewer-voice
```
