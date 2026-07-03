// system-prompt-diff — capture the system prompt blocks from a fresh launch
// and write them to a JSON file for comparison across models/providers/configs.
//
// Usage:
//   node cases/system-prompt-diff.case.mjs [--model haiku] [--label default]
// Output: .lab/<run>/system-prompt.json (pretty-printed system blocks)

import { launch, runDirName } from '../driver/driver.mjs';
import { loadRecords, mainTurns, waitForTrace } from '../driver/tap.mjs';
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';

const args = process.argv.slice(2);
const getArg = (flag, def) => {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : def;
};
const model = getArg('--model', 'haiku');
const label = getArg('--label', model);

const runDir = join('.lab', runDirName('sysprompt-' + label));

const s = await launch({ runDir, model, env: { CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' } });
console.log(`run dir: ${s.runDir}  model: ${model}  label: ${label}`);

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // One trivial turn to force a real Messages request (system prompt is on every turn).
  s.send('Say OK and nothing else.');
  await s.waitIdle(4000, 90000);
  console.log('-- turn idle --');
} finally {
  await s.close();
}

if (!s.tapSessionId) {
  console.error('FAIL: no tap session id captured');
  process.exit(1);
}

// Stabilize trace, then extract the system prompt from the first main turn.
await waitForTrace(s.tapSessionId);
const records = loadRecords(s.tapSessionId);
const turns = mainTurns(records);

if (!turns.length) {
  console.error('FAIL: no main turns found');
  process.exit(1);
}

const sys = turns[0].request?.body?.system;
const out = {
  label,
  model,
  tapSessionId: s.tapSessionId,
  runDir: s.runDir,
  systemBlockCount: Array.isArray(sys) ? sys.length : (typeof sys === 'string' ? 1 : 0),
  system: sys,
};

const outPath = join(s.runDir, 'system-prompt.json');
writeFileSync(outPath, JSON.stringify(out, null, 2));
console.log(`\nSystem prompt written to: ${outPath}`);
console.log(`Blocks: ${out.systemBlockCount}`);
if (Array.isArray(sys)) {
  sys.forEach((b, i) => {
    const type = b.type || 'unknown';
    const preview = JSON.stringify(b).slice(0, 120);
    console.log(`  [${i}] ${type}: ${preview}...`);
  });
}

console.log('\nDONE. tap session:', s.tapSessionId);
