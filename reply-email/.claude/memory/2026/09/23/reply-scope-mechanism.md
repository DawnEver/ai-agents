---
name: reply-scope-mechanism
description: "A reply answers only the newest message in the quoted thread — never restate the correspondent's own instructions, never re-answer a settled point; codified as AGENTS.md → Reply scope"
metadata:
  type: project
---

User feedback on 2026-09-23, reviewing a draft for a multi-round technical thread: the draft had
spent a whole paragraph playing the correspondent's own instructions back at them (the simulation
method they had prescribed), and had repeated a quantity already confirmed in the previous round.
The instruction was blunt — *only focus on the latest email; don't repeat what has already been
said* — and was immediately followed by 建立机制: don't just fix this draft, build the rule in so it
can't recur.

**The rule now lives in `AGENTS.md` → `### Reply scope`** (under Reference, after Style), with
pointer lines in `.claude/output-styles/Email.md` under Fidelity and in
`.claude/commands/reply-email.md` step 4, plus an amendment to AGENTS.md workflow step 4 ("don't
re-ask answered questions, and don't re-answer them either"). Substance: `original.txt` carries the
whole quoted thread, but a reply answers **only the newest message**; earlier turns are context for
understanding it, never a to-do list. Five bullets — answer only what's new; never restate the
correspondent's instructions; never re-answer a settled point; acknowledgement is a word not a
paragraph; new substance earns length, repetition never. The one-line test: *if a line could have
been written without reading the latest message, cut it.*

**Why the failure mode is structural, not carelessness.** `read_mail.py` renders `original.txt` with
the full quoted history inline, so by the time the draft is written the freshest, most concrete text
in context is the *correspondent's* words describing what they want done. Mirroring that text back
feels responsive and reads as padding. The mechanism is deliberately a written rule rather than a
one-off fix, because the same setup regenerates the same temptation on every continuation.

**Watch out when writing examples into committed files.** The first version of the new section
illustrated "don't restate their instructions" by paraphrasing the actual instructions from the live
thread. `AGENTS.md` is public-facing and its desensitization rule bars verbatim correspondence —
a close paraphrase of live content is the same leak in softer clothing. The example is now abstract
("as you described, I'll do A, then B, then C"). Cheap check after any such edit: grep the committed
files for project and counterpart identifiers.

**Unproven.** The rule is a prediction about future drafts; it has not yet been confirmed by an
archive diff, since the round that prompted it is still ongoing. If a later archive shows the same
padding despite the rule, that is the signal to move it from prose guidance into something the
workflow enforces.
