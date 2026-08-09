// tui-vs-printloop.case.mjs — same 3-turn task × 4 execution modes, token usage measured.
//
// Modes compared (identical task, same 3 turns):
//   A. claude interactive TUI        — one persistent session, PTY-driven (driver)
//   B. claude -p loop                — fabric engine/session.mjs openWriteSession pattern:
//                                      fresh `claude -p --allowedTools` process PER TURN with
//                                      the whole history replayed in the prompt (verbatim
//                                      spawn args), routed through claude-tap so each
//                                      fresh process's usage is captured in the tap DB
//   C. codex interactive TUI         — node-pty PTY, usage from ~/.codex/sessions token_count
//   D. codex exec loop               — fresh `codex exec` process per turn, history re-sent,
//                                      usage from session token_count + "tokens used" stderr
//
// Turn tasks (identical text in all modes; T2/T3 reference prior answers so context
// retention is exercised):
//   T1: "In 2-3 sentences, explain what a database index is."
//   T2: "From your previous answer, give one concrete example query that the index
//        would speed up, and why."
//   T3: "Merge your first and second answers into a single final sentence."
//
// Claude models are pinned to the same (haiku) in both claude modes; codex uses its
// configured default in both codex modes. Cross-model token counts are NOT directly
// comparable in absolute terms — the structural signals (harness per fresh process,
// cache read vs creation, history repayment) are the point.
//
// Run: node cases/tui-vs-printloop.case.mjs [--phases=AB] → prints run dir, dumps usage.json.
// --phases: selective phases; run claude modes separately (A then B) with ≥5-min gaps
// for cache-cold numbers — a full ABCD run is warm by construction (warned loudly).

