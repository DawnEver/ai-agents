---
name: eml-attachment-extraction
description: "Extracting a saved .eml the user drops in (Desktop/File.eml) — python stdlib email, counter-named image parts (Outlook reuses image.png), cp1252 text parts, and often no body text at all"
metadata:
  type: project
---

When the user hands over a saved email as a file instead of pasting it (e.g.
`C:\Users\linxu\Desktop\File.eml`), extract it with the python stdlib rather than reading the raw
MIME by eye — a real Outlook `.eml` ran ~900 KB with base64 image and PDF parts.

```python
import email
msg = email.message_from_binary_file(open(src, 'rb'))
for part in msg.walk():
    fn = part.get_filename()
    payload = part.get_payload(decode=True)   # decodes base64/QP for you
    ...
```

**Three traps, all hit on 2026-09-20:**

1. **Duplicate part filenames silently overwrite.** Outlook `.eml` files commonly carry several
   inline images *all* named `image.png`. Writing each to `get_filename()` loses every one but
   the last — the first screenshot vanished this way. Enumerate with a counter
   (`image-1.png`, `image-2.png`, …) and never trust `get_filename()` for uniqueness.
2. **`text/plain` parts are often `charset="Windows-1252"`, not UTF-8.** Decode with `cp1252`
   (`errors='replace'`) or the body throws or mangles. Confirm the charset by grepping the part
   headers before assuming.
3. **The body may be empty of content.** A forwarded `.eml` can be signature-only with everything
   meaningful living in inline screenshots plus an attachment — the 2026-09-20 one was a signature
   block, two PNGs, and a booking-confirmation PDF. Read the images with the Read tool and pull
   the PDF's first page for text (Key Travel's confirmation named the provider, reference,
   cost centre, and price). Do not conclude the email is empty because `text/plain` is short.

**Also:** the extracted images and PDF belong in the round folder as attachments
(`ongoing/<topic>/`, later archived in place) — AGENTS.md documents attachments as unconstrained
filenames alongside `original.txt`. Write each screenshot's *content* into `original.txt` as
annotated text (flight numbers, times, prices, filters), because the images are unreadable to
anything that only reads the text files, and that transcription is what the draft's numbers get
checked against. Clean up scratch files (`_body.html`, `_body.txt`) afterwards.
