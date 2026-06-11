# 04 — Phase 3-5: 分身份合议 → 综合裁决 → 全平台总览

## Phase 3：分身份合议

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

## Phase 4：综合裁决

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

## Phase 5：全平台总览

```
📊 三方会审总览 — <slug>

| 平台    | A读者 | B技术 | 综合  | 分歧数 |
|---------|-------|-------|-------|--------|
| 小红书  |  ❌   |  —    |  ❌   |   1    |
| 微信    |  ⚠️  |  ✅   |  ⚠️   |   2    |
| 知乎    |  ✅   |  ⚠️  |  ⚠️   |   0    |
| Twitter |  ✅   |  —    |  ✅   |   0    |

建议操作：
- 小红书：手动重写后重新 `/post-review <slug> xiaohongshu`
- 微信：手动处理分歧后 `/post-publish wechat <slug>`
- 知乎：确认技术问题后 `/post-publish zhihu <slug>`
- Twitter：`/post-publish twitter <slug>`
```
