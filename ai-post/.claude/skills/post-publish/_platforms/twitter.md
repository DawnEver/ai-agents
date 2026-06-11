# Twitter/X Publish Rules

## Publish URL
https://x.com/home

## Clipboard Format
Each tweet as a separate block:
```
[Tweet 1] (<N> chars)
<content>

[Tweet 2] (<N> chars)
<content>
---
```

## How to Compose
Twitter threads must be built tweet-by-tweet:
1. Open https://x.com/home
2. Compose Tweet 1, paste content, attach image if any
3. Click "+" to add each subsequent tweet

## Character Count
Each tweet verified against 280-char limit. Flag any over limit.

## Image
Attach to Tweet 1 (the hook visual). `twitter-cover.png` if available (16:9 — see `templates/_platform-registry.md`).

## Thread Verify
After composing, read top-to-bottom to verify flow.

## Pre-Publish Checklist
- [ ] 每条推文 ≤280 字符
- [ ] Tweet 1 以 🧵👇 结尾
- [ ] 配图已附加
- [ ] GitHub 链接仅在最后推文
