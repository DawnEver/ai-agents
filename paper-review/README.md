# Paper-Review

Claude Code agent for reviewing academic papers. Ingest a PDF, profile the literature, build a shared summary (folding in landscape and venue type), fan out 4-angle 锐评 across Sonnet/Codex/DeepSeek, then polish a user-edited draft into publishable plain-text reviewer comments.

## Setup

```bash
# 1. Clone this repo
git clone https://github.com/DawnEver/paper-review.git
cd paper-review

# 2. Clone the ingest library
git clone https://github.com/DawnEver/paper_pdf_ingest.git

# 3. Create shared venv and install the library
python -m venv ~/.local/share/paper-review-venv
~/.local/share/paper-review-venv/bin/pip install -e paper_pdf_ingest/
```

The pipeline's ingest step calls `scripts/ingest.py`, which delegates to `paper_pdf_ingest`.

## Commands

| Command | Description |
|---------|-------------|
| `/paper-review:new <pdf>` | Main pipeline. Re-invoking with a slug resumes from the latest artifact. |
| `/paper-review:rerun <step> <slug>` | Re-run any single step. |

## Pipeline

`/paper-review:new <pdf>` walks a 9-step pipeline with progressive disclosure — `SKILL.md` is the map, each sub-file under `.claude/skills/paper-review/` is the playbook:

| Step | File | What happens |
|------|------|--------------|
| 0 | `00-language.md` | Pick intermediate-file language (en/zh) |
| 1 | `01-ingest.md` | PDF → per-section markdown + extracted figures |
| 2 | `02-literature.md` | Search references + author background → `literature.md` |
| 2b | `02b-consensus.md` | Write `summary.md` — shared truth (literature + venue + gaps), user confirms |
| 3 | `03-angle-gate.md` | Propose angles from defaults + library, user confirms |
| 4 | `04-fanout.md` | Spawn 4 reviewers in parallel (Sonnet vision + Codex/DeepSeek takeover) |
| 5 | `05-aggregate.md` | Merge, dedupe, rank → `critiques.md`; user picks |
| 6 | `06-user-draft.md` | Orchestrator generates complete draft; user edits (session boundary) |
| 7 | `07-polish.md` | `polisher-english` → plain-text `final.md` |
| 8 | `08-archive.md` | Move to `archived/YYMMDD/<slug>/`, update style + angle library |

**Core principle**: Literature before consensus. Consensus before fanout. Fanout before draft. Draft before polish. No opinion without reading `summary.md`. Polisher never invents.

## Model Routing

| Agent | Default router |
|-------|---------------|
| novelty, experiments, freestyle | `sonnet-vision` |
| methodology | `takeover-codex` (DeepSeek alternative) |

Per-paper overrides in `angles.md`. Takeover prompts are fully self-contained (inline summary + sections).

## Directory Layout

```
.claude/
  skills/paper-review/  — pipeline (SKILL.md + 00–08 sub-files)
  skills/paper-rerun/   — re-run single step
  agents/               — 4 reviewers + polisher
ongoing/<slug>/         — papers under review
  0-raw.pdf             — original (gitignored)
  1-paper-text/         — ingested text (paper.md, md/, img/, INDEX.md)
  2-review/             — literature, summary, angles, critiques
  3-response/           — draft.md → final.md
archived/YYMMDD/<slug>/ — completed reviews, date-sorted
style/profile.md        — synthesised voice + 10-sample rolling window (gitignored)
critiques-library/      — deduped angle library (gitignored)
templates/              — literature-template, critiques-template, summary-template,
                          default-angles, reviewer-voice, polish-checklist, ingest-errors
paper_pdf_ingest/       — standalone git repo: PDF→markdown library (install with pip install -e)
```

## Design notes

- **Progressive disclosure**: orchestrator reads one sub-step file at a time. Total instruction context per step is ~200 lines.
- **Venue calibration**: conference vs journal gates the `Obvious gaps` section — EE conference papers are not penalised for missing hardware/code/data.
- **Intermediate language**: all review prose can switch to Chinese via `review-config.md` `lang: zh`. `final.md` is always plain-text English.
