---
name: sharp-review-2026-07-23
description: Sharp review findings — 48 total
metadata:
  type: project
---






## Review 2026-07-23 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260723-001] [HIGH] .claude/skills/manuscript-review/SKILL.md — The documented entrypoint `/manuscript-review:new` does not match the actual skill definition.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either rename/add the real slash-command/skill entrypoint so `/manuscript-review:new` exists, or update all docs to the actual invocable command exposed by `name: manuscript-review`.

The repo has `.claude/skills/manuscript-review/SKILL.md` with frontmatter `name: manuscript-review`, but there is no `.claude/commands/manuscript-review/new.md` or equivalent command directory. README.md, AGENT.md, and the skill itself repeatedly document `/manuscript-review:new <pdf>`. As documented, a user will try a command that the checked-in skill layout does not prove exists.

---

### [SR-20260723-002] [HIGH] .claude/skills/manuscript-rerun/SKILL.md — The documented rerun command namespace does not match the actual skill name.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make the rerun skill invocable as `/manuscript-review:rerun` via an actual command file/alias, or change docs to the real skill command name implied by `name: manuscript-rerun`.

The rerun skill frontmatter says `name: manuscript-rerun`, but its title and examples document `/manuscript-review:rerun`. README.md and AGENT.md repeat that command. There is no visible command directory wiring `manuscript-review:rerun` to this skill, so the docs describe an entrypoint that is not backed by the repo structure.

---

### [SR-20260723-003] [MEDIUM] .claude/skills/manuscript-rerun/SKILL.md — Rerun claims steps 2 and 4 work, but the tool allowlist omits `Workflow`.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add `Workflow` to the rerun skill `allowed-tools`, or document that workflow-backed steps must be rerun through the main orchestrator instead.

The examples explicitly include `/manuscript-review:rerun 2 ...`, and the text says rare earlier steps work. But step 02 invokes `manuscript-review-literature` via `Workflow`, and step 04 invokes `manuscript-review-fanout` via `Workflow`. The rerun skill allowlist is only `Read,Write,Bash,Glob,Grep,Agent,Skill`, so the documented rerun path cannot execute those workflow-backed steps as written.

---

### [SR-20260723-004] [MEDIUM] .claude/skills/manuscript-review/08-archive.md — Archive step reads `archived/YYMMDD/<slug>/angles.md`, but the pipeline writes angles under `2-review/angles.md`.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the archive instructions to read `archived/YYMMDD/<slug>/2-review/angles.md`.

Step 03 outputs `ongoing/<slug>/2-review/angles.md`, the directory layout in README.md/AGENT.md places `angles.md` under `2-review/`, and step 08 moves the whole slug directory unchanged. After the move, the file is `archived/YYMMDD/<slug>/2-review/angles.md`, not `archived/YYMMDD/<slug>/angles.md`. The current instruction points at a path that will not exist.

---

### [SR-20260723-005] [LOW] AGENT.md — Setup wording says clone the ingest library 'alongside this repo' but the command and actual layout put it inside the repo root.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Clarify the intended layout: either say 'inside this repo root' or change the install command to the correct sibling path.

AGENT.md says `# Clone the ingest library alongside this repo`, then runs `git clone https://github.com/DawnEver/paper_pdf_ingest.git` and `pip install -e paper_pdf_ingest/` from the manuscript-review root. The actual repo contains `manuscript-review/paper_pdf_ingest/`, so 'alongside this repo' is misleading and conflicts with the relative install path.

---

### [SR-20260723-006] [INFO] README.md — No stale `paper-review`, `paper-rerun`, `paper_review`, `/paper-review:`, or `paper-review-fanout` references were found in active docs.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Leave `paper_pdf_ingest` references alone unless the ingest library itself is renamed; they match the actual `paper_pdf_ingest/` dependency and `scripts/ingest.py`.

A hidden grep over README.md, AGENT.md, CLAUDE.md, `.claude/skills`, `.claude/workflows`, `.claude/agents`, templates, and scripts found old-name hits only for `paper_pdf_ingest` and historical memory entries. The active workflow filenames are `.claude/workflows/manuscript-review-literature.js` and `.claude/workflows/manuscript-review-fanout.js`, matching the active skill docs.


