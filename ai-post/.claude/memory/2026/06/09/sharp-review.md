---
name: sharp-review-2026-06-09
description: Sharp review findings — 26 total
metadata:
  type: project
created: 2026-06-09
accessed: 2026-06-09
tier: short
---

## Review 2026-06-09 (session) — current branch

### Reviewer Status
- Reviewer A (Codex, via takeover): OK
- Reviewer B (DeepSeek, via takeover): OK
- Reviewer C (Claude, native): OK

### Confirmed findings

---

### [SR-20260609-001] [MEDIUM] .claude/memory/.claude/rules/MEMORY.md — Redundant nested .claude/ directory inside memory/ with template-only MEMORY.md that conflicts architecturally with the real index at .claude/rules/MEMORY.md

- **Category:** Bug
- **Module:** memory-system
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Move the three-tier memory documentation comment into .claude/rules/MEMORY.md or a dedicated docs file; remove the nested .claude/memory/.claude/ path

File creates path .claude/memory/.claude/rules/MEMORY.md containing only HTML comment documentation about the memory system. The actual memory index lives at .claude/rules/MEMORY.md. Having .claude/ nested inside memory/ breaks the convention that .claude/ is a top-level config directory, and tools scanning for rules may pick up the wrong file.

---

### [SR-20260609-002] [MEDIUM] ~~README.md~~ AGENT.md — Pipeline flow and command table disagree on whether publish + archive are part of /post-new

- **Category:** Bug
- **Module:** docs
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Align README command table with AGENT.md: change 'clone through archive' to 'clone through 3-final' and clarify that publish + archive are /post-publish and /post-archive respectively

The README pipeline diagram shows /post-new ending with '→ publish → archive', but the AGENT.md command table correctly says /post-new ends at '→ 3-final'. The README command table further claims '/post-new' is 'Full pipeline — clone through archive'. These are three mutually inconsistent descriptions of the same command's scope.

---

### [SR-20260609-003] [LOW] .claude/skills/post-new/06-images.md — Agent() pseudo-syntax is not real Claude Code syntax for spawning subagents

- **Category:** Bug
- **Module:** post-new
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Replace Agent({subagent_type: ...}) with actual TaskCreate tool invocation format or a natural-language instruction like 'Spawn a takeover-image subagent with...'

The Phase 2 Batch 1 instructions use Agent({subagent_type: "takeover-image", description: ..., prompt: ...}) which resembles JavaScript but is not a valid Claude Code tool call. While Claude reading this as natural language would likely interpret the intent correctly, explicit pseudo-syntax in documentation can lead to confusion if someone tries to copy-paste or automate it.

---

### [SR-20260609-004] [LOW] .claude/agents/takeover-image.md — allowed-tools YAML field uses comma-separated string instead of YAML list

- **Category:** Bug
- **Module:** agents
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Change to YAML list format: allowed-tools: [Skill(codex-image:generate), Skill(codex-image:edit), Skill(codex-image:status), Read, Write, Bash]

The current value is a single quoted string 'Skill(codex-image:generate),Skill(codex-image:edit),...' rather than a YAML list. If the tool permission system splits on commas, this works accidentally; if it expects a proper list type, all tool permissions silently fail and the agent cannot run any tools.

---

### [SR-20260609-005] [LOW] .claude/settings.json — New Skill permissions added but no Skill(takeover-image) or Agent permission for spawning the takeover-image agent

- **Category:** Bug
- **Module:** settings
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Verify whether Skill(takeover-image) or an Agent permission is needed for the orchestrator to spawn takeover-image subagents; if so, add it alongside the codex-image Skill permissions

settings.json adds Skill(codex-image:generate/edit/status) for the takeover-image agent itself, but the orchestrator (post-new) needs to be able to spawn the takeover-image agent. If the spawn mechanism requires a Skill permission for the agent name, this is missing.

---

### [SR-20260609-006] [INFO] .claude/skills/post-new/06-images.md — Cost estimates labeled as 'rough baseline — measure to calibrate' but no mechanism described for measuring actual tokens

- **Category:** Feature
- **Module:** post-new
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Add a one-liner on how to check actual token usage (e.g., 'check Codex CLI logs or app-server telemetry after each batch')

The document repeats 'measure actuals to calibrate' in three places without telling the user how to actually measure token consumption. This makes the cost-awareness good practice but incomplete.

---

