---
name: sharp-review-2026-06-18
description: Sharp review findings — 38 total
metadata:
  type: project
---


## Review 2026-06-18 (session) — architecture survey (架构锐评) — round 2

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): OK
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260618-001] [HIGH] .claude/agents/wechat-writer.md — UTF-8 BOM before YAML frontmatter can break agent/skill registration

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Strip BOMs from wechat-writer.md, post-new/SKILL.md, post-archive/SKILL.md; add lint that files start with exact --- bytes

Files render line 1 as ﻿--- with bytes EF BB BF before ---. A strict frontmatter parser may not recognize the metadata, silently failing to register.

---

### [SR-20260618-002] [HIGH] .claude/skills/post-new/08-user-review.md — Finalization gate accepts any review-verdict.md even if the verdict failed

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Parse latest verdict table; require every active platform publishable; block ❌ and define ⚠️ handling

Lines 72-78 only require a verdict artifact before finalized:true; 09-review.md sets review_completed:true regardless of pass/fail. A failing 三方会审 can still mark the article finalized.

---

### [SR-20260618-003] [HIGH] .claude/skills/post-archive/SKILL.md — Archive deletes ongoing/<slug> before later steps still need the version chain

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Move style archive/profile extraction before cleanup, or read only archived flat finals after Step 3

Step 3 rm -rf ongoing/<slug>, then Step 4 assembles from 2-draft/v<N>/ to write style/published/. The raw version chain is gone, destroying its own input.

---

### [SR-20260618-004] [HIGH] .claude/skills/post-archive/SKILL.md — Archive gate trusts brief.md finalized:true and does not verify a passing review artifact

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Use same verdict gate as publish: locate latest review-verdict.md, parse status, abort on missing/failed review

Step 1 only checks brief.md finalized:true while archive claims to store audit of passing 三方会审. Stale/edited brief can archive unreviewed or rejected drafts.

---

### [SR-20260618-005] [MEDIUM] .claude/skills/post-new/05-brief-gate.md — Twitter has no title contract, but every writer is told to require one

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Always write a Twitter Selected Titles entry, using a [DERIVE: ...] marker when no fixed title chosen

Phase 2 is Chinese-platform-only and Twitter-only runs skip it, but _writer-base.md requires every writer to read ## Selected Titles and use it as H1.

---

### [SR-20260618-006] [MEDIUM] .claude/skills/post-new/SKILL.md — Steps 02 and 03 declared parallel, but market research depends on exploration output

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Make Step 03 consume only Step 01 metadata, or stop advertising 02/03 as dependency-free parallel

SKILL.md says 02/03 have no dependency; 03-market-research.md lists repo-exploration.md as input and extracts language/topics from Step 02 notes.

---

### [SR-20260618-007] [MEDIUM] .claude/skills/post-review/02-reviewers.md — --full-review third reviewer is Codex in one place and Opus in another

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Choose one third reviewer, define once in reviewer config, reference from SKILL maps

post-review/SKILL.md and post-new/09-review.md say --full-review adds Codex. 02-reviewers.md says it appends Claude Opus as reviewer C.

---

### [SR-20260618-008] [MEDIUM] .claude/skills/post-review/04-synthesis.md — Review examples skip identity B for 小红书 even though only Twitter should skip it

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Fix synthesis and persist examples so only Twitter/X has B技术 marked skipped

post-review/SKILL.md says Twitter/X skips identity B, but 04-synthesis.md and 06-persist.md show 小红书 with B as —, teaching reviewers to skip technical review on the wrong platform.

---

### [SR-20260618-009] [MEDIUM] .claude/agents/_writer-base.md — Draft-stage image placeholder contract conflicts with platform templates demanding markdown image refs

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Split template image instructions into draft-time placeholders and final-time resolved refs; remove stale images/<file> examples

_writer-base.md says v1 drafts use only [IMAGE: ...]. WeChat/Zhihu/Twitter templates require markdown image refs and some examples use unversioned images/<file> instead of ../../images/<id>-vN.png.

---

### [SR-20260618-010] [MEDIUM] templates/_platform-registry.md — The platform registry is still not the single source of truth

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Make registry metadata machine-readable or remove copied literals from templates, scripts, and skill examples

