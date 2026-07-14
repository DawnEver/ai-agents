// long-running-live.case.mjs — live measurement of fabric Haiku multi-turn vs fork
// token consumption. Validates the offline cost model in .scratch/long-running-cost-model.mjs
//
// Question: what are the actual per-turn token costs when using:
//   1. fabric call with Haiku (single-turn baseline)
//   2. fabric spawn_session + session_send with Haiku (multi-turn, persistent session)
//   3. /fork subagent (CC built-in, context-by-reference)
//
// Method: launch CC under claude-tap with fabric MCP registered. The parent CC is
// Sonnet (reliable tool use). All Haiku child processes (fabric's claude children,
// fork subagent) inherit ANTHROPIC_BASE_URL from claude-tap, so their API traffic
// lands in the same tap trace. Filter by model to separate parent (sonnet) from
// children (haiku).
//
// Run: node cases/long-running-live.case.mjs
// Then: parent Claude reads the tap trace and writes findings

import { launch, runDirName } from '../driver/driver.mjs';
import { loadRecords, mainTurns, summarize, messages } from '../driver/tap.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const runDir = join('.lab', runDirName('long-running-live'));

// ── Setup: register fabric MCP ──────────────────────────────────────────

function fabricMCPPath() {
  if (process.env.FABRIC_MCP_PATH) return process.env.FABRIC_MCP_PATH;
  return resolve(
    fileURLToPath(new URL('.', import.meta.url)),
    '..', '..', '..', 'claude', 'cc-market', 'fabric', 'scripts', 'mcp-server.mjs',
  );
}

function setupFabricMCP(configDir) {
  const mcpJsonPath = join(configDir, '.mcp.json');
  const mcpConfig = {
    mcpServers: {
      fabric: {
        command: 'node',
        args: [fabricMCPPath()],
      },
    },
  };
  mkdirSync(configDir, { recursive: true });
  writeFileSync(mcpJsonPath, JSON.stringify(mcpConfig, null, 2));
  console.log('fabric MCP registered at', mcpJsonPath);
}

// ── Helpers ────────────────────────────────────────────────────────────

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function assert(cond, msg) {
  if (!cond) { console.error('FAIL:', msg); process.exitCode = 1; }
  else console.log('ok  -', msg);
}

// ── Launch ─────────────────────────────────────────────────────────────

const absRunDir = resolve(runDir);
const configDir = join(absRunDir, 'config');
setupFabricMCP(configDir);

const s = await launch({
  runDir,
  model: 'claude-haiku-4-5-20251001', // Haiku parent to avoid rate limits
  claudeArgs: [],
  observe: 'tap',
  env: {
    CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1',
    CLAUDE_CODE_ENABLE_ALL_TOOLS: '1',
  },
});
console.log('run dir:', s.runDir);

setTimeout(() => { console.error('WATCHDOG: case exceeded budget'); process.exit(2); }, 300000).unref();

const W = async (re, to) => { try { await s.waitOutput(re, to); return true; } catch { return false; } };
const idle = async (ms, to) => { try { await s.waitIdle(ms, to); } catch { /* animations */ } };
const K = (seq) => { try { s.key(seq); } catch { /* exited */ } };

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // ═══════════════════════════════════════════════════════════════════════
  // Turn 1: Fabric call with Haiku (single-turn baseline)
  // ═══════════════════════════════════════════════════════════════════════
  K(`Use the fabric MCP tool to call the "claude" provider with model "claude-haiku-4-5-20251001" and resultMode "full".
Task: "In one sentence, explain what a Rust mutex does."
Do NOT read any files. Just make the tool call and show the result.`);
  await W(/mutex|Mutex|sentence/, 120000);
  await idle(3000, 30000);
  console.log('-- turn 1: fabric call haiku done --');

  // Check mid-run tap capture
  {
    const mid = loadRecords(s.tapSessionId);
    const midMsgs = messages(mid);
    console.log(`  mid-run tap: ${mid.length} records, ${midMsgs.length} messages`);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Turn 2: /fork subagent — equivalent task
  // ═══════════════════════════════════════════════════════════════════════
  K(`/fork In one sentence, explain what a Rust mutex does.`);
  await W(/mutex|Mutex/, 120000);
  await idle(5000, 60000);
  console.log('-- turn 2: fork subagent done --');

  // ═══════════════════════════════════════════════════════════════════════
  // Turn 3: Fabric spawn_session + session_send with Haiku
  // ═══════════════════════════════════════════════════════════════════════
  K(`Use fabric spawn_session to create a session with provider "claude" and model "claude-haiku-4-5-20251001".
Then use session_send to ask: "In one sentence, explain what a Rust trait does."
Report the session ID and the response.`);
  await W(/trait|Trait|sentence/, 120000);
  await idle(3000, 30000);
  console.log('-- turn 3: fabric session done --');

  // Settle
  await idle(5000, 30000);
  console.log('-- settled --');

} finally {
  await s.close();
  // Give claude-tap time to flush
  await sleep(2000);
}

