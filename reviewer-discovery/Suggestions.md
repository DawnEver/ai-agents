可以。你的场景非常适合做成一个 **“Reviewer Candidate Copilot”**，但我不建议把所有逻辑都塞进一个 Claude Code prompt。更稳的设计是：

**Claude Code = 编排/UI；Python 服务 = 检索、实体消歧、COI、打分等确定性逻辑；MCP = 两者之间的工具接口。**

Claude Code 现在原生支持 MCP、subagents、hooks 和细粒度 permissions，很适合这种“多个专业步骤 + 外部 API + 最终人工选择”的工作流。([Claude][1])

### 我最推荐的总体架构

```text
                    ┌─────────────────────┐
                    │     Associate Editor │
                    │     Claude Code      │
                    └──────────┬──────────┘
                               │
                         MCP: reviewer-mcp
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
   Paper Profiler       Candidate Search      Conflict Engine
   论文主题解析           候选专家发现             COI排除
          │                    │                    │
          └──────────────┬─────┴────────────────────┘
                         ▼
                   Candidate Ranker
                         │
                         ▼
                  Contact Enricher
                         │
                         ▼
                  Reviewer Shortlist
```

我会把系统拆成 **7 个 deterministic modules + 4 个 Claude subagents**。

---

## 1. Paper Profiler：先把论文变成“检索画像”

输入最好支持：

```yaml
manuscript:
  title:
  abstract:
  keywords:
  authors:
    - name:
      affiliation:
      country:
      orcid:
  references: []
```

然后输出一个结构化 `paper_profile.json`：

```json
{
  "primary_topics": [
    "wireless federated learning",
    "resource allocation",
    "edge intelligence"
  ],
  "methods": [
    "deep reinforcement learning",
    "non-convex optimization"
  ],
  "application_domains": [
    "6G",
    "mobile edge computing"
  ],
  "ieee_terms": [
    "federated learning",
    "resource management"
  ],
  "search_queries": [
    "\"federated learning\" AND \"resource allocation\"",
    "\"edge intelligence\" AND optimization",
    "\"federated learning\" AND wireless"
  ]
}
```

**这里 LLM 很适合做 semantic understanding，但不要让它直接决定 reviewer。**

IEEE Xplore Metadata API 本身可以检索 abstract、author、affiliation、index terms、IEEE thesaurus terms 等，因此你现有的 IEEE API 很适合作为第一层检索源。([developer.ieee.org][2])

---

## 2. Candidate Search：不要直接“搜索人”，先“搜索论文 → 提取作者”

这是我认为最重要的设计。

不要：

```text
论文 -> LLM："给我推荐10个专家"
```

而是：

```text
论文
 ↓
产生 5~10 个 query
 ↓
搜索 100~300 篇相关已发表论文
 ↓
计算 paper similarity
 ↓
取最相关论文 Top 30~50
 ↓
提取这些论文作者
 ↓
Author Entity Resolution
 ↓
候选 reviewer
```

例如：

```text
submitted manuscript
        ↓
query 1 ──→ IEEE papers ──┐
query 2 ──→ OpenAlex ─────┼→ deduplicate papers
query 3 ──→ S2 ───────────┘
                              ↓
                       top relevant papers
                              ↓
                 first/second/corresponding authors
                              ↓
                       candidate authors
```

你提到“找第一作者、第二作者”，可以保留，但我建议**不要只限第一、第二作者**。

更好的 weighting：

```text
相关论文 first author        +1.0
second author               +0.8
corresponding author        +1.0
last/senior author          +0.8
其他作者                    +0.4
```

因为不同领域作者排序习惯不一样。

Semantic Scholar Academic Graph API 也能直接给 paper → authors、author → papers、references/citations，很适合作 IEEE 数据之外的补充。([api.semanticscholar.org][3])

---

# 3. Author Resolver：这是系统真正困难的地方

比如：

```text
J. Wang
Jian Wang
Jian H. Wang
Wang, Jian
```

必须判断是不是同一个人。

建立自己的：

```python
AuthorIdentity
```

核心字段：

```yaml
author_id: internal UUID

names:
  - Jian Wang
  - J. Wang

orcid:
openalex_id:
semantic_scholar_id:
ieee_author_id:

current_affiliation:
institution:
department:
country:

previous_affiliations: []

research_topics: []

recent_papers: []

public_email:
email_source:
email_verified_at:
```

消歧优先级建议：

```text
ORCID
 >
IEEE/OpenAlex/S2 persistent author ID
 >
name + affiliation
 >
name + coauthor graph
 >
name + topic similarity
```

**绝对不要只用名字 match。**

---

# 4. Conflict Engine：COI 一定独立于 LLM

