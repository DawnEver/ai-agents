---
name: sharp-review-2026-08-01
description: Engineering review findings — acquisition + screening CLI fixes (topic-agnostic)
metadata:
  type: project
---

# Engineering review 2026-08-01

Adversarial review of the acquisition/screening diff. All findings are generic
engineering issues in the `literature-review` tooling — no research-topic content.

## Resolved this session

- **import-screening `out_dir` nesting**: CLI passed the full file path
  (`screening/screening_stage1.jsonl`) to `import_agent_screening`'s `out_dir`,
  which mkdirs then writes `out_dir/screening_stage1.jsonl` → nested directory.
  Fixed to pass the `screening/` dir; added stale-directory migration
  (stage-file → rmtree dir → hoist); success now returns exit 0 (was
  `len(merged)`).
- **IEEE PDF selector drift**: `PDF_BUTTON_SELECTORS` lacked the current
  `.xpl-btn-pdf` / `a[href*="/stamp/stamp.jsp"]` patterns (IEEE rebuilt its
  Angular app). Browser transport could log in but never capture a PDF.
  Added both selectors; verified end-to-end.
- **`--profile` session reuse**: docs claimed `--browser-channel chrome`
  reuses publisher sessions, but without `--profile` a fresh zero-cookie
  context is launched. Docs updated: session reuse requires
  `lit-review login --profile <name>` + `acquire --profile <name>`.
- **Docs hygiene**: `--http-only` is diagnostic/headless-only (not blanket-
  forbidden); `--limit` hard cap 20 documented; no `--headed` flag exists;
  `maybe` items need `--candidate-id`; `--browser-channel` is redundant
  (default); `--approved-by <you>` placeholder → use a real value.

## Still open

- **SR-007**: no automated test covers the import-screening `out_dir` contract
  or the stale-directory migration. Add regression tests.
- **SR-013**: `cli.py` >600 lines; parser registration + handlers overdue for
  extraction (pre-existing).
- **SR-014**: `maybe` decisions silently skipped under auto-approve — documented
  in 03-acquire.md; a louder log line when maybes are present would help.

## Privacy guardrail (this review enforced it)

Workspace/topic research content must never be written into project-level
`memory/`. Only generic engineering knowledge belongs there. See AGENT.md.
