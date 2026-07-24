# Step 03 — PDF acquisition

Script-first batch PDF acquisition with multi-scenario access handling.
For detailed paywall methodology → see `03-acquire-paywall.md` (progressive disclosure).

## Core principle

**Agent auto-clicks. User only intervenes when manual login is unavoidable.**

## Steps

1. **Build & review download queue**:
   ```bash
   lit-review acquire --topic <slug> --queue-only
   ```

2. **Classify access scenario** (agent does this once per paper):

   | Scenario | Detection | Method |
   |----------|-----------|--------|
   | **arXiv preprint** | `arxiv_id` in provider_raw | Direct HTTP download |
   | **Open Access** | OpenAlex `is_oa=true` | Download from `oa_url` |
   | **Campus IP** | `128.243.*` or `*.nottingham.ac.uk` | Direct access or headed Chrome |
   | **VPN** | User says VPN is on | Same as campus IP |
   | **Off-campus / paywall** | OA check fails + no campus IP | `lit-review login --profile <name>` then headed Chrome |
   | **CAPTCHA wall** | Page body has "captcha" / "verify you are human" | Real Chrome (`channel="chrome"`) with existing sessions |

3. **Download (auto-click where possible)**:
   ```bash
   lit-review acquire --topic <slug> [--profile <name>] [--headed]
   ```
   - `--headed`: visible Chrome with auto-click on PDF buttons
   - Without `--headed`: headless with saved browser profile
   - Real Chrome (`channel="chrome"`) reuses your existing publisher sessions

4. **Match & manifest**: script matches downloaded PDFs to queue entries.

5. **Report**: X downloaded, Y failed, Z matched. Proceed to step 04.

## Manual fallback

If auto-click fails, the script opens the paper URL in visible Chrome.
User clicks "View PDF" once; the file is auto-saved to the download directory.

## Paywall decision tree

```
Paper to acquire
  │
  ├─ arXiv preprint? → direct HTTP download (free, fast, legal)
  │
  ├─ Open Access? (OpenAlex API) → download from oa_url
  │
  ├─ Author preprint? → search arXiv by author + title keywords
  │
  ├─ Campus IP / VPN? → headed Chrome with auto-click
  │
  ├─ Off-campus with institutional access?
  │     └─ lit-review login → headed Chrome with saved profile
  │
  └─ Fully closed? → skip, note in audit log
```
