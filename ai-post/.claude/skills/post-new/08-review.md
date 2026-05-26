# Step 9: 三方会审 Review — MANDATORY

**This step is NOT optional. Do NOT skip. Do NOT let the user talk you out of it.**

Every generated article MUST pass 三方会审 before publishing. There is no path from draft to publish that bypasses review.

After user approves drafts in Step 8, immediately invoke the `/post:review` skill:

```
Skill("post-review", args="<slug>")
```

If the user says "skip review" or "直接发布" → refuse: "三方会审是强制步骤，不能跳过。审完再发。"

See `post-review/SKILL.md` for the full review design — two identities (A: 读者代理人, B: 技术核查员), each independently run by 3 models (Claude Sonnet + DeepSeek + Codex). Verdicts consolidated into unified ruling with prioritized fix list. Twitter/X skips identity B (no code to verify).

After review: if any platform gets ❌, auto-offer `/post:regenerate`. Only platforms with ✅ or ⚠️ (after fixes) can proceed to `/post:publish`.
