# Literature-Review

Systematic literature review agent. Define → Search → Acquire → Ingest → user chooses next (read, synthesize, export, Zotero).

## Environment

- **One venv only**: `~/.local/share/lit-review-venv`. All Python dependencies (`lit-review` CLI, `zotero-mcp-server`, etc.) live here. Never create ad-hoc venvs or use `uv run` (without `--no-project`) inside the project — it will create `.venv/`.
- **Secrets in `.env`**: `ZOTERO_API_KEY`, `ZOTERO_LIBRARY_ID`, etc. go in `.env` (gitignored). MCP config (`scripts/zotero-mcp-launcher.py`) loads `.env` via stdlib — no dotenv dependency.
- **Cross-platform**: `scripts/zotero-mcp-launcher.py` uses Python stdlib only. `.mcp.json` uses `uv run --no-project --with zotero-mcp-server` to avoid touching the project venv.

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

## Zotero

### Adding papers — do this EVERY time

**Architecture (agreed 2026-07-27)**: ALL papers go into ONE shared Zotero collection
(`Engineering`, key `HNRLNAP9`). Each workspace maintains its own catalogue in
`zotero_registry.jsonl` (file ↔ zotero_key) plus a workspace tag from
`workspace.toml` → `[zotero].tags`. Never create per-topic collections.

1. **确认范围再导入**。用户说"导入哪几篇"就导入哪几篇。先 `lit-review zotero-import --topic <slug> --dry-run` 展示将导入哪些 PDF,与用户核对范围(全部 or 指定篇目)后再执行。禁止未经确认就全量导入。
   - **按篇导入**:`lit-review zotero-import --topic <slug> --candidate-id <id1> --candidate-id <id2>` — 只导入指定论文(推荐用于"就这几篇"场景)。
   - **全量导入**:`lit-review zotero-import --topic <slug>` — 扫描 `download/pdfs` + `papers` + `pdfs` 全部 PDF,仅在用户明确要全部时使用。
   - 去重:DOI → title-key(three-pass grouping);DOI-bearing groups CrossRef-enriched at creation。
2. **Interactive single paper**: `zotero_add_from_file` (MCP) with the collection and
   workspace tag explicitly set — never bare "My Library".
3. **After any import**: `lit-review zotero-maintain --topic <slug>` (registry-scoped
   enrich + local file mirroring; `--all` for whole-collection maintenance), then
   `zotero_update_search_database` (MCP) to re-embed.

### Collections

- Shared collection lives in `workspace.toml` → `[zotero].collection_name` **and**
  `collection_key` (names are not unique — there are two "Engineering" collections;
  the real one is `HNRLNAP9`, `PETTGPID` is an empty stray).
- All workspaces share the collection; workspace identity = registry + tag.
- `zotero-maintain` is registry-scoped by default so it never touches other
  projects' items; `--all` opts into whole-collection maintenance.

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
lit-review init/search/acquire/ingest/export/stats --topic <slug>
lit-review zotero-import/zotero-maintain/zotero-sync/zotero-status --topic <slug>
lit-review login [--profile ...]
```

## AI 推理 — 层解耦,fabric 优先,litellm 回退,每次确认

- **AI 调用层解耦**:fabric(MCP,首选,provider=deepseek,默认 v4-flash)· litellm(`ai/client.py`,`chat()`,回退)· CLI read/synthesize(走 litellm,保留)。各层独立,agent 按需决策。
- **每次调用前必须询问用户用哪个后端 + 模型**(如 "fabric/deepseek-v4-flash,还是 litellm?"),绝不默默用默认。
- 报告/卡片引用用 **ShortRef**(作者+年份,见 `reading/papers_registry.md`),禁用 hash;card 文件名 = `<lastname>-<year>_card.md`。
- 模板库:`templates/`(skill 层)共享,不入 workspace。

## Acquisition — auto-run the full ladder

The acquire call is a single backgrounded command that auto-approves includes and
walks `http → browser → researchgate` per source internally. Run it and move on:

```
lit-review acquire --topic <slug> --approved-by <you> --profile <name> --limit <N>   # run_in_background; N ≤ 20
```

**Session reuse requires `--profile`.** Without it the browser launches a fresh
temporary context with zero cookies, so subscribed/off-campus papers fail even on
a campus IP. Create the profile once, then reuse it:

```
lit-review login --profile <name> --url <publisher-page> --completion browser-close   # log in in headed Chrome, close window
lit-review acquire --topic <slug> --profile <name> --limit <N>
```

`--http-only` is for diagnosis and headless/CI machines with no display only.
`--browser-channel` defaults to `chrome` (omit it). There is no `--headed` flag —
the browser transport is always headed. ResearchGate's circuit breaker handles
error 1020. Check `download/download_log.csv` after the run for per-URL failure
reasons before any manual retry. `maybe` decisions are never auto-approved — use
`--candidate-id <id>` to include one explicitly.

## Memory privacy guardrail

**Research-topic content never enters project-level memory.** Workspace and topic
material — research briefs, concept taxonomies, paper lists/screening outcomes,
acquisition/analysis results, and any conclusions derived from a topic — is
confidential research data. It lives only inside the workspace
(`workspaces/<slug>/`, which is gitignored) and its own scoped
`.claude/rules/MEMORY.md`.

Project-level `.claude/memory/` and `.claude/rules/MEMORY.md` may contain ONLY
generic, topic-agnostic engineering knowledge: tooling bugs fixed, CLI contract
changes, workflow patterns. Never write a topic slug, paper title, or research
finding there. When REM / sharp-review write session memory, strip topic
content before committing; if a topic record was written by mistake, delete it
and amend the commit (do not leave it in git history).

## Details

Progressive disclosure — load as needed:
- **Pipeline step details** → `.claude/skills/literature-review/0[1-5]*.md`
- **Zotero integration + registry format** → `.claude/memory/2026/07/25/zotero-integration-design.md`
- **Provider matrix + directory layout** → `CLAUDE.md`
- **CHP workspace context** → `workspaces/<slug>/workspace.toml` + `research_brief.toml`
