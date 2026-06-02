# Step 07 — Spawn Platform Agents

Now spawn sub-agents to generate the articles. Each agent reads the analysis, the market research, the image manifest, and its template.

**If generating for ALL platforms**, spawn all 4 agents in PARALLEL (single message, multiple Agent tool calls):

| Agent | Slug | Task |
|-------|------|------|
| `xiaohongshu-writer` | `<slug>` | Generate 小红书 article |
| `wechat-writer` | `<slug>` | Generate 微信公众号 article |
| `zhihu-writer` | `<slug>` | Generate 知乎 article |
| `twitter-writer` | `<slug>` | Generate Twitter/X thread |

**If generating for ONE platform**, spawn just that agent:
- xiaohongshu → `xiaohongshu-writer`
- wechat → `wechat-writer`
- zhihu → `zhihu-writer`
- twitter → `twitter-writer`

Pass the slug to each agent. Each agent must:
1. Read `ongoing/<slug>/1-research/repo-analysis.md`
2. Read `ongoing/<slug>/1-research/market-research.md` — use market context to inform angle selection
3. Read `ongoing/<slug>/2-draft/images.md` — use the image paths defined there, do NOT invent new paths
4. Place markdown image references `![alt text](../images/<filename>)` in the article where images belong
5. Write output to `ongoing/<slug>/2-draft/<platform>.md`

After all agents complete, proceed to the User Draft Review (08-user-review).
