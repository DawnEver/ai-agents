---
name: sharp-review-2026-06-17
description: Sharp review findings — 29 total
metadata:
  type: project
---

## Review 2026-06-17 (session) — architecture survey (架构锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): OK
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260617-001] [MEDIUM] ai-post/templates/_platform-registry.md — Platform registry declared authoritative but platform facts hardcoded across templates, skills, and publish rules.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make registry machine-readable or remove copied values so consumers resolve platform metadata from one place.

Character limits and emoji density repeated in template frontmatter, agent mapping repeated in post-new/06-spawn.md, aspect ratios repeated in post-new/07-images.md and post-review/05-images.md, publish URLs/limits repeated in post-publish/_platforms. Already drifting in WeChat cover handling.

---

### [SR-20260617-002] [HIGH] ai-post/.claude/skills/post-new/07-images.md — WeChat cover aspect ratio is split between 2.35:1 and 16:9 across files.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Align every WeChat cover reference to the registry value, or change the registry if 16:9 is intended.

_platform-registry.md and post-publish/_platforms/wechat.md say 2.35:1, while templates/wechat.md, post-new/07-images.md, and post-review/05-images.md instruct 16:9. v3 image manifest notes the WeChat PNG is still a 16:9 render.

---

### [SR-20260617-003] [HIGH] ai-post/.claude/skills/post-new/08-user-review.md — Final-confirm branch can set review_completed true without actually running post-review.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Only set finalized:true after a real latest review-verdict.md exists; otherwise route to Step 09.

File says 三方会审 is mandatory, but its 'If user confirms final' path sets finalized:true and review_completed:true before Step 10, creating a documented bypass path.

---

### [SR-20260617-004] [HIGH] ai-post/.claude/skills/post-publish/SKILL.md — Publish gate trusts brief.md finalized:true and does not verify the latest review verdict.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Require latest 2-draft/vN/review-verdict.md and reject platforms marked failing before export.

Because finalized/review_completed can be stale or wrongly set, post-publish should validate the actual review artifact, not just brief.md state.

---

### [SR-20260617-005] [HIGH] ai-post/.claude/skills/post-review/02-reviewers.md — 三方会审 quorum model contradicts its own synthesis rules.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Run at least two reviewers per identity by default, or rewrite synthesis to match single-reviewer semantics.

post-review/SKILL.md and post-new/09-review.md promise two reviewers per identity by default, but 02-reviewers.md and 03-execution.md use pickStrategy seed-mod to run only one backend. 04-synthesis.md then depends on findings from >=2 reviewers, which cannot exist in default mode.

---

### [SR-20260617-006] [MEDIUM] ai-post/.claude/skills/post-new/06-spawn.md — Single-platform generation supported upstream but spawn verification requires all four platform files.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Validate only the active platforms recorded in brief.md, defaulting from the platform registry.

01-clone.md and 05-brief-gate.md allow one platform or Twitter-only, while 06-spawn.md says v1 baseline must contain all 4 platform files, blocking valid partial runs.

---

### [SR-20260617-007] [MEDIUM] ai-post/.claude/skills/post-new/05-brief-gate.md — Title skip/Twitter-only path conflicts with writer rule that titles must come from brief.md.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Define an explicit fallback title contract in brief.md or remove the skip path.

05-brief-gate.md allows titles_confirmed: skipped and says writers derive their own titles, but 06-spawn.md and _writer-base.md say to read ## Selected Titles and not invent a title.

---

### [SR-20260617-008] [MEDIUM] ai-post/.claude/agents/_writer-base.md — Draft image rules conflict with platform template checklists.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split draft-time placeholder rules from final-time image-reference checks.

_writer-base.md tells writers to use [IMAGE: ...] placeholders and never markdown image refs, while platform templates require cover/content markdown refs and post-publish parses only ../../images refs. Generation self-checks are impossible at v1.

---

### [SR-20260617-009] [MEDIUM] ai-post/.claude/agents/twitter-writer.md — Twitter writer wrapper says bilingual EN+CN while the Twitter template is English-only.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the agent description to English-only; keep language policy solely in templates/twitter.md.

