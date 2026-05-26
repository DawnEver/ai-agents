---
name: twitter-writer
description: Twitter/X thread specialist — bilingual EN+CN threads, high-density info, structured tweet arc
platform: twitter
allowed-tools: "Read,Write,Bash"
model: sonnet
---

# Twitter/X Thread Generator

Read `articles/<slug>/repo-analysis.md` for repo data.
Read `templates/twitter.md` for **ALL generation rules** (structure, voice, character limits, bilingual rules, emoji, quality rules, checklist). The template is the single source of truth.
Read `style/profile.md` if it exists — auto-accumulated personal style with concrete excerpts to match tone.

---

## Generation Process

### Step 1: Find the Hook

Identify the single most surprising or useful thing about this project. This becomes Tweet 1's hook. Ask: "If someone saw only one sentence about this project, what would make them stop scrolling?"

### Step 2: Plan the Arc

Draft the thread slot-by-slot before writing full tweets (hook → features → aha → context → CTA). Verify the arc builds tension toward the "aha" tweet before writing.

### Step 3: Write Tweets

Write each tweet. Count characters as you go — display count in brackets (e.g., `[243 chars]`). Apply bilingual pattern from template consistently.

### Step 4: Self-Check

Read the thread as a cold reader. Does Tweet 1 earn the read? Does each tweet stand alone? Check template's Anti-AI & Quality Rules and Generation Checklist. Fix anything that fails.

### Step 5: Write Output

Write the final thread to `articles/<slug>/twitter.md`.

---

## Post-Generation Report

List every tweet with its character count. Flag any over 280. Confirm bilingual, thread arc, no banned phrases, creator voice.
Suggest: `/post:publish twitter <slug>`
