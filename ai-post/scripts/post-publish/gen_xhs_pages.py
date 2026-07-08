#!/usr/bin/env python3
"""Generate 小红书 text-card images (分页文字卡) from a finalized xiaohongshu.md.

Deterministic Pillow rendering — NOT an AI image model — so the text stays crisp.
Page 1 is a title card (the H1 hook); the body is packed into 3:4 cards by
capacity. A per-article YAML config (``images/xhs-pages.yaml``) is auto-created on
first run: edit per-page text / font / size / color / background / alignment and
re-run to regenerate. Delete the config (or pass ``--reinit``) to re-derive it
from the article.

Usage:
    python gen_xhs_pages.py <slug> [--reinit]

The <slug> is an ongoing article dir (e.g. ``dawneever--cc-market__fabric``); the
latest 2-draft/vN/xiaohongshu.md is used (walk-back inheritance).
"""
import argparse
import os
import platform as _platform
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required — run: pip install -r scripts/post-publish/requirements.txt")

from PIL import Image, ImageColor, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent.parent  # ai-post/
ONGOING = ROOT / "ongoing"

# Emoji codepoint ranges (deliberately excludes CJK, arrows like →, and em-dash —
# so ordinary punctuation renders with the text font). FE0F/200D/20E3 are joined
# into the preceding emoji run so 🛠️ and ZWJ sequences stay intact.
EMOJI_RE = re.compile(
    "([\U0001F300-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF"
    "\U0001F1E6-\U0001F1FF\U0000FE0F\U0000200D\U000020E3]+)"
)


# ---------------------------------------------------------------- fonts

def _first_existing(paths):
    for p in paths:
        if p and Path(p).exists():
            return str(p)
    return None


def resolve_fonts():
    """Return (text_regular, text_bold, emoji) absolute paths for this OS."""
    sysname = _platform.system()
    if sysname == "Windows":
        f = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Fonts"
        return (
            _first_existing([f / "msyh.ttc", f / "msyh.ttf"]),
            _first_existing([f / "msyhbd.ttc", f / "msyhbd.ttf", f / "msyh.ttc"]),
            _first_existing([f / "seguiemj.ttf"]),
        )
    if sysname == "Darwin":
        pf = Path("/System/Library/Fonts/PingFang.ttc")
        return (
            _first_existing([pf, Path("/System/Library/Fonts/STHeiti Medium.ttc")]),
            _first_existing([pf]),
            _first_existing([Path("/System/Library/Fonts/Apple Color Emoji.ttc")]),
        )
    # Linux / other
    noto = [
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf"),
    ]
    return (
        _first_existing(noto),
        _first_existing(noto),
        _first_existing([Path("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")]),
    )


_FONT_CACHE = {}


def get_font(path, size, emoji=False):
    key = (path, size, emoji)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    font = None
    if path:
        try:
            font = ImageFont.truetype(path, size)
        except OSError:
            # Bitmap-strike color-emoji fonts (e.g. Apple) only load at fixed
            # sizes; try common strikes, then give up (caller falls back to text).
            if emoji:
                for strike in (137, 160, 96, 64):
                    try:
                        font = ImageFont.truetype(path, strike)
                        break
                    except OSError:
                        continue
    if font is None:
        font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


# ---------------------------------------------------------------- article parsing

def resolve_md(slug):
    versions = ONGOING / slug / "2-draft"
    if not versions.exists():
        sys.exit(f"No 2-draft/ for slug '{slug}'")
    v_dirs = sorted(
        (d for d in versions.iterdir() if d.is_dir() and re.fullmatch(r"v\d+", d.name)),
        key=lambda d: int(d.name[1:]),
    )
    for vd in reversed(v_dirs):
        f = vd / "xiaohongshu.md"
        if f.exists():
            return f
    sys.exit(f"No xiaohongshu.md in any version of '{slug}'")


def parse_article(md_path):
    """Return (title, [body_paragraph, ...]) — excludes the 配图 manifest and the
    trailing hashtag line (those belong to the caption, not the cards)."""
    title = md_path.stem
    paras = []
    buf = []
    for raw in md_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        # H1 title
        m = re.match(r"^#\s+(.*)", line)
        if m and title == md_path.stem:
            title = m.group(1).strip()
            continue
        # Stop at the 配图 manifest (## 配图 ...) — nothing after belongs on a card.
        if re.match(r"^#{2,}\s*配图", line):
            break
        # Skip other headings (小红书 body rarely has them; keep text clean).
        if re.match(r"^#{2,}\s", line):
            continue
        # Skip the hashtag line (starts with '#tag', i.e. # not followed by space).
        if re.match(r"^#\S", line):
            continue
        if line.strip() == "":
            if buf:
                paras.append("\n".join(buf).strip())
                buf = []
            continue
        buf.append(line)
    if buf:
        paras.append("\n".join(buf).strip())
    return title, [p for p in paras if p]