## Review 2026-07-23 (follow-up)

## Review 2026-07-23 (session) — adversarial review (对抗性审查) + diff review

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): OK

### Confirmed findings

---

### [SR-20260723-007] [HIGH] manuscript-review/.claude/skills/manuscript-review/SKILL.md — The rename strands existing untracked review state because resume only looks under the new project path.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add an explicit migration step/check for legacy `paper-review/ongoing` and `paper-review/archived`, or keep a compatibility command that can locate and migrate/copy old slugs before resuming.

The pipeline now documents `/manuscript-review:new <slug>` and searches only `ongoing/<slug>/` and `archived/*/<slug>/` inside `manuscript-review`. But the actual review artifacts (`ongoing/`, `archived/`, raw PDFs, generated critique files) are typically gitignored runtime state. A user pulling this rename will get tracked files in `manuscript-review/`, while their untracked `paper-review/ongoing` may remain outside the new project. The resume table then reports `nothing` and can start a duplicate run instead of resuming the existing manuscript review.

---

### [SR-20260723-008] [MEDIUM] manuscript-review/.claude/skills/manuscript-rerun/SKILL.md — Deleting the old `paper-rerun` skill provides no compatibility path for existing command muscle memory, docs, or automation.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Keep a deprecated `paper-rerun` wrapper skill for one release that forwards users to `/manuscript-review:rerun`, or document the breaking command rename prominently with exact migration instructions.

The old skill is deleted and the new examples replace `/paper-review:*` with `/manuscript-review:*`. Any saved prompts, scripts, aliases, or memory instructions that invoke `/paper-review:rerun` now fail hard. The table labelled `Old call | Now` is also misleading: it maps old archive/repolish concepts after already renaming the namespace, but does not preserve or explain the actually removed `/paper-review:*` entry points.

---

### [SR-20260723-009] [MEDIUM] manuscript-review/.claude/skills/manuscript-review/01-ingest.md — The ingest step documents a renamed venv elsewhere but still runs ambient `python`, so dependency failures are left to luck.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either invoke the documented venv interpreter explicitly, add a preflight that verifies `paper_pdf_ingest` and its dependencies under the interpreter being used, or change setup docs to require activating the venv before running the skill.

README/AGENT now tell users to create `~/.local/share/manuscript-review-venv`, but step 01 runs `python -m scripts.ingest ...`. That does not use the documented venv unless the shell is already activated. Worst case: users recreate the new venv exactly as instructed, then the pipeline still runs system Python and fails with missing `paper_pdf_ingest`, `pymupdf4llm`, or `marker-pdf`. The error template also points users at fixing the venv even though the command may not be using it.

---

### [SR-20260723-010] [LOW] manuscript-review/README.md — The README silently changes the clone URL to a new repository name without any fallback or migration note.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Confirm the `DawnEver/manuscript-review` remote exists and add a note for users of `DawnEver/paper-review` explaining whether the old repository was renamed, archived, or replaced.

The setup command now says `git clone https://github.com/DawnEver/manuscript-review.git`. If the remote rename has not happened, fresh installs fail immediately. If it has happened, existing users still need to know whether GitHub redirects the old URL and whether local remotes should be updated. The change assumes the external repository rename is already complete and stable but does not enforce or document that assumption.

---

### [SR-20260723-011] [LOW] manuscript-review/.claude/workflows/manuscript-review-fanout.js — Stale 'paper reviews' terminology in workflow description after rename

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change description to 'Parallel fanout of manuscript reviews across multiple models'.

meta.name was correctly updated to 'manuscript-review-fanout', but line 3's description string still reads 'Parallel fanout of paper reviews'. Cosmetic only (description isn't a lookup key), but it's an incomplete rename that will show stale text in the /workflows list and permission dialog.

---

