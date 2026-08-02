// struggle.mjs — post-hoc "where did the agent get stuck" detectors over a persisted
// session transcript (driver/session.mjs loadTranscript entries). Pure functions, no IO.
//
// Each detector returns episodes: { kind, startI, endI, summary, evidence } where
// startI/endI are entry indices back into the transcript (for deep-reading the jsonl)
// and evidence is a short excerpt. detectStruggles() runs all detectors and returns
// episodes sorted by descending span (longest struggle first).

const EDIT_TOOLS = new Set(['Edit', 'Write', 'MultiEdit', 'NotebookEdit']);

/** Fabric/MCP tools that run long work on an external engine (deepseek/codex/…). */
const FABRIC_TOOL_RE = /^mcp__plugin_fabric_fabric__(fan_out|call|spawn_session|team_spawn|session_send|team_send)$/;
/** The client's message when an MCP tool exceeds the sync window and is backgrounded. */
const BG_TASK_RE = /moved to the background as task (\w+)/;

/** Normalize an error string for clustering: strip paths, numbers, volatile bits. */
function normErr(s) {
  return String(s).slice(0, 300)
    .replace(/[A-Za-z]:[\\/][\w\\/.-]+/g, '<path>')
    .replace(/[\w/.-]+\.(mjs|js|ts|py|json|m|md)(:\d+)?/g, '<file>')
    .replace(/\d+/g, 'N');
}

/** Short excerpt of an entry for evidence. */
function excerpt(e, n = 140) {
  return e.text.replace(/\s+/g, ' ').slice(0, n);
}

/** Map every tool_use block id → tool name (for attributing tool_results). */
function toolUseNames(entries) {
  const m = new Map();
  for (const e of entries) {
    const c = e.raw.message?.content;
    if (!Array.isArray(c)) continue;
    for (const b of c) if (b.type === 'tool_use' && b.id) m.set(b.id, b.name);
  }
  return m;
}

/**
 * tool-error-repeat: same tool failing with the same normalized error ≥2 times.
 * Clustered per (tool, normalized error) and split into windows: occurrences more
 * than `window` entries apart become separate episodes (a whole-session span means
 * two unrelated collisions, not one struggle).
 */
export function toolErrorRepeats(entries, window = 300) {
  const names = toolUseNames(entries);
  const fails = new Map(); // key -> [{i, tool, errText}]
  for (const e of entries) {
    if (!e.isError || e.role !== 'user') continue;
    const c = e.raw.message?.content;
    if (!Array.isArray(c)) continue;
    for (const b of c) {
      if (b.type !== 'tool_result') continue;
      const t = typeof b.content === 'string' ? b.content : JSON.stringify(b.content ?? '');
      const tool = names.get(b.tool_use_id) ?? '?';
      const key = `${tool}:${normErr(t)}`;
      if (!fails.has(key)) fails.set(key, []);
      fails.get(key).push({ i: e.i, tool, err: t.slice(0, 140) });
    }
  }
  const out = [];
  for (const [, list] of fails) {
    if (list.length < 2) continue;
    let run = [list[0]];
    const flush = () => {
      if (run.length >= 2) {
        out.push({
          kind: 'tool-error-repeat', startI: run[0].i, endI: run[run.length - 1].i,
          summary: `${run[0].tool} same error ×${run.length}`,
          evidence: run[0].err,
        });
      }
      run = [];
    };
    for (let k = 1; k < list.length; k++) {
      if (list[k].i - list[k - 1].i > window) flush();
      run.push(list[k]);
    }
    flush();
  }
  return out;
}

/** edit-thrash: same file edited ≥3 times across the session. */
export function editThrash(entries, min = 3) {
  const byFile = new Map();
  entries.forEach((e) => {
    for (const tu of e.toolUses) {
      if (!EDIT_TOOLS.has(tu.name) || !tu.filePath) continue;
      if (!byFile.has(tu.filePath)) byFile.set(tu.filePath, []);
      byFile.get(tu.filePath).push(e.i);
    }
  });
  const out = [];
  for (const [file, idx] of byFile) {
    if (idx.length < min) continue;
    out.push({
      kind: 'edit-thrash', startI: idx[0], endI: idx[idx.length - 1],
      summary: `${file} edited ×${idx.length}`,
      evidence: file,
    });
  }
  return out;
}

/** identical-loop: the exact same tool_use (name+input) issued ≥2 times in a row. */
export function identicalLoops(entries) {
  const out = [];
  let run = null; // { key, startI, count, lastI, sample }
  const flush = () => {
    if (run && run.count >= 2) {
      out.push({
        kind: 'identical-loop', startI: run.startI, endI: run.lastI,
        summary: `identical tool call ×${run.count}`,
        evidence: run.sample,
      });
    }
    run = null;
  };
  for (const e of entries) {
    const tu = e.toolUses[0];
    const key = tu ? `${tu.name}:${tu.inputKey}` : null;
    if (key && run && key === run.key) { run.count++; run.lastI = e.i; continue; }
    flush();
    if (key) run = { key, startI: e.i, lastI: e.i, count: 1, sample: excerpt(e) };
  }
  flush();
  return out;
}