### [SR-20260609-007] [HIGH] .claude/memory/.claude/rules/MEMORY.md — References 3 non-existent scripts (touch-memory.js, prune-memory.js, compact.js) — silent failures if the memory system is ever invoked

- **Category:** Bug
- **Module:** memory system
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Either commit the referenced scripts or remove the comment block describing an unimplemented tier system

The HTML comment block describes a three-tier memory system with promotion, demotion, pruning, and compaction — all gated on scripts that appear nowhere in this diff or repo. Any agent or automation that tries to follow these instructions will hit 'command not found' errors. This is architecture fiction.

---

### [SR-20260609-008] [HIGH] .claude/skills/post-new/06-images.md — Agent({}) syntax has no known implementation — fabricated pseudo-code that cannot execute

- **Category:** Bug
- **Module:** image generation
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Replace with the actual subagent spawn mechanism for the target platform, or document that this is pseudocode awaiting implementation

The sharp-review memory (SR-009, SR-004) claims Agent() pseudo-syntax was 'fixed' to Agent({}), but both are invented. Neither Claude Code nor Codex CLI has an Agent({subagent_type: ...}) API. The entire parallel spawn section in Phase 2 is non-functional placeholder that will silently do nothing if an orchestrator tries to execute it literally.

---

### [SR-20260609-009] [HIGH] .claude/memory/tasks/archive/2026-06.md — All 18 SR findings marked FIXED on 2026-06-06, but the sharp-review that supposedly found them is dated 2026-06-08 — timeline is impossible

- **Category:** Bug
- **Module:** memory system
- **Status:** WONTFIX
- **Confidence:** single-reviewer
- **Suggestion:** Correct dates: either the review happened on 06-06 (update sharp-review.md) or the fixes happened on 06-08 (update archive dates)

The archive claims bulk resolution on 2026-06-06. The sharp-review.md that catalogs these findings has created: 2026-06-08. The fixes predate the findings by 2 days. This undermines trust in the entire task tracking system and suggests fabricated process documentation.

---

### [SR-20260609-010] [HIGH] .claude/rules/MEMORY.md — References stamp-memory.js which does not exist in the diff — dead reference in the authoritative memory index

- **Category:** Bug
- **Module:** memory system
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Add stamp-memory.js to the repo or remove the comment claiming the index is auto-managed

