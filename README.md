# agents

Host-neutral workspaces for Claude Code and Codex. Each workflow can be used by
someone who has installed only one of the two hosts; no host depends on the
other's configuration directory or environment variables.

## Getting started

Clone anywhere **except** a cloud-synced folder — a sync daemon replicating `.git/`
corrupts the index and destroys the reflog:

```
git clone https://github.com/DawnEver/ai-agents.git ~/Documents/Code/AI/ai-agents
cd ~/Documents/Code/AI/ai-agents
./scripts/link-agent-data.sh --local
```

### Where the data lives

The repo carries code and contracts; it carries **no working data**. Drafts, archives, PDF
corpora and review runs are gitignored — they are large, and some (`cc-docx/workspace`)
hold real contact emails and partner names. A fresh clone therefore has none of the data
directories, and each workspace needs them to exist before it can write.

`scripts/link-agent-data.sh` provisions them, in one of two modes:

| Mode | Command | What you get |
| --- | --- | --- |
| **Local** | `./scripts/link-agent-data.sh --local` | plain directories inside the repo. Nothing leaves the machine. **Use this unless you need several machines to share one dataset.** |
| **Synced** | `./scripts/link-agent-data.sh "<path>/agent-data"` | symlinks into a folder you sync (OneDrive, Dropbox, Syncthing…). The data gets backup and cross-machine availability; the working tree still travels by git. |

`--status` shows what each path currently is. The two modes are interchangeable — re-run
with the other flag to switch. Either way the paths are gitignored, so `git status` stays
clean and nothing sensitive is ever committed.

`cc-docx/workspace` maps to the complete `agent-data/cc-docx` data root. Active tasks live
under `workspace/ongoing/`, completed tasks under `workspace/archived/`, and every task
keeps its own rendered deliverables in `<task>/out/`; there is no global `cc-docx/out`.

In synced mode the data dir is resolved from the argument, `$AGENT_DATA_DIR`, or the
`~/.claude/sync-dir` pointer's sibling — so it works across machines with different
usernames without editing anything.

## Projects

| Directory | Purpose |
|-----------|---------|
| `reply-email/` | Draft and archive email replies (`$reply-email` in Codex, `/reply-email` in Claude Code) |
| `ai-post/` | Multi-platform article generation, review, publishing and archiving (`$post-*` in Codex, `/post-*` in Claude Code) |
| `manuscript-review/` | Confidential academic-paper review data for the public `cc-academia` plugin (`manuscript-review` skill in Codex, `/cc-academia:manuscript-review` in Claude Code) |
| `literature-review/` | Systematic-review data for the public `cc-academia` plugin (`literature-review` skill in Codex, `/cc-academia:literature-review` in Claude Code) |
| `reviewer-discovery/` | Confidential submission-to-reviewer matching data for the public `cc-academia` plugin (`reviewer-discovery` skill in Codex, `/cc-academia:reviewer-discovery` in Claude Code) |
| `cc-lab/` | PTY + claude-tap experiment harness for observing Claude Code behavior (see `cc-lab/PLAN.md`) |
| `cc-docx/` | Word ↔ Markdown round-trip harness — iterate in markdown, deliver .docx, PDF on demand (`$docx` / `/docx`) |

Codex may start either here or in a child project. Always read the target
child's `AGENTS.md`; Claude Code reaches the same contract through that child's
`CLAUDE.md`. Workflow implementations may live in a public plugin rather than
this data repository, so resolve them from the installed package and never from
a developer-specific absolute path. Native Claude and Codex manifests are
independent: install only the host and plugin variant you use.
