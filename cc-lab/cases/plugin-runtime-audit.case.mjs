// plugin-runtime-audit.case.mjs — one case to measure ALL plugin runtime token costs.
//
// Captures a full system prompt + tools schema dump from a session with all plugins
// active, then reports per-plugin contribution to the fixed overhead. One run replaces
// N individual plugin cases.
//
// Run: node cases/plugin-runtime-audit.case.mjs
// Output: .lab/<run>/plugin-audit.json + stderr breakdown

import { launch, runDirName } from '../driver/driver.mjs';
import { loadRecords, mainTurns, summarize, waitForTrace } from '../driver/tap.mjs';
import { writeFileSync, readFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const runDir = join('.lab', runDirName('plugin-audit'));

// Register fabric MCP in the isolated config so it gets measured
const absRunDir = resolve(runDir);
const configDir = join(absRunDir, 'config');
const fabricMCP = resolve(fileURLToPath(new URL('.', import.meta.url)), '..', '..', '..', 'claude', 'cc-market', 'fabric', 'scripts', 'mcp-server.mjs');
mkdirSync(configDir, { recursive: true });
writeFileSync(join(absRunDir, 'claude_settings.json'), JSON.stringify({
  mcpServers: { fabric: { command: 'node', args: [fabricMCP] } },
}, null, 2));
console.log('fabric MCP registered');

const s = await launch({
  runDir,
  model: 'claude-haiku-4-5-20251001',
  env: { CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
});
console.log('run dir:', s.runDir);

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // One trivial turn to force a real Messages API request. The system prompt
  // and tools schema are on every request — this first turn captures the full
  // per-request fixed overhead.
  s.send('Say OK and nothing else.');
  await s.waitIdle(4000, 90000);
  console.log('-- turn idle --');
} finally {
  await s.close();
}

// Ensure tap has flushed
await waitForTrace(s.tapSessionId, { timeoutMs: 15000 });
console.log('tap session:', s.tapSessionId);

// ── Extract system prompt + tools schema ──────────────────────────────

const records = loadRecords(s.tapSessionId);
const turns = mainTurns(records);
if (!turns.length) {
  console.error('FAIL: no main turns captured');
  process.exit(1);
}

const first = summarize(turns[0]);
const usage = first.usage;

// ── System prompt block analysis ──────────────────────────────────────

const INJECTED_SECTIONS = [
  'Memory Index', 'cc-market is a Separate Git Repo', 'Git Conventions',
  'GLOBAL-AGENTS.md', 'Hook Behavior', 'Migration Tooling',
  'No Terminal Window Flash', 'Provider Configuration', 'Skill & Agent File Location',
  '## Scoped', '## Entries',
];

function splitInstructionBlock(text) {
  // Try to find injected sections within the monolithic instructions block
  const sections = [];
  let current = { owner: 'cc-builtin', text: '' };
  const lines = text.split('\n');
  for (const line of lines) {
    const header = line.match(/^#{1,4}\s+(.+)/);
    if (header) {
      if (current.text) sections.push({ ...current, chars: current.text.length });
      const title = header[1];
      const isInjected = INJECTED_SECTIONS.some(s => title.includes(s) || line.includes(s));
      current = { owner: isInjected ? 'injected-rules' : 'cc-builtin', text: line + '\n', title };
    } else {
      current.text += line + '\n';
    }
  }
  if (current.text) sections.push({ ...current, chars: current.text.length });
  return sections;
}

const rawSystem = (Array.isArray(first.system) ? first.system : []);
const systemBlocks = [];
for (let i = 0; i < rawSystem.length; i++) {
  const b = rawSystem[i];
  const text = typeof b === 'string' ? b : (b.text || '');
  if (i === 2 && text.length > 5000) {
    // The large instruction block — split into sections
    const sections = splitInstructionBlock(text);
    const ccChars = sections.filter(s => s.owner === 'cc-builtin').reduce((s, sec) => s + sec.chars, 0);
    const ruleChars = sections.filter(s => s.owner === 'injected-rules').reduce((s, sec) => s + sec.chars, 0);
    systemBlocks.push({ index: i, type: 'instructions', owner: 'cc-builtin', chars: ccChars, estTok: Math.round(ccChars / 3), preview: 'CC built-in instructions' });
    if (ruleChars > 0) {
      systemBlocks.push({ index: i, type: 'instructions', owner: 'injected-rules', chars: ruleChars, estTok: Math.round(ruleChars / 3), preview: 'Injected .claude/rules/rem/* + MEMORY.md' });
    }
  } else {
    systemBlocks.push({ index: i, type: b.type || 'text', owner: 'cc-builtin', chars: text.length, estTok: Math.round(text.length / 3), preview: text.slice(0, 120).replace(/\n/g, ' ') });
  }
}

// ── Tools schema analysis ─────────────────────────────────────────────

const tools = first.tools || [];
const toolOwners = new Map(); // owner → { count, chars }
for (const t of tools) {
  let owner = 'builtin';
  const name = t.name || '';
  if (name.startsWith('mcp__plugin_fabric')) owner = 'fabric';
  else if (name.startsWith('mcp__plugin_rem') || name === 'TaskCreate' || name === 'TaskUpdate' || name === 'TaskList' || name === 'TaskGet') owner = 'rem';
  else if (name === 'Bash' || name === 'Read' || name === 'Write' || name === 'Edit' || name === 'Glob' || name === 'Grep' || name === 'WebFetch' || name === 'WebSearch' || name === 'Skill' || name === 'Agent' || name === 'TaskCreate' || name === 'TaskUpdate' || name === 'TaskList' || name === 'TaskGet' || name === 'TaskOutput' || name === 'TaskStop') owner = 'builtin';
  else if (name.startsWith('mcp__plugin_fabric')) owner = 'fabric';
  else if (name.startsWith('mcp__')) owner = 'other-mcp';

  const json = JSON.stringify(t);
  const entry = toolOwners.get(owner) || { count: 0, chars: 0, tools: [] };
  entry.count++;
  entry.chars += json.length;
  entry.tools.push({ name, chars: json.length, estTok: Math.round(json.length / 3) });
  toolOwners.set(owner, entry);
}

// ── Per-plugin token breakdown ────────────────────────────────────────

const totalSystemChars = systemBlocks.reduce((s, b) => s + b.chars, 0);
const totalToolsChars = [...toolOwners.values()].reduce((s, o) => s + o.chars, 0);
const totalChars = totalSystemChars + totalToolsChars;

console.log('\n═══════════════════════════════════════════');
console.log('  PLUGIN RUNTIME AUDIT — per-request fixed overhead');
console.log('═══════════════════════════════════════════');
console.log('Model:', first.model);
console.log('Total system prompt:', totalSystemChars, 'chars /', Math.round(totalSystemChars / 3), 'tok');
console.log('Total tools schema :', totalToolsChars, 'chars /', Math.round(totalToolsChars / 3), 'tok');
console.log('TOTAL fixed overhead:', totalChars, 'chars /', Math.round(totalChars / 3), 'tok');
console.log('');
console.log('Usage (this turn):');
console.log('  input_tokens            :', usage.input_tokens);
console.log('  output_tokens           :', usage.output_tokens);
console.log('  cache_read_input_tokens :', usage.cache_read_input_tokens);
console.log('  cache_creation_input_tokens:', usage.cache_creation_input_tokens);

console.log('\n--- System Prompt Blocks ---');
for (const b of systemBlocks) {
  console.log(`  [${b.index}] ${b.owner.padEnd(16)} | ${b.chars.toString().padStart(6)} chars / ${b.estTok.toString().padStart(4)} tok | ${b.preview}`);
}

console.log('\n--- Tools by Owner ---');
const ownerOrder = ['fabric', 'rem', 'other-mcp', 'builtin'];
for (const owner of ownerOrder) {
  const entry = toolOwners.get(owner);
  if (!entry) continue;
  console.log(`\n  ${owner.toUpperCase()} (${entry.count} tools, ${entry.chars} chars / ${Math.round(entry.chars / 3)} tok):`);
  for (const t of entry.tools.sort((a, b) => b.chars - a.chars)) {
    console.log(`    ${t.name.padEnd(40)} ${t.chars.toString().padStart(5)} chars / ${t.estTok.toString().padStart(4)} tok`);
  }
}

console.log('\n--- Per-Plugin Token Contribution ---');
for (const owner of ownerOrder) {
  const toolsEntry = toolOwners.get(owner) || { chars: 0 };
  const sysBlocks = systemBlocks.filter(b => b.owner === owner || (owner === 'rem' && b.owner === 'rem-rules'));
  const sysChars = sysBlocks.reduce((s, b) => s + b.chars, 0);
  const total = toolsEntry.chars + sysChars;
  const pct = totalChars > 0 ? (total / totalChars * 100).toFixed(1) : '0';
  console.log(`  ${owner.padEnd(16)} | system: ${sysChars.toString().padStart(6)} chars | tools: ${toolsEntry.chars.toString().padStart(6)} chars | TOTAL: ${total.toString().padStart(7)} chars / ${Math.round(total/3).toString().padStart(5)} tok | ${pct}%`);
}

// ── Write structured output ───────────────────────────────────────────

const report = {
  runDir: s.runDir,
  tapSessionId: s.tapSessionId,
  model: first.model,
  timestamp: new Date().toISOString(),
  summary: {
    totalChars, totalEstTok: Math.round(totalChars / 3),
    systemBlocks: systemBlocks.length,
    totalTools: tools.length,
    usage,
  },
  systemBlocks,
  toolsByOwner: Object.fromEntries(
    [...toolOwners.entries()].map(([owner, entry]) => [
      owner,
      { count: entry.count, totalChars: entry.chars, totalEstTok: Math.round(entry.chars / 3), tools: entry.tools },
    ]),
  ),
};

const outPath = join(s.runDir, 'plugin-audit.json');
writeFileSync(outPath, JSON.stringify(report, null, 2));
console.log('\nReport written to:', outPath);
console.log('DONE.');
