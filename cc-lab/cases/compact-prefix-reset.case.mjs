// compact-prefix-reset — after /compact, does the cache_read prefix reset to a fresh
// short prefix, or stay at the accumulated-history size?
//
// The user's expectation: "按道理 compact 后就应该从零开始了" — compaction summarizes
// history, so the next request's prefix should collapse to ~system+tools, NOT keep
// re-reading the whole accumulated history. This case tests that mechanism on the
// reference backend (vanilla Anthropic / Sonnet) with tap capture.
//
// Method:
//   1. Build up a growing message history over ~5 turns (one includes a file read to
//      add a real content jump to the prefix).
//   2. Trigger /compact and confirm it completes.
//   3. Send 2 more trivial turns.
//   4. From the tap trace, print cache_read/cache_creation per main turn.
//      - pre-compact turns should show cache_read growing with the prefix.
//      - post-compact turns should show cache_read collapsing back to ~system+tools
//        (the summary is short), NOT the accumulated history.
//
// Run: node cases/compact-prefix-reset.case.mjs
// (analysis detail → reports/compact-prefix-reset.md)

import { launch, runDirName } from '../driver/driver.mjs';
import { loadRecords, mainTurns } from '../driver/tap.mjs';
import { findTranscripts } from '../driver/session.mjs';
import { join } from 'node:path';
import { readFileSync } from 'node:fs';

const runDir = join('.lab', runDirName('compact-prefix-reset'));

const s = await launch({
  runDir,
  // The question is about the compaction/cache mechanism on the reference backend;
  // the user asked for Sonnet explicitly. Cheap enough for a few trivial turns.
  model: 'claude-sonnet-5',
  env: { CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
});

console.log('run dir:', s.runDir);
setTimeout(() => { console.error('WATCHDOG: case exceeded budget'); process.exit(2); }, 420000).unref();

const W = async (re, to) => { try { await s.waitOutput(re, to); return true; } catch { return false; } };
const K = (seq) => { try { s.key(seq); } catch (e) { console.error('key after exit:', e.message); } };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Grow the context prefix cheaply WITHOUT file reads: have the model emit a long
// reply once (enters history), then reference it in a later turn.
async function turn(prompt, tokenRe, label, to = 60000) {
  s.send(prompt);
  const ok = await W(tokenRe, to);
  if (!ok) { console.warn(`  !! turn '${label}' did not surface ${tokenRe}`); }
  try { await s.waitIdle(2500, 30000); } catch { /* animations */ }
  console.log(`-- ${label} --`);
}

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // T1 — warm the cache, establish baseline.
  await turn('Reply with exactly: SEED-ONE.', /SEED.ONE/, 'turn 1: seed');
  // T2 — emit a LONG reply so a real chunk enters history (grows the prefix).
  await turn('Spell the alphabet A to Z, one letter per line, nothing else.', /[WXYZ]/, 'turn 2: long reply (grow prefix)');
  // T3 — reference the long reply, forcing the accumulated history to be re-read.
  await turn('In your previous reply, which letter came right after P? Reply with exactly that single letter.', /Q\b/, 'turn 3: reference history');

  // ── Trigger /compact ──────────────────────────────────────────────
  // The PTY re-echoes the last prompt into the input box after a turn, so a raw
  // send('/compact') gets MERGED with that leftover text and is treated as a normal
  // user message (verified: "…single letter./compact"). Fix: clear the input line
  // (Ctrl+U), then type the command separately from the Enter that submits it.
  await sleep(3000);
  try { await s.waitIdle(5000, 60000); } catch {}
  K('\x15');         // Ctrl+U — clear any residual text on the input line
  await sleep(300);
  K('/compact');     // type the command (no Enter yet)
  await sleep(400);
  K('\r');           // submit it as its own command
  console.log('-- /compact sent (cleared input first) --');
  // Accept any confirmation dialog, then VERIFY compaction actually ran by polling
  // the persisted jsonl for a compaction marker ("being continued" / "Compacted").
  K('\r');
  const { main } = findTranscripts(s.configDir);
  const mainFile = main[0];
  const deadline = Date.now() + 120000;
  let compacted = false;
  while (Date.now() < deadline && !compacted) {
    try {
      const txt = readFileSync(mainFile, 'utf8');
      if (/being continued|Compacted|PostCompact/i.test(txt)) compacted = true;
    } catch { /* file may rotate */ }
    await sleep(500);
  }
  console.log(`-- compact confirmed: ${compacted} --`);
  if (!compacted) { console.error('FAIL: /compact did not produce a compaction marker in the persisted jsonl'); process.exitCode = 1; }
  await sleep(2000);
  try { await s.waitIdle(3000, 30000); } catch {}

  // T4/T5 — post-compact turns. If compaction reset the prefix, these read back
  // only ~system+tools+summary (small cache_read), not the accumulated history.
  await turn('Reply with exactly: POST-ONE.', /POST.ONE/, 'turn 4: post-compact 1');
  await turn('Reply with exactly: POST-TWO.', /POST.TWO/, 'turn 5: post-compact 2');

} finally {
  await s.close();
  await sleep(2000);
}

