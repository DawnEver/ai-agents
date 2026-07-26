---
name: zotero-hybrid-mode-pdf-bug
description: zotero_add_from_file silently fails PDF upload in hybrid mode (ZOTERO_LOCAL=true + API key)
created: 2026-07-26
metadata:
  type: bug
tags: [zotero, mcp, hybrid-mode, pdf, attachment]
---

## Problem

In hybrid mode (ZOTERO_LOCAL=true + ZOTERO_API_KEY + ZOTERO_LIBRARY_ID), `zotero_add_from_file`
reports "File attached: <filename>.pdf" but the file is never actually uploaded. Verification:
- `zotero_get_item_children` returns "No child items found"
- `zotero_get_attachment_path` returns "No attachments found"
- Zotero desktop does not show the attachment

Tested on 5+ files including zanarini2017 (swopt.pdf), england2021, liang2019tec — all identical behavior.

`zotero_add_by_doi` metadata-only write works correctly. Collections and tags are applied.

## Workaround

Manually drag PDFs into Zotero desktop. Or use pure web mode (ZOTERO_LOCAL=false).

## Context

- zotero-mcp-server version: latest (2026-07-26)
- Python: 3.13.3 in ~/.local/share/lit-review-venv
- Zotero desktop: running (3 processes confirmed)
- OS: Windows 11
