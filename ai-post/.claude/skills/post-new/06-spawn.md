# Step 06 — Spawn Platform Agents

Now spawn sub-agents to generate the articles. Each agent reads the analysis, market research, and its template.

**Active platforms** are those recorded in `ongoing/<slug>/1-research/brief.md` (defaulting to the full set in `templates/_platform-registry.md` if the brief lists none). A single-platform or Twitter-only run is valid — only spawn agents for the active platforms.

**Agent mapping**: consult `templates/_platform-registry.md` (the `agent` column) for the authoritative platform→agent mapping. Do not hardcode it here.

Spawn the active platform agents in parallel, using the host's native sub-agent mechanism:

- **Claude Code:** invoke the named agent from `.claude/agents/<agent>.md` with the Agent tool.
- **Codex:** read `.claude/agents/<agent>.md` (and `_writer-base.md` when referenced), then spawn a collaboration sub-agent with that prompt. Do not expect Claude named agents to be registered in Codex.

Use one parallel batch where the host supports it. Pass the slug to each agent. Each agent must:
1. Read `ongoing/<slug>/1-research/source-analysis.md`
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
2. Verify a platform file exists in `2-draft/v1/` for EACH active platform recorded in `brief.md` (defaulting from `templates/_platform-registry.md`) — only the active platforms form the baseline, not always all 4
3. Update `brief.md`: `current_version: v1`
4. Proceed to Image Planning (07-images)

**Layout**: `2-draft/v1/` is the baseline — every active platform required. Subsequent versions (`v2/`, `v3/`, ...) only contain files that changed. Missing files inherit from the previous version. No separate `annotated/` or `3-final/` directory.

Do NOT create version snapshots if agents failed — only for successfully written drafts.
