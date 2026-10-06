---
name: playbook-code-drift-2026-09-22
description: Skill playbooks describe behaviour the code does not have — three instances in one session, and why a warning that a step "will not work" must be verified before it is obeyed
metadata:
  type: engineering
---

# A playbook warning is a claim to check against the source

`created: 2026-09-22, accessed: 2026-09-22`

Three separate places in cc-academia where the operating instructions and the
code disagree. Each was found by reading the source rather than the playbook,
and in one case the cost of trusting the playbook was a user action that was
never necessary.

## The instances

**1. A warning about a destructive side effect that does not exist.** The
acquisition playbook warns, in bold, that the browser-login command force-kills
every browser process on the machine to clear a profile lock, and tells the
operator to close their personal windows first. The function that does the kill
is reachable only from the *download* helper, never from the login command.
Following the warning costs the operator all their open tabs for nothing.

**2. The same parameter name meaning two different things.** `login --profile`
takes a name and expands it to a profile directory; `acquire --profile` takes a
filesystem path. The playbook writes `<name>` for both. Passing a name to
`acquire` fails with a path-not-found error that names the name.

**3. A pointer to a file that does not exist.** An agent prompt named a module
path that had been moved; the real file lives under a different package root. An
agent asked to verify the output contract against that reference would find
nothing and could conclude the contract is undefined.

## Why this matters more than ordinary doc rot

A stale reference costs a lookup. A stale **warning** costs behaviour: it makes
an operator do something unnecessary (close their browser), or avoid something
safe, and it is believed precisely because it is emphatic. The failure mode is
inverted from the usual: the more alarming the warning, the less it gets
checked.

## The rule

**Before obeying a playbook warning that a step is dangerous or will not work,
read the code path it describes.** Confirm the claimed function is reachable
from the claimed command. This is cheap — one grep for the function name and its
call sites — and it is the difference between following instructions and
following a rumour.

Corollary for the playbooks themselves: a warning about a side effect should
name the command it applies to and the function that implements it, so the claim
is checkable. "This command will X" with no function named cannot be verified
without reading everything.

## Files

- `skills/literature-review/03-acquire.md` — the force-kill warning, the
  `<name>`-for-a-path usage
- `src/academia/litreview/acquire/download.py` — `_kill_stale_chrome` (call
  sites: the download helper only), `open_login` (no kill path)
- `src/academia/cli/lit_review.py` — the two `--profile` arguments
- `agents/abstract-screener.md` — the moved-module pointer (corrected this
  session to `src/academia/litreview/screen.py`)
