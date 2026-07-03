// env-var-matrix (PLAN M3.3) — run one minimal scenario under selected env vars and
// classify where each var manifests:
//   startup-config | API-request | tool-env | UI-render | state/persistence
//
// Each config gets its own fresh launch + one trivial turn. The case COLLECTS
// structured evidence per run (record counts, main-turn max_tokens/model, presence of
// auxiliary model calls, whether a session transcript persisted) and prints a compact
// JSON blob. Classification is written by the parent Claude to reports/env-var-matrix.md.

import { launch } from '../driver/driver.mjs';
import { loadRecords } from '../driver/tap.mjs';
import { readdirSync, existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19) + '-' + Math.random().toString(36).slice(2, 6);

// Vars chosen because each SHOULD surface in a different layer — the point is to
// verify (not assume) which one.
const CONFIGS = [
  { name: 'baseline', env: {} },
  { name: 'disable-nonessential', env: { DISABLE_NON_ESSENTIAL_MODEL_CALLS: '1' } },
  { name: 'max-output-256', env: { CLAUDE_CODE_MAX_OUTPUT_TOKENS: '256' } },
  { name: 'no-persistence', env: {}, noForce: true },
  { name: 'no-alt-screen', env: { CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN: '1' } },
];

/** Count how many files look like session transcripts under the run's config dir. */
function sessionArtifacts(configDir) {
  const hits = [];
  const walk = (dir) => {
    if (!existsSync(dir)) return;
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      const p = join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name.endsWith('.jsonl')) hits.push(p.replace(configDir, ''));
    }
  };
  walk(join(configDir, 'projects'));
  return hits.length;
}

const results = [];

for (const cfg of CONFIGS) {
  const runDir = join('.lab', `${stamp}-envmatrix-${cfg.name}`);
  const env = { ...cfg.env };
  // All runs simulate a normal user (persistence on) EXCEPT the no-persistence probe.
  if (!cfg.noForce) env.CLAUDE_CODE_FORCE_SESSION_PERSISTENCE = '1';

  const s = await launch({ runDir, env });
  console.log(`\n=== ${cfg.name} === ${s.runDir}`);
  try {
    await s.ready(60000);
    s.key('Reply with the single word: PINEAPPLE.');
    await s.waitOutput(/PINEAPPLE/, 8000);
    s.key('\r');
    await s.waitIdle(4000, 90000);
  } finally {
    await s.close();
  }

  const recs = loadRecords(s.tapSessionId);
  const msgReqs = recs.filter((r) => (r.request?.path || '').includes('/v1/messages'));
  const mains = recs.filter(
    (r) => Array.isArray(r.request?.body?.system)
      && (r.request.body.tools?.length || 0) > 0
      && r.response?.body?.usage,
  );
  const main = mains.sort((a, b) => a.turn - b.turn)[0];

  // UI-render signal: the alternate-screen enter escape (ESC[?1049h) in tty.log.
  const tty = readFileSync(join(s.runDir, 'tty.log'), 'utf8');
  const usesAltScreen = tty.includes('\x1b[?1049h');

  results.push({
    config: cfg.name,
    env: env,
    tapSession: s.tapSessionId,
    totalRecords: recs.length,
    messageRequests: msgReqs.length,
    auxRequests: msgReqs.length - mains.length, // title-gen / quota / classifiers
    mainMaxTokens: main?.request?.body?.max_tokens ?? null,
    mainModel: main?.request?.body?.model ?? null,
    sessionTranscripts: sessionArtifacts(s.configDir),
    usesAltScreen,
  });
}

console.log('\n===EVIDENCE-JSON===');
console.log(JSON.stringify(results, null, 2));
console.log('Analyze → reports/env-var-matrix.md');
