---
name: ktp-proposal-review-fixes-workflow
description: KTP review fixes + workflow restructure — workspace/project.toml layout, dated outputs, track-changes bug fixes, Time Plan 3.0/quarter model
metadata:
  type: project
---

# KTP proposal review fixes & workflow restructure (2026-08-05, second pass)

Follow-up to `ktp-proposal-drafting-session.md`. The user reviewed the Word deliverables; three rounds of fixes + a workflow restructure landed.

## Workflow restructure (user-requested)

- **`work/` → `workspace/<yyMMdd>-<project>/`** — e.g. `workspace/260805-ktp_proposal/`. `.gitignore`, `.claude/settings.json` (Write perms), README, SKILL.md, 01/03-extract-render phase files, memory files all updated.
- **Per-project `project.toml`** — `[project]` (name, slug, date, **iteration** count, duration/associates/ktp_type), `[source]` (original template paths under `<ktp-project-dir>/ref`), `[delivery]` (output dir + dated filenames), `[documents]` (md working copies). Bump `iteration` on every substantive draft revision before re-render.
- **Dated output convention** — `md2docx.py` default output name is now `out/<stem>-<yyMMdd>.docx` (traceable renders); explicit path still overrides. Deliverables renamed: `KTP Application Form 26_27 R2 (filled draft)-260805.docx`, `Workplan (filled draft)-260805.docx`, `Commercial impacts (filled draft)-260805.docx`.

## Track-changes (--track-changes) review mode — three rounds of root-cause fixes

Unchanged-block detection kept misjudging untouched template content as changed (revision-marked in red). Each round fixed one layer in `scripts/md2docx.py`:

1. **Markdown markers**: compare via `_md_plain()` (parse_inline stripped) — template headings carry `**bold**` in the md transcript, so raw text comparison always "differed".
2. **Whitespace + curly quotes**: `_norm_ws()` collapses runs of whitespace (double spaces, NBSP) to single spaces and normalises ’ ‘ " " to straight quotes — the docx carries these, the md doesn't.
3. **Whole-cell paragraphs**: template cells can split one sentence across 3 paragraphs (e.g. the T&D description); comparison must join all cell paragraphs, not just `paras[0]`.
4. **Bold intent**: same text but md adds bold the template lacks (`Select one: Yes / **No**` answer marks) = intentional change → rewrite + revision; template bold (headings) stays untouched.
5. `sync_table` propagates the track flag to every cell (was defaulting to False for tables).

Also: revision author renamed to **"AI Agent"** (user request; was "Claude Code (AI)").

## Time Plan effort model (user caught the sums)

- Every quarter column (3 months) must sum to **3.0** (associate full-time) — distribution was 2.1–3.6, fixed to exactly 3.0 per column.
- **Stage 1 row was missing** from Time Plan (template only pre-populates Stage 2–6) → total was 22.0 ≠ 24.0; added Stage 1 (1.2 + 0.8).
- Stage title months aligned with the Time Plan distribution: 0-6 / 3-9 / 6-12 / 9-16 / 15-21 / 18-24.
- Verified self-consistency: standard activities 6.0 + stages 18.0 = Time Plan rows 24.0 = total-effort box 24; each quarter column = 3.0.

## Content review fixes (user: "check for similar problems")

- **Q18**: removed "co-authoring the project definition" (internal-process flavour, same class as Q21's FFF co-author sentence).
- **Q21**: removed "co-authored the Fact Find Form with SMT's CTO..." — abrupt; Q21 is a background question.
- **Q22**: de-duplicated vs Q21 (10+ years / holistic platforms verbatim repeat) and vs Q32 (half-day supervision details) — Q22 now keeps supervisor positioning only.
- **Commercial formula made self-consistent**: Y1 = 2 accounts × ~£75k = £150k; Y5 = 20 accounts × £150k = £3.0M (was 20×£150k + £200k upgrades = £3.2M ≠ table). Services row was already consistent (100d×£500=£50k; 600d×£500=£300k). Q29 wording synced.
- **GBP format**: user wants "150,000 GBP" (GBP after the amount) — applied throughout commercial + Q29.

## Conventions learned (additional)

- Time Plan column totals must equal the quarter length in months (3.0) — reviewers check this.
- Template Time Plan only pre-populates Stage 2–6 rows; Stage 1 effort must be added explicitly.
- Stage title months should match the Time Plan distribution, not an independent calendar.
- Word locks files being reviewed — renders fail with PermissionError until closed; render to a temp path meanwhile.
- Review-mode renders keep template-intrinsic formatting (yellow-highlight headings, NBSP); re-extract diffs against md show these as expected, non-content differences.

## Open items (unchanged from drafting session — all ==highlight== in Word)

- KTA name, UoN project manager name; Q12 SIC 71121 pending SMT confirmation; Q39/Q40 "No" pending; salary evidence Q34; budget numbers (UoN KTP team); commercial assumptions (account ramp, £75k→£150k licence values, £500 day rate, 60%/30% margins); Dr Zou dual role; Q36 papers (2–3).
