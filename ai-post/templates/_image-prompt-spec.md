# Three-Layer Image Prompt Spec (SSOT)

Single source of truth for the three-layer composition every generated image must satisfy. Referenced by `.claude/skills/post-new/07-images.md` (manifest authoring) and `.claude/agents/takeover-image.md` (generation). Never restate these layers elsewhere — link here.

Every `AI Prompt` MUST describe three distinct, explicitly-labeled layers so the image is rich and never monotone — a flat single-color background is a defect. If a prompt arrives without all three, expand it before generating.

1. **前景 (Foreground)** — the focal subject(s): diagram nodes, code block, magnifying glasses, etc. Sharp, high-contrast — the eye lands here.
2. **后景 (Background)** — a textured, layered backdrop that fills the whole frame: gradients, depth, ambient glow, subtle grid/circuitry/particle/bokeh motifs, soft vignetting. NEVER a flat solid fill; no large region may read as empty.
3. **文字排版 (Text layout)** — exact characters to render, their position (top/center/etc.), hierarchy (title vs subtitle vs badge), font weight/style, and color. Follow the Text Rendering rules in `.claude/agents/takeover-image.md`.

Write each layer as a labeled clause inside the `AI Prompt`, e.g. `Foreground: …. Background: …. Text: ….`.
