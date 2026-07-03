// output-style-layer (PLAN M3.2) — which system-prompt block does a mid-session
// directive change, and does the prompt cache survive it?
//
// The PLAN targeted `/output-style`, but output styles are REMOVED in this build
// (cc 2.1.199): no /output-style, /style, or /output command exists. To still answer
// the underlying question — how a session-level directive layers into the `system`
// array and what it does to the cache — we use an available equivalent: `/goal`,
// which sets a standing directive Claude checks before stopping.
//
// Flow: turn 1 (no goal) → `/goal <directive with token GOALPINE>` → turn 2 → close.
// Analysis (parent Claude → reports/output-style-layer.md) diffs the `system` array
// (and messages) between the two main turns and reads cache usage.

import { launch, runDirName } from '../driver/driver.mjs';
import { join } from 'node:path';

const runDir = join('.lab', runDirName('output-style-layer'));
const runDir = join('.lab', `${stamp}-output-style-layer`);

const s = await launch({
  runDir,
  env: { CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
});

// Robust submit: type → confirm it landed → Enter (see btw-isolation for the why).
async function type(text, marker) {
  s.key(text);
  await s.waitOutput(marker, 8000);
  s.key('\r');
}

console.log('run dir:', s.runDir);

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // Turn 1 — no directive. Marker MANGOONE.
  await type('Reply with the single word: MANGOONE.', /MANGOONE/);
  await s.waitIdle(4000, 90000);
  console.log('-- turn 1 idle (no goal) --');

  // Set a standing directive mid-session. /goal takes its text inline; GOALPINE is
  // a distinctive token to locate wherever the directive lands (system vs context).
  await type('/goal Always include the token GOALPINE in every reply.', /GOALPINE/);
  await s.waitIdle(2000, 15000);
  console.log('-- goal set --');

  // Turn 2 — under the new directive. Marker PAPAYATWO.
  await type('Reply with the single word: PAPAYATWO.', /PAPAYATWO/);
  await s.waitIdle(4000, 90000);
  console.log('-- turn 2 idle (goal active) --');
} finally {
  await s.close();
}

console.log('\nDONE.');
console.log('run dir    :', s.runDir);
console.log('tap session:', s.tapSessionId);
console.log('Analyze → reports/output-style-layer.md (diff system[]/messages across the two main turns)');
