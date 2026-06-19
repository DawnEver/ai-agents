# 02 — Reviewer 配置 & Workflow 路径

每个身份**默认跑 3 个后端**（Opus + DeepSeek + Codex）—— 名副其实的"三方"会审：三个**异构模型**独立审同一份稿，跨模型分歧才是会审的核心价值（≥2 reviewer 命中 = high-confidence，三方都中 = 铁案，只有一方提 = 待人工判断）。这也对齐 sharp-review 引擎自带的默认 reviewer 集（Codex / DeepSeek / Opus）。key 对齐 workflow 引擎的路由。

## 身份 A — 读者代理人（默认 3 个后端）

```json
[
  { "key": "A", "name": "读者代理人 (Opus)", "provider": "claude", "model": "opus" },
  { "key": "B", "name": "读者代理人 (DeepSeek)", "provider": "deepseek" },
  { "key": "C", "name": "读者代理人 (Codex)", "provider": "codex" }
]
```

## 身份 B — 技术核查员（默认 3 个后端）

```json
[
  { "key": "A", "name": "技术核查员 (Opus)", "provider": "claude", "model": "opus" },
  { "key": "B", "name": "技术核查员 (DeepSeek)", "provider": "deepseek" },
  { "key": "C", "name": "技术核查员 (Codex)", "provider": "codex" }
]
```

> 默认：`pickStrategy: "all"` → 每个身份上面 3 个后端**全部跑**（3 个 reviewer per identity）。
> `--fast`：只跑前 2 个后端（Opus + DeepSeek），省一次 Codex 调用，用于快速复审。
> Twitter/X 跳过身份 B（纯文字平台，无代码需验证），只跑身份 A。

## Sharp-Review Workflow 路径

The workflow script ships with the sharp-review plugin. Resolve at runtime:

1. If `$env:CLAUDE_PLUGIN_ROOT` is set (inside sharp-review's own skill), use `${CLAUDE_PLUGIN_ROOT}/scripts/sharp-review-workflow.js`
2. Otherwise, find the latest installed version under `~/.claude/plugins/cache/cc-market/sharp-review/` and use its `scripts/sharp-review-workflow.js`
3. If neither path resolves to an existing `sharp-review-workflow.js`, **abort immediately** with an actionable message — `sharp-review plugin not found — install cc-market/sharp-review` — instead of letting the `Workflow()` call fail cryptically on a missing scriptPath.
