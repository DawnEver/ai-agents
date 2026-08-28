# cc-academia migration (2026-08-28)

Design record for merging literature-review, manuscript-review and
reviewer-discovery into one cc-market plugin. Kept in memory rather than at the
repository root: the plan is finished, the code is the current truth, and a
stale plan next to working code gets read as documentation.

The parts still worth returning to are §0.2 (eleven questions settled by probing
live APIs, several of which contradict the vendor documentation) and §13 (where
the implementation diverged from the plan, and the three defects only a live run
exposed).

Implementation lives in `Sync/claude/cc-market/cc-academia/`.

---

# cc-academia — 重构与迁移计划

> 状态：**已实施完毕**。全部 7 个 phase 落地，395 测试通过，已推送 DawnEver/cc-market。
> 实施中发现并修正的偏差记录在 §13。
> 目标：把 literature-review / manuscript-review / reviewer-discovery 合并为**一个**
> Claude + Codex 双 host 插件 `cc-academia`，自带唯一的 Python 库，
> 落在既有 marketplace 仓 `Sync/claude/cc-market/cc-academia/`（GitHub public，DawnEver/cc-market）。
> 构建环境用 `UV_PROJECT_ENVIRONMENT` 指到本地盘，累积库默认本地盘 —— 两者都不进 OneDrive 同步。
> 不考虑向后兼容：import 路径、CLI 参数、数据布局、skill 命名可以彻底重来。

---

## 0. 事实核查

### 0.1 现状

| 观察 | 数据 | 结论 |
|------|------|------|
| literature-review 654MB | 其中 `workspaces/` 651MB | **OneDrive 的负担是数据不是代码**；迁移收益是版本控制与 CI，不是减重 |
| manuscript-review 245MB | Python 仅 137 行 | 它是 prompt 项目；其 `scripts/ingest.py` 与 lit-review 的 `pipeline/ingest.py` 合并为唯一实现 |
| 现有 Python 代码 | `literature_review/` 10,562 行 + 19 个测试 | 迁移主体 |
| 插件源码仓 | `Sync/claude/cc-market`（26MB，DawnEver/cc-market，autoUpdate） | 双 host 布局可直接照搬 |
| Codex 兼容既有做法 | 每插件 `.claude-plugin/plugin.json` + `.codex-plugin/plugin.json`；市场 `.claude-plugin/marketplace.json` + `.agents/plugins/marketplace.json`；生成器 `scripts/gen-codex.mjs`(213 行) + 契约测试 | 照此实现，生成器另写（见 §3.3） |
| 全局配置能力 | `~/.claude/settings.json` 有 `env` 与 `extraKnownMarketplaces` | 覆盖层用环境变量即可，无需新机制 |

### 0.2 实测验证结论（本次全部跑通，非推测）

| # | 问题 | 实测结果 | 对设计的影响 |
|---|------|----------|-------------|
| 1 | IEEE `/rest/search` 是否给 affiliation？ | **否**。record 无 affiliation、无 index terms。但 `authors[]` 含**稳定 IEEE author id**（如 `38080260200`）+ firstName/lastName/normalizedName | 机构与受控词必须由 OpenAlex 提供；IEEE 白送一个持久作者 ID，进消歧第二优先级 |
| 2 | S2 author 端点免 key 够用吗？ | **不够**。首次调用即 `HTTP 429` | **OpenAlex 升为作者维度主源**，S2 降为「有 key 时的补充」 |
| 3 | OpenAlex 机构国别质量？ | 优。`affiliations[].institution` 含 `ror` + `country_code` + **`years` 时间序列**；另有 `last_known_institutions`、`display_name_alternatives` | 地域判定与历任机构轨迹直接可得，不需要自建 |
| 4 | ORCID education 填写率（电机/电力电子/电驱，2023+）？ | 抽样 40 人：**education 30%，employment 38%** | 教育轨迹是**加分项不是必需项**；需第二来源（见 §6） |
| 5 | 目标领域 ORCID 覆盖率？ | 227 位作者中 **203 位有 ORCID（89%）** | 消歧第一优先级（ORCID）对多数人可用，方案可行性远好于预期 |
| 6 | 纯姓名检索可靠吗？ | 搜 "Jianmin Du" 返回的是**农业遥感**领域的人 | 实证支持「禁止纯姓名匹配」，候选人必须从 **论文 → authorship** 反查 |
| 7 | OpenAlex 作者位次粒度？ | 只有 `first / middle / last`；`corresponding_author_ids` 实测为空 | 位次权重改用 authorships **数组下标**推导；通讯作者不可依赖，降级处理 |
| 8 | OpenAlex 还给什么？ | `keywords`(带 score)、`topics`、`referenced_works`(88 条)、`related_works`、`abstract_inverted_index` | 受控词打分与「引文式 COI」有了数据基础 |
| 9 | `orchestrator.py` 是死代码吗？ | **不是**。它是 `cli.py` 分发的 7 个 `run_*` 宏命令层（search/acquire/ingest/read/synthesize/export/stats） | 处置改为**解散**而非删除 |
| 10 | `repair.py` 是死代码吗？ | **不是**。`cli.py:643` 有活调用，`pipeline/ingest.py:41-47` 依赖它写的 `compat_map.json` | 迁移并修两个已知缺陷；`compat_map` 因不要向后兼容而废弃 |
| 11 | Codex 的插件 root 变量？ | Codex **同样注入 `${CLAUDE_PLUGIN_ROOT}`**（只是路径根不同） | playbook 原样写 `${CLAUDE_PLUGIN_ROOT}`，双 host 通用 |

