---
platform: zhihu
character_limit: 1500-4000
language: zh
emoji_density: minimal
---

# 知乎 Article Generation Instructions

## Platform DNA

知乎 is objective, analytical, long-form content. Readers expect intellectual honesty and are skeptical of pure promotion. The best-performing content frames itself as answering a specific question. Readers are technically literate and will call out shallow or biased analysis. You earn credibility by acknowledging trade-offs and comparing honestly.

## Structural Formula

1. **Opening: Direct Answer (1 paragraph)** — Answer the implied question immediately. Don't bury the lede. "推荐一个开源项目：[name]。它能解决 [problem]，相比现有方案 [key differentiator]。"
2. **Context: Why This Matters (1-2 paragraphs)** — Personal experience, not industry report. What changed, why existing solutions started failing you, the specific moment you decided to look for an alternative.
3. **What It Is (1-2 paragraphs)** — What it does, key stats. One paragraph is usually enough. Don't over-explain.
4. **Comparative Analysis (核心章节)** — This is the most important section for 知乎. Compare with 2-3 alternatives across relevant dimensions. Use a table format:
   | 维度 | 本项目 | 替代A | 替代B |
   |------|--------|-------|-------|
   | 性能 | ... | ... | ... |
   | 易用性 | ... | ... | ... |
   | 生态 | ... | ... | ... |
   | 适用场景 | ... | ... | ... |
5. **Hands-On Experience (1-2 paragraphs)** — Actually use it and report back. What worked well? What was surprising? Any rough edges? Be honest — acknowledging flaws increases credibility.
6. **适用场景 & 局限性** (Use Cases & Limitations) — Where should you use this? Where SHOULDN'T you? This honesty is what 知乎 readers value most.
7. **Closing** — Brief summary + GitHub link. "如果你也在做 [领域] 相关开发，值得 Star 关注。"

## Voice Rules

- **Write as the project's maintainer sharing firsthand experience**: You built or deeply use this tool. Share real insights, not academic observations. Frame as "我做了X，发现Y" not "该项目具有X特性".
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

- **Density**: 0-3 per article. Minimal to none.
- Use only for technical emphasis or to break up a very long section. Never as bullet markers.
- Preferred: 📊 (for data/comparison), ⚡ (for performance), 🔧 (for configuration)

## Technical Depth

- **Deep**. This is the most technical of all platforms.
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

- **Aspect ratio**: `--ar 16:9`
- **Purpose**: Article header + feed preview. 读者在时间线看到的第一视觉。
- **Style**: Clean academic/professional, project name as focal point, neutral tech aesthetic.
- **Design notes**: 
  - 封面图应包含项目名称（英文）作为视觉主体
  - 避免过于花哨 —— 知乎读者偏好克制、专业的设计
- **Output**: 封面图放在文章最开头，使用 markdown 图片引用：`![封面](images/zhihu-cover.png)`

## 正文配图 (Content Images)

**核心原则**：图片路径来自 `articles/<slug>/images.md`，不要自行发明路径。优先使用项目真实截图，AI 生成图作为补充。

- **Format**: 在文章正文中直接使用 markdown 图片引用：`![中文说明](images/<filename>)`
- **Aspect ratio**: `--ar 16:9`
- **Number**: 2-3 张正文配图（知乎读者重视数据可视化）
- **Image types for 知乎**:
  1. 对比表格可视化（将 markdown 表格转为视觉图表）
  2. Benchmark / 性能对比图
  3. 架构或工作流程图

Example:
```
![横向对比——三个工具在性能/易用性/生态三个维度的得分对比](images/comparison.png)
```

## Anti-AI Writing Techniques

### 开门见山 (Lead with the Answer)
First paragraph: directly answer "推荐/不推荐, reason is X." No buildup, no suspense. 知乎 readers have high tolerance for density but zero for burying the lede.

### 具体帧 (First-Person Concrete Frame)
Write from direct experience: "在实际使用中我发现..." not "该项目具有..."  
知乎 readers detect promotional framing immediately and discount the entire article.

### 段落迷你论点 (Paragraph Mini-Thesis)
Every paragraph should have a clear core point expressible in one sentence. If you can't, the paragraph needs to be split or rewritten. String all mini-theses together — they should form the article's logical spine.

### 句子节奏 (Sentence Rhythm)
Even analytical writing needs rhythm. After a long explanatory sentence, drop a short one to let the reader breathe. Avoid 5+ consecutive long sentences — it becomes a wall.

### 降AI味自查 (Anti-AI Check)
- ❌ Delete: 这篇文章 / 本文将 / 总的来说 / 值得注意的是 / 综上所述 / 通过对比可以发现
- ❌ Delete hype: 惊艳 / 震撼 / 逆天 / 神器
- ❌ Replace vague quantifiers with numbers or explicit uncertainty: "大幅提升" → "提升约3倍（benchmark见原文）" or "我没有测试，但官方声称..."
- ✅ Keep: specific versions, concrete limitations, "在X场景下" qualifiers
- Grade each paragraph: 🟢 technical human / 🟡 slightly formulaic / 🔴 obvious AI (must rewrite 🔴)

## Generation Checklist

- [ ] 1500-4000 characters
- [ ] Comparison table with 2+ real alternatives (REQUIRED)
- [ ] Table has meaningful dimensions (not just 2 rows)
- [ ] At least 1-2 limitations or "not suitable for" scenarios acknowledged
- [ ] Paragraph mini-thesis check passed (every paragraph has a core point)
- [ ] Sentence rhythm: no 5+ consecutive long sentences
- [ ] Objective, measured tone — no hype words (惊艳/震撼/逆天/神器)
- [ ] Specific, verifiable claims (not "fastest ever")
- [ ] 封面图 present: `![封面](images/zhihu-cover.png)` at top of article
- [ ] 正文配图 present (2-3 markdown image refs, paths from images.md)
- [ ] Anti-AI check complete — no 🔴 paragraphs
- [ ] GitHub link at the end
- [ ] Frame answers a real question/need
