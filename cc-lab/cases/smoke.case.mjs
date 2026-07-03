// Smoke test — validates the driver end to end before any real case exists.
// Launches an isolated Claude Code under claude-tap, asks a trivial question,
// waits idle, closes, then asserts: tap trace-session id captured, records loaded
// from the shared sqlite DB, at least one /v1/messages 200 with usage, and
// tty.log is non-empty. Fails meaningfully (timeout, not hang) if the child never
// responds.

import { launch, runDirName } from '../driver/driver.mjs';
import { loadRecords, messages } from '../driver/tap.mjs';
import { statSync } from 'node:fs';
import { join } from 'node:path';

const runDir = join('.lab', runDirName('smoke'));

function assert(cond, msg) {
  if (!cond) { console.error('FAIL:', msg); process.exitCode = 1; throw new Error(msg); }
  console.log('ok  -', msg);
}

const s = await launch({
  runDir,
  claudeArgs: [],
  // A real user run: keep this session out of the child-exclusion path.
  env: { CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
});

console.log('run dir:', s.runDir);

try {
  // Clear startup gate dialogs (folder-trust, external-CLAUDE.md-imports) and
  // wait for the interactive input prompt.
  await s.ready(60000);
  console.log('-- prompt ready --');

  s.send('Say OK and nothing else.');
  await s.waitIdle(4000, 90000);
  console.log('-- turn idle --');
} finally {
  await s.close();
}

// Assertions on the structured evidence layers.
// 1. The tap trace DB captured this session's API traffic.
assert(!!s.tapSessionId, 'captured a tap trace-session id');
const records = loadRecords(s.tapSessionId);
console.log('trace records:', records.length);
assert(records.length > 0, 'trace DB has records for this session');

// 2. At least one real Messages API call with usage was captured.
const msgs = messages(records);
console.log('messages records:', msgs.length);
assert(msgs.length > 0, 'at least one /v1/messages 200 record');
const withUsage = msgs.find((r) => r.response?.body?.usage?.input_tokens != null);
assert(!!withUsage, 'a Messages record carries usage.input_tokens');

// 3. TTY log (unstructured input-channel evidence) is non-empty.
const ttyStat = statSync(join(s.runDir, 'tty.log'));
assert(ttyStat.size > 0, 'tty.log is non-empty');

console.log('\nSMOKE PASSED. tap session:', s.tapSessionId);