这部分我会写成纯规则引擎。

Claude 不应该回答：

> “我觉得 Zhang Wei 看起来没有利益冲突。”

而应该返回：

```json
{
  "candidate": "Wei Zhang",
  "coi_status": "BLOCK",
  "reasons": [
    {
      "rule": "recent_coauthor",
      "author": "Submission Author A",
      "paper": "...",
      "year": 2024
    }
  ]
}
```

设计成三档：

```text
BLOCK
REVIEW
CLEAR
```

例如：

```python
BLOCK:
    candidate is manuscript author
    candidate in author-exclusion-list
    recent coauthor
    same current research group
    advisor/student relationship if confirmed

REVIEW:
    same institution
    previous institution overlap
    many historic collaborations
    unusually dense coauthor relationship

CLEAR:
    no detected conflict
```

注意写成：

> **No detected conflict**

而不是：

> **No conflict**

因为数据库不可能证明不存在私人关系、竞争关系、financial COI 等。

IEEE 明确要求实际、潜在和感知的利益冲突都应避免，并列举了频繁合作、advisor/student、同一研究组、直接竞争及财务利益等情况。具体时间窗口则最好作为**期刊级可配置 policy**，不要让模型自行定义。([IEEE Author Center Journals][4])

配置可以是：

```yaml
coi:
  coauthor_years: 5
  same_current_institution: review
  same_department: block
  advisor_advisee: block
  author_exclusion_list: block
  minimum_evidence: 1
```

不同 IEEE Transactions 可以放不同 config。

---

# 5. “国内 / 国外”不要判断国籍，要判断 current affiliation country

你这个需求我建议实现成：

```text
manuscript_origin_country
vs
candidate_current_affiliation_country
```

而不是：

```text
candidate nationality
```

比如中国籍教授现在在 Stanford：

```text
current_affiliation_country = US
```

应该按美国机构计算。

这样既准确，又不会涉及不必要的国籍/族裔推断。

而且我建议做成 **soft preference**：

```yaml
geo_policy:
  mode: prefer_cross_region

  if_manuscript_country: CN
  preferred_reviewer_country:
    not: CN

  bonus: 0.08
```

而不是：

```text
China -> 必须外国 reviewer
Foreign -> 必须中国 reviewer
```

除非你所在 journal 明确要求这样做。

最终顺序应该始终：

```text
COI safe
   >
topic expertise
   >
review quality
   >
geographic preference
```

这样更符合 IEEE 关于公平、减少偏见以及选择独立合格 reviewer 的原则。([IEEE Author Center Journals][4])

---

# 6. Reviewer Ranking：推荐采用“硬过滤 + 可解释打分”

例如：

$$
Score =
0.40 TopicMatch
+0.20 MethodMatch
+0.15 RecentExpertise
+0.10 PublicationEvidence
+0.10 GeographicPreference
+0.05 ReviewerHistory
$$

但：

```text
COI = BLOCK
```

直接：

```text
score = -∞
```

不要：

```text
Expertise 95
COI -20
最终 75
```

因为利益冲突不是普通 ranking feature。

一个候选人的最终解释可以是：

```text
Dr. Jane Smith
University of X, USA

Match score: 91/100
COI: CLEAR

Why:
• 2025 paper on federated learning for wireless networks
• 2024 paper on edge resource allocation
• 8 related papers during 2022–2026
• cosine topic similarity = 0.91
• no detected coauthorship with manuscript authors
• different current institution

Representative papers:
1. ...
2. ...
3. ...
```

这比一个 opaque `91% suitable` 好很多。

---

# 7. Email 模块单独做

不要把：

```text
找到 reviewer
```

和：

```text
猜 reviewer email
```

混成一步。

推荐：

```text
1. published corresponding-author email
2. official university profile
3. official lab homepage
4. public ORCID email
5. other explicitly public professional source
```

输出：

```json
{
  "email": "jane.smith@example.com",
  "source": "university_profile",
  "source_url": "...",
  "confidence": 0.98,
  "verified_at": "2026-08-28"
}
```

我会**禁止默认生成邮箱模式**：

```text
firstname.lastname@example.com
```

这种只能标：

```text
email_guess
```

不能作为正常 reviewer contact。

尤其 ORCID 不能被当成 email database；ORCID 明确说明 email 默认通常只有本人可见，只有研究者主动公开或授权 trusted-party access 的地址才可能由第三方读取。([ORCID][5])

---

# Claude Code 部分，我建议这样搭

目录：

