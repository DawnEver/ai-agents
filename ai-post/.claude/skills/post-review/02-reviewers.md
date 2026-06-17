# 02 — Reviewer 配置 & Workflow 路径

每个身份的 reviewer 池是 **3 个后端**（Codex / DeepSeek / Opus）。默认用 `pickStrategy: "seed-mod"`，由时间种子**随机抽 1 个**跑——所以每次会审的组合都在变，不再固定 A/B。key 对齐 workflow 引擎的路由（A→codex、B→deepseek、C→opus）。

## 身份 A — 读者代理人

```json
[
  { "key": "A", "name": "读者代理人 (Codex)", "provider": "codex" },
  { "key": "B", "name": "读者代理人 (DeepSeek)", "provider": "deepseek" },
  { "key": "C", "name": "读者代理人 (Opus)", "provider": "claude", "model": "opus" }
]
```

## 身份 B — 技术核查员

```json
[
  { "key": "A", "name": "技术核查员 (Codex)", "provider": "codex" },
  { "key": "B", "name": "技术核查员 (DeepSeek)", "provider": "deepseek" },
  { "key": "C", "name": "技术核查员 (Opus)", "provider": "claude", "model": "opus" }
]
```

> 随机：`pickStrategy: "seed-mod"` → 每个身份从上面 3 个后端里随机抽 1 个跑。
> `--full-review`：把 `pickStrategy` 设为 `"all"`，3 个后端全跑（Codex + DeepSeek + Opus）。
> Twitter/X 跳过身份 B（纯文字平台，无代码需验证），只跑身份 A。

## Sharp-Review Workflow 路径

The workflow script ships with the sharp-review plugin. Resolve at runtime:

1. If `$env:CLAUDE_PLUGIN_ROOT` is set (inside sharp-review's own skill), use `${CLAUDE_PLUGIN_ROOT}/scripts/sharp-review-workflow.js`
2. Otherwise, find the latest installed version under `~/.claude/plugins/cache/cc-market/sharp-review/` and use its `scripts/sharp-review-workflow.js`
