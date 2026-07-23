# Download Compliance Checklist

Checklist for the agent before and during PDF acquisition. Every item must pass.

## Pre-Flight

- [ ] Download queue is approved (`approved: true` for each selected candidate)
- [ ] Browser profile exists and is located OUTSIDE the repo (`%LOCALAPPDATA%/literature-review/browser-profiles/`)
- [ ] The dedicated browser profile was used for institutional login (never reuse the user's daily profile)
- [ ] User explicitly requested download in the current conversation (never auto-download)
- [ ] Download limit is respected (default: 10, hard max: 20 per run)

## During Acquisition

- [ ] Rate limiting: ≥1 second delay between downloads
- [ ] Each PDF is saved with candidate ID in filename: `<candidate_id>_<first_author>_<year>.pdf`
- [ ] Failed downloads are recorded with failure reason (HTTP status, CAPTCHA, redirect, etc.)
- [ ] Stop immediately on: authentication failure, access denial, CAPTCHA, HTTP 403/429

## Post-Acquisition

- [ ] PDF signatures validated: minimum size (1024 bytes), magic bytes check (%PDF-)
- [ ] HTML login pages, error pages, and ambiguous responses are REJECTED (not saved as PDF)
- [ ] SHA-256 hash computed for each acquired PDF
- [ ] `match_downloaded_pdfs.py` run to pair PDFs with queue entries
- [ ] `make_download_manifest.py` generates `handoff/download_manifest.json`

## Failure Recovery

| Error | Action |
|-------|--------|
| HTTP 403 | STOP — access denied. May need institutional VPN or different network. |
| HTTP 429 | STOP — rate limited. Wait and resume later. |
| CAPTCHA | STOP — browser session flagged. May need new browser profile. |
| PDF < 1024 bytes | Reject — likely an error page. Mark as failed. |
| Non-PDF content | Reject — validate magic bytes. Mark as failed. |
| Timeout | Retry once after 5s. If still failing, skip and continue. |

## Hard Rules

- **Never** reuse the user's daily browser profile.
- **Never** auto-download without explicit user instruction.
- **Never** exceed `hard_max_pdfs_per_run` (20).
- **Always** validate PDF signatures before accepting.
- **Always** record provenance (acquisition method, timestamp, URL).
