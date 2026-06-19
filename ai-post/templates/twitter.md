---
platform: twitter
language: English ONLY (no Chinese)
emoji_density: see `templates/_platform-registry.md` (emoji_density) — moderate
---

# Twitter/X Article Generation Instructions

## Platform DNA

Twitter/X is concise, high-density, **English-only** content in thread format. Each tweet must stand alone as a valuable unit of information while contributing to a larger narrative. The first tweet determines whether the thread gets read or scrolled past. Information density matters: every word must earn its place. The audience is global English-speaking developers. **Do NOT add Chinese lines** — this thread is English only.

## Structural Formula (Thread)

**Tweet 1 (Hook)**: Shock, curiosity, or pain point. A surprising stat, a bold claim, or a relatable problem. End with "🧵👇" to signal a thread.

**Tweets 2-3 (Features)**: One key feature per tweet. Emoji-anchored. Each tweet = feature name + what it does + why it matters. Self-contained but building the case.

**Tweet 4 (How It Works / Demo)**: The "aha" moment. Describe a quick demo, a clever implementation detail, or an elegant API call. Make it concrete.

**Tweet 5 (Context / Comparison)**: Who built it, what it compares to, why now. Optional: a brief comparison ("vs X, this is faster because...").

**Tweet 6 (CTA)**: GitHub link + call to action (Star, RT, Like, bookmark). End the thread.

## Voice Rules

- **Write as the project's creator**: "I built this because..." not "I found this project that..." — first-person author voice.
- **English only**: no Chinese lines, no bilingual summaries. Every tweet is pure English.
- **Energetic but not hyperbolic**: "Impressive" not "mind-blowing." "Fast" not "blazingly fast."
- **Direct**: No preamble. No "I'm excited to share." Jump straight to the point.
- **One idea per tweet**: If you need a comma-separated list of features, put each in its own tweet.
- **Self-contained tweets**: Someone should understand a single tweet even if they don't read the whole thread.
- No thread-unraveling phrases like "As I mentioned in the previous tweet..."
- **BANNED phrases**: "Check out this article", "In this thread I'll", "Here's a breakdown" — just say the thing directly.

## Emoji Rules

- **Density**: canonical level in `templates/_platform-registry.md` (emoji_density: moderate) — craft target 1-2 per tweet.
- **Position**: Start of tweet as visual anchor. Or inline as emphasis.
- **Set**: ✨ 🚀 💡 ⚡ 🔥 🧵 👇 🔗 ⭐ 💻
- **Thread markers**: Tweet 1 ends with 🧵👇. Other tweets can start with ✨ or 💡 as category markers.

## Technical Depth

- **Shallow but precise**: No code blocks (Twitter formatting destroys them). Describe functionality in plain English with technical accuracy.
- Use analogies for complex concepts: "It's like WebPack but with Rust's speed."
- Mention the tech stack if it's a differentiator: "Built in Rust" is worth a tweet. "Built in JavaScript" usually isn't.
- Stats and numbers work great: "3x faster than ESLint" is a tweet. "Very fast" is not.

## Content Constraints

- **Length — HARD LIMIT**: Each tweet MUST be ≤280 characters. Count every tweet exactly (spaces, punctuation, emoji each count). If any tweet exceeds 280, rewrite/split it before finalizing — never ship an over-limit tweet. Report the char count per tweet.
- **Thread length**: 4-6 tweets. Shorter feels incomplete. Longer loses engagement.
- **English only**: no Chinese lines anywhere in the thread.
- **Links**: Only in the final tweet. Twitter penalizes link-heavy threads.
- **Hashtags**: 0-2 max. #opensource #github are fine. Don't hashtag-stuff.
- **No thread marks mid-thread**: Only Tweet 1 has 🧵👇. Don't number tweets "1/6" — it looks automated.

## Example Structure

```
Tweet 1 (Hook):
Most build tools spend 80% of their time on things other than building.
I got tired of it and built something that doesn't. 🧵👇

Tweet 2 (Feature):
✨ Zero-config startup
Drop it in any JS project and it just works. No config file. No plugin system to learn.

Tweet 3 (Feature):
⚡ Built in Rust
Cold builds are 10-50x faster than Webpack. HMR under 100ms even on large codebases.

Tweet 4 (How it works):
💻 One command: `bun run index.ts`
That's it. No node_modules. No tsconfig. TypeScript just runs.

Tweet 5 (Context):
From the team at @oven_sh. Already at 70k+ stars.
The JS tooling space is finally getting real competition.

Tweet 6 (CTA):
🔗 github.com/oven-sh/bun
Star it. Try it. Your build times will thank you. ⭐
```

Every tweet is English only — no Chinese lines.

## Images

Image paths and counts: see `templates/_platform-registry.md`.

Twitter threads benefit from 1-2 strong images. Place them using markdown image refs alongside the relevant tweet.

- **Format**: `![alt text](../../images/<id>-vN.png)` placed below the relevant tweet (path from `images.md`)
- **Aspect ratio**: `--ar 16:9` (Twitter card) or `--ar 1:1` (inline tweet image)
- **Number**: 1-2 images max — threads with too many images lose focus
- **Image types for Twitter/X**:
  1. Bold hook visual for Tweet 1 — can reuse `product-shot.png` or `comparison.png` from images.md (16:9 crop)
  2. Demo/output screenshot for the "how it works" tweet (real project screenshot preferred)

Example (alongside Tweet 1):
```
![Side-by-side: 30s build vs 0.5s build — same codebase](../../images/comparison-vN.png)
```

## Writing Quality

`templates/_writing-craft.md` is the SSOT for universal writing techniques — see its Section Index. **Twitter is English-only**, so SKIP the Connectives & Transitions section (Chinese connective tables don't apply) and ignore the Chinese examples/banned-phrase table in 「我」as Subject and Anti-AI Check. Do apply: Strong Opening, Microhumor, Concept Handles, Sentence Rhythm, Dopamine Density, and the 🟢🟡🔴 grading. Twitter-specific applications:
- **Strong opening**: Tweet 1 hook uses the 惊人结论/result-first or 痛点直击/pain-point pattern (in English)
- **Specifics over adjectives**: "3x faster than ESLint on 10k-file repos" not "significantly faster"
- **No preamble**: start with the fact, never "I'm excited to share"
- **Self-contained tweets**: every tweet readable standalone (test: cover others, read just this one)
- **Thread narrative arc**: Tweet 1 hook → 2-3 build → 4 "aha" → 5 context → 6 CTA
- **Banned openers**: "Check out this article", "In this thread I'll", "Here's a breakdown", "excited to share"

This template contains only Twitter-specific rules. Apply BOTH files when generating.

## Generation Checklist

- [ ] Each tweet ≤280 characters — count exactly, report per-tweet counts, split any over-limit tweet
- [ ] Thread: 4-6 tweets total
- [ ] Tweet 1 has 🧵👇 thread marker
- [ ] English only — no Chinese lines anywhere
- [ ] One clear idea per tweet
- [ ] GitHub link only in final tweet
- [ ] CTA for engagement (Star / RT / Like) in final tweet
- [ ] No code blocks — described in plain language
- [ ] Images (if any): markdown refs `![alt](../../images/<id>-vN.png)`, paths from images.md
- [ ] Stats/specifics over adjectives (no "significantly", "blazingly", "revolutionary")
- [ ] Thread builds tension toward an "aha" moment (Tweet 4)
- [ ] Every tweet stands alone (self-contained, no thread-unraveling phrases)
- [ ] No banned opener phrases
- [ ] Creator voice throughout (direct experience, not "this project...")
