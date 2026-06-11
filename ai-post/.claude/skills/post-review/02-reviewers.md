# 02 — Reviewer 配置 & Workflow 路径

## 身份 A — 读者代理人

```json
[
  { "key": "A", "name": "读者代理人 (Claude)", "provider": "claude", "model": "sonnet" },
  { "key": "B", "name": "读者代理人 (DeepSeek)", "provider": "deepseek" }
]
```

## 身份 B — 技术核查员

```json
[
  { "key": "A", "name": "技术核查员 (Claude)", "provider": "claude", "model": "sonnet" },
  { "key": "B", "name": "技术核查员 (DeepSeek)", "provider": "deepseek" }
]
```

> `--full-review`：每个身份追加 `{ "key": "C", "name": "... (Codex)", "provider": "codex" }`
> Twitter/X 跳过身份 B（纯文字平台，无代码需验证），只跑身份 A。

## Sharp-Review Workflow 路径

The workflow script ships with the sharp-review plugin. Resolve at runtime:

1. If `$env:CLAUDE_PLUGIN_ROOT` is set (inside sharp-review's own skill), use `${CLAUDE_PLUGIN_ROOT}/scripts/sharp-review-workflow.js`
2. Otherwise, find the latest installed version under `~/.claude/plugins/cache/cc-market/sharp-review/` and use its `scripts/sharp-review-workflow.js`