# ---------------------------------------------------------------- text layout

def split_runs(text):
    """Split into [(segment, is_emoji), ...]."""
    out = []
    for i, part in enumerate(EMOJI_RE.split(text)):
        if part:
            out.append((part, bool(i % 2)))
    return out


def _tokenize(text):
    """Latin words stay whole; CJK/other chars break individually; keep spaces."""
    return re.findall(r"[A-Za-z0-9@._/:%+\-]+|\s+|.", text)


def measure(token, is_emoji, size, fonts):
    path = fonts["emoji"] if is_emoji else fonts["text"]
    if is_emoji and not fonts["emoji"]:
        path = fonts["text"]
    font = get_font(path, size, emoji=is_emoji)
    return font.getlength(token)


def wrap_paragraph(text, size, max_w, fonts):
    """Return a list of lines; each line is [(token, is_emoji, width), ...]."""
    units = []
    for seg, is_emoji in split_runs(text.replace("\n", " ")):
        if is_emoji:
            units.append((seg, True))
        else:
            for tok in _tokenize(seg):
                units.append((tok, False))
    lines, cur, cur_w = [], [], 0.0
    for tok, is_emoji in units:
        w = measure(tok, is_emoji, size, fonts)
        if tok.isspace():
            if not cur:
                continue
            if cur_w + w > max_w:
                lines.append(cur)
                cur, cur_w = [], 0.0
            else:
                cur.append((tok, is_emoji, w))
                cur_w += w
            continue
        if cur and cur_w + w > max_w:
            lines.append(cur)
            cur, cur_w = [(tok, is_emoji, w)], w
        else:
            cur.append((tok, is_emoji, w))
            cur_w += w
    if cur:
        lines.append(cur)
    return lines


def page_height(paras, size, max_w, line_spacing, para_spacing, fonts):
    line_h = size * line_spacing
    total = 0.0
    for idx, p in enumerate(paras):
        n = len(wrap_paragraph(p, size, max_w, fonts))
        total += n * line_h
        if idx < len(paras) - 1:
            total += line_h * para_spacing
    return total


# ---------------------------------------------------------------- config

def build_config(title, paras, fonts):
    text_font, bold_font, emoji_font = fonts
    cfg = {
        "canvas": {"width": 1080, "height": 1440, "background": "#FFFFFF"},
        "margin": {"x": 96, "y": 150},
        "line_spacing": 1.5,
        "para_spacing": 0.7,
        "align": "left",
        "page_number": True,
        "fonts": {"text": text_font or "", "bold": bold_font or "", "emoji": emoji_font or ""},
        "title": {"size": 76, "color": "#222222", "align": "left", "background": "#FFF3F0", "bold": True},
        "body": {"size": 44, "color": "#2b2b2b", "min_size": 30, "max_size": 52, "bold": False},
        "pages": [],
    }
    cfg["pages"].append({"type": "title", "text": title})
    fdict = {"text": text_font, "bold": bold_font, "emoji": emoji_font}
    avail_w = cfg["canvas"]["width"] - 2 * cfg["margin"]["x"]
    avail_h = cfg["canvas"]["height"] - 2 * cfg["margin"]["y"]
    size = cfg["body"]["size"]
    # Capacity-fill: pack paragraphs into a card until the next would overflow.
    cur = []
    for p in paras:
        trial = cur + [p]
        h = page_height(trial, size, avail_w, cfg["line_spacing"], cfg["para_spacing"], fdict)
        if cur and h > avail_h:
            cfg["pages"].append({"type": "body", "text": "\n\n".join(cur)})
            cur = [p]
        else:
            cur = trial
    if cur:
        cfg["pages"].append({"type": "body", "text": "\n\n".join(cur)})
    return cfg


# ---------------------------------------------------------------- rendering

def _hex(color):
    return ImageColor.getrgb(color)


def draw_line(draw, x, y, line, size, color, fonts):
    for tok, is_emoji, w in line:
        path = fonts["emoji"] if (is_emoji and fonts["emoji"]) else fonts["text"]
        font = get_font(path, size, emoji=is_emoji)
        if is_emoji and fonts["emoji"]:
            draw.text((x, y), tok, font=font, embedded_color=True)
        else:
            draw.text((x, y), tok, font=font, fill=color)
        x += w


