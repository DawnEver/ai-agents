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

/**
 * List top-level sessions across a real projects dir (e.g. ~/.claude/projects).
 * `match` filters project-dir names by substring (case-insensitive). Returns
 * [{ project, file, sessionId, title, mtime, lines }] sorted by mtime descending.
 */
export function findSessions(projectsDir, { match } = {}) {
  const out = [];
  if (!existsSync(projectsDir)) return out;
  for (const proj of readdirSync(projectsDir)) {
    if (match && !proj.toLowerCase().includes(match.toLowerCase())) continue;
    const dir = join(projectsDir, proj);
    if (!statSync(dir).isDirectory()) continue;
    for (const name of readdirSync(dir)) {
      if (!name.endsWith('.jsonl')) continue;
      const file = join(dir, name);
      const lines = readFileSync(file, 'utf8').split(/\r?\n/).filter(Boolean);
      let title;
      for (const ln of lines) {
        const m = ln.match(/"customTitle"\s*:\s*"((?:[^"\\]|\\.)*)"/);
        if (m) { try { title = JSON.parse(`"${m[1]}"`); } catch { title = m[1]; } break; }
      }
      out.push({
        project: proj, file, sessionId: name.replace(/\.jsonl$/, ''),
        title, mtime: statSync(file).mtimeMs, lines: lines.length,
      });
    }
  }
  return out.sort((a, b) => b.mtime - a.mtime);
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

/** True when a user entry carries a failed/denied/interrupted tool result. */
function entryIsError(raw) {
  const tur = raw.toolUseResult;
  if (tur && typeof tur === 'object' && (tur.is_error || tur.isError)) return true;
  if (typeof tur === 'string' && /^(error|Error)[:\s]/.test(tur)) return true;
  const c = raw.message?.content;
  if (Array.isArray(c)) {
    for (const b of c) {
      if (b.type !== 'tool_result') continue;
      if (b.is_error) return true;
      const t = typeof b.content === 'string' ? b.content : JSON.stringify(b.content ?? '');
      if (/does not exist|command not found|Permission denied|Exit code [1-9]/i.test(t) && /error|failed|denied|not found|Exit code/i.test(t)) return true;
      if (/user (denied|rejected)|permission|interrupted/i.test(t)) return true;
    }
  }
  return false;
}

/** tool_use blocks of an assistant entry → [{ name, inputKey, filePath?, command? }]. */
function entryToolUses(raw) {
  const c = raw.message?.content;
  if (!Array.isArray(c)) return [];
  const out = [];
  for (const b of c) {
    if (b.type !== 'tool_use') continue;
    const inp = b.input ?? {};
    out.push({
      name: b.name,
      inputKey: JSON.stringify(inp),
      filePath: inp.file_path ?? inp.filePath ?? inp.path,
      command: inp.command,
    });
  }
  return out;
}

/**
 * Parse a session jsonl into an array of entries. Each: the raw object plus a normalized
 * `{ i, type, role, text, timestamp, isApiError, isError, toolUses }`. Non-JSON lines
 * are skipped. isError/toolUses enable post-hoc struggle analysis (scripts/analyze-session.mjs).
 */
export function loadTranscript(file) {
  const lines = readFileSync(file, 'utf8').split(/\r?\n/).filter(Boolean);
  const entries = [];
  lines.forEach((ln, i) => {
    let raw;
    try { raw = JSON.parse(ln); } catch { return; }
    entries.push({
      i, type: raw.type || raw.role || '?', role: raw.message?.role, text: entryText(raw), raw,
      timestamp: raw.timestamp,
      isApiError: !!raw.isApiErrorMessage,
      isError: entryIsError(raw),
      toolUses: entryToolUses(raw),
    });
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
