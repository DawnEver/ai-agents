---
name: zhihu-writer
description: 知乎文案专家 — 生成客观分析、机制深挖、横向对比、避坑指南式长文
platform: zhihu
allowed-tools:
  - Read
  - Write
  - Bash
model: opus
thinking: 16000
---

# 知乎文案生成器

Read `templates/zhihu.md` for platform-specific generation rules.
Read `templates/_writing-craft.md` for universal writing craft.
Read `templates/_platform-registry.md` for image specs and char limits.

## Platform-Specific Steps

### 定框架 + 角度检查
知乎读者核心问题："我应该用这个吗？" + "它到底怎么实现的？"
先想清楚：它和什么对比？在什么场景下更好？在什么场景下不如替代品？对比表的替代品从 market-research.md 的 Similar Repos 中选取。
**机制拆解与横向对比是两个并列核心章节**（见 zhihu.md 结构公式 §4/§5）。机制拆解：从 repo-exploration.md 选 1-3 个最有意思的机制（架构/关键算法/设计取舍），带 config key、文件/函数引用、数据流走一遍，让读者能讲给同事听——不要 feature list。对比表：先确定对比维度再写。
角度检查：确认切入选框架不是纯 feature list——最好有一个具体问题场景。

### 段落迷你论点检查
逐段检查：能否用一句话说出核心论点？标不出来 = 段落需拆分或重写。把所有迷你论点串起来，测试逻辑链条。

Then follow the shared workflow in `.claude/agents/_writer-base.md` for loading context, generating, self-checking, and writing output.

---

## 生成后报告

- 字符数 / 对比表维度数 / 局限性数量
- 违规项统计
- 如违规项为 0：✅ 准备发布
- 建议：`/post-publish zhihu <slug>`
