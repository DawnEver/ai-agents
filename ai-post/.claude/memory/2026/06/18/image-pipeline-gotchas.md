---
name: image-pipeline-gotchas
description: takeover-image / codex imagegen gotchas — sandbox can't write to images/, credit exhaustion, raw-output recovery, mandatory three-layer prompt
metadata:
  type: retrospect
---

# Image Pipeline Gotchas (takeover-image + codex imagegen)

Session: regenerated all 8 images for `dawneever--cc-market__sharp-review` as v2 (v1 backgrounds were too flat/monotone).

## Three-layer prompt rule (NEW, now enforced)
Every image `AI Prompt` MUST describe three layers — a flat single-color background is a defect:
1. **前景 (Foreground)** — focal subject, sharp/high-contrast.
2. **后景 (Background)** — textured, layered backdrop filling the frame (gradient, depth, glow, grid/circuit/particle/bokeh, vignette). Never flat; no large empty region.
3. **文字排版 (Text layout)** — exact characters, position, hierarchy, weight, color.
Codified in `.claude/skills/post-new/07-images.md` (manifest spec) and `.claude/agents/takeover-image.md` (generation). Write each layer as a labeled clause: `Foreground: … Background: … Text: …`.

## Gotcha: codex sandbox can't write to images/
codex `--sandbox workspace-write` denies writes to the sibling `images/` dir (PermissionError 13). It saves the PNG into its workspace (`2-draft/v<N>/images/`) or `~/.codex/generated_images/<session>/`. The agent MUST then locate the produced PNG and copy it to the target path, then verify with `ls -lh`. Leaves stray fallback copies in `2-draft/v<N>/images/` — clean them up after.

## Gotcha: agent "comes to rest" without copying
A takeover-image agent can finish its turn while codex is still running detached ("waiting for monitor to notify"), so the file never gets copied. Always verify the target path on disk after the notification — don't trust the agent's self-report. If missing, the raw output is likely in `~/.codex/generated_images/`; identify it by dimensions (e.g. the 3:4 cover vs other 16:9 raws) and copy it in rather than regenerating.

## Gotcha: codex credit exhaustion
gpt-image-2 via codex burns workspace credits; ~8 images exhausted them. Error: `Your workspace is out of credits`. Not workaroundable locally — needs OpenAI workspace top-up before any further generation. Batch generation can drain mid-run; the early images succeed, later ones fail.

## Deterministic vs gpt-image-2 render
codex sometimes renders diagrams deterministically (PIL/vector drawing) instead of gpt-image-2 — precise layout + exact text, but a different (flatter) visual style than the painterly gpt-image covers. Fine for technical diagrams; watch style consistency across a set.
