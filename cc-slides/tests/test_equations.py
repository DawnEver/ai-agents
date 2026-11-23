import sys
import unittest
from pathlib import Path

from lxml import etree
from pptx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import omml  # noqa: E402
import slides_lib  # noqa: E402

M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
A14 = "{http://schemas.microsoft.com/office/drawing/2010/main}"


def body(text):
    tx = etree.fromstring(
        '<p:txBody xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:bodyPr/>'
        '<a:p><a:r><a:rPr lang="en-GB" sz="1600"/><a:t>old</a:t></a:r></a:p></p:txBody>')
    slides_lib.set_text(tx, text)
    return tx


@unittest.skipUnless(omml.find_xsl(), "MML2OMML.XSL (Microsoft Office) not found")
class EquationTests(unittest.TestCase):
    def test_fraction_subscript_root_superscript_become_omml(self):
        tx = body(r"$$k = \frac{P_{\mathrm{DC}}+P_{\mathrm{AC}}}{P_{\mathrm{DC}}}$$" "\n"
                  r"skin depth $\delta = \sqrt{2\rho/(\omega\mu_0)}$ and $I^2$")
        p1, p2 = tx.findall(qn("a:p"))
        self.assertIsNotNone(p1.find(f".//{A14}m/{M}oMathPara/{M}oMath"))
        for tag in ("f", "sSub"):
            self.assertIsNotNone(p1.find(f".//{M}{tag}"), tag)
        self.assertIsNotNone(p2.find(f".//{M}rad"))
        self.assertIsNotNone(p2.find(f".//{M}sSup"))
        self.assertIsNone(p2.find(f".//{M}oMathPara"), "inline math is not a display paragraph")
        texts = [t.text for t in p2.iter(qn("a:t"))
                 if not any(a.tag.endswith("Fallback") for a in t.iterancestors())]
        self.assertEqual(texts, ["skin depth ", " and "])
        # every math run carries the slot's size and the math font
        for r in tx.iter(f"{M}r"):
            rpr = r.find(qn("a:rPr"))
            self.assertEqual(rpr.get("sz"), "1600")
            self.assertEqual(rpr.find(qn("a:latin")).get("typeface"), "Cambria Math")

    def test_plain_text_without_dollar_is_untouched(self):  # planted control
        tx = body("k = (P_DC + P_AC)/P_DC **bold**")
        self.assertIsNone(next(tx.iter(f"{M}oMath"), None))
        self.assertEqual("".join(t.text for t in tx.iter(qn("a:t"))), "k = (P_DC + P_AC)/P_DC bold")

    def test_escaped_dollar_is_literal(self):
        tx = body(r"costs \$5")
        self.assertIsNone(next(tx.iter(f"{M}oMath"), None))
        self.assertEqual("".join(t.text for t in tx.iter(qn("a:t"))), "costs $5")

    def test_unbalanced_dollar_is_a_hard_error(self):
        with self.assertRaisesRegex(ValueError, r"unbalanced \$"):
            body("price $5 and more")
        with self.assertRaisesRegex(ValueError, r"\$\$"):
            body("$$x = 1$ tail")

    def test_get_text_round_trips_equations_and_literal_dollars(self):
        text = "costs \\$5 and $x^2$\n$$\\frac{a}{b}$$"
        self.assertEqual(slides_lib.get_text(body(text)), text)

    def test_latex_spacing_survives_as_space_characters(self):
        tx = body(r"$a \qquad b \, c$")
        text = "".join(t.text for t in tx.iter(f"{M}t"))
        self.assertIn("\u2003\u2003", text)  # \qquad = 2 em
        self.assertIn("\u2009", text)  # \, = thin space

    def test_bold_span_may_contain_an_equation(self):
        tx = body("**peak at $k = 4.59$** here")
        p = tx.find(qn("a:p"))
        runs = [(r.findtext(qn("a:t")), r.find(qn("a:rPr")).get("b")) for r in p.findall(qn("a:r"))]
        self.assertEqual(runs, [("peak at ", "1"), (" here", None)])
        self.assertIsNotNone(p.find(f".//{M}oMath"))
        self.assertEqual({r.find(qn("a:rPr")).get("b") for r in p.iter(f"{M}r")}, {"1"})

    def test_bad_latex_is_a_hard_error(self):
        with self.assertRaisesRegex(ValueError, "LaTeX"):
            body(r"$\frac{1}{$")


if __name__ == "__main__":
    unittest.main()