/** bash-retry: a Bash command errors, then a similar command (same first word) is retried. */
export function bashRetries(entries) {
  const out = [];
  for (let k = 0; k < entries.length; k++) {
    const e = entries[k];
    if (!e.isError) continue;
    // find the failed command: nearest preceding assistant entry with a Bash tool_use
    let cmd;
    for (let j = k - 1; j >= 0 && j >= k - 3; j--) {
      const tu = entries[j].toolUses.find((t) => t.name === 'Bash' && t.command);
      if (tu) { cmd = tu.command; break; }
    }
    if (!cmd) continue;
    const head = cmd.trim().split(/\s+/)[0];
    // look for a retry of the same head within the next 20 entries
    for (let j = k + 1; j < entries.length && j <= k + 20; j++) {
      const tu = entries[j].toolUses.find((t) => t.name === 'Bash' && t.command);
      if (tu && tu.command.trim().split(/\s+/)[0] === head) {
        out.push({
          kind: 'bash-retry', startI: e.i, endI: entries[j].i,
          summary: `bash '${head}' failed then retried`,
          evidence: cmd.slice(0, 140),
        });
        break;
      }
    }
  }
  return out;
}

/** permission-denial: tool results indicating the user denied/interrupted. */
export function permissionDenials(entries) {
  const out = [];
  for (const e of entries) {
    if (e.role !== 'user') continue;
    if (!/user (denied|rejected)|permission to use|interrupted/i.test(e.text)) continue;
    out.push({
      kind: 'permission-denial', startI: e.i, endI: e.i,
      summary: 'tool use denied/interrupted',
      evidence: excerpt(e),
    });
  }
  return out;
}

/** api-retry: clusters of isApiErrorMessage assistant entries. */
export function apiRetries(entries) {
  const idx = entries.filter((e) => e.isApiError).map((e) => e.i);
  if (!idx.length) return [];
  return [{
    kind: 'api-retry', startI: idx[0], endI: idx[idx.length - 1],
    summary: `API error/retry messages ×${idx.length}`,
    evidence: excerpt(entries[idx[0]]),
  }];
}

/**
 * long-stall: >threshold assistant entries between two real user text inputs.
 * Episodes are classified by what CLOSED the stall: 'user' (a real human message —
 * the only kind that signals under-completion) vs 'notification' (task-notification /
 * teammate-message — the agent was legitimately waiting on subagents). Notification-
 * ended stalls are returned with kind 'wait-on-subagents' so callers can tell the two
 * apart; they are not struggles.
 */
export function longStalls(entries, threshold = 40) {
  const isRealUser = (e) => e.role === 'user' && e.type === 'user'
    && !e.raw.message?.content?.some?.((b) => b.type === 'tool_result')
    && e.text && !e.text.startsWith('[tool_result');
  const isNotification = (e) => /[<]task-notification[>]|[<]teammate-message|idle_notification/.test(e.text);
  const out = [];
  let count = 0, start = -1;
  for (const e of entries) {
    if (isRealUser(e) || isNotification(e)) {
      if (count > threshold) {
        const notification = isNotification(e);
        out.push({
          kind: notification ? 'wait-on-subagents' : 'long-stall',
          startI: start, endI: e.i,
          summary: `${count} assistant entries ${notification ? 'waiting on subagents' : 'between user inputs'}`,
          evidence: excerpt(e),
        });
      }
      count = 0; start = -1;
    } else if (e.role === 'assistant') {
      if (start < 0) start = e.i;
      count++;
    }
  }
  return out;
}

/**
 * fabric-wait: a fabric/MCP tool that exceeded the sync window (>120s) and was
 * backgrounded — "moved to the background as task X" — closed when its
 * <task-notification> completion lands. These are LEGITIMATE waits on an external
 * engine (deepseek/codex), NOT struggles. kind 'fabric-wait'; excluded from
 * detectStruggles() by default (kept with opts.includeWaits), counted as waitsOnFabric
 * in summarize(). A backgrounded task whose completion never surfaces is emitted as an
 * open (startI==endI) episode so it stands out instead of silently hanging a sync.
 */
