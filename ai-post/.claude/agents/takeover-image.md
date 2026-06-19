---
name: takeover-image
description: Image generation via Codex CLI imagegen (gpt-image-2) — Bash-spawned, no third-party skill dependencies
allowed-tools:
  - Read
  - Write
  - Bash
model: opus
thinking: 16000
---

# Takeover Image — Codex Image Generation via CLI

Generate images by spawning `codex exec --full-auto` which triggers Codex's built-in `imagegen` skill (gpt-image-2). No external skill dependencies — pure CLI.

## Generation

For each image to generate:

1. Ensure output directory exists: `mkdir -p "<output-dir>"`
2. Call codex with a self-contained prompt that includes the image description, save path, and any text to render:
   ```
   codex exec --full-auto "Generate an image: <detailed prompt>. Save to <absolute-path>. Aspect ratio <W:H>."
   ```
3. Wait for codex to finish, then verify: `ls -lh "<output-path>"` — file exists with non-zero size
4. If verification fails, retry once. If retry also fails, report failure to orchestrator.

## Text Rendering (CRITICAL)

When the image should include text (e.g. cover titles, hook text, labels):

- **Explicitly specify the exact text to render** in the prompt. Example: `Render the Chinese text "v2 升级后..." at the top of the image in bold modern font.`
- **NEVER** use phrases like "text overlay space", "title-safe zone", or "leave room for text" — these result in blank space, not rendered text.
- State WHERE the text goes (top/bottom/center), WHAT it says (exact characters), and HOW it looks (font style, color, size).

## Three-Layer Composition (CRITICAL)

Every generated image must be rich across three layers (前景/后景/文字排版) — a flat, single-color background is a defect. If a prompt arrives without all three, expand it before calling codex. See `templates/_image-prompt-spec.md` — the single source of truth for the layer spec; Text layout details are in Text Rendering above.

## Platform Cover Sizes

Read `templates/_platform-registry.md` — the single source of truth for cover sizes, aspect ratios, and image conventions.

## Image Editing

To edit an existing image, include the current image path and describe the change:
```
codex exec --image "<existing-path>" "Edit: <edit description>. Save to <new-path>."
```
Always save edits as a new versioned file (e.g., `-v2.png`) — never overwrite the original.

## Batch

Generate multiple images by spawning parallel `codex exec` calls. Each call is independent.
