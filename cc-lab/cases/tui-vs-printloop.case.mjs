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
//                                      usage from the "tokens used N" line + session file
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
// Run: node cases/tui-vs-printloop.case.mjs   → prints run dir, dumps usage.json.

import { launch, runDirName } from '../driver/driver.mjs';
import { loadRecords, mainTurns, waitForTrace } from '../driver/tap.mjs';
import { spawn as cspawn } from 'node:child_process';
import { spawn as pspawn } from 'node-pty';
import { mkdirSync, copyFileSync, writeFileSync, existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { homedir } from 'node:os';

const runDir = join('.lab', runDirName('tui-vs-printloop'));
const absRunDir = resolve(runDir);
const CLAUDE_MODEL = 'claude-haiku-4-5-20251001';
const CODEX_JS = 'C:/Users/linxu/nodejs/node_modules/@openai/codex/bin/codex.js';

const TURNS = [
  'In 2-3 sentences, explain what a database index is.',
  'From your previous answer, give one concrete example query that the index would speed up, and why.',
  'Merge your first and second answers into a single final sentence.',
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const stripAnsi = (s) => s.replace(/\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]|\x1b\[[0-?]*[ -/]*[@-~]/g, '');
function assert(cond, msg) {
  if (!cond) { console.error('FAIL:', msg); process.exitCode = 1; }
  else console.log('ok  -', msg);
}

// Persist measurements after every phase so a watchdog kill never loses data.
function writeUsage() {
  try { writeFileSync(join(absRunDir, 'usage.json'), JSON.stringify(usage, null, 2)); } catch { /* best-effort */ }
}

const usage = { modes: {} };

// ── Phase A: claude interactive TUI ──────────────────────────────────
// cc 2.1.226 TUI quirks (measured empirically, see reports/tui-vs-printloop.md):
// 1. After each reply the TUI fires a background "[SUGGESTION MODE]" call; a message
//    sent while that is finishing lands in the CLI-side message QUEUE and stalls
//    (reported queue-stall bug; Escape flushes but also interrupts).
// 2. A single Enter after typing queues the message instead of dispatching it —
//    sending text + Enter + (1.5s) + Enter dispatches reliably (verified).
// The TTY is therefore NOT a reliable sync: poll the tap DB for the actual main-turn
// dispatch, and on timeout Escape-flush + resend.
function claudeRealTurns(sessionId) {
  return mainTurns(loadRecords(sessionId)).filter((r) => {
    const sys = JSON.stringify(r.request?.body?.system ?? '');
    if (sys.includes('SUGGESTION')) return false; // background suggestion calls
    return (r.response?.body?.content ?? []).some((c) => (c.text ?? '').trim().length > 0);
  });
}

async function phaseClaudeTui() {
  const s = await launch({
    runDir,
    model: CLAUDE_MODEL,
    env: { CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
    // Driver tap mode now strips ANTHROPIC_BASE_URL/API_KEY from the child env so
    // it routes vanilla to api.anthropic.com via the copied claudeAiOauth creds
    // (the parent env would otherwise make tap auto-detect the deepseek gateway
    // upstream, where the OAuth Bearer is rejected). Phase B strips the same vars.
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
      console.log(`-- A: turn ${i + 1} dispatched (${ok ? 'tap-confirmed' : 'TIMEOUT'}) --`);
    }
    await s.close();
    usage.modes.claudeTui = {
      tapSessionId: s.tapSessionId,
      turns: claudeRealTurns(s.tapSessionId).map((r) => ({
        input: r.response?.body?.usage?.input_tokens ?? 0,
        output: r.response?.body?.usage?.output_tokens ?? 0,
        cacheRead: r.response?.body?.usage?.cache_read_input_tokens ?? 0,
        cacheCreate: r.response?.body?.usage?.cache_creation_input_tokens ?? 0,
      })),
    };
    writeUsage(); // incremental — the watchdog must not lose this data
    assert(usage.modes.claudeTui.turns.length === 3, `claude TUI: expected 3 main turns, got ${usage.modes.claudeTui.turns.length}`);
  } finally {
    try { await s.close(); } catch { /* already closed */ }
  }
}

// ── Phase B: claude -p loop (fabric openWriteSession pattern) ────────
// Replicates engine/session.mjs openWriteSession exactly: fresh `claude -p` per turn,
// history = ["User: …", "Assistant: …"].join("\n\n") replayed each time, same
// --allowedTools / --permission-mode flags — but spawned via claude-tap so each
// fresh process's API usage lands in the trace DB under its own trace-session UUID.
function phaseClaudePrintLoop() {
  return new Promise(async (resolvePhase) => {
    const pconfig = join(absRunDir, 'pconfig');
    mkdirSync(pconfig, { recursive: true });
    const srcCreds = join(homedir(), '.claude', '.credentials.json');
    if (existsSync(srcCreds)) copyFileSync(srcCreds, join(pconfig, '.credentials.json'));
    writeFileSync(join(pconfig, '.claude.json'), JSON.stringify({ hasCompletedOnboarding: true, theme: 'dark' }));

    // Same vanilla routing as phase A (driver tap strip): drop the parent's
    // provider base-url/keys so -p falls back to the copied OAuth creds and tap
    // routes to api.anthropic.com — both claude modes hit the same upstream.
    const env = { ...process.env, CLAUDE_CONFIG_DIR: pconfig };
    for (const k of Object.keys(env)) {
      if (/^ANTHROPIC_FOUNDRY_|^CLAUDE_CODE_USE_FOUNDRY$|^ANTHROPIC_DEFAULT_|^ANTHROPIC_BASE_URL$|^ANTHROPIC_API_KEY$|^ANTHROPIC_AUTH_TOKEN$/.test(k)) delete env[k];
    }
    const tapBin = join(homedir(), '.local', 'bin', 'claude-tap.exe');
    const history = [];
    const perTurn = [];

    for (let i = 0; i < TURNS.length; i++) {
      history.push(`User: ${TURNS[i]}`);
      const prompt = history.join('\n\n');
      // Prompt goes via STDIN, not argv: measured — `claude -p` truncates a
      // multi-line argv prompt at the first newline (only "User: T1" ever reaches
      // the model; fabric's openWriteSession passes the whole history as one argv
      // arg, so its replay is currently lost on this build — see report).
      const args = ['--tap-no-live', '--tap-no-open', '--tap-no-update-check',
        '--', '-p', '--model', CLAUDE_MODEL,
        '--prompt-suggestions', 'false', // match phase A: no suggestion calls in the measurement
        '--allowedTools', 'Bash,Read,Write,Edit,Glob,Grep',
        '--permission-mode', 'bypassPermissions'];
      const child = cspawn(tapBin, args, { env, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
      child.stdin.end(prompt);
      let stdout = '', stderr = '', tapId = null;
      child.stdout.on('data', (d) => {
        stdout += d;
        const m = String(d).match(/Trace session:\s*([0-9a-f-]{36})/i);
        if (m && !tapId) tapId = m[1];
      });
      child.stderr.on('data', (d) => { stderr += d; });
      const code = await new Promise((r) => child.on('close', r));
      if (code !== 0) throw new Error(`claude -p turn ${i + 1} exited ${code}: ${stderr.slice(0, 300)}`);
      // Reply text from the trace (authoritative); stdout banner-stripping is fragile.
      let reply = stdout, usage_ = {};
      if (tapId) {
        await waitForTrace(tapId, { timeoutMs: 15000 });
        const recs = loadRecords(tapId);
        const main = mainTurns(recs);
        const withText = main.find((r) => (r.response?.body?.content ?? []).some((c) => c.text));
        const text = (withText?.response?.body?.content ?? [])
          .map((c) => c.text ?? '').join('').trim();
        if (text) reply = text;
        const u = withText?.response?.body?.usage ?? main[0]?.response?.body?.usage ?? {};
        usage_ = { input: u.input_tokens ?? 0, output: u.output_tokens ?? 0, cacheRead: u.cache_read_input_tokens ?? 0, cacheCreate: u.cache_creation_input_tokens ?? 0 };
      }
      history.push(`Assistant: ${reply}`);
      perTurn.push({ tapId, reply: reply.slice(0, 120), ...usage_ });
      console.log(`-- B: -p turn ${i + 1} done (tap ${tapId}) --`);
    }
    usage.modes.claudePrintLoop = { perTurn };
    assert(perTurn.length === 3 && perTurn.every((t) => t.tapId), 'claude -p loop: expected 3 captured turns');
    writeUsage();
    resolvePhase();
  });
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

function phaseCodexTui() {
  return new Promise(async (resolvePhase) => {
    const work = join(absRunDir, 'codex-tui-work');
    mkdirSync(work, { recursive: true });
    const term = pspawn(process.execPath, [CODEX_JS, '-c', 'tui.starter_suggestions=false'], {
      name: 'xterm-256color', cols: 140, rows: 40, cwd: work,
    });
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
    // Turn completion = a new token_count entry in our session file (created when
    // the first turn starts; token_count flushes live at turn completion). The
    // Ready status is NOT a sync point — it stays visible while typing.
    const totalTokenCount = () => codexSessionsForCwd(work).reduce((n, f) => n + codexTokenCounts(f).length, 0);
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
        // codex 0.147 quirks (verified empirically): the starter suggestion menu
        // must be disabled (tui.starter_suggestions=false), and a post-reply send
        // needs Enter twice — the first Enter arms the input, the second submits
        // (single Enter leaves the text stuck in the input box).
        term.write(TURNS[i] + '\r');
        await sleep(1500);
        term.write('\r');
        const done = await waitTurn(i + 1, 60000);
        console.log(`-- C: codex TUI turn ${i + 1} done (${done ? 'token_count' : 'TIMEOUT'}) --`);
      }
      term.write('\u0003');
      await sleep(1500);
    } finally {
      try { term.kill(); } catch { /* gone */ }
    }
    const files = codexSessionsForCwd(work);
    const sessionFile = files[0];
    const tokenCounts = sessionFile ? codexTokenCounts(sessionFile) : [];
    usage.modes.codexTui = { sessionFile, tokenCounts };
    assert(files.length >= 1, 'codex TUI: expected a session file for this cwd');
    assert(tokenCounts.length >= 3, `codex TUI: expected >=3 token_count entries, got ${tokenCounts.length}`);
    writeUsage();
    resolvePhase();
  });
}

// ── Phase D: codex exec loop (fresh process per turn, history re-sent) ─
function phaseCodexExecLoop() {
  return new Promise(async (resolvePhase) => {
    const work = join(absRunDir, 'codex-exec-work');
    mkdirSync(work, { recursive: true });
    const history = [];
    const perTurn = [];
    for (let i = 0; i < TURNS.length; i++) {
      history.push(`User: ${TURNS[i]}`);
      const prompt = history.join('\n\n');
      // stdin 'ignore': codex exec reads stdin for extra input and waits forever
      // on an open pipe (measured: "Reading additional input from stdin..." hang).
      // "tokens used N" is printed on STDERR — merge both streams for parsing.
      const child = cspawn(process.execPath, [CODEX_JS, 'exec', '-C', work, '--skip-git-repo-check', prompt], { windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
      let out = '', err = '';
      child.stdout.on('data', (d) => { out += d; });
      child.stderr.on('data', (d) => { err += d; });
      const code = await new Promise((r) => child.on('close', r));
      if (code !== 0) throw new Error(`codex exec turn ${i + 1} exited ${code}`);
      const merged = out + '\n' + err;
      const used = (merged.match(/tokens used\s+([\d,]+)/i) || [])[1];
      const reply = out.replace(/.*?tokens used[\s\S]*$/i, '').trim().slice(-200);
      history.push(`Assistant: ${reply}`);
      perTurn.push({ tokens: used ? Number(used.replace(/,/g, '')) : null, reply });
      console.log(`-- D: codex exec turn ${i + 1} done (tokens used: ${used}) --`);
    }
    usage.modes.codexExecLoop = { perTurn };
    assert(perTurn.every((t) => t.tokens !== null), 'codex exec loop: expected "tokens used" per turn');
    writeUsage();
    resolvePhase();
  });
}

// ── Main ─────────────────────────────────────────────────────────────
// Selective phases via args, e.g. `--phases AB` — needed for cold-cache runs
// (each claude mode measured with a ≥5-min gap so prompt caches expire).
const phases = new Set((process.argv[2]?.match(/--phases=(\w+)/)?.[1] ?? 'ABCD').split(''));
console.log('run dir:', runDir, '| phases:', [...phases].join(''));
setTimeout(() => {
  console.error('WATCHDOG: case exceeded budget');
  writeUsage(); // persist what we have before dying
  process.exit(2);
}, 1200000).unref();

try {
  if (phases.has('A')) await phaseClaudeTui();
  if (phases.has('B')) await phaseClaudePrintLoop();
  if (phases.has('C')) await phaseCodexTui();
  if (phases.has('D')) await phaseCodexExecLoop();
} finally {
  writeUsage();
}

// ── Summary table ────────────────────────────────────────────────────
const sum = (a) => a.reduce((x, y) => x + (y ?? 0), 0);
const tui = usage.modes.claudeTui?.turns ?? [];
const pl = usage.modes.claudePrintLoop?.perTurn ?? [];
const cxs = usage.modes.codexExecLoop?.perTurn ?? [];
console.log('\n=== summary ===');
console.log('claude TUI      (3 turns): input=%d cacheRead=%d cacheCreate=%d output=%d',
  sum(tui.map((t) => t.input)), sum(tui.map((t) => t.cacheRead)), sum(tui.map((t) => t.cacheCreate)), sum(tui.map((t) => t.output)));
console.log('claude -p loop  (3 turns): input=%d cacheRead=%d cacheCreate=%d output=%d',
  sum(pl.map((t) => t.input)), sum(pl.map((t) => t.cacheRead)), sum(pl.map((t) => t.cacheCreate)), sum(pl.map((t) => t.output)));
console.log('codex TUI      (3 turns): tokenCounts=%s', JSON.stringify(usage.modes.codexTui?.tokenCounts ?? []));
console.log('codex exec loop(3 turns): %s', JSON.stringify(cxs.map((t) => t.tokens)));
console.log('\nusage.json written to', join(absRunDir, 'usage.json'));
