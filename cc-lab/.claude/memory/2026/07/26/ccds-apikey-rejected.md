---
created: 2026-07-26
accessed: 2026-07-26
---

# ccds "Invalid API key" 报错 — 本机 key 审批状态被拒

## 症状
`ccds`(deepseek provider)报 API key 错误,但 key 正确、其他电脑同一份
`claude_env_settings.json`(OneDrive 同步)都能用。

## 根因
与 key 内容无关。`~/.claude.json` 的 `customApiKeyResponses.rejected` 里记录了该 key
的**末 20 位** —— 之前某次交互弹窗 "Do you want to use this API key?" 时选了 No,状态被持久化。
交互模式每次校验此列表即报错;其他机器该 key 在 approved(或从未被拒)所以正常。

## 关键诊断事实
- 非交互 `ccds -p "..."` 不走该检查,所以会"时而能用"——用它可区分 key 本身错误 vs 审批状态问题。
- 检查方法(不泄露 key):比较 `claude_env_settings.json` 中 `env:deepseek.ANTHROPIC_API_KEY`
  的 `.slice(-20)` 是否在 `~/.claude.json` 的 rejected/approved 列表中,只打印布尔值。
- approved/rejected 列表存的是 key 末 20 位,不是完整 key。

## 修复
- 办法 A:交互模式弹窗时选 Yes,自动写入 approved。
- 办法 B:编辑 `~/.claude.json`,把该尾号从 `rejected` 移到 `approved`(先备份)。
  本次用 B,备份在 `~/.claude.json.bak-*`。
- 注意:自动模式分类器会拦截"代用户改同意状态"的脚本,需用户明确确认后执行。

## 排查路径(可复用)
1. `which ccds` → `~/.local/bin/ccds` → `~/.claude/scripts/runtime/cc.js`(删 PROVIDER_KEYS 后注入 profile)。
2. 校验 profile 各值长度/首尾空白/换行(不打印内容)。
3. 最小复现:`cd /tmp && ccds -p "say hi"`。
4. 查 `~/.claude/settings.json` 与项目级 settings 的 `env.ANTHROPIC_*` 覆盖。
5. 查 `~/.claude.json` 的 customApiKeyResponses。
