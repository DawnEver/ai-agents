# Universal Writing Craft

Shared writing techniques applied across all platforms. Platform templates reference this file — do NOT copy these rules into individual templates.

---

## Strong Opening

Choose ONE formula — never use "在当今时代/随着XX的发展/越来越多的人/今天来分享一个/最近发现了/相信很多小伙伴":

- **痛点直击**: Describe the exact frustrating scenario the reader is living right now
- **惊人结论/钩子**: Lead with the result, raise a question, make them want to know how. Create suspense.
- **反常识开头**: Challenge common assumptions, force the reader to ask "why?"
- **具体事件开头**: Specific time + specific number + real reaction. Instantly creates authenticity.

Opening checklist: first 3 sentences have specific details? Create at least 1 question/curiosity? First sentence has content (not filler)?

---

## Microhumor

Every 200 characters, at least 1 moment that makes the reader's corner of the mouth twitch upward. Not jokes — subtle real details:

- **Unexpected specifics**: "我试了23次才搞定" not "试了很多次"; "刷新了27次后台" not "很紧张"
- **Self-deprecating honesty**: a small real failure before the win; "至少在我仅有的3次尝试中是这样"
- **Exaggerated-but-true**: "手机震到从桌上掉下来" not "反应很大"
- **Funniest word at sentence end** (Dave Barry technique)

AVOID: forced jokes, emoji stacking, trying-too-hard humor.

---

## 「我」as Subject — Identity Consistency

全文以"我"的视角贯穿。每一段至少有一句以"我"作主语。不是介绍项目——是我在讲我的经历和发现。Write as the project's author/maintainer, not a third-party reviewer.

- ❌ "该项目提供了X" / "工具支持Y" / "用户可以Z" / "本文介绍" / "作者" / "笔者"
- ✅ "我做了X" / "我遇到过这个问题" / "我最开始以为Y，结果Z" / "我在实际项目里用下来..."
- 凡是一整段主语都是"项目/它/该工具/用户"，必须改写成"我"的视角

---

## Concept Handles

Create or use 1-2 concise phrases that capture complex ideas (e.g., "AI味", "创意水龙头"). These become the reader's mental hook. Introduce with a brief explanation the first time, use freely after.

---

## Sentence Rhythm

Short (5-10 chars) + Medium (15-25 chars) + Long (25-35 chars) alternating. Never 3+ consecutive sentences of similar length. Read aloud to test — writing should "sing."

**句首不重复**: Never start 3+ consecutive sentences with the same word or structure. Mix: 主语开头 / 状语开头 / 连词开头 / 短句.

**段落拆分节奏**: 有力的短句独立成段，不要粘在前一段末尾。
- ❌ ...都得交一笔复制粘贴税。这笔税，我交了一年多。
- ✅ ...都得交一笔**复制粘贴税**——丢掉上下文，丢掉手头的文件状态，丢掉正在进行的任务。\n\n这笔税，我交了半年多。

---

## Connectives & Transitions

AI writing treats each sentence as a standalone fact. Human writing stitches sentences together.

### Sentence-Level Connectives

- 转折: 不过、但、然而、只是、话虽如此
- 递进: 而且、另外、更重要的是、加上、更爽的是、还有个细节
- 因果: 所以、因此、正是因为、这才导致、这也导致了
- 举例: 比如、比方说、具体来说、以X为例
- 解释: 也就是说、换句话说、说白了
- 让步: 当然、确实、倒是、不可否认

### Paragraph Transitions

First sentence of each new paragraph should connect back:
- ❌ 每段开头都是主语+动词: "X功能可以..." / "Y组件负责..." / "Z场景下..."
- ✅ "这就引出了另一个问题：..." / "但真正麻烦的地方在这里..." / "光靠这个还不够，更关键的是..." / "用下来，最意外的其实是..."

### 动机段衔接 (Critical Rule)

