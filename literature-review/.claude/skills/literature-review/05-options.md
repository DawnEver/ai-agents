# Options Menu — What would you like to do?

核心流水线完成后，后续能力作为选项菜单供用户自由选择。非强制、非线性、可组合。

## AI 推理机制（所有 AI 步骤必须遵守）

**AI 调用层解耦，fabric 优先，litellm 回退，agent 按需决策。** 各层互相独立：

- **fabric**（MCP `fabric__call` / `fabric__fan_out`）—— 首选。provider = **deepseek**，默认模型 **deepseek-v4-flash**。
- **litellm**（`ai/client.py` 的 `chat()`）—— 作为 fabric 的回退，保留不删。
- **CLI read/synthesize** —— 走 litellm，保留，可用作回退。

**每次 AI 调用前必须先询问用户确认用哪个后端 + 哪个模型**（如"这篇用 fabric/deepseek-v4-flash,还是 litellm?"）。列出任务 + 建议,等用户确认后再发起。绝不默默用默认。

调用结果直接由 orchestrator 落盘（写 `reading/*.md`、`notes/*.md` 等）。

## 论文引用规范（建立后永久遵守）

**报告/卡片一律用 ShortRef（作者+年份），禁用 hash。**

- 唯一引用源 = 各 workspace 的 `reading/papers_registry.md`（模板见 `templates/_papers_registry_template.md`）。
- 正文引用：`[Author et al. YYYY]` 或 `Author (YYYY)`。
- 卡片文件名 = `<author-lastname>-<year>_card.md`（多名作者取首个；同作者同年加后缀）。
- `candidate_id`(hash) 只用于 CLI 操作，绝不进入叙述性报告。
- card 模板见 `templates/_card_template.md`（skill 层，跨 topic 共享）。

## Available Options

### Deep-Read Papers

用 fabric(deepseek) 对论文做深度阅读 → 生成 paper card：
1. 复制 `templates/_card_template.md` 为 `reading/<lastname>-<year>_card.md`
2. **先询问用户确认模型**（默认 deepseek-v4-flash）
3. 用 `fabric__call`（provider=deepseek）读分解后的 `ingest/<id>/1-paper-text/` markdown，产出结构化 card
4. 追加对应行到 `reading/papers_registry.md`

（`lit-review read` 命令依赖 litellm，已被 fabric 机制取代，不再使用。）

### Cross-Paper Synthesis

综合所有 paper card → `notes/synthesis.md`。同样用 fabric(deepseek)，先确认模型。引用一律用 ShortRef。

### Export

```bash
lit-review export --topic <slug> [--format markdown|csv|bibtex|json] [--paper <id1> ...]
```
Exports paper cards in the requested format to `export/`.

### Statistics & Plots

```bash
lit-review stats --topic <slug> [--plots]
```
Summary statistics (candidates, screening breakdown, downloads, decomposed, deep-read). With `--plots`, generates year/venue distribution charts.

### Zotero Sync

Push all workspace PDFs into the shared Zotero collection (`workspace.toml` → `[zotero]`), then fix metadata and local files:

```
lit-review zotero-import --topic <slug>     # DOI-deduped batch import + registry
lit-review zotero-maintain --topic <slug>   # enrich bare items + mirror PDFs to ~/Zotero/storage
```

Then re-embed via the `zotero_update_search_database` MCP tool so `zotero_semantic_search` sees the new items. Workspace ↔ Zotero mapping lives in `zotero_registry.jsonl`; every item gets the workspace tag.

### Custom

Anything else — re-search with modified queries, add papers manually, compare specific papers, generate a summary report. Just ask.

## How it works

1. **Present the menu** after step 04 completes (or whenever the user asks).
2. **User picks** one or more options. Execute and return to menu.
3. **No forced sequence**. User can deep-read 2 papers, skip synthesis, export BibTeX, done.
4. **AI steps go through fabric(deepseek), model confirmed per call; non-AI steps use CLI.**
