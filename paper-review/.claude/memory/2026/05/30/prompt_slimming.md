---
name: prompt-slimming
description: After 2-round 锐评, slashed ~90 lines of instruction context — deduped AGENT.md↔SKILL.md overlap, extracted inline templates, merged prompt contracts
metadata:
  type: project
---

Reduced paper-review prompt bloat after a 2-round 锐评 analysis. Net -90 lines of instruction context (192 deleted, 102 added across 7 files).

**Why**: AGENT.md and SKILL.md had ~40% semantic overlap (pipeline steps, core principles, routing). Three sub-step files (02-literature, 04-fanout, 05-aggregate) embedded 30-line output templates as inline markdown instead of referencing standalone template files. Two prompt contracts in 04-fanout.md repeated the same output format spec.

**What changed**:
- AGENT.md: 105→66. Removed 26-line Pipeline Flow ASCII diagram (duplicated SKILL.md table), condensed Architecture diagram 14→3 lines, condensed Model Routing to a 4-line table.
- SKILL.md: 74→65. Merged 10 hard rules → 8 (removed "read summary.md first" and "polisher never invents" which are in AGENT.md). Compressed --restart-from/--reingest notes 8→1 line.
- 01-ingest.md: 96→86. Extracted 7-row failure triage table → templates/ingest-errors.md.
- 02-literature.md: 112→82. Extracted 31-line output template → templates/literature-template.md.
- 04-fanout.md: 79→78. Merged separate Sonnet and Takeover prompt contracts into a unified "all reviewers" + "router-specific" structure. Line count barely changed but eliminated the risk of the two contracts diverging.
- 05-aggregate.md: 86→57. Extracted 27-line output template → templates/critiques-template.md.
- README.md: 37→64. Expanded with pipeline table, commands, routing, design notes.

New files: templates/literature-template.md (35), templates/critiques-template.md (33), templates/ingest-errors.md (11).

**Runtime impact**: orchestrator context per step dropped from ~290→~220 lines. AGENT.md permanent load dropped from 105→66 lines (37% reduction).

**How to apply**: When adding new sub-step files, keep templates in templates/ and reference by path. When adding rules, add to SKILL.md (execution) or AGENT.md (principles), never both. See [[prompt-slimming]] for the analysis approach.
