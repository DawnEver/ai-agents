---
platform: twitter
character_limit: 280 per tweet, 4-6 tweets per thread
language: bilingual (EN primary, CN secondary)
emoji_density: moderate
---

# Twitter/X Article Generation Instructions

## Platform DNA

Twitter/X is concise, high-density, bilingual content in thread format. Each tweet must stand alone as a valuable unit of information while contributing to a larger narrative. The first tweet determines whether the thread gets read or scrolled past. Information density matters: every word must earn its place. The audience is global — primarily English-speaking developers, with Chinese-speaking tech community as secondary.

## Structural Formula (Thread)

**Tweet 1 (Hook)**: Shock, curiosity, or pain point. A surprising stat, a bold claim, or a relatable problem. End with "🧵👇" to signal a thread.

**Tweets 2-3 (Features)**: One key feature per tweet. Emoji-anchored. Each tweet = feature name + what it does + why it matters. Self-contained but building the case.

**Tweet 4 (How It Works / Demo)**: The "aha" moment. Describe a quick demo, a clever implementation detail, or an elegant API call. Make it concrete.

**Tweet 5 (Context / Comparison)**: Who built it, what it compares to, why now. Optional: a brief comparison ("vs X, this is faster because...").

**Tweet 6 (CTA)**: GitHub link + call to action (Star, RT, Like, bookmark). End the thread.

## Voice Rules

- **Write as the project's creator**: "I built this because..." not "I found this project that..." — first-person author voice.
- **Bilingual by default**: English as primary language, with Chinese as parenthetical or summary line. Example: "A build tool that's actually fast. 一个真的很快的构建工具。"
- **Energetic but not hyperbolic**: "Impressive" not "mind-blowing." "Fast" not "blazingly fast."
- **Direct**: No preamble. No "I'm excited to share." Jump straight to the point.
- **One idea per tweet**: If you need a comma-separated list of features, put each in its own tweet.
- **Self-contained tweets**: Someone should understand a single tweet even if they don't read the whole thread.
- No thread-unraveling phrases like "As I mentioned in the previous tweet..."
- **BANNED phrases**: "Check out this article", "In this thread I'll", "Here's a breakdown" — just say the thing directly.

## Emoji Rules

- **Density**: 1-2 per tweet.
- **Position**: Start of tweet as visual anchor. Or inline as emphasis.
- **Set**: ✨ 🚀 💡 ⚡ 🔥 🧵 👇 🔗 ⭐ 💻
- **Thread markers**: Tweet 1 ends with 🧵👇. Other tweets can start with ✨ or 💡 as category markers.

## Technical Depth

- **Shallow but precise**: No code blocks (Twitter formatting destroys them). Describe functionality in plain English with technical accuracy.
- Use analogies for complex concepts: "It's like WebPack but with Rust's speed."
- Mention the tech stack if it's a differentiator: "Built in Rust" is worth a tweet. "Built in JavaScript" usually isn't.
- Stats and numbers work great: "3x faster than ESLint" is a tweet. "Very fast" is not.

## Content Constraints

- **Length**: Each tweet MUST stay under 280 characters. Count them.
- **Thread length**: 4-6 tweets. Shorter feels incomplete. Longer loses engagement.
- **Bilingual**: At least a CN summary line in each tweet, or alternate EN/CN tweets.
- **Links**: Only in the final tweet. Twitter penalizes link-heavy threads.
- **Hashtags**: 0-2 max. #opensource #github are fine. Don't hashtag-stuff.
- **No thread marks mid-thread**: Only Tweet 1 has 🧵👇. Don't number tweets "1/6" — it looks automated.

## Example Structure

```
Tweet 1 (Hook):
Did you know most build tools spend 80% of time on things other than building? 
I found an open-source tool that fixes this. 终于有工具解决这个问题了 🧵👇

Tweet 2 (Feature):
✨ Zero-config startup
Drop it in any JS project and it just works. No config file. No plugin system to learn. 
零配置，开箱即用。

Tweet 3 (Feature):
⚡ Built in Rust
Cold builds are 10-50x faster than Webpack. HMR under 100ms even on large codebases.
冷启动比 Webpack 快 10-50 倍。

Tweet 4 (How it works):
💻 One command:
`bun run index.ts`
That's it. No node_modules. No tsconfig. TypeScript just runs.
一行命令，TypeScript 直接运行。

Tweet 5 (Context):
From the team at @oven_sh. Already at 70k+ stars. 
The JS tooling space is finally getting competition. 终于有人挑战 JS 工具链的现状了。

Tweet 6 (CTA):
🔗 github.com/oven-sh/bun
Star it. Try it. Your build times will thank you. ⭐
```

