---
platform: twitter
slug: dawneever--cc-market
published: 2026-06-11
title: takeover v2 — MCP server for multi-model dispatch
---
# Twitter/X Thread: takeover v2

---

takeover v2 shipped. v1 was Bash heredoc. v2 is a real MCP server. Any agent, any workflow can now call external models 鈥?not just Bash.
浠?Bash heredoc 鍗囩骇鍒扮湡姝ｇ殑 MCP 鏈嶅姟鍣紝v2 鏉ヤ簡 馃У馃憞

---

鉁?Pure MCP + direct Codex
v2 is a JSON-RPC 2.0 stdio server. No Bash anywhere. Talks directly to `codex app-server` 鈥?zero third-party plugin deps. Image generation and editing included.
绾?MCP 鏈嶅姟鍣紝鐩磋繛 Codex app-server锛岃嚜甯﹀浘鐗囩敓鎴愩€?
---

鈿?5 modes. 1 plugin.
task / review (adversarial) / agent (full tools) / image-generate / image-edit. DeepSeek agent mode: full Read/Write/Bash through Claude Code's tool loop, LLM calls hit DeepSeek's API.
浜旂妯″紡锛屼竴涓彃浠躲€侱eepSeek 涔熻兘鐢ㄥ叏濂楀伐鍏蜂簡銆?
---

馃挕 The kicker: Codex found the shell injection in v1. v2 eliminates the shell entirely. The plugin caught its own bug and inspired its own architecture.
v1 鐨勫畨鍏ㄦ紡娲炴槸 Codex 鍙戠幇鐨勶紝v2 鐩存帴鍘绘帀浜?shell 鏈韩銆?
---

300 lines of MCP server. Zero npm deps 鈥?pure Node.js built-ins. Deterministic flag parsing: no LLM in the critical path. Cross-platform Windows.
300 琛屼唬鐮侊紝闆朵緷璧栵紝纭畾鎬цВ鏋愶紝璺ㄥ钩鍙般€?
---

馃敆 github.com/DawnEver/cc-market
`--provider deepseek` for cheap bulk work. `--provider codex --review` for adversarial review. `--provider codex --image` for covers.
渚垮疁閲忓ぇ鐨勭敤 DeepSeek锛岄攼璇勭敤 Codex锛屽皝闈㈠浘涔熺敤 Codex 猸?
