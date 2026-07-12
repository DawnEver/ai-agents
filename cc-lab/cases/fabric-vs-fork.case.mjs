// fabric-vs-fork.case.mjs — live comparison of fabric call vs built-in /fork subagent.
//
// Question: how does the new fabric (with resultMode summarization + write sessions)
// compare to the built-in fork subagent on token consumption and capability boundaries?
//
// Method: launch Claude Code under claude-tap, instruct the parent to use BOTH
// fabric call (with different resultModes) AND /fork subagent on equivalent tasks,
// then compare the tap traces. Fabric MCP must be registered in the isolated config
// before launch (see setup note below).
//
// Prerequisites:
//   1. fabric MCP server registered in the parent Claude's config (see setupFabricMCP below)
//   2. claude-tap installed (~/.local/bin/claude-tap)
//   3. At least one non-Claude provider configured (deepseek) in claude_env_settings.json
//
// Setup: the case auto-registers fabric MCP in the isolated config via setupFabricMCP().
// Override FABRIC_MCP_PATH env if the fabric plugin root is not at the sibling path.
//
// Run: node cases/fabric-vs-fork.case.mjs
// Then analyze: node .scratch/fabric-vs-fork-cost-model.mjs  (offline cost model)
//               OR parent Claude reads the tap trace and writes reports/fabric-vs-fork.md

import { launch, runDirName } from '../driver/driver.mjs';
import { loadRecords, mainTurns, summarize, messages } from '../driver/tap.mjs';
import { writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';

const runDir = join('.lab', runDirName('fabric-vs-fork'));

// ── Setup: register fabric MCP in the isolated config ──────────────────

function fabricMCPPath() {
  if (process.env.FABRIC_MCP_PATH) return process.env.FABRIC_MCP_PATH;
  // Default: sibling Sync/claude checkout → cc-market/fabric
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

// Register fabric MCP before launch (driver creates configDir).
// We need to hook into the config dir path: it's join(runDir, 'config').
const absRunDir = resolve(runDir);
const configDir = join(absRunDir, 'config');
setupFabricMCP(configDir);

const s = await launch({
  runDir,
  model: 'claude-sonnet-4-5-20250929', // Sonnet for reliable tool use
  claudeArgs: [],
  env: {
    CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1',
    // Allow fabric MCP tool calls
    CLAUDE_CODE_ENABLE_ALL_TOOLS: '1',
  },
});
console.log('run dir:', s.runDir);

setTimeout(() => { console.error('WATCHDOG: case exceeded budget'); process.exit(2); }, 600000).unref();

const W = async (re, to) => { try { await s.waitOutput(re, to); return true; } catch { return false; } };
const idle = async (ms, to) => { try { await s.waitIdle(ms, to); } catch { /* animations */ } };
const K = (seq) => { try { s.key(seq); } catch { /* exited */ } };

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // ── Turn 1: Fabric call with summary mode ────────────────────────────
  const fabricTask = `Use the fabric tool to call deepseek with resultMode summary.
Task: "Explain what a mutex is in 3-4 sentences. Include a simple example in Rust."
Do NOT read any files. Just make the tool call and return the result.`;

  K(fabricTask);
  await W(/mutex|Mutex/i, 120000);
  await idle(3000, 30000);
  console.log('-- fabric summary call done --');

  // ── Turn 2: Fabric call with full mode ────────────────────────────────
  const fabricFullTask = `Use the fabric tool to call deepseek with resultMode full.
Same task: "Explain what a mutex is in 3-4 sentences. Include a simple example in Rust."`;

  K(fabricFullTask);
  await W(/mutex|Mutex/i, 120000);
  await idle(3000, 30000);
  console.log('-- fabric full call done --');

  // ── Turn 3: Fork subagent ────────────────────────────────────────────
  const forkTask = `/fork Explain what a mutex is in 3-4 sentences. Include a simple example in Rust.`;

  K(forkTask);
  await W(/mutex|Mutex/i, 120000);
  await idle(5000, 60000);
  console.log('-- fork subagent done --');

  // Let any pending notifications arrive
  await idle(3000, 30000);
  console.log('-- settled --');

} finally {
  await s.close();
}

// ── Assertions & Trace Analysis ────────────────────────────────────────

console.log('\ntap session:', s.tapSessionId);
assert(!!s.tapSessionId, 'captured a tap trace-session id');

const records = loadRecords(s.tapSessionId);
console.log('trace records:', records.length);
assert(records.length > 0, 'trace DB has records for this session');

const turns = mainTurns(records);
console.log('main turns:', turns.length);
assert(turns.length >= 3, 'at least 3 main turns (fabric summary + fabric full + fork)');

// Per-turn token breakdown
console.log('\n## Per-Turn Token Breakdown\n');
console.log('| Turn | Model | Input tok | Output tok | Cache read | Cache create |');
console.log('|---|---:|---:|---:|---:|');

let totalInput = 0, totalOutput = 0, totalCacheRead = 0, totalCacheCreate = 0;

for (const t of turns) {
  const s = summarize(t);
  totalInput += s.usage.input_tokens;
  totalOutput += s.usage.output_tokens;
  totalCacheRead += s.usage.cache_read_input_tokens;
  totalCacheCreate += s.usage.cache_creation_input_tokens;
  console.log(
    `| ${s.turn} | ${s.model || '?'} | ${s.usage.input_tokens} | ${s.usage.output_tokens} | ${s.usage.cache_read_input_tokens} | ${s.usage.cache_creation_input_tokens} |`,
  );
}

console.log(`\n| **Total** | | **${totalInput}** | **${totalOutput}** | **${totalCacheRead}** | **${totalCacheCreate}** |`);

// Tool call result sizes (parent context pollution)
const msgRecords = messages(records);
console.log('\n## Tool Call / Fork Notification Sizes\n');
for (const r of msgRecords) {
  const body = r.request?.body;
  if (!body?.messages) continue;
  const lastMsg = body.messages[body.messages.length - 1];
  const content = lastMsg?.content;
  if (typeof content === 'string' && content.length > 50) {
    console.log(`turn ${r.turn}: last message = ${content.length} chars`);
  }
}

// Fork notifications from the session transcripts
console.log('\n## Fork Subagent Notifications (from session jsonl)\n');
const { findTranscripts, loadTranscript, taskNotifications } = await import('../driver/session.mjs');
const { main } = findTranscripts(s.configDir);
for (const mf of main) {
  const entries = loadTranscript(mf);
  const notifs = taskNotifications(entries);
  for (const n of notifs) {
    console.log(`taskId=${n.taskId?.slice(0, 30)}... subagentTokens=${n.subagentTokens} result=${(n.result || '').slice(0, 80)}`);
  }
}

console.log('\nDONE. Analyze → reports/fabric-vs-fork.md');
console.log('Or run: node .scratch/fabric-vs-fork-cost-model.mjs (offline cost model)');
