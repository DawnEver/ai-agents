# Step 05 — Brief Review Gate: 选题确认 (Angles + Titles)

**Stop here. Do NOT spawn agents yet. Do NOT generate drafts.**

This is an **iterative discussion gate**. The user may question angles, ask for alternatives, refine direction, and go back-and-forth across multiple rounds. Only proceed past this gate when the user **explicitly approves** the full plan (angles + titles). A simple "确认" / "ok" / "go" is not enough — the user must signal they are satisfied with both angles AND titles before you move on.

```
🛑 初稿生成前最后一次确认
→ 用户明确认可角度 + 标题后，才开始写初稿
→ 用户可以在这里提问、质疑、调整任意多轮
```

This gate has three phases: **Phase 0 身份确认 (persona)**, then angle confirmation, then title selection. **All phases write to `ongoing/<slug>/1-research/brief.md`** so the session can resume correctly after interruption.

## Phase 0: Persona Determination (narrator identity)

Before angles, decide who「我」is — this is **identity binding**, not tone. Get it wrong and writers leak a third-party "作者" (e.g.「能看出作者真踩过坑」「翻代码才看懂」) no matter how much the prompt says "第一视角".

1. Read `style/private/author-identity.md` (gitignored personal-info file).
2. Get the target repo owner / primary git author (`git -C repos/<repo-slug> remote get-url origin`, or gh metadata).
3. Decide:
   - Owner matches an identity in `author-identity.md` → **persona: author** (我 = repo 的设计者本人).
   - Clearly the user's repo but owner not listed → **ask the user**, then add the alias to `author-identity.md`.
   - Repo is someone else's and user didn't write it → **persona: deep-user**.
   - **Uncertain → ask the user. Never guess.**
4. Write `persona: author` (or `deep-user`) into `brief.md`. Writers MUST honor it (see `_writing-craft.md` 身份绑定).

Personal info beyond the persona flag stays in `style/private/` (gitignored) — never copy it into drafts or committed research.

## Persistence File: `brief.md`

`ongoing/<slug>/1-research/brief.md` is the gate's single source of truth. Write it after each confirmed state:

```markdown
# Brief: <slug>

## Confirmed Angles
- **小红书**: <angle>
- **微信公众号**: <angle>
- **知乎**: <angle>
- **Twitter/X**: <angle>

## Selected Titles
- **小红书**: <title>          ← added after Phase 2; may be revised in step 08
- **微信公众号**: <title>
- **知乎**: <title>

## Status
persona: author                ← set in Phase 0 (author | deep-user); writers MUST honor
angles_confirmed: true         ← set after Phase 1 approved
titles_confirmed: true         ← set after Phase 2 approved
titles_reviewed: true          ← set after step 08 user approves drafts (may include title changes)
platforms: xiaohongshu,wechat,zhihu,twitter   ← active platform list
```

**Title lifecycle**: Phase 2 selects initial titles → step 06 writers use them → step 08 user may revise them → step 10 final confirmation. The title in the latest `2-draft/v<N>/<platform>.md` is the definitive published title.

**Resume logic**: if `brief.md` exists with `angles_confirmed: true` but no `titles_confirmed`, skip Phase 1 and go straight to Phase 2. If both are true, skip this step entirely.

## Phase 1: Angle Confirmation

Present a brief summary to the user for confirmation. Include market research signals:

```
📋 调研完成，准备写作

**项目**：<repo name> — <one-line summary>

**选题方向**：
- 小红书：<angle>
- 微信公众号：<angle>
- 知乎：<angle>
- Twitter/X：<angle>

**市场信号**：<key finding from market-research.md — trending demand, content gap>

**需要调整什么吗？** 确认后进入标题选择。
（如只需某平台，请指定。）
```

Wait for the user to reply. The user may:
- Ask questions about specific angles ("这个角度具体怎么写？")
- Suggest refinements ("微信的角度太浅了，往深挖")
- Request alternative angles ("小红书有没有更偏情绪的方向？")
- Adjust scope ("只做微信和知乎")

**This is iterative** — go back and forth until the user is satisfied with all angles. Update `ongoing/<slug>/1-research/repo-analysis.md` after each adjustment, re-present if needed.

- **If user adjusts angles** → update `repo-analysis.md` Article Angles section, re-present, wait again (loop).
- **If user specifies a single platform** → update target platforms list, re-present for that platform only.
- **If user signals they're done with angles** ("可以了" / "进入标题" / "next") → write `brief.md` with confirmed angles and `angles_confirmed: true`, then proceed to Phase 2.

## Phase 2: Title Selection (Chinese platforms only)

After angles are confirmed, generate titles for each Chinese platform being generated. Titles are derived from the repo analysis — pain points, standout details, key numbers, the project's best insight. Writers will use the selected title as creative direction.

**Title generation rules:**
- Author is the subject, tool is the instrument. ✅ "我用它3分钟搞定" not ❌ "被它3分钟搞定"
- No banned opening formulas (see templates/ for per-platform banned-phrase lists and banned section headers)
- **小红书标题 ≤20 字硬上限**（含标点/emoji）。生成 RA/RB 选项时每条都数一遍，超 20 字的直接不要。

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

**小红书 (R)**：
A轮 (钩子型):
  RA1. <title>
  RA2. <title>
  RA3. <title>
B轮 (自然型):
  RB1. <title>
  RB2. <title>
  RB3. <title>

**微信公众号 (W)**：
A轮 (钩子型):
  WA1. <title>
  ...
B轮 (自然型):
  ...

**知乎 (Z)**：
A轮 (钩子型):
  ZA1. <title>
  ...
B轮 (自然型):
  ...

每个平台选一个（回复如"RA1, WB2, ZA3"），或告诉我要调整哪个平台的方向。
```

**Platform letter labels**: 小红书=R, 微信=W, 知乎=Z. Prefix every option ID with the platform letter (`RA1`, `WB2`, `ZA3`) so the user can select across platforms in one compact reply without naming each platform.

**This is iterative** — the user may ask for different title styles, request alternatives for a specific platform, or go back to adjust angles. Loop until satisfied.

- **If user selects titles for all platforms** → write selected titles into `brief.md` (add `## Selected Titles` + `titles_confirmed: true`), then confirm:
  > "角度 + 标题已确认，开始生成初稿？"
- **If user wants adjustments** → regenerate titles for that platform, re-present that platform's options (loop).
- **If user wants to revisit angles** → go back to Phase 1, update `brief.md` accordingly.
- **If user says "skip"** → proceed without pre-selected titles (writers will derive their own); write `brief.md` with `titles_confirmed: skipped`.

> 🛑 **Final gate**: Only start writing when the user explicitly says yes to "开始生成初稿？"

If only Twitter is being generated, skip Phase 2 and proceed directly to Step 06.
