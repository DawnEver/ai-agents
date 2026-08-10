# agents

My daily-use Codex and Claude Code skills and agents.

## Projects

| Directory | Purpose |
|-----------|---------|
| `reply-email/` | Draft and archive email replies (`$reply-email` in Codex, `/reply-email` in Claude Code) |
| `ai-post/` | — |
| `manuscript-review/` | Academic paper review pipeline (`$manuscript-review` / `/manuscript-review`) |
| `literature-review/` | Systematic literature review — discover, screen, acquire, read, synthesize (`$literature-review` / `/literature-review`) |
| `cc-lab/` | PTY + claude-tap experiment harness for observing Claude Code behavior (see `cc-lab/PLAN.md`) |
| `cc-docx/` | Word ↔ Markdown round-trip harness — iterate in markdown, deliver .docx, PDF on demand (`$docx` / `/docx`) |

Codex may start either here or in a child project. Root `.agents/skills/` aggregates thin launchers for every workflow; child `.agents/skills/` provides the same entries when working inside one project. In both cases the canonical workflow content remains under each project's `.claude/` tree. Always read the target child's `AGENTS.md` and resolve commands from that child directory.
