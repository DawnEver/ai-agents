# Step 03 — Market Research

Search for similar repos, trending discussions, and existing content coverage. This runs **before** the analysis (step 04) so the repo analysis can fold market context into article angles.

## Inputs
- `ongoing/<slug>/1-research/repo-exploration.md` — step 02 output: repo structure, language, topics
- Repo metadata from step 01: primary language, topics, description

## Output
- `ongoing/<slug>/1-research/market-research.md` — following `templates/market-research-template.md`

## Steps

### 1. Create output directory
```bash
mkdir -p "ongoing/<slug>/1-research"
```

### 2. Search similar repos (Source A: GitHub)

Extract the repo's primary language and top 3 topic keywords from step 02 exploration notes. Build 2-3 search queries:

```
WebSearch: site:github.com <primary-language> <topic-keyword-1> <topic-keyword-2>
WebSearch: "<repo-name>" alternatives OR vs OR comparison site:github.com
```

Pick top 3-5 repos that solve a similar problem. For each: name, stars, primary language, and the key difference vs our target repo. Prefer repos with >50 stars and recent activity.

### 3. Search trending discussions (Source B: HN + Reddit)

```
WebSearch: <repo-name> site:news.ycombinator.com OR site:reddit.com
WebSearch: <domain-keywords> trending OR "hot take" OR discussion 2025 2026
```

Identify: what people are excited about, common complaints, recurring feature requests in this domain. Note the tone of discussion — enthusiastic, skeptical, pragmatic.

### 4. Search existing content (Source C: Chinese platforms)

```
WebSearch: <repo-name> 教程 OR 介绍 OR 评测 OR 体验 site:zhihu.com
WebSearch: <repo-name> site:mp.weixin.qq.com
WebSearch: <repo-name> OR <domain-keywords> site:xiaohongshu.com
```

For each article found: title, platform, date, angle used, and what's **missing** from their coverage. This is the content gap — your article should fill it.

### 5. Search existing content (Source D: English platforms)

```
WebSearch: <repo-name> tutorial OR review OR "getting started" OR overview
```

Same analysis as Chinese platforms — what angle did they use, what did they miss?

### 6. Write `market-research.md`

Fill in `templates/market-research-template.md`. Be specific — name repos, cite actual posts with dates, quote notable comments. This is factual research, not opinion.

## Hard rules

- Write exactly what you found — no invented repos, posts, or numbers.
- If a search returns no results, note "no results" and move on. Don't fabricate.
- Proceed gracefully with partial data. A thin market research file is better than a blocked pipeline.
- Content gap analysis must cite specific existing articles — "no one has written X about Y because the only existing post at <url> covered Z instead."
- This is context for step 04 analysis and step 05 brief gate. Don't form conclusions here — just present findings.

## Fallback

If WebSearch is not available or returns no results for all queries, write a minimal `market-research.md` with a `## Note` section: "WebSearch unavailable or returned no results. Market context could not be gathered." Proceed to step 04 — the pipeline must not block on search failures. The analysis step will note the missing market context.

## Resume

If `ongoing/<slug>/1-research/market-research.md` is non-empty, skip this step entirely.
