---
name: takeover-image
description: Image generation via Codex imagegen (gpt-image-2) — dispatch image tasks to Codex CLI's built-in image_gen tool
allowed-tools:
  - Skill(codex-image:generate)
  - Skill(codex-image:edit)
  - Skill(codex-image:status)
  - Read
  - Write
  - Bash
---

# Takeover Image — Codex Image Generation

Generate images by dispatching to Codex CLI's built-in `imagegen` skill (gpt-image-2).
This agent delegates image creation to Codex, complementing the `takeover` agent (which delegates text tasks to other models via MCP).

## Generation

For each image to generate:

1. Ensure the output directory exists: `Bash(mkdir -p, "<output-dir>")`
2. Call: `Skill(codex-image:generate, "<natural-language prompt>, save to <output-path> at <WxH>")`
3. Verify the output: `Bash(ls -lh, "<output-path>")` — confirm file exists and has non-zero size
4. If verification fails, retry once with the same prompt. If retry also fails, report the failure to the orchestrator.

The argument is passed verbatim to Codex's imagegen skill.
Output paths, sizes, quality, count, transparency, etc. are expressed as natural language.

**Batch variations**: Append `Generate N variations.` to the prompt to get multiple candidates in one agent turn.

**Skill call format**: `Skill(codex-image:generate, "<prompt>")` — the single string argument contains both the image description AND the save path/size instructions in natural language.

## Platform Cover Sizes

See `.claude/skills/post-new/07-images.md` — the canonical source for cover sizes and aspect ratios. No local copy; always read the manifest.

## Cost

Token consumption varies with prompt length, image resolution, and retries. Batch requests ("5 variations") cost one agent turn instead of 5. Measure actuals from your first few runs to calibrate.