---

## 1. 架构决策

**插件与库同仓同 tag 发布。** 一个功能改动 = 一个 commit，同时改 CLI、playbook、测试。
不存在契约漂移，因此**不需要** `tools.lock`、契约哈希、`doctor` 这类黏合剂——
上一版方案需要它们，正是切口位置错了的证据。

**调用方式：`uv run --project ${CLAUDE_PLUGIN_ROOT}`。** playbook 与它调用的代码在同一棵树里，
版本一致是结构性的，不是检查出来的。代价约 100ms/次 uv 开销。
`uv.lock` 入库保证可复现；`.venv/` gitignore，不影响 marketplace 的 git pull 自动更新。

**分层判据按变更周期，不按格式：**

```
① 随功能变    → cc-market/cc-academia（GitHub public，版本化）
   库代码 · CLI · tests · skills · agents · hooks · COI 默认策略 · 默认 lens · 默认模板

② 随「我这个人」变 → 本仓库 ai-agents / ~/.claude（薄覆盖层，不是分叉）
   我的期刊偏好 override · 我的自定义 lens · memory · 其他非 academia 项目

③ 随研究工作变 → OneDrive workspaces + 本地 SQLite
   稿件 · PDF · 报告 · 累积库
```

第 ② 层是**配置覆盖**：插件出默认值，本仓库出 override。同一类东西可以两边都有。

| 变量 | 默认 | 覆盖位置 |
|------|------|----------|
| `ACADEMIA_CONFIG_DIR` | 插件 `configs/` | `~/.claude/settings.json` → `env` |
| `ACADEMIA_LENS_DIR` | 插件 `configs/lenses/` | 同上 |
| `ACADEMIA_DATA_ROOT` | OneDrive 工作区根 | 同上 |
| `ACADEMIA_DB` | `Documents/PEMC/cc-academia-data/academia.db` | 同上 |
| `UV_PROJECT_ENVIRONMENT` | 无（默认 `.venv/`，会落在 OneDrive） | 用户环境变量，指向本地盘 |
| `ACADEMIA_CONTACT` | 无 | 同上（OpenAlex/Crossref polite pool 需要邮箱） |

解析顺序：override 目录存在同名文件则覆盖，否则回落插件默认。Codex 侧设同名变量。

---

## 2. 仓库布局

