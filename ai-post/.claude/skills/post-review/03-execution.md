# 03 — Phase 1-2: 并行 Workflow 执行 & 结果收集

## Phase 1：并行运行两个 Workflow

对每个目标平台，并行调用 sharp-review workflow 两次（一次 per 身份）。

**Workflow 调用 — 身份 A（读者代理人）：**

```js
Workflow({
  scriptPath: "<sharp-review-workflow.js>",
  args: {
    date: "<today YYYY-MM-DD>",
    contentType: "content",
    content: "<article full text>",
    reviewScope: "开头钩子吸引度(1-5分), 逐段AI味(🟢人味/🟡轻微AI/🔴明显AI), 微幽默密度与位置, 最无聊段落, 句子节奏, 图片alt text与主题一致性",
    findingSchema: <身份A finding schema>,
    reviewers: <身份A reviewers>,
    pickStrategy: "all",
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
    findingSchema: <身份B finding schema>,
    reviewers: <身份B reviewers>,
    pickStrategy: "all",
    dedupKeyFields: ["location", "dimension"],
    idPrefix: "CR-B"
  }
})
```

> 每个 workflow 内 2 个 reviewer agent 并行运行，全部受 JSON Schema 约束。

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
