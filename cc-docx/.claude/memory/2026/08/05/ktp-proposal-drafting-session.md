---
name: ktp-proposal-drafting-session
description: KTP proposal drafting session — filled application form, workplan, commercial impacts; ==highlight== feature added to harness
metadata:
  type: project
---

# KTP proposal drafting — SMT × UoN PEMC (2026-08-05)

Drafted the KTP application deliverables (24-month Classic KTP, 1 associate) from the Fact Find Form source, using the cc-docx markdown-first workflow.

## What was produced

- **`workspace/260805-ktp_proposal/application-form.md`** — filled all answer slots: title/duration/innovation area, team tables (KB lead + supervisor 1, business contact, business supervisor — names kept local-only), Project Summary (~163w), Public Description (~41w), Scope, Q18–Q36, data collection Q1–17/19, finances (travel £3,880, consumables £8,600, company costs £10,400 — all estimates in highlight).
- **`workspace/260805-ktp_proposal/commercial-impacts.md`** — 2 activities × (In Project + Y1–Y5): software ramps 150k→3,000k, services 50k→300k; NP margins 60% software / 30% services; Y5 total £3.3M revenue / £1.89M NPBT. Calculations section with formulas.
- **`workspace/260805-ktp_proposal/workplan.md`** — standard activities 6.0m (induction 0.5, T&D 2.4=10%, holidays 2.6, mini 0.5) + 6 stages 18.0m (0.5m steps in first 6 months, 1.0m after) = **24.0m total** matching declared duration; 21 steps with milestones M1–M12; 6-item risk register; Time Plan table (14 cols, quarters 0–39).
- **Rendered to Word** at `<ktp-project-dir>/` (templates live there, NOT in repo — handoff's `<ktp-project-dir>/ref` path inside repo was wrong): `KTP Application Form 26_27 R2 (filled draft).docx`, `Workplan (filled draft).docx`, `Commercial impacts (filled draft).docx`. All round-trip verified (re-extract diff clean except filename/NBSP/trailing-space).

## New harness capability (this session)

- **`==text==` yellow-highlight syntax** added to `scripts/md2docx.py` (render → `w:highlight w:val="yellow"`, nested `==**bold**==` supported) and `scripts/docx2md.py` (extract back). Round-trip verified. Documented in `AGENT.md`.
- Patch scripts live in `.scratch/patch-{application,commercial,workplan}.py` (local-only, idempotent, anchor-keyed).

## Conventions learned

- md2docx table separators must match docx2md output (`width+1` dashes) or round-trip diff fails.
- Time Plan table is **14 columns** (task + 13 quarter columns 0–39).
- Word normalizes trailing spaces and NBSP; template instruction lines differ only by those.
- Keep question text on choice questions; mark answers as `**bold**` on the "Select one:" line or "(selected)" on list items.

## Open items (user to confirm — all marked with ==highlight== in Word)

- KTA name, UoN project manager name (UoN KTP team)
- Q12 SIC code: filled 71121 from Companies House, pending SMT confirmation
- Q39/Q40: filled "No", pending SMT confirmation
- Salary evidence for Q34, budget numbers (UoN KTP team), commercial assumptions (customer ramp, £150k ASP, £500 day rate, 60%/30% margins)
- Dr Zou dual role (KB lead + supervisor 1)
- Q36 publications count (2–3)
