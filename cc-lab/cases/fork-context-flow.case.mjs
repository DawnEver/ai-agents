// fork-context-flow — when the user converses with a /fork, what reaches the MAIN agent?
//
// Question (from the user): after `/fork`, the user switches into the fork (agents view)
// and chats with it directly. Does the MAIN agent receive each user<->fork exchange?
//
// Hypothesis: NO shared transcript. The fork is a worker subagent that inherits the
// parent history AT SPAWN (by reference), then runs forward-isolated. The only thing that
// flows back to main is a `<task-notification>` carrying the fork's final <result> — one
// EACH TIME the fork stops. Main never sees the user's message to the fork, nor the fork's
// thinking/tool calls.
//
// Method (all driving verified against the persisted jsonl, which is the ground truth —
// the resumed fork runs as a detached process INVISIBLE to claude-tap, so tap alone can't
// see the fork's turns; driver/session.mjs reads what actually entered each history):
//   1. main turn establishes codeword MAINOK-ALPHA.
//   2. /fork "say FORKBORN then wait" — retry until the fork's subagent jsonl exists.
//   3. enter the fork composer (DOWN=manage, DOWN=select fork, ENTER=view) and reply with
//      a message carrying two tokens: GAMMA-OKAPI (in the user's message) and a directed
//      final output FORKRESULT-GAMMA (the fork's <result>). Retry until it lands in the
//      fork jsonl.
//   4. let the fork stop; read both transcripts.
//
// Assertions capture the finding: the fork inherited ALPHA; main got a task-notification
// per fork stop; each notification carries only <result> (FORKRESULT-GAMMA) — and NOT the
// user's message token OKAPI. Parent Claude writes the narrative to
// reports/fork-context-flow.md.

import { launch, runDirName } from '../driver/driver.mjs';
import { findTranscripts, loadTranscript, taskNotifications } from '../driver/session.mjs';
import { join } from 'node:path';

const runDir = join('.lab', runDirName('fork-context-flow'));
const s = await launch({
  runDir,
  // Model-agnostic (this is client-side context routing) — keep the cheap default.
  env: { CLAUDE_CODE_FORK_SUBAGENT: '1', CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
});
console.log('run dir:', s.runDir);

// A hard watchdog: the fork agents-view is a modal TUI; a dropped keystroke must fail the
// case (non-zero exit) rather than hang the harness.
setTimeout(() => { console.error('WATCHDOG: case exceeded budget'); process.exit(2); }, 300000).unref();

const W = async (re, to) => { try { await s.waitOutput(re, to); return true; } catch { return false; } };
const idle = async (ms, to) => { try { await s.waitIdle(ms, to); } catch { /* animations never idle */ } };
const K = (seq) => { try { s.key(seq); } catch (e) { console.error('key after exit:', e.message); } };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const forkFiles = () => findTranscripts(s.configDir).forks;
// Poll the fork jsonl(s) until `pred(text)` holds — the reliable oracle for TUI actions
// whose on-screen echo is ambiguous (the garbled alt-screen buffer echoes typed input).
async function pollFork(pred, timeout) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    for (const f of forkFiles()) {
      try { if (pred(loadTranscript(f).map((e) => e.text).join('\n'))) return f; } catch { /* mid-write */ }
    }
    await sleep(500);
  }
  return null;
}
async function typeInto(text, token) {
  for (let i = 0; i < 3; i++) { K(text); if (await W(token, 4000)) return true; await idle(800, 4000); }
  return false;
}

