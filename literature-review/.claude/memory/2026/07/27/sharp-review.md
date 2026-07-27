---
name: sharp-review-2026-07-27
description: Sharp review findings — 25 total
metadata:
  type: project
---

## Review 2026-07-27 (session) — diff review + docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): skipped
- Reviewer B (DeepSeek): OK
- Reviewer C (Opus): OK

### Confirmed findings

---

### [SR-20260727-001] [HIGH] literature-review/literature_review/cli.py — Empty registry inverts scoping: zotero-maintain enriches the WHOLE collection instead of nothing

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Pass `only_keys=only_keys` directly (not `only_keys or None`); when the registry is empty, either short-circuit with 'nothing to enrich' or require --all explicitly.

In _handle_zotero_maintain: `only_keys = {e.get('zotero_key') for e in load_registry(...)}; only_keys.discard(None)` then `enrich_items(..., only_keys=only_keys or None)`. If the workspace registry is empty (fresh workspace, or zotero-import never ran), `only_keys` is an empty set, `or None` turns it into None, and enrich_items treats None as 'no restriction' — it will then scan and PUT-update every too-thin item in the shared collection, mutating items belonging to other projects. This is exactly the shared-collection hazard the only_keys parameter exists to prevent, defeated by a falsy-value shortcut.

---

### [SR-20260727-002] [HIGH] literature-review/scripts/zotero_mcp_patch.py — Monkey-patch on pyzotero internals with no version guard; silently rots when pyzotero changes

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Pin a pyzotero version range alongside the patch, assert the patched attributes exist and have the expected signature at apply() time, and log loudly that the patch is active. Better: submit the fix upstream and pin to the fixed release.

apply() replaces Zotero.attachment_both wholesale and calls Zupload(self, templates, parentid, basedir=basedir).upload(), assuming the private _attachment_template method, Zupload's constructor signature, and the success/failure/unchanged result keys all keep their current shape. Any pyzotero upgrade either silently reverts to the buggy behavior (if the patch fails to import internals it raises at apply time, but if internals change shape the failure mode is a confusing TypeError deep in an upload) or breaks uploads entirely. Since the launcher applies this unconditionally for every MCP session, a routine `uv` dependency refresh becomes a silent behavioral change. There is also no test asserting the patch still matches the installed pyzotero version.

---

### [SR-20260727-003] [MEDIUM] literature-review/literature_review/export/zotero_import.py — _find_item_by_doi swallows all exceptions — auth/network failures silently cause duplicate item creation

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Catch only expected lookup errors (or let the exception propagate to the per-group handler which already records 'error'). A failed DOI lookup must not fall through to create_items.

`try: for item in zot.items(q=doi) ... except Exception: pass` — if the API key is wrong, rate-limited (403/429), or the network drops, the lookup returns None and the code proceeds to create_items, manufacturing duplicate items in Zotero for papers already in the library. The dedupe guarantee this module's docstring promises collapses precisely when the API is flaky, which is when batch imports most need it.

---

### [SR-20260727-004] [MEDIUM] literature-review/literature_review/export/zotero_maintenance.py — find_collection_key fetches only the first 100 collections; misses beyond that silently

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Paginate /collections like iter_items does (start/limit loop) or use the collection-key config path as the documented requirement and warn when falling back to name lookup.

`_request(f"{base}/collections?limit=100")` with no pagination. In a library with >100 collections the target collection is simply 'not found' and the CLI errors out with a misleading message — or worse, if two collections share a name (allowed in Zotero), the first in arbitrary API order wins. The CLI comments acknowledge names aren't unique but the fallback still uses them.

---