// ═══════════════════════════════════════════════════════════════════════
// Tap Trace Analysis
// ═══════════════════════════════════════════════════════════════════════

console.log('\ntap session:', s.tapSessionId);
assert(!!s.tapSessionId, 'captured a tap trace-session id');

const records = loadRecords(s.tapSessionId);
console.log('total tap records:', records.length);
assert(records.length > 0, 'trace DB has records');

// Filter main turns (parent CC — Sonnet)
const allTurns = mainTurns(records);
console.log('main turns (parent CC):', allTurns.length);

// Filter ALL /v1/messages records by model to find Haiku children
// (fabric claude children, fork subagent)
const allMsgs = messages(records);
const haikuRecords = allMsgs.filter((r) => {
  const model = r.request?.body?.model || '';
  return model.includes('haiku');
});
const sonnetRecords = allMsgs.filter((r) => {
  const model = r.request?.body?.model || '';
  return model.includes('sonnet');
});

console.log(`\nall /v1/messages: ${allMsgs.length}`);
console.log(`  sonnet (parent CC): ${sonnetRecords.length}`);
console.log(`  haiku (children):   ${haikuRecords.length}`);

// ── Parent CC turns (Sonnet) ───────────────────────────────────────────
console.log('\n## Parent CC Turns (Sonnet)\n');
console.log('| Turn | Input tok | Output tok | Cache read | Cache create |');
console.log('|---:|---:|---:|---:|---:|');

let parentTotalIn = 0, parentTotalOut = 0, parentTotalCacheR = 0, parentTotalCacheC = 0;

for (const r of sonnetRecords) {
  const s = summarize(r);
  parentTotalIn += s.usage.input_tokens;
  parentTotalOut += s.usage.output_tokens;
  parentTotalCacheR += s.usage.cache_read_input_tokens;
  parentTotalCacheC += s.usage.cache_creation_input_tokens;
  console.log(`| ${s.turn} | ${s.usage.input_tokens} | ${s.usage.output_tokens} | ${s.usage.cache_read_input_tokens} | ${s.usage.cache_creation_input_tokens} |`);
}

console.log(`\n| **Total** | **${parentTotalIn}** | **${parentTotalOut}** | **${parentTotalCacheR}** | **${parentTotalCacheC}** |`);

// ── Haiku child turns (fabric claude children + fork) ──────────────────
console.log('\n## Haiku Child Turns (fabric claude children + fork)\n');
console.log('| # | Model | Input tok | Output tok | System prompt chars | Likely source |');
console.log('|---:|---|---:|---:|---:|');

let childTotalIn = 0, childTotalOut = 0;

haikuRecords.forEach((r, i) => {
  const s = summarize(r);
  childTotalIn += s.usage.input_tokens;
  childTotalOut += s.usage.output_tokens;
  const sysLen = Array.isArray(s.system)
    ? s.system.reduce((sum, b) => sum + (typeof b.text === 'string' ? b.text.length : 0), 0)
    : 0;
  // Heuristic: fork subagent has tools in the request, fabric claude children don't
  const hasTools = Array.isArray(s.tools) && s.tools.length > 0;
  const source = hasTools ? 'fork subagent' : 'fabric claude child';
  console.log(`| ${i + 1} | ${s.model || '?'} | ${s.usage.input_tokens} | ${s.usage.output_tokens} | ${sysLen} | ${source} |`);
});