function assert(cond, msg) {
  if (!cond) { console.error('FAIL:', msg); process.exitCode = 1; }
  else console.log('ok  -', msg);
}

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // 1. Main establishes ALPHA.
  K('Reply with exactly: MAINOK-ALPHA'); await W(/Reply/, 4000); K('\r');
  await W(/MAINOK-ALPHA|MAINOKALPHA/, 40000);
  console.log('-- main established MAINOK-ALPHA --');

  // 2. Spawn the fork; verify via its persisted jsonl (retry once — spawn can drop input).
  let forkFile = null;
  for (let attempt = 0; attempt < 2 && !forkFile; attempt++) {
    K('/fork say exactly FORKBORN and then wait for further instructions');
    await W(/FORKBORN/, 6000); K('\r');
    forkFile = await pollFork((t) => /FORKBORN/.test(t), 45000);
    console.log(`-- /fork spawn attempt ${attempt}: ${forkFile ? 'spawned' : 'retry'} --`);
  }
  assert(!!forkFile, 'fork spawned (subagent jsonl exists)');
  await idle(2500, 15000);

  // 3. Open the fork's reply composer and send an interactive follow-up.
  //    From the main prompt: DOWN enters "manage", DOWN selects the fork row, ENTER views
  //    it (opening the "send the fork your next instruction" composer).
  K('\x1b[B'); await idle(800, 5000);
  K('\x1b[B'); await idle(800, 5000);
  K('\r');    await idle(1200, 6000);
  await W(/next instruction|say-exactly-forkborn/i, 6000);
  await idle(1000, 5000);

  let landed = null;
  for (let attempt = 0; attempt < 3 && !landed; attempt++) {
    await typeInto('New codeword GAMMA-OKAPI. Reply with exactly: FORKRESULT-GAMMA', /OKAPI/);
    K('\r');
    landed = await pollFork((t) => /GAMMA-OKAPI|FORKRESULT-GAMMA/.test(t), 30000);
    console.log(`-- reply attempt ${attempt}: ${landed ? 'landed in fork' : 'retry'} --`);
    if (!landed) { K('\x1b[B'); await idle(600, 4000); K('\x1b[B'); await idle(600, 4000); K('\r'); await idle(1000, 5000); }
  }
  assert(!!landed, 'interactive reply reached the fork');

  // 4. Let the fork stop and the notification post to main.
  await idle(6000, 90000);
  console.log('-- settled --');
} finally {
  await s.close();
}

// ---- Assertions on the persisted transcripts (evidence layer 2) ----
const { main, forks } = findTranscripts(s.configDir);
const mainDocs = main.map(loadTranscript);
const mainEntries = mainDocs.slice().sort((a, b) => b.length - a.length)[0] || []; // the interactive session
const forkEntries = forks.map(loadTranscript).sort((a, b) => b.length - a.length)[0] || [];
// Check OKAPI-absence across EVERY main-level transcript (the session id can rotate on some
// nav paths → more than one main file; a single-file check could be a false negative).
const mainText = mainDocs.flat().map((e) => e.text).join('\n');
const forkText = forkEntries.map((e) => e.text).join('\n');
const notifs = mainDocs.flatMap(taskNotifications); // union across all main-level sessions

console.log(`\nmain entries=${mainEntries.length} fork entries=${forkEntries.length} notifications=${notifs.length}`);
console.log('notification results:', notifs.map((n) => n.result));

// The fork inherited the parent conversation at spawn (fork-context-ref to the parent).
assert(forkEntries.some((e) => e.type === 'fork-context-ref'), 'fork carries a fork-context-ref (inherits parent history by reference)');
// The fork received the user's interactive follow-up (OKAPI) and answered it.
assert(/GAMMA-OKAPI/.test(forkText), "fork's history contains the user's follow-up (GAMMA-OKAPI)");
assert(/FORKRESULT-GAMMA/.test(forkText), 'fork produced the directed result FORKRESULT-GAMMA');
// Main got a task-notification per fork STOP (initial directive + the interactive reply).
assert(notifs.length >= 2, 'main received >=2 task-notifications (one per fork stop, same task-id)');
assert(notifs.some((n) => /FORKBORN/.test(n.result || '')), "main's first notification result carries FORKBORN");
assert(notifs.some((n) => /FORKRESULT-GAMMA/.test(n.result || '')), "main's second notification result carries FORKRESULT-GAMMA");
// The crux: main sees only the RESULT — NOT the user's message to the fork.
assert(!/OKAPI/.test(mainText), "main NEVER sees the user's message to the fork (no OKAPI token in main history)");

console.log('\nDONE.');
console.log('run dir    :', s.runDir);
console.log('tap session:', s.tapSessionId);
console.log('Analyze → reports/fork-context-flow.md (task-notification result-callback model)');
