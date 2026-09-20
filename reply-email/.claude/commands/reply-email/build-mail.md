---
name: reply-email:build-mail
description: Build the importable .eml and .ics for a finished draft, so the round can be opened in a mail client instead of pasted by hand.
disable-model-invocation: true
---

# Build Mail

Run at the **Build** step of the reply workflow, and again after every edit to `final.md`.
The frontmatter schema, the command's flags, and the behaviour worth knowing are defined once
in `AGENTS.md` (Reference → **Mail and calendar generation**) — do not restate them here.

## Steps

1. **Fill the frontmatter.** Read `final.md`. If it has no frontmatter block, add one before
   the body, deriving what you can:
   - `to:` from the incoming email's `From:` (the reply goes back to its sender) — but for a
     forwarded or delegated round, the real recipient may be someone else; ask rather than
     guess.
   - `subject:` from the incoming subject, `Re:`-prefixed as the draft's own convention
     implies.
   - `attach:` for each file in the round folder that should travel with the reply, and
     `![alt](file.png)` in the body for each image that should appear inline.

   Frontmatter is metadata, not prose — it is never part of the message the recipient reads.

2. **Build.** Run the command from `AGENTS.md` against `final.md`. Add nothing else to the
   call unless the user asked for it.

3. **Report what was written, and every warning.** Warnings name the problem and the line or
   path it came from — a mistyped key silently dropping an attachment is the failure this
   exists to catch, so never swallow one. If a warning reflects a real mistake in the draft
   (an unknown key, an image that does not resolve), fix the draft and rebuild rather than
   explaining the warning away.

4. **Hand over, and say what to do.** Tell the user the files are beside `final.md` and that
   double-clicking them is what imports them: the `.eml` opens as an editable draft with a
   Send button, the `.ics` offers to add the event. Remind them the draft is still not sent
   and the archive gate has not moved.

5. **Rebuild after edits.** Any later change to `final.md` — including one the user makes
   themselves — invalidates both files. Rebuild on request, or when you next touch the round.

## Notes

- **Building is not approving.** Step 6 of the reply workflow still ends the sequence, and
  nothing archives until the user says 归档. Generating a file the user might send does not
  count as approval to send or to archive it.
- **Nothing here sends anything.** Both files are local artifacts.
- **A missing `to:` is a real error, not a warning.** If the frontmatter has no recipient,
  there is nowhere for the reply to go; ask the user instead of inventing an address.
