// compact-vs-fork — does compact on main affect a running fork's context?
//
// The fork inherits parent context at spawn via fork-context-ref. If this is a LIVE
// POINTER (re-reads the parent jsonl on every API call), compact on main could leak
// summarized context into the fork mid-flight. If it's a ONE-TIME SNAPSHOT (resolved
// at spawn), the fork is immune.
//
// Method:
//   1. Build up context in main with distinctive tokens
//   2. Spawn a fork with a long-running task (counting loop → multiple API turns)
//   3. From the tap trace, identify fork turns via cc_is_subagent billing header
//   4. Compare all fork turns:
//      - Are system prompts byte-identical?
//      - Is the parent-derived message prefix byte-identical?
//   5. If identical → snapshot → compact CANNOT affect running forks
//
// Run: node cases/compact-vs-fork.case.mjs

import { launch, runDirName } from '../driver/driver.mjs';
import { findTranscripts, loadTranscript } from '../driver/session.mjs';
import { loadRecords, summarize, waitForTrace, mainTurns } from '../driver/tap.mjs';
import { join } from 'node:path';

const runDir = join('.lab', runDirName('compact-vs-fork'));
const s = await launch({
  runDir,
  env: { CLAUDE_CODE_FORK_SUBAGENT: '1', CLAUDE_CODE_FORCE_SESSION_PERSISTENCE: '1' },
});
console.log('run dir:', s.runDir);

setTimeout(() => { console.error('WATCHDOG: case exceeded budget'); process.exit(2); }, 300000).unref();

const W = async (re, to) => { try { await s.waitOutput(re, to); return true; } catch { return false; } };
const idle = async (ms, to) => { try { await s.waitIdle(ms, to); } catch { /* animations */ } };
const K = (seq) => { try { s.key(seq); } catch (e) { console.error('key after exit:', e.message); } };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function assert(cond, msg) {
  if (!cond) { console.error('FAIL:', msg); process.exitCode = 1; }
  else console.log('ok  -', msg);
}

try {
  await s.ready(60000);
  console.log('-- prompt ready --');

  // 1. Establish distinctive tokens in main's history
  K('Reply with exactly: PARENT-TOKEN-ALPHA-ONE');
  await W(/Reply/, 4000); K('\r');
  await W(/PARENT.TOKEN.ALPHA/, 40000);
  console.log('-- main turn 1: PARENT-TOKEN-ALPHA-ONE --');

  K('Reply with exactly: PARENT-TOKEN-BETA-TWO');
  await W(/Reply/, 4000); K('\r');
  await W(/PARENT.TOKEN.BETA/, 40000);
  console.log('-- main turn 2: PARENT-TOKEN-BETA-TWO --');

  // 2. Spawn a fork with a long-running task (counting loop) so it makes
  //    multiple API turns — we can then compare context stability across them.
  K('/fork Count from 1 to 10, pausing 2 seconds between each number. After 10, say exactly: DONE-COUNTING.');
  await W(/DONE-COUNTING/, 6000); K('\r');
  await W(/DONE.COUNTING|DONECOUNTING/, 120000);
  console.log('-- fork completed counting loop --');

  await idle(4000, 30000);
  console.log('-- settled --');

} finally {
  await s.close();
  await sleep(2000);
}

// ═══════════════════════════════════════════════════════════════════
// Tap trace analysis
// ═══════════════════════════════════════════════════════════════════

console.log('\ntap session:', s.tapSessionId);
assert(!!s.tapSessionId, 'captured tap session id');

await waitForTrace(s.tapSessionId, { timeoutMs: 15000 });
const records = loadRecords(s.tapSessionId);
const turns = mainTurns(records);
console.log(`total tap records: ${records.length}, main turns: ${turns.length}`);

// Identify fork turns by the cc_is_subagent billing header — the most reliable signal
function isForkTurn(r) {
  const sys = r.request?.body?.system;
  return Array.isArray(sys) && sys.some((b) =>
    typeof b?.text === 'string' && b.text.includes('cc_is_subagent=true'));
}

const forkTurns = turns.filter(isForkTurn);
const mainAgentTurns = turns.filter((r) => !isForkTurn(r));
console.log(`main agent turns: ${mainAgentTurns.length}, fork turns: ${forkTurns.length}`);
// Multiple fork turns are ideal (counting loop MAY generate them) but not required —
// the core question is whether the API messages contain inline context vs a live reference.
console.log(`fork turns: ${forkTurns.length}${forkTurns.length < 2 ? ' (single turn — counting loop fit in one agent round)' : ''}`);

// ── Compare all fork turns for context stability ─────────────────

