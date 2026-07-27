---
name: zotero-maintenance-pipeline
description: Shared-Engineering architecture — zotero-import (DOI-dedup batch) + zotero-maintain (registry-scoped enrich + local mirror)
created: 2026-07-26
metadata:
  type: design
tags: [zotero, maintenance, arxiv, crossref, local-storage, import]
---

## Architecture (agreed 2026-07-27, supersedes per-topic collections)

- **ALL papers → one shared Zotero collection** `Engineering` (`HNRLNAP9`).
  Collection names are NOT unique: `PETTGPID` is an empty stray also named
  "Engineering" — always resolve by `collection_key` from workspace.toml.
- **Workspace identity lives in the project**: `zotero_registry.jsonl`
  (candidate/file ↔ zotero_key, pdf_attached, source_path) + workspace tag
  (`workspace.toml` → `[zotero].tags`, e.g. `chp`).

## Mechanisms

### `lit-review zotero-import --topic <slug>` (export/zotero_import.py)
Batch import of `download/pdfs` + `papers` + `pdfs` (ingest/ excluded).
Dedupe: three-pass grouping — (1) DOI from PDF, (2) exact title_key match,
(3) title_key substring (≥20 chars). `title_key` = normalised stem minus
leading `authorYYYY` token, with fallback to full stem when stripping leaves
<20 chars (AllSAT_TACAS2005 must not collapse to ''). CrossRef metadata at
creation; registry upserted per item; idempotent via registry skip.
Gotcha: Zotero rejects `publicationTitle` on conferencePaper — container
field is type-specific (proceedingsTitle / bookTitle / repository).

### `lit-review zotero-maintain --topic <slug>` (export/zotero_maintenance.py)
- **Enrich** — registry-scoped by default (only the workspace's own items;
  `--all` widens to the whole configured collection, never the whole library;
  an EMPTY registry short-circuits with "nothing to maintain").
  Identifier ladder: arXiv → DOI → guarded CrossRef title query (Jaccard ≥ 0.6,
  HTML stripped). PUT failures surface the server's error body.
- **Mirror** — also registry-scoped by default. Downloads uploaded-but-locally-
  missing attachments into `~/Zotero/storage/<key>/` (cures desktop "File Not
  Found"), md5-verified against the server record; any 200 non-empty body is
  accepted (attachments aren't only PDFs).

## Lessons from the 2026-07-27 incident

A whole-collection enrich run (before scoping existed) updated 65 items
including ~5 false matches on user manuals ("SimEvents User's Guide" →
"User guide to seed tracing"). Root causes: blind first-hit CrossRef title
query + no HTML stripping + no scope limit. All three are now fixed in code;
the 5 visible mis-enrichments were reverted to their original titles.

## Standard sequence after adding PDFs

1. `lit-review zotero-import --topic <slug>`
2. `lit-review zotero-maintain --topic <slug>`
3. `zotero_update_search_database` (MCP)

## Files

- `literature_review/export/zotero_import.py`, `zotero_maintenance.py`
- `literature_review/cli.py` — `zotero-import`, `zotero-maintain`
- `tests/test_zotero_import.py`, `test_zotero_maintenance.py`
- Upload-layer fix: see zotero-hybrid-mode-pdf-bug (scripts/zotero_mcp_patch.py)
