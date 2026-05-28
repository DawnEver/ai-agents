---
name: project-architecture-refactor
description: AI-Post 架构重整计划 — post-new 渐进式披露拆分 + 整体管线层级重构
metadata: 
  node_type: memory
  type: project
  originSessionId: a7702495-e64e-4699-9397-9f381555f652
---

# AI-Post 架构重整

## 背景

2026-05-26 讨论了三项架构问题：

1. **post-new SKILL.md 太长**（~380行），需渐进式披露拆分
2. **post-style 是否在用** — 确认已正确集成（4个writer agents + post-publish + post-regenerate 都读取 style/profile.md）
3. **整体架构** — 5个skill本质是一条管线，但缺少清晰层级

## 已完成的改动

- ✅ 选题（title generation）从 post-publish Step 4.5 移到 post-new Step 5.5 Brief Review Gate
- ✅ Step 5.5 扩展为两阶段门：Phase 1 Angle Confirmation + Phase 2 Title Selection，多轮迭代
- ✅ 新增 Step 8: User Draft Review（强制用户阅读初稿，在三方会审之前）
- ✅ post-new 渐进式披露拆分：SKILL.md → 轻量 orchestrator + 9个子文件 (01-09)
- ✅ CLAUDE.md 架构层级描述：Architecture 段 + Pipeline Flow 段 + progressive disclosure 说明
- ✅ post-style 集成确认：4个writer agents + post-publish + post-regenerate 都读取 style/profile.md

## 当前完整管线流程

```
/post:new <repo>
  → clone + deep explore
  → write repo-analysis.md
  → ⭐ BRIEF REVIEW GATE: 选题确认 (angles + titles, iterate until user approves)
  → write images.md
  → spawn writers in parallel (创意排水 → draft → 三遍审校)
  → ⭐ USER DRAFT REVIEW: mandatory read-through before review
  → 三方会审 (3-model fanout per identity)
  → fix (auto-offer /post:regenerate on ❌)
  → /post:publish
  → /post:style add
```
