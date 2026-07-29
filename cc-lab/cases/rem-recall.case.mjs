// REM features e2e — remember.js CLI + recall.js UserPromptSubmit hook.
//
// Part A (no child): run the dev-clone remember.js three times into a scratch
//   project scope (<runDir>/.claude/memory) and assert file + _meta.json +
//   .claude/rules/MEMORY.md index stamps, plus the overwrite guard.
// Part B (child): seed the isolated CLAUDE_CONFIG_DIR with the LOCAL dev clone of
//   the rem plugin (cache copy + installed_plugins.json + known_marketplaces.json
//   + settings.json enabledPlugins) so the child runs the NEW recall.js hook.
//   A negative prompt (no matching memory tokens) must produce NO injection;
//   a positive prompt (distinctive token) must inject exactly the matching
//   memory body ("Relevant memories (auto-recalled):") and not the others.
//
// Observation: observe:'proxy' (deepseek upstream) — this macOS host has keychain
// auth only, which an isolated CLAUDE_CONFIG_DIR cannot use, and the inherited
// ANTHROPIC_API_KEY is a Kimi key, so claude-tap/vanilla routing cannot auth here.
// The proxy owns upstream/auth; capture lands in <runDir>/http.jsonl.
//
// Sync strategy: assertions need only the first agent REQUEST per prompt — the
// hook's additionalContext lands in it before any response. We never wait for
// turn completion, because the deepseek child occasionally goes tool-happy
// (e.g. tries to Read the recalled memory file) and parks on a TUI approval
// prompt; any such prompt is dismissed with Escape (deny), never approved.
//
// Cost control: two trivial prompts, assertions on the structured capture.

