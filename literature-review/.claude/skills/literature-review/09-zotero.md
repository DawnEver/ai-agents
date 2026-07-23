# Step 09 — Zotero bridge

This step is implemented in Phase 3.

## Planned behaviour

Bidirectional sync between the literature review workspace and a Zotero collection. Push ingested papers with their metadata and reading notes into Zotero. Pull papers already in Zotero that match the review topic to seed new reviews or supplement existing ones. Maintains a sync log to avoid duplicate entries.

## Output (Phase 3)

```
workspaces/<slug>/
  zotero/
    sync_log.json                ← bidirectional sync audit trail
```

Zotero collection is updated with:
- Paper metadata (title, authors, venue, year, DOI)
- PDF attachments
- Reading notes as child notes
- Tags derived from concept taxonomy

## Current action

Pipeline complete.