The comment 'Managed by stamp-memory.js' claims automation, but the script is absent. The index was clearly hand-edited (inline created/accessed timestamps are manually duplicated from each file's frontmatter). This is documentation that lies about its own maintenance model.

---

### [SR-20260609-011] [MEDIUM] .claude/rules/MEMORY.md — Every index entry redundantly inlines created/accessed timestamps already present in each file's YAML frontmatter — guaranteed to drift out of sync

- **Category:** Performance
- **Module:** memory system
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Drop the inline timestamps; the index should only contain date, name, and one-line description — timestamps live in the files

Entries like '2026-06-08 sharp-review-2026-06-08 — created: 2026-06-08, accessed: 2026-06-08' duplicate frontmatter that's already in sharp-review.md. When frontmatter is updated (e.g. by the hypothetical touch-memory.js), this index will go stale immediately. Single source of truth violation.

---

### [SR-20260609-012] [MEDIUM] .claude/skills/post-new/06-images.md — Cost estimates ('~30K+', '~120K+', '~210-240K+') are presented as data but admit 'measure to calibrate' — guesses dressed as estimates

- **Category:** Feature
- **Module:** image generation
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Either remove specific numbers until measured, or label them explicitly as '[UNTESTED ESTIMATE]' with a TODO to replace after a real run

The same vague '~30K+' appears in takeover-image.md and 06-images.md. Multiplying uncertainty: 4× ~30K+ = ~120K+ means nothing. This creates a false sense of cost modeling that will mislead users making generation decisions.

---

### [SR-20260609-013] [MEDIUM] .claude/memory/.claude/rules/MEMORY.md — Confusing directory nesting: .claude/memory/.claude/rules/MEMORY.md mirrors .claude/rules/MEMORY.md — two files named MEMORY.md at different paths with different purposes

- **Category:** Bug
- **Module:** memory system
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Rename one: the memory-tier documentation should be MEMORY-TIERS.md or live in memory/README.md, not masquerade as another MEMORY.md in a nested .claude/rules/ path

One is an index of memories (.claude/rules/MEMORY.md), the other is documentation about how the memory system works (.claude/memory/.claude/rules/MEMORY.md). The nested .claude/rules/ inside .claude/memory/ is architecturally misleading — it suggests memory has its own rule subsystem when it's really just documentation.

---

### [SR-20260609-014] [MEDIUM] .claude/memory/tasks/tasks.md — A committed file whose sole content is '0 open tasks' and a sync timestamp — dead weight that serves no purpose when empty

- **Category:** Feature
- **Module:** task tracking
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Generate tasks.md on-demand from the archive rather than committing an empty stub; or auto-hide when count is 0

The file exists to be loaded 'on demand via MEMORY.md' but contains zero actionable information. When there are no open tasks, the index entry in MEMORY.md is noise. Either don't list it when empty, or don't commit the file at all.

---

### [SR-20260609-015] [LOW] .claude/skills/post-new/06-images.md — Phase 2 adds ~80 lines of agent orchestration logic to a manifest spec — file now mixes spec and execution instructions

- **Category:** Feature
- **Module:** image generation
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Extract Phase 2 into a separate skill file (e.g. 06b-image-generation.md) following the progressive disclosure pattern the project claims to use

At ~168 lines the file is under 400, but the content split is wrong: manifest specification and agent spawning/error-handling/cost-tracking are distinct concerns. The project's own architecture doc praises 'progressive disclosure split' — this file violates that principle.

---

### [SR-20260609-016] [LOW] README.md — Prerequisites section lists 'claude plugin install' command — not a standard Claude Code CLI command and may mislead users

- **Category:** Bug
- **Module:** documentation
- **Status:** WONTFIX
- **Confidence:** single-reviewer
- **Suggestion:** Verify the actual plugin installation command for the target Claude Code version and update, or link to the plugin's own install docs

The syntax 'claude plugin install codex-image@codex-image-in-cc --scope project' looks plausible but is unverified. The settings.json uses enabledPlugins which is also non-standard. If these are aspirational APIs, mark them as such.

---

### [SR-20260609-017] [LOW] .claude/memory/tasks/archive/2026-06.md — SR-005 and SR-016 are duplicates (both about cover size table duplication) listed as separate findings — inflates review count

- **Category:** Bug
- **Module:** task tracking
- **Status:** WONTFIX
- **Confidence:** single-reviewer
- **Suggestion:** Merge or cross-reference duplicate findings; the archive note '(same as 005)' on SR-010 and '(same root cause as 001)' on SR-013 are honest but should have been deduplicated before archiving

Four pairs of effectively duplicate findings (005/010/016, 001/013, 007/017, 004/009). An 18-finding review with 4 duplicates suggests the review process lacks triage before archiving. This inflates the task count artificially.

---

### [SR-20260609-018] [INFO] .claude/settings.json — enabledPlugins uses key format 'codex-image@codex-image-in-cc' — mixing plugin name and package reference in an unconventional way

- **Category:** Feature
- **Module:** configuration
- **Status:** WONTFIX
- **Confidence:** single-reviewer
- **Suggestion:** Use a standard format like {'name': 'codex-image', 'source': 'codex-image-in-cc'} or follow whatever schema the actual plugin system expects

The @-separated format is ambiguous: is 'codex-image-in-cc' a scope, a registry, or a package name? If the plugin system doesn't exist yet, mark this as speculative config.

---

### [SR-20260609-019] [HIGH] .claude/memory/.claude/rules/MEMORY.md — Orphan MEMORY.md at path that will never be loaded by Claude Code rules injection

- **Category:** Bug
- **Module:** memory system
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Delete this file. Claude Code only auto-injects .claude/rules/MEMORY.md at the project root. This deeply nested copy serves no purpose and creates ambiguity about which MEMORY.md is authoritative.

The file documents the three-tier memory system mechanics (promotion/demotion/prune) but lives at a path that no tooling reads. The comment block references scripts (touch-memory.js, prune-memory.js, compact.js) that don't exist in the repo. The actual rules file at .claude/rules/MEMORY.md references a different script (stamp-memory.js) that also doesn't exist. This looks like a mkdir accident during the memory directory restructure.

---

### [SR-20260609-020] [MEDIUM] .claude/rules/MEMORY.md — Memory index lost all human-readable descriptions; replaced with machine metadata already in frontmatter

- **Category:** Feature
- **Module:** memory system
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Restore one-line semantic summaries. Example: "— 6 systemic transition gaps found by diffing 2-draft vs 3-final edits; all 3 CN templates updated" instead of "— created: X, accessed: Y"

Old format: `[2026-06-02 transition-patterns] — 6 systemic transition gaps found...` New format: `[2026-06-02 transition-patterns] — created: 2026-06-02, accessed: 2026-06-02`. The new format is a regression — the timestamps are already in each file's YAML frontmatter. A reader scanning the index has no way to know which memory is relevant without opening every file. The index is supposed to help humans decide what to load; machine timestamps don't help.

---

### [SR-20260609-021] [MEDIUM] .claude/skills/post-new/06-images.md — Agent({}) pseudo-syntax is undocumented fiction; no such function exists in Claude Code

- **Category:** Bug
- **Module:** post-new pipeline
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Replace Agent({}) with actual Claude Code agent spawning syntax: either TaskCreate tool calls or Skill-based sub-agent dispatch with the correct parameter schema.

The Phase 2 section instructs orchestrators to write `Agent({ subagent_type: "takeover-image", description: "...", prompt: "..." })`. This is not a real Claude Code construct. The sharp-review (SR-009) claimed this was fixed by changing `Agent()` to `Agent({})`, but both are fictional. Real sub-agent spawning uses the TaskCreate deferred tool (name, description, prompt fields). Pseudo-code presented as executable instructions will cause confusion and failed agent spawns.

---

### [SR-20260609-022] [MEDIUM] .claude/skills/post-new/06-images.md — Cost estimates are uncalibrated filler masquerading as data

- **Category:** Performance
- **Module:** post-new pipeline
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Either measure actual token counts from a real run and publish those numbers, or drop the cost table entirely. The hedging ('rough baseline — measure to calibrate') acknowledges the data is unreliable while presenting it anyway.

The table claims ~120K tokens for 4 covers, ~90-120K for 3-4 content images, totaling ~210-240K. Meanwhile the text says batch of 5 variations = one agent turn (~30K), which contradicts the per-image math. If 5 variations in one turn costs 30K, then 4 covers should cost closer to 30K (one parallel batch), not 120K. The numbers don't add up internally and have no empirical basis.

---

### [SR-20260609-023] [LOW] .claude/agents/takeover-image.md — Cover size quick reference duplicates canonical table in 06-images.md, guaranteeing future drift

- **Category:** Bug
- **Module:** image generation
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Remove the 'Quick reference' line. If there's a canonical source, don't create a secondary reference — codebases don't sync natural language.

The agent says 'See 06-images.md for the canonical cover size table' then immediately provides its own quick reference (1024x1536, 1536x1024). This is two sources of truth for the same data. When someone changes dimensions in 06-images.md, the quick reference here will go stale.

---

### [SR-20260609-024] [LOW] .claude/skills/post-new/06-images.md — Image generation failure notes have no defined storage location or consumer

- **Category:** Bug
- **Module:** post-new pipeline
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Define where failure notes are stored (e.g., append to images.md manifest with a generated: failed flag per image) so post-publish can read them.

Error handling says 'note: ⚠️ <image-id> generation failed — needs manual creation' but never specifies the medium. post-publish auto-offers generation for missing images but has no way to distinguish 'not yet attempted' from 'attempted and failed twice'. Without structured failure tracking, post-publish will retry perpetually failed images.

---

### [SR-20260609-025] [LOW] README.md — Pipeline flow diagram misrepresents /post-new as encompassing publish and archive

- **Category:** Bug
- **Module:** documentation
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Change '→ publish → archive' to '→ /post-publish → /post-archive' to make it clear these are separate slash commands, not steps within /post-new.

The README shows a single continuous pipeline ending in '→ publish → archive'. But /post-publish and /post-archive are independent commands invoked separately. AGENT.md correctly shows them as downstream tools under /post-new, not as sequential steps within it. The README contradicts the authoritative AGENT.md architecture diagram.

---

### [SR-20260609-026] [INFO] .claude/skills/post-new/06-images.md — Codex CLI pre-check uses bare backtick code block that may confuse Markdown parsers

- **Category:** Bug
- **Module:** post-new pipeline
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Use a fenced code block (```bash) for the codex --version command, or inline code if it's just a single line for the orchestrator to execute.

The pre-check instruction shows `codex --version` inside a ```backtick``` Markdown code block, but the text around it says 'Before spawning any image agents, verify Codex CLI is installed:' followed by the code block. A fenced block would be clearer. Also, `command -v codex` is more portable than relying on `--version` exit codes for existence checks.