### [SR-20260723-012] [LOW] manuscript-review/.claude/skills/manuscript-rerun/SKILL.md — Skill folder/name 'manuscript-rerun' but every invocation is documented as '/manuscript-review:rerun' — possible namespace mismatch

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Verify command resolution: if prefix derives from plugin name (manuscript-review) and not folder name, this is fine; if not, rename folder or invocation strings.

The main skill uses folder 'manuscript-review' to '/manuscript-review:new', so prefix appears to track the folder name. By that pattern, folder 'manuscript-rerun' would resolve to '/manuscript-rerun:rerun', not the '/manuscript-review:rerun' documented. This mismatch predates the rename (old paper-rerun/ had the same shape), so it's likely a working plugin-namespace convention — but the rename was the moment to reconcile it.

---

### [SR-20260723-013] [INFO] manuscript-review/README.md — Renamed venv path in docs will orphan existing installs

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a one-line migration note, or leave as-is if only fresh installs are expected.

README.md:17 and AGENT.md:13 now reference '~/.local/share/manuscript-review-venv/'. Anyone who installed under the old 'paper-review-venv' path will follow these docs into a fresh install with no note that the old venv is now dead.


## Review 2026-07-23 (follow-up)

## Review 2026-07-23 (session) — docs review (文档锐评) + adversarial review (对抗性审查)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): FAILED
- Reviewer C (Opus): skipped
- Warning: only 1/2 reviewers succeeded

### Confirmed findings

---

### [SR-20260723-014] [HIGH] README.md — The documented `/literature-review:new` and `/literature-review:rerun` commands are not backed by the checked-in skill layout.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either add command files under `.claude/commands/literature-review/` for `new` and `rerun`, or update the docs to invoke the actual skills that exist: `.claude/skills/literature-review` and `.claude/skills/literature-review-rerun`.

The repo contains `.claude/skills/literature-review/SKILL.md` with `name: literature-review` and `.claude/skills/literature-review-rerun/SKILL.md`, but no `.claude/commands` tree. README documents `/literature-review:new <topic>` and `/literature-review:rerun <step> <topic>`, which users cannot verify from the current repository.

---

### [SR-20260723-015] [HIGH] .claude/skills/literature-review/03-search-screen.md — Several documented `lit_review.py` commands use arguments or output layouts that the current CLI does not support.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update step 03 examples to match `scripts/lit_review.py`: `normalize-candidates --raw ... --query-id ... --out <dir>`, remove `--batch-size`, and describe the actual single `screening_packet.jsonl/.csv` output unless batching is implemented.

The docs show `normalize-candidates --input ... --out .../normalized.jsonl`, but the parser requires `--raw`, `--query-id`, and treats `--out` as an output directory. The docs also show `make-screening-packet --batch-size 15` and batch files like `batch_001.jsonl`, but the parser has no `--batch-size` option and `scripts/make_screening_packet.py` writes one `screening_packet.jsonl` and one CSV.

---

### [SR-20260723-016] [HIGH] README.md — Setup omits the `uv` runtime required by PDF decomposition.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document installing `uv` and explain that decomposition runs `uv run --project <paper_pdf_ingest> --frozen ingest ...`; alternatively change the script/docs to use the editable `pip install -e` environment consistently.

README tells users to `pip install -e paper_pdf_ingest/` and set `PAPER_INGEST_ROOT`, but `scripts/pdf_decompose.py` invokes `uv run --project <tool_root> --frozen ingest ...`. `uv` is not in `requirements.txt` and is not mentioned in setup, so a user following the docs can reach step 05 and fail before ingestion starts.

---

### [SR-20260723-017] [MEDIUM] README.md — Browser setup is incomplete for the documented Playwright search and PDF acquisition flow.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a setup step such as `python -m playwright install chromium`, and mention any institution/proxy login expectations before `browser-login` or `acquire-pdf`.

`requirements.txt` installs the Playwright Python package, but browser binaries are installed separately. The code in `scripts/browser_login.py`, `scripts/ieee_web_probe.py`, `scripts/ieee_web_search.py`, and `scripts/pdf_acquire.py` launches Playwright Chromium, so setup can fail on a clean machine even after `pip install -r requirements.txt`.