### [SR-20260727-005] [MEDIUM] literature-review/literature_review/export/zotero_maintenance.py — update_item changes itemType but keeps old-type fields, risking 400s and silently dropped updates

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** After changing itemType, strip fields not valid for the new type (or fetch Zotero's item-type field schema), and treat non-204 responses as reported errors — currently `return status == 204` swallows the server's error body.

When enrichment upgrades `document` -> `journalArticle`, the shallow merge sets data['itemType'] but leaves every field the bare document item had. Zotero's API validates fields per item type and can 400 the PUT; update_item then returns False and enrich_items records `applied=False` with no detail about why (the response body from the failed PUT is discarded via `status, _ = _request(...)`). Silent update failures on a maintenance tool whose entire job is fixing items is the worst failure mode.

---

### [SR-20260727-006] [MEDIUM] literature-review/literature_review/export/zotero_maintenance.py — mirror_attachments magic-byte check rejects valid non-PDF/non-zip attachments as errors

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Check the Content-Type header or compare against the attachment's md5 instead of sniffing for %PDF/PK; at minimum accept any 200 response with non-empty body and log the type.

`if status != 200 or not raw.startswith((b"%PDF", b"PK"))` — any attachment that is an HTML snapshot, plain text, image, or other legitimate stored file is reported as 'error: http 200' and never mirrored. The filename is right there to gate the check to .pdf only; as written the mirror silently under-reports coverage for mixed-format libraries.

---

### [SR-20260727-007] [MEDIUM] literature-review/literature_review/export/zotero_import.py — _load_pyzotero mutates global sys.path at runtime to import a sibling script

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Move zotero_mcp_patch.py into the package (literature_review/export/_pyzotero_patch.py) and import it normally; scripts/zotero-mcp-launcher.py can keep its own thin copy or import from the installed package too.

`sys.path.insert(0, .../scripts); import zotero_mcp_patch` makes package behavior depend on repository layout, breaks if the package is installed without the scripts dir, and pollutes sys.path for the whole process (the launcher also inserts the same dir, so the module now exists under two import paths). The patch is production code used by the library, not a script — it belongs in the package.

---

### [SR-20260727-008] [MEDIUM] literature-review/literature_review/export/zotero_maintenance.py — Writing bytes directly into ~/Zotero/storage races with the running Zotero desktop client

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Verify with md5 after write, and document/enforce that Zotero desktop should be closed or that files must be placed before sync; alternatively use Zotero's local API (localhost:23119) to register files instead of raw filesystem surgery.

mirror_attachments writes files into Zotero's storage directory behind the desktop app's back. If Zotero is running and syncing concurrently, it can partially download the same attachment, producing a torn file on one side, or overwrite the mirrored file. There is no locking, no md5 verification after write (the md5 is available in data['md5'] and never used), and dest.exists() with size>0 counts a half-synced file as 'present'. A corrupted PDF is then 'present' forever.

---

### [SR-20260727-009] [LOW] literature-review/literature_review/cli.py — zotero-import --dry-run requires ZOTERO_API_KEY/Library ID even though it never touches the API

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Move the credential check below the dry-run early return (or into import_workspace_pdfs after the dry-run branch), so the dedupe plan can be inspected on machines without credentials.

_handle_zotero_import checks api_key/library_id and exits 2 before calling import_workspace_pdfs, whose dry_run path returns before _load_pyzotero. Dry-run is exactly what you'd run on a fresh checkout to sanity-check grouping; forcing .env setup for a read-only local operation is friction with no benefit.

---

### [SR-20260727-010] [LOW] literature-review/literature_review/export/zotero_import.py — Registry saved once per item inside the loop — O(n) full-file rewrites

- **Category:** Performance
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Accumulate registry updates and save_registry once after the loop (plus a save in a finally block if crash-safety mid-run matters).

save_registry(workspace_dir, registry) runs inside the per-group loop. For a few hundred PDFs this rewrites the entire JSONL file a few hundred times. Not catastrophic, but trivially avoidable and inconsistent with the ledger-style append-only pattern used elsewhere in the project.

---

### [SR-20260727-011] [LOW] literature-review/literature_review/export/zotero_import.py — extract_doi_from_pdf swallows every exception, making DOI-extraction failures invisible

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Catch fitz-specific/open errors narrowly and count extraction failures in the result detail; a corrupt PDF currently just degrades to filename grouping with no signal.

Bare `except Exception: return None` around fitz.open/page reads means encrypted, corrupt, or zero-byte PDFs silently fall into the fn: bucket and may import as bare 'document' items — the very problem zotero_maintenance exists to clean up. A per-file detail note would let the user distinguish 'no DOI in paper' from 'could not read PDF'.

---

### [SR-20260727-012] [LOW] literature-review/literature_review/export/zotero_import.py — Duplicates within a group are dropped: never attached, never recorded in the registry

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Record duplicate paths in the registry entry (e.g. 'alternate_paths') so provenance survives; or attach them as additional files when they differ in content.

group_pdfs carefully collects duplicates, and ImportResult reports a count, but the registry entry only stores the canonical source_path. If the canonical file later turns out to be a worse scan, the information about where the alternates lived is lost outside the console output.

---

### [SR-20260727-013] [LOW] literature-review/literature_review/export/zotero_maintenance.py — _split_name butchers multi-word surnames ('van der Waals', 'de Berg')

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Prefer CrossRef/arXiv structured author fields when available (CrossRef already gives given/family); for the arXiv path, at least keep a small particle set (van, von, de, der, den, di, le) attached to the lastName.

`name.rsplit(' ', 1)` turns 'Mark de Berg' into firstName='Mark', lastName='Berg' — wrong sort order and wrong citations in bibliographies for exactly the Dutch/German names common in the CS literature this tool imports.

---

### [SR-20260727-014] [LOW] literature-review/.mcp.json — File now missing trailing newline

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add the trailing newline back.

Trivial, but it will keep showing up as diff noise in every future edit of this file.

---

### [SR-20260727-015] [INFO] literature-review/literature_review/export/zotero_maintenance.py — 500-line module mixing HTTP plumbing, metadata mapping, enrichment, and filesystem mirroring

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split into _crossref.py / _arxiv.py (metadata sources), enrich.py, mirror.py; keep _request/_library_base in a small _api.py. The pure helpers are well-isolated already, which makes the split cheap.

Per the review scope (>300 lines warrants scrutiny): the module is cohesive in theme but does four separable jobs, and the tests already mirror that structure. Splitting would also remove the temptation of the circular-ish import where zotero_import reaches into zotero_maintenance for extract_doi/fetch_crossref_doi.

---

### [SR-20260727-016] [INFO] literature-review/literature_review/export/zotero_import.py — Three-pass grouping heuristic is clever but fragile; title_key substring merging can over-merge

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a guard that both stems share an author-year prefix (or same first token) before substring-merging, and log every heuristic merge in the result detail so bad merges are auditable.

The third pass merges any two groups where one normalized title_key (>=20 chars) is a substring of the other and at most one has a DOI. Two genuinely different papers from the same author-year with a common title prefix (e.g. 'smith2023_Graph_Coloring' vs 'smith2023_Graph_Coloring_Algorithms_Survey'... wait, that one is arguably fine — but 'smith2023_Attention' vs 'smith2023_Attention_Is_All_You_Need_Revisited' is not the same paper) will be collapsed with only a console '(+1 dup)' as evidence. The >=20 char threshold helps but doesn't prevent it.

---

### [SR-20260727-017] [HIGH] literature-review/AGENT.md — `--all` documented as "whole-collection" but code runs against the whole LIBRARY

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Fix AGENT.md ("`--all` for whole-collection maintenance", "opts into whole-collection maintenance") and the memory doc zotero-maintenance-pipeline.md ("`--all` for whole collection") to say "whole library", or change the code to keep the collection filter and only drop the registry scope.

AGENT.md line ~68 and ~77 and .claude/memory/2026/07/26/zotero-maintenance-pipeline.md ("Enrich — registry-scoped by default ... `--all` for whole collection") claim --all widens scope to the whole collection. In literature_review/cli.py the flag is dest=whole_library with help "Run against the whole library instead of one collection", and _handle_zotero_maintain then passes collection_key=None into zm.enrich_items / zm.mirror_attachments, so enrichment and mirroring iterate EVERY item in the Zotero library — exactly the kind of unscoped run that caused the 2026-07-27 mis-enrichment incident the memory doc itself describes. Given the collection is shared, a user trusting the docs will blast other projects' items.

---

### [SR-20260727-018] [HIGH] literature-review/.claude/memory/2026/07/25/zotero-integration-design.md — Old design memory contradicts the new shared-collection architecture and is not marked superseded

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a "superseded by 2026-07-27 shared-Engineering design (see zotero-maintenance-pipeline.md)" banner to zotero-integration-design.md, or rewrite its flat-collection/slug-name principles.

The 2026-07-25 memory states "One workspace → one Zotero collection" and "Workspace slug = collection name. Predictable, idempotent mapping" (lines 14, 23). The new AGENT.md and zotero-maintenance-pipeline.md say the opposite: ALL papers go into ONE shared collection (Engineering/HNRLNAP9) and "Never create per-topic collections". The new memory says it "supersedes per-topic collections" but the old memory file itself is untouched and still indexed in .claude/rules/MEMORY.md with no staleness marker, so an agent loading the older design doc gets actively wrong instructions.

---

### [SR-20260727-019] [MEDIUM] literature-review/AGENT.md — "registry-scoped ... never touches other projects' items" is only true for enrich, not for mirror

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Clarify in AGENT.md and zotero-maintenance-pipeline.md that only the enrich phase is registry-scoped; mirror always scans the full collection (or library with --all) and downloads other projects' attachments into ~/Zotero/storage.

AGENT.md says "zotero-maintain is registry-scoped by default so it never touches other projects' items". In _handle_zotero_maintain only enrich_items receives only_keys; mirror_attachments is called with just collection_key and iterates every attachment in the shared Engineering collection regardless of registry membership (zotero_maintenance.py mirror_attachments). It won't corrupt metadata, but it does touch/download other projects' files — the blanket safety claim is wrong, and with --all it mirrors the entire library.

---

### [SR-20260727-020] [MEDIUM] literature-review/.claude/skills/literature-review/05-options.md — Options-menu doc still describes the old "Zotero Sync" flow; new import/maintain pipeline is undocumented there

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the "Zotero Sync" section (or add an option) to reference `lit-review zotero-import --topic <slug>` and `zotero-maintain`, the shared Engineering collection, and the post-import `zotero_update_search_database` step.

05-options.md line 31-32 still says "Push paper metadata, PDFs, and reading notes to a Zotero collection. Requires Zotero binding in workspace.toml" — the pre-2026-07-27 per-topic-collection flow. AGENT.md now declares a different preferred path (zotero-import → zotero-maintain → MCP re-embed), but the skill doc a user/agent actually walks through after step 04 never mentions it, so the two docs steer the workflow differently.

---

### [SR-20260727-021] [LOW] literature-review/literature_review/cli.py — `zotero-maintain --all` still requires a meaningless `--topic` argument

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make --topic optional when --all is passed (validate in the handler: require topic unless whole_library), and document that in AGENT.md.

The argparse definition has `p.add_argument("--topic", required=True)` for zotero-maintain, but _handle_zotero_maintain only reads args.topic inside the `if not args.whole_library` branch. So `lit-review zotero-maintain --all` fails with "the following arguments are required: --topic" unless you pass a dummy slug. No doc mentions this quirk.

---

### [SR-20260727-022] [LOW] literature-review/.claude/rules/MEMORY.md — New memory zotero-maintenance-pipeline.md is not in the memory index

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add an index entry: [2026-07-26 zotero-maintenance-pipeline](../memory/2026/07/26/zotero-maintenance-pipeline.md).

.claude/rules/MEMORY.md lists the 2026-07-26 hybrid-mode bug, 2026-07-25 design, and 2026-07-25 entry-point bug, but not the new 2026-07-26 zotero-maintenance-pipeline.md — the document that records the current authoritative architecture. Agents relying on the index will miss the superseding design and keep following the stale 2026-07-25 one.

---

### [SR-20260727-023] [LOW] literature-review/AGENT.md — Key Commands list omits the zotero-* commands the doc itself mandates

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Extend the command line to `lit-review init/search/acquire/ingest/read/synthesize/export/stats/zotero-import/zotero-maintain --topic <slug>` (and optionally zotero-sync/zotero-status).

The "Key Commands" block still shows only the pre-Zotero pipeline (`init/search/acquire/ingest/read/synthesize/export/stats`), while the same file's Zotero section makes `zotero-import` / `zotero-maintain` the required post-import sequence. The canonical quick-reference is out of sync with the prose.

---

### [SR-20260727-024] [INFO] literature-review/AGENT.md — Claim that zotero-import "creates CrossRef-enriched items" overstates: identifier-less PDFs become bare `document` items

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Note that only DOI-bearing groups get CrossRef enrichment; DOI-less files import as `document` items titled by filename stem, which zotero-maintain's enrich pass is meant to fix later.

build_item_template (zotero_import.py:161-174) only calls fetch_crossref_doi when group.doi is set; otherwise it returns zot.item_template("document") with title = filename stem. The AGENT.md bullet implies universal enrichment. Not wrong enough to mislead badly — this is exactly why the maintain step exists — but the doc elides the two-tier outcome.

---

### [SR-20260727-025] [INFO] literature-review/.mcp.json — File lost its trailing newline

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Re-add the final newline to keep diffs/POSIX tools clean.

The diff ends with "\ No newline at end of file" — trivial, but it will show up as noise in every future diff touching the file.
