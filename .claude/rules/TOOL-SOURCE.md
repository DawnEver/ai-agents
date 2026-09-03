# Change the tool at its source, never at its installed copy

Every project here is data and workflow; the executable tooling ships as a
plugin. So a fix to behaviour is a change to the plugin's **source checkout**,
and never to the copy the host installed.

An installed plugin lives under the host's own directory — for Claude Code
`~/.claude/plugins/marketplaces/<marketplace>/<plugin>/`, for Codex the
equivalent under `~/.codex/`. That is a **cache**. It is refreshed from the
marketplace, so an edit there is lost at the next update, invisible to every
other machine, and absent from the history that explains why the change was
made. It will also read as "already fixed" for the rest of the session while
being unfixed everywhere else.

## Finding the source

Discover it; do not carry a path around. In order:

1. A checkout the user has already named in this session or a project's own
   notes.
2. A git repository whose `origin` matches the installed plugin's marketplace
   remote. `git -C <installed-copy> remote -v` names the remote to look for.
3. A sibling checkout of the marketplace repository near this workspace.

**If none of those resolves, stop and ask the user for the path.** Do not fall
back to editing the installed copy, and do not guess. One question costs less
than a change that silently does not exist.

Never write an absolute path to anyone's checkout into a committed file. These
projects sync across machines and hosts, where such a path is right on exactly
one of them. The path belongs in the conversation, or in a local, ignored
setting — not in the repository.

## After changing the source

- Run that project's tests **in the source checkout**, not in the cache.
- Commit there, so the reasoning travels with the change.
- If the running session needs the new behaviour immediately, re-sync the
  installed copy from the source rather than editing it in place, and say that
  you did.