---

### [SR-20260723-018] [MEDIUM] README.md — README presents Zotero bidirectional sync as part of the active pipeline, but the current skill marks it as Phase 3 and unimplemented.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Mark Zotero sync as planned/Phase 3 in README, or add the missing implementation and usage instructions for the bridge.

README says the agent can sync paper notes to Zotero and lists step 9 as `Zotero bridge bidirectional sync`. The actual `.claude/skills/literature-review/09-zotero.md` says `This step is implemented in Phase 3` and its current action is only `Pipeline complete`, so the README overstates current functionality.

---

### [SR-20260723-019] [MEDIUM] README.md — References to `SKILL.md` are broken or ambiguous because there is no root-level `SKILL.md`.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Replace `SKILL.md` references with `.claude/skills/literature-review/SKILL.md` and `.claude/skills/literature-review-rerun/SKILL.md` as appropriate.

README says `SKILL.md` is the map and that resume details are in `SKILL.md`, but the only matching file is under `.claude/skills/literature-review/SKILL.md`. From the repository root, `SKILL.md` does not exist.

---

### [SR-20260723-020] [MEDIUM] AGENT.md — The documented agent model routing claims `gpt-5.6-luna` defaults, which may be stale or non-portable as setup documentation.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either document these as project-local frontmatter values rather than available platform defaults, or update the agent frontmatter to supported model identifiers for the target Claude/Codex environment.

AGENT.md lists `gpt-5.6-luna` for all three agents, and the `.claude/agents/*.md` files contain the same model value. If this repository is intended to be usable outside the author's local setup, the docs provide no fallback or installation requirement for that model name.

---

### [SR-20260723-021] [LOW] AGENT.md — Directory layout documents `.CLAUDE/` and `.claude/workflows/`, but the actual tree uses `.claude/` and has no workflows directory.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change `.CLAUDE/` to `.claude/` and remove or mark `.claude/workflows/` as planned unless workflow files are added.

The repository contains `.claude/agents`, `.claude/skills`, `.claude/settings.json`, and `.claude/memory`; there is no uppercase `.CLAUDE` directory and no `.claude/workflows`. This makes the layout section misleading for users exploring the project.

---

### [SR-20260723-022] [LOW] .claude/skills/literature-review/03-search-screen.md — The abstract screener agent name in the step docs does not match the actual agent file/frontmatter.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Use `literature-abstract-screener`, matching `.claude/agents/abstract-screener.md`, or rename the agent/frontmatter to the documented identifier consistently.

Step 03 says to delegate to `literature_abstract_screener`, but the checked-in agent frontmatter says `name: literature-abstract-screener`. This can cause failed delegation or confusion when manually following the playbook.

---

### [SR-20260723-023] [LOW] README.md — README and skill docs contain mojibake, making arrows and status markers unreadable.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Re-save the Markdown files as UTF-8 and replace corrupted sequences with plain ASCII or valid Unicode arrows/checkmarks.

README, AGENT.md, and several `.claude/skills/literature-review/*.md` files contain strings such as `鈥?`, `鈫?`, and `猸?`. This is not a code behavior issue, but it degrades setup and pipeline instructions and can break text matching for users copying commands or headings.


## Review 2026-07-23 (follow-up)

## Review 2026-07-23 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260723-024] [HIGH] .claude/skills/literature-review/04-acquire.md — The documented acquisition handoff paths do not match the current CLI outputs, so the documented step 04 flow cannot reach step 05 as written.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the step 04 commands and resume table to use the actual output locations, or change the scripts to emit the documented `download/matches.json` and accept `--out` as a target file consistently.

`match-pdfs` currently writes `download/pdf_match/match_report.json`, but the docs say it produces `download/matches.json`. The next documented command passes `--matches .../download/matches.json`, which will not exist. The same file also documents `make-download-queue --out .../download/download_queue.json` and `make-download-manifest --out .../handoff/download_manifest.json`, but `write_download_queue()` and `write_manifest()` treat `--out` as a directory and create `download_queue.json` or `download_manifest.json` underneath it.