```
Sync/claude/cc-market/                   ← 既有 marketplace 仓
├── .claude-plugin/marketplace.json      ← 加一条 cc-academia 条目
├── .agents/plugins/marketplace.json     ← 同上（Codex 侧）
├── .github/workflows/cc-academia-ci.yml
└── cc-academia/                         ← 本插件
    ├── .claude-plugin/plugin.json
    ├── .codex-plugin/plugin.json        Codex 清单（interface 段照 cc-market/rem）
    ├── AGENTS.md  CLAUDE.md(@AGENTS.md)  README.md  CHANGELOG.md
    ├── pyproject.toml  uv.lock          extras: [acquire] [browser] [ai] [pdf] [plot] [zotero]
    ├── src/academia/
    │   ├── core/        models  paths  log  http  text  ai  errors
    │   ├── sources/     base(PaperSource/AuthorSource)  openalex  ieee  orcid  s2  arxiv  dblp
    │   ├── store/       SQLite schema + repository（累积库）
    │   ├── ingest/      PDF → 结构化文本（三个工作流共用的唯一实现）
    │   ├── litreview/   search  acquire/  screen  read  synthesize  export  zotero/
    │   ├── reviewer/    profile  discover  enrich  coi  geo  rank  report  workspace  policy
    │   └── cli/         dispatch  doctor  lit_review  rev_disc
    ├── configs/         coi.toml  journals/*.toml  lenses/*.toml  templates/*.md
    ├── schemas/         paper_profile / candidate / person / coi_verdict / shortlist
    ├── skills/          literature-review/  manuscript-review/  reviewer-discovery/  _shared/
    ├── agents/          前缀 lr- / mr- / rd- 避免同仓撞名
    ├── commands/        new · rerun
    ├── hooks/           稿件保密的 PreToolUse 拦截（Claude 侧第二道锁）
    ├── scripts/         release.py（双清单版本同步）· record_fixtures.py
    └── tests/           单测 + 录制 fixture（不打真实网络）
```

**为什么合成一个插件**：三者共用同一个库、同一个 SQLite 库、同一套 ingest 与 AI 后端选择逻辑。
拆三个插件会让 `_shared/` 无处安放，又绕回跨包协调。
skill 命名空间 `/cc-academia:literature-review` / `:manuscript-review` / `:reviewer-discovery`。

**agent 撞名**：合仓后 agent 名必须唯一，约定前缀
`lr-abstract-screener` `lr-paper-reader` `lr-query-reviewer` /
`mr-reviewer-{1..4}` `mr-polisher` /
`rd-paper-profiler` `rd-candidate-researcher` `rd-coi-auditor` `rd-candidate-reporter`。

---

## 3. Codex 兼容的硬约束

1. **双清单**：本插件自己的两份（`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`）
   版本号必须与 `pyproject.toml` 一致，由 `scripts/release.py` 一次写两处；
   cc-market 的两份 marketplace 清单按路径引用本插件，不带版本号。CI 断言全部一致。
2. **`${CLAUDE_PLUGIN_ROOT}` 原样使用**（实测 Codex 同样注入），playbook 里不做 host 分支。
3. **playbook host 中立**：host 差异只集中在 `skills/_shared/host-adapters.md` 一处
   （沿用 lit-review 现有的 Claude/Codex Fabric 映射写法），其余剧本引用它。
4. **hooks 不是唯一防线**：Codex 侧未必支持 Claude hook，因此稿件保密**必须落在 CLI 内部**——
   工具从不向 stdout 吐稿件原文，只吐 `sanitized.json`。Claude hook 是第二道锁。
5. **不引入 Node 专有能力**：cc-market 的 `shared/*.mjs` 模式不照搬；共享逻辑在 Python 库里，
   两个 host 都只是调 CLI。`scripts/release` 用 Python 写，不复制 `gen-codex.mjs`
   （那是 N 插件市场的生成器，我们是单插件，需求只有版本号同步，20 行足够；
   跨仓复制 213 行构建脚本才是真正的重复维护）。

---

## 4. 现有代码处置（彻底梳理）

