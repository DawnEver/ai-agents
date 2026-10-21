#!/usr/bin/env node
// Grant Claude Code access to every project's data links on THIS workstation.
//
// Each project keeps its data (ongoing/, archived/, workspace/, ...) behind a
// link into a synced root outside the repository. Claude checks permissions
// against the resolved path, which differs per machine and OS, so it cannot be
// committed. This script resolves the links where it runs and writes them into
// each project's git-ignored .claude/settings.local.json.
//
// Usage (once per workstation, and again after adding a project or link):
//   node .claude/hooks/allow-data-links.js           write
//   node .claude/hooks/allow-data-links.js --check   show, write nothing
"use strict";
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..", "..");
const TOOLS = ["Read", "Edit", "Write", "Glob", "Grep"];
const check = process.argv.includes("--check");

// Claude permission rules take absolute paths as //<posix path>;
// on Windows C:\x\y becomes //c/x/y.
function rulePath(p) {
  const posix = p.replace(/\\/g, "/").replace(/^([A-Za-z]):/, (_, d) => "/" + d.toLowerCase());
  return "/" + posix;
}

function dataLinks(dir) {
  const out = [];
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    let st;
    try { st = fs.lstatSync(p); } catch { continue; }
    if (!st.isSymbolicLink()) continue; // symlinks and Windows junctions
    try { out.push(fs.realpathSync(p)); } catch { console.warn(`  broken link: ${p}`); }
  }
  return out;
}

function projects() {
  const dirs = [ROOT];
  for (const name of fs.readdirSync(ROOT)) {
    const p = path.join(ROOT, name);
    try {
      if (!fs.lstatSync(p).isSymbolicLink() && fs.statSync(p).isDirectory()
          && fs.existsSync(path.join(p, ".claude"))) dirs.push(p);
    } catch { /* unreadable entry */ }
  }
  return dirs;
}

function ignored(file) {
  try { execFileSync("git", ["-C", ROOT, "check-ignore", "-q", file]); return true; }
  catch { return false; }
}

for (const proj of projects()) {
  const targets = dataLinks(proj);
  if (!targets.length) continue;
  const file = path.join(proj, ".claude", "settings.local.json");
  const settings = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, "utf8")) : {};
  const perms = (settings.permissions ??= {});
  const dirs = new Set(perms.additionalDirectories ?? []);
  const allow = new Set(perms.allow ?? []);
  for (const t of targets) {
    dirs.add(t);
    for (const tool of TOOLS) allow.add(`${tool}(${rulePath(t)}/**)`);
  }
  perms.additionalDirectories = [...dirs];
  perms.allow = [...allow];

  console.log(`${path.relative(ROOT, proj) || "."}: ${targets.length} data link(s)`);
  targets.forEach(t => console.log(`  ${t}`));
  if (!ignored(file)) console.warn(`  WARNING: ${path.relative(ROOT, file)} is not git-ignored`);
  if (!check) fs.writeFileSync(file, JSON.stringify(settings, null, 2) + "\n");
}
if (check) console.log("(--check: nothing written)");