```text
reviewer-copilot/
│
├── CLAUDE.md
├── .mcp.json
│
├── .claude/
│   ├── agents/
│   │   ├── paper-profiler.md
│   │   ├── candidate-researcher.md
│   │   ├── coi-auditor.md
│   │   └── candidate-reporter.md
│   │
│   ├── commands/
│   └── settings.json
│
├── reviewer_mcp/
│   ├── server.py
│   └── tools/
│       ├── ieee.py
│       ├── semantic_scholar.py
│       ├── openalex.py
│       ├── author_resolver.py
│       ├── coi.py
│       ├── email.py
│       └── ranking.py
│
├── app/
│   ├── models/
│   ├── services/
│   ├── policies/
│   └── pipelines/
│
├── configs/
│   ├── journals/
│   │   ├── twc.yaml
│   │   ├── tcom.yaml
│   │   └── jsac.yaml
│   └── coi.yaml
│
├── cache/
└── tests/
```

Claude Code 自己已经支持 custom subagents，而且每个 subagent 有独立 context、工具权限和 MCP server，因此特别适合把 search、COI audit 和 report 分开，避免一个 agent 的搜索结果污染全部上下文。([Claude][6])

---

## MCP tools 我会设计成这些，而不是一个万能 `/search`

```text
profile_manuscript()

search_ieee_papers()
search_related_papers()

get_paper_authors()

resolve_author()

get_author_publications()
get_author_affiliation()

check_coauthorship()
check_institution_overlap()
check_author_exclusions()
run_coi_check()

find_public_professional_email()

rank_candidates()

generate_candidate_report()
```

例如 Claude 调：

```text
search_related_papers(
    query="federated learning wireless resource allocation",
    year_from=2021,
    limit=50
)
```

然后：

```text
resolve_author(
    name="Jian Wang",
    affiliation_hint="University of ...",
    paper_ids=[...]
)
```

再：

```text
run_coi_check(
    manuscript_author_ids=[...],
    candidate_author_id="..."
)
```

整个过程就非常可审计。

---

# Claude subagents，我只建四个

### `paper-profiler`

权限：

```text
只看允许进入 AI 的 title / abstract / sanitized metadata
```

任务：

```text
topic
method
domain
IEEE terms
search queries
```

### `candidate-researcher`

只能调用：

```text
search_publications
resolve_author
get_author_publications
```

**不能调用 email，也不能修改 COI。**

### `coi-auditor`

只能调用：

```text
coauthor graph
affiliation graph
excluded reviewers
policy engine
```

这个 agent 不负责推荐专家。

### `candidate-reporter`

只能拿经过 filter 后的候选人：

```text
candidate → readable table/report
```

这样职责分离会比“一个超强 reviewer agent”可靠很多。

---

# 另外一定加一个 Claude Code Hook

这是我认为你这个项目里最值得做的安全控制。

Claude Code hooks 可以在工具执行前拦截调用，permissions 也可以直接 deny 特定工具或路径。([Claude][7])

例如：

```text
PreToolUse
    ↓
如果 Read manuscript/*.pdf
    ↓
BLOCK
```

或者：

```text
允许：
metadata/sanitized.json

禁止：
submissions/raw/*
submissions/manuscript.pdf
```

也就是：

```text
RAW MANUSCRIPT
      ↓
local trusted preprocessing
      ↓
sanitized metadata
      ↓
Claude
```

**不要依赖 CLAUDE.md 写一句“不要读 manuscript PDF”。要 permission/hook 层真的挡住。**

---

# 数据层我推荐 PostgreSQL + pgvector

不需要一开始就搞 Neo4j。

Schema 可以简单：

```text
papers
authors
paper_authors
affiliations
author_affiliations
coauthor_edges
emails
manuscripts
manuscript_authors
candidate_runs
candidate_scores
coi_evidence
```

其中：

```text
papers.embedding
authors.topic_embedding
```

放 pgvector。

你的 COI coauthor graph 也完全可以 PostgreSQL 查询：

```sql
candidate
JOIN paper_authors
JOIN papers
JOIN paper_authors
author
WHERE year >= current_year - 5
```

等数据真正到百万/千万级关系查询，再考虑 Neo4j。

---

# 检索推荐 Hybrid Search

不要只 embedding。

采用：

```text
BM25 / keyword
       +
vector similarity
       +
IEEE controlled terms
```

例如：

```text
candidate_paper_score =
    0.40 embedding_similarity
  + 0.30 BM25
  + 0.20 IEEE_term_overlap
  + 0.10 recency
```

这样对于：

```text
RIS-assisted ISAC
cell-free massive MIMO
GaN HEMT
PLL phase noise
```

这种非常具体的 IEEE 技术术语，比纯 LLM embedding 稳。

---

# 最终输出我建议就是一张 shortlist

