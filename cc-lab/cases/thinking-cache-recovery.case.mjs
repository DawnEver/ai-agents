// thinking-cache-recovery — follow-ups to thinking-cache.md:
//   (Q1) Does *raising* effort (not just lowering) also bust the prompt cache?
//   (Q2) Do same-effort cache breakpoints SURVIVE a switch-away-and-back? i.e. after
//        high→low→high, does turn 3 recover the high-cache created in turn 1?
//
// Build note (cc 2.1.204): the /effort UX changed since the original report
// (cc 2.1.199). There is NO cache-invalidation confirmation dialog anymore — the
// picker applies immediately and prints "Set effort level to <X> (saved as default)".
// The effort level is now visible IN the request body at output_config.effort (the
// old report's "body byte-identical" no longer holds), so we assert on the trace, not
// the screen. Driving is made deterministic by clamping the horizontal slider to LOW
// (many ← presses) then stepping RIGHT a fixed count, and confirming via the printed
// "Set effort level to <target>" line.
//
// Flow (levels: low·medium·high·…):
//   T1 @ high  "apple"   → creates the high-cache
//   → low                → T2 @ low  "banana"  known bust; creates the low-cache
//   → high (RAISE+back)  → T3 @ high "cherry"  Q1/Q2: recover T1's high-cache?
//   → low  (back)        → T4 @ low  "date"    Q2 other dir: recover T2's low-cache?

import { launch, runDirName } from '../driver/driver.mjs';
import { loadRecords, mainTurns } from '../driver/tap.mjs';
import { join } from 'node:path';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const runDir = join('.lab', runDirName('thinking-cache-recovery'));

const s = await launch({
  runDir,
  model: 'claude-sonnet-5',  // model-specific (needs the /effort slider); Sonnet, not Opus
  env: { CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
});
console.log('run dir:', s.runDir);

// Match the buffer TAIL only — waitOutput scans the CUMULATIVE buffer, so a stale
// "Set effort level to low" from an earlier switch matches immediately on the next.
async function waitTail(re, timeout = 12000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    if (re.test(s.text.slice(-1200))) return true;
    await sleep(100);
  }
  throw new Error(`waitTail: timed out waiting for ${re}`);
}

// Deterministic effort set: open picker → clamp LEFT to 'low' → step RIGHT to target →
// Enter applies (no confirm dialog in this build) → verify via the printed result line.
const IDX = { low: 0, medium: 1, high: 2 };
// /effort is racy: sometimes the submit doesn't open the picker, and then a stray ←
// navigates the main UI to the agents view. Only send arrows once the slider is
// CONFIRMED up ("Esc to cancel" is picker-unique); retry (Esc + resubmit) otherwise.
async function openEffortPicker() {
  for (let attempt = 0; attempt < 4; attempt++) {
    await s.waitIdle(600, 8000);
    s.send('/effort');
    try { await waitTail(/Esc to cancel|to adjust/i, 4000); return; }
    catch { s.key('\x1b'); await sleep(500); }  // clear state, retry
  }
  throw new Error('effort picker did not open after retries');
}
async function setEffort(target) {
  await openEffortPicker();
  await sleep(300);
  for (let i = 0; i < 6; i++) { s.key('\x1b[D'); await sleep(220); }  // clamp → low
  for (let i = 0; i < IDX[target]; i++) { s.key('\x1b[C'); await sleep(260); } // → target
  s.key('\r');                                        // apply slider position
  // A DOWNGRADE (e.g. → low) pops a "Change effort level? … 1. Yes, switch to X"
  // confirm dialog (its existence is itself the cache-reset finding); an upgrade / a
  // small change applies directly. Poll: result line → done; dialog → accept (Enter).
  // The TUI renders spaces as cursor-forward escapes, so stripAnsi yields
  // word-CONCATENATED text ("Seteffortleveltolow"). Match with \s* (zero-or-more) so
  // both the spaced dialog title and the concatenated result line match.
  const done = new RegExp(`effort\\s*level\\s*to\\s*${target}`, 'i');
  const dialog = /Change\s*effort\s*level|Yes,\s*switch\s*to/i;
  const start = Date.now();
  let ok = false;
  while (Date.now() - start < 12000) {
    const tail = s.text.slice(-800);
    if (done.test(tail)) { ok = true; break; }
    if (dialog.test(tail)) { s.key('\r'); await sleep(500); }
    await sleep(150);
  }
  if (!ok) throw new Error(`setEffort(${target}): no confirmation seen`);
  await s.waitIdle(1000, 8000);
  console.log(`-- effort → ${target} --`);
}

async function turn(word) {
  s.key(`Reply with the single word: ${word}.`);
  await s.waitOutput(new RegExp(word), 8000);
  s.key('\r');
  await s.waitIdle(4000, 90000);
  console.log(`-- turn "${word}" idle --`);
}

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // T1 uses the session DEFAULT effort (high, verified from the trace) — the very
  // first /effort right after ready() doesn't render the picker (cold prompt), and
  // routing T1 through setEffort is unnecessary since default is already high.
  await turn('apple');                             // T1 @ high (default) → high-cache
  await setEffort('low');   await turn('banana');  // T2 @ low   → bust, low-cache
  await setEffort('high');  await turn('cherry');  // T3 @ high  → Q1/Q2 recovery?
  await setEffort('low');   await turn('date');    // T4 @ low   → Q2 recovery?
} finally {
  await s.close();
}

// Guard + effort/cache table. Full analysis is written to reports/thinking-cache.md.
if (s.tapSessionId) {
  // mainTurns also catches the client's "[SUGGESTION MODE …]" autocomplete calls
  // (they carry system+tools+usage too) — drop them so only the 4 real turns remain.
  const isSuggestion = (t) => JSON.stringify(t.request?.body?.messages?.at(-1)?.content)
    ?.includes('SUGGESTION MODE');
  const turns = mainTurns(loadRecords(s.tapSessionId)).filter((t) => !isSuggestion(t));
  console.log(`\nmain turns: ${turns.length}`);
  turns.forEach((t, i) => {
    const u = t.response?.body?.usage ?? {};
    console.log('turn %d (idx %d): effort=%s cache_read=%d cache_create=%d',
      i + 1, t.turn, t.request?.body?.output_config?.effort,
      u.cache_read_input_tokens ?? 0, u.cache_creation_input_tokens ?? 0);
  });
  if (turns.length < 4) {
    console.error('FAIL: expected >= 4 main turns, got', turns.length);
    process.exitCode = 1;
  }
}

console.log('\nDONE.');
console.log('run dir    :', s.runDir);
console.log('tap session:', s.tapSessionId);
