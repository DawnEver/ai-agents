# literature-review (data only)

The pipeline lives in the public `cc-academia` plugin. Read its `AGENTS.md` for
principles and `skills/literature-review/` for operations. Never depend on the
plugin's location on one developer's machine.

This directory holds **research data**, which is confidential and never leaves it.

Active reviews live in `ongoing/<slug>/`; completed ones in `archived/<slug>/`.
These are the only valid data directories for this workflow. The plugin locates
them by walking up from wherever you are; `ACADEMIA_DATA_ROOT` overrides that if
you keep research data outside the repository. Do not add machine-specific
absolute paths here.

## Memory privacy guardrail

Research-topic content never enters project-level memory. Workspace material —
briefs, concept taxonomies, paper lists, screening outcomes, findings — lives
only inside `ongoing/<slug>/` and its own scoped memory.

Project-level `.claude/memory/` may contain only generic, topic-agnostic
engineering knowledge. Never write a topic slug, a paper title or a research
finding there. If one is written by mistake, delete it and amend the commit
rather than leaving it in history.
