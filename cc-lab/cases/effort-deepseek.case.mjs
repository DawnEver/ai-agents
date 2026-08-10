// effort-deepseek — does the DeepSeek Anthropic-compatible endpoint ACTUALLY change
// behavior across /effort levels?
//
// One interactive session via observe:'proxy' (provider deepseek, ccds env layout with
// the full capability set so the /effort slider shows every level). Walks the slider
// high (default) → xhigh → max → low → ultracode, one probe turn per level, and
// measures from the proxy capture (<runDir>/http.jsonl):
//   - what effort value reaches the WIRE (request.body.output_config.effort) and
//     whether it changes per level (does ultracode send xhigh, per docs?)
//   - cache_read / cache_creation per turn (DeepSeek always reports creation 0 — does
//     an effort switch cold-miss here like on Anthropic, or is DeepSeek's cache key
//     effort-agnostic?)
//   - latency (response.duration_ms), output tokens, response thinking/text block
//     sizes, and answer correctness on a numeric trap question.
//
// Probe: well/snail problem, one variant per level so later turns cannot just repeat
// the previous answer. Expected day = ceil((H-c)/(c-s)) + 1.

import { launch, runDirName } from '../driver/driver.mjs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const shared = process.env.CC_MARKET_SHARED
  || resolve(import.meta.dirname, '..', '..', '..', 'claude', 'cc-market', 'fabric', 'engine');
const { loadRows, mainTurns, pair } = await import(pathToFileURL(join(shared, 'observe-reader.mjs')).href);

// --- sanitize inherited provider env (childEnv starts from process.env) ---
for (const k of Object.keys(process.env)) {
  if (/^ANTHROPIC_(API_KEY|AUTH_TOKEN|BASE_URL|MODEL$|DEFAULT_)/.test(k)
    || k === 'CLAUDE_CODE_SUBAGENT_MODEL') {
    delete process.env[k];
  }
}

const PRO = 'deepseek-v4-pro[1m]';
const FLASH = 'deepseek-v4-flash';
// Declare the full effort capability set so the slider exposes xhigh/max/ultracode.
const CAPS = 'thinking,adaptive_thinking,temperature,effort,xhigh_effort,max_effort';
const ENV = {
  ANTHROPIC_DEFAULT_FABLE_MODEL: PRO,
  ANTHROPIC_DEFAULT_FABLE_MODEL_SUPPORTED_CAPABILITIES: CAPS,
  ANTHROPIC_DEFAULT_OPUS_MODEL: PRO,
  ANTHROPIC_DEFAULT_OPUS_MODEL_SUPPORTED_CAPABILITIES: CAPS,
  ANTHROPIC_DEFAULT_SONNET_MODEL: PRO,
  ANTHROPIC_DEFAULT_SONNET_MODEL_SUPPORTED_CAPABILITIES: CAPS,
  ANTHROPIC_DEFAULT_HAIKU_MODEL: FLASH,
  ANTHROPIC_DEFAULT_HAIKU_MODEL_SUPPORTED_CAPABILITIES: CAPS,
};

// Slider positions observed in this build family (low·medium·high·xhigh·max·ultracode·
// xhigh+workflows). The case reads the LANDED label from the result line rather than
// trusting the position — if the picker shows fewer levels, `landed` records reality.
const SLIDER = ['low', 'medium', 'high', 'xhigh', 'max', 'ultracode', 'xhigh+workflows'];

const LEVELS = [
  { target: 'high',      H: 10, c: 3, s: 2, ans: 8  }, // T1 uses the session default
  { target: 'xhigh',     H: 12, c: 4, s: 3, ans: 9  },
  { target: 'max',       H: 15, c: 5, s: 4, ans: 11 },
  { target: 'low',       H: 20, c: 6, s: 5, ans: 15 },
  { target: 'ultracode', H: 8,  c: 3, s: 2, ans: 6  },
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const runDir = join('.lab', runDirName('effort-deepseek'));

const s = await launch({ runDir, observe: 'proxy', provider: 'deepseek', model: null, env: ENV });
console.log('run dir :', s.runDir);
console.log('capture :', s.jsonlPath);

// --- /effort slider driving (adapted from thinking-cache-recovery.case.mjs) ---

// Match the buffer TAIL only — waitOutput scans the CUMULATIVE buffer, so a stale
// result line from an earlier switch would match immediately on the next.
async function waitTail(re, timeout = 12000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    if (re.test(s.text.slice(-1200))) return true;
    await sleep(100);
  }
  throw new Error(`waitTail: timed out waiting for ${re}`);
}

// /effort is racy: sometimes the submit doesn't open the picker, and a stray ← then
// navigates the main UI to the agents view. Gate arrows on a picker-unique token.
async function openEffortPicker() {
  for (let attempt = 0; attempt < 4; attempt++) {
    await s.waitIdle(600, 8000);
    s.send('/effort');
    try { await waitTail(/Esc to cancel|to adjust/i, 4000); return; }
    catch { s.key('\x1b'); await sleep(500); }
  }
  throw new Error('effort picker did not open after retries');
}