// ── Trace analysis ─────────────────────────────────────────────────
if (s.tapSessionId) {
  const records = loadRecords(s.tapSessionId);
  const turns = mainTurns(records);
  console.log(`\ntap session: ${s.tapSessionId}`);
  console.log(`total records: ${records.length}, main turns: ${turns.length}`);

  // Which turn is post-compact? The first turn whose request system contains a
  // compaction summary (a system block whose text begins with a summary/continuation),
  // OR simply the last two turns. Prefer detecting the summary in the API body.
  let compactTurnIdx = -1;
  turns.forEach((r, i) => {
    const sys = r.request?.body?.system;
    const texts = Array.isArray(sys) ? sys.map((b) => b?.text || '') : [];
    if (texts.some((t) => /This session|summar/i.test(t) && t.length > 200)) compactTurnIdx = i;
  });
  // Fall back: the post-compact turns are the ones whose user text is AFTER-COMPACT.
  if (compactTurnIdx < 0) {
    turns.forEach((r, i) => {
      const msgs = r.request?.body?.messages || [];
      const user = msgs.filter((m) => m.role === 'user').map((m) =>
        Array.isArray(m.content) ? m.content.map((b) => b.text || '').join(' ') : String(m.content || '')).join(' ');
      if (/AFTER.COMPACT.ONE/.test(user)) compactTurnIdx = i;
    });
  }

  console.log('\nturn | msgs | cache_read | cache_create | input | output | (post-compact?)');
  let preLast = 0, postFirst = 0, postSecond = 0;
  turns.forEach((r, i) => {
    const u = r.response?.body?.usage ?? {};
    const cr = u.cache_read_input_tokens ?? 0;
    const cc = u.cache_creation_input_tokens ?? 0;
    const msgs = (r.request?.body?.messages ?? []).length;
    const tag = i === compactTurnIdx ? '  ← POST-COMPACT' : (compactTurnIdx >= 0 && i > compactTurnIdx ? '  ← post+1' : '');
    console.log(`  ${String(i).padStart(2)} | ${String(msgs).padStart(4)} | ${String(cr).padStart(10)} | ${String(cc).padStart(11)} | ${String(u.input_tokens ?? 0).padStart(6)} | ${String(u.output_tokens ?? 0).padStart(6)} |${tag}`);
    if (i === compactTurnIdx - 1) preLast = cr;
    if (i === compactTurnIdx) postFirst = cr;
    if (i === compactTurnIdx + 1) postSecond = cr;
  });
  // Compaction evidence: post-compact turns should show the message count RESET
  // (history replaced by a short summary), not monotonic growth.
  if (compactTurnIdx > 0) {
    const preMsgs = turns[compactTurnIdx - 1].request?.body?.messages?.length ?? 0;
    const postMsgs = turns[compactTurnIdx].request?.body?.messages?.length ?? 0;
    console.log(`\nmessage count: pre-compact turn = ${preMsgs}, post-compact turn = ${postMsgs} (reset = ${postMsgs < preMsgs})`);
  }

  if (compactTurnIdx > 0 && postFirst > 0) {
    const drop = preLast > 0 ? (1 - postFirst / preLast) * 100 : 0;
    console.log(`\npre-compact last cache_read = ${preLast}`);
    console.log(`post-compact first cache_read = ${postFirst}`);
    console.log(`post-compact second cache_read = ${postSecond}`);
    console.log(`cache_read drop after compact = ${drop.toFixed(1)}%`);
    const reset = postFirst < preLast * 0.5;
    console.log(reset ? 'RESULT: prefix COLLAPSED after /compact (fresh short prefix)' : 'RESULT: prefix did NOT collapse — still re-reading accumulated history');
    if (!reset) process.exitCode = 1;
  } else {
    console.warn('could not identify a clean pre/post compact boundary in the trace');
  }
}

console.log('\nDONE.');
console.log('run dir   :', s.runDir);
console.log('tap session:', s.tapSessionId);
