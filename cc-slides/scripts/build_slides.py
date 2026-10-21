#!/usr/bin/env python3
"""Build a deck from a template and a deck.toml spec.

Usage:
    python scripts/build_slides.py <deck.toml> [output.pptx]

A *pattern* is a slide of the template reused as a layout: its title, pictures, text boxes and
tables become slots (numbered in reading order — see inspect_slides.py); every other shape is
copied verbatim. Pattern slides are dropped from the output unless listed with `keep`.

Spec (paths relative to the spec file):
    template = "src/Template.pptx"
    output   = "out/Deck.pptx"              # optional; default out/<template-stem>-<yyMMdd>.pptx
    base     = "figures"                     # optional base dir for images

    [patterns.three-up]
    slide  = 19                              # 1-based template slide
    static = ["Logo"]                        # optional: shapes never treated as slots

    [[slides]]
    keep = 1                                 # template slide 1, unchanged

    [[slides]]
    pattern = "three-up"
    title   = "Efficiency Map"
    images  = ["a.png", { path = "b.png", fit = "cover" }, ""]   # "" leaves a slot empty
    texts   = ["Caption line\\n  indented **bold** line"]
    tables  = [[["Speed", "Eff"], ["1000", "93.2"]]]
    notes   = "Speaker notes"
"""
import argparse
import sys
from datetime import date
from pathlib import Path

from PIL import Image
from pptx import Presentation

import slides_lib as lib

FITS = ("contain", "cover", "stretch")


def default_output_path(spec_path, template):
    return Path(spec_path).parent / "out" / f"{Path(template).stem}-{date.today():%y%m%d}.pptx"


def _resolve(base, value):
    p = Path(value).expanduser()
    return p if p.is_absolute() else base / p


def _image_item(item, base):
    if isinstance(item, str):
        item = {"path": item}
    if not item.get("path"):
        return None
    fit = item.get("fit", "contain")
    if fit not in FITS:
        raise ValueError(f"unknown fit {fit!r}; use one of {FITS}")
    path = _resolve(base, item["path"])
    if not path.is_file():
        raise FileNotFoundError(f"image not found: {path}")
    return path, fit


def _place_picture(slide, box_shape, path, fit):
    x, y, w, h = box_shape.left, box_shape.top, box_shape.width, box_shape.height
    with Image.open(path) as im:
        iw, ih = im.size
    if fit == "contain":
        scale = min(w / iw, h / ih)
        pw, ph = round(iw * scale), round(ih * scale)
        pic = slide.shapes.add_picture(str(path), x + (w - pw) // 2, y + (h - ph) // 2, pw, ph)
    else:
        pic = slide.shapes.add_picture(str(path), x, y, w, h)
        if fit == "cover":
            img_ratio, box_ratio = iw / ih, w / h
            if img_ratio > box_ratio:
                crop = (1 - box_ratio / img_ratio) / 2
                pic.crop_left = pic.crop_right = crop
            else:
                crop = (1 - img_ratio / box_ratio) / 2
                pic.crop_top = pic.crop_bottom = crop
    pic.name = box_shape.name
    return pic


def _render_slide(prs, pattern_slide, entry, static, base, slide_no):
    slide = prs.slides.add_slide(pattern_slide.slide_layout)
    for ph in list(slide.placeholders):  # the pattern supplies every shape explicitly
        ph._element.getparent().remove(ph._element)

    labels = lib.slot_map(pattern_slide, static)
    queues = {
        "image": [_image_item(i, base) for i in entry.get("images", [])],
        "text": list(entry.get("texts", [])),
        "table": list(entry.get("tables", [])),
    }
    counts = {k: sum(1 for v in labels.values() if v.startswith(k + "[")) for k in queues}
    for kind, items in queues.items():
        if len(items) > counts[kind]:
            raise ValueError(f"slide {slide_no}: {len(items)} {kind} item(s) given but pattern "
                             f"{entry['pattern']!r} has {counts[kind]} {kind} slot(s)")
    slot_values = {}
    for sid, label in labels.items():
        kind, _, idx = label.partition("[")
        if kind == "title":
            slot_values[sid] = entry.get("title")
        else:
            i = int(idx.rstrip("]"))
            slot_values[sid] = queues[kind][i] if i < len(queues[kind]) else None

    src_part = pattern_slide.part
    for shape in pattern_slide.shapes:  # z-order preserved: every shape is appended in turn
        label = labels.get(shape.shape_id)
        if label is None:
            lib.copy_shape(shape._element, src_part, slide)
            continue
        value = slot_values[shape.shape_id]
        if value in (None, ""):
            continue  # unfilled slot → dropped, never leaks template content
        if label.startswith("image"):
            _place_picture(slide, shape, *value)
        elif label.startswith("table"):
            lib.set_table(lib.copy_shape(shape._element, src_part, slide), value)
        else:  # title / text
            el = lib.copy_shape(shape._element, src_part, slide)
            lib.set_text(lib.shape_tx_body(el), str(value))

    if entry.get("notes"):
        slide.notes_slide.notes_text_frame.text = entry["notes"]
    lib.renumber_shape_ids(slide)
    return slide


def build(spec_path, output=None):
    spec_path = Path(spec_path).absolute()
    spec = lib.load_toml(spec_path)
    root = spec_path.parent
    template = _resolve(root, spec["template"])
    if not template.is_file():
        raise FileNotFoundError(f"template not found: {template}")
    base = _resolve(root, spec.get("base", "."))
    out = Path(output) if output else (
        _resolve(root, spec["output"]) if spec.get("output") else default_output_path(spec_path, template))
    if out.resolve() == template.resolve():
        raise ValueError("refusing to overwrite the template; choose another output path")

    prs = Presentation(template)
    original = list(prs.slides)

    def template_slide(n, what):
        if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= len(original):
            raise ValueError(f"{what}: template slide {n!r} out of range 1..{len(original)}")
        return original[n - 1]

    patterns = {name: (template_slide(p["slide"], f"pattern {name!r}"), set(p.get("static", [])))
                for name, p in spec.get("patterns", {}).items()}

    order = []
    for no, entry in enumerate(spec.get("slides", []), start=1):
        if "keep" in entry:
            order.append(template_slide(entry["keep"], f"slide {no}").slide_id)
            continue
        name = entry.get("pattern")
        if name not in patterns:
            raise ValueError(f"slide {no}: unknown pattern {name!r}; defined: {sorted(patterns)}")
        pattern_slide, static = patterns[name]
        order.append(_render_slide(prs, pattern_slide, entry, static, base, no).slide_id)
    if not order:
        raise ValueError("spec defines no slides")

    id_list = prs.slides._sldIdLst
    by_id = {int(s.get("id")): s for s in id_list}
    for sid_el in list(id_list):
        id_list.remove(sid_el)
    used = set()
    for sid in order:
        el = by_id[sid]
        if sid in used:
            raise ValueError(f"template slide id {sid} kept twice")
        used.add(sid)
        id_list.append(el)
    for sid, el in by_id.items():
        if sid not in used:
            prs.part.drop_rel(el.rId)

    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("output", nargs="?")
    args = ap.parse_args(argv)
    try:
        out = build(args.spec, args.output)
    except (ValueError, FileNotFoundError) as e:
        sys.exit(f"error: {e}")
    print(out)


if __name__ == "__main__":
    main()