---

### [SR-20260723-025] [HIGH] scripts/make_download_manifest.py — The generated download manifest is incompatible with the schema that step 05 validates against, despite docs presenting it as the ingest handoff artifact.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either make `make_download_manifest.py` populate the required schema fields or update the documented handoff contract and schema so they agree.

`schemas/download_manifest.schema.json` requires `run_id`, `approved_brief_sha256`, and per-paper fields such as `provider`, `acquisition_method`, and `acquired_at`. `make_download_manifest.py` writes only `artifact_version`, `manifest_type`, `generated_at`, and `papers` with a smaller per-paper shape. `scripts/pdf_decompose.py` validates the manifest against this schema before ingest, so a manifest produced by the documented command can fail at decomposition.

---

### [SR-20260723-026] [MEDIUM] .claude/skills/literature-review/05-ingest.md — The documented `decompose-pdfs --run-dir` value creates a nested ingest directory and the documented status names do not match the schema/code.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document `--run-dir workspaces/<slug>/runs/<run-id>` if the code should create `ingest/` internally, and replace `success` with `succeeded` everywhere.

`pdf_decompose.decompose_pdfs()` sets `ingest_root = run_dir / "ingest"`. The docs pass `--run-dir .../runs/<run-id>/ingest/`, which produces `.../ingest/ingest/ingest_manifest.json` instead of the documented `.../ingest/ingest_manifest.json`. The docs also list statuses `success`, `failed`, and `skipped`, but the code and `schemas/ingest_manifest.schema.json` use `succeeded`, `failed`, and `skipped`.

---

### [SR-20260723-027] [MEDIUM] .claude/skills/literature-review/03-search-screen.md — The documented normalization/dedupe artifact names are stale relative to the current scripts.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update step 03 to use the integrated `search` output or document the actual standalone outputs: `candidates_raw.jsonl` and `candidates_ranked.jsonl`. Avoid showing a wildcard as a single `--input` unless the CLI supports multiple files.

The docs say normalization writes `normalized.jsonl` and dedupe writes `search/records.jsonl`. The standalone `normalize-candidates` command writes `candidates_raw.jsonl`, while `dedupe-rank` reads one input path and writes `candidates_ranked.jsonl` under the output directory. The documented `--input .../*/normalized.jsonl --out .../search/records.jsonl` therefore does not match the argparse contract or produced artifacts.

---

### [SR-20260723-028] [MEDIUM] README.md — README overstates implemented Zotero functionality.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Mark Zotero sync as planned/Phase 3 in the opening description, or add the missing implementation and setup instructions.

README says the agent can sync academic papers to Zotero and lists step 9 as `Zotero bridge bidirectional sync`. The actual `.claude/skills/literature-review/09-zotero.md` says the step is implemented in Phase 3 and the current action is only `Pipeline complete`.

---

### [SR-20260723-029] [LOW] README.md — Setup is incomplete for the Windows environment used by the project docs.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a PowerShell variant for setting `PAPER_INGEST_ROOT`, for example `$env:PAPER_INGEST_ROOT = (Resolve-Path .\paper_pdf_ingest)`, and clarify whether it must be persisted.

The README includes only `export PAPER_INGEST_ROOT=$(pwd)/paper_pdf_ingest`, which is POSIX shell syntax. The repository path and other docs are Windows-oriented, so a Windows user following setup in PowerShell will not set the environment variable required by `scripts/pdf_decompose.py`.

---

### [SR-20260723-030] [LOW] AGENT.md — The provider support table claims IEEE PDF acquisition support even though the provider adapter method is explicitly a stub.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Clarify that IEEE PDF acquisition is implemented through `scripts/lit_review.py acquire-pdf` / `scripts/pdf_acquire.py`, while `IeeeXploreProvider.acquire()` is not implemented.