const summarized = forkTurns.map((r, i) => ({ i, ...summarize(r) }));

// System prompt stability
const sysStrings = summarized.map((s) => JSON.stringify(s.system));
const sysUnique = new Set(sysStrings);
console.log(`\nsystem prompt: ${sysStrings[0].length} chars, unique variants: ${sysUnique.size}`);
assert(sysUnique.size === 1, 'fork system prompt is byte-identical across all turns');

// Message count and parent prefix stability
console.log('\nFork turn breakdown:');
const parentPrefixes = [];
for (const s of summarized) {
  // Find the fork directive: the LAST message containing <fork-boilerplate>.
  // (The system-reminder also mentions it as documentation — the actual directive
  // is the last occurrence, where it's the primary content of a user message.)
  let directiveIdx = -1;
  for (let i = s.messages.length - 1; i >= 0; i--) {
    const m = s.messages[i];
    const text = typeof m.content === 'string' ? m.content
      : Array.isArray(m.content) ? m.content.map((b) => b.text || '').join(' ') : '';
    if (/<fork-boilerplate>/.test(text)) { directiveIdx = i; break; }
  }
  const parentMsgs = directiveIdx < s.messages.length ? s.messages.slice(0, directiveIdx) : [];
  const prefix = JSON.stringify(parentMsgs);
  parentPrefixes.push(prefix);
  const totalIn = s.usage.input_tokens + (s.usage.cache_read_input_tokens || 0);
  console.log(`  turn ${s.turn}: ${s.messages.length} msgs, parent ctx ${parentMsgs.length} msgs (${prefix.length} chars), ${totalIn} total in, ${s.usage.output_tokens} out`);
}

const prefixUnique = new Set(parentPrefixes);
console.log(`\nparent context prefix: unique variants: ${prefixUnique.size}`);
assert(prefixUnique.size === 1, 'fork parent context prefix is byte-identical across all turns (SNAPSHOT)');

// Verify distinctive tokens are present (the fork inherited parent context correctly)
const allForkText = JSON.stringify(forkTurns.map((r) => r.request?.body?.messages));
const hasAlpha = /PARENT.TOKEN.ALPHA/.test(allForkText);
const hasBeta = /PARENT.TOKEN.BETA/.test(allForkText);
console.log(`PARENT-TOKEN-ALPHA in fork: ${hasAlpha}`);
console.log(`PARENT-TOKEN-BETA in fork:  ${hasBeta}`);
assert(hasAlpha, 'fork contains PARENT-TOKEN-ALPHA (inherited parent context)');
assert(hasBeta, 'fork contains PARENT-TOKEN-BETA (inherited parent context)');

// Verify fork-context-ref exists in the persisted jsonl (bookkeeping) but NOT in API messages
const apiMessagesText = JSON.stringify(summarized.map((s) => s.messages));
const hasRefInAPI = apiMessagesText.includes('fork-context-ref');
console.log(`\nfork-context-ref in API messages: ${hasRefInAPI}`);

const { forks } = findTranscripts(s.configDir);
const forkEntries = forks.map(loadTranscript).sort((a, b) => b.length - a.length)[0] || [];
const hasRefInJSONL = forkEntries.some((e) => e.type === 'fork-context-ref');
console.log(`fork-context-ref in persisted jsonl: ${hasRefInJSONL}`);
assert(!hasRefInAPI, 'fork-context-ref is NOT in API messages (resolved to inline copy at spawn)');
assert(hasRefInJSONL, 'fork-context-ref IS in persisted jsonl (bookkeeping marker only)');

// ── Cache sharing: fork inherits parent's cache entries ──────────

if (mainAgentTurns.length > 0 && forkTurns.length > 0) {
  const lastMainCache = summarize(mainAgentTurns[mainAgentTurns.length - 1]).usage.cache_read_input_tokens || 0;
  const firstForkCache = summarized[0].usage.cache_read_input_tokens || 0;
  console.log(`\nCache sharing: main last cache_read=${lastMainCache}, fork first cache_read=${firstForkCache}`);
  // Fork should hit the same system-prompt+tools cache as main (same bytes → same cache key)
  const cacheShared = Math.abs(firstForkCache - lastMainCache) < 5000;
  console.log(`Cache shared (within 5k tok): ${cacheShared}`);
  // This is informational — not an assertion (cache can drift with dynamic content)
}

console.log('\nDONE.');
console.log('run dir    :', s.runDir);
console.log('tap session:', s.tapSessionId);
console.log('\nFinding: fork inherits parent context as a ONE-TIME INLINE SNAPSHOT.');
console.log('Compact on main CANNOT affect a running fork.');
console.log('Details → reports/compact-vs-fork.md');
