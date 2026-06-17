---
platform: twitter
slug: dawneever--cc-market
published: 2026-06-17
title: rem — Claude Code memory that lives IN your repo
---

# rem — Claude Code memory that lives IN your repo

**Tweet 1 (Hook)** — 222 chars

Claude Code now writes its own memory. The catch: it lives in `~/.claude/` on your machine — not in the repo. Change something at the office. Clone it at home to keep going. Claude remembers none of it. Teammates? Same. 🧵👇


---

**Tweet 2 (What rem does)** — 256 chars

✨ So I built rem. Memory as committed markdown.

Learnings land in `.claude/memory/YYYY/MM/DD/*.md`, tracked by git. It travels with the clone, shows up as a diff in your PR, and your teammate gets your context for free. No DB, no vector store, no service.

---

**Tweet 3 (The content/state split)** — 265 chars

💡 The trick: split content from state.

The `.md` knowledge is committed and shared. The volatile per-entry state — accessed date, touch count — lives in gitignored `_meta.json` sidecars, local to each machine. So two devs never fight over whose counter is "right."

---

**Tweet 4 (3-tier + auto-prune — the aha)** — 268 chars

⚡ It forgets the right things on its own.

Stale short-term notes age out at 90 days; anything you keep touching gets promoted to long-term. And nothing is ever hard-deleted — prune just marks it `dropped`, so the audit trail survives. (3 tiers: rules / long / short.)

---

**Tweet 5 (Memory-as-platform)** — 257 chars

🔥 Here's where it stops being "just memory."

That same git-tracked store backs a `/todo` task system — no derived file, the memory entry IS the task. My sharp-review plugin writes its findings into it too. Memory becomes the substrate other tools build on.

---

**Tweet 6 (CTA)**

🔗 github.com/dawneever/cc-market

Zero deps, just markdown + git. If you've re-explained your project to Claude for the 5th time, rem is for you. ⭐

Install:
/plugin marketplace add DawnEver/cc-market
/plugin install rem@cc-market

#ClaudeCode