AGENT.md lists IEEE Xplore PDF Acquire as supported. However, `providers/ieee_xplore.py::IeeeXploreProvider.acquire()` raises `NotImplementedError`, and the smoke test asserts that behavior. The repository does contain a separate browser acquisition script, so the documentation should distinguish the CLI workflow from provider-interface support.


## Review 2026-07-23 (follow-up)

## Review 2026-07-23 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260723-031] [HIGH] .claude/skills/literature-review/05-ingest.md — Documented decompose-pdfs command omits --tool-root, but the lit_review.py wrapper passes None and crashes instead of using PAPER_INGEST_ROOT.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either fix scripts/lit_review.py to pass pdf_decompose.DEFAULT_TOOL_ROOT when --tool-root is omitted, or update the documentation to require --tool-root until the wrapper is fixed.

The step says the command uses PAPER_INGEST_ROOT and documents python scripts/lit_review.py decompose-pdfs ... --confirmed-by-user. In scripts/lit_review.py the decompose subparser sets --tool-root default to None and then passes args.tool_root into decompose_pdfs. That overrides pdf_decompose.py's default Path from PAPER_INGEST_ROOT, so decompose_pdfs calls tool_root.expanduser() on None and fails outside the documented path.

---

### [SR-20260723-032] [HIGH] .claude/skills/literature-review/00-workspace.md — Workspace setup documents a validate-workspace command that does not exist in the actual CLI.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a validate-workspace subcommand wired to schemas/workspace.schema.json, or remove the command from the step and describe the actual validation mechanism.

The step instructs python scripts/lit_review.py validate-workspace --workspace workspaces/<slug>/workspace.yaml. python scripts/lit_review.py --help lists no validate-workspace subcommand, and scripts/lit_review.py has no dispatch branch for it. A user or orchestrator following step 00 will hit an unsupported command before the pipeline can start.

---

### [SR-20260723-033] [HIGH] .claude/skills/literature-review/02-queries.md — Query resume instructions reference a queries-status command that is not implemented.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Implement queries-status --queries <path> or change the resume rule to use the existing approval validation performed by probe/search or confirm-queries.

The resume rule says to run python scripts/lit_review.py queries-status --queries <path>. The actual lit_review.py subcommands include confirm-queries, probe, evaluate-queries, search, and others, but no queries-status. This makes documented resume behavior stale and will block or confuse re-invocation logic.

---

### [SR-20260723-034] [HIGH] .claude/skills/literature-review/01-brief.md — Brief output path is documented under briefs/<brief-id>, but later CLI gates expect run-dir/research_brief.yaml.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Choose one storage model and update the skill files and CLI together; the simplest fix is to document research_brief.yaml under the active run directory if confirm-queries is meant to bind queries to the same run.

Step 01 writes and confirms workspaces/<slug>/briefs/<brief-id>/research_brief.yaml. Step 02 writes queries to workspaces/<slug>/runs/<run-id>/queries.yaml and runs confirm-queries --run-dir workspaces/<slug>/runs/<run-id>. In code, confirm_queries reads run_dir / queries.yaml and then resolves brief_ref relative to that same run_dir, defaulting to run_dir / research_brief.yaml. Without an explicit copied brief_ref path strategy, the documented brief location does not match the code's default provenance chain.

---

### [SR-20260723-035] [MEDIUM] .claude/skills/literature-review/05-ingest.md — Ingest resume rule uses status success, but code and schema use succeeded.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Replace success with succeeded in the resume rule and any downstream instructions that inspect ingest_manifest.json.

pdf_decompose.py writes per-paper statuses as succeeded, failed, or skipped, and print_ingest_summary counts succeeded. The documentation says to proceed if all papers are success or skipped. An orchestrator checking the documented value will not recognize successful ingests.

---

### [SR-20260723-036] [MEDIUM] .claude/skills/literature-review/04-acquire.md — The documented acquire-pdf --run-dir points at the download directory, but the code creates its own download subdirectory under run-dir.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document --run-dir workspaces/<slug>/runs/<run-id> for acquire-pdf and match-pdfs, or rename the CLI argument if it is intentionally a download-root argument.

