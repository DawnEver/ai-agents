// deepseek-model-env-cache — does the "legacy" model-env layout (ANTHROPIC_MODEL +
// tier defaults, NO *_SUPPORTED_CAPABILITIES) still cause multi-turn cache misses on
// the current Claude Code build, vs the ccds layout (tier defaults + FABLE +
// SUPPORTED_CAPABILITIES)?
//
// Two interactive sessions via observe:'proxy' (provider deepseek), same 4 trivial
// user turns each. Asserts on the proxy capture (<runDir>/http.jsonl): per-main-turn
// usage (input / cache_read / cache_creation) parsed from the SSE stream.
//
// Env hygiene: the parent (this) process usually has the ccds vars set. In proxy mode
// the driver's childEnv starts from process.env and ANTHROPIC_DEFAULT_FABLE_* is NOT in
// PROVIDER_ENV_KEYS, so it would leak into the legacy run — delete every provider-ish
// var from process.env up front so each run sees exactly its own `env` block.

import { launch, runDirName } from '../driver/driver.mjs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const shared = process.env.CC_MARKET_SHARED
  || resolve(import.meta.dirname, '..', '..', '..', 'claude', 'cc-market', 'shared');
const { loadRows, mainTurns, pair } = await import(pathToFileURL(join(shared, 'observe-reader.mjs')).href);

// --- sanitize inherited provider env (see header) ---
for (const k of Object.keys(process.env)) {
  if (/^ANTHROPIC_(API_KEY|AUTH_TOKEN|BASE_URL|MODEL$|DEFAULT_)/.test(k)
    || k === 'CLAUDE_CODE_SUBAGENT_MODEL') {
    delete process.env[k];
  }
}

const PRO = 'deepseek-v4-pro[1m]';
const FLASH = 'deepseek-v4-flash';
const CAPS = 'thinking,adaptive_thinking,temperature,effort,max_effort';

const CONFIGS = {
  // The user's old layout: pin ANTHROPIC_MODEL + tier defaults, no capabilities.
  legacy: {
    ANTHROPIC_MODEL: PRO,
    ANTHROPIC_DEFAULT_OPUS_MODEL: PRO,
    ANTHROPIC_DEFAULT_SONNET_MODEL: PRO,
    ANTHROPIC_DEFAULT_HAIKU_MODEL: FLASH,
    CLAUDE_CODE_SUBAGENT_MODEL: PRO,
  },
  // The ccds layout that reportedly caches fine.
  ccds: {
    ANTHROPIC_DEFAULT_FABLE_MODEL: PRO,
    ANTHROPIC_DEFAULT_FABLE_MODEL_SUPPORTED_CAPABILITIES: CAPS,
    ANTHROPIC_DEFAULT_OPUS_MODEL: PRO,
    ANTHROPIC_DEFAULT_OPUS_MODEL_SUPPORTED_CAPABILITIES: CAPS,
    ANTHROPIC_DEFAULT_SONNET_MODEL: PRO,
    ANTHROPIC_DEFAULT_SONNET_MODEL_SUPPORTED_CAPABILITIES: CAPS,
    ANTHROPIC_DEFAULT_HAIKU_MODEL: FLASH,
    ANTHROPIC_DEFAULT_HAIKU_MODEL_SUPPORTED_CAPABILITIES: CAPS,
  },
};

const PROMPTS = [
  'Reply with exactly: ALPHA',
  'Reply with exactly: BRAVO',
  'Reply with exactly: CHARLIE',
  'Reply with exactly: DELTA',
];

/** Extract per-request usage from the SSE response body (message_start + final delta). */
function sseUsage(body) {
  const out = {};
  if (typeof body !== 'string') return out;
  for (const m of body.matchAll(/^data: (\{.*\})$/gm)) {
    let ev; try { ev = JSON.parse(m[1]); } catch { continue; }
    if (ev.type === 'message_start' && ev.message?.usage) Object.assign(out, ev.message.usage);
    if (ev.type === 'message_delta' && ev.usage) Object.assign(out, ev.usage);
  }
  return out;
}

