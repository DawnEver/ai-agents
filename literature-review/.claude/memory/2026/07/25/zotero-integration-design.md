---
name: zotero-integration-design
description: Zotero integration principles — flat collections, workspace registry, MCP-first workflow
created: 2026-07-25
metadata:
  type: design
tags: [zotero, architecture, registry, mcp]
---

## Zotero Integration Design

> ⚠️ **SUPERSEDED 2026-07-27.** The "one workspace → one collection" and
> "workspace slug = collection name" principles below are replaced by the
> shared-collection architecture: ALL papers → `Engineering` (`HNRLNAP9`),
> workspace identity = `zotero_registry.jsonl` + workspace tag.
> See `2026/07/26/zotero-maintenance-pipeline.md`. The registry format and
> registry-CRUD parts below still apply.

### Principles

1. **Flat collections.** One workspace → one Zotero collection. No nested subcollections.
   Zotero is for human reading and PDF storage, not complex taxonomy.

2. **Registry as bridge.** Each workspace maintains `zotero_registry.jsonl` —
   the single source of truth linking `candidate_id` ↔ `zotero_key`.

3. **MCP-first.** The agent uses Zotero MCP tools directly for interactive operations.
   The Python `sync_papers` function handles batch CLI sync.

4. **Workspace slug = collection name.** Predictable, idempotent mapping.

### Registry Format

```jsonl
{"candidate_id": "xxx", "zotero_key": "ABC12345", "title": "...", "doi": "...", "date_synced": "2026-07-25T...", "pdf_attached": true, "notes_synced": false, "zotero_collection": "my-topic"}
```

### Files Changed

- `literature_review/models.py` — added `ZoteroRegistryEntry` dataclass, updated `ZoteroBinding`
- `literature_review/export/zotero.py` — added registry CRUD + workspace-aware `sync_papers`
- `literature_review/export/__init__.py` — exported new registry functions
- `literature_review/cli.py` — added `zotero-sync` and `zotero-status` commands
- `AGENT.md` — documented Zotero integration section
- `workspaces/*/workspace.toml` — added `collection_name` field, `sync_attachments = true`

### Agent Workflow

1. Read `zotero_registry.jsonl` to know what's already synced
2. `zotero_search_collections` / `zotero_create_collection` — find or create flat collection
3. `zotero_add_by_doi` — add paper (rich metadata + OA PDF)
4. `zotero_batch_update_tags` — tag with workspace identifier
5. Append entry to `zotero_registry.jsonl`

### CLI

```bash
lit-review zotero-sync --topic <slug>      # Sync include/maybe papers
lit-review zotero-status --topic <slug>    # Show registry state
```
