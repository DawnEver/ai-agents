---
name: tte-260903-runs
description: "Three TTE cases and what their deliverables do and do not cover; how to invoke rev-disc from this workspace"
metadata:
  type: project
---

# The three TTE cases as of 2026-09-03

One file per case is handed over: `ongoing/<slug>/<slug>.xlsx`, beside that
case's `0-raw.pdf`. Everything in `5-shortlist/` is working material. Written by
`rev-disc report` itself — `openpyxl` is a hard dependency now, because a run
that cannot write the workbook has produced nothing to hand over.

| Case | Rows | In play | Source PDF |
|---|---|---|---|
| `tte-2026-08-2905` | 166 | 10 | `260828-TTE/` (AFPM electromagnetic noise orders) |
| `tte-2026-08-2798` | 172 | 12 | `260903-TTE/` (hybrid winding + oil-immersed in-slot cooling) |
| `tte-2026-08-2978` | 199 | 10 | `260903-TTE/` (superlet synchrosqueezing, bearing fault diagnosis) |

All three regenerated on the six-rule policy. Audit sheet 45–46 columns,
decision sheet 16, every row carrying a clickable *Homepage or paper* link.

## What these runs do NOT cover — read before trusting a shortlist

1. **Semantic Scholar returned 429/500 for all ten queries** on both new cases,
   so recall is IEEE + OpenAlex only. This matters more than it looks: the
   related-journal floor of 3 is counted over *harvested* evidence, so thin
   recall reads as thin candidates. Worth re-running `search` if it recovers.
2. **No public-address search has been run.** `never_searched` is 71 / 150 /
   190. The playbook (`04-enrich.md`) expects an agent-owned public search to
   close the gap; structured sources reach ~a fifth of this field. This is why
   most rows read `Check first` rather than `Recommend` — a missing address asks
   for a human, it no longer excludes anybody.
3. **2798's author countries were set by hand.** The cover names
   "Nanjing University of Aeronautics and Astronautics" with no country line, so
   `origin_countries_from` yielded nothing and all five authors needed
   `country: CN` in `sanitized.json`. Origin country drives the geographic
   preference.
4. **The queries are not the auto-derived ones.** The cover keywords are IEEE's
   controlled vocabulary ("Electric machines", "Fault diagnosis") and would pull
   the whole subfield, so `paper_profile.json` was rewritten with five terms of
   art per case before `--approve`.

## Running the CLI from here

```bash
uv run --frozen --project "<plugin-root>" rev-disc <command> --slug <slug>
```

**Run it from the data workspace, not from the plugin.** `paths.data_root()`
discovers the root by walking up for a directory containing a workflow folder —
`cd`-ing into the plugin checkout makes it fall back to `~/cc-academia-data` and
the command reports "workspace not found". `--project` points at the code;
the working directory decides where the data is.

`init` needs `uv sync --project "<plugin-root>" --extra pdf` once.

## Gotcha

Writing the workbook fails while it is open in Excel — Excel holds an exclusive
lock. `rev-disc report` catches the `PermissionError` and names the file to
close, because it is now the last step of every run rather than a manual script
somebody chose to invoke.