/** Defensive: dismiss any IDE-onboarding gate that slipped past ready() (the VS Code
 *  welcome modal appears asynchronously on first launch and swallows Enter). */
async function dismissGates() {
  for (let i = 0; i < 3; i++) {
    if (/welcome\s*to\s*claude\s*code\s*for|press\s*enter\s*to\s*continue/i.test(s.text.slice(-1200))) {
      s.key('\r');
      await sleep(800);
    } else break;
  }
}

/** Clamp the slider LEFT (low), step RIGHT to target, apply. Returns the LANDED label. */
async function setEffort(target) {
  await openEffortPicker();
  await sleep(300);
  for (let i = 0; i < 6; i++) { s.key('\x1b[D'); await sleep(200); } // clamp → low
  const idx = SLIDER.indexOf(target);
  if (idx < 0) throw new Error(`setEffort: unknown target ${target}`);
  for (let i = 0; i < idx; i++) { s.key('\x1b[C'); await sleep(240); }
  s.key('\r'); // apply
  // Best-effort confirmation only: the result-line text varies by build/direction and
  // its absence does NOT mean the switch failed — the trace (output_config.effort on
  // the next turn's request) is the source of truth. A downgrade (→ low) pops a
  // "Change effort level? … Yes, switch to X" confirm dialog; an upgrade applies
  // directly. The TUI renders spaces as cursor-forward escapes, so stripAnsi
  // word-CONCATENATES the result line ("Seteffortleveltoxhigh").
  const done = /effort\s*level\s*to\s+([a-z][\w+]*)/i;
  const dialog = /(Change\s*effort\s*level|Yes,|switch\s*to|workflow)/i;
  const start = Date.now();
  let landed = null;
  while (Date.now() - start < 8000) {
    const tail = s.text.slice(-800);
    const m = tail.match(done);
    if (m) { landed = m[1].toLowerCase(); break; }
    if (dialog.test(tail)) { s.key('\r'); await sleep(500); }
    await sleep(150);
  }
  await s.waitIdle(1000, 8000);
  console.log(`-- effort → ${target}${landed ? ` (landed label: ${landed})` : ' (no result line captured — verifying via trace)'} --`);
  return landed ?? target;
}

// --- per-turn capture from the proxy capture (evidence layer 1) ---

function sseParts(body) {
  const out = { usage: {}, text: '', thinkingBlocks: 0, thinkingChars: 0 };
  if (typeof body !== 'string') return out;
  for (const m of body.matchAll(/^data: (\{.*\})$/gm)) {
    let ev; try { ev = JSON.parse(m[1]); } catch { continue; }
    if (ev.type === 'message_start') {
      if (ev.message?.usage) Object.assign(out.usage, ev.message.usage);
      for (const b of ev.message?.content ?? []) if (b.type === 'thinking') out.thinkingBlocks++;
    }
    if (ev.type === 'content_block_delta' && ev.delta?.type === 'thinking_delta') {
      out.thinkingChars += ev.delta.thinking?.length ?? 0;
    }
    if (ev.type === 'content_block_delta' && ev.delta?.type === 'text_delta') {
      out.text += ev.delta.text;
    }
    if (ev.type === 'message_delta' && ev.usage) Object.assign(out.usage, ev.usage);
  }
  return out;
}

/**
 * Submit a prompt robustly: type, wait for the input-box echo, then press Enter
 * SEPARATELY. A one-shot write(text+'\r') races the TUI (suggestion popup / late
 * status-bar repaint) on newer builds and can swallow the Enter — observed with the
 * text sitting unsubmitted in the box while http.jsonl stayed empty. Verifies the
 * request actually STARTED (poll the capture) and retries: bare Enter, then
 * Esc-and-retype.
 */
async function submitTurn(prompt, wireToken) {
  // TUI echo matching: the alt-screen renders spaces as cursor-forward escapes, so
  // stripAnsi concatenates words ("deep well" → "deepwell"). Match with \s* between
  // words; use the spaced `wireToken` only against the JSON capture (real spaces).
  const echo = /deep\s*well/;
  for (let attempt = 0; attempt < 3; attempt++) {
    if (attempt === 0) {
      s.key(prompt);
      await s.waitOutput(echo, 8000); // typed echo visible in the box
      await sleep(400);
    } else if (attempt === 1) {
      await sleep(300); // text is likely still in the box — Enter again
    } else {
      s.key('\x1b'); // cancel any lingering draft/popup state
      await sleep(300);
      if (!/bottom\s*of\s*a/.test(s.text)) { // draft was cleared — retype
        s.key(prompt);
        await s.waitOutput(echo, 8000);
        await sleep(400);
      }
    }
    s.key('\r');
    const deadline = Date.now() + 6000;
    let started = false;
    while (Date.now() < deadline) {
      const sent = pair(loadRows(s.jsonlPath)).some((e) =>
        e.request && e.request.path !== '/anthropic/api/hello'
        && JSON.stringify(e.request.body?.messages ?? []).includes(wireToken));
      if (sent) { started = true; break; }
      await sleep(300);
    }
    if (started) return;
    console.log(`[WARN] submit attempt ${attempt + 1} did not start a request — retrying`);
  }
  throw new Error(`submitTurn: request never started after 3 attempts`);
}