| 现文件 | 行数 | 处置 | 理由 |
|--------|------|------|------|
| `providers/base.py` | 229 | 重写为 `sources/base.py` | 拆 `PaperSource` / `AuthorSource` 两个能力接口；`acquire()` 移出接口（本就 raise NotImplementedError，职责错位） |
| `providers/{ieee,s2,dblp,arxiv}.py` | 1475 | 迁移 + 去重 | 四份各自的 `_as_text`/`_optional_int`/`_api_get`/错误分类下沉 `core/http.py`，预计瘦身 25–30% |
| — | — | **新增** `sources/openalex.py` | 本次验证后升为**作者维度主源**：机构+ROR+country_code+年份序列、keywords、topics、referenced_works |
| — | — | **新增** `sources/orcid.py` | 教育/任职轨迹（best-effort，实测填写率 30%/38%） |
| `models.py` | 372 | 重写 | 现在混了检索候选与工作区状态；拆为 `core/models.py` 与各子域 dataclass |
| `pipeline/orchestrator.py` | 772 | **解散（不是删除）** | 实测它是 cli 分发的 7 个 `run_*` 宏命令层。逐个搬进 `litreview/{search,acquire,ingest,read,synthesize,export,stats}.py`；`_bibtex_*` 系列进 `litreview/export/bibtex.py`。文件消失，功能不丢 |
| `pipeline/repair.py` | 374 | **迁移并修缺陷** | 实测是活命令（`cli.py:643`）。迁为 `academia repair`，同时修 SR-20260730-005（`--dry-run` 是空壳）与 SR-20260730-008（修复出的 canonical 目录不完整，反而挡住后续 ingest） |
| `pipeline/ingest.py` 的 `compat_map` 分支 | ~20 | **删除** | 它只为兼容旧 title-based 目录而存在；本次不要向后兼容，新数据布局一次到位 |
| `pipeline/search.py` | 494 | 拆分 | 检索循环 → `litreview/search.py`；`normalize_doi`/`normalize_title`/去重合并 → `core/text.py`（reviewer 也用） |
| `pipeline/query.py` + `search/query.py` | 363 | **合并为一个** | 职责重叠的历史包袱 |
| `pipeline/acquire.py` + `acquire/*` | 1712 | 迁移，接口收敛 | oa_resolve → transport → verify → ledger 这条链设计是对的；`types.py` 合入 `core/models.py` |
| `pipeline/ingest.py` (259) + manuscript-review `scripts/ingest.py` (137) | 396 | **合并为 `ingest/` 唯一实现** | 三个工作流共用 |
| `review/{screen,reader,extract,synthesis}.py` | 429 | 迁到 `litreview/` | |
| `export/zotero*.py` | 1749 | 合并为 `litreview/zotero/` 子包 | 三文件重复度高；对外只留 import/maintain/sync/status |
| `export/{render,plot}.py` + `pipeline/brief.py` | 321 | 迁移 | plot 进 `[plot]` extra |
| `ai/client.py` | 283 | 迁到 `core/ai.py` | reviewer 也要用 |
| `utils/*` | ~350 | 迁到 `core/` | `common.py` 按功能拆散，不留 misc 抽屉 |
| `cli.py` | 713 | 重写为 `cli/` 包 | 每命令一个模块；统一 `--json`；顺带清 SR-013 |
| `tests/*` 19 个 | — | 随模块迁移并重写 | 网络相关改录制 fixture；补 store / reviewer 测试；补 SR-007（import-screening `out_dir` 契约无测试） |
| `scripts/zotero-mcp-launcher.py` | — | 迁移为 console script | `.mcp.json` 只写命令名，不写路径 |
| manuscript-review `scripts/validate_workflow_output.py` | — | 迁为 `academia validate-workflow` | |
| 三个项目的 `.claude/{skills,agents,commands}` | — | 迁入插件 | 本仓库不再持有 |
| `lenses/*.toml`、skill `templates/*.md` | — | 默认值进插件 `configs/`；本仓库留个人 override | 覆盖关系，非归属关系 |

**净预期**：10.5k 行 → 7–8k 行，另加 store + reviewer 约 2.5k 行新代码。

---

## 5. 数据源分工（实测后定稿）

| 需要什么 | 主源 | 备源 | 备注 |
|----------|------|------|------|
| 论文检索（IEEE 系期刊） | IEEE `/rest/search` | OpenAlex works | IEEE 相关性最好但字段最少 |
| 论文检索（跨库） | OpenAlex works | S2 / DBLP / arXiv | OpenAlex 有 `referenced_works` |
| 摘要 | IEEE / S2 | OpenAlex `abstract_inverted_index` | 需反转还原 |
| 受控词 / 关键词 | OpenAlex `keywords`(带 score) + `topics` | 摘要抽词 | **IEEE 检索响应不含 index terms** |
| 作者持久 ID | ORCID（域内覆盖 89%） | OpenAlex ID → IEEE author id → S2 ID | IEEE 白送 author id |
| 作者位次 | OpenAlex authorships **数组下标** | IEEE authors 顺序 | OpenAlex 只标 first/middle/last，通讯作者字段实测为空 |
| 当前机构 + 国别 | OpenAlex `last_known_institutions`(ROR + country_code) | 论文署名 | |
| 历任机构轨迹 | OpenAlex `affiliations[].years` | ORCID employments | |
| 教育轨迹 | ORCID educations（30%） | 机构主页抓取（与邮箱同一次请求） | best-effort |
| 合著关系 | OpenAlex works → authorships | IEEE / S2 | 建 `coauthor_edges` |
| 引文关系 | OpenAlex `referenced_works` | — | 用于「候选人是否被本稿大量引用」 |
| 公开邮箱 | 已发表通讯邮箱 → 机构主页 → 实验室主页 → 公开 ORCID | — | 禁止模式生成 |