The wrapper advertises bilingual threads, but templates/twitter.md repeatedly bans Chinese lines and requires pure English tweets.

---

### [SR-20260617-010] [MEDIUM] ai-post/.claude/agents/zhihu-writer.md — Zhihu writer is not a thin wrapper; it duplicates core template rules.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Keep the wrapper to routing/angle setup and reference templates/zhihu.md sections instead of restating them.

The wrapper repeats required mechanism deep-dive, 1-3 mechanisms, config/file evidence, no feature list, and comparison table rules already owned by templates/zhihu.md.

---

### [SR-20260617-011] [MEDIUM] ai-post/.claude/skills/post-archive/SKILL.md — Archive contract is internally inconsistent and not progressively disclosed.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split post-archive into 0X playbooks and define exactly what survives archive.

Description says it moves the entire ongoing slug, Step 3 says raw 2-draft is not preserved and only final output matters, yet archives contain extras like docx/review-verdict. At ~194 lines, SKILL.md does too much.

---

### [SR-20260617-012] [LOW] ai-post/AGENT.md — Documented committed layout is too broad for style/.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document style/profile.md and style/published/ as committed, style/private/ as gitignored.

AGENT.md says 'style/ and config/ are committed', but .gitignore excludes style/private/ and the pipeline depends on style/private/author-identity.md for persona.

---

### [SR-20260617-013] [LOW] ai-post/.claude/skills/post-new/10-summary.md — Final confirmation points to ongoing/<slug>/images.md, but the manifest lives under 2-draft/vN/images.md.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the reference to the latest 2-draft/vN/images.md resolved through the version chain.

post-new/07-images.md defines images.md as versioned beside drafts, and post-review copies it forward. Step 10's summary path is a stale/broken cross-file reference.

---

### [SR-20260617-014] [HIGH] .claude/agents/twitter-writer.md — Agent description says 'bilingual EN+CN threads' but templates/twitter.md enforces 'English ONLY (no Chinese)' on 5 lines — contradiction with template SSOT

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change agent description to 'English-only threads, high-density info, structured tweet arc'

twitter-writer.md:3 declares 'bilingual EN+CN threads' but the template (SSOT) bans Chinese on lines 12, 29, 55, 88, and checklist 126. One is wrong regardless of which the writer follows.

---

### [SR-20260617-015] [HIGH] templates/_platform-registry.md — Character limits duplicated: each platform template has character_limit in frontmatter while _platform-registry.md also declares char_limit — SSOT violated

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove character_limit from individual template frontmatters; read char limits only from _platform-registry.md

xiaohongshu.md:3 has 800-1000 while registry says ≤1000 (drift). Others match. A char-limit change requires updating 2 files.

---

### [SR-20260617-016] [HIGH] .claude/skills/post-publish/_platforms/ — Publish URLs duplicated identically across _platform-registry.md (16-19) and all four post-publish/_platforms/<platform>.md files

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove Publish URL sections from _platforms/ files; reference templates/_platform-registry.md in post-publish Step 3

All 4 URLs exist byte-for-byte in both locations. The _platforms/ files already reference the registry for cover ratios but not for URLs.

---

### [SR-20260617-017] [HIGH] .claude/skills/post-review/01-identities.md — Review finding JSON schemas defined in 01-identities.md and hardcoded again in 03-execution.md as args.findingSchema — dual maintenance

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make 03-execution.md reference 01-identities.md schemas instead of re-inlining the JSON

Identity A/B schemas appear both as docs in 01-identities.md and as JSON passed to Workflow() in 03-execution.md. Adding a dimension requires changing both.

---

### [SR-20260617-018] [HIGH] AGENT.md — Directory layout omits style/published/<platform>/ created by post-archive Step 4, which holds the committed style reference corpus

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add style/published/<platform>/ to the AGENT.md directory tree

AGENT.md shows style/profile.md but not style/published/. post-archive writes committed text-only articles there as the corpus profile.md accumulates from. Contributors can't discover it.

---

### [SR-20260617-019] [MEDIUM] .claude/skills/post-new/06-spawn.md — Agent-to-platform mapping table duplicated in 06-spawn.md (7-14) and _platform-registry.md agent column

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove the hardcoded table; instruct to read _platform-registry.md for the authoritative mapping

