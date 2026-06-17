# Step 08 — User Review: MANDATORY READ-THROUGH

**Do NOT invoke review yet. Do NOT skip this step.**

三方会审 costs 18+ agent calls across all platforms. The user must read and approve every draft AND the image plan before review begins.

## Layout

```
ongoing/<slug>/2-draft/
  v1/<platform>.md    ← AI originals (baseline, all platforms)
  v2/<platform>.md    ← user round 1 edits (only changed platforms)
  v3/<platform>.md    ← after 三方会审 (only changed platforms)
  ...
```

**Inheritance rule**: Each version only stores files that changed. To get the full article set at version N, walk back through N, N-1, N-2, ... v1 until you find each platform's latest copy. v1 is the baseline — always complete.

## Presentation

After step 07 completes, present the generated articles AND image plan:

```
📄 初稿 + 图片计划，请阅读

**生成结果** (v1 baseline) — render ONE line per ACTIVE platform only (from `brief.md` `platforms:`, defaulting from `templates/_platform-registry.md`). Do not list inactive platforms:
- <platform-label>：`<title>` — ongoing/<slug>/2-draft/v1/<platform>.md (<char_count> chars / <tweet_count> tweets)
  (e.g. 小红书 / 微信公众号 / 知乎 — char_count; Twitter/X — tweet_count)

**图片计划**：ongoing/<slug>/2-draft/v1/images.md (N 张图)

**请逐篇阅读，提出你的看法：**
- 标题是否合适？
- 角度和语气是否符合预期？
- 有没有需要调整的段落？
- 技术事实准确吗？
- 图片计划是否匹配文章内容？
```

## Iteration Loop

Track `current_version`. Between versions the user can light edit, annotate, or request 三方会审 (mandatory at least once).

### On user edit (any method — IDE, conversation request, file paste):

1. Create `2-draft/v<N+1>/` directory
2. Copy only changed platform files to `2-draft/v<N+1>/` — unchanged platforms inherit from previous version
3. Increment `current_version` in `brief.md`
4. If user edited via IDE, diff `v<N>/` vs `v<N+1>/` to understand changes
5. Re-present changed articles, wait again

### If user requests regeneration of one platform:

1. Create `2-draft/v<N+1>/`, snapshot current state of that platform there
2. Re-spawn the writer agent, write to `2-draft/v<N+1>/<platform>.md`
3. Increment `current_version`

### If user requests 三方会审:

1. Create `2-draft/v<N+1>/`, snapshot current changed files there
2. Proceed to Step 09. After review, fixes create another version.
3. User may then do further light edits → confirm final.

### If user changes a title:

Update both the H1 heading in the file AND `brief.md` (`## Selected Titles`).

### If user confirms final ("可以发布了" / "final"):

**Gate first — 三方会审 must have actually run AND passed.** Check for a real `2-draft/v<N>/review-verdict.md` (the latest one resolved via the version chain). It must exist, reflect a completed review, and pass for every ACTIVE platform.

1. **Resolve active platforms** from `brief.md` `platforms:` (defaulting from `templates/_platform-registry.md` if absent).
2. **Parse the latest `review-verdict.md`** and read each active platform's verdict.

Then branch:

- **If no `review-verdict.md` exists** (review never ran) → do NOT set `finalized` or `review_completed`. Route the user to Step 09: "还没过三方会审，先审完再发。" Run the review, then return here.
- **If any ACTIVE platform is ❌ (rejected/failing)** → do NOT set `finalized` or `review_completed`. Report which platform(s) failed and route back to Step 09 (re-review) or manual rewrite: "<platform> 三方会审未通过，先修复再发。" A finalized article requires every active platform to be publishable.
- **If every ACTIVE platform passes** (✅, or ⚠️ warnings-only — warnings may proceed):
  1. Create final snapshot `2-draft/v<N+1>/` with any last changes
  2. **Assemble full set**: for each platform, walk back versions until you find the latest copy. If any platform is missing entirely, re-spawn or copy from the nearest version that has it — the final version set must be complete.
  3. Update `brief.md`: `finalized: true`, `current_version: v<N+1>`, `review_completed: true`
  4. Proceed to Step 10.

> ⚠️ `finalized: true` / `review_completed: true` may ONLY be set after a real latest `2-draft/vN/review-verdict.md` exists AND every active platform passes (❌ blocks; ⚠️ warnings may proceed). Never set them to skip ahead.

## Optional Self-Check Supplement (NOT a replacement for 三方会审)

The mandatory gate is 三方会审 (Step 09). The quick pass below is an **optional** aid the user (or you) may run while reading drafts — it does not substitute for review and never satisfies the `review_completed` gate. Full banned-phrase list, replacement table, and anti-AI grading live in `templates/_writing-craft.md`.

- [ ] 「我」视角一致：每段至少一句以"我"作主语；核对 brief `persona` — 若 `author`，无「能看出作者…」「翻代码才看懂」等把自身设计当外部发现的第三人称措辞
- [ ] 段落迷你论点 + 串联测试：每段一句话能说出核心论点，串起来逻辑链条通顺
- [ ] 多巴胺密度：每段至少 1 个点（洞察/例子/比喻/细节/微幽默），无连续 3 段空白
- [ ] 句子节奏：无连续 5 句长度相近；插入短句(5-10字)或长句(25-35字)打破单调
- [ ] 段落长度：手机屏 3-5 行，无超过 7 行的段落

## State Tracking in brief.md

```
## Status
angles_confirmed: true
titles_confirmed: true
current_version: v3
review_completed: true        ← set after first 三方会审 pass
finalized: true               ← set when user confirms final
platforms: xiaohongshu,wechat,zhihu,twitter
```

> 🛑 **Gates**:
> - 三方会审 must run at least once (review_completed: true) before finalized: true
> - Never run 三方会审 before the user has read and okayed the current state
> - v1 must be complete (all platforms). Later versions only store deltas.
> - Before publish/archive, assemble the full set — walk back versions until each platform is found
