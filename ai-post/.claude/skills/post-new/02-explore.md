# Step 02 — Ingest Source

Turn the raw source into structured notes. Two branches depending on the source kind — but both
write the **same output file** so every later step is source-agnostic.

## Inputs
- `ongoing/<slug>/1-research/source.md` — the pointer from step 01 (`kind` + `resolved_path`)

## Output
- `ongoing/<slug>/1-research/source-exploration.md` — organized findings. This file feeds step 03
  (market research) and step 04 (analysis).

First read `source.md` and branch on `kind`.

---

## Branch A — Code source (`kind: github` or `kind: local-dir`)

Explore the codebase at `resolved_path` and write structured exploration notes.

### 1. Project overview
```bash
ls -la <resolved_path>/
```
Read these if they exist: `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`.

### 2. Source code structure
Use Glob to map source files and identify the architecture pattern, entry points, and dependencies.
Check for package manifests (`package.json`, `Cargo.toml`, `go.mod`, `requirements.txt`).

### 3. Implementation details
Read the main entry point, core library API, example/demo code, and key test files. Look for clever
patterns, performance tricks, elegant API design.

### 4. Recent activity (git repos only)
```bash
cd <resolved_path> && git log --oneline -20   # skip if not a git repo (a plain local-dir may not be)
```

---

## Branch B — Research report (`kind: local-file`)

The document *is* the material. Read it and extract what a writer needs — don't summarize blandly,
mine it for the sharp, quotable, specific stuff.

### 1. Read the report
- PDF → use the Read tool's `pages` parameter (max 20 pages/request; page through longer docs).
- `.md` / `.txt` / other text → plain Read.
- Capture document metadata: title, author/publisher, date, venue/source if stated.

### 2. Extract the substance
Pull out, with the report's own wording where it's vivid:
- **Core thesis** — the one claim the report is making.
- **Key findings** — the 3–7 load-bearing results, each with the concrete number/evidence behind it.
- **Data & figures** — specific statistics, benchmarks, chart takeaways (note figure/section refs so
  claims stay traceable — no invented numbers).
- **Method / how they know it** — study design, dataset, model, or reasoning, in plain terms.
- **Surprises & tensions** — counter-intuitive results, caveats, limitations the report admits.
- **Quotable lines** — sentences worth quoting verbatim.

### 3. Traceability
Every claim in the notes must trace to a real place in the document (page/section/figure). Flag
anything the report asserts without support as `[unsupported]` — do not launder it into fact.

---

## Write exploration notes

Write `ongoing/<slug>/1-research/source-exploration.md` with all findings organized under clear
headings (use the sections above appropriate to the branch). Both branches produce the same
filename so step 03 and step 04 read one input regardless of source kind.

## Resume

If `ongoing/<slug>/1-research/source-exploration.md` is non-empty, skip this step.
