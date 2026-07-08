// thinking-cache — does toggling thinking mode mid-session break prompt-cache hits?
//
// Flow: launch → trivial msg #1 → waitIdle → toggle thinking → trivial msg #2 →
// waitIdle → close → print run dir + tap session id. Analysis (cache_read vs
// cache_creation across the two turns, and the system/thinking diff) is done by the
// parent Claude against the trace DB and written to reports/thinking-cache.md.
//
// Thinking control (empirically verified in this build, cc 2.1.199): reasoning
// effort is the `/effort` slash command (status bar shows "●high · /effort").
// Shift+Tab only cycles PERMISSION modes (accept-edits/plan), not thinking — a
// confirmed no-op for this question. So we switch effort via the /effort picker
// mid-session and compare the two turns' cache usage + thinking/system blocks.

import { launch, runDirName } from '../driver/driver.mjs';
import { loadRecords, mainTurns } from '../driver/tap.mjs';
import { join } from 'node:path';

const runDir = join('.lab', runDirName('thinking-cache'));

const s = await launch({
  runDir,
  // This question is model-specific (needs the /effort reasoning slider), so pin a
  // reasoning-capable model — but Sonnet, not Opus, to keep the run cheap.
  model: 'claude-sonnet-5',
  env: { CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
});

console.log('run dir:', s.runDir);

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // Turn 1 — establish the cache with a trivial message.
  s.send('Reply with the single word: apple.');
  await s.waitIdle(4000, 90000);
  console.log('-- turn 1 idle --');

  // Switch reasoning effort mid-session via the /effort picker. It is a HORIZONTAL
  // slider (low·medium·high·xhigh·max·…) controlled by ←/→, confirmed with Enter.
  // Match picker-specific text ("adjust"), not the status-bar word "effort".
  // Left twice from the default 'high' lands well below it; the exact landing level
  // is read back from the trace — we only need it to DIFFER from turn 1.
  s.send('/effort');
  await s.waitOutput(/to adjust|Faster|Smarter/, 15000);
  s.key('\x1b[D'); await s.waitIdle(400, 6000); // ← lower one step
  s.key('\x1b[D'); await s.waitIdle(400, 6000); // ← lower another step
  s.key('\r');                                  // confirm slider position
  // Claude Code then pops a cache-invalidation confirmation:
  //   "This conversation is cached for the current effort level. Switching to low
  //    means the full history gets re-read on your next message. 1. Yes … 2. No …"
  // (Its very existence is a finding.) Accept it (option 1 / Enter).
  await s.waitOutput(/switch to|Change effort level/i, 12000);
  s.key('\r');
  await s.waitIdle(1500, 10000);
  console.log('-- switched effort via /effort (2× left) + confirmed --');

  // Turn 2 — trivial message under the new (lower) effort/thinking state.
  // Type first, confirm the text actually landed in the input, THEN submit.
  s.key('Reply with the single word: banana.');
  await s.waitOutput(/banana/, 8000);
  s.key('\r');
  await s.waitIdle(4000, 90000);
  console.log('-- turn 2 idle --');
} finally {
  await s.close();
}

// Lightweight guard: verify the session produced the expected two turns with
// different effort levels and a busted prompt cache. Full analysis (cache-key
// dimension, system/thinking diff) is done by the parent Claude against the trace
// DB and written to reports/thinking-cache.md — this only confirms the action
// actually happened.
if (s.tapSessionId) {
  const records = loadRecords(s.tapSessionId);
  const turns = mainTurns(records);
  if (turns.length < 2) {
    console.error('FAIL: expected >= 2 main turns, got', turns.length);
    process.exitCode = 1;
  } else {
    const t1 = turns[0].request?.body?.thinking;
    const t2 = turns[1].request?.body?.thinking;
    const u1 = turns[0].response?.body?.usage ?? {};
    const u2 = turns[1].response?.body?.usage ?? {};
    const thinkingChanged = JSON.stringify(t1) !== JSON.stringify(t2);
    const cacheBusted = (u2.cache_read_input_tokens ?? 0) < (u1.cache_read_input_tokens ?? 0)
      || (u2.cache_creation_input_tokens ?? 0) > (u1.cache_creation_input_tokens ?? 0);
    console.log('turn 1: thinking=%s cache_read=%d cache_create=%d',
      JSON.stringify(t1), u1.cache_read_input_tokens ?? 0, u1.cache_creation_input_tokens ?? 0);
    console.log('turn 2: thinking=%s cache_read=%d cache_create=%d',
      JSON.stringify(t2), u2.cache_read_input_tokens ?? 0, u2.cache_creation_input_tokens ?? 0);
    if (!thinkingChanged) {
      console.error('FAIL: thinking/effort did not change between turns');
      process.exitCode = 1;
    }
    if (!cacheBusted) {
      console.error('FAIL: prompt cache was not invalidated');
      process.exitCode = 1;
    }
    if (thinkingChanged && cacheBusted) {
      console.log('ok  - thinking changed + cache busted');
    }
  }
}

console.log('\nDONE.');
console.log('run dir   :', s.runDir);
console.log('tap session:', s.tapSessionId);