Emoji density duplicated in template frontmatter; char limits repeated in registry, templates, char_count.py, publish rules; aspect ratios repeated in image planning/review. WeChat fixed but architecture still requires multi-file edits.

---

### [SR-20260618-011] [MEDIUM] .claude/settings.json — Settings still authorize removed codex-image-in-cc plugin instead of actual Codex CLI path

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Remove stale codex-image Skill permissions and enabledPlugins; explicitly allow required codex exec Bash command

Settings allow Skill(codex-image:*) and enable codex-image@codex-image-in-cc, while takeover-image.md says no third-party deps and runs codex exec --full-auto. The actual Bash path is not represented.

---

### [SR-20260618-012] [MEDIUM] .claude/skills/post-publish/SKILL.md — Publish skill ignores delta-version inheritance when loading the article

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Use same walk-back lookup as export_article.py: search vN down to v1 for target platform file

Step 1 loads 2-draft/v<N>/<platform>.md from highest version, but later versions store only changed files; unchanged platforms inherit from earlier and will be missing at highest vN.

---

### [SR-20260618-013] [MEDIUM] .claude/skills/post-publish/char_count.py — Character counter does not parse formats the templates tell writers to emit

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** For 小红书 stop at ## 配图; for Twitter split on Tweet N, [Tweet N], bold headers, and --- separators

小红书 counter stops at --- but template uses ## 配图（单独上传...）section. Twitter counter claims to split on --- but only regex-splits bold **Tweet...** headers.

---

### [SR-20260618-014] [MEDIUM] AGENT.md — Architecture doc claims all skills use progressive disclosure, but publish/archive are monoliths

- **Category:** Feature
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Split post-publish and post-archive into 01-* playbooks like post-new/post-review; keep SKILL.md as map only

AGENT says every skill has SKILL.md map plus 0X-*.md playbooks. post-publish/SKILL.md contains whole workflow; post-archive/SKILL.md contains nine steps plus destructive shell snippets.

---

### [SR-20260618-015] [MEDIUM] .claude/skills/post-new/08-user-review.md — Later pipeline steps hard-code all four platforms despite active-platform support

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Render review, final summary, and archive tables from brief.md platforms: or registry default

06-spawn.md correctly says only active platforms required, but 08-user-review.md, 10-summary.md, and post-archive/SKILL.md show fixed rows for 小红书/微信/知乎/Twitter, making single-platform runs look incomplete.

---

### [SR-20260618-016] [LOW] README.md — README still says codex-image-in-cc powers takeover-image after move to raw Codex CLI

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Remove the stale acknowledgment or rewrite it as historical inspiration, not a current dependency

README prerequisites say no third-party plugin required, but Acknowledgments says codex-image-in-cc bridges imagegen into Claude Code and powers takeover-image.

---

### [SR-20260618-017] [LOW] .claude/skills/post-new/SKILL.md — Resume-by-slug documented but command signature and Step 01 parser only accept repo identifiers

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Change arg hint to <github-url|slug> [platform] and document a pre-Step-01 dispatcher detecting existing slugs

SKILL.md says re-invoking /post-new <slug> resumes work; 01-clone.md only validates GitHub URL forms or owner/repo, so article slugs like owner--repo__topic are invalid unless undocumented routing happens first.

---

### [SR-20260618-018] [LOW] config/preferences.md — Preferences say style tracking is manual, but archive now updates style automatically

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Update preference text to match post-archive, or make it an explicit opt-out/opt-in setting

config/preferences.md says published articles are manually added to style references; AGENT and post-archive/SKILL.md say style/published/ and style/profile.md are updated automatically.

---

### [SR-20260618-019] [HIGH] .claude/settings.json — Stale codex-image-in-cc plugin enabled and Skill(codex-image:*) permissions remain — image path now uses Agent(takeover-image)

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Remove "codex-image@codex-image-in-cc" from enabledPlugins and drop all Skill(codex-image:*) permission entries; keep Agent(takeover-image)

enabledPlugins declares "codex-image@codex-image-in-cc": true and permissions allow Skill(codex-image:generate/edit/status). The project moved to direct codex exec --full-auto via takeover-image.md. Dead config; may cause startup warnings or confusion about the active image path.

