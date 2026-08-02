// struggle.test.mjs — unit tests for the harness's fabric-aware struggle detection.
// Run with: node --test test/
//
// Covers:
//   - fabricToolWaits: a fabric fan_out that exceeds the sync window (>120s) and is
//     backgrounded is surfaced as a 'fabric-wait' (NOT a struggle), closed by its
//     <task-notification>; a synchronous fabric call produces nothing; an orphaned
//     background task (completion never arrives) is emitted as an open episode.
//   - backgroundTaskPending: waitIdle's guard against declaring a backgrounded fabric
//     task idle before its completion surfaces.

import test from 'node:test';
import assert from 'node:assert';
import { fabricToolWaits, detectStruggles, summarize } from '../driver/struggle.mjs';
import { backgroundTaskPending } from '../driver/driver.mjs';

// ---- transcript builders (mirror driver/session.mjs loadTranscript entry shape) ----
function toolUse(id, name, input = {}) {
  return { type: 'tool_use', id, name, input };
}
function toolResult(id, content) {
  return { type: 'tool_result', tool_use_id: id, content };
}
function textBlock(t) {
  return { type: 'text', text: t };
}
/** Build a loadTranscript-style entry from raw content blocks. */
function entry(i, role, content, textOverride) {
  const text = textOverride ?? content.map((b) =>
    b.type === 'tool_result' ? '[tool_result]'
    : b.type === 'tool_use' ? `[tool_use:${b.name}]`
    : (b.text ?? '')).join(' ');
  return { i, type: role, role, text, raw: { message: { role, content } }, isError: false, toolUses: [] };
}

const FAN_OUT = 'mcp__plugin_fabric_fabric__fan_out';
const CALL = 'mcp__plugin_fabric_fabric__call';
const BG_MSG = (id) =>
  `MCP tool "plugin:fabric:fabric/fan_out" is still running after 120s. ` +
  `It was moved to the background as task ${id} and keeps running; you'll receive a ` +
  `notification with the result when it completes.`;
const NOTIF = (id) =>
  `<task-notification> <task-id>${id}</task-id> <status>completed</status> ` +
  `<result> {"ok":true,"count":4,"failed":0}</result>`;

test('fabricToolWaits: backgrounded fan_out (sync result → task-notification) is one fabric-wait, not a struggle', () => {
  const entries = [
    entry(0, 'user', [textBlock('write a xhs review')]),
    entry(1, 'assistant', [toolUse('c1', FAN_OUT, { synthesize: true, tasks: [{ id: 'A', provider: 'deepseek', prompt: 'x' }] })]),
    entry(2, 'user', [toolResult('c1', BG_MSG('kieetrpq0'))]),
    entry(3, 'assistant', [textBlock('continuing other work while it runs')]),
    entry(4, 'user', [textBlock(NOTIF('kieetrpq0'))]),
  ];
  const waits = fabricToolWaits(entries);
  assert.strictEqual(waits.length, 1, 'exactly one fabric-wait');
  assert.strictEqual(waits[0].kind, 'fabric-wait');
  assert.strictEqual(waits[0].startI, 2);
  assert.strictEqual(waits[0].endI, 4);
  assert.match(waits[0].summary, /kieetrpq0/);

  // Not a struggle: excluded by default, counted only under includeWaits.
  assert.strictEqual(detectStruggles(entries).some((e) => e.kind === 'fabric-wait'), false);
  assert.strictEqual(detectStruggles(entries, { includeWaits: true }).filter((e) => e.kind === 'fabric-wait').length, 1);
  const sm = summarize(entries);
  assert.strictEqual(sm.waitsOnFabric, 1);
  assert.strictEqual(sm.episodes, 0, 'no struggle episodes');
});

test('fabricToolWaits: synchronous fabric call (no backgrounding) is ignored', () => {
  const entries = [
    entry(0, 'assistant', [toolUse('c1', CALL, { provider: 'deepseek', mode: 'agent', prompt: 'review' })]),
    entry(1, 'user', [toolResult('c1', '[{"type":"text","text":"done"}]')]),
  ];
  assert.deepStrictEqual(fabricToolWaits(entries), []);
});

test('fabricToolWaits: orphaned background task (completion never surfaces) is an open episode', () => {
  const entries = [
    entry(0, 'assistant', [toolUse('c1', FAN_OUT, {})]),
    entry(1, 'user', [toolResult('c1', BG_MSG('stuck-task'))]),
    // no <task-notification> ever arrives
  ];
  const waits = fabricToolWaits(entries);
  assert.strictEqual(waits.length, 1);
  assert.strictEqual(waits[0].startI, waits[0].endI, 'open episode');
  assert.match(waits[0].summary, /never surfaced/);
});

test('fabricToolWaits: non-fabric backgrounded tool is not attributed to fabric', () => {
  const entries = [
    entry(0, 'assistant', [toolUse('c1', 'some_other_mcp__tool', {})]),
    entry(1, 'user', [toolResult('c1', BG_MSG('other-task'))]),
  ];
  assert.deepStrictEqual(fabricToolWaits(entries), []);
});

test('backgroundTaskPending: true only while a backgrounded task awaits its completion', () => {
  const bgOnly = `MCP tool ... moved to the background as task abcd1234 and keeps running.`;
  assert.strictEqual(backgroundTaskPending(bgOnly), true, 'no completion yet → pending');

  const withTaskId = `${bgOnly} <task-notification> <task-id>abcd1234</task-id> <status>completed</status>`;
  assert.strictEqual(backgroundTaskPending(withTaskId), false, 'completion surfaced → not pending');

  const withStatus = `${bgOnly} <status>failed</status>`;
  assert.strictEqual(backgroundTaskPending(withStatus), false, 'terminal status → not pending');

  assert.strictEqual(backgroundTaskPending('no background marker here'), false);
  assert.strictEqual(backgroundTaskPending(''), false);
});
