---
name: literature-review-architecture-plan-2026-07-23
description: Created a 7-document reference architecture plan for the literature-review project — a general-purpose literature review harness with multi-topic workspaces, Zotero integration, and paper_pdf_ingest PDF decomposition.
metadata.type: project
---

# Literature Review Architecture Plan (2026-07-23)

Created a reference plan at `literature-review temp/` with 7 documents:

1. `01-architecture.md` — System layers, directory layout, core design decisions (provider abstraction, lens plugins, workspace as first-class citizen)
2. `02-data-contracts.md` — Full data contracts from research brief through paper card to Zotero bridge, with YAML examples and versioning policy
3. `03-skill-pipeline.md` — Three-stage pipeline: scout (discover→download→decompose) → read (triage→deep-read→note) → zotero (export→import→sync)
4. `04-workspace-model.md` — Multi-topic workspace model with parent-child inheritance, workspace.yaml schema, and CLI design
5. `05-zotero-integration.md` — Zotero bridge design: bidirectional integration via Web API, BetterBibTeX import path, collection health check
6. `06-implementation-phases.md` — Phased roadmap: Phase 0 Foundation → Phase 1 Scout → Phase 2 Read → Phase 3 Zotero → Phase 4 Multi-Provider
7. `07-reference-analysis.md` — Migration map from reference repo: 8 items to keep, 8 to fix, 8 new capabilities

## Key Design Decisions
- Provider abstraction over hardcoded IEEE
- Domain lenses as pluggable YAML (not hardcoded markdown)
- Workspace as first-class concept with Zotero collection binding
- `paper_pdf_ingest` invoked via `PAPER_INGEST_ROOT` env var (no hardcoded paths)
- Zotero communication via Web API only (never direct SQLite)
- Shared schemas at project root (not per-skill)

## Next Steps
Phase 0 implementation: project scaffolding, shared schemas, provider interface, workspace CLI.