import { launch, runDirName } from '../driver/driver.mjs';
import { loadRecords, mainTurns, waitForTrace } from '../driver/tap.mjs';
import { spawn as cspawn, spawnSync } from 'node:child_process';
import { spawn as pspawn } from 'node-pty';
import { mkdirSync, copyFileSync, writeFileSync, renameSync, existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { homedir } from 'node:os';

const runDir = join('.lab', runDirName('tui-vs-printloop'));
const absRunDir = resolve(runDir);
const CLAUDE_MODEL = 'claude-haiku-4-5-20251001';
const CLAUDE_TOOL_FLAGS = ['--allowedTools', 'Bash,Read,Write,Edit,Glob,Grep'];
// Both claude modes share the same tool allow-list so the measured tool schema is
// identical (SR-010). --permission-mode is deliberately NOT set in either mode:
// bypassPermissions pops a "You are responsible..." startup dialog whose default
// selection is "No, exit", and acceptEdits changes the status bar so ready()'s
// "? for shortcuts" marker never appears. Dropping it from both modes keeps the
// permission instructions identical while deviating from fabric's exact flags —
// documented in reports/tui-vs-printloop.md.

const TURNS = [
  'In 2-3 sentences, explain what a database index is.',
  'From your previous answer, give one concrete example query that the index would speed up, and why.',
  'Merge your first and second answers into a single final sentence.',
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const stripAnsi = (s) => s.replace(/\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]|\x1b\[[0-?]*[ -/]*[@-~]/g, '');
// Fail-fast: a phase that cannot be confirmed must fail the run, never be
// mistaken for a valid measurement (SR-004).
function assert(cond, msg) {
  if (!cond) throw new Error(msg);
  console.log('ok  -', msg);
}

// Handles to kill when the watchdog fires (SR-014): node-pty terminals + spawned children.
const activeChildren = new Set();
function track(child) { activeChildren.add(child); return child; }
function untrack(child) { activeChildren.delete(child); }

// Persist measurements after every phase so a watchdog kill never loses data.
// Atomic (temp + rename) so a kill mid-write cannot truncate the file (SR-014).
function writeUsage() {
  try {
    const p = join(absRunDir, 'usage.json');
    writeFileSync(p + '.tmp', JSON.stringify(usage, null, 2));
    renameSync(p + '.tmp', p);
  } catch { /* best-effort */ }
}

const usage = { modes: {} };

// ── Shared helpers ───────────────────────────────────────────────────
// Resolve the codex JS entry (SR-006): CODEX_CLI_PATH override, else derive the npm
// package from the `codex` shim on PATH (the shim is a shell script; node-pty needs
// the real node + codex.js).
function resolveCodexJs() {
  if (process.env.CODEX_CLI_PATH) return process.env.CODEX_CLI_PATH;
  const where = spawnSync(process.platform === 'win32' ? 'where' : 'which', ['codex'], { encoding: 'utf8', timeout: 10000 });
  if (where.status === 0) {
    const line = (where.stdout.split(/\r?\n/).find((l) => l.trim()) || '').trim();
    if (line) {
      const js = join(resolve(line, '..'), 'node_modules', '@openai', 'codex', 'bin', 'codex.js');
      if (existsSync(js)) return js;
      if (line.endsWith('.js') && existsSync(line)) return line;
    }
  }
  throw new Error('codex CLI not found — install @openai/codex or set CODEX_CLI_PATH to bin/codex.js');
}
const CODEX_JS = resolveCodexJs();

// Isolated config dir + vanilla routing env for the -p children (same shape as the
// driver's tap-mode OAuth path: copied creds, provider-routing vars stripped).
function claudePrintConfig() {
  const pconfig = join(absRunDir, 'pconfig');
  mkdirSync(pconfig, { recursive: true });
  const srcCreds = join(homedir(), '.claude', '.credentials.json');
  if (existsSync(srcCreds)) copyFileSync(srcCreds, join(pconfig, '.credentials.json'));
  writeFileSync(join(pconfig, '.claude.json'), JSON.stringify({ hasCompletedOnboarding: true, theme: 'dark' }));
  const env = { ...process.env, CLAUDE_CONFIG_DIR: pconfig };
  for (const k of Object.keys(env)) {
    if (/^ANTHROPIC_FOUNDRY_|^CLAUDE_CODE_USE_FOUNDRY$|^ANTHROPIC_DEFAULT_|^ANTHROPIC_BASE_URL$|^ANTHROPIC_API_KEY$|^ANTHROPIC_AUTH_TOKEN$/.test(k)) delete env[k];
  }
  return env;
}

// ── Phase A: claude interactive TUI ──────────────────────────────────
// cc 2.1.226 TUI quirks (measured empirically, see reports/tui-vs-printloop.md):
// 1. After each reply the TUI fires a background "[SUGGESTION MODE]" call (real paid
//    tokens — accounted separately as suggestionCost, SR-008); a message sent while
//    that is finishing lands in the CLI-side message QUEUE and stalls (reported
//    queue-stall bug; Escape flushes but also interrupts).
// 2. A single Enter after typing queues the message instead of dispatching it —
//    sending text + Enter + (1.5s) + Enter dispatches reliably (verified).
// The TTY is therefore NOT a reliable sync: poll the tap DB for the actual main-turn
// dispatch, and on timeout Escape-flush + resend.
function claudeRecords(sessionId) {
  return mainTurns(loadRecords(sessionId));
}
// Suggestion-mode calls carry "[SUGGESTION MODE...]" in the LAST USER MESSAGE
// (2.1.226 puts it there, not in the system blocks — verified empirically), so
// scan both.
function claudeIsSuggestion(r) {
  const req = r.request?.body ?? {};
  const last = (req.messages ?? []).slice(-1)[0];
  const hay = JSON.stringify(req.system ?? '') + ' ' + JSON.stringify(last?.content ?? '');
  return hay.includes('SUGGESTION');
}
function claudeRealTurns(sessionId) {
  return claudeRecords(sessionId).filter((r) => {
    if (claudeIsSuggestion(r)) return false; // background suggestion calls
    return (r.response?.body?.content ?? []).some((c) => (c.text ?? '').trim().length > 0);
  });
}
function claudeSuggestionCost(sessionId) {
  return claudeRecords(sessionId).filter(claudeIsSuggestion)
    .map((r) => {
      const u = r.response?.body?.usage ?? {};
      return {
        input: u.input_tokens ?? 0,
        output: u.output_tokens ?? 0,
        cacheRead: u.cache_read_input_tokens ?? 0,
        cacheCreate: u.cache_creation_input_tokens ?? 0,
      };
    });
}
const toUsage = (r) => {
  const u = r.response?.body?.usage ?? {};
  return {
    input: u.input_tokens ?? 0,
    output: u.output_tokens ?? 0,
    cacheRead: u.cache_read_input_tokens ?? 0,
    cacheCreate: u.cache_creation_input_tokens ?? 0,
  };
};

async function phaseClaudeTui() {
  const s = await launch({
    runDir,
    model: CLAUDE_MODEL,
    // Same permission mode + tool allow-list as phase B (SR-010): identical system
    // prompt / tool schema so the harness comparison isolates process architecture.
    claudeArgs: CLAUDE_TOOL_FLAGS,
    env: { CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
    // Driver tap mode strips ANTHROPIC_BASE_URL/API_KEY from the child env so it
    // routes vanilla to api.anthropic.com via the copied claudeAiOauth creds (the
    // parent env would otherwise make tap auto-detect the deepseek gateway upstream,
    // where the OAuth Bearer is rejected). Phase B strips the same vars.
  });
  console.log('-- A: claude TUI launched --');
  try {
    await s.ready(60000);
    const waitDispatched = (i, ms) => new Promise((res) => {
      const t0 = Date.now();
      const iv = setInterval(() => {
        if (claudeRealTurns(s.tapSessionId).length >= i) { clearInterval(iv); res(true); }
        else if (Date.now() - t0 > ms) { clearInterval(iv); res(false); }
      }, 1000);
    });
    for (let i = 0; i < TURNS.length; i++) {
      s.key(TURNS[i] + '\r');        // Enter #1: text + queue/arm
      await sleep(1500);
      s.key('\r');                   // Enter #2: dispatch
      let ok = await waitDispatched(i + 1, 45000);
      if (!ok) {
        s.key('\x1b');               // flush the stalled message queue
        await sleep(1200);
        ok = await waitDispatched(i + 1, 20000);
      }
      if (!ok) {
        s.send(TURNS[i]);            // resend
        ok = await waitDispatched(i + 1, 60000);
      }
      if (!ok) throw new Error(`claude TUI: turn ${i + 1} never dispatched`);
      console.log(`-- A: turn ${i + 1} dispatched (tap-confirmed) --`);
    }
    await s.close();
    usage.modes.claudeTui = {
      tapSessionId: s.tapSessionId,
      turns: claudeRealTurns(s.tapSessionId).map(toUsage),
      // Real paid background calls, reported separately from the main-turn cost (SR-008).
      suggestionCost: claudeSuggestionCost(s.tapSessionId),
    };
    writeUsage(); // incremental — the watchdog must not lose this data
    assert(usage.modes.claudeTui.turns.length === 3, `claude TUI: expected 3 main turns, got ${usage.modes.claudeTui.turns.length}`);
  } finally {
    try { await s.close(); } catch { /* already closed */ }
  }
}

// ── Phase B: claude -p loop (fabric openWriteSession pattern) ────────
// Replicates engine/session.mjs openWriteSession: fresh `claude -p` per turn, history
// = ["User: …", "Assistant: …"].join("\n\n") replayed each time, same tool/permission
// flags — but spawned via claude-tap so each fresh process's API usage lands in the
// trace DB under its own trace-session UUID.
async function phaseClaudePrintLoop() {
  const env = claudePrintConfig();
  const tapBin = join(homedir(), '.local', 'bin', 'claude-tap.exe');
  const history = [];
  const perTurn = [];

  for (let i = 0; i < TURNS.length; i++) {
    history.push(`User: ${TURNS[i]}`);
    const prompt = history.join('\n\n');
    // Prompt goes via STDIN, not argv: measured — `claude -p` truncates a multi-line
    // argv prompt at the first newline (only "User: T1" ever reaches the model;
    // fabric's openWriteSession passes the whole history as one argv arg — observed
    // on claude 2.1.226; see reports/tui-vs-printloop.md).
    const args = ['--tap-no-live', '--tap-no-open', '--tap-no-update-check',
      '--', '-p', '--model', CLAUDE_MODEL,
      '--prompt-suggestions', 'false', // match phase A's main-turn call set (SR-008)
      ...CLAUDE_TOOL_FLAGS];
    const child = track(cspawn(tapBin, args, { env, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] }));
    child.stdin.end(prompt);
    let stdout = '', stderr = '', tapId = null;
    child.stdout.on('data', (d) => {
      stdout += d;
      const m = String(d).match(/Trace session:\s*([0-9a-f-]{36})/i);
      if (m && !tapId) tapId = m[1];
    });
    child.stderr.on('data', (d) => { stderr += d; });
    const code = await new Promise((r) => child.on('close', r));
    untrack(child);
    if (code !== 0) throw new Error(`claude -p turn ${i + 1} exited ${code}: ${stderr.slice(0, 300)}`);
    // Reply text from the trace (authoritative); stdout banner-stripping is fragile.
    let reply = stdout, usage_ = {};
    if (tapId) {
      await waitForTrace(tapId, { timeoutMs: 15000 });
      const main = mainTurns(loadRecords(tapId));
      const withText = main.find((r) => (r.response?.body?.content ?? []).some((c) => c.text));
      const text = (withText?.response?.body?.content ?? [])
        .map((c) => c.text ?? '').join('').trim();
      if (text) reply = text;
      usage_ = toUsage(withText ?? main[0]);
    }
    history.push(`Assistant: ${reply}`);
    perTurn.push({ tapId, reply: reply.slice(0, 120), ...usage_ });
    console.log(`-- B: -p turn ${i + 1} done (tap ${tapId}) --`);
  }
  usage.modes.claudePrintLoop = { perTurn };
  assert(perTurn.length === 3 && perTurn.every((t) => t.tapId), 'claude -p loop: expected 3 captured turns');
  writeUsage();
}

// ── Phase C: codex interactive TUI ───────────────────────────────────
// Codex session files are keyed by the session_meta cwd, NOT by recency — other
// codex sessions (user's own, fabric app-server) write concurrently into the same
// dir. Filter by cwd so we never account another session's tokens.
function codexSessionsForCwd(cwd) {
  const root = join(homedir(), '.codex', 'sessions');
  const found = [];
  (function walk(dir) {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      const p = resolve(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name.endsWith('.jsonl')) {
        const meta = (() => {
          try { return JSON.parse(readFileSync(p, 'utf8').split('\n')[0]); } catch { return null; }
        })();
        if (meta?.payload?.cwd === cwd) found.push([statSync(p).mtimeMs, p]);
      }
    }
  })(root);
  found.sort((a, b) => b[0] - a[0]);
  return found.map(([, p]) => p);
}

function codexTokenCounts(file) {
  if (!file || !existsSync(file)) return [];
  return readFileSync(file, 'utf8').trim().split('\n')
    .map((l) => { try { return JSON.parse(l); } catch { return null; } })
    .filter((l) => l?.type === 'event_msg' && l?.payload?.type === 'token_count')
    .map((l) => l.payload.info.total_token_usage ?? {});
}

// Last assistant text in a codex session file — authoritative reply for history replay.
function codexLastAssistantText(file) {
  if (!file || !existsSync(file)) return '';
  const items = readFileSync(file, 'utf8').trim().split('\n')
    .map((l) => { try { return JSON.parse(l); } catch { return null; } })
    .filter((l) => l?.type === 'response_item' && l?.payload?.role === 'assistant');
  const last = items[items.length - 1];
  return (last?.payload?.content ?? []).map((c) => c.text ?? '').join('').trim();
}

async function phaseCodexTui() {
  const work = join(absRunDir, 'codex-tui-work');
  mkdirSync(work, { recursive: true });
  const term = track(pspawn(process.execPath, [CODEX_JS, '-c', 'tui.starter_suggestions=false'], {
    name: 'xterm-256color', cols: 140, rows: 40, cwd: work,
  }));
  let buf = '';
  term.onData((d) => { buf += d; });
  const plain = () => stripAnsi(buf);
  const waitFor = (re, ms, label) => new Promise((res, rej) => {
    const t0 = Date.now();
    const iv = setInterval(() => {
      if (re.test(plain())) { clearInterval(iv); res(); }
      else if (Date.now() - t0 > ms) { clearInterval(iv); rej(new Error(`timeout waiting ${label}: ${plain().slice(-200)}`)); }
    }, 200);
  });
  // Turn completion = a NEW token_count entry in our session file (token_count
  // flushes live at turn completion). Count entries ABOVE the pre-phase baseline so
  // a stale session file left in this cwd by a prior run cannot short-circuit the
  // wait (SR-013). The Ready status is NOT a sync point — it stays visible while typing.
  const baseline = codexSessionsForCwd(work).reduce((n, f) => n + codexTokenCounts(f).length, 0);
  const totalTokenCount = () => codexSessionsForCwd(work).reduce((n, f) => n + codexTokenCounts(f).length, 0) - baseline;
  const waitTurn = (min, ms) => new Promise((res) => {
    const t0 = Date.now();
    const iv = setInterval(() => {
      if (totalTokenCount() >= min) { clearInterval(iv); res(true); }
      else if (Date.now() - t0 > ms) { clearInterval(iv); res(false); }
    }, 1000);
  });

  try {
    await waitFor(/Ready/, 60000, 'codex TUI startup');
    for (let i = 0; i < TURNS.length; i++) {
      // codex 0.147 quirks (verified empirically): the starter suggestion menu must
      // be disabled (tui.starter_suggestions=false), and a post-reply send needs
      // Enter twice — the first Enter arms the input, the second submits (single
      // Enter leaves the text stuck in the input box).
      term.write(TURNS[i] + '\r');
      await sleep(1500);
      term.write('\r');
      const done = await waitTurn(i + 1, 60000);
      if (!done) throw new Error(`codex TUI: turn ${i + 1} produced no token_count`);
      console.log(`-- C: codex TUI turn ${i + 1} done (token_count) --`);
    }
    term.write('');
    await sleep(1500);
  } finally {
    try { term.kill(); } catch { /* gone */ }
    untrack(term);
  }
  const files = codexSessionsForCwd(work);
  const sessionFile = files[0];
  const tokenCounts = sessionFile ? codexTokenCounts(sessionFile) : [];
  usage.modes.codexTui = { sessionFile, tokenCounts };
  assert(files.length >= 1, 'codex TUI: expected a session file for this cwd');
  assert(tokenCounts.length >= 3, `codex TUI: expected >=3 token_count entries, got ${tokenCounts.length}`);
  writeUsage();
}

// ── Phase D: codex exec loop (fresh process per turn, history re-sent) ─
// Usage per turn comes from the exec session file's token_count (input/cached/output
// separately — SR-003); "tokens used N" (stderr) is kept as a cross-check. The reply
// for history replay is the session file's last assistant text (full, untruncated —
// SR-002/SR-012).
async function phaseCodexExecLoop() {
  const work = join(absRunDir, 'codex-exec-work');
  mkdirSync(work, { recursive: true });
  const history = [];
  const perTurn = [];
  for (let i = 0; i < TURNS.length; i++) {
    history.push(`User: ${TURNS[i]}`);
    const prompt = history.join('\n\n');
    // stdin 'ignore': codex exec reads stdin for extra input and waits forever on an
    // open pipe (measured: "Reading additional input from stdin..." hang).
    const child = track(cspawn(process.execPath, [CODEX_JS, 'exec', '-C', work, '--skip-git-repo-check', prompt], { windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] }));
    let out = '', err = '';
    child.stdout.on('data', (d) => { out += d; });
    child.stderr.on('data', (d) => { err += d; });
    const code = await new Promise((r) => child.on('close', r));
    untrack(child);
    if (code !== 0) throw new Error(`codex exec turn ${i + 1} exited ${code}`);
    await sleep(1200); // let the session file flush
    const files = codexSessionsForCwd(work);
    const sessionFile = files[0];
    const counts = sessionFile ? codexTokenCounts(sessionFile) : [];
    const lastCount = counts[counts.length - 1] ?? {};
    const reply = codexLastAssistantText(sessionFile) || out.trim();
    const merged = out + '\n' + err;
    const used = (merged.match(/tokens used\s+([\d,]+)/i) || [])[1];
    history.push(`Assistant: ${reply}`);
    perTurn.push({
      tokens: used ? Number(used.replace(/,/g, '')) : null,
      input: lastCount.input_tokens ?? null,
      cached: lastCount.cached_input_tokens ?? null,
      cacheWrite: lastCount.cache_write_input_tokens ?? null,
      output: lastCount.output_tokens ?? null,
      sessionFile,
      reply: reply.slice(0, 120),
    });
    console.log(`-- D: codex exec turn ${i + 1} done (tokens used: ${used}) --`);
  }
  usage.modes.codexExecLoop = { perTurn };
  assert(perTurn.every((t) => t.tokens !== null), 'codex exec loop: expected "tokens used" per turn');
  assert(perTurn.every((t) => t.input !== null), 'codex exec loop: expected token_count per turn');
  writeUsage();
}