## Bilingual Patterns

Choose one pattern for the thread and stick with it:

**Pattern A (line-by-line)**: English line, Chinese line below it.
```
A build tool that actually delivers on speed.
一个真正快速的构建工具。
```

**Pattern B (per-tweet)**: Alternate EN and CN tweets.
```
Tweet 1: EN
Tweet 2: CN summary of Tweet 1 content + new info
```

**Pattern C (EN-only with CN hashtag)**: English tweets, one CN hashtag at end.
Default to Pattern A — it works best for a bilingual tech audience.

## Images

**核心原则**：图片路径来自 `articles/<slug>/images.md`，不要自行发明路径。优先复用其他平台已有的图片。

Twitter threads benefit from 1-2 strong images. Place them using markdown image refs alongside the relevant tweet.

- **Format**: `![alt text](images/<filename>)` placed below the relevant tweet
- **Aspect ratio**: `--ar 16:9` (Twitter card) or `--ar 1:1` (inline tweet image)
- **Number**: 1-2 images max — threads with too many images lose focus
- **Image types for Twitter/X**:
  1. Bold hook visual for Tweet 1 — can reuse `product-shot.png` or `comparison.png` from images.md (16:9 crop)
  2. Demo/output screenshot for the "how it works" tweet (real project screenshot preferred)

Example (alongside Tweet 1):
```
![Side-by-side: 30s build vs 0.5s build — same codebase](images/comparison.png)
```

## Anti-AI & Quality Rules

### Voice Authenticity
- **Creator voice, not reviewer voice**: "I built this because..." not "This project aims to..." — you have direct experience, not secondhand observations.
- **Specifics over adjectives**: "3x faster than ESLint on 10k-file repos" is a tweet. "Significantly faster" is filler. If you don't have a number, describe the concrete behavior instead.
- **Energetic, not hyperbolic**: "Impressive" yes. "Mind-blowing", "blazingly fast", "revolutionary", "game-changing" — no. The tech speaks; let it.
- **No preamble**: Start with the fact or the hook. Never "I'm excited to share", "Today I want to talk about", "Thrilled to announce."

### Thread Narrative Arc
The thread must build tension toward an "aha" moment, not just list features:
- Tweet 1 = hook: one surprising stat, bold claim, or sharp pain point that makes the reader stop scrolling
- Tweets 2-3 = build: each tweet a self-contained feature that raises the stakes
- Tweet 4 = "aha": the demo, clever detail, or elegant API that makes it click
- Tweet 5 = context/comparison (optional): who built it, what it replaces, why now
- Tweet 6 = CTA only: GitHub link + engagement ask, nothing else

If reading the thread top-to-bottom doesn't create rising interest toward Tweet 4, restructure before finalizing.

### Self-Contained Tweets
Every tweet must be readable standalone — someone who only sees that tweet should get full value. Test: cover all other tweets, read just this one. Does it make sense? Is it useful on its own?

No thread-unraveling phrases: "As I mentioned...", "Building on that...", "From my previous tweet..." — each tweet starts fresh.

### BANNED phrases
"Check out this article" / "In this thread I'll" / "Here's a breakdown" / "excited to share" / "I'm happy to announce" — say the thing directly, skip the meta-announcement.

## Generation Checklist

- [ ] Each tweet under 280 characters (count them exactly)
- [ ] Thread: 4-6 tweets total
- [ ] Tweet 1 has 🧵👇 thread marker
- [ ] Bilingual: EN primary, CN summary in each tweet
- [ ] One clear idea per tweet
- [ ] GitHub link only in final tweet
- [ ] CTA for engagement (Star / RT / Like) in final tweet
- [ ] No code blocks — described in plain language
- [ ] Images (if any): markdown refs `![alt](images/<file>)`, paths from images.md
- [ ] Stats/specifics over adjectives (no "significantly", "blazingly", "revolutionary")
- [ ] Thread builds tension toward an "aha" moment (Tweet 4)
- [ ] Every tweet stands alone (self-contained, no thread-unraveling phrases)
- [ ] No banned opener phrases
- [ ] Creator voice throughout (direct experience, not "this project...")
