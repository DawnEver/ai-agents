---
name: cc-academia-workspace-mechanics-2026-09-17
description: lit-review workspace lifecycle — init idempotency and its silent no-write, data-root walk-up rules, the absence of schema validation, and which artefact files a workspace should and should not have
metadata:
  type: engineering
---

# lit-review workspace lifecycle

`created: 2026-09-17, accessed: 2026-09-17`

How `lit-review` finds and validates a workspace, and the two ways a
hand-assembled one goes wrong.

## Creating one

```bash
uv run --project "<plugin-root>" lit-review init "<topic>"
```

- Takes a **positional** topic, not `--topic` like every other subcommand.
  Slug is `re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")`.
- **Non-interactive**, no prompts.
- **Idempotent, and silently so**: if the directory already exists it prints
  `Workspace already exists: <path>`, returns **0**, and does **not** write
  `workspace.toml`. So if you placed files there first, `init` leaves you with a
  directory the CLI accepts (existence is the only gate) but that has no
  `workspace.toml` — and `workspace.toml` is what supplies `providers`, which
  `workflow_search` otherwise falls back to `["ieee_xplore"]` for. Either move
  the files aside, `init`, then restore; or write `workspace.toml` by hand.
- It creates exactly eight subdirs — `search, screening, download, handoff,
  ingest, reading, notes, export` — plus `workspace.toml`. Nothing else.

## Where it lands

`find_data_root` walks up from `Path.cwd()`, and for each ancestor requires
`<ancestor>/literature-review/` to be a directory **and** to contain either
`AGENTS.md`/`README.md` or an `ongoing/` dir. The workspace then goes to
`<that ancestor>/literature-review/ongoing/<slug>`.

Two consequences worth remembering:

- **A scratch data dir becomes a valid data root as soon as it holds a
  `README.md` and an `ongoing/`.** That is how you keep a workspace out of a
  repo's own data tree — run `init` from the directory you actually want it in.
- **Run it from the wrong cwd and it silently creates under
  `~/cc-academia-data/literature-review/ongoing/<slug>`** instead of erroring.
  `ACADEMIA_DATA_ROOT` overrides the walk-up if you need to be explicit.

## Validation

There is none beyond the directory existing. `_topic_dir()` is the whole gate —
everything else fails lazily, per command, with a specific message: search wants
`research_brief.toml` and `queries.toml`; acquire wants
`screening/screening_stage1.jsonl`; ingest wants a `handoff/` manifest. A
workspace can therefore be partially valid for a long time without complaint.

## Which artefacts belong

- **Search-driven workspace**: needs `research_brief.toml` (keys
  `original_request`, `research_objective`, `constraints`, `concepts`) and
  `queries.toml` (a `[[queries]]` list; each item needs `query_id` and a
  non-empty `expression`, and only `enabled = true` runs).
- **Workspace holding a handed-over fixed paper list**: must **not** have those
  two files. Their presence implies the define→search→screen→acquire pipeline
  ran, which it did not, and the next reader of the workspace will believe a
  search happened. Leave `search/` and `screening/` empty too.
- **There is one `queries.toml` per workspace, not one per provider.** The code
  reads exactly `<topic_dir>/queries.toml`; provider is resolved separately from
  `workspace.toml → providers` or `--provider`, and only the *outputs* are
  namespaced per provider (`search/probe/<provider>/`, `search/evaluation/<provider>/`).
  Files like `queries_ieee.toml` found in existing workspaces are agent scratch
  that no CLI code reads.
- Approval gating is bypassed in the normal flow: `confirm_brief` and
  `confirm_queries` are library-only (no CLI subcommand), and `run_search`
  passes `allow_unapproved_plan=True`. No `approval` blocks are needed.

## Verify a workspace resolves

```bash
cd "<the dir you init'd from>" && uv run --project "<plugin-root>" lit-review stats --topic <slug>
```

Cheap and read-only — it proves the walk-up lands where you think.
