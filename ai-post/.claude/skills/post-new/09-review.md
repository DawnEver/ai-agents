# Step 09 — 三方会审 Review: MANDATORY

**This step is NOT optional. Do NOT skip. Do NOT let the user talk you out of it.**

Every article must pass 三方会审 at least once before publishing. There is no path to publish that bypasses review. The image plan (`images.md`) is also reviewed.

## Pre-Review: Version Diff Chain

Before invoking review, collect the full revision history:

1. Walk `2-draft/v1/` through `2-draft/v<N>/` (current). For each platform, find every version that changed it.
2. Build a diff chain: `diff v1/<platform>.md v<N>/<platform>.md` for each platform
3. Also diff consecutive versions to show what the user changed each round
4. Package into context for the review skill:

```
## Revision History for <platform>
v1 → v2: user adjusted tone, added Workflow motivation story
v2 → v3: user restructured argument flow
...
Current version: v<N>

## Full diff from baseline
<diff v1 → vN>
```

5. Pass this context: prepend the version history to the article content before passing to the sharp-review workflow, so reviewers can see what changed and won't re-flag already-fixed issues.

After collecting version context, invoke the review:

```
Skill("post-review", args="<slug>")
```

The review reads the diff chain from the version history prepended to content.

If the user says "skip review" or "直接发布" → refuse: "三方会审是强制步骤，不能跳过。审完再发。"

See `post-review/SKILL.md` for the full review design — two identities (A: 读者代理人, B: 技术核查员), each independently run by 2 models (Claude Sonnet + DeepSeek; 3 with --full-review adding Claude Opus). Twitter/X skips identity B (no code to verify).

## Image Plan Review — MANDATORY, not optional

Every review round MUST also审 `images.md` (post-review Phase 6). Do not finish a review without it. The `review-verdict.md` must contain an `## Image plan review` section (or explicitly note "no images.md yet").

- Do the images match the article content? (orphan check — every manifest image still maps to an `[IMAGE]` marker in the latest drafts)
- Are any key images missing?
- Does each image's AI prompt accurately describe the requirement?
- **Cover hook freshness**: does each cover's hook text match the LATEST title? A title or motivation change between versions almost always staleizes the cover prompt — this is the most common miss. Update the stale cover text and save the corrected `images.md` to `v<N+1>/`.
- Aspect ratios per `templates/_platform-registry.md`.

## After Review

1. Persist review outcomes per `post-review/06-persist.md` — writes fixed articles + `review-verdict.md` to `v<N+1>/`
2. Update `brief.md`: `review_completed: true`, `current_version: v<N+1>`
3. Return to step 08 — user may do light edits, re-review, or confirm final

For any platform that fails (❌):
- Tell user: "需要手动重写后重新 `/post-review <slug> <platform>`"
