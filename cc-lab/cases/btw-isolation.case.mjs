// btw-isolation — does /btw run as an isolated side-thread?
//
// Hypothesis (from the PLAN): a /btw question sent while the main turn is active
// produces a SEPARATE API request that (a) carries no `tools`, and (b) does not leak
// into later main-thread requests' message history.
//
// Flow: launch → start a main turn that runs long enough to overlap → fire
// `/btw <side question>` during it → let both settle → send a second main message →
// close. Analysis (parent Claude, → reports/btw-isolation.md) compares the /btw
// request against the main-thread requests in the trace.

import { launch, runDirName } from '../driver/driver.mjs';
import { join } from 'node:path';

const runDir = join('.lab', runDirName('btw-isolation'));
const runDir = join('.lab', `${stamp}-btw-isolation`);

const s = await launch({
  runDir,
  env: { CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
});

console.log('run dir:', s.runDir);

// Robust submit: type text, confirm it landed in the input, THEN press Enter as a
// separate keystroke. A bare send() races a CR against long/pasted input and can
// leave the text unsubmitted (learned the hard way — see reports/btw-isolation.md).
async function type(text, marker) {
  // Retry once: right after a turn settles the input can briefly drop keystrokes.
  try {
    s.key(text);
    await s.waitOutput(marker, 6000);
  } catch {
    await s.waitIdle(1000, 8000);
    s.key(text);
    await s.waitOutput(marker, 8000);
  }
  s.key('\r');
}

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // Main turn — a long text generation (no tools) keeps the turn streaming for
  // several seconds, giving /btw a real in-flight window to overlap. ZEBRAMAIN
  // marks the main thread in the trace.
  await type(
    'Write a detailed 250-word essay on the history of tea. Begin the very first line with the token ZEBRAMAIN, then the essay.',
    /essay/,
  );
  // Confirm the turn is actually in-flight before firing /btw.
  await s.waitOutput(/esc to interrupt|ZEBRAMAIN/i, 25000);
  console.log('-- main turn in-flight, firing /btw --');

  // Side question via /btw while the main turn runs — distinctive token QUOKKABTW.
  await type('/btw what is the capital of France? Include the token QUOKKABTW.', /QUOKKABTW/);
  await s.waitIdle(6000, 120000);
  console.log('-- main + /btw settled --');

  // Second main turn — an extra forward-isolation probe. Best-effort: the analysis
  // already gets forward-isolation from the main-thread request that trails the
  // /btw (it carries the essay history but must NOT carry the /btw Q&A), so a
  // dropped keystroke here is not fatal to the case.
  try {
    await type('Reply with the single word: OKAPI.', /OKAPI/);
    await s.waitIdle(4000, 90000);
    console.log('-- second main turn idle --');
  } catch {
    console.log('-- second main turn skipped (input dropped) — trailing main turn already suffices --');
  }
} finally {
  await s.close();
}

console.log('\nDONE.');
console.log('run dir    :', s.runDir);
console.log('tap session:', s.tapSessionId);
console.log('Analyze → reports/btw-isolation.md (compare /btw request vs main-thread requests)');
