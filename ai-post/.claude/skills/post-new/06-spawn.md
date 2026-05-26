# Step 7: Spawn Platform Agents

Now spawn sub-agents to generate the articles. Each agent reads the analysis, the image manifest, and its template.

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
1. Read `articles/<slug>/repo-analysis.md`
2. Read `articles/<slug>/images.md` — use the image paths defined there, do NOT invent new paths
3. Place markdown image references `![alt text](images/<filename>)` in the article where images belong

After all agents complete, proceed to the User Draft Review (07-user-review).
