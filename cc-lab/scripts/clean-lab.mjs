// clean-lab — remove `.lab/` run artifacts.
//
// `.lab/` runs are disposable: the authoritative traces live in the shared claude-tap
// sqlite DB (keyed by tap-session UUID, which reports reference), NOT in `.lab/`. The
// only per-run artifacts are tty.log (fragile, dev-only) and the isolated config dir —
// which, until close() scrubs it, holds a copied `.credentials.json`. Since `.lab/`
// sits under a cloud-synced tree, it should not accumulate.
//
// Usage:
//   node scripts/clean-lab.mjs           # remove ALL runs
//   node scripts/clean-lab.mjs --days 2  # keep runs newer than N days
//   node scripts/clean-lab.mjs --creds   # only scrub .credentials.json, keep runs

import { readdirSync, statSync, rmSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const labDir = join(fileURLToPath(new URL('../', import.meta.url)), '.lab');
if (!existsSync(labDir)) {
  console.log('[clean-lab] no .lab/ — nothing to do');
  process.exit(0);
}

const args = process.argv.slice(2);
const daysIdx = args.indexOf('--days');
const keepDays = daysIdx >= 0 ? Number(args[daysIdx + 1]) : null;
const credsOnly = args.includes('--creds');
const cutoff = keepDays != null ? Date.now() - keepDays * 86400_000 : null;

let removed = 0;
let scrubbed = 0;
for (const name of readdirSync(labDir)) {
  const runDir = join(labDir, name);
  let st;
  try { st = statSync(runDir); } catch { continue; }
  if (!st.isDirectory()) continue;

  // Always scrub any lingering credential copy first (defense in depth).
  const cred = join(runDir, 'config', '.credentials.json');
  if (existsSync(cred)) { rmSync(cred, { force: true }); scrubbed++; }

  if (credsOnly) continue;
  if (cutoff != null && st.mtimeMs >= cutoff) continue; // keep recent

  rmSync(runDir, { recursive: true, force: true });
  removed++;
}

console.log(`[clean-lab] removed ${removed} run(s), scrubbed ${scrubbed} credential copy(ies)`
  + (keepDays != null ? ` (kept < ${keepDays}d)` : '') + (credsOnly ? ' (creds-only)' : ''));