Step 04 documents --run-dir workspaces/<slug>/runs/<run-id>/download/. In scripts/pdf_acquire.py the code builds download_dir = run_dir / "download" / "pdfs", so the documented command writes into .../download/download/pdfs. match-pdfs has the same documented run-dir shape, which risks looking in the nested location rather than the intended run download area.

---

### [SR-20260723-037] [MEDIUM] README.md — Setup omits a usable CLI quickstart for the actual implemented workflow.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a short section showing python scripts/lit_review.py --help and the concrete command sequence for validate-brief, confirm-brief, confirm-queries, probe, search, screening, queue approval, acquisition, manifest, and decomposition.

README only documents slash commands and a high-level pipeline. The actual executable surface is scripts/lit_review.py with many subcommands and required flags, including approval gates and paths. Users outside Claude slash-command execution have no accurate end-to-end usage path, even though the code exposes one.

---

### [SR-20260723-038] [LOW] scripts/query_planner.py — query_planner.py is over 300 lines and appears partly stale or orphaned from the documented pipeline.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either wire query_planner.py into Step 02 and README with its actual inputs/outputs, or split/remove the stale planning code if query generation is now agent-authored.

The file is 368 lines, has defaults for lenses/power_electronics.yaml, and references a missing templates/search_plan.md.j2 as not created yet. The current Step 02 instructs the agent to generate queries directly and never mentions query_planner.py. This is a maintenance risk: a large script with stale defaults can diverge from the documented data contract silently.

---

### [SR-20260723-039] [LOW] AGENT.md — AGENT.md claims multiple provider discovery, but only IEEE is implemented.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Tone the description down to current support, or clearly mark arXiv, Semantic Scholar, and CrossRef as planned rather than part of the current discovery capability.

The opening description says the agent discovers papers from multiple academic sources. The provider table later says IEEE is Phase 1 and the other providers are planned. The codebase contains providers/ieee_xplore.py only. This contradictory setup can make users expect cross-provider search that the current implementation does not provide.


## Review 2026-07-23 (follow-up)

## Review 2026-07-23 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260723-040] [HIGH] AGENT.md — Current-capability claims overstate provider and downstream support.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Rewrite the overview and architecture text to say the current implementation is IEEE-only, with triage, deep reading, synthesis, and Zotero explicitly planned/skipped until implemented.

AGENT.md says the agent can discover papers from multiple academic sources, deep-read with lenses, and sync paper notes to Zotero. The actual provider package contains only providers/ieee_xplore.py; arXiv, Semantic Scholar, and CrossRef adapters do not exist. Steps 06-09 skill files explicitly say Phase 2/3 planned and immediately proceed or complete. The top-level doc sells capabilities the code cannot execute.

---

### [SR-20260723-041] [HIGH] README.md — README presents unfinished pipeline phases as part of the usable product.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split the pipeline table into implemented vs planned phases, and remove current-tense claims about deep reading, synthesis, and Zotero sync until scripts/agents exist for those steps.

README describes an agent that can acquire, ingest, deep-read, synthesize, and sync to Zotero. In the checked-in skill files, 06-triage.md, 07-read.md, and 08-synthesis.md are Phase 2 placeholders, and 09-zotero.md is Phase 3 with 'Current action: Pipeline complete.' There is no implementation in scripts/ for triage, paper-card generation, synthesis, or Zotero sync.

---

### [SR-20260723-042] [HIGH] .claude/skills/literature-review/03-search-screen.md — Documented search/probe/evaluation command paths do not match the CLI output contract.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document the real path contract: pass the run directory or update the scripts to stop appending probe/search; pass the probe JSONL to evaluation and the evaluation YAML to search.

run_probe() writes to out_dir/'probe', but the doc passes --out .../search/probe/, producing .../search/probe/probe/. query_evaluator.py expects --probe-results to be a JSONL file, but the doc passes the probe directory. run_search() writes to out_dir/'search', but the doc passes --out .../search/, producing .../search/search/records.jsonl. search --evaluation expects the YAML file, not the evaluation directory shown in the doc.