import { launch, runDirName } from '../driver/driver.mjs';
import { execFileSync } from 'node:child_process';
import { cpSync, mkdirSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = fileURLToPath(new URL('.', import.meta.url));
// Test target: commits 08df9db + b5017be. The dev clone's working tree carries
// teammates' in-flight edits, so point REM_DEV_CLONE at a pinned worktree
// (e.g. .scratch/cc-market-b5017be) for a reproducible run.
const DEV_CLONE = process.env.REM_DEV_CLONE
  || resolve(here, '..', '..', '..', 'claude', 'cc-market');
const REM_SRC = join(DEV_CLONE, 'rem');
const REM_VERSION = JSON.parse(readFileSync(join(REM_SRC, '.claude-plugin', 'plugin.json'), 'utf8')).version;
const shared = process.env.CC_MARKET_SHARED || join(DEV_CLONE, 'fabric', 'engine');
const { loadRows, mainTurns } = await import(pathToFileURL(join(shared, 'observe-reader.mjs')).href);

const runDir = join('.lab', runDirName('rem-recall'));
const absRunDir = resolve(runDir);

function assert(cond, msg) {
  if (!cond) { console.error('FAIL:', msg); process.exitCode = 1; throw new Error(msg); }
  console.log('ok  -', msg);
}

// ── Part A: remember.js CLI ──────────────────────────────────────────────

const REMEMBER = join(REM_SRC, 'scripts', 'remember.js');
const today = new Date().toISOString().slice(0, 10);
const [y, m, d] = today.split('-');

function remember(name, type, description, body, extra = []) {
  return execFileSync(
    process.execPath,
    [REMEMBER, '--name', name, '--type', type, '--description', description, '--body', body, '--scope', absRunDir, ...extra],
    { cwd: absRunDir, encoding: 'utf8', windowsHide: true },
  ).trim();
}

mkdirSync(join(absRunDir, '.claude', 'memory'), { recursive: true });

const entries = [
  ['golangbolo-prefs', 'user', 'golangbolo testing preference',
    'The golangbolo test framework prefers table-driven tests executed with the ZQD-7 runner.'],
  ['zephyrine-freeze', 'project', 'zephyrine release freeze',
    'The zephyrine release freeze starts whenever codename MARROW is announced.'],
  ['sourdough-notes', 'reference', 'sourdough hydration notes',
    'Sourdough hydration for this kitchen sits at 78 percent with bread flour.'],
];
for (const [name, type, desc, body] of entries) {
  const out = remember(name, type, desc, body);
  console.log('remember →', out);
}

for (const [name, type, desc] of entries) {
  const file = join(absRunDir, '.claude', 'memory', y, m, d, `${name}.md`);
  assert(existsSync(file), `remember.js wrote ${name}.md`);
  const content = readFileSync(file, 'utf8');
  assert(content.includes(`name: ${name}`), `${name}.md frontmatter has name`);
  assert(content.includes(`description: ${desc}`), `${name}.md frontmatter has description`);
  // Frontmatter type may be flat (`metadata.type: user`, b5017be) or nested
  // (`metadata:\n  type: user`, later working-tree format) — accept both.
  assert(new RegExp(`metadata(\\.type:\\s*${type}|:\\s*\\n\\s+type:\\s*${type})`).test(content),
    `${name}.md frontmatter has metadata type ${type}`);
  assert(!/^(accessed|count|tier|dropped)\s*:/m.test(content), `${name}.md has no volatile frontmatter`);

  const meta = JSON.parse(readFileSync(join(absRunDir, '.claude', 'memory', y, m, d, '_meta.json'), 'utf8'));
  const rec = meta[`${name}.md`];
  assert(rec && rec.accessed === today && rec.count === 1 && rec.tier === 'short',
    `_meta.json entry for ${name} (accessed=${today}, count=1, tier=short)`);

  const index = readFileSync(join(absRunDir, '.claude', 'rules', 'MEMORY.md'), 'utf8');
  assert(index.includes(`${y}/${m}/${d}/${name}.md`) && index.includes(name),
    `MEMORY.md index line for ${name}`);
}

// Overwrite guard: different body without --update must fail; with --update succeeds.
let guardFailed = false;
try {
  remember('golangbolo-prefs', 'user', 'golangbolo testing preference', 'A different body.');
} catch { guardFailed = true; }
assert(guardFailed, 'overwrite without --update is refused');
remember('golangbolo-prefs', 'user', 'golangbolo testing preference',
  'The golangbolo test framework prefers table-driven tests executed with the ZQD-7 runner.',
  ['--update']);
console.log('ok  - overwrite with --update succeeds (body restored)');

// ── Part B: recall.js hook in a real child session ───────────────────────

// Seed the isolated config dir with the LOCAL dev clone of the rem plugin BEFORE
// launch() spawns the child (launch only adds credentials + .claude.json).
const configDir = join(absRunDir, 'config');
const installPath = join(configDir, 'plugins', 'cache', 'cc-market', 'rem', REM_VERSION);
mkdirSync(installPath, { recursive: true });
cpSync(REM_SRC, installPath, { recursive: true });

const mktDir = join(configDir, 'plugins', 'marketplaces', 'cc-market');
mkdirSync(join(mktDir, '.claude-plugin'), { recursive: true });
cpSync(join(DEV_CLONE, '.claude-plugin', 'marketplace.json'), join(mktDir, '.claude-plugin', 'marketplace.json'));

// Sanity: the seeded plugin really carries the NEW hook registration.
const seededHooks = readFileSync(join(installPath, 'hooks', 'hooks.json'), 'utf8');
assert(seededHooks.includes('recall.js'), 'seeded plugin hooks.json registers recall.js (UserPromptSubmit)');

const now = new Date().toISOString();
writeFileSync(join(configDir, 'plugins', 'installed_plugins.json'), JSON.stringify({
  version: 2,
  plugins: {
    'rem@cc-market': [{
      scope: 'user', installPath, version: REM_VERSION,
      installedAt: now, lastUpdated: now,
    }],
  },
}, null, 2));
writeFileSync(join(configDir, 'plugins', 'known_marketplaces.json'), JSON.stringify({
  'cc-market': {
    source: { source: 'github', repo: 'DawnEver/cc-market' },
    installLocation: mktDir,
    lastUpdated: now,
    autoUpdate: false,
  },
}, null, 2));
writeFileSync(join(configDir, 'settings.json'), JSON.stringify({
  enabledPlugins: { 'rem@cc-market': true },
}, null, 2));

const s = await launch({
  runDir,
  observe: 'proxy',
  provider: 'deepseek',
  claudeArgs: [],
  env: {
    CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1',
    // Inherited Kimi provider env must not leak into the child: an empty
    // ANTHROPIC_API_KEY avoids the custom-API-key approval dialog, and the proxy
    // owns the real upstream/model.
    ANTHROPIC_API_KEY: '',
    ANTHROPIC_MODEL: '',
    // recall.js treats any CODEX_HOME as a Codex host and exits silently — the
    // parent shell may export it, so pin it empty for the child.
    CODEX_HOME: '',
    // Running inside a VS Code terminal makes the child show its "Welcome to
    // Claude Code for VS Code" dialog, which swallows submitted prompts.
    TERM_PROGRAM: 'Apple_Terminal',
  },
});

console.log('run dir:', s.runDir);
console.log('capture:', s.jsonlPath);

const MARKER = 'Relevant memories (auto-recalled):';
const msgsJson = (t) => JSON.stringify(t.request?.body?.messages ?? []);

/** Agent requests carry the full tool schema; auxiliary calls (title-gen,
 * classifiers) repeat the prompt text with tools:0 and would false-match. */
const agentRequests = (rows) =>
  mainTurns(rows).filter((t) => (t.request?.body?.tools?.length || 0) > 0);

/**
 * Poll the proxy capture until a NEW agent request appears whose last user
 * message contains `token`. Never waits on turn completion (see header).
 */
async function waitAgentRequest(token, skip = 0, timeoutMs = 120000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    for (const t of agentRequests(loadRows(s.jsonlPath)).slice(skip)) {
      const users = (t.request?.body?.messages ?? []).filter((x) => x.role === 'user');
      if (users.length && JSON.stringify(users[users.length - 1]).includes(token)) return t;
    }
    await new Promise((r) => setTimeout(r, 400));
  }
  throw new Error(`waitAgentRequest: timed out waiting for an agent request containing "${token}"`);
}