---

### [SR-20260618-020] [HIGH] README.md — Acknowledgments (L41) still credit codex-image-in-cc as powering takeover-image, contradicting L27 which says 'no third-party plugin required'

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Drop or rewrite L41 to credit Codex CLI's built-in imagegen skill; takeover-image spawns codex exec --full-auto directly

L41: 'codex-image-in-cc by KingGyuSuh ... Powers the takeover-image agent.' But L27 of the same README states the takeover-image agent triggers Codex's built-in imagegen with 'no third-party plugin required.' Internal contradiction within README plus drift from actual takeover-image.md implementation.

---

### [SR-20260618-021] [HIGH] .claude/skills/post-review/SKILL.md — --full-review hard rule (L57) says it adds 'Codex' as 3rd reviewer, but 02-reviewers.md configures Claude Opus

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Change 'adds Codex as a 3rd reviewer' (SKILL.md L57) and 09-review.md L39 to 'adds Claude Opus'

post-review/SKILL.md L57 and post-new/09-review.md L39 both say --full-review adds Codex. But 02-reviewers.md L14/L25/L28 append {provider: claude, model: opus} and say '追加 Opus 变 3 个'. Two SKILL.md map surfaces stale after Codex→Opus swap; would mis-route the 3rd reviewer in docs/expectations.

---

