# Step 06 — Spawn Platform Agents

Now spawn sub-agents to generate the articles. Each agent reads the analysis, market research, and its template.

**If generating for ALL platforms**, spawn all 4 agents in PARALLEL (single message, multiple Agent tool calls):

**Agent mapping** — see `templates/_platform-registry.md` for the authoritative platform→agent mapping:

| Platform Key | Agent |
|-------------|-------|
| xiaohongshu | xiaohongshu-writer |
| wechat | wechat-writer |
| zhihu | zhihu-writer |
| twitter | twitter-writer |

Spawn all target platform agents in PARALLEL (single message, multiple Agent tool calls). Pass the slug to each agent.

Pass the slug to each agent. Each agent must:
1. Read `ongoing/<slug>/1-research/repo-analysis.md`
2. Read `ongoing/<slug>/1-research/market-research.md` — use market context to inform angle selection
3. Read `ongoing/<slug>/1-research/brief.md` — use the selected title from `## Selected Titles`; do NOT invent a new title
4. Write the title as an H1 heading (`# <title>`) on the first line of the article
5. Write output to `ongoing/<slug>/2-draft/v1/<platform>.md`

## Image Placeholders

Images are planned AFTER drafts exist (step 07). During writing, mark potential image spots inline:

```
[IMAGE: brief description of what image would help here]
```

Example: `[IMAGE: terminal screenshot showing agent mode output with Read/Write/Bash operations]`

These markers become input for step 07 to plan the image manifest.

## After All Agents Complete

1. Create `ongoing/<slug>/2-draft/v1/` directory (if not already created by agents)
2. Verify all 4 platform files exist in `2-draft/v1/` — this is the baseline, must be complete
3. Update `brief.md`: `current_version: v1`
4. Proceed to Image Planning (07-images)

**Layout**: `2-draft/v1/` is the baseline — all platforms required. Subsequent versions (`v2/`, `v3/`, ...) only contain files that changed. Missing files inherit from the previous version. No separate `annotated/` or `3-final/` directory.

Do NOT create version snapshots if agents failed — only for successfully written drafts.
