---
platform: zhihu
language: zh
emoji_density: see `templates/_platform-registry.md` (emoji_density) — minimal
---

# 知乎 Article Generation Instructions

## Platform DNA

知乎 is objective, analytical, long-form content. Readers expect intellectual honesty and are skeptical of pure promotion. The best-performing content frames itself as answering a specific question. Readers are technically literate and will call out shallow or biased analysis. You earn credibility by acknowledging trade-offs and comparing honestly.

## Structural Formula

1. **Opening: Direct Answer (1 paragraph)** — Answer the implied question immediately. Don't bury the lede. "推荐一个开源项目：[name]。它能解决 [problem]，相比现有方案 [key differentiator]。"
2. **Context: Why This Matters (1-2 paragraphs)** — Personal experience, not industry report. What changed, why existing solutions started failing you, the specific moment you decided to look for an alternative.
3. **What It Is (1-2 paragraphs)** — What it does, key stats. One paragraph is usually enough. Don't over-explain.
4. **机制拆解 / 技术深挖 (核心章节之一)** — Dig into *how it actually works*, not just what it does. This is co-core with the comparison for 知乎's technical audience. Pick the 1-3 most interesting mechanisms (architecture, key algorithm, clever design trade-off) and walk through the **logic** so the reader understands *why* it works. Ground your own understanding in `repo-exploration.md` / `repo-analysis.md` Standout Details, but **explain in plain terms — do NOT cite source file paths, function names, or line numbers in the article**; readers want the idea, not a code map. A short, self-contained code snippet (a few lines) is welcome when it makes the mechanism concrete. A reader should finish this section able to explain the design to a colleague. Don't hand-wave with feature lists — show the actual mechanism.
5. **Comparative Analysis (核心章节之一)** — The other core section for 知乎. Compare with 2-3 alternatives across relevant dimensions. Use a table format:
   | 维度 | 本项目 | 替代A | 替代B |
   |------|--------|-------|-------|
   | 性能 | ... | ... | ... |
   | 易用性 | ... | ... | ... |
   | 生态 | ... | ... | ... |
   | 适用场景 | ... | ... | ... |
6. **Hands-On Experience (1-2 paragraphs)** — Actually use it and report back. What worked well? What was surprising? Any rough edges? Be honest — acknowledging flaws increases credibility.
7. **适用场景 & 局限性** (Use Cases & Limitations) — Where should you use this? Where SHOULDN'T you? This honesty is what 知乎 readers value most.
8. **Closing** — Brief summary + GitHub link. "如果你也在做 [领域] 相关开发，值得 Star 关注。"

## Voice Rules

- **Objective, measured, professional**: Present facts and analysis, not enthusiasm. Even as the author, be honest about trade-offs.
- Use concrete, personal framing: "在实际使用中我发现..." (In actual use I found...), "用下来感觉..." (After using it...), "有个地方被我踩到了..." (I stepped on a landmine...)
- Avoid hype words entirely: NO "惊艳", "震撼", "逆天", "神器"
- Acknowledge downsides proactively. Readers will comment them anyway — own them first.
- Answer the question "我应该用这个吗？" (Should I use this?) with a nuanced "it depends."
- Assume a technically literate audience. You can use domain terminology without explaining basics.
- **BANNED phrases**: "这篇文章", "本文将", "总的来说", "值得注意的是", "综上所述", "通过对比可以发现", "需要承认的是", "解决的是一个边界很清晰的问题" — write like a developer's firsthand experience, not a literature review.
- **BANNED section headers**: "项目概览", "问题背景", "上手体验", "适用场景与局限", "总结" — these are textbook labels, not how real people title sections. Use conversational alternatives or skip the header.

## Comparative Analysis Rules

- Compare with at least 2 alternatives. Real ones, not strawmen.
- Use specific, verifiable claims. "比 X 快 3 倍" needs a source or benchmark.
- Acknowledge when alternatives are better for certain use cases.
- The comparison table is the anchor — readers often scroll to it first.

## Emoji Rules

- **Density**: canonical level in `templates/_platform-registry.md` (emoji_density: minimal) — craft target 0-3 per article. Minimal to none.
- Use only for technical emphasis or to break up a very long section. Never as bullet markers.
- Preferred: 📊 (for data/comparison), ⚡ (for performance), 🔧 (for configuration)

## Technical Depth

- **Deep**. This is the most technical of all platforms. A dedicated 机制拆解 section (structural formula §4) is co-core with the comparison — not optional flavor.
- Walk through the actual mechanism: architecture, key algorithm, data flow, key design trade-offs. Read `repo-exploration.md` to understand it, then explain the **logic** in plain terms — show how it works, don't just assert that it does. Do NOT pepper the article with source file paths, function names, or line numbers; keep it about the idea.
- Concise code snippets are welcome to illustrate a mechanism, but keep them short and self-contained (focus on analysis, not a tutorial walkthrough of the repo).
- Include architecture observations, performance characteristics, and design trade-offs.
- Mention specific versions, benchmarks, and compatibility notes when relevant.
- Code blocks are fine for illustrating behavior, but the focus is on analysis, not tutorial.
- If the project has academic papers or technical blog posts behind it, reference them.

## Content Constraints

- **Length**: 1500-4000 characters. Can go longer if the analysis warrants it.
- **Comparison table**: Required. This is the signature 知乎 format.
- **Honest limitations**: Must mention at least 1-2 limitations or scenarios where the project isn't the right fit.
- **Links**: GitHub link at the end is fine. Can also link to alternatives for fair comparison.
- **Images**: Reference with `[配图：描述]` placeholders.

