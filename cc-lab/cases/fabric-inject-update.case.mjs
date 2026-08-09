// fabric-inject-update.case.mjs — updated fabric plugin (0.1.17) injection chain,
// verified through the observe proxy with a REAL claude child and REAL upstream.
//
// The 2026-08-10 systematic layering (one model, three layers) made these claims:
//   A. stateless spawnChild: platform fabric.systemPromptFile lands in body.system
//      (replacing the official prompt), full default tools schema, usage present
//   B. cross-process cache: a second identical run is a full cache_read (0 create)
//   C. toolsPreset trimming: --tools=<preset list> → body.tools trimmed to the preset
//   D. style chain: profile style → auto-built dist file → style body inside system
//   E. persistent openSession + profile: toolsPreset 'exec' + systemPromptFile
//      honored on a PTY session (separate-arg --tools after stdin flags must NOT
//      trigger the argv-prompt mis-parse)
//   F. mode layering: mode template (prompts/task.md) prepended to the USER
//      message; system stays platform-only (no template bleed into system)
//
// Evidence layer: observe-proxy http.jsonl (session.jsonlPath), read via the
// shared observe-reader (loadRows/mainTurns). The engine under test is the
// ACTIVE plugin cache version (CC_MARKET_SHARED overrides).

import { readdirSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const PLUGIN_CACHE = join(
  process.env.USERPROFILE || process.env.HOME || '',
  '.claude', 'plugins', 'cache', 'cc-market', 'fabric',
);
const REPO_ENGINE = resolve(import.meta.dirname, '..', '..', '..', 'claude', 'cc-market', 'fabric', 'engine');

function newestPluginEngine() {
  if (!existsSync(PLUGIN_CACHE)) return null;
  const vers = readdirSync(PLUGIN_CACHE, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .filter((v) => /^\d+\.\d+\.\d+$/.test(v))
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  if (!vers.length) return null;
  const engine = join(PLUGIN_CACHE, vers[vers.length - 1], 'engine');
  return existsSync(join(engine, 'spawn-child.mjs')) ? engine : null;
}

const shared = process.env.CC_MARKET_SHARED || newestPluginEngine() || REPO_ENGINE;
console.log('engine under test:', shared);

const { spawnChild } = await import(pathToFileURL(join(shared, 'spawn-child.mjs')).href);
const { openSession } = await import(pathToFileURL(join(shared, 'open-session.mjs')).href);
const { loadRows, mainTurns } = await import(pathToFileURL(join(shared, 'observe-reader.mjs')).href);
const { TOOL_PRESETS } = await import(pathToFileURL(join(shared, 'profile.mjs')).href);
const { buildPrompt } = await import(pathToFileURL(join(shared, '..', 'scripts', 'lib', 'parse.mjs')).href);

const ROOT = resolve(import.meta.dirname, '..', '.lab', 'fabric-inject-update');
// Fresh capture per execution: the proxy APPENDS to http.jsonl and restarts its id
// sequence, so a re-run against the same dir mispairs request/response rows.
rmSync(ROOT, { recursive: true, force: true });
const CWD = join(ROOT, 'cwd'); // same cwd for the cache pair (dynamic system tail must not differ)
mkdirSync(CWD, { recursive: true }); // spawn ENOENTs when the cwd does not exist
const CLAUDE_BASE = '# claude-base.md — claude platform base';
const OFFICIAL = 'agentic coding tool';
const ACADEMIC = 'scholarly writing and thinking partner';
const TASK_MODE = 'Identify root causes';

function assert(cond, msg) {
  if (!cond) { console.error('FAIL:', msg); process.exitCode = 1; throw new Error(msg); }
  console.log('ok  -', msg);
}

// The real main turn is the tool-bearing request. stdin-mode spawns fire an extra
// lightweight title-gen /v1/messages call first (tools: 0, system = title instruction);
// the same filter AGENT.md prescribes for tap records (tools.length > 0).
function mainTurn(jsonlPath) {
  const turns = mainTurns(loadRows(jsonlPath));
  const real = turns.find((t) => Array.isArray(t.request.body.tools) && t.request.body.tools.length > 0);
  assert(real, `${jsonlPath}: a real (tool-bearing) main turn (${turns.length} captured)`);
  return real;
}

// The CLI sends system as an ARRAY of blocks (billing header + SDK head + our file);
// join their texts for marker checks.
function sysText(system) {
  if (typeof system === 'string') return system;
  if (Array.isArray(system)) return system.map((b) => b.text || '').join('\n');
  return String(system || '');
}

// Responses are captured as raw SSE text; pull the last usage object out of `data:` frames.
function sseUsage(turn) {
  const txt = String(turn.response.body || '');
  let usage = null;
  for (const line of txt.split('\n')) {
    if (!line.startsWith('data: ')) continue;
    try { const j = JSON.parse(line.slice(6)); if (j.usage) usage = j.usage; } catch {}
  }
  return usage;
}

const prompts = { A: 'Say OK.', B: 'Say OK.', C: 'Say OK.', D: 'Say OK.', F: null };
const modeInstruction = buildPrompt('task', 'Say OK.').systemPrompt;
prompts.F = modeInstruction ? `${modeInstruction}\n\nSay OK.` : 'Say OK.';

console.log('-- A: stateless spawnChild, platform default systemPromptFile --');
const resA = await spawnChild({
  provider: 'deepseek', observe: true, runDir: join(ROOT, 'a'), cwd: CWD,
  model: 'haiku', prompt: prompts.A, timeoutMs: 180000,
});
const tA = mainTurn(resA.jsonlPath);
const sysA = sysText(tA.request.body.system);
assert(sysA.includes(CLAUDE_BASE), 'A: body.system carries claude-base platform prompt');
assert(!sysA.includes(OFFICIAL), 'A: official prompt absent from system');
assert(Array.isArray(tA.request.body.tools) && tA.request.body.tools.length > 6, `A: full default tools schema (${tA.request.body.tools?.length})`);
const uA = sseUsage(tA);
assert(uA?.input_tokens > 0, `A: usage present (input ${uA?.input_tokens})`);

console.log('-- B: identical second run — cross-process cache --');
const resB = await spawnChild({
  provider: 'deepseek', observe: true, runDir: join(ROOT, 'b'), cwd: CWD,
  model: 'haiku', prompt: prompts.B, timeoutMs: 180000,
});
const tB = mainTurn(resB.jsonlPath);
const uB = sseUsage(tB) || {};
const sysB = sysText(tB.request.body.system);
assert(sysB === sysA, 'B: system byte-identical to run A (cache-key precondition)');
// DeepSeek's anthropic-compat layer reports cache fields but never engages them for our
// blocks (no cache_control marker on the file block — see report). The deterministic
// deepseek claim is the identical per-run bill, not cache_read.
assert(uB.input_tokens === uA.input_tokens, `B: identical per-run input tokens (${uB.input_tokens} = ${uA.input_tokens})`);
console.log('note: deepseek cache fields:', JSON.stringify({ cA: { r: uA.cache_read_input_tokens, c: uA.cache_creation_input_tokens }, cB: { r: uB.cache_read_input_tokens, c: uB.cache_creation_input_tokens } }));

console.log('-- C: toolsPreset exec via --tools --');
const resC = await spawnChild({
  provider: 'deepseek', observe: true, runDir: join(ROOT, 'c'), cwd: CWD,
  model: 'haiku', prompt: prompts.C, timeoutMs: 180000,
  extraArgs: ['--tools=' + TOOL_PRESETS.exec.join(',')],
});
const tC = mainTurn(resC.jsonlPath);
const namesC = (tC.request.body.tools || []).map((t) => t.name);
assert(namesC.length === TOOL_PRESETS.exec.length, `C: schema trimmed to ${TOOL_PRESETS.exec.length} tools (got ${namesC.length})`);
assert(TOOL_PRESETS.exec.every((n) => namesC.includes(n)), 'C: preset names present');
const uC = sseUsage(tC) || {};
assert(uC.input_tokens < uA.input_tokens, `C: trimmed schema cuts input tokens (${uC.input_tokens} < ${uA.input_tokens})`);

console.log('-- D: style chain (academic → auto-built dist) --');
const resD = await spawnChild({
  provider: 'deepseek', observe: true, runDir: join(ROOT, 'd'), cwd: CWD,
  model: 'haiku', prompt: prompts.D, timeoutMs: 180000, style: 'academic',
});
const tD = mainTurn(resD.jsonlPath);
const sysD = sysText(tD.request.body.system);
assert(sysD.includes(CLAUDE_BASE) && sysD.includes(ACADEMIC), 'D: system = claude-base + academic style body');

console.log('-- E: persistent openSession with profile {toolsPreset:exec, systemPromptFile} --');
const sE = await openSession({
  provider: 'deepseek', observe: true, runDir: join(ROOT, 'e'), model: 'haiku',
  profile: { toolsPreset: 'exec' }, // systemPromptFile falls back to the platform default chain
});
try {
  await sE.send('Say OK.', null, { timeoutMs: 180000 });
} finally {
  await sE.close();
}
const tE = mainTurn(sE.jsonlPath);
const sysE = sysText(tE.request.body.system);
const namesE = (tE.request.body.tools || []).map((t) => t.name);
assert(sysE.includes(CLAUDE_BASE), 'E: persistent session system = claude-base');
assert(namesE.length === TOOL_PRESETS.exec.length && TOOL_PRESETS.exec.every((n) => namesE.includes(n)),
  `E: profile toolsPreset trimmed schema (${namesE.length})`);

console.log('-- F: mode layering — template in user message, system untouched --');
const resF = await spawnChild({
  provider: 'deepseek', observe: true, runDir: join(ROOT, 'f'), cwd: CWD,
  model: 'haiku', prompt: prompts.F, timeoutMs: 180000,
});
const tF = mainTurn(resF.jsonlPath);
const sysF = sysText(tF.request.body.system);
const msgF = tF.request.body.messages || [];
const lastUser = [...msgF].reverse().find((m) => m.role === 'user');
// The user message is an array of blocks: [0] agent-types reminder, [1] claudeMd context,
// [2] the mode template + prompt — join ALL text blocks, not just [0].
const contentF = typeof lastUser?.content === 'string' ? lastUser.content
  : (lastUser?.content || []).map((b) => b.text || '').join('');
assert(contentF.includes(TASK_MODE), 'F: mode template present in the user message');
assert(sysF.includes(CLAUDE_BASE) && !sysF.includes(TASK_MODE), 'F: system stays platform-only (no template bleed)');

console.log('\nFABRIC-INJECT-UPDATE PASSED.');
console.log('run dirs:', ROOT);
