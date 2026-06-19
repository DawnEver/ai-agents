# Shared Writer Workflow

> Shared include for all platform writer agents — not directly invocable.

All platform writer agents follow this base workflow. Platform-specific agents add their unique pre-writing steps, then delegate to this shared flow.

## Standard Generation Pipeline

### 1. Load Context
Read these files in order:
- `ongoing/<slug>/1-research/repo-analysis.md` — repo data, features, architecture
- `ongoing/<slug>/1-research/market-research.md` — competitive landscape, content gaps
- `ongoing/<slug>/1-research/brief.md` — selected title from ## Selected Titles (use as H1 heading) AND `persona:` from ## Status (narrator identity — author | deep-user). **Title contract**: always read `## Selected Titles`; use the recorded title verbatim as the H1. The ONE exception is a `[DERIVE: ...]` marker (titles were skipped — e.g. Twitter-only): treat it as direction to generate your own title from the confirmed angle + repo analysis, not as literal H1 text. Never invent a title when a concrete one is recorded.
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
- Mark potential image spots with `[IMAGE: brief description]` placeholders. **At draft/v1 generation time, use ONLY `[IMAGE: ...]` placeholders — do NOT write markdown image references.** The canonical final form is the versioned markdown ref `![alt](../../images/<image-id>-vN.png)` (never an unversioned `images/<file>` path), added LATER at the image-generation / finalization stage (Step 10), once images exist. This is a deliberate two-stage lifecycle: `[IMAGE: ...]` placeholders now, resolved `../../images/<id>-vN.png` refs at finalization — they are not a contradiction.

### 4. Self-Check
- Run through the platform template's Generation Checklist
- Apply anti-AI check from _writing-craft.md — grade each paragraph 🟢/🟡/🔴, rewrite 🔴 paragraphs
- Verify title matches brief.md selection (or, for a `[DERIVE: ...]` marker, that a title was generated from the angle)
- **Image check is draft-stage only**: confirm every image spot is an `[IMAGE: ...]` placeholder. Do NOT check for `../../images/...` markdown refs here — those don't exist until Step 10 finalization. (The orphan/ref consistency check between markdown refs and the images manifest happens at finalization, not at v1.)

### 5. Write Output
Write final article to `ongoing/<slug>/2-draft/v1/<platform>.md`

### 6. Report
Post-generation report with:
- Char count + platform-relevant metrics (emoji count, code blocks, comparison-table dimensions, limitations count, etc.)
- Violation count
- Readiness: if violations are 0 → ✅ ready to publish
- Suggested next step: `/post-publish <platform> <slug>`