def fit_size(paras, cfg, style, avail_w, avail_h, fonts):
    """If a page pins ``size`` use it; else shrink-to-fit within [min,max]."""
    if "size" in style:
        return int(style["size"])
    lo = int(cfg["body"]["min_size"])
    hi = int(style.get("max_size", cfg["body"]["max_size"]))
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        h = page_height(paras, mid, avail_w, cfg["line_spacing"], cfg["para_spacing"], fonts)
        if h <= avail_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def render_page(cfg, page, index, total, fonts):
    W = cfg["canvas"]["width"]
    H = cfg["canvas"]["height"]
    mx = cfg["margin"]["x"]
    my = cfg["margin"]["y"]
    is_title = page.get("type") == "title"
    style = cfg["title"] if is_title else cfg["body"]
    bg = page.get("background", style.get("background", cfg["canvas"]["background"]))
    img = Image.new("RGBA", (W, H), _hex(bg))
    draw = ImageDraw.Draw(img)
    avail_w = W - 2 * mx
    avail_h = H - 2 * my
    align = page.get("align", style.get("align", cfg["align"]))
    color = _hex(page.get("color", style["color"]))
    paras = [seg for seg in page["text"].split("\n\n") if seg.strip()]

    # Title cards default to the bold face; any page can override with `bold:`.
    use_bold = page.get("bold", style.get("bold", is_title))
    if use_bold and fonts.get("bold"):
        fonts = {**fonts, "text": fonts["bold"]}

    if is_title:
        size = int(page.get("size", style["size"]))
        # Shrink an over-long title until it fits the card height.
        while size > 28 and page_height(paras, size, avail_w, cfg["line_spacing"],
                                        cfg["para_spacing"], fonts) > avail_h:
            size -= 2
    else:
        size = fit_size(paras, cfg, page if "size" in page else style,
                        avail_w, avail_h, fonts)

    line_h = size * cfg["line_spacing"]
    # Compose all lines (with paragraph gaps) then vertically center the block.
    blocks = []
    for p in paras:
        blocks.append(wrap_paragraph(p, size, avail_w, fonts))
    total_h = 0.0
    for bi, lines in enumerate(blocks):
        total_h += len(lines) * line_h
        if bi < len(blocks) - 1:
            total_h += line_h * cfg["para_spacing"]
    y = my + max(0, (avail_h - total_h) / 2)

    for lines in blocks:
        for line in lines:
            line_w = sum(w for _, _, w in line)
            x = mx + (avail_w - line_w) / 2 if align == "center" else mx
            draw_line(draw, x, y, line, size, color, fonts)
            y += line_h
        y += line_h * cfg["para_spacing"]

    if cfg.get("page_number") and total > 1:
        badge = f"{index}/{total}"
        bf = get_font(fonts["text"], 30)
        bw = bf.getlength(badge)
        draw.text((W - mx - bw, H - my + 30), badge, font=bf, fill=(150, 150, 150))
    return img.convert("RGB")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Generate 小红书 text-card images.")
    ap.add_argument("slug")
    ap.add_argument("--reinit", action="store_true",
                    help="Re-derive the config from the article, discarding edits.")
    args = ap.parse_args()

    md = resolve_md(args.slug)
    img_dir = ONGOING / args.slug / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = img_dir / "xhs-pages.yaml"

    reinit = args.reinit or not cfg_path.exists()
    if reinit:
        title, paras = parse_article(md)
        cfg = build_config(title, paras, resolve_fonts())
        cfg_path.write_text(
            yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )
        print(f"📝 config {'re-created' if args.reinit else 'created'}: {cfg_path}")
    else:
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        print(f"📝 config loaded: {cfg_path}")

    fonts = {
        "text": cfg["fonts"].get("text") or resolve_fonts()[0],
        "bold": cfg["fonts"].get("bold") or resolve_fonts()[1],
        "emoji": cfg["fonts"].get("emoji") or "",
    }
    if not fonts["text"]:
        sys.exit("No CJK text font found — set fonts.text in the config to a .ttf/.ttc path.")
    if not fonts["emoji"]:
        print("⚠️  no color-emoji font found — emoji will render in the text font "
              "(set fonts.emoji in the config to fix).")

    # Clear stale page PNGs so a shorter re-run doesn't leave orphans.
    for old in img_dir.glob("xhs-page-*.png"):
        old.unlink()

    pages = cfg["pages"]
    total = len(pages)
    for i, page in enumerate(pages, start=1):
        img = render_page(cfg, page, i, total, fonts)
        out = img_dir / f"xhs-page-{i:02d}.png"
        img.save(out)
        kind = page.get("type", "body")
        print(f"  🖼️  xhs-page-{i:02d}.png  [{kind}]")
    print(f"✅ {total} 张卡片 → {img_dir}")
    print(f"   编辑 {cfg_path.name}（每页 text/size/color/background/align）后重跑即可重生成。")


if __name__ == "__main__":
    main()
