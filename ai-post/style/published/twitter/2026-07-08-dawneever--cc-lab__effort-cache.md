---
platform: twitter
slug: dawneever--cc-lab__effort-cache
published: 2026-07-08
title: Twitter/X Thread — the prompt cache partitions on /effort
---

# Twitter/X Thread — the prompt cache partitions on /effort

---

**Tweet 1 (Hook — finding)**

I switched Claude Code's /effort level mid-session and watched the prompt cache do something I didn't expect. It didn't reset — it partitioned. Each effort level quietly keeps its own cache namespace. 🧵👇

---

**Tweet 2 (Proof)**

Proof: go high → low → high. On the way back, the original high block returns verbatim — cache_create collapses from 10,896 tokens to 1,355. A true reset would rebuild ~10k every time. It doesn't. Effort is a hidden cache-key dimension. (tested on cc 2.1.204)

---

**Tweet 3 (Harness)**

How do I know? I built cc-lab: a parent Claude drives a REAL Claude Code session through a pseudo-terminal, while every API request the child sends is tapped to disk. Drive it, don't eyeball the TUI — the screen doesn't count, the trace does.

---

**Tweet 4 (Fabric / proxy)**

It rides on fabric, my multi-model plugin. claude-tap can't see Foundry/DeepSeek-routed traffic; fabric's observe-proxy can — the child speaks plain HTTP to a local proxy that owns the upstream. That's how a Foundry provider becomes observable.

---

**Tweet 5 (Cross-cue to fabric)**

Don't let the harness scare you — fabric itself is one line for anyone: /plugin install fabric@cc-market, and you're handing tasks to any model from inside Claude Code. Separate thread on that. 👇

---

**Tweet 6 (CTA)**

🔗 fabric: /plugin install fabric@cc-market
cc-lab + the findings: github.com/DawnEver/ai-agents/tree/main/cc-lab
Stop guessing how Claude Code caches. Drive a real session and watch it. ⭐
