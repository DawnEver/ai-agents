# Step 04 — Write Analysis & Brief

Write `ongoing/<slug>/1-research/source-analysis.md` synthesizing ALL findings from steps 02-03:

## Before Writing

1. Read `ongoing/<slug>/1-research/source.md` (step 01) — the source kind (github | local-dir | local-file)
2. Read `ongoing/<slug>/1-research/source-exploration.md` (step 02) — code exploration OR report notes
3. Read `ongoing/<slug>/1-research/market-research.md` (step 03) — competitive landscape, content gaps, audience interest
   - **If market-research.md is missing or empty**: abort with "Market research not found. Run step 03 first (`--restart-from 03`)." Do not proceed with uninformed analysis.

The article angles in this analysis must be informed by the market research — what's missing from existing coverage, what audiences are asking for, which similar sources have buzz.

**Pick the template variant by source kind.** Keep the common tail (Market Context, Article Angles);
swap the body to match the source.

### Variant 1 — Code source (`github` / `local-dir`)

```markdown
# Source Analysis: <repo-name>

## Metadata
- **Source**: code — <url or local path>
- **Stars**: <count> (or "new project, <100 stars" / "local, n/a")
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
```

### Variant 2 — Research report (`local-file`)

```markdown
# Source Analysis: <report title>

## Metadata
- **Source**: report — <file path>
- **Author / Publisher**: <who> · **Date**: <when> · **Venue**: <where, if stated>
- **Domain**: <field / topic tags>
- **Target Audience**: [beginner | intermediate | advanced | all]
- **Complexity**: [simple | moderate | complex]
- **Has Visual Assets**: [yes — charts/figures in report | no]

## One-Line Summary
<One sentence — the report's core claim>

## Core Thesis
<The single argument the report makes>

## Key Findings (with evidence, traceable to the document)
- <Finding 1> — <number / figure / section ref>

## Method / How They Know It
<Study design, dataset, model, or reasoning — plain terms>

## Pain Points It Speaks To
<What real question or problem this finding matters for>

## Standout Details
<Counter-intuitive results, sharp quotable lines, surprising data>

## Caveats & Limitations
<What the report admits it doesn't show — or "[unsupported]" claims flagged in step 02>

## Visual Assets Available
<Charts / figures worth reproducing — or "text only">
```

### Common tail (both variants)

```markdown
## Market Context (from market research)
- **Related work / alternatives**: <competing sources and how this differs>
- **Trending demand**: <what audiences are discussing, pain points>
- **Content gap**: <what's missing from existing coverage>

## Article Angles
- 小红书: <emotional hook angle — driven by market gap>
- 微信公众号: <tutorial / deep-dive angle — driven by market gap>
- 知乎: <comparative / mechanism angle — driven by market gap>
- Twitter/X: <hook stat or punchy angle — driven by market gap>
```

Proceed to the Brief Review Gate (05-brief-gate).
