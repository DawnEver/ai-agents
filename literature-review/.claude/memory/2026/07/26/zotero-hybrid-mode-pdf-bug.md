---
name: zotero-hybrid-mode-pdf-bug
description: zotero_add_from_file falsely reported PDF upload success — root cause in pyzotero attachment_both, fixed via runtime patch
created: 2026-07-26
metadata:
  type: bug
  status: fixed
tags: [zotero, mcp, hybrid-mode, pdf, attachment]
---

## Problem

`zotero_add_from_file` reported "File attached: <filename>.pdf" but the PDF was never
uploaded (`zotero_get_item_children` empty, desktop shows no attachment).

## Root cause (two layers)

1. **pyzotero `attachment_both`** copies the *full file path* into the attachment
   template's `filename` field. The Zotero web API rejects it:
   `400 Stored-file filename '/…/x.pdf' cannot contain a directory path`.
   The attachment item is never created and the upload lands in the `failure` list.
2. **zotero-mcp-server `add_from_file`** never inspects that `failure` list and
   unconditionally prints "File attached" — the false success.

## Fix (2026-07-26)

Runtime monkeypatch applied before the MCP server starts:

- `scripts/zotero_mcp_patch.py` — patches `pyzotero.Zotero.attachment_both` to send
  basename-only `filename` + pass the directory via `Zupload(basedir=…)`, and to
  **raise** when `failure` is non-empty (no more silent success).
- `scripts/zotero-mcp-launcher.py` — imports and applies the patch before
  `zotero_mcp.cli.main()`.
- `tests/test_zotero_mcp_patch.py` — 3 tests (basename+basedir, multi-dir, raise-on-failure).

Verified end-to-end against the live web API: attachment created with real md5.

## Indexing

`.mcp.json` now installs `zotero-mcp-server[semantic,pdf]` so
`zotero_update_search_database` / `zotero_semantic_search` work (first run downloads
chromadb + sentence-transformers — heavy). After adding papers, run
`zotero_update_search_database` to embed them.

## Gotchas

- **Local API disabled on the Mac's Zotero desktop** → all hybrid-mode *reads* 403
  ("Local API is not enabled"). Enable in Zotero: Settings → Advanced →
  "Allow other applications on this computer to communicate with Zotero", or set
  `ZOTERO_LOCAL=false` for pure web mode. Verify uploads via web API in the meantime.
- Zotero dedups identical file content server-side: re-upload returns "unchanged".
- Pre-existing unrelated test failures (4) in test_fixes_regression /
  test_models_serde / test_retry_and_serde_hardening — confirmed on clean HEAD.