// ── Main ─────────────────────────────────────────────────────────────
// Selective phases via args, e.g. `--phases AB` — run each claude mode as its own
// invocation with ≥5-min gaps for cache-cold numbers (SR-011).
const phases = new Set((process.argv[2]?.match(/--phases=(\w+)/)?.[1] ?? 'ABCD').split(''));
console.log('run dir:', runDir, '| phases:', [...phases].join(''));
if (['A', 'B', 'C', 'D'].every((p) => phases.has(p))) {
  console.warn('WARNING: full ABCD run is cache-warm by construction (A warms B, B warms C/D). '
    + 'For cold numbers run --phases=A and --phases=B as separate invocations with a >=5-min gap.');
}
setTimeout(() => {
  console.error('WATCHDOG: case exceeded budget');
  for (const c of activeChildren) { try { c.kill?.(); } catch { /* already gone */ } }
  writeUsage(); // persist what we have before dying (atomic)
  process.exit(2);
}, 1200000).unref();

try {
  if (phases.has('A')) await phaseClaudeTui();
  if (phases.has('B')) await phaseClaudePrintLoop();
  if (phases.has('C')) await phaseCodexTui();
  if (phases.has('D')) await phaseCodexExecLoop();
  usage.status = 'complete';
} catch (e) {
  usage.status = 'failed';
  usage.error = String(e.message ?? e);
  writeUsage();
  throw e;
} finally {
  writeUsage();
}

