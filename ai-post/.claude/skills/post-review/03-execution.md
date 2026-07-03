# 03 — Phase 1-2: 并行 fan-out 执行 & 结果收集

## Phase 1：每个身份并行 fan-out reviewers

对每个目标平台，对**两个身份各跑一组 reviewers**。每个身份默认跑 **3 个 reviewer**（Opus + DeepSeek + Codex，见 `02-reviewers.md`），这样 Phase 3 的 `confidence (≥2 reviewers)` 合议才有数据。

Fan out 用 takeover MCP 工具 `mcp__plugin_takeover_takeover__call_model` —— 直接调各 provider API，逐个调用身份的每个 active reviewer（默认全 3 个；`--fast` → 前 2 个）。

> `findingSchema`、persona、`reviewers` **不在此内联**——单一真源在别处，下方 `<...>` 占位符指向它们，运行时按引用加载，切勿复制字面量回此处（避免漂移）：
> - persona + `findingSchema` → `01-identities.md` 的身份 A / B 段落与 `### 身份 X finding schema (SSOT)` 代码块。
> - `reviewers` 数组 → `02-reviewers.md` 的 `## 身份 A` / `## 身份 B`。

**每个 reviewer 调用**（`provider`/`model` 取自该身份 reviewers 数组的对应项）：

```
mcp__plugin_takeover_takeover__call_model({
  provider: "<reviewer.provider>",     // claude | deepseek | codex
  model: "<reviewer.model 或省略>",     // 仅 Opus 传 model="opus"
  mode: "task",                         // 内容审查，非 code-review endpoint
  systemPrompt: "<该身份 persona — 见 01-identities.md>",
  userPrompt: `
<reviewScope，见下>

审阅下面的文章。只返回一个 JSON 对象：{ "findings": [...] }
每条 finding 必须匹配该 schema（required 字段必填）：
<该身份 finding schema — 见 01-identities.md「### 身份 X finding schema (SSOT)」>

文章正文：
<article full text>
`
})
```

- **身份 A（读者代理人）** reviewScope：`开头钩子吸引度(1-5分), 逐段AI味(🟢人味/🟡轻微AI/🔴明显AI), 微幽默密度与位置, 最无聊段落, 句子节奏, 图片alt text与主题一致性`
- **身份 B（技术核查员）** reviewScope：`代码块语法与可运行性, 安装步骤准确性, 技术术语正确使用, 架构描述与repo-analysis一致性, 性能数据真实性, 依赖包名版本真实性`；其 `userPrompt` 的文章正文后追加 `\n\n---\n\n## Repo Analysis Reference\n\n<repo-analysis.md content>`。

从每个 reviewer 的响应中提取 `{ "findings": [...] }` JSON。某 reviewer 调用失败或无有效 JSON → 该槽位记为 `null`。

## Phase 2：合并（merge-findings 引擎）& 收集结果

收集完一个身份的所有 reviewer 原始结果后，组装 `raw.json`（`rawResults[i]` 与 `active[i]` 位置对齐，失败槽为 `null`）：

```json
{
  "reviewers": <该身份完整 reviewers 数组 — 见 02-reviewers.md>,
  "active":    <实际跑的 reviewers（all=全部；--fast=前2个）>,
  "idPrefix": "CR-A",                       // 身份 B 用 "CR-B"
  "dedupKeyFields": ["location", "dimension"],
  "profileLabel": "读者代理人",              // 身份 B 用 "技术核查员"
  "rawResults": [ <reviewer A findings 或 null>, <reviewer B …>, <reviewer C …> ]
}
```

用 Write 工具把 `raw.json` 写到临时文件（Windows 上勿用 Bash 重定向），然后调 sharp-review 的 `merge-findings.js`（路径解析见 `02-reviewers.md`）合并 —— 它复用 sharp-review 的 dedup/confidence 引擎，但**不写任何 memory**，把结果打到 stdout：

```powershell
node "<merge-findings.js>" --raw "<raw.json>" --date "<today YYYY-MM-DD>"
```

stdout 是一个 JSON：

```json
{
  "reviewFile": ".claude/memory/2026/06/10/sharp-review.md",
  "markdown": "## Review … ",
  "merged": [
    {
      "id": "CR-A-20260610-001",
      "location": "开头",
      "dimension": "hook",
      "rating": "2/5",
      "issue": "第1句是套话",
      "suggestion": "换具体事件开头",
      "confidence": "high-confidence (≥2 reviewers)"
    }
  ],
  "summary": "5 issues (3 high-confidence) → .claude/memory/..."
}
```

post-review 只消费 `merged` 与 `summary`（`reviewFile`/`markdown` 是 code-review 的产物，内容审查忽略）。`merged` 保留每条 finding 自己的字段（`location`/`dimension`/`rating`/`issue`/`suggestion`/`correction`），并附 `id` + `confidence`。

某 reviewer 失败 → 该槽 `null`，merge 照常进行；整个身份所有 reviewer 都失败或 merge 报错 → 标该身份 `⚠️ 未响应`，不阻塞另一身份。
