// observe:'proxy' profile — validates the driver's fabric observe-proxy wiring.
// Launches a real interactive Claude Code session that direct-speaks vanilla
// Anthropic HTTP at the cc-market observe proxy, which owns the DeepSeek
// upstream/auth/model-alias. This is the profile that makes a Foundry provider
// observable (claude-tap cannot: Foundry bypasses ANTHROPIC_BASE_URL).
//
// Asserts on the structured capture (<runDir>/http.jsonl via observe-reader):
// at least one main turn with a 200 response and usage.

import { launch, runDirName } from '../driver/driver.mjs';
import { statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const shared = process.env.CC_MARKET_SHARED
  || resolve(import.meta.dirname, '..', '..', '..', 'claude', 'cc-market', 'shared');
const { loadRows, mainTurns } = await import(pathToFileURL(join(shared, 'observe-reader.mjs')).href);

const runDir = join('.lab', runDirName('observe-proxy'));

function assert(cond, msg) {
  if (!cond) { console.error('FAIL:', msg); process.exitCode = 1; throw new Error(msg); }
  console.log('ok  -', msg);
}

const s = await launch({
  runDir,
  observe: 'proxy',
  provider: 'deepseek',
  env: { CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
});

console.log('run dir:', s.runDir);
console.log('capture:', s.jsonlPath);

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  s.send('Say OK and nothing else.');
  await s.waitIdle(4000, 90000);
  console.log('-- turn idle --');
} finally {
  await s.close();
}

// Assertions on the proxy capture.
assert(s.observe === 'proxy' && !!s.jsonlPath, 'session exposes a jsonlPath');
const rows = loadRows(s.jsonlPath);
console.log('captured rows:', rows.length);
assert(rows.length > 0, 'http.jsonl has captured requests');

const turns = mainTurns(rows); // already filtered to 200 /v1/messages, probe excluded
console.log('main turns:', turns.length);
assert(turns.length > 0, 'at least one real Messages turn (quota probe filtered)');
assert(
  turns.some((t) => /"?(output_tokens|usage)"?/.test(t.response.body || '')),
  'a main turn response carries usage'
);
assert(
  turns.some((t) => (t.request.modelAfter || '').includes('deepseek')),
  'model alias remapped to the deepseek upstream id'
);

// TTY log still captured (input-channel evidence).
assert(statSync(join(s.runDir, 'tty.log')).size > 0, 'tty.log is non-empty');

console.log('\nOBSERVE-PROXY PROFILE PASSED.');
