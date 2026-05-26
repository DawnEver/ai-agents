---
platform: twitter
slug: dawnever--quick-inline-suggestion
published: 2026-05-26
title: Thread: quick-inline-suggestion
---

**Tweet 1 (Hook)**

VS Code's AI kept getting heavier. More panels, more subscriptions, more things fighting for Cmd+I. I missed the old flow: select code, describe change, see diff, keep or revert. So I built it back. 400 lines. 零依赖。🧵👇


[229 chars]

---

**Tweet 2 (Features — core flow)**

✨ Cmd+I → QuickPick → diff preview → Keep/Revert

Select any code. Hit Cmd+I. Describe the change. A diff view opens — you decide if it's good. No auto-apply. No surprises.

选中代码，描述修改，看 diff，你来决定。



[196 chars]

---

**Tweet 3 (Features — backends)**

⚡ Claude Code and Codex CLI as backends — with auto-fallback.

If one fails, it silently retries with the other. BYOC: bring your own credentials. No Copilot subscription needed.

两个 AI 后端自动容灾，用自己的 API key。

[202 chars]

---

**Tweet 4 (Aha — clever details)**

💡 Prompts go via stdin, not shell args. No injection risk, no ps leakage, no arg-length limits.

Also: type a question in English or Chinese — isQuestion() detects both and auto-switches to Ask mode.

中英文问句自动识别，切换到 Ask 模式。



[240 chars]

---

**Tweet 5 (Context)**

💻 400 lines of TypeScript. Zero npm runtime dependencies. Instruction history with frequency tracking — your most-used prompts bubble up automatically.

Built because Copilot's inline edit became something I didn't recognize anymore.

400 行代码，自己的插件，自己说了算。

[262 chars]

---

**Tweet 6 (CTA)**

🔗 github.com/DawnEver/quick-inline-suggestion

Star it if you're tired of bloated AI editors. PRs welcome.

如果你也觉得 VS Code AI 越来越重，试试这个。 ⭐ #opensource #vscode

[172 chars]