**S2 降级说明**：author 端点免 key 实测立即 429，因此 S2 只在 `S2_API_KEY` 存在时启用，
且永不作为唯一来源。

---

## 6. 累积数据库

**SQLite + FTS5**，单文件，`ACADEMIA_DB` 指定，默认
`Documents/PEMC/cc-academia-data/academia.db`。**绝不放 OneDrive**——同步会损坏数据库。
FTS5 自带 BM25，第一版不需要向量库；embedding 作为可选增强存 BLOB，用 numpy 暴力算。
到十万级再考虑 sqlite-vec 或 Postgres——届时只换 `store/` 一层。

```sql
papers(paper_id PK, doi, title, abstract, year, venue, venue_type,
       citation_count, source, source_id, url, first_seen, last_seen)
papers_fts                                  -- FTS5(title, abstract)
paper_terms(paper_id, term, kind, score)    -- openalex keywords / topics / IEEE terms
paper_refs(paper_id, referenced_paper_id)   -- 来自 OpenAlex referenced_works
paper_embeddings(paper_id PK, model, vec BLOB)

persons(person_id PK, display_name, orcid, openalex_id, ieee_author_id, s2_id,
        confidence, resolution_method, first_seen, last_seen)
person_names(person_id, name_variant)       -- 含 OpenAlex display_name_alternatives
authorships(paper_id, person_id, idx, position, is_corresponding, position_weight)

institutions(inst_id PK, name, ror_id, country_code, city, type)
affiliations(person_id, inst_id, department, role, year_from, year_to, is_current, source, source_url)
education(person_id, inst_id, degree, field, year_from, year_to,
          advisor_person_id, source, source_url)
coauthor_edges(a_person_id, b_person_id, paper_count, first_year, last_year)

manuscripts(ms_id PK, journal, title_hash, origin_countries, created_at)
manuscript_authors(ms_id, person_id, name, affiliation, country)
runs(run_id PK, ms_id, created_at, config_hash)
candidate_scores(run_id, person_id, score, components_json)
coi_evidence(run_id, person_id, rule, status, evidence_json, checked_at)
emails(person_id, email, source, source_url, confidence, verified_at)
review_history(person_id, ms_id, invited_at, responded, accepted, quality_note)
```

- **只增不改**：`papers`/`persons`/`authorships` upsert，`runs`/`candidate_scores`/`coi_evidence` 追加。
  跑得越多人物图越完整，后续 run 越快。
- **IEEE 只做 query-time 检索**，落库只存标识符与派生结果，不做全库缓存，遵守 API 条款。
  OpenAlex 是 CC0，可自由缓存——这也是把它设为主源的额外理由。
- `review_history` 是本地库相对一次性检索的最大增量：第二篇稿件起就能避开「刚请过」「从不回复」。
- **隐私**：`manuscripts` 只存 `title_hash` 与国别，**不存标题与摘要原文**；稿件内容只留工作区。

---

## 7. 候选人背景（替代族裔推断）

**不做姓名→族裔推断。** 姓名推断准确率低，且把「回避机构/地域利益关系」替换成对审稿人的族裔画像，
与 IEEE 同行评议公平性要求冲突、事后难以解释。真正需要的信号由三样东西更准地给出：
current affiliation country、教育与任职轨迹、合著图。

