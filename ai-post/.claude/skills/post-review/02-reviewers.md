# 02 — Reviewer 配置 & Workflow 路径

每个身份**默认跑 2 个后端**（Claude Sonnet + DeepSeek）—— 跨模型分歧是三方会审的核心价值，所以默认就要 ≥2 个 reviewer，才能产生 high-confidence (≥2 reviewers) 与模型分歧。`--full-review` 时再加上 Opus 作为第 3 个后端。key 对齐 workflow 引擎的路由。

## 身份 A — 读者代理人（默认 2 个后端）

```json
[
  { "key": "A", "name": "读者代理人 (Claude Sonnet)", "provider": "claude", "model": "sonnet" },
  { "key": "B", "name": "读者代理人 (DeepSeek)", "provider": "deepseek" }
]
```

> `--full-review`：追加第 3 个后端 `{ "key": "C", "name": "读者代理人 (Opus)", "provider": "claude", "model": "opus" }`。

## 身份 B — 技术核查员（默认 2 个后端）

```json
[
  { "key": "A", "name": "技术核查员 (Claude Sonnet)", "provider": "claude", "model": "sonnet" },
  { "key": "B", "name": "技术核查员 (DeepSeek)", "provider": "deepseek" }
]
```

> `--full-review`：追加第 3 个后端 `{ "key": "C", "name": "技术核查员 (Opus)", "provider": "claude", "model": "opus" }`。

> 默认：`pickStrategy: "all"` → 每个身份上面 2 个后端**全部跑**（2 个 reviewer per identity）。
> `--full-review`：reviewer 数组追加 Opus（变 3 个后端），仍用 `pickStrategy: "all"`，3 个全跑。
> Twitter/X 跳过身份 B（纯文字平台，无代码需验证），只跑身份 A。

## Sharp-Review Workflow 路径

The workflow script ships with the sharp-review plugin. Resolve at runtime:

1. If `$env:CLAUDE_PLUGIN_ROOT` is set (inside sharp-review's own skill), use `${CLAUDE_PLUGIN_ROOT}/scripts/sharp-review-workflow.js`
2. Otherwise, find the latest installed version under `~/.claude/plugins/cache/cc-market/sharp-review/` and use its `scripts/sharp-review-workflow.js`
3. If neither path resolves to an existing `sharp-review-workflow.js`, **abort immediately** with an actionable message — `sharp-review plugin not found — install cc-market/sharp-review` — instead of letting the `Workflow()` call fail cryptically on a missing scriptPath.
