# 03 — Phase 1-2: 并行 Workflow 执行 & 结果收集

## Phase 1：并行运行两个 Workflow

对每个目标平台，并行调用 sharp-review workflow 两次（一次 per 身份）。每个 workflow 默认跑 **3 个 reviewer**（Opus + DeepSeek + Codex，见 `02-reviewers.md`），这样 Phase 3 的 `confidence (≥2 reviewers)` 合议才有数据。

> `findingSchema` 与 `reviewers` **不在此内联**——单一真源在别处，下方 `<...>` 占位符指向它们，运行时按引用加载，切勿复制 schema 字面量回此处（避免漂移）：
> - `findingSchema` → `01-identities.md` 的 `### 身份 A finding schema (SSOT)` / `### 身份 B finding schema (SSOT)` 代码块。
> - `reviewers` → `02-reviewers.md` 的 `## 身份 A` / `## 身份 B` reviewer 数组。

**Workflow 调用 — 身份 A（读者代理人）：**

```js
Workflow({
  scriptPath: "<sharp-review-workflow.js>",
  args: {
    date: "<today YYYY-MM-DD>",
    contentType: "content",
    content: "<article full text>",
    reviewScope: "开头钩子吸引度(1-5分), 逐段AI味(🟢人味/🟡轻微AI/🔴明显AI), 微幽默密度与位置, 最无聊段落, 句子节奏, 图片alt text与主题一致性",
    findingSchema: <身份A finding schema — 见 01-identities.md「### 身份 A finding schema (SSOT)」>,
    reviewers: <身份A reviewers — 见 02-reviewers.md>,
    pickStrategy: "all",   // 默认 3 个后端全跑（Opus + DeepSeek + Codex，3 reviewers/identity）；--fast 时只跑前 2 个
    dedupKeyFields: ["location", "dimension"],
    idPrefix: "CR-A"
  }
})
```

**Workflow 调用 — 身份 B（技术核查员）：**

```js
Workflow({
  scriptPath: "<sharp-review-workflow.js>",
  args: {
    date: "<today YYYY-MM-DD>",
    contentType: "content",
    content: "<article full text>\n\n---\n\n## Repo Analysis Reference\n\n<repo-analysis.md content>",
    reviewScope: "代码块语法与可运行性, 安装步骤准确性, 技术术语正确使用, 架构描述与repo-analysis一致性, 性能数据真实性, 依赖包名版本真实性",
    findingSchema: <身份B finding schema — 见 01-identities.md「### 身份 B finding schema (SSOT)」>,
    reviewers: <身份B reviewers — 见 02-reviewers.md>,
    pickStrategy: "all",   // 默认 3 个后端全跑（Opus + DeepSeek + Codex，3 reviewers/identity）；--fast 时只跑前 2 个
    dedupKeyFields: ["location", "dimension"],
    idPrefix: "CR-B"
  }
})
```

> 每个 workflow 内 reviewer agent 并行运行，全部受 JSON Schema 约束。

## Phase 2：收集结果

Each workflow returns:

```json
{
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

If a workflow or individual reviewer fails — log the failure, mark that identity as `⚠️ 未响应`. Don't block the other identity.