| Rank | Reviewer | Institution | Country | Expertise | Evidence                | COI    | Email    |
| ---- | -------- | ----------- | ------- | --------- | ----------------------- | ------ | -------- |
| 1    | A        | Univ X      | USA     | 94        | 3 highly related papers | Clear* | verified |
| 2    | B        | Univ Y      | UK      | 91        | 5 related papers        | Clear* | verified |
| 3    | C        | Univ Z      | SG      | 88        | 4 related papers        | Review | verified |
| 4    | D        | Univ Q      | CN      | 87        | 6 related papers        | BLOCK  | —        |

点击一个 candidate 再展开：

```text
Candidate: XXX

Institution:
Department:
Country:
Public professional email:

Expertise summary:
...

Top evidence:
[1] paper...
[2] paper...
[3] paper...

COI audit:
✓ no same affiliation detected
✓ no coauthorship in configured window detected
✓ not in author exclusion list
⚠ historic collaboration in 2017

Sources:
IEEE:
ORCID:
University:
Semantic Scholar:
```

重点是**每个判断都有 source/evidence**。

---

## 有一点需要特别处理：IEEE API 的缓存

IEEE Xplore API 当前可以查 Metadata、abstract 等，但其 API terms 对用途、批量保存、索引和 rate limit 有限制，所以我不会设计成：

```text
每天把 IEEE 全库 crawl 到本地
```

而是：

```text
query-time retrieval
→ normalize
→ candidate calculation
→ 保存 internal ID / derived score /必要审计结果
```

具体允许保存哪些原始 IEEE 字段，要以你的 API license 为准。([developer.ieee.org][8])

---

# 如果是我来做，我会选这个技术栈

```text
Language        Python 3.12+
API             FastAPI
Models          Pydantic
DB              PostgreSQL
Vector          pgvector
HTTP            httpx
Retry           tenacity
Workflow        普通 Python pipeline
CLI             Typer

AI interface    Claude Code
Integration     MCP server

Search:
    IEEE Xplore
    Semantic Scholar
    OpenAlex
    ORCID
    institutional websites

Testing:
    pytest
    pytest-recording / mocked API fixtures
```

**暂时不要上 LangChain。**

你的问题本质上不是“agent 很复杂”，而是：

```text
retrieval
entity resolution
graph checks
rules
ranking
provenance
```

这些应该尽可能 deterministic。

以后真的需要长流程 checkpoint/retry，再考虑 Temporal / Prefect / LangGraph。

---

## 最终我推荐的职责边界

```text
                    Claude
                       │
     understanding + orchestration + explanation
                       │
                       ▼
┌─────────────────────────────────────────┐
│              Reviewer MCP               │
├──────────┬───────────┬─────────┬────────┤
│ Search   │ Resolver  │ COI     │ Rank   │
│ API      │ Identity  │ Rules   │ Score  │
└──────────┴───────────┴─────────┴────────┘
                       │
                 deterministic
                       │
                       ▼
                  PostgreSQL
```

一句话概括：

> **不要做一个“AI 帮我猜 reviewer”的系统，而要做一个“学术搜索引擎 + author graph + COI rule engine”，Claude Code 只是自然语言控制器和结果解释器。**

这套架构以后甚至可以很自然地接 ScholarOne/Editorial Manager，而不用重写核心逻辑。

还有一点我会放在第一优先级：**第一版只让 Claude 接触已公开论文和经过批准的 manuscript metadata，不直接把 confidential full text 接进去。** IEEE 的现行政策明确要求未发表稿件保密，而且对把审稿材料送入公共 AI 平台有专门限制。([journals.ieeeauthorcenter.ieee.org][4])

[1]: https://code.claude.com/docs/en/mcp?utm_source=chatgpt.com "Connect Claude Code to tools via MCP - Claude Code Docs"
[2]: https://developer.ieee.org/docs?utm_source=chatgpt.com "Currently Available APIs | IEEE Xplore"
[3]: https://api.semanticscholar.org/api-docs/recom%E2%80%A6?utm_source=chatgpt.com "Semantic Scholar - Academic Graph API"
[4]: https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/?utm_source=chatgpt.com "Submission and Peer Review Policies - IEEE Author Center Journals"
[5]: https://info.orcid.org/documentation/integration-and-api-faq/?utm_source=chatgpt.com "Integration and API FAQ - ORCID"
[6]: https://code.claude.com/docs/en/sub-agents?utm_source=chatgpt.com "Create custom subagents - Claude Code Docs"
[7]: https://code.claude.com/docs/en/hooks?utm_source=chatgpt.com "Hooks reference - Claude Code Docs"
[8]: https://developer.ieee.org/apps/tos?utm_source=chatgpt.com "IEEE Xplore"
