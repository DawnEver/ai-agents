---
name: project-architecture-refactor
description: AI-Post 架构重整 — 渐进式披露拆分 → 消除跨文件重复 → 共享引用文件体系
metadata:
  type: project
---

# AI-Post 架构重整

## 2026-05-26 — 渐进式披露拆分

- post-new SKILL.md 从 ~380 行拆分为轻量 orchestrator + 10 个子文件 (01-10)
- 选题确认从 post-publish 移到 post-new Step 5 (Brief Review Gate)
- Step 8 User Draft Review（强制阅读初稿，三方会审之前）
- 确认 post-style 集成：4 个 writer agents + post-publish 都读取 style/profile.md

## 2026-06-11 — 消除跨文件重复（去臃肿）

**问题**：31 个 markdown 文件 ~3500 行，大量重复——封面比例 8 处、平台列表 6 处、降 AI 味技巧 4 份 ~223 行重复、agent 工作流 4 份重复。

**方案**：提取 3 个共享引用文件作为单一真相源，所有引用方瘦身指向它们。

**新增共享文件**：
- `templates/_writing-craft.md` (90L) — 通用写作技艺，从 4 模板提取合并
- `templates/_platform-registry.md` (29L) — 平台元数据注册表（比例/字数/agent映射/发布URL）
- `.claude/agents/_writer-base.md` (30L) — 共享 writer 工作流

**瘦身效果**：
- 4 模板：196-229 → 116-127 (-40%)
- 4 agents：49-56 → 18-24 (-59%)
- post-publish/SKILL.md：173 → 74 (-57%)
- 审校checklist.md：100 → 51

**新增发布子文件**：`post-publish/_platforms/` 下 4 个平台发布细则 (15-27L each)

**设计约定**：`_` 前缀文件 = 引用文件，不独立调用。所有引用是增量 Read，零破坏性变更。

**Commit**: `f254e62` — 33 files, +593/-582
