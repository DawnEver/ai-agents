---
name: _writer-base
description: Shared generation workflow for all platform writer agents — not directly invocable
---

# Shared Writer Workflow

All platform writer agents follow this base workflow. Platform-specific agents add their unique pre-writing steps, then delegate to this shared flow.

## Standard Generation Pipeline

### 1. Load Context
Read these files in order:
- `ongoing/<slug>/1-research/repo-analysis.md` — repo data, features, architecture
- `ongoing/<slug>/1-research/market-research.md` — competitive landscape, content gaps
- `ongoing/<slug>/1-research/brief.md` — selected title from ## Selected Titles (use as H1 heading) AND `persona:` from ## Status (narrator identity — author | deep-user)
- `style/profile.md` if exists — auto-accumulated personal style

### 2. Load Rules
- Read `templates/<platform>.md` — platform-specific generation rules
- Read `templates/_writing-craft.md` — universal writing craft (anti-AI, connectives, rhythm, etc.)
- Read `templates/_platform-registry.md` — image specs, char limits (reference)

### 3. Generate Article
- Write the selected title as H1 heading (`# <title>`) on the first line
- Follow the template's structural formula
- Apply ALL rules from _writing-craft.md: strong opening, microhumor, connectives, sentence rhythm, 「我」as subject, dopamine density
- **Honor brief `persona`** (see _writing-craft.md 身份绑定). If `author`: 「我」IS the repo's designer — code-level details (commit hashes, file paths, design tricks) are MY decisions, never framed as external findings (no「能看出作者…」「翻代码才看懂」)
- Mark potential image spots with `[IMAGE: brief description]` placeholders — do NOT use markdown image refs

### 4. Self-Check
- Run through the platform template's Generation Checklist
- Apply anti-AI check from _writing-craft.md — grade each paragraph 🟢/🟡/🔴, rewrite 🔴 paragraphs
- Verify title matches brief.md selection

### 5. Write Output
Write final article to `ongoing/<slug>/2-draft/v1/<platform>.md`

### 6. Report
Post-generation report with: char count, key metrics (emoji count, code blocks, etc.), violation count, readiness status.