06-spawn.md already references the registry as authoritative in text, then hardcodes the same table — pure drift risk.

---

### [SR-20260617-020] [MEDIUM] README.md — README says image gen needs 'codex-image-in-cc' plugin but takeover-image.md uses bare 'codex exec --full-auto' with 'no third-party skill dependencies' — stale

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update README prerequisites to reflect direct codex exec usage; remove the stale plugin reference

README:28 and settings.json reference the plugin, but takeover-image.md:3 says no third-party deps and uses bare CLI. Docs out of sync with the agent.

---

### [SR-20260617-021] [MEDIUM] .claude/skills/post-archive/SKILL.md — post-archive/SKILL.md is a 195-line monolith with 9 inline steps — only pipeline skill without progressive-disclosure sub-files

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split into SKILL.md map + 01-verify/02-move/03-style-persist/04-style-accumulate sub-files

post-new has 10 sub-files, post-review has 6, post-archive has zero — inconsistent with the stated progressive-disclosure design.

---

### [SR-20260617-022] [MEDIUM] .claude/skills/post-publish/SKILL.md — post-publish SKILL.md runs 5 steps inline with no 0X-*.md workflow sub-files; its _platforms/ files are metadata, not workflow steps

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Restructure with 01-05 workflow sub-files for consistency with post-new/post-review

_platforms/ is per-platform publish metadata (analogous to templates/), not the 0X workflow decomposition the other pipeline skills use.

---

### [SR-20260617-023] [MEDIUM] .claude/agents/takeover-image.md — takeover-image agent lacks model and thinking frontmatter that all four writer agents specify (model: opus, thinking: 16000)

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add model and thinking frontmatter (or document the intentional omission)

Inconsistent agent metadata means it inherits session defaults unpredictably.

---

### [SR-20260617-024] [MEDIUM] .claude/skills/post-review/SKILL.md — Phase numbering inconsistent: table groups Setup(01,02)/1-2(03)/3-5(04)/6(05)/7(06); sub-file headers and body text disagree

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Number phases 1-7 sequentially across the table and sub-file headers

SKILL.md body says 'Phase 1-2 run per platform' but the table maps Phase 1-2 to 03-execution; 'Setup' row has no phase number. Headers across sub-files use mismatched labels.

---

### [SR-20260617-025] [MEDIUM] templates/审校checklist.md — 审校checklist.md is an orphan — unreferenced by any skill/agent/template; duplicates banned-phrase and anti-AI grading now done by post-review

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Wire it into post-new/08-user-review.md as an optional supplement, or remove it

Only referenced by a stale memory file. Risks misleading a user into manual review instead of the mandatory 三方会审.

---

### [SR-20260617-026] [LOW] .claude/skills/post-publish/_platforms/zhihu.md — Cover aspect ratios partially duplicated in _platforms/ files — inline value alongside 'see _platform-registry.md'

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Remove inline ratios; rely solely on the registry reference

zhihu/wechat/twitter inline ratios next to the reference; xiaohongshu inlines 3:4 with no reference. Inline values can go stale.

---

### [SR-20260617-027] [LOW] AGENT.md — Platform Agents table lists takeover-image as a writer-agent row though it has no platform — breaks the table's semantic model

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Split into Writer Agents vs Utility Agents, or add a Type column

takeover-image's Platform cell says 'Image generation via Codex', not a platform name, under a 'Agent | Platform' header implying all entries write articles.

---

### [SR-20260617-028] [LOW] .claude/skills/post-review/02-reviewers.md — Sharp-review workflow path resolution has no error handling for when both plugin paths are absent — cryptic failure

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Abort with 'sharp-review plugin not found — install cc-market/sharp-review' before the Workflow() call fails

Two resolution paths described but no failure case; absent plugin yields a file-not-found error instead of an actionable message.

---

### [SR-20260617-029] [LOW] .gitignore — No .DS_Store entry — macOS metadata in committed dirs like style/ could be accidentally committed

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add .DS_Store to .gitignore

style/.DS_Store and root .DS_Store exist on disk; style/ is committed so its .DS_Store shows as untracked.
