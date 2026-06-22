---
name: output-style-boundary
description: Email output style governs voice only — workflow/files/archiving stay in AGENT.md
metadata:
  type: project
---

# Output-style boundary

The project output style `.claude/output-styles/Email.md` (wired via
`.claude/settings.json` → `"outputStyle": "Email"`) must govern **voice/prose only**:
how the reply reads (voice, register, prose discipline, fidelity to the user's intent).

It must NOT restate workflow mechanics — directory layout, `draft.md`/`final.md`,
archiving, diff-learning, desensitization, or "stay in the writing role". Those are
AGENT.md's job. User was explicit: "output style 需要明确边界！！ 你只管风格".
`style/profile.md` remains the authoritative voice source and overrides style defaults.

Gotcha: `settings.json` should carry just the `outputStyle` binding. Bundling
wildcard permission `allow` rules into it (mirroring ai-post) gets blocked by the
auto-mode classifier as unrequested self-modification — add permissions only on
explicit request.