### [SR-20260618-022] [HIGH] .claude/skills/post-archive/SKILL.md — Archive step checks ongoing/<slug>/<slug>.docx but export_article.py writes <title>.docx (H1-derived) — exported Word file silently skipped

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Use a glob: copy ongoing/<slug>/*.docx, since the filename is derived from the article H1, not the slug

SKILL.md L92: [ -f ongoing/<slug>/<slug>.docx ] && cp ... But export_article.py L53: OUT_FILE = ARTICLES/slug/f"{_safe_title}.docx" where _safe_title comes from the H1 heading. The fixed <slug>.docx name will never match, so the .docx the skill promises to archive (L22/L75/L78) is never copied.

---

### [SR-20260618-023] [MEDIUM] AGENT.md — Claims every skill uses progressive disclosure (SKILL.md map + 0X-*.md), but post-archive and post-publish are monolithic with zero sub-files

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Qualify the statement to note post-archive and post-publish remain monolithic, or decompose them

AGENT.md L11: 'Each uses progressive disclosure: SKILL.md is the map, 0X-*.md sub-files are the playbook.' Only post-new (01-10) and post-review (01-06) follow this. post-archive/SKILL.md and post-publish/SKILL.md have no 0X sub-files. Documentation overstates uniformity.

---

### [SR-20260618-024] [MEDIUM] templates/_platform-registry.md — Registry (declared SSOT for platform metadata) has no title_limit column; xiaohongshu's ≤20字 title cap is duplicated across 3 files

- **Category:** Feature
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Add a title_limit column to the registry and have templates/brief-gate/publish reference it

The ≤20字 xiaohongshu title limit is hardcoded in templates/xiaohongshu.md frontmatter, post-publish/_platforms/xiaohongshu.md, and post-new/05-brief-gate.md. Body char_limit lives in the registry but title_limit does not — a surviving SSOT gap requiring 3 edits to change.

---

### [SR-20260618-025] [LOW] .claude/skills/post-review/05-images.md — References 'takeover image-edit' but the registered agent is named takeover-image — name won't resolve

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Change to 'spawn a takeover-image agent with an edit prompt'

05-images.md L32 instructs 'use takeover image-edit to create a new version.' No agent by that name exists; the agent is .claude/agents/takeover-image.md. Stale terminology from the pre-takeover image path.

---

### [SR-20260618-026] [LOW] templates/xiaohongshu.md — Body ≤1000字 limit hardcoded in template while registry already declares char_limit: ≤1000 — redundant literal

- **Category:** Feature
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Reference the registry for the hard limit instead of restating the number

Template hardcodes 800-1000 / ≤1000字; registry already owns char_limit ≤1000. Per-platform 800-1000 craft guidance is fine, but the hard cap should visibly delegate to _platform-registry.md so a registry change doesn't leave stale numbers.

---

### [SR-20260618-027] [INFO] .claude/skills/post-archive/SKILL.md — Monolithic 9-step SKILL.md with no progressive-disclosure decomposition, unlike post-new/post-review

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Decompose into SKILL.md map + 0X-*.md sub-files (identify/verify/assemble/style/cleanup/postmortem/report)

Clear sequential 9-step workflow maps naturally to sub-files; current single file is re-read in full on every invocation and breaks the AGENT.md-stated pattern.

---

### [SR-20260618-028] [INFO] .claude/skills/post-publish/SKILL.md — Monolithic SKILL.md lacks 0X sub-file decomposition (platform rules already split into _platforms/)

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Decompose the 5 main steps into 0X-*.md for consistency with post-new/post-review

_platforms/*.md are already decomposed; the main step list (identify/verify-images/publish-prep/clipboard/checklist) is not, leaving post-publish a partial exception to the architecture principle.


## Review 2026-06-18 (follow-up)

## Review 2026-06-18 (session) — diff review

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): OK

### Confirmed findings

---

### [SR-20260618-029] [MEDIUM] .claude/skills/post-publish/export_article.py — Inline $...$ regex misfires on dollar-sign prose (currency)

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Tighten the inline pattern (non-space-adjacent delimiters) or detect currency context.

The new alternative `\$[^$]+\$` greedily spans any text between two dollar signs on a line. Prose like 'plans cost $5 and $10' captures '$5 and $10' and renders it in code font. Found independently by both reviewers (also SR-005).

---

### [SR-20260618-030] [LOW] .claude/skills/post-publish/export_article.py — Unterminated $$ block consumes the rest of the document

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** On EOF without closing $$, fall back to normal paragraphs instead of swallowing everything.

If the closing $$ is missing, the while loop runs to EOF and every remaining line is emitted as one verbatim math block — content silently vanishes. Found independently by both reviewers (also SR-006).

---

### [SR-20260618-031] [INFO] .claude/skills/post-publish/export_article.py — add_code_block ignores its lang argument

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Branch on lang, or drop the unused 'math' label.

`add_code_block(doc, code, lang='')` never uses lang; the 'math' tag implies styling that does not occur.

---

### [SR-20260618-032] [INFO] .claude/skills/post-publish/_platforms/wechat.md — Clipboard contract is doc-only, not script-enforced

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Confirm SKILL.md matches the new full-markdown guidance.

Clipboard population is a manual /post-publish step (PowerShell Set-Clipboard), not export_article.py — by design. Doc consistency only.

---

### [SR-20260618-033] [HIGH] .claude/skills/post-publish/export_article.py — Inline `$...$` regex corrupts prose with currency

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Add a heuristic distinguishing formulas from currency.

Duplicate of SR-001, surfaced by the second reviewer — high signal. `$` as currency is common in tech writing (pricing).

---

### [SR-20260618-034] [HIGH] .claude/skills/post-publish/export_article.py — Unterminated `$$` block swallows the rest of the document

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** If closing `$$` never found, treat opener as literal text and fall through.

Duplicate of SR-002, surfaced by the second reviewer — high signal.

---

### [SR-20260618-035] [LOW] .claude/skills/post-publish/export_article.py — `$$$$` emits an empty math code block

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Require non-empty inner content before emitting.

`$$$$` passes len>2 and endswith('$$'), producing an empty block. Cosmetic.

---

### [SR-20260618-036] [MEDIUM] .claude/skills/post-publish/_platforms/wechat.md — Full-markdown clipboard flow not backed by code change

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Verify the playbook step produces full-markdown clipboard output.

Clipboard is populated manually per /post-publish Step 4 — by design. Doc consistency only.

---

### [SR-20260618-037] [MEDIUM] .claude/skills/post-publish/_platforms/zhihu.md — Same doc/impl note as wechat.md

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Keep both platform docs in sync with actual behavior.

Mirror of SR-008. Clipboard is manual; by-design.

---

### [SR-20260618-038] [INFO] .claude/agents/takeover-image.md — Three-layer spec duplicated across two files

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Extract the 前景/后景/文字排版 spec into a shared `_`-prefixed reference file.

07-images.md and takeover-image.md both contain the spec; AGENT.md favors single-source-of-truth. Risks drift on future edits.
