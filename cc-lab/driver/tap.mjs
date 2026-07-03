// tap.mjs — read claude-tap traces from the shared sqlite DB.
//
// claude-tap does NOT write per-run files into --tap-output-dir (that flag is a
// legacy one-shot import dir). Every intercepted API request/response is persisted
// as a row in ~/.local/share/claude-tap/traces.sqlite3, keyed by the tap trace
// session UUID (the "Trace session: <uuid>" line printed at startup, captured by
// the driver as session.tapSessionId).
//
// This module turns that DB into structured records for assertions. It is the
// PRIMARY evidence layer — cache hits, system-prompt diffs, tools schema, usage.

import { DatabaseSync } from 'node:sqlite';
import { homedir } from 'node:os';
import { join } from 'node:path';

export function tracesDbPath() {
  return join(homedir(), '.local', 'share', 'claude-tap', 'traces.sqlite3');
}

/** Splice a value into `obj` at a JSON-pointer-ish path like "/request/body/tools". */
function setByPath(obj, path, value) {
  const parts = path.split('/').filter(Boolean);
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    const k = /^\d+$/.test(parts[i]) ? Number(parts[i]) : parts[i];
    cur = cur[k];
    if (cur == null) return; // path missing — skip
  }
  const last = parts[parts.length - 1];
  cur[/^\d+$/.test(last) ? Number(last) : last] = value;
}

/**
 * Rehydrate a compact record. claude-tap offloads large fields (tools, big
 * messages) to the record_blobs table and stores a pointer:
 *   { __claude_tap_compact_record__: { refs: [{path, hash, bytes}] }, record }
 * Small records store the payload directly. This returns the full record either way.
 */
function rehydrate(payload, blobs) {
  const compact = payload.__claude_tap_compact_record__;
  if (!compact) return payload; // already a plain record
  const record = payload.record;
  for (const ref of compact.refs ?? []) {
    const raw = blobs.get(ref.hash);
    if (raw === undefined) {
      // A ref with no matching blob means an incomplete record — warn loudly rather
      // than silently returning a record missing its tools/messages, which would make
      // assertions run on partial data.
      console.warn(`[tap] missing blob ${ref.hash} for path ${ref.path} — record incomplete`);
      continue;
    }
    setByPath(record, ref.path, JSON.parse(raw)); // corrupt blob throws — fail loud
  }
  return record;
}

/**
 * Load all trace records for a tap session, in record_index order, with any
 * blob-offloaded fields (tools, large messages) rehydrated in place.
 * Each record: { request_id, turn, duration_ms,
 * request:{method,path,headers,body}, response:{status,headers,body}, ... }.
 */
export function loadRecords(tapSessionId, dbPath = tracesDbPath()) {
  if (!tapSessionId) throw new Error('loadRecords: tapSessionId is required');
  let lastError;
  for (let attempt = 0; attempt < 5; attempt++) {
    try {
      const db = new DatabaseSync(dbPath, { readOnly: true });
      try {
        const blobRows = db
          .prepare('select hash, payload_json from record_blobs where session_id=?')
          .all(tapSessionId);
        const blobs = new Map(blobRows.map((b) => [b.hash, b.payload_json]));
        const rows = db
          .prepare('select payload_json from records where session_id=? order by record_index')
          .all(tapSessionId);
        return rows.map((r) => rehydrate(JSON.parse(r.payload_json), blobs));
      } finally {
        db.close();
      }
    } catch (e) {
      lastError = e;
      if (!/SQLITE_BUSY|locked/i.test(e.message || '') || attempt >= 4) throw e;
      // tap may still be flushing the final rows after close() — brief wait then retry
      const t = Date.now();
      while (Date.now() - t < 100) { /* spin */ }
    }
  }
  throw lastError;
}

/** The session summary row (record_count, status, timing), or null. */
export function loadSession(tapSessionId, dbPath = tracesDbPath()) {
  const db = new DatabaseSync(dbPath, { readOnly: true });
  try {
    return db.prepare('select * from sessions where id=?').get(tapSessionId) ?? null;
  } finally {
    db.close();
  }
}

/**
 * Poll loadSession until record_count stabilizes (or the session row appears).
 * Use after close() to avoid reading the trace DB before claude-tap has flushed
 * its final rows — the DB writes are async to PTY teardown.
 */
export async function waitForTrace(tapSessionId, { stableRounds = 2, intervalMs = 200, timeoutMs = 10000, dbPath } = {}) {
  if (!tapSessionId) throw new Error('waitForTrace: tapSessionId is required');
  const start = Date.now();
  let lastCount = -1;
  let stable = 0;
  while (Date.now() - start < timeoutMs) {
    let session;
    try {
      session = loadSession(tapSessionId, dbPath);
    } catch (e) {
      if (/SQLITE_BUSY|locked/i.test(e.message || '')) continue; // transient lock
      throw e;
    }
    const count = session?.record_count ?? 0;
    if (count > 0 && count === lastCount) {
      stable++;
      if (stable >= stableRounds) return session;
    } else {
      stable = 0;
    }
    lastCount = count;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  // best effort — session may still be writing
  try { return loadSession(tapSessionId, dbPath); } catch { return null; }
}

/** True for real Anthropic Messages API calls (not the /v1/messages?beta quota probe 404s). */
export function isMessages(rec) {
  return typeof rec?.request?.path === 'string'
    && rec.request.path.includes('/v1/messages')
    && rec?.response?.status === 200;
}

/** Successful Messages API records only. NB: this still includes auxiliary model
 * calls (title-gen, quota probe, classifiers). For the real agent turns use
 * `mainTurns` instead. */
export function messages(records) {
  return records.filter(isMessages);
}

/**
 * The real main-thread agent turns, in `turn` order. Isolates them from the many
 * auxiliary Messages calls (title-gen / quota / classifiers) by the empirical
 * heuristic: a full 3-block `system` array, a populated `tools` array, and a
 * response `usage`. This is the filter every case was re-implementing inline.
 */
export function mainTurns(records) {
  return records
    .filter(
      (r) => Array.isArray(r.request?.body?.system)
        && r.request.body.system.length >= 3
        && (r.request.body.tools?.length || 0) > 0
        && r.response?.body?.usage,
    )
    .sort((a, b) => (a.turn ?? 0) - (b.turn ?? 0));
}

/**
 * Normalize a Messages record to the fields cases care about.
 * `system` is the request's system array (or string); `usage` is from the response.
 */
export function summarize(rec) {
  const b = rec.request?.body ?? {};
  const u = rec.response?.body?.usage ?? {};
  return {
    requestId: rec.request_id,
    turn: rec.turn,
    model: b.model,
    system: b.system,
    tools: b.tools ?? [],
    messages: b.messages ?? [],
    thinking: b.thinking,
    usage: {
      input_tokens: u.input_tokens,
      output_tokens: u.output_tokens,
      cache_read_input_tokens: u.cache_read_input_tokens,
      cache_creation_input_tokens: u.cache_creation_input_tokens,
    },
  };
}
