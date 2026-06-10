---
name: post-review
description: 三方会审 — each reviewer identity is run independently by Claude Sonnet and DeepSeek via sharp-review workflow engine. Disagreements between models surface genuine issues.
argument-hint: <slug> [platform]
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Agent
  - Skill
  - Workflow
---

# /post-review — 三方会审

## 核心设计

Two independent reviewer identities, each run by 2 models via sharp-review's generalized workflow engine. The engine handles parallel fanout, JSON Schema enforcement, dedup merge, and confidence tagging. post-review handles identity-specific configuration and pipeline integration.

```
身份A 读者代理人:  [Claude Sonnet] [DeepSeek V4 Pro]  → sharp-review workflow → merged findings
身份B 技术核查员:  [Claude Sonnet] [DeepSeek V4 Pro]  → sharp-review workflow → merged findings
                              ↓
                    Cross-identity synthesis
                    (post-review SKILL.md)
```

Two models independently review with the same prompt. **Both agree → confident. They disagree → needs human judgment.**

> **`--full-review` 模式**：追加 Codex reviewer (`{ provider: "codex" }`) 到每个身份的 `reviewers` 数组。

---

## 参数解析

- `<slug>` — 文章目录名，对应 `ongoing/<slug>/`
- `[platform]` — 可选，指定单一平台；不填则审所有已生成平台

Walk `ongoing/<slug>/2-draft/` to find the latest version number (highest N). For each platform, walk back through versions to find the latest copy. Also check for `images.md` in the version chain.

---

## 审稿身份 & Finding Schema

### 身份 A：读者代理人

```
你是一名对 AI 生成内容极度敏感的挑剔读者。不懂平台规则，只在乎"这篇文章好不好看"。你每天被 AI 内容轰炸，能瞬间识别 AI 腔。

检查项：
- 开头前 3 句：是否抓住你？还是让你想划走？（1-5分）
- 逐段 AI 味打分：🟢 人味 / 🟡 轻微AI / 🔴 明显AI，每段说明原因
  - 🔴 标准：套话堆砌、无个人立场、像新闻稿
  - 🟢 标准：像真实的人在分享经历和观点
- 微幽默：哪里有让你嘴角微扬的细节？哪里完全没有？
- 最无聊的段落是哪段？为什么？
- 句子节奏：默读一遍，是否单调？
- 图片描述（alt text）：是否与文章主题/术语一致？是否过于通用像占位符？
```

**身份 A finding schema:**

```json
{
  "type": "object",
  "properties": {
    "location": { "description": "段落 N / 开头 / 全文 / 图片alt", "type": "string" },
    "dimension": { "description": "Check dimension", "enum": ["hook", "ai_taste", "humor", "rhythm", "boredom", "alt_text"] },
    "rating": { "description": "Rating (1-5 for hook, 🟢🟡🔴 for ai_taste, etc.)", "type": "string" },
    "issue": { "description": "Specific issue found", "type": "string" },
    "suggestion": { "description": "Fix suggestion", "type": "string" }
  },
  "required": ["location", "dimension", "rating", "issue"]
}
```

### 身份 B：技术核查员

```
你是一名软件工程师，专门验证技术内容的准确性。不在乎文章好不好看，只在乎技术对不对。

检查项（对照 repo-analysis.md）：
- 每个代码块：语法正确？能实际运行？
- 安装步骤：命令准确？顺序正确？
- 技术术语：是否被正确使用（无误用/夸大）？
- 架构描述：与 repo-analysis 中实际代码发现一致？
- 性能声明、数据：有无编造或夸大？
- 依赖包名、版本：是否真实存在？
```

**身份 B finding schema:**

```json
{
  "type": "object",
  "properties": {
    "location": { "description": "代码块 #N / 安装步骤 / 术语 / 架构描述 / 数据声明 / 依赖", "type": "string" },
    "dimension": { "description": "Check dimension", "enum": ["syntax", "runnable", "terminology", "architecture", "data_claims", "dependencies"] },
    "rating": { "description": "Accuracy rating", "enum": ["✅", "⚠️", "❌"] },
    "issue": { "description": "Specific issue found", "type": "string" },
    "correction": { "description": "Correct content", "type": "string" }
  },
  "required": ["location", "dimension", "rating", "issue"]
}
```

---

## 审稿 Reviewer 配置

### 身份 A — 读者代理人

```json
[
  { "key": "A", "name": "读者代理人 (Claude)", "provider": "claude", "model": "sonnet" },
  { "key": "B", "name": "读者代理人 (DeepSeek)", "provider": "deepseek" }
]
```

### 身份 B — 技术核查员

