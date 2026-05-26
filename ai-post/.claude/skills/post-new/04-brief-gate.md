# Step 5.5: ⭐ Brief Review Gate — 选题确认 (Angles + Titles)

**Stop here. Do NOT spawn agents yet. Do NOT generate drafts.**

This is an **iterative discussion gate**. The user may question angles, ask for alternatives, refine direction, and go back-and-forth across multiple rounds. Only proceed past this gate when the user **explicitly approves** the full plan (angles + titles). A simple "确认" / "ok" / "go" is not enough — the user must signal they are satisfied with both angles AND titles before you move on.

```
🛑 初稿生成前最后一次确认
→ 用户明确认可角度 + 标题后，才开始写初稿
→ 用户可以在这里提问、质疑、调整任意多轮
```

This gate has two phases: angle confirmation, then title selection.

## Phase 1: Angle Confirmation

Present a brief summary to the user for confirmation:

```
📋 调研完成，准备写作

**项目**：<repo name> — <one-line summary>

**选题方向**：
- 小红书：<angle>
- 微信公众号：<angle>
- 知乎：<angle>
- Twitter/X：<angle>

**需要调整什么吗？** 确认后进入标题选择。
（如只需某平台，请指定。）
```

Wait for the user to reply. The user may:
- Ask questions about specific angles ("这个角度具体怎么写？")
- Suggest refinements ("微信的角度太浅了，往深挖")
- Request alternative angles ("小红书有没有更偏情绪的方向？")
- Adjust scope ("只做微信和知乎")

**This is iterative** — go back and forth until the user is satisfied with all angles. Update `repo-analysis.md` after each adjustment, re-present if needed.

- **If user adjusts angles** → update `repo-analysis.md` Article Angles section, re-present, wait again (loop).
- **If user specifies a single platform** → update target platforms list, re-present for that platform only.
- **If user signals they're done with angles** ("可以了" / "进入标题" / "next") → proceed to Phase 2.

## Phase 2: Title Selection (Chinese platforms only)

After angles are confirmed, generate titles for each Chinese platform being generated. Titles are derived from the repo analysis — pain points, standout details, key numbers, the project's best insight. Writers will use the selected title as creative direction.

**Title generation rules:**
- Author is the subject, tool is the instrument. ✅ "我用它3分钟搞定" not ❌ "被它3分钟搞定"
- No banned opening formulas (see CLAUDE.md Quality Standards)

**Round A — Hook titles (3 per platform)**. Use varied elements across the 3 options:
- 💰 Specific numbers (time saved, speed multiplier, star count)
- ⚡ Surprising gap: "X 已经出现了，你还在用 Y？"
- 🚀 Shortcut framing: fast / easy / one-command
- ☠️ Stakes: eliminate / replace / obsolete
- 反差对比: before vs after with specific numbers

**Round B — Natural style titles (3 per platform)**. No formulas — derive from the project's best insight:
- A compelling one-line statement distilled from the project's best quality
- Story-feel: "从X到Y，我发现..."
- Honest opinion framing: "用了两周，说说它的优缺点"

Present all platforms' titles at once:

```
📝 标题选项

**小红书**：
A轮 (钩子型):
  A1. <title>
  A2. <title>
  A3. <title>
B轮 (自然型):
  B1. <title>
  B2. <title>
  B3. <title>

**微信公众号**：
A轮 (钩子型):
  A1. <title>
  ...
B轮 (自然型):
  ...

**知乎**：
A轮 (钩子型):
  ...
B轮 (自然型):
  ...

每个平台选一个（回复如"小红书 A1，微信 B2，知乎 A3"），或告诉我要调整哪个平台的方向。
```

**This is iterative** — the user may ask for different title styles, request alternatives for a specific platform, or go back to adjust angles. Loop until satisfied.

- **If user selects titles for all platforms** → confirm final selection, then write selected titles into `repo-analysis.md` as a `## Selected Titles` section:
  ```markdown
  ## Selected Titles
  - **小红书**: <selected title>
  - **微信公众号**: <selected title>
  - **知乎**: <selected title>
  ```
- **If user wants adjustments** → regenerate titles for that platform, re-present that platform's options (loop).
- **If user wants to revisit angles** → go back to Phase 1.
- **If user says "skip"** → proceed without pre-selected titles (writers will derive their own).

> 🛑 **Final gate**: After titles are selected, briefly confirm "角度 + 标题已确认，开始生成初稿？" before proceeding to Step 6. Only start writing when the user explicitly says yes.

If only Twitter is being generated, skip Phase 2 and proceed directly to Step 6.