## Example Structure

```
[Direct opening: state your conclusion first. No buildup.]

## [Problem/question, phrased conversationally — e.g. "Cmd+I 怎么变成这样了" NOT "问题背景"]

[Context: what changed, why existing solutions fell short. Personal experience, not industry report.]

## [What it is, phrased casually — e.g. "它到底是什么" NOT "项目概览"]

[One paragraph. What it does, key stats, how it works at a high level.]

## [Mechanism deep-dive, phrased as curiosity — e.g. "它到底怎么让几个模型各审各的" NOT "技术实现"]

[Walk through the 1-3 most interesting mechanisms — explain the logic and data flow in plain terms so the reader understands *why* it works; a short code snippet is fine to make it concrete. Do NOT cite source file paths, function names, or line numbers. The reader should finish able to explain the design to a colleague. This is co-core with the comparison below.]

## 横向对比
| 维度 | 本项目 | [Alt A] | [Alt B] |
|------|--------|---------|---------|
| ... | ... | ... | ... |

[1-2 paragraphs analyzing the comparison. Lead with the one thing the reader needs to know to decide.]

## [Usage experience, phrased as a story — e.g. "用了几天，说几个地方" NOT "上手体验"]

[What happened. Be specific. Include surprises, rough edges, things that worked better than expected. Tell it like you'd tell a colleague.]

## [Limitations, direct — e.g. "不适合你的情况" NOT "适用场景与局限"]

[Where it falls short. No hedging. If someone shouldn't use this, say so plainly.]

[Brief closing + repo link. No "总结" section header — just end.]
```

**Section header rule**: Section headers must sound like something the author would actually say. Formal labels like `## 项目概览`, `## 上手体验`, `## 总结` are dead giveaways of AI writing. Use conversational headers: `## 它到底是什么`, `## 用了几天，说几个地方`, or skip the header entirely and just write the next paragraph.

## 避坑指南 (Pitfall Avoidance)

- Don't sound like a promotion. 知乎 readers downvote obvious shilling.
- Don't claim "最好" (best) without qualification. Say "在 X 场景下表现最好."
- Don't ignore the competition. Mentioning alternatives signals you've done your research.
- Don't oversimplify. Technical depth is respected here.

## 封面图 (Cover Image)

知乎文章需要一张封面图，显示在文章顶部和 feed 流中。封面图独立于正文配图，单独生成。

- **Aspect ratio**: see `templates/_platform-registry.md` (16:9 for 知乎).
- **Purpose**: Article header + feed preview. 读者在时间线看到的第一视觉。
- **Style**: Clean academic/professional, project name as focal point, neutral tech aesthetic.
- **Design notes**: 
  - 封面图应包含项目名称（英文）作为视觉主体
  - 避免过于花哨 —— 知乎读者偏好克制、专业的设计
- **Output**: 封面图放在文章最开头，使用 markdown 图片引用：`![封面](../../images/zhihu-cover-vN.png)`（路径取自 `images.md`，终版用真实版本号）

## 正文配图 (Content Images)

**核心原则**：图片路径来自 `ongoing/<slug>/2-draft/v1/images.md`，不要自行发明路径。优先使用项目真实截图，AI 生成图作为补充。

- **Format**: 在文章正文中直接使用 markdown 图片引用：`![中文说明](../../images/<id>-vN.png)`（从 `2-draft/vN/<platform>.md` 的相对路径，路径取自 `images.md`）
- Image paths and counts: see `templates/_platform-registry.md`.
- **Image types for 知乎**:
  1. 对比表格可视化（将 markdown 表格转为视觉图表）
  2. Benchmark / 性能对比图
  3. 架构或工作流程图

Example:
```
![横向对比——三个工具在性能/易用性/生态三个维度的得分对比](../../images/comparison-vN.png)
```

## Writing Quality

`templates/_writing-craft.md` is the SSOT for all universal writing techniques — see its Section Index and load every section (知乎 is a zh platform, so the Connectives & Transitions tables apply). As a long-form platform, run the full 3-Pass Review; 知乎 readers especially value Paragraph Mini-Thesis (logical spine).

This template contains only 知乎-specific rules. Apply BOTH files when generating.

## Generation Checklist

- [ ] 1500-4000 characters
- [ ] 机制拆解 section present (REQUIRED) — ≥1 mechanism explained as logic/data flow (optionally a short code snippet), not a feature list; NO source file paths / function names / line numbers in the article
- [ ] Comparison table with 2+ real alternatives (REQUIRED)
- [ ] Table has meaningful dimensions (not just 2 rows)
- [ ] At least 1-2 limitations or "not suitable for" scenarios acknowledged
- [ ] Paragraph mini-thesis check passed (every paragraph has a core point)
- [ ] Sentence rhythm: no 5+ consecutive long sentences
- [ ] Connectives used: transitions between paragraphs not naked subject-verb starts
- [ ] No 3+ consecutive sentences with same opening structure
- [ ] Objective, measured tone — no hype words (惊艳/震撼/逆天/神器)
- [ ] Specific, verifiable claims (not "fastest ever")
- [ ] 封面图 present: `![封面](../../images/zhihu-cover-vN.png)` at top of article
- [ ] 正文配图 present (2-3 markdown image refs, paths from images.md)
- [ ] 「我」主语覆盖：每段至少一句以"我"作主语，无整段以"项目/它"为主语的段落
- [ ] Writing quality check complete (see `_writing-craft.md`) — no 🔴 paragraphs
- [ ] GitHub link at the end
- [ ] Frame answers a real question/need