console.log(`\n| **Total** | | **${childTotalIn}** | **${childTotalOut}** | | |`);

// ── Cost comparison ────────────────────────────────────────────────────
const PRICING = {
  sonnet: { input: 3, output: 15 },
  haiku:  { input: 1, output: 5 },
};

function cost(model, inputTok, outputTok) {
  const p = PRICING[model] || PRICING.haiku;
  return (inputTok / 1e6) * p.input + (outputTok / 1e6) * p.output;
}

const parentCost = cost('sonnet', parentTotalIn, parentTotalOut);
const childCost = cost('haiku', childTotalIn, childTotalOut);

console.log('\n## Cost Summary\n');
console.log(`Parent CC (Sonnet): ${parentTotalIn} in + ${parentTotalOut} out = $${parentCost.toFixed(4)}`);
console.log(`Children (Haiku):  ${childTotalIn} in + ${childTotalOut} out = $${childCost.toFixed(4)}`);
console.log(`**Total: $${(parentCost + childCost).toFixed(4)}**`);

// ── Per-mechanism breakdown ────────────────────────────────────────────
console.log('\n## Per-Mechanism Token Breakdown\n');

// Group haiku records by source (fork vs fabric)
const forkTurns = haikuRecords.filter((r) => {
  const body = r.request?.body;
  return Array.isArray(body?.tools) && body.tools.length > 0;
});
const fabricClaudeTurns = haikuRecords.filter((r) => {
  const body = r.request?.body;
  return !Array.isArray(body?.tools) || body.tools.length === 0;
});

const forkIn = forkTurns.reduce((s, r) => s + (r.request?.body?.usage ? 0 : summarize(r).usage.input_tokens), 0);
const forkOut = forkTurns.reduce((s, r) => s + (summarize(r).usage.output_tokens), 0);
// Recalculate properly
let forkTotalIn = 0, forkTotalOut = 0;
for (const r of forkTurns) {
  const su = summarize(r);
  forkTotalIn += su.usage.input_tokens;
  forkTotalOut += su.usage.output_tokens;
}

let fabricTotalIn = 0, fabricTotalOut = 0;
for (const r of fabricClaudeTurns) {
  const su = summarize(r);
  fabricTotalIn += su.usage.input_tokens;
  fabricTotalOut += su.usage.output_tokens;
}

console.log(`Fork subagent:   ${forkTurns.length} turns, ${forkTotalIn} in + ${forkTotalOut} out = $${cost('haiku', forkTotalIn, forkTotalOut).toFixed(4)}`);
console.log(`Fabric claude:   ${fabricClaudeTurns.length} turns, ${fabricTotalIn} in + ${fabricTotalOut} out = $${cost('haiku', fabricTotalIn, fabricTotalOut).toFixed(4)}`);

// Per-turn averages
if (fabricClaudeTurns.length > 0) {
  console.log(`\nFabric avg/turn: ${Math.round(fabricTotalIn / fabricClaudeTurns.length)} in + ${Math.round(fabricTotalOut / fabricClaudeTurns.length)} out`);
}
if (forkTurns.length > 0) {
  console.log(`Fork avg/turn:   ${Math.round(forkTotalIn / forkTurns.length)} in + ${Math.round(forkTotalOut / forkTurns.length)} out`);
}

// ── Fork notification analysis ─────────────────────────────────────────
console.log('\n## Fork Notifications (from session jsonl)\n');

const { findTranscripts, loadTranscript, taskNotifications } = await import('../driver/session.mjs');
const { main } = findTranscripts(s.configDir);
for (const mf of main) {
  const entries = loadTranscript(mf);
  const notifs = taskNotifications(entries);
  for (const n of notifs) {
    console.log(`taskId=${n.taskId?.slice(0, 30)}... subagentTokens=${n.subagentTokens} result=${(n.result || '').slice(0, 100)}`);
  }
}

console.log('\nDONE.');
console.log('run dir    :', s.runDir);
console.log('tap session:', s.tapSessionId);
