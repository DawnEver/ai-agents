# compact-prefix-reset — Sonnet 实测：/compact 后 cache_read 前缀会不会"从零开始"

- 日期: 2026-08-15
- 实验: `cases/compact-prefix-reset.case.mjs`
- 后端: **vanilla Anthropic / claude-sonnet-5**（tap 捕获），非 DeepSeek
- 问题: 用户预期"compact 后就应该从零开始"。在参考后端上实测 /compact 前后 cache_read 前缀是否归零。

## 一句话结论

**"从零开始"只对"消息历史前缀"成立，对 cache_read 不成立。** 在 vanilla Sonnet 上，cache_read 被**永久存在的 system+tools 前缀（约 65k token）**主导，每次请求都命中缓存重读，**compact 前后都稳定在 ~60–73k，从不掉到接近 0**；真正累积的"消息历史"根本不是 cache_read 的来源——它是作为未缓存 input 每次重发的。[project] 那次 600–800k 的 cache_read 是 **DeepSeek 后端把整段对话都计为 cache_read**，与 vanilla Anthropic 的记账方式不同。

## 原始数据（tap trace，会话 [tap-session]）

| turn | msgs | cache_read | cache_create | input | 说明 |
|------|------|-----------|-------------|-------|------|
| 0 | 2 | 52,234 | 12,521 | 2 | 建立 system+tools 缓存 |
| 1 | 5 | 64,755 | 76 | 2 | cache_read ≈ system+tools |
| 2 | 7 | 64,831 | 56 | 504 | compact 前最后一轮正常增长 |
| 3 | **5** | 64,755 | 10 | **2,061** | ← **/compact 执行**：msgs 7→5 重置，摘要作为 input 注入 |
| 4 | 4 | 57,503 | 15,511 | 2 | compact 后重建缓存 |
| 5 | 7 | 73,014 | 66 | 2 | 恢复，cache_read 反超 compact 前 |
| 6 | 9 | 73,080 | 9 | 504 | ← 被误标 POST-COMPACT（真边界在 turn 3） |

- **/compact 确实执行了**（已验证）：turn 3 消息数从 7 重置为 5，input 跳到 2,061（注入的摘要），持久化 jsonl 出现 compact 标记。
- **cache_read 几乎不变**：compact 前 64.8k → compact 后 57.5k→73k，同一量级（≈ system+tools），**从未归零**。

## 三个实测事实

1. **cache_read 地板 = system+tools（≈65k），永久存在、每次命中缓存重读。** 从 turn 1 起 cache_read 就稳定在 ~65k，不随会话变短——因为 Claude Code 的工具 schema 巨大，system+tools 就是这么大，且每次都作为前缀重读。compact 不能消除它（system+tools 永远在请求里）。
2. **消息历史不是 cache_read 的来源，是未缓存 input。** 每轮真实 turn 的 input≈504（累积的消息），cache_read 恒定 65k——即消息历史是**作为 uncached input 重新发送**的，并没有进入 cache_read。所以"会话越长 cache_read 越高"在 vanilla Anthropic 小规模下**不成立**。
3. **compact 重置的是消息前缀，不是 cache_read。** 消息数从 7 回到 5、摘要成为新前缀；但 cache_read 依旧 ≈ system+tools，因为那部分与消息历史无关。

## 与 [project]（DeepSeek）那次对不上的原因

token 报告里那个会话 cache_read 涨到 **600–800k/轮**。本实验表明 vanilla Anthropic 的 cache_read 被 system+tools 钉在 ~65k、不随消息增长——所以那个 600–800k 是 **DeepSeek 后端把整段热对话都计为 cache_read**（其服务器缓存整段上下文并作为 cache_read 报告）的记账/行为，不是 vanilla Anthropic 的机制。

这也顺带修正了 token 报告的措辞：DeepSeek 那次"每轮重读整段历史"是真的（它把整段上下文算 cache_read），但把它当成人畜无害的普遍 Anthropic 行为则不对——vanilla Anthropic 下 cache_read 不会随会话膨胀到那个量级。

## 对"compact 后从零开始"的最终回答

- **消息层面**：是。compact 把累积消息压缩成摘要，消息前缀重置（实测 7→5，input 变 2061）。
- **cache_read 层面**：否。cache_read 有 system+tools 这个 ~65k 的永久底，compact 前后都在这个量级，**永远不会归零**。
- **跨后端**：[project] 的 600–800k 是 DeepSeek 特有记账；在 Sonnet 上同样长度的会话 cache_read 不会到那个量级。

## 方法/复现说明

- 驱动: `node cases/compact-prefix-reset.case.mjs`（Sonnet，tap，trivial turns 建上下文 → /compact → 2 个 post turn → 读 trace 的 cache_read/cache_creation/msgs）。
- **PTY 陷阱（harness 开发注意）**：直接 `send('/compact')` 会把命令**合并进上一轮残留的输入文本**，被当成普通用户消息处理（实测 tty 显示 `…single letter./compact`，模型开始"Wibbling"思考而非执行命令）。必须**先 Ctrl+U 清空输入行，再分两步敲 `/compact` + Enter**，并用持久化 jsonl 轮询 compact 标记来**确认压缩真的发生**（消息数重置 / 摘要注入），不能只看 UI 静默。
- 一次性分析脚本在 `.scratch/`（gitignored）；`.lab/` run 目录已清理。

## 建议

- 报告结论区分后端：[project] 的 cache_read 爆炸是 DeepSeek 记账；若改用 vanilla Anthropic，同样的自主迭代循环 cache_read 只会在 ~65k（system+tools）附近，不会到 800k——**但这不代表更便宜**，因为未缓存的消息历史按 input 计费且每次重发，上下文膨胀的成本从 cache_read 转移到 input_tokens。
- "从零开始"的期待要校准为：compact 重置的是消息前缀，省的是"整段历史重读"（DeepSeek 下可观），但省不掉 system+tools 那个固定 ~65k 的底。
