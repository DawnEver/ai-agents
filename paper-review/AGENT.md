# Paper-Review

Claude Code agent for reviewing academic papers. Ingest a PDF, build a shared summary, fan out 4-angle 锐评 across Sonnet subagents and Codex/DeepSeek takeover, then polish an orchestrator-generated draft (user-edited) into publishable **plain-text** reviewer comments.

## Architecture

```
/paper-review:new <pdf>                   (single entry, orchestrator)
  ├── 01-ingest         pdf → 1-paper-text/paper.md + md/ + img/sec*/ + INDEX.md  (marker-pdf)
  ├── 02-consensus      2-review/summary.md (shared truth, includes Obvious gaps)
  ├── 02b-literature    top N refs (paper + IEEE Xplore) + author background → 2-review/literature.md
  ├── ⭐ 03-angle-gate  4 defaults + library, user confirms
  ├── 04-fanout         spawn reviewers in parallel (Sonnet vision + takeover codex/deepseek)
  ├── 05-aggregate      merge → 2-review/critiques.md
  ├── ⭐ 06-user-draft  orchestrator generates complete draft, user edits (hard gate, SESSION BOUNDARY)
  ├── 07-polish         polisher-english → 3-response/final.md (PLAIN TEXT)
  └── 08-archive        ongoing/<slug>/ → archived/<slug>/, update global style + angles
                        + optional postmortem (per-weakness scoring)
```

## Commands

| Command | Description |
|---------|-------------|
| `/paper-review:new <pdf>` | Main pipeline. Re-invoking with a slug resumes from the latest non-empty artifact (see SKILL.md resume table). |
| `/paper-review:rerun <step> <slug>` | Re-run any single step (replaces old archive/repolish skills). |

## Pipeline Flow

```
/paper-review:new ongoing/<slug>/0-raw.pdf
  → marker-pdf → 1-paper-text/paper.md (title + abstract + section index)
                  1-paper-text/md/01-introduction.md, 02-related-work.md, ...
                  1-paper-text/img/sec01/, sec02/, ...
                  1-paper-text/INDEX.md (figure-number ↔ file ↔ caption)
  → write 2-review/summary.md (incl. Obvious gaps section) — shared ground truth
  → 2-review/literature.md: top N refs (from paper + IEEE Xplore) + author background (first/corresponding author prior work, affiliation, research focus) → landscape summary
  → ⭐ ANGLE GATE: 4 defaults + top library angles → user picks/edits
  → fanout (parallel):
      reviewer-novelty       (sonnet-vision; novelty + related-work)
      reviewer-methodology   (takeover-codex by default; methodology + reproducibility)
      reviewer-experiments   (sonnet-vision; experiments + figures + writing)
      reviewer-freestyle     (sonnet-vision; wildcard)
      → routing from agent frontmatter `router:`, overridable in angles.md
      → each writes 2-review/critiques/<angle>.md
  → aggregate → 2-review/critiques.md (deduped, ranked, conflicts flagged)
  → ⭐ USER DRAFT (session boundary): orchestrator generates complete draft from selected critiques, user edits, then re-invokes /paper-review:new <slug>
  → polisher-english → 3-response/final.md (plain text, venue-form ready)
  → archive: move ongoing/<slug>/ → archived/<slug>/
            rolling update of style/profile.md (10 recent samples + synthesised voice)
            deduped update of critiques-library/angles.md (semantic merge + aliases)
            optional postmortem.md (per-weakness valid/partial/hallucinated)
```

**Core principle**: Consensus before fanout. Fanout before draft. Draft before polish. No agent forms an opinion without first reading `summary.md`. The polisher never invents content.

`paper-review` uses **progressive disclosure** — `SKILL.md` is the map, each step's sub-file is the detailed playbook:
`.claude/skills/paper-review/{01-ingest,02-consensus,03-angle-gate,04-fanout,05-aggregate,06-user-draft,07-polish,08-archive}.md`

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
      md/               — per-section markdown (01-intro.md, 02-..., ...)
      img/sec*/         — per-section images + rendered figure/table pages
      INDEX.md          — figure/table number ↔ file mapping
      appended/         — if PDF contains multiple papers (e.g. conference versions)
    2-review/           — steps 02–05: review materials
      summary.md        — consensus (every agent reads first, incl. Obvious gaps)
      angles.md         — chosen angles + optional router overrides
      critiques/        — one .md per reviewer agent
      critiques.md      — aggregated, deduped, ranked
    3-response/         — steps 06–07: generated draft → publishable response
      draft.md          — orchestrator-generated draft (user-edited)
      final.md          — polished plain-text review
archived/<slug>/        — completed reviews (mirrors ongoing/ 0-1-2-3 structure)
style/profile.md        — GLOBAL: synthesised voice + 10-slug rolling samples
critiques-library/
  angles.md             — GLOBAL: deduped angle library (name, aliases, hit-count, precision, sample)
templates/              — default-angles, polish-checklist, summary-template
```

## Model Routing

Routing is declared **per agent** in frontmatter `router:`. Defaults:
- **reviewer-novelty** — `sonnet-vision`
- **reviewer-methodology** — `takeover-codex` (deep reasoning; DeepSeek as alternative)
- **reviewer-experiments** — `sonnet-vision` (figures need vision)
- **reviewer-freestyle** — `sonnet-vision`

`angles.md` may override per-paper. Step 04 reads: override > frontmatter default.

For takeover (Codex/DeepSeek), the prompt is fully self-contained — `summary.md` and the relevant section excerpts are **inlined** into the prompt, because the takeover process cannot read this conversation and OneDrive paths with spaces are unreliable across processes.
