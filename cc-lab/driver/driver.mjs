// cc-lab driver — a thin PTY wrapper that launches a real interactive Claude Code
// session under claude-tap and exposes five primitives for cases to drive it.
//
// Design: the TUI is only an input channel. Assertions live in the tap trace and
// session files — never in screen-scraping. See AGENT.md.

import { spawn } from 'node-pty';
import { mkdirSync, copyFileSync, existsSync, writeFileSync, createWriteStream, rmSync } from 'node:fs';

import { homedir } from 'node:os';
import { join, resolve } from 'node:path';

const isWin = process.platform === 'win32';

// Strip ANSI/VT escape sequences so sync-point matching survives the TUI's heavy
// cursor-motion rendering. Note: the TUI often emits ESC[<n>C (cursor-forward)
// instead of literal spaces, so matched text may be word-concatenated — prefer
// single distinctive tokens in waitOutput patterns, not multi-word phrases.
// eslint-disable-next-line no-control-regex
const ANSI_RE = /\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]|\x1b\[[0-?]*[ -/]*[@-~]/g;
export function stripAnsi(s) {
  return s.replace(ANSI_RE, '');
}

/** Resolve the claude-tap executable (PATH first, then ~/.local/bin). */
function resolveClaudeTap() {
  const bin = isWin ? 'claude-tap.exe' : 'claude-tap';
  const local = join(homedir(), '.local', 'bin', bin);
  if (existsSync(local)) return local;
  return bin; // fall back to PATH
}

/**
 * Generate a unique run-directory name to prevent collisions when two cases launch
 * in the same wall-clock second. ISO timestamp + case name + PID suffix.
 */
export function runDirName(name) {
  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  return `${stamp}-${name}-${process.pid}`;
}

/** Locate the real (host) config dir to bootstrap credentials from. */
function realConfigDir() {
  return process.env.CLAUDE_CONFIG_DIR || join(homedir(), '.claude');
}

/**
 * Launch an isolated, authenticated Claude Code session under claude-tap.
 * Returns a session object with five primitives: send/key/waitOutput/waitIdle/close.
 */
export async function launch(opts = {}) {
  const {
    runDir,
    claudeArgs = [],
    env = {},
    cols = 140,
    rows = 40,
    // Cost control: test runs default to the cheapest model. Override per-case only
    // when the question is genuinely model-specific (and prefer Sonnet over Opus).
    // Pass model:null to launch with the account default.
    model = 'claude-haiku-4-5-20251001',
  } = opts;

  if (!runDir) throw new Error('launch: runDir is required');

  // Inject --model unless the case already specified one (handles both --model val
  // and --model=val forms).
  const hasModel = claudeArgs.some((a) => a === '--model' || a.startsWith('--model='));
  const argv = model && !hasModel
    ? ['--model', model, ...claudeArgs]
    : claudeArgs;

  const absRunDir = resolve(runDir);
  const tapDir = join(absRunDir, 'tap');
  const configDir = join(absRunDir, 'config');
  mkdirSync(tapDir, { recursive: true });
  mkdirSync(configDir, { recursive: true });

  // 1. Bootstrap the isolated config dir so the child skips onboarding + is authed.
  const srcCreds = join(realConfigDir(), '.credentials.json');
  if (existsSync(srcCreds)) {
    copyFileSync(srcCreds, join(configDir, '.credentials.json'));
  }
  // macOS keychain case: no file creds — claude-tap handles auth detection, so skip.

  // .claude.json lives *outside* CLAUDE_CONFIG_DIR historically, but recent builds
  // read it from the config dir. Write it there to suppress the onboarding wizard
  // AND pre-trust the workspace, so neither the first-run nor the folder-trust
  // dialog blocks the PTY.
  writeFileSync(
    join(configDir, '.claude.json'),
    JSON.stringify(
      {
        hasCompletedOnboarding: true,
        theme: 'dark',
        projects: {
          [absRunDir]: {
            hasTrustDialogAccepted: true,
            hasCompletedProjectOnboarding: true,
            projectOnboardingSeenCount: 1,
          },
        },
      },
      null,
      2,
    ),
  );

  // 2. Build the tap command. All non-tap flags are forwarded to claude.
  const tap = resolveClaudeTap();
  const tapArgs = [
    '--tap-no-live',
    '--tap-no-open',
    '--tap-no-update-check',
    '--tap-output-dir', tapDir,
    '--', ...argv,
  ];

  const childEnv = {
    ...process.env,
    CLAUDE_CONFIG_DIR: configDir,
    ...env,
  };

  // Strip Foundry-mode env vars inherited from the parent (CCDS/Codex). When
  // Foundry is active, CC ignores ANTHROPIC_BASE_URL and routes through
  // ANTHROPIC_FOUNDRY_BASE_URL instead — bypassing claude-tap's proxy entirely.
  // The child session needs vanilla Anthropic routing so claude-tap can intercept.
  for (const k of Object.keys(childEnv)) {
    if (/^ANTHROPIC_FOUNDRY_|^CLAUDE_CODE_USE_FOUNDRY$|^ANTHROPIC_DEFAULT_/.test(k)) {
      delete childEnv[k];
    }
  }

  // 3. Spawn under a PTY. Wrap so missing binaries surface clearly.
  let term;
  try {
    term = spawn(tap, tapArgs, {
      name: 'xterm-256color',
      cols,
      rows,
      cwd: absRunDir,
      env: childEnv,
    });
  } catch (e) {
    if (e.code === 'ENOENT') {
      throw new Error(`claude-tap not found: "${tap}". Install it or add ~/.local/bin to PATH.`);
    }
    throw e;
  }

  // 4. Tee output to tty.log (full history) + a BOUNDED in-memory buffer for
  //    waitOutput. The buffer is capped to a trailing window so a long/verbose
  //    session cannot grow memory unboundedly or make each poll O(n) over the whole
  //    transcript; sync points are always recent, and tty.log keeps the full record.
  const BUFFER_CAP = 512 * 1024; // 512 KiB trailing window
  const ttyLog = createWriteStream(join(absRunDir, 'tty.log'));
  ttyLog.on('error', () => { /* disk/log errors must never kill the driver */ });
  let buffer = '';
  let lastOutputAt = Date.now();
  let exited = false;
  let exitCode = null;
  let tapSessionId = null;

  term.onData((d) => {
    buffer += d;
    if (buffer.length > BUFFER_CAP) buffer = buffer.slice(-BUFFER_CAP);
    lastOutputAt = Date.now();
    if (!ttyLog.writableEnded) ttyLog.write(d); // guard write-after-end on exit race
    // claude-tap prints "Trace session: <uuid>" once at startup — this is the key
    // into the trace DB (distinct from Claude Code's own X-Claude-Code-Session-Id).
    // Match on the tail only (the line is early and the buffer is now windowed).
    if (!tapSessionId) {
      const m = stripAnsi(buffer).match(/Trace session:\s*([0-9a-f-]{36})/i);
      if (m) tapSessionId = m[1];
    }
  });
  term.onExit(({ exitCode: c }) => {
    exited = true;
    exitCode = c;
    ttyLog.end();
  });

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const session = {
    runDir: absRunDir,
    tapDir,
    configDir,
    /** claude-tap trace-session UUID (key into the trace DB); null until printed. */
    get tapSessionId() { return tapSessionId; },
    get buffer() { return buffer; },
    /** ANSI-stripped view of the buffer — use for sync-point matching. */
    get text() { return stripAnsi(buffer); },
    get exited() { return exited; },
    get exitCode() { return exitCode; },

    /** Type text and submit (Enter). */
    send(text) {
      if (exited) throw new Error('send: child has already exited');
      term.write(text + '\r');
    },

    /** Send raw key sequence(s) verbatim: '\t', '\x1b', '\x04', etc. */
    key(seq) {
      if (exited) throw new Error('key: child has already exited');
      term.write(seq);
    },

    /** Resolve when `regex` matches the accumulated buffer; reject on timeout. */
    async waitOutput(regex, timeout = 30000) {
      const start = Date.now();
      // Rebuild the regex without stateful flags (g/y) so repeated .test() calls
      // don't advance lastIndex and flakily miss a match.
      const src = regex instanceof RegExp ? regex.source : regex;
      const flags = regex instanceof RegExp ? regex.flags.replace(/[gy]/g, '') : '';
      const re = new RegExp(src, flags);
      while (Date.now() - start < timeout) {
        if (re.test(stripAnsi(buffer))) return true;
        if (exited) throw new Error(`waitOutput: child exited (code ${exitCode}) before matching ${re}`);
        await sleep(100);
      }
      throw new Error(`waitOutput: timed out after ${timeout}ms waiting for ${re}`);
    },

    /** Resolve when there has been no pty output for `quietMs`. */
    async waitIdle(quietMs = 2500, timeout = 60000) {
      const start = Date.now();
      while (Date.now() - start < timeout) {
        if (Date.now() - lastOutputAt >= quietMs) return true;
        if (exited) return true;
        await sleep(100);
      }
      throw new Error(`waitIdle: still active after ${timeout}ms`);
    },

    /**
     * Clear any startup gate dialogs (folder-trust, external-CLAUDE.md-imports)
     * and resolve once the interactive input prompt is up ("? for shortcuts").
     * Each such dialog defaults to the safe/affirmative option, so pressing Enter
     * accepts it. Returns once "shortcuts" is seen.
     */
    async ready(timeout = 60000) {
      const start = Date.now();
      // Single tokens (spaces are cursor-forward escapes → stripped text concatenates).
      const DIALOG = /trustthisfolder|allowexternal|externalimports/i;
      while (Date.now() - start < timeout) {
        // Inspect only the tail: the cumulative buffer keeps dismissed dialogs' text,
        // and a screen redraw pushes them out of this window once answered.
        const tail = stripAnsi(buffer).slice(-2000);
        if (/shortcuts/.test(tail)) return true;
        if (exited) throw new Error(`ready: child exited (code ${exitCode}) before prompt`);
        if (DIALOG.test(tail)) {
          term.write('\r');
          await sleep(1200);
          continue;
        }
        await sleep(200);
      }
      throw new Error(`ready: timed out after ${timeout}ms waiting for input prompt`);
    },

    /**
     * Graceful shutdown: Ctrl-D, grace, then kill the process tree. Also scrubs the
     * copied `.credentials.json` from the run's config dir — the trace is already
     * captured and the run dir lives under a cloud-synced tree, so a live auth token
     * must not linger there. Pass keepCredentials:true to retain it (e.g. resume
     * tests).
     */
    async close(graceMs = 8000, { keepCredentials = false } = {}) {
      if (!exited) {
        try { term.write('\x04'); } catch { /* already gone */ }
        const start = Date.now();
        while (!exited && Date.now() - start < graceMs) await sleep(100);
        if (!exited && !isWin) {
          // On Windows, node-pty's ConPTY can crash on term.kill() (AttachConsole
          // failure in conpty_console_list_agent.js). Just wait longer — the child
          // almost always exits from Ctrl-D. On POSIX, kill the process group.
          try { term.kill(); } catch { /* ignore */ }
          if (term.pid) {
            try { process.kill(-term.pid, 'SIGKILL'); } catch { /* ignore */ }
          }
          const killStart = Date.now();
          while (!exited && Date.now() - killStart < 2000) await sleep(50);
        }
      }
      // Wait for ttyLog to finish writing so callers don't race the stream flush.
      if (!ttyLog.writableEnded) {
        await new Promise((resolve) => {
          ttyLog.once('finish', resolve);
          setTimeout(resolve, 1000); // safety timeout
        });
      }
      if (!keepCredentials) {
        try { rmSync(join(configDir, '.credentials.json'), { force: true }); } catch { /* ignore */ }
      }
      return exitCode;
    },
  };

  return session;
}
