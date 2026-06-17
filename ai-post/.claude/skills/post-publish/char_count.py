#!/usr/bin/env python
"""Platform char-count checker for ai-post drafts.

Counts the publish-relevant length of an article the way each platform's
editor counts, and checks it against the platform limit.

Usage:
    python char_count.py <path-to-md> [platform]

If platform is omitted it's inferred from the filename
(xiaohongshu / wechat / zhihu / twitter).

Counting rules (match what the platform editor shows):
- xiaohongshu: title = H1 (≤20). caption = everything from after the H1 up to
  the first '---' that introduces the '## 配图' upload list (that list is NOT
  posted), with image markdown refs / [IMAGE:] markers stripped. Spaces and
  line breaks COUNT (小红书 counts them). Limit 1000.
- wechat / zhihu: body length reported for info (no hard cap here); also reports
  the 摘要 if a line '摘要：...' is present (wechat ≤120).
- twitter: each tweet (split on '**Tweet' headers / '---') counted, limit 280.
"""
import re
import sys
from pathlib import Path

LIMITS = {
    "xiaohongshu": {"title": 20, "caption": 1000},
    "wechat": {"summary": 120},
    "zhihu": {},
    "twitter": {"tweet": 280},
}


def strip_images(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)          # ![alt](path)
    text = re.sub(r"\[IMAGE:[^\]]*\]", "", text)               # [IMAGE: ...]
    return text


def count_xhs(text: str):
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else ""
    body = []
    for ln in lines[1:]:
        if ln.strip() == "---":      # 配图 upload list separator — stop
            break
        body.append(ln)
    caption = strip_images("\n".join(body)).strip()
    # collapse the blank lines left by stripped image markers
    caption = re.sub(r"\n{3,}", "\n\n", caption)
    return [
        ("标题", len(title), LIMITS["xiaohongshu"]["title"], title),
        ("正文(含空格+换行)", len(caption), LIMITS["xiaohongshu"]["caption"], None),
    ]


def count_twitter(text: str):
    # split into tweets on the **Tweet N** headers
    blocks = re.split(r"(?m)^\*\*Tweet[^\n]*\*\*[^\n]*$", text)
    out = []
    n = 0
    for b in blocks:
        b = strip_images(b)
        # drop separator lines and the H1
        b = "\n".join(l for l in b.splitlines() if l.strip() not in ("---",) and not l.startswith("# "))
        b = b.strip()
        if not b:
            continue
        n += 1
        out.append((f"Tweet {n}", len(b), LIMITS["twitter"]["tweet"], None))
    return out


def count_generic(text: str, platform: str):
    body = strip_images(text)
    body = "\n".join(l for l in body.splitlines() if not l.startswith("# "))
    out = [("正文(含空格+换行)", len(body.strip()), None, None)]
    m = re.search(r"摘要[:：]\s*(.+)", text)
    if m and platform == "wechat":
        out.append(("摘要", len(m.group(1).strip()), LIMITS["wechat"]["summary"], m.group(1).strip()))
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    p = Path(sys.argv[1])
    text = p.read_text(encoding="utf-8")
    platform = sys.argv[2].lower() if len(sys.argv) > 2 else None
    if not platform:
        stem = p.stem.lower()
        for k in LIMITS:
            if k in stem:
                platform = k
                break
    if platform == "xiaohongshu":
        rows = count_xhs(text)
    elif platform == "twitter":
        rows = count_twitter(text)
    else:
        rows = count_generic(text, platform or "")

    print(f"[{platform or '?'}] {p.name}")
    bad = 0
    for label, n, limit, val in rows:
        tag = ""
        if limit is not None:
            ok = n <= limit
            tag = f"  / {limit}  {'OK' if ok else 'OVER ❌'}"
            if not ok:
                bad += 1
        extra = f'  «{val}»' if val else ""
        print(f"  {label}: {n}{tag}{extra}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
