# Step 04 — Write Analysis & Brief

Write `ongoing/<slug>/1-research/repo-analysis.md` synthesizing ALL findings from steps 02-03:

## Before Writing

1. Read `ongoing/<slug>/1-research/repo-exploration.md` (step 02) — deep code exploration notes
2. Read `ongoing/<slug>/1-research/market-research.md` (step 03) — competitive landscape, content gaps, audience interest
   - **If market-research.md is missing or empty**: abort with "Market research not found. Run step 03 first (`--restart-from 03`)." Do not proceed with uninformed analysis.

The article angles in this analysis must be informed by the market research — what's missing from existing coverage, what audiences are asking for, which similar repos have buzz.

```markdown
# Repo Analysis: <repo-name>

## Metadata
- **URL**: <url>
- **Stars**: <count> (or "new project, <100 stars")
- **Language**: <primary> + <others>
- **Topics**: <tags>
- **Category**: [dev-tool | library | framework | app | learning-resource | other]
- **Target Audience**: [beginner | intermediate | advanced | all]
- **Complexity**: [simple | moderate | complex]
- **Has Visual Assets**: [yes — screenshots/GIFs in README | no — CLI/text only]

## One-Line Summary
<One sentence>

## Architecture Overview
<Organization, patterns, entry points>

## Key Features (from code, with file path evidence)
- <Feature 1> — `path/to/file`
- <Feature 2> — `path/to/file`

## Pain Points It Solves
<What specific developer pain?>

## Standout Details
<Clever tricks, beautiful API, surprising finds in the actual code>

## Performance / Scale
<Benchmarks, perf claims, architecture for scale — or "no benchmarks found">

## Ecosystem & Dependencies
<Dependencies, plugin system, ecosystem>

## Visual Assets Available
<Screenshots, GIFs, demo links — or "text/CLI only, no visuals in README">

## Market Context (from market research)
- **Similar repos**: <key alternatives and how this differs>
- **Trending demand**: <what audiences are discussing, pain points>
- **Content gap**: <what's missing from existing coverage>

## Article Angles
- 小红书: <emotional hook angle — driven by market gap>
- 微信公众号: <tutorial deep-dive angle — driven by market gap>
- 知乎: <comparative analysis angle — driven by market gap>
- Twitter/X: <hook stat or punchy angle — driven by market gap>
```

Proceed to the Brief Review Gate (05-brief-gate).