| 字段 | 主来源 | 备用 | 实测覆盖 |
|------|--------|------|----------|
| 当前机构 + 国别 | OpenAlex `last_known_institutions` | 最近一年论文署名 | 高 |
| 历任机构 | OpenAlex `affiliations[].years` | ORCID employments (38%) | 高 |
| 本硕博院校 + 学位 + 年份 | ORCID educations (30%) | 机构主页抓取 | 中低 |
| 导师 | 早期合著模式、机构主页 | — | 低，仅有直接文本证据时记录 |

**设计取舍**：因为 ORCID education 只有三成，把「邮箱发现」与「背景补全」**合并为一步 `rev-disc enrich`**
——同一次机构主页抓取同时取邮箱与教育/任职信息。既减少外部请求，又让两类信息**证据同源**
（同一个 `source_url`）。找不到就标 `unknown`，绝不猜测。

**用途**：① COI——同校博士、同一导师、近五年同机构直接进规则引擎，比姓名信号强且可举证；
② 展示——dossier 给出「本科 X → 博士 Y（导师 Z）→ 现任 W」；
③ 资历过滤——博士毕业年份推算 academic age，避免请刚毕业的人审长文。

---

## 8. reviewer 管线

| 步 | 命令 | 产出 | 谁做 |
|----|------|------|------|
| 01 | `rev-disc init <pdf>` / `profile` | `sanitized.json` + `paper_profile.json` | 脚本 ingest；LLM 只读脱敏内容 |
| 02 | `rev-disc search` | 多源检索 → 去重 → 入库 | 纯脚本 |
| 03 | `rev-disc candidates` | 论文 → authorship 反查 → 消歧 | 纯脚本 |
| 04 | `rev-disc enrich` | 机构/国别/教育轨迹/邮箱（一次抓取，同源证据） | 脚本 + 受控抓取 |
| 05 | `rev-disc coi` | 三档裁定 + 逐条证据 | **纯规则引擎，LLM 不参与** |
| 06 | `rev-disc report` | shortlist.md/.csv + 逐人 dossier | 脚本渲染，LLM 只写方向摘要 |

`run_state.json` 记录各步状态，重入按状态续跑（沿用两个既有项目的 resume 表约定）。

### 8.1 算法

**论文相关性**
```
paper_score = 0.30 BM25(title+abstract, FTS5)
            + 0.20 keyword_topic_overlap(OpenAlex keywords·score + topics)
            + 0.10 recency
            + 0.40 embedding_similarity      # 无 key 时该项去除，其余权重归一
```

**作者位次权重**（按 §0.2#7 修正）：由 authorships 数组下标推导，不依赖 host 字段
```
idx==0 (first)              1.0
idx==1 (second)             0.8
last                        0.8
is_corresponding == true    1.0   # 实测常缺失，缺失时不惩罚，退回位次
其他                         0.4
```

**消歧优先级**（实测 ORCID 域内覆盖 89%，第一优先级可用性好）
```
ORCID > OpenAlex ID > IEEE author id > S2 ID > name+affiliation > name+coauthor 图 > name+topic
```
禁止纯姓名匹配（§0.2#6 有实证）。`confidence < 0.6` 在报告中显式标注待人工确认。

**COI 三档**
```yaml
coi:
  coauthor_years: 5
  block:  [manuscript_author, exclusion_list, recent_coauthor,
           same_department, same_phd_institution_and_period, advisor_advisee]
  review: [same_institution, previous_institution_overlap,
           dense_historic_collaboration, heavily_cited_by_manuscript]
  minimum_evidence: 1
```
`BLOCK → score = -inf`，**不是扣分**，COI 不与 expertise 加权混算。

**最终排序**
```
score = 0.40 topic + 0.20 method + 0.15 recent_expertise
      + 0.10 publication_evidence + 0.10 geo_preference + 0.05 reviewer_history
```
优先级恒为 `COI safe > expertise > geo preference`。
地域按 current affiliation country（不推断国籍）；跨区 +0.08，期刊 config 可切 `mode: hard_filter`。
中国籍学者现任 Stanford → 按 US 计。

**措辞**：一律写 **no detected conflict**，不写 no conflict——数据库无法证明私人关系与财务 COI 不存在。

**邮箱**：已发表通讯邮箱 > 机构主页 > 实验室主页 > 公开 ORCID；找不到标 `not_found`；
**禁止**模式生成；ORCID 不当邮箱库（其邮箱默认仅本人可见）。

---

## 9. CLI 命令面

