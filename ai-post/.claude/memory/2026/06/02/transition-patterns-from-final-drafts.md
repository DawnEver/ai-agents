---
name: transition-patterns-from-final-drafts
description: Connective/transition patterns extracted from diffing 2-draft vs 3-final edits — systematically missing in generated drafts
metadata:
  type: feedback
---

# Transition Patterns — What 3-final fixes that 2-draft misses

**Why:** User edited all four 3-final drafts for dawneever--cc-market. Diffing 2-draft vs 3-final revealed 6 systematic transition gaps that templates now encode.

**How to apply:** After generating 2-draft, before presenting to user, run through these checks. Also encoded in templates/wechat.md, xiaohongshu.md, zhihu.md under "Anti-AI Writing Techniques > Connectives & Transitions".

## 6 Patterns

### 1. 动机段衔接 (Motivation paragraph bridging)
When "my workflow" paragraph is immediately followed by "pain point" paragraph, connective is mandatory.
- ❌ `...Codex 来锐评。\n\n还有个绕不开的卡点：Chrome MCP...`
- ✅ `...Codex 来锐评。\n\n但这个工作流还有个绕不开的卡点：Chrome MCP...`
- Bridge words: "但这个工作流" / "问题是" / "当然，使用中还有别的卡点" / "不过有个坎绕不过去"

### 2. 场景链式衔接 (Scene-to-scene chaining)
Multiple usage scenarios must be chained with transitions, not bare juxtaposition.
- ❌ `Claude 做完 plan，把实现甩给 DeepSeek。\n\nPR 写完了，让它过一遍...`
- ✅ `...所以一个很爽的工作流就是，让 Claude 做完 plan，然后把具体实现甩给 DeepSeek。\n\n又比如 PR 写完了，再让它过一遍...`
- Chain words: "所以一个很爽的工作流就是" / "又比如" / "再比如" / "更让我上头的是" / "还有一个场景"

### 3. 段落首句回扣 (Section-first-sentence callback)
New sections must connect back to the previous section's idea. Section headers alone are NOT enough.
- ❌ `## 它到底是什么\n\ntakeover 是一个 Claude Code 插件...`
- ✅ `## 所以我写了 takeover\n\n所以我写了 takeover 这个插件，核心三个命令...`

### 4. 段落拆分节奏 (Paragraph splitting for rhythm)
Punchy concluding sentences should be standalone paragraphs.
- ❌ `...都得交一笔复制粘贴税。这笔税，我交了一年多。`
- ✅ `...都得交一笔复制粘贴税——丢掉上下文，丢掉手头的文件状态，丢掉正在进行的任务。\n\n这笔税，我交了半年多。`

### 5. 身份一致性 (Authorship consistency)
"我" throughout, NEVER "作者" or "笔者" or "项目作者".
- ❌ `takeover 的作者用 heredoc 把这个口子焊死了`
- ✅ `我用 heredoc 把这个口子焊死了`

### 6. 口语化数字和限定词 (Colloquial quantifiers)
- "零 npm 依赖" → "没有 npm 依赖"
- "实现同等 sonnet 任务" → "一般来说 deepseek-v4-pro 可以实现 sonnet 同等的任务"
- "纯 Node.js 内置模块" → "纯用 Node.js 内置模块"
- "没人写过的概念，我管它叫" → "以前很少有人关注的概念，可以叫做"

## Related
- [[2026-05-27-ai-taste-patterns]] — banned phrases, emoji catalogs, formal headers
- [[2026-05-27-author-voice]] — write as author/maintainer, not third-party reviewer
