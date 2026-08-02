#!/usr/bin/env node
// analyze-session.mjs — post-hoc "where did the agent struggle" analysis over REAL
// persisted sessions (evidence layer 2) in a projects dir (default ~/.claude/projects).
// No PTY, no launch — reads jsonl, prints a markdown (or --json) struggle summary for
// the parent Claude to deep-read and turn into a reports/<name>.md.
//
// Usage:
//   node scripts/analyze-session.mjs --list [--project <substr>] [--dir <projectsDir>]
//   node scripts/analyze-session.mjs --project <substr> [--session <id>] [--last N]
//                                    [--json] [--dir <projectsDir>]

import { homedir } from 'node:os';
import { join } from 'node:path';
import { findSessions, loadTranscript } from '../driver/session.mjs';
import { detectStruggles, summarize } from '../driver/struggle.mjs';

const args = process.argv.slice(2);
const opt = (name, dflt) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : dflt;
};
const has = (name) => args.includes(`--${name}`);

const dir = opt('dir', join(homedir(), '.claude', 'projects'));
const project = opt('project');
const last = Number(opt('last', 1));

const sessions = findSessions(dir, { match: project });
if (!sessions.length) {
  console.error(`no sessions found in ${dir}${project ? ` matching "${project}"` : ''}`);
  process.exit(1);
}

if (has('list')) {
  for (const s of sessions) {
    const when = new Date(s.mtime).toISOString().slice(0, 16).replace('T', ' ');
    console.log(`${when}  ${String(s.lines).padStart(6)}  ${s.sessionId}  ${s.project}  ${s.title ?? ''}`);
  }
  process.exit(0);
}

const wanted = opt('session')
  ? sessions.filter((s) => s.sessionId.startsWith(opt('session')))
  : sessions.slice(0, last);
if (!wanted.length) { console.error('no session matches --session'); process.exit(1); }

const results = [];
for (const s of wanted) {
  const entries = loadTranscript(s.file);
  results.push({
    session: { project: s.project, sessionId: s.sessionId, title: s.title, file: s.file },
    summary: summarize(entries),
    episodes: detectStruggles(entries).map((ep) => ({
      ...ep,
      start: entries.find((e) => e.i === ep.startI)?.timestamp,
      end: entries.find((e) => e.i === ep.endI)?.timestamp,
    })),
  });
}

if (has('json')) { console.log(JSON.stringify(results, null, 2)); process.exit(0); }

for (const r of results) {
  const { summary: sm, session: se } = r;
  console.log(`\n# ${se.title ?? se.sessionId}`);
  console.log(`project: ${se.project}  file: ${se.file}`);
  console.log(`entries: ${sm.entries}  assistant turns: ${sm.assistantTurns}  tool errors: ${sm.toolErrors}  api errors: ${sm.apiErrors}`);
  console.log(`episodes: ${sm.episodes}  waits-on-subagents: ${sm.waitsOnSubagents}  waits-on-fabric: ${sm.waitsOnFabric ?? 0}  ${JSON.stringify(sm.byKind)}`);
  console.log(`\n| kind | span (entries) | time | summary | evidence |`);
  console.log(`|---|---|---|---|---|`);
  for (const ep of r.episodes.slice(0, 50)) {
    const time = (ep.start ?? '').slice(5, 16).replace('T', ' ');
    const ev = (ep.evidence ?? '').replace(/\|/g, '\\|');
    console.log(`| ${ep.kind} | ${ep.startI}–${ep.endI} | ${time} | ${ep.summary} | ${ev} |`);
  }
}