当描述完工作流紧接着引出痛点时，必须用桥接词，不能裸跳：
- ❌ ...DeepSeek 拿来实现，再让 Codex 来锐评。\n\n另一个卡点是 Chrome MCP...
- ✅ ...DeepSeek 拿来实现，再让 Codex 来锐评。但这个工作流有个绕不开的坎：Chrome MCP...
- 桥接词库: "但问题是" / "不过有个坎" / "这就碰到" / "麻烦的是" / "但这个分工还有个前提" / "问题出在" / "这就碰到一个硬限制"

### 场景链式衔接

多个使用场景之间必须用过渡词串联，不能裸跳：
- ❌ Claude 做完 plan，把实现甩给 DeepSeek。\n\nPR 写完了，让它过一遍安全问题和逻辑 bug。
- ✅ ...所以一个很爽的工作流就是，让 Claude 做完 plan，然后把具体实现甩给 DeepSeek。\n\n又比如 PR 写完了，再让它过一遍安全问题和逻辑 bug。
- 链式词库: "所以一个很爽的工作流就是" / "又比如" / "再比如" / "更让我上头的是" / "还有一个场景" / "还有个工程细节"

### 段落首句回扣

新段落的开头必须与上一段有语义连接，不能凭空另起：
- ❌ ## 它到底是什么\n\ntakeover 是一个 Claude Code 插件...
- ✅ ## 所以我写了 takeover\n\n所以我写了 takeover 这个插件，核心三个命令...
- 回扣模式: "所以" / "这就引出了" / "但真正麻烦的是" / "用了之后我发现" / "相比之下"

---

## Dopamine Density

Every paragraph needs at least 1 "interesting" moment: unexpected insight, vivid example, precise metaphor, real detail, or microhumor. 3 consecutive paragraphs with nothing interesting = danger zone, inject content.

---

## Anti-AI Check

Before finalizing, read every sentence aloud. Grade each paragraph: 🟢 human / 🟡 slightly AI / 🔴 obvious AI (must rewrite 🔴).

### Banned Phrases (delete on sight)

| Category | Phrases |
|----------|---------|
| Meta-announcement | 这篇文章、本文将、总结一下、总的来说、值得注意的是、综上所述、通过对比可以发现、通过以上分析、需要强调的是、需要承认的是 |
| Filler adjectives | 显著提升、充分利用、进行操作、相关功能、有效提升 |
| Hype words | 惊艳、震撼、逆天、神器、revolutionary、game-changing、blazingly fast |
| AI sentence patterns | "不是A而是B" 重复出现、"不仅…还…" 堆砌、三段对称结构过于工整 |
| Vague quantifiers | "大幅提升" → specific number or "我没有测试，但官方声称..." |
| Formal written style | "通过XX方式进行XX" → 直接说怎么做、"可能会" → "我觉得" |
| Banned section headers | 项目概览、问题背景、上手体验、适用场景与局限、总结 |

### Replacement Table

| Vague/Formal | → Natural |
|---|---|
| 显著提升 | 具体数字 |
| 充分利用 | 用好 |
| 进行操作 | 直接动词 |
| 有效提升 | 具体效果 |
| 解决的是一个边界很清晰的问题 | 具体说什么问题 |

---

## Paragraph Mini-Thesis

Every paragraph should have a clear core point expressible in one sentence. If you can't, the paragraph needs to be split or rewritten. String all mini-theses together — they should form the article's logical spine.

---

## 3-Pass Review

**Pass 1 — Content**: Facts accurate? Logic clear? Each paragraph has a mini-thesis? Structure complete?

**Pass 2 — Style (降AI味)**: Delete all banned phrases. Simplify written-formal words. Add personal voice (明确观点 instead of "可能会"). Mark AI density: 🟢Low/🟡Medium/🔴High — rewrite 🔴 paragraphs.

**Pass 3 — Detail**: Mark sentence lengths, find monotone regions, break with short/long sentences. Check paragraph length (3-5 lines on mobile). Read the whole article aloud.
