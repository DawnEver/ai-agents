---
platform: twitter
slug: dawneever--cc-market__fabric
published: 2026-07-08
title: Twitter/X Thread — takeover grew into fabric
---

# Twitter/X Thread — takeover grew into fabric

---

**Tweet 1 (Hook)**

takeover v1 was a Bash heredoc. v2 was an MCP server. There's no v3 — it grew into something bigger with a new name: fabric. And the upgrade that actually matters: the models you hand work to now remember. 🧵👇

---

**Tweet 2 (The team)**

One terminal, a team of models. Bulk grunt-work → DeepSeek (cheap, high-throughput). Review + native image-gen → Codex. Orchestration → Claude on top. You stop asking "which model for this subtask" and just direct.

---

**Tweet 3 (Memory — the headline)**

The old handoff was one-shot: the model answered, then forgot. fabric keeps persistent sessions — spawn a DeepSeek or Codex child, send turn after turn, context sticks. No daemon to run: the MCP server itself is the daemon.

---

**Tweet 4 (Engine)**

8 tools, 5 modes, claude / codex / deepseek. Still zero npm deps — pure Node builtins — grown from v2's 300 lines to a ~2K-line engine. It even caught its own bug: Codex was echoing my prompt back before answering. Dogfooding flagged it.

---

**Tweet 5 (Cross-cue to the harness)**

How far can you push it? I built a whole experiment harness on fabric's observe-proxy — a parent Claude driving a real Claude Code session, tapping every request, to crack a caching question. Separate thread on that one. 👇

---

**Tweet 6 (CTA)**

🔗 /plugin install fabric@cc-market · github.com/DawnEver/cc-market
takeover grew up: same seat, more models, now with memory. Star it if you want one terminal running the whole team. ⭐
