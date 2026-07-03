# 06 — Phase 7: 持久化裁决 + 修复文件

将本轮三方会审的完整结果写入版本文件夹，使裁决可跨会话追溯、支持多轮复审。

## Pre-Persist Gate

Before writing any files, confirm all prior phases completed:

- [ ] Phase 1-2: All identity fan-outs completed and results collected
- [ ] Phase 3-5: Cross-identity synthesis + per-platform verdicts finalized
- [ ] Phase 6: Image review completed — `images.md` checked per `05-images.md` checklist, findings noted

If Phase 6 was skipped, return to `05-images.md` now. Do NOT write v<N+1> files until all three boxes are checked.

## 修复后的文章文件

对每个产生了 high-confidence fix 的平台，将修复后的全文写入 `2-draft/v<N+1>/<platform>.md`。未修改的平台不写（从更早版本继承）。

## 修复后的图片清单

始终将图片审查结果写入 `2-draft/v<N+1>/images.md`（从最新版本的 images.md 继承并更新）。即使图片审查无任何修改，也要 copy forward——`images.md` 跟着版本链走，不只在 v1。

## 裁决文件

写入 `2-draft/v<N+1>/review-verdict.md`，包含：

```markdown
# 三方会审裁决 — <slug> — Round <N>

**日期**: <YYYY-MM-DD>
**版本**: v<N+1> (审 v<N>)
**模式**: <default (Opus+DeepSeek+Codex) | --fast (Opus+DeepSeek)>

## 综合裁决

| 平台    | A读者 | B技术 | 综合  | 分歧数 |
|---------|-------|-------|-------|--------|
| 小红书  |  ❌   |  ✅   |  ❌   |   1    |
| 微信    |  ⚠️  |  ✅   |  ⚠️   |   2    |
| 知乎    |  ✅   |  ⚠️  |  ⚠️   |   0    |
| Twitter |  ✅   |  —    |  ✅   |   0    |

## 各平台详情

### 知乎 — ⚠️ 有条件通过

**身份A 读者代理人 — ⚠️**
- 🔴 必须修改：<high-confidence findings>
- 🟡 建议修改：<single-reviewer findings>
- 🔀 模型分歧：<disagreements>

**身份B 技术核查员 — ✅**
- 🟡 建议修改：<single-reviewer findings>

**修复清单**（已写入 v<N+1>/zhihu.md）：
- [x] 开头 hook 改具体事件
- [x] 第3段去套话

### 微信公众号 — ...

## 建议操作
- 知乎：确认技术问题后 `/post-publish zhihu <slug>`
- 微信：手动处理分歧后 `/post-publish wechat <slug>`
- 小红书：手动重写后重新 `/post-review <slug> xiaohongshu`
- Twitter：`/post-publish twitter <slug>`
```

## 命名规则

每次都写入当前 round 的版本文件夹。多轮复审时，v3/、v4/、v5/ 各自包含自己的 `review-verdict.md`，形成完整的审核链路。

## 状态判断

此后任何工具/skill 通过检查最新版本的 `review-verdict.md` 是否存在 + 其综合裁决列即可判断三方会审是否通过，无需依赖会话上下文。