// Turn sync via the capture, NOT the TTY (waitIdle races ahead of slow upstreams).
async function waitTurn(token, timeoutMs = 240000) {
  const deadline = Date.now() + timeoutMs;
  const hasToken = (e) => {
    const msgs = e.request?.body?.messages;
    if (!Array.isArray(msgs)) return false;
    return JSON.stringify(msgs.at(-1)?.content ?? '').includes(token);
  };
  while (Date.now() < deadline) {
    const hit = pair(loadRows(s.jsonlPath)).find((e) => hasToken(e) && (e.response || e.error));
    if (hit) return hit;
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error(`waitTurn: no completed request for "${token}" within ${timeoutMs}ms`);
}

let failed = false;
function check(cond, msg) {
  console.log((cond ? 'ok  - ' : 'FAIL- ') + msg);
  if (!cond) failed = true;
}

const rows = [];
let effortUI = 'ok'; // set 'absent' only if the /effort picker itself never opens
try {
  await s.ready(90000);
  console.log('-- prompt ready --');
  for (let i = 0; i < LEVELS.length; i++) {
    const { target, H, c, s: slip, ans } = LEVELS[i];
    if (i > 0) {
      try { await setEffort(target); }
      catch (e) {
        console.log(`[WARN] ${e.message} — continuing at current effort`);
        effortUI = 'absent';
      }
    }
    const prompt = `A snail is at the bottom of a ${H} m deep well. Each day it climbs ${c} m; each night it slides back ${slip} m. Starting from the bottom on day 0, on which day does it first reach the top? Answer with the day number and one short sentence of reasoning.`;
    const token = `deep well`; // contiguous substring of every prompt variant
    await dismissGates();
    await submitTurn(prompt, token);
    const done = await waitTurn(token);
    await s.waitIdle(2000, 30000); // let the TUI settle before the next /effort
    rows.push({ level: target, ans, entry: done });
    console.log(`-- turn ${i + 1} done @ ${target} (status ${done.response?.status ?? 'ERR'}) --`);
  }
} finally {
  await s.close();
}

// --- table ---
console.log('\n==== PER-LEVEL TABLE ====');
console.log('effort UI on deepseek path:', effortUI);
const turns = mainTurns(loadRows(s.jsonlPath))
  .filter((t) => (t.request.body?.tools || []).length > 0);
console.log('conversation turns captured:', turns.length);
const summary = turns.map((t, i) => {
  const body = t.request.body;
  const parts = sseParts(t.response.body);
  const expected = LEVELS[i]?.ans;
  const answerOK = expected != null && new RegExp(`\\b${expected}\\b`).test(parts.text);
  const row = {
    turn: i + 1,
    requested: LEVELS[i]?.target ?? '?',
    wire_effort: body?.output_config?.effort ?? null,
    thinking_req: body?.thinking ?? null,
    model: t.request.modelAfter,
    input: parts.usage.input_tokens ?? null,
    cache_read: parts.usage.cache_read_input_tokens ?? null,
    cache_create: parts.usage.cache_creation_input_tokens ?? null,
    output: parts.usage.output_tokens ?? null,
    dur_ms: t.response.duration_ms ?? null,
    text_chars: parts.text.length,
    think_blocks: parts.thinkingBlocks,
    think_chars: parts.thinkingChars,
    answer_ok: answerOK,
  };
  console.log(JSON.stringify(row));
  return row;
});

console.log('\n==== ASSERTIONS ====');
check(turns.length >= LEVELS.length, `captured >= ${LEVELS.length} conversation turns (got ${turns.length})`);
check(summary.every((r) => r.model && r.model.includes('deepseek')), 'every turn remapped to the deepseek upstream id');
const wireEfforts = [...new Set(summary.map((r) => r.wire_effort).filter(Boolean))];
console.log(`distinct wire effort values: ${JSON.stringify(wireEfforts)}`);
check(summary.every((r) => typeof r.cache_read === 'number'), 'usage reports cache_read_input_tokens on every turn');
const cold = summary.filter((r) => r.cache_read === 0);
console.log(`turns with cache_read = 0 (cold): ${cold.length} ${cold.map((r) => `T${r.turn}@${r.wire_effort}`).join(', ')}`);

console.log(failed ? '\nEFFORT-DEEPSEEK: FAILED (see above)' : '\nEFFORT-DEEPSEEK PASSED (capture sanity)');
process.exitCode = failed ? 1 : 0;