// ── Summary table ────────────────────────────────────────────────────
const sum = (a) => a.reduce((x, y) => x + (y ?? 0), 0);
const tui = usage.modes.claudeTui?.turns ?? [];
const sug = usage.modes.claudeTui?.suggestionCost ?? [];
const pl = usage.modes.claudePrintLoop?.perTurn ?? [];
const cxs = usage.modes.codexExecLoop?.perTurn ?? [];
console.log('\n=== summary ===');
console.log('claude TUI      (3 turns): input=%d cacheRead=%d cacheCreate=%d output=%d',
  sum(tui.map((t) => t.input)), sum(tui.map((t) => t.cacheRead)), sum(tui.map((t) => t.cacheCreate)), sum(tui.map((t) => t.output)));
console.log('claude TUI      suggestion calls (%d): input=%d cacheRead=%d cacheCreate=%d output=%d',
  sug.length, sum(sug.map((t) => t.input)), sum(sug.map((t) => t.cacheRead)), sum(sug.map((t) => t.cacheCreate)), sum(sug.map((t) => t.output)));
console.log('claude -p loop  (3 turns): input=%d cacheRead=%d cacheCreate=%d output=%d',
  sum(pl.map((t) => t.input)), sum(pl.map((t) => t.cacheRead)), sum(pl.map((t) => t.cacheCreate)), sum(pl.map((t) => t.output)));
console.log('codex TUI      (3 turns): tokenCounts=%s', JSON.stringify(usage.modes.codexTui?.tokenCounts ?? []));
console.log('codex exec loop(3 turns): %s', JSON.stringify(cxs.map((t) => ({ tokens: t.tokens, input: t.input, cached: t.cached, output: t.output }))));
console.log('\nusage.json written to', join(absRunDir, 'usage.json'));