/**
 * Send a prompt and wait for its agent request, re-pressing Enter if the TUI
 * left the text sitting in the composer (observed: the second send's '\r' is
 * intermittently swallowed — text visible in the input box, never submitted).
 */
async function sendAndCapture(token, skip = 0) {
  s.send(token.includes('golangbolo')
    ? 'what is my golangbolo testing preference? (answer briefly, no tools needed)'
    : 'what is 2 + 2?');
  const start = Date.now();
  for (;;) {
    try {
      return await waitAgentRequest(token, skip, 10000);
    } catch (e) {
      if (Date.now() - start > 110000) throw e;
      s.key('\r'); // composer still holding the text — submit again
    }
  }
}

let tNeg, t1;
try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // Negative FIRST: no matching memory tokens → hook must stay silent. First
  // also means no replayed history, so the absence check covers the whole body.
  tNeg = await sendAndCapture('2 + 2');
  console.log('-- negative request captured --');

  // Let turn 1 fully finish (stream + stop hook) before typing the next prompt —
  // input sent mid-turn is swallowed by the TUI instead of queued.
  await s.waitIdle(4000, 120000);

  // Positive: a distinctive token matching exactly one memory entry.
  const skip = agentRequests(loadRows(s.jsonlPath)).length;
  t1 = await sendAndCapture('golangbolo', skip);
  console.log('-- positive request captured --');
} finally {
  // Deny/escape any approval prompt the child may have parked on, then close.
  try { s.key('\x1b'); } catch { /* already exited */ }
  await s.close();
}

assert(!!s.jsonlPath, 'session exposes a proxy capture path');

// Negative: the 2+2 request carries no recall injection anywhere. (The entry
// NAMES legitimately appear via the auto-loaded .claude/rules/MEMORY.md rules
// index, so the leak check is on the memory BODIES, which only recall injects.)
const jNeg = msgsJson(tNeg);
assert(!jNeg.includes(MARKER), 'negative prompt: no auto-recalled injection');
assert(!jNeg.includes('ZQD-7') && !jNeg.includes('MARROW') && !jNeg.includes('78 percent'),
  'negative prompt: no memory body leaked');

// Positive: injection present, with the RIGHT entry only.
const j1 = msgsJson(t1);
assert(j1.includes(MARKER), 'positive prompt: request carries the auto-recalled marker');
// Inspect only the injected block: the same request also carries the auto-loaded
// .claude/rules/MEMORY.md index (project rules), which legitimately names the
// other entries — the recall injection itself must not.
const block = j1.slice(j1.indexOf(MARKER), j1.indexOf(MARKER) + 1024);
assert(block.includes('golangbolo-prefs'), 'positive prompt: injection names golangbolo-prefs');
assert(block.includes('ZQD-7'), 'positive prompt: injection carries the memory body');
assert(!block.includes('zephyrine-freeze'), 'positive prompt: unrelated zephyrine memory not injected');
assert(!block.includes('sourdough'), 'positive prompt: unrelated sourdough memory not injected');

console.log('\nREM RECALL E2E PASSED. capture:', s.jsonlPath);
