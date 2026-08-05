# Phase 2 — Edit: the markdown iteration loop

This is where AI and human both work. The md is a normal text file: edit it, review it, `git diff` it. No Word needed.

## Rules of the working copy

1. **Keep anchors**: `<!-- ccxN -->` comments are the round-trip map. Never delete, renumber, or reorder them.
2. **Fill an answer slot**: write text on the same line as the anchor —
   `<!-- ccx16 --> **Calculations**` stays as-is; an empty slot `<!-- ccx17 -->` becomes `<!-- ccx17 --> My answer text`.
3. **Empty md cell/paragraph → cleared in the render.** To keep original content, don't touch that block.
4. **Add new content**: just write it without an anchor comment, after the block where it belongs. On render it's inserted after the previous anchored block. (After the first render/re-extract it gains its own `ccxN` anchor — that's normal, keep it.)
5. **Don't hand-write tables with a different column count** than the grid, unless you intend the row to be truncated/padded. For workplan-style step expansion, adding/removing **rows** is supported — the render resizes the table.
6. Inline formatting supported: `**bold**`, `*italic*`, `` `code` ``, `[text](url)`. Line-initial `#` in plain text will be parsed as a heading on render — escape or avoid.

## Comparison workflow (AI/human)

- Keep the md under git. Every iteration = one commit/diff — the review surface is the diff.
- For "what changed vs last version" questions: `git diff` the md, never the docx.
- Update the transcript header comment if the source file changes name.