function usageTable(jsonlPath, label) {
  // Title-gen etc. are 1-message, tool-free calls; real conversation turns carry tools.
  const turns = mainTurns(loadRows(jsonlPath))
    .filter((t) => (t.request.body?.tools || []).length > 0);
  console.log(`\n== ${label}: ${turns.length} conversation turns ==`);
  const usage = turns.map((t, i) => {
    const u = sseUsage(t.response.body);
    const row = {
      turn: i + 1,
      model: t.request.modelAfter,
      input: u.input_tokens ?? null,
      cache_read: u.cache_read_input_tokens ?? null,
      cache_create: u.cache_creation_input_tokens ?? null,
      output: u.output_tokens ?? null,
    };
    console.log(JSON.stringify(row));
    return row;
  });
  return { turns, usage };
}

/**
 * Turn sync via evidence layer 1 (the proxy capture), NOT the TTY: poll http.jsonl
 * until the request whose last user message carries `token` has a paired terminal
 * row (response or error). waitIdle races ahead of slow upstreams (observed: the
 * second user turn was still streaming when the session closed), which queued the
 * remaining prompts and made the run look cache-cold.
 */
async function waitTurn(jsonlPath, token, timeoutMs = 240000) {
  const deadline = Date.now() + timeoutMs;
  const hasToken = (e) => {
    const msgs = e.request?.body?.messages;
    if (!Array.isArray(msgs)) return false;
    return JSON.stringify(msgs.at(-1)?.content ?? '').includes(token);
  };
  while (Date.now() < deadline) {
    const hit = pair(loadRows(jsonlPath)).find((e) => hasToken(e) && (e.response || e.error));
    if (hit) return hit;
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error(`waitTurn: no completed request for token "${token}" within ${timeoutMs}ms`);
}

let failed = false;
function check(cond, msg) {
  console.log((cond ? 'ok  - ' : 'FAIL- ') + msg);
  if (!cond) failed = true;
}

const results = {};
for (const [name, env] of Object.entries(CONFIGS)) {
  const runDir = join('.lab', runDirName(`ds-env-${name}`));
  const s = await launch({
    runDir,
    observe: 'proxy',
    provider: 'deepseek',
    model: null,           // env drives the model, not a --model flag
    env,
  });
  console.log(`\n### config=${name}  run dir: ${s.runDir}`);
  try {
    await s.ready(90000);
    for (const p of PROMPTS) {
      const token = p.split(': ')[1]; // ALPHA / BRAVO / …
      s.send(p);
      const done = await waitTurn(s.jsonlPath, token);
      console.log(`-- turn done: ${token} (status ${done.response?.status ?? 'ERR'})`);
      await s.waitIdle(2000, 30000); // let the TUI settle back to the prompt
    }
  } finally {
    await s.close();
  }
  results[name] = usageTable(s.jsonlPath, name);
}

console.log('\n==== ASSERTIONS ====');
for (const [name, { usage }] of Object.entries(results)) {
  check(usage.length >= PROMPTS.length, `${name}: captured >= ${PROMPTS.length} main turns`);
  check(usage.every((u) => u.model && u.model.includes('deepseek')), `${name}: model remapped to deepseek upstream id`);
  check(usage.every((u) => typeof u.cache_read === 'number'), `${name}: usage reports cache_read_input_tokens`);
  const late = usage.slice(1); // turn 1 creates the cache; turns 2+ should read it
  check(late.every((u) => (u.cache_read ?? 0) > 0),
    `${name}: turns 2..n hit the prompt cache (cache_read > 0)`);
}

console.log(failed ? '\nDEEPSEEK-ENV-CACHE: CACHE MISS REPRODUCED (see table)' : '\nDEEPSEEK-ENV-CACHE PASSED (both configs cache)');
process.exitCode = failed ? 1 : 0;