```
academia   doctor · repair · validate-workflow · db {init,stats,vacuum} · release
lit-review init · search · acquire · ingest · read · synthesize · export · stats · login
           zotero-{import,maintain,sync,status}
rev-disc   init · profile · search · candidates · enrich · coi · report
```
全部命令支持 `--json`（机器可读）与人类可读双输出；退出码统一：0 成功 / 2 用法错 / 3 外部源失败。

---

## 10. 保密与合规

- **第一道锁在 CLI 内部**（host 无关）：工具从不输出稿件原文，只输出 `sanitized.json`。
- **第二道锁是 Claude hook**：拦截对 `ongoing/*/0-raw.pdf` 与未脱敏文本的读取。
- 外部检索只发送派生检索式，不发送摘要原文；数据库不存稿件标题与摘要原文。
- 报告每条判断必须有 source/evidence。
- **仓库 public 的额外要求**（相较 private 更严）：
  - `.gitignore` 覆盖 `.venv/`、`*.local.*`、`.env`、`cc-academia-data/`、任何真实候选人数据；
  - 测试 fixture 必须是**公开论文的公开元数据**，不含真实邮箱与私人信息；
  - `configs/journals/*.yaml` 只放公开可查的期刊参数，个人偏好走本仓库 override；
  - 首次 push 前跑 secret 扫描（gitleaks 或等价），CI 常驻同一检查；
  - README 明示数据来源与各自的使用条款（OpenAlex CC0 可缓存；IEEE 仅 query-time）。

---

## 11. 迁移阶段

| Phase | 内容 | 验收 |
|-------|------|------|
| 0 | 在 cc-market 下建目录 + 双 host 清单 + 两份 marketplace 各加一条 + `release` 版本同步 + `src/` 骨架 + CI(ruff+pytest+gitleaks) | 两个 host 都能加载插件；CI 断言清单一致 |
| 1 | `core/` 落地（models/http/text/ai/paths/state/log） | core 单测通过 |
| 2 | `sources/` 迁移去重 + 新增 openalex/orcid + 双能力接口 | 全部 source 用录制 fixture 测试通过 |
| 3 | `store/` schema + repository + 回灌工具 | 现有三个 workspace 的检索结果可入库 |
| 4 | `litreview/` 解散 orchestrator + `ingest/` 合并 + `cli/` 重写 + repair 修缺陷 | 现有 workspace 端到端无功能回归 |
| 5 | skills/agents/commands 迁入、改前缀、按新 CLI 契约改写、抽 `_shared/` | `/cc-academia:literature-review` 与 `:manuscript-review` 全流程无回归（两个 host 各跑一次） |
| 6 | `reviewer/` 全量实现（profile→report）+ 新 skill + 4 个 agent | 一篇真实稿件端到端产出 shortlist |
| 7 | push 到 DawnEver/cc-market；OneDrive 侧清理已迁走的 Python 与 venv/缓存 | ai-agents 只剩数据、override 与非 academia 项目 |

开发期 marketplace 直接指向 `Documents/PEMC/cc-academia` 本地路径，免 push-pull 往返；
稳定后切 GitHub 源并开 autoUpdate。

TDD：每模块先写失败测试。外部 API 一律录制 fixture，测试中不打真实网络。

---

## 12. 风险登记

| 风险 | 影响 | 缓解 |
|------|------|------|
| Phase 4/5 迁移期，现有三个 workspace 的日常工作被打断 | 高 | 旧代码保持可用直到 Phase 5 验收通过再删；两套并存期不超过一个 phase |
| IEEE `/rest/search` 是非公开 REST 端点，可能改版 | 中 | 已有前科（`.xpl-btn-pdf` 选择器漂移）。OpenAlex 作为可完全替代的检索备源；IEEE 失效不阻塞主流程 |
| OpenAlex 作者消歧本身有误（同名合并/拆分） | 中 | ORCID 优先（域内 89%）；`confidence` 显式暴露；报告标注待确认项 |
| 机构主页抓取被封 | 中 | 限速 + 失败即 `not_found`，绝不重试升级；不做规避 |
| public 仓误提交敏感数据 | 高 | gitleaks 常驻 CI + `.gitignore` 白名单式 + fixture 审查 |
| 单插件体积随三工作流增长，加载变慢 | 低 | 渐进披露：SKILL.md 只做地图，剧本按需读 |