```json
[
  { "key": "A", "name": "技术核查员 (Claude)", "provider": "claude", "model": "sonnet" },
  { "key": "B", "name": "技术核查员 (DeepSeek)", "provider": "deepseek" }
]
```

> `--full-review`：每个身份追加 `{ "key": "C", "name": "... (Codex)", "provider": "codex" }`

---

## Sharp-Review Workflow 路径

```
C:\Users\linxu\OneDrive - The University of Nottingham\Sync\claude\cc-market\sharp-review\scripts\sharp-review-workflow.js
```

---

## 执行流程

### Phase 1：并行运行两个 Workflow

对每个目标平台，并行调用 sharp-review workflow 两次（一次 per 身份）：

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

> **Twitter/X 跳过身份 B**（纯文字平台，无代码需验证）。只跑身份 A。每个 workflow 内 2 个 reviewer agent 并行运行，全部受 JSON Schema 约束。

### Phase 2：收集结果

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

### Phase 3：分身份合议

Use the `confidence` field from the workflow output:

```
═══ 身份A 读者代理人 合议 ═══

High-confidence findings (≥2 reviewers):
  [CR-A-001] 开头 — hook: 2/5 — 第1句是套话，换具体事件
  [CR-A-002] 第3段 — ai_taste: 🔴 — 套话堆砌，无个人立场

Single-reviewer findings:
  [CR-A-005] 第5段 — humor: 稀少 — DeepSeek认为微幽默密度不足

身份A 合议判决: ✅ PASS / ⚠️ CONDITIONAL / ❌ FAIL
```

**合议规则**：
- `high-confidence (≥2 reviewers)` → `🔴 必须修改`（阻断发布）
- `single-reviewer` → `🟡 建议修改`（单一模型发现）
- 如果同一 location+dimension 上两个 reviewer 都返回 finding 但 rating 不同 → `🔀 模型分歧`（需人工判断）

### Phase 4：综合裁决

```
╔═══════════════════════════════════════════════════╗
║  🏛️ 三方会审综合裁决 — <platform>                 ║
╠═══════════════════════════════════════════════════╣
║  身份A 读者代理人:  PASS ✅ / FAIL ❌             ║
║  身份B 技术核查员:  PASS ✅ / FAIL ❌             ║
╠═══════════════════════════════════════════════════╣
║  综合裁决:                                        ║
║  ✅ 可发布 — 两身份全部通过                       ║
║  ⚠️ 有条件 — <X身份>发现次要问题，修改后可发      ║
║  ❌ 不可发布 — <X身份>发现严重问题，需重写        ║
╚═══════════════════════════════════════════════════╝

📋 问题汇总（按优先级）

🔴 必须修改（high-confidence，阻断发布）：
  [身份A] 开头 hook 1/5 — 第1句是套话，换具体事件开头

🟡 建议修改（single-reviewer，高置信）：
  [身份B] 代码块#2 pip install 命令可能缺少版本锁定

🔀 模型分歧（需人工判断）：
  [身份A] 第3段 AI味：Claude🟡 / DeepSeek🔴
    → DeepSeek认为明显AI腔，Claude认为尚可，建议你自己判断

🟢 可选优化：
  [身份A] 微幽默密度可再提高
```

**裁决逻辑**：
- `❌ 不可发布`：存在 high-confidence finding with 严重问题（hook ≤2/5、code syntax ❌、data claims ❌）
- `⚠️ 有条件`：存在 high-confidence findings 但可修复，或仅有 single-reviewer findings
- `✅ 可发布`：无 high-confidence findings 且无严重 single-reviewer findings

### Phase 5：全平台总览

```
📊 三方会审总览 — <slug>

| 平台    | A读者 | B技术 | 综合  | 分歧数 |
|---------|-------|-------|-------|--------|
| 小红书  |  ❌   |  —    |  ❌   |   1    |
| 微信    |  ⚠️  |  ✅   |  ⚠️   |   2    |
| 知乎    |  ✅   |  ⚠️  |  ⚠️   |   0    |
| Twitter |  ✅   |  —    |  ✅   |   0    |

建议操作：
- 小红书：`/post-regenerate <slug> xiaohongshu`
- 微信：手动处理分歧后 `/post-publish wechat <slug>`
- 知乎：确认技术问题后 `/post-publish zhihu <slug>`
- Twitter：`/post-publish twitter <slug>`
```

### Phase 6：图片提示词会审（Image Prompt Review）

文章正文审完后，从最新版本的 `images.md`（walk back through versions to find it）做独立审查。

**检查项**：术语一致性 / 残留引用 / 封面标题匹配 / 过时描述 / 比例正确

**输出**：修复后的 `images.md` 写入 `2-draft/v<N+1>/images.md`。如有无法确定的项，标注 `⚠️ 需人工确认`。
