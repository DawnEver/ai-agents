"""LaTeX math in text slots -> native PowerPoint equations (Office Math, OMML).

`$...$` is an inline equation, a whole paragraph `$$...$$` a display equation, `\\$` a literal
dollar. Route: LaTeX -> MathML (latex2mathml) -> OMML (Office's own MML2OMML.XSL, the converter
Word and PowerPoint use) -> `<a14:m>` inside an `mc:AlternateContent`, the way PowerPoint stores an
equation. The fallback run holds the `$LaTeX$` source, so older readers and slides2md see it.
Malformed input is a hard error: an equation never silently degrades to plain text.
"""
import copy
import os
import re
from functools import lru_cache
from pathlib import Path

from lxml import etree
from pptx.oxml.ns import qn

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
A14_NS = "http://schemas.microsoft.com/office/drawing/2010/main"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
MATH_FONT = "Cambria Math"
XSL_ENV = "CC_SLIDES_MML2OMML"
XSL_CANDIDATES = (
    r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL",
    r"C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL",
    r"C:\Program Files\Microsoft Office\Office16\MML2OMML.XSL",
    "/Applications/Microsoft Word.app/Contents/Resources/mathml2omml.xsl",
)
MML_NS = "http://www.w3.org/1998/Math/MathML"
_TOKEN = re.compile(r"\\\$|\$\$|\$")


def _m(tag):
    return f"{{{M_NS}}}{tag}"


def find_xsl():
    """Path of MML2OMML.XSL ($CC_SLIDES_MML2OMML first), or None."""
    for c in (os.environ.get(XSL_ENV), *XSL_CANDIDATES):
        if c and Path(c).is_file():
            return Path(c)
    return None


@lru_cache(maxsize=1)
def _transform():
    xsl = find_xsl()
    if xsl is None:
        raise ValueError(f"equations need Office's MML2OMML.XSL: install Microsoft Office or set {XSL_ENV}")
    return etree.XSLT(etree.parse(str(xsl)))


def split_math(line):
    """[(kind, text)] with kind 'text' | 'inline' | 'display'. Raises ValueError on a stray $."""
    parts, buf, pos, open_tok = [], "", 0, None
    for mt in _TOKEN.finditer(line):
        buf += line[pos:mt.start()]
        pos = mt.end()
        tok = mt.group()
        if tok == "\\$":
            buf += tok if open_tok else "$"
            continue
        if open_tok is None:
            if buf:
                parts.append(("text", buf))
            buf, open_tok = "", tok
        elif tok == open_tok:
            if not buf.strip():
                raise ValueError(f"empty equation in {line!r}")
            parts.append(("display" if tok == "$$" else "inline", buf.strip()))
            buf, open_tok = "", None
        else:
            raise ValueError(f"mismatched $ / $$ in {line!r}")
    if open_tok:
        raise ValueError(f"unbalanced {open_tok} in {line!r} (write \\$ for a literal dollar)")
    buf += line[pos:]
    if buf:
        parts.append(("text", buf))
    if any(k == "display" for k, _ in parts) and len(parts) > 1:
        raise ValueError(f"$$...$$ must be a whole paragraph: {line!r}")
    return parts


def _spaces_to_text(mathml):
    r"""MML2OMML drops <mspace>; \quad, \, ... survive as em / four-per-em / thin spaces."""
    for sp in list(mathml.iter(f"{{{MML_NS}}}mspace")):
        width = sp.get("width", "0em")
        em = float(width[:-2]) if width.endswith("em") else 0.0
        text = "\u2003" * int(em)
        rest = em - int(em)
        text += "\u2005" if rest >= 0.25 else "\u2009" if rest >= 0.1 else ""
        if not text:
            sp.getparent().remove(sp)
            continue
        mtext = etree.Element(f"{{{MML_NS}}}mtext")
        mtext.text = text
        mtext.tail = sp.tail
        sp.getparent().replace(sp, mtext)


def latex_to_omml(latex):
    """LaTeX -> <m:oMath>. Raises ValueError for LaTeX latex2mathml cannot parse."""
    from latex2mathml.converter import convert
    try:
        mathml = etree.fromstring(convert(latex).encode())
    except Exception as e:  # latex2mathml raises its own exception zoo
        raise ValueError(f"bad LaTeX {latex!r}: {type(e).__name__} {e}".rstrip()) from e
    for el in mathml.iter():
        if el.text and el.text.startswith("\\"):
            raise ValueError(f"bad LaTeX {latex!r}: unknown command {el.text}")
    _spaces_to_text(mathml)
    omath = _transform()(mathml).getroot()
    if omath is None or omath.tag != _m("oMath"):
        raise ValueError(f"bad LaTeX {latex!r}: MML2OMML produced no equation")
    return omath


def _math_rpr(rpr, upright):
    out = copy.deepcopy(rpr)  # bold only when the equation sits inside **...**
    out.set("i", "0" if upright else "1")
    for tag in ("a:latin", "a:ea", "a:cs", "a:sym", "a:hlinkClick", "a:hlinkMouseOver", "a:rtl", "a:extLst"):
        for old in out.findall(qn(tag)):
            out.remove(old)
    for tag in ("a:latin", "a:cs"):  # schema order: fills/effects ... latin ea cs (all trailing now)
        etree.SubElement(out, qn(tag), typeface=MATH_FONT)
    return out


def equation(latex, rpr, display=False):
    """An mc:AlternateContent holding the equation, to append to an a:p. `rpr` is the slot's run
    formatting (size, colour), applied to every math run in the Cambria Math font."""
    omath = latex_to_omml(latex)
    for r in omath.iter(_m("r")):
        for foreign in [c for c in r if not c.tag.startswith(f"{{{M_NS}}}")]:
            r.remove(foreign)  # MML2OMML may emit Word run properties; PowerPoint uses a:rPr
        mrpr = r.find(_m("rPr"))
        sty = mrpr.find(_m("sty")) if mrpr is not None else None
        upright = sty is not None and sty.get(_m("val")) == "p"
        r.insert(0 if mrpr is None else 1, _math_rpr(rpr, upright))
    alt = etree.Element(f"{{{MC_NS}}}AlternateContent", nsmap={"mc": MC_NS})
    choice = etree.SubElement(alt, f"{{{MC_NS}}}Choice", nsmap={"a14": A14_NS}, Requires="a14")
    holder = etree.SubElement(choice, f"{{{A14_NS}}}m")
    if display:
        para = etree.SubElement(holder, _m("oMathPara"), nsmap={"m": M_NS})
        jc = etree.SubElement(etree.SubElement(para, _m("oMathParaPr")), _m("jc"))
        jc.set(_m("val"), "centerGroup")
        para.append(omath)
    else:
        holder.append(omath)
    run = etree.SubElement(etree.SubElement(alt, f"{{{MC_NS}}}Fallback"), qn("a:r"))
    run.append(copy.deepcopy(rpr))
    etree.SubElement(run, qn("a:t")).text = f"$${latex}$$" if display else f"${latex}$"
    return alt