---

## 13. 明确不做

Postgres / pgvector / FastAPI / 新增 MCP server（zotero 是既有的）/ Neo4j / LangChain /
ScholarOne 对接 / 邮箱模式猜测 / 全库爬取 / 姓名→族裔推断 /
让 LLM 直接判定 COI 或直接推荐审稿人 / 向后兼容旧 import 路径、旧 CLI 参数、旧目录布局 /
复制 cc-market 的 `gen-codex.mjs` /
git submodule 或符号链接把代码仓挂进 OneDrive（Windows + OneDrive 上不稳，且会同步 `.venv`）。

---

## 14. 迁移后本仓库剩下什么

```
ai-agents/ (OneDrive)
├── ai-post/  cc-docx/  cc-lab/  reply-email/     非 academia 项目，不动
├── literature-review/    workspaces/ 数据 + 个人 lens override + memory
├── manuscript-review/    ongoing/ 数据 + critiques-library/ style/ + memory
├── reviewer-discovery/   ongoing/ 数据 + 期刊偏好 override + Suggestions.md
└── .claude/rules/MEMORY.md
```
三个目录不再有 Python 代码与 `.claude/skills`。

---

## 13. 实施中与计划的偏差

计划是推测，实施是证据。以下每条都是实施过程中发现计划有误或不足而改的。

| 计划怎么写 | 实际怎么做 | 为什么 |
|-----------|-----------|--------|
| 仓库落 `Documents/PEMC/cc-academia`，自成 marketplace | 落 `cc-market/cc-academia/`，用既有 marketplace | 你的原意；且 cc-market 的 `gen-codex.mjs` 与 pre-push 钩子直接接住了新插件，一行没改 |
| `configs/*.yaml` | `configs/*.toml` | stdlib `tomllib` 可读，零依赖，且与既有 lens 格式一致 |
| `pyproject.toml` 版本为准，`release.py` 写四处 | `plugin.json` 为准，pyproject 用 hatch `dynamic` 派生 | cc-market 的 pre-push 钩子会 bump plugin.json；第二个版本源永远慢一拍 |
| `acquire/types.py` 合入 `core/models.py` | 留在 `litreview/acquire/` | 它们是采集域概念（Attempt/Outcome/Source），不是跨工作流实体 |
| `query.py` 与 `search/query.py` 「职责重叠」 | 合并了，但**不是**去重 | 一个管计划审批与评估，一个管布尔表达式构造 —— 互补而非重复 |
| agent 前缀 `lr-` / `mr-` / `rd-` | `literature-*` / `manuscript-*` / `discovery-*` | 既有的 `literature-*` 已唯一且更可读；目标是防撞名，不是特定缩写 |
| 仅迁 openalex/ieee/orcid | 另迁 s2 / arxiv / dblp | 旧测试覆盖它们，且 arXiv 的开放 PDF 链接最可靠 |

### 实跑才暴露的三个缺陷

单元测试全绿之后，用真实 API 端到端跑一遍才发现：

1. **候选人列表未排序** —— `build_candidates` 遍历 dict，导致下游所有 `--limit` 切的是任意子集。
2. **`enrich --limit` 默认 40** —— 机构信息是 COI 规则与地域判定的输入，而最终排名要等 COI 之后才知道；设上限会让榜首候选人**既没有机构、也没经过机构级 COI 筛查**。改为默认全量，且 report 会点名警告。
3. **雇主列显示的是资助方** —— OpenAlex 会把多个机构标 current，取第一个就把"福建省教育厅"放进了编辑当作雇主读的那一列。改为按机构类型优先（大学 > 政府/资助方），同类型下取任职时长最长者。

第 3 条不只是显示问题：机构直接驱动 same_institution / same_department 两条 COI 规则，认错机构等于削弱筛查。

### 计划未预见但必须做的

- **可选 extra 缺失时的行为**：裸 `uv sync` 会让 6 个采集测试无法收集、`lit-review` 直接崩在 import 上。拆出无依赖的 `acquire/options.py`，并用 `collect_ignore` 干净跳过。现在两种配置都绿（250 / 395）。
- **fixture 脱敏**：IEEE 响应里带 `userInfo`（含订阅机构名）。public 仓必须在写入前剥掉。