---

### [SR-20260723-043] [HIGH] .claude/skills/literature-review/03-search-screen.md — The normalization/dedupe/screening artifact flow is internally inconsistent with the code.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Choose one flow and document it: search produces normalized search/records.jsonl, then optionally dedupe-rank --input search/records.jsonl --out search/, then screen search/candidates_ranked.jsonl.

The doc says search saves per-query raw responses under search/queries/<query-id>/raw/, then normalizing creates candidates_raw.jsonl, then dedupe creates candidates_ranked.jsonl, but later commands and resume rules use search/records.jsonl. The actual scripts/ieee_web_search.py already normalizes and writes search/records.jsonl; scripts/dedupe_rank.py accepts one JSONL input and writes candidates_ranked.jsonl. The documented per-query dedupe/merge instructions are not executable as written.

---

### [SR-20260723-044] [MEDIUM] .claude/skills/literature-review/04-acquire.md — The documented PDF output layout is wrong for the current acquisition and matching scripts.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the output tree to show runs/<run-id>/pdfs/ and runs/<run-id>/pdf_match/, or change pdf_acquire.py and match_downloaded_pdfs.py to write under download/ as documented.

The doc claims PDFs land in download/pdfs/ and match reports in download/pdf_match/match_report.json. With the documented commands, pdf_acquire.acquire_pdfs() writes PDFs to run_dir/'pdfs', and match_downloaded_pdfs.match_pdfs() writes run_dir/'pdf_match'/'match_report.json'. The documented make-download-manifest --matches .../download/pdf_match/match_report.json points at a file the code will not create.

---

### [SR-20260723-045] [MEDIUM] .claude/skills/literature-review/05-ingest.md — The ingest command description names the wrong executable interface.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Say the script invokes python -m paper_pdf_ingest, or change pdf_decompose.py to call the documented ingest CLI if that is the intended public contract.

AGENT.md and step 05 say scripts/pdf_decompose.py calls the ingest CLI provided by paper_pdf_ingest. The actual code builds [sys.executable, '-m', 'paper_pdf_ingest', <pdf>, <out>]. Users debugging environment issues will look for the wrong executable.

---

### [SR-20260723-046] [MEDIUM] AGENT.md — Model routing docs use misleading agent identifiers and invent orchestrator behavior.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Use the actual frontmatter names literature-query-reviewer, literature-abstract-screener, and literature-paper-reader; remove the claim that code reads .claude/agents/*.md dynamically unless an implemented orchestrator does that.

The model table lists agents as query-reviewer, abstract-screener, and paper-reader, but the frontmatter names are literature-query-reviewer, literature-abstract-screener, and literature-paper-reader. AGENT.md also says the orchestrator reads agent configs at invocation time. There is no orchestrator implementation in scripts/; the command files only tell Claude to read skill markdown.

---

### [SR-20260723-047] [MEDIUM] .claude/skills/literature-review/SKILL.md — The resume table references artifacts that the documented commands will not create at those paths.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Align the resume table with actual script outputs after fixing the path contract, especially search/records.jsonl, download/pdf_match, pdf_match, and approved queue detection.

The resume table says runs/<id>/search/records.jsonl resumes step 03 and runs/<id>/download/download_queue.json drives step 04. But the step 03 documented --out values currently cause search/search/records.jsonl, while step 04 documentation expects match artifacts under download/pdf_match although code writes pdf_match at run root. Resume behavior based on these paths will misroute or fail.

---

### [SR-20260723-048] [LOW] AGENT.md — Directory layout says providers/ contains adapters for arXiv, Semantic Scholar, and more, but only IEEE exists.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the directory layout comment to 'providers/ — provider abstraction and current IEEE adapter; additional providers planned'.

The provider support table marks non-IEEE providers as planned, but the directory layout still says 'providers/ — literature source adapters (IEEE, arXiv, Semantic Scholar, ...)'. In the current tree, providers/ contains _base.py, ieee_xplore.py, and __init__.py only. It reinforces the larger false impression of multi-provider implementation.
