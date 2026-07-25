# Literature-Review

Systematic literature review agent. Define → Search → Acquire → Ingest → user chooses next (read, synthesize, export, Zotero).

## Tool Priority

**Project tools first. Generic tools will hit walls these tools bypass.**

| Task | ✅ Use | ❌ Skip |
|------|-------|--------|
| PDF download | `lit-review acquire --topic <slug>` | curl / wget |
| Paper import + OA PDF | `zotero_add_by_doi` (MCP) | manual HTTP |
| Batch parallelism | `Workflow` tool | sequential Bash loops |
| Semantic search | `zotero_semantic_search` | grep on PDFs |
| Deep-read | `lit-review read --topic <slug> --paper <id>` | ad-hoc Read of text dumps |

## PDF Download Strategy

**Publisher sites (IEEE Xplore, Springer Link) use Cloudflare Turnstile — automated download WILL fail. Always resolve URLs in this order:**

1. **University repository** — `repo.uni-hannover.de`, `acris.aalto.fi`, `nottingham-repository.worktribe.com`, etc. No Cloudflare, use HTTP fast path.
2. **Preprint servers** — arXiv, techrxiv. Direct PDF download.
3. **ResearchGate** — `www.researchgate.net`. Author-uploaded PDFs, often available for otherwise paywalled papers. Handled by `literature_review/acquire/researchgate.py`, which does the three hops a plain URL fetch cannot: search → publication page → `/download`. An RG search is appended automatically for every paper (ranked last), so no queue changes are needed.

   **Rate limits are strict and escalate to an IP ban.** The module paces requests (~6 s apart, max 3 publication pages per paper), warms up on the home page to avoid a cold-search challenge, and waits out a bot check so you can solve it in the headed window. If Cloudflare returns **error 1020 ("Access denied", IP-level ban)** there is nothing to solve: a circuit breaker trips and the rest of the run skips ResearchGate. Do not retry — wait for the ban to lapse or use a different network. Never attempt to evade it; that risks the institution's IP reputation.
4. **Publisher OA page** — only as last resort; requires real Chrome + persistent profile + cookie-dismissal + PDF-button auto-click.

**Architecture** (`literature_review/acquire/`): `oa_resolve` (identity → ranked sources) →
`transport` (sources → bytes, cheapest-capable first: `http` → `browser` → `researchgate`) →
`verify` (one definition of a valid PDF) → `ledger` (append-only `download/ledger.jsonl`,
the source of truth downstream reads). `engine` orchestrates; `net` holds the single HTTP policy.
`download/download_log.csv` is a derived projection of the ledger — never edit it.

Use `lit-review acquire --topic <slug> --dry-run` to print the per-paper source plan without
downloading anything; that answers "why didn't this download" before spending a run.

**`lit-review acquire` does this automatically.** For each queue item it:

1. Resolves the DOI against Unpaywall, OpenAlex, and Semantic Scholar to discover repository/preprint mirrors.
2. Merges those with the queue's `pdf_url`/`html_url` and ranks all of them by the priority above (`literature_review/acquire/oa_resolve.py`).
3. Tries every source in order — one blocked publisher no longer fails the paper.
4. Per source: plain HTTP first (landing pages are parsed for `citation_pdf_url` / `/files/` / `/bitstream/` links), falling back to the browser only for Cloudflare-guarded hosts.
5. On total failure, logs the per-URL reason in `download/download_log.csv` — read that column before retrying by hand.

So a bare DOI in the queue is usually enough; a good `html_url` still helps. Set `LIT_REVIEW_CONTACT` to your email to enter the Unpaywall/OpenAlex polite pool.

## Search Sources

| Source | Access | Notes |
|--------|--------|-------|
| Semantic Scholar API | REST (free) | OA URL aggregation, citation graph |
| IEEE Xplore | REST + Playwright | Primary for EE papers |
| arXiv | REST + direct PDF | Preprints |
| DBLP | REST | CS bibliography |
| **ResearchGate** | Playwright browser | Author uploads, paywalled papers often available; blocks HTTP |

## Key Commands

```
lit-review init/search/acquire/ingest/read/synthesize/export/stats --topic <slug>
lit-review login [--profile ...]
```

## Details

Progressive disclosure — load as needed:
- **Pipeline step details** → `.claude/skills/literature-review/0[1-5]*.md`
- **Zotero integration + registry format** → `.claude/memory/2026/07/25/zotero-integration-design.md`
- **Provider matrix + directory layout** → `CLAUDE.md`
- **CHP workspace context** → `workspaces/<slug>/workspace.toml` + `research_brief.toml`
