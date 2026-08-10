# Literature-Review

Systematic literature review agent. Define → Search → Acquire → Ingest → user chooses next (read, synthesize, export, Zotero).

> **本文档只放开发原则。** 具体操作步骤(命令、参数、排障、流程)在 skill 工作流
> `.claude/skills/literature-review/` 的 playbook(`0[1-5]*.md`)。原则与操作分离——
> 操作细节一律查 skill,不在这里重复。

## Environment

- **One venv only**: `~/.local/share/lit-review-venv`. All Python dependencies (`lit-review` CLI, `zotero-mcp-server`, etc.) live here. Never create ad-hoc venvs or use `uv run` (without `--no-project`) inside the project — it will create `.venv/`.
- **Secrets in `.env`**: `ZOTERO_API_KEY`, `ZOTERO_LIBRARY_ID`, etc. go in `.env` (gitignored). MCP config (`scripts/zotero-mcp-launcher.py`) loads `.env` via stdlib — no dotenv dependency.
- **Cross-platform**: `scripts/zotero-mcp-launcher.py` uses Python stdlib only. `.mcp.json` uses `uv run --no-project --with zotero-mcp-server` to avoid touching the project venv.

## Tool Priority

**Project tools first. Generic tools will hit walls these tools bypass.**

| Task | ✅ Use | ❌ Skip |
|------|-------|--------|
| PDF download | `lit-review acquire` | curl / wget |
| Paper import + OA PDF | `zotero_add_by_doi` (MCP) | manual HTTP |
| Batch parallelism | Claude named agents or Codex collaboration agents, using the canonical prompts in `.claude/agents/` | unvalidated sequential Bash loops |
| Semantic search | `zotero_semantic_search` | grep on PDFs |
| Deep-read | skill 工作流(05-options: fabric/litellm,每次确认) | ad-hoc Read of text dumps |

## PDF Download Strategy — 原则

Publisher sites (IEEE Xplore, Springer Link) use Cloudflare Turnstile — automated download WILL fail. Resolve URLs by priority: **university repository → preprint (arXiv/techrxiv) → ResearchGate → publisher OA page**.

- ResearchGate rate-limits escalate to IP ban (error 1020 is not solvable — circuit-break, never retry, never evade).
- Architecture: `oa_resolve` (identity → ranked sources) → `transport` (http → browser → researchgate) → `verify` (valid PDF) → `ledger` (append-only `download/ledger.jsonl`; `download_log.csv` is a derived projection — never edit it).

**Operations(来源优先级细节、限速、dry-run、排障)→ `03-acquire.md`。**

## Zotero — 原则

- ALL papers → ONE shared collection (`workspace.toml` → `[zotero]`, resolved by `collection_key`; names are not unique — use the key, not the name). Never per-topic collections.
- Workspace identity = `zotero_registry.jsonl` (file ↔ zotero_key) + workspace tag.
- `zotero-maintain` is registry-scoped by default (never touches other projects' items).

**Operations(导入范围确认、import/maintain/mirror、PDF-unavailable 排查)→ `05-options.md` → Zotero Sync。**

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

## AI 推理 — 原则

- 各层解耦:fabric 首选(provider=deepseek,默认 v4-flash)· litellm 回退 · CLI read/synthesize 保留。agent 按需决策。
- 每次调用前确认后端+模型。
- 报告引用用 ShortRef(作者+年份,禁 hash);模板在 skill 层共享,不入 workspace。

**Operations(模型选择、引用格式、模板用法)→ `05-options.md`。**

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
