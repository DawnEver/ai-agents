// session.mjs — read Claude Code's persisted session jsonl (evidence layer 2).
//
// The tap trace (driver/tap.mjs) is authoritative for the MAIN process's API traffic,
// but it has a blind spot: a fork/background agent that the user resumes from the agents
// view runs as a DETACHED process whose HTTP bypasses the claude-tap proxy — invisible to
// tap. Those turns ARE persisted, though, in the per-session jsonl under the isolated
// CLAUDE_CONFIG_DIR. This module reads that layer so a case can assert on what actually
// entered each agent's history — main AND its subagents/forks.
//
// Layout (under <configDir>/projects/<encoded-cwd>/):
//   <sessionId>.jsonl                                  ← a top-level session (main)
//   <sessionId>/subagents/agent-<name>-<hash>.jsonl    ← a fork / subagent of that session
// Each line is one event: user/assistant/system messages, plus bookkeeping
// (mode, queue-operation, task-notification is a user event, fork-context-ref, …).

import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join } from 'node:path';

/** Recursively collect every *.jsonl under dir. */
function walk(dir, out = []) {
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    const st = statSync(p);
    if (st.isDirectory()) walk(p, out);
    else if (p.endsWith('.jsonl')) out.push(p);
  }
  return out;
}

/**
 * Locate the persisted transcripts for a launched session. Returns
 * { main: string[], forks: string[] } of absolute jsonl paths. `main` holds top-level
 * session files (the interactive session + any sibling sessions); `forks` holds
 * subagent/fork transcripts (…/subagents/agent-*.jsonl).
 */
export function findTranscripts(configDir) {
  const files = walk(join(configDir, 'projects'));
  const isFork = (f) => /[\\/]subagents[\\/]/.test(f);
  return { main: files.filter((f) => !isFork(f)), forks: files.filter(isFork) };
}

/** Flatten one message's content to plain text (thinking/tool blocks tagged, not dropped). */
export function entryText(entry) {
  const c = entry?.message?.content;
  if (typeof c === 'string') return c;
  if (Array.isArray(c)) {
    return c.map((b) => b.type === 'text' ? b.text
      : b.type === 'thinking' ? '[thinking]'
      : b.type === 'tool_use' ? `[tool_use:${b.name} ${JSON.stringify(b.input).slice(0, 120)}]`
      : b.type === 'tool_result' ? `[tool_result ${(typeof b.content === 'string' ? b.content : JSON.stringify(b.content)).slice(0, 120)}]`
      : `[${b.type}]`).join(' ');
  }
  return '';
}

/**
 * Parse a session jsonl into an array of entries. Each: the raw object plus a normalized
 * `{ i, type, role, text }`. Non-JSON lines are skipped.
 */
export function loadTranscript(file) {
  const lines = readFileSync(file, 'utf8').split(/\r?\n/).filter(Boolean);
  const entries = [];
  lines.forEach((ln, i) => {
    let raw;
    try { raw = JSON.parse(ln); } catch { return; }
    entries.push({ i, type: raw.type || raw.role || '?', role: raw.message?.role, text: entryText(raw), raw });
  });
  return entries;
}

/**
 * Extract every fork/subagent completion notification recorded in a MAIN transcript.
 * Claude Code injects a `<task-notification>` user event each time a fork STOPS; it
 * carries the fork's final `<result>` + usage, NOT the fork's transcript. Returns
 * [{ taskId, status, result, subagentTokens, i }] in order.
 */
export function taskNotifications(mainEntries) {
  const out = [];
  for (const e of mainEntries) {
    if (e.role !== 'user' || !/[<]task-notification[>]/.test(e.text)) continue;
    const m = (re) => (e.text.match(re) || [])[1];
    out.push({
      i: e.i,
      taskId: m(/<task-id>([\s\S]*?)<\/task-id>/),
      status: m(/<status>([\s\S]*?)<\/status>/),
      result: m(/<result>([\s\S]*?)<\/result>/),
      subagentTokens: Number(m(/<subagent_tokens>(\d+)<\/subagent_tokens>/)) || null,
    });
  }
  return out;
}