export function fabricToolWaits(entries) {
  const names = toolUseNames(entries);
  const pending = new Map(); // bgTaskId -> { startI, tool, sample }
  const out = [];
  for (const e of entries) {
    const c = e.raw.message?.content;
    if (Array.isArray(c)) {
      for (const b of c) {
        if (b.type !== 'tool_result') continue;
        const t = typeof b.content === 'string' ? b.content : JSON.stringify(b.content ?? '');
        const tool = names.get(b.tool_use_id) ?? '';
        if (!FABRIC_TOOL_RE.test(tool)) continue;
        const m = t.match(BG_TASK_RE);
        if (m) pending.set(m[1], {
          startI: e.i,
          tool: tool.replace(/^mcp__plugin_fabric_fabric__/, ''),
          sample: t.slice(0, 140),
        });
      }
    }
    if (e.role === 'user' && /[<]task-notification[>]/.test(e.text)) {
      const m = e.text.match(/<task-id>([\s\S]*?)<\/task-id>/);
      const p = m && pending.get(m[1]);
      if (p) {
        out.push({
          kind: 'fabric-wait', startI: p.startI, endI: e.i,
          summary: `fabric ${p.tool} backgrounded >120s (task ${m[1]})`,
          evidence: p.sample,
        });
        pending.delete(m[1]);
      }
    }
  }
  for (const [id, p] of pending) {
    out.push({
      kind: 'fabric-wait', startI: p.startI, endI: p.startI,
      summary: `fabric ${p.tool} backgrounded >120s (task ${id}) — completion never surfaced`,
      evidence: p.sample,
    });
  }
  return out;
}

/**
 * repeated-command: the same NORMALIZED Bash command (paths/numbers/quoted strings
 * stripped) run ≥min times. Catches near-identical loops that identicalLoops misses —
 * e.g. the same pytest target re-run after every edit, same commit retried with a
 * different message.
 */
export function repeatedCommands(entries, min = 3) {
  const norm = (cmd) => String(cmd)
    .replace(/'[^']*'|"[^"]*"/g, '<str>')
    .replace(/[A-Za-z]:[\\/][\w\\/.-]+/g, '<path>')
    .replace(/[\w/.-]+\.(py|mjs|js|ts|json|md|m|toml)/g, '<file>')
    .replace(/\d+/g, 'N')
    .replace(/\s+/g, ' ').slice(0, 200);
  const byCmd = new Map();
  for (const e of entries) {
    for (const tu of e.toolUses) {
      if (tu.name !== 'Bash' || !tu.command) continue;
      const key = norm(tu.command);
      if (!byCmd.has(key)) byCmd.set(key, []);
      byCmd.get(key).push({ i: e.i, cmd: tu.command });
    }
  }
  const out = [];
  for (const [, list] of byCmd) {
    if (list.length < min) continue;
    out.push({
      kind: 'repeated-command', startI: list[0].i, endI: list[list.length - 1].i,
      summary: `same normalized bash command ×${list.length}`,
      evidence: list[0].cmd.slice(0, 140),
    });
  }
  return out;
}

/**
 * Run every detector; episodes sorted by span (desc), then startI.
 * 'wait-on-subagents' spans (longStalls episodes closed by a task-notification) are
 * NOT struggles and are excluded here; opts.includeWaits keeps them. 'fabric-wait'
 * spans (fabricToolWaits) are likewise legit external-engine waits, excluded by default.
 */
export function detectStruggles(entries, opts = {}) {
  const stalls = longStalls(entries, opts.stallThreshold);
  const all = [
    ...toolErrorRepeats(entries, opts.errorWindow),
    ...editThrash(entries, opts.editMin),
    ...identicalLoops(entries),
    ...bashRetries(entries),
    ...permissionDenials(entries),
    ...apiRetries(entries),
    ...repeatedCommands(entries, opts.commandMin),
    ...stalls.filter((s) => opts.includeWaits || s.kind !== 'wait-on-subagents'),
    ...(opts.includeWaits ? fabricToolWaits(entries) : []),
  ];
  return all.sort((a, b) => (b.endI - b.startI) - (a.endI - a.startI) || a.startI - b.startI);
}

/** Session-level counters for the overview header. */
export function summarize(entries) {
  const byKind = {};
  const eps = detectStruggles(entries, { includeWaits: true });
  for (const ep of eps) byKind[ep.kind] = (byKind[ep.kind] || 0) + 1;
  return {
    entries: entries.length,
    assistantTurns: entries.filter((e) => e.role === 'assistant').length,
    toolErrors: entries.filter((e) => e.isError).length,
    apiErrors: entries.filter((e) => e.isApiError).length,
    episodes: eps.filter((e) => e.kind !== 'wait-on-subagents' && e.kind !== 'fabric-wait').length,
    waitsOnSubagents: eps.filter((e) => e.kind === 'wait-on-subagents').length,
    waitsOnFabric: eps.filter((e) => e.kind === 'fabric-wait').length,
    byKind,
  };
}
