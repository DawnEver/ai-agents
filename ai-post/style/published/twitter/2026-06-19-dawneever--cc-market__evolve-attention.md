---
platform: twitter
slug: dawneever--cc-market__evolve-attention
published: 2026-06-19
title: AI can watch ten loops at once. I can watch one. So I built an attention gate.
---

I told Claude Code to fix the repo and walked away. Came back to ten loops running. It can watch all ten. My attention holds about one.

Automating the work didn't free me — the judgment, the priorities, the sign-off still land on me. 🧵👇

⚡ So I built evolve: an autonomous review→fix loop.

Each round runs sharp-review (2+ critics), then fans out fixes across disjoint file sets so no two agents touch the same file. Every commit waits behind a green test suite. I never type the fix.

💡 But autonomy alone is a trap.

A loop that fixes its own code doesn't lighten my load. It just turns me from the one doing the work into the one supervising N loops at once. The 2026 bottleneck was never compute. It's the one human still on the hook.

🔥 So the real design is an attention gate every skill passes through.

Anything reversible and low-stakes resolves itself — I never see it. The rest gets stripped to what I actually need to decide, and what breaks if I ignore it. One prompt, ≤4 asks.

✨ The rule: no skill spends my attention directly.

And the gate isn't evolve-only. It lives in shared/, wired into every plugin I built — sharp-review finds, evolve fixes, rem remembers.

I automated the work and gave myself more meetings — with myself.

"Don't interrupt me" never means dropped. Deferred findings stay open, get re-attempted every round, and escalate to me after 3 unfixed rounds. Defer ≠ drop — the gate decides whether to interrupt me, never whether it gets fixed.

The scarce resource was never how fast AI works. It's the one thing that doesn't parallelize — me.

Stop optimizing throughput. Budget the human.

🔗 github.com/DawnEver/cc-market
evolve treats my attention as the budget. Star it if that reframe lands. ⭐
