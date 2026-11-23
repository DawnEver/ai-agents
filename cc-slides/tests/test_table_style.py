"""A generated table takes the deck's own table style, copied from a pattern table."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import build_slides  # noqa: E402
import omml  # noqa: E402
import restyle_tables  # noqa: E402
import slides_lib as lib  # noqa: E402
from fixtures import make_template  # noqa: E402

DECK_STYLE = "{93296810-A885-4BE3-A3E7-6D5BEEA58F35}"
A14 = "{http://schemas.microsoft.com/office/drawing/2010/main}m"
M_JC = "{http://schemas.openxmlformats.org/officeDocument/2006/math}jc"
M_VAL = "{http://schemas.openxmlformats.org/officeDocument/2006/math}val"


def add_pattern_table(slide):
    """The deck's own look: style id, first row + first column, centred, 14 pt, white first column."""
    frame = slide.shapes.add_table(3, 3, Emu(0), Emu(900000), Emu(6000000), Emu(1800000))
    tbl = frame._element.find(".//" + qn("a:tbl"))
    tbl_pr = tbl.find(qn("a:tblPr"))
    for k in list(tbl_pr.attrib):
        del tbl_pr.attrib[k]
    tbl_pr.set("firstRow", "1"); tbl_pr.set("firstCol", "1"); tbl_pr.set("bandRow", "1")
    tbl_pr.find(qn("a:tableStyleId")).text = DECK_STYLE
    for r, row in enumerate(frame.table.rows):
        for c, cell in enumerate(row.cells):
            cell.text = f"p{r}{c}"
            tc = cell._tc
            tc_pr = tc.get_or_add_tcPr()
            tc_pr.set("marL", "3964"); tc_pr.set("anchor", "ctr")
            if r and c == 0:
                tc_pr.set("marR", "1111")  # first-column cells differ from body cells
            p = tc.find(qn("a:txBody")).find(qn("a:p"))
            ppr = etree.SubElement(p, qn("a:pPr")); p.remove(ppr); p.insert(0, ppr)
            ppr.set("algn", "ctr"); ppr.set("fontAlgn", "b")
            rpr = p.find(qn("a:r")).get_or_add_rPr()
            rpr.set("sz", "1400")
            if r and c == 0:
                fill = etree.SubElement(rpr, qn("a:solidFill"))
                etree.SubElement(fill, qn("a:schemeClr")).set("val", "lt1")
    frame.name = "Pattern table"
    return frame


def add_generic_table(slide):
    frame = slide.shapes.add_table(3, 3, Emu(0), Emu(3000000), Emu(6000000), Emu(1500000))
    rows = [["Quantity", "$P_{DC}$", "k"], ["low", "1", "2"], ["**peak**", "3", "4"]]
    for tr, values in zip(lib.table_rows(frame._element), rows):
        for tc, v in zip(tr.findall(qn("a:tc")), values):
            body = tc.find(qn("a:txBody"))
            r = etree.SubElement(body.find(qn("a:p")), qn("a:r"))
            etree.SubElement(r, qn("a:rPr")).set("sz", "1100")
            lib.set_text(body, v)
    frame.name = "Generic table"
    return frame, rows


def cells(frame):
    return [tr.findall(qn("a:tc")) for tr in lib.table_rows(frame._element)]


class ApplyTableStyleTests(unittest.TestCase):
    def setUp(self):
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        self.pattern = add_pattern_table(slide)
        self.target, self.rows = add_generic_table(slide)
        lib.apply_table_style(self.target._element, self.pattern._element)

    def test_table_properties_and_style_id_are_the_patterns(self):
        get = lambda f: etree.tostring(f._element.find(".//" + qn("a:tblPr")))
        self.assertEqual(get(self.target), get(self.pattern))

    def test_cell_properties_follow_the_cell_role(self):
        pat = cells(self.pattern)
        for r, row in enumerate(cells(self.target)):
            for c, tc in enumerate(row):
                role = pat[min(r, 1)][min(c, 1)]
                self.assertEqual(etree.tostring(tc.find(qn("a:tcPr"))),
                                 etree.tostring(role.find(qn("a:tcPr"))), (r, c))

    def test_text_takes_pattern_alignment_size_and_colour_keeping_bold(self):
        for r, row in enumerate(cells(self.target)):
            for c, tc in enumerate(row):
                for p in tc.iter(qn("a:p")):
                    self.assertEqual(p.find(qn("a:pPr")).get("algn"), "ctr")
                rprs = list(tc.iter(qn("a:rPr")))
                self.assertTrue(rprs)
                for rpr in rprs:
                    self.assertEqual(rpr.get("sz"), "1400", (r, c))
                    has_fill = rpr.find(qn("a:solidFill")) is not None
                    self.assertEqual(has_fill, bool(r and c == 0), (r, c))
        peak = cells(self.target)[2][0].find(".//" + qn("a:rPr"))
        self.assertEqual(peak.get("b"), "1")

    def test_equation_stays_native_and_follows_the_alignment(self):
        tc = cells(self.target)[0][1]
        self.assertIsNotNone(tc.find(".//" + A14))
        self.assertEqual(tc.find(".//" + M_JC).attrib, {M_VAL: "center"})
        self.assertEqual(lib.get_table(self.target._element), self.rows)

    def test_pattern_without_a_table_is_an_error(self):
        with self.assertRaises(ValueError):
            lib.apply_table_style(self.target._element, etree.Element(qn("p:graphicFrame")))


class TableStyleInDecksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        template = make_template(self.dir)
        prs = Presentation(template)
        add_pattern_table(prs.slides.add_slide(prs.slide_layouts[6]))   # slide 3: style source
        add_generic_table(prs.slides.add_slide(prs.slide_layouts[6]))   # slide 4: table pattern
        prs.save(template)
        self.template = template

    def tearDown(self):
        self.tmp.cleanup()

    def style_id(self, slide):
        frame = next(s for s in slide.shapes if s.has_table)
        return frame._element.find(".//" + qn("a:tableStyleId")).text

    def test_build_pattern_table_style_option(self):
        spec = self.dir / "deck.toml"
        spec.write_text('template = "template.pptx"\n[patterns.t]\nslide = 4\ntable_style = 3\n'
                        '[[slides]]\npattern = "t"\ntables = [[["a", "b", "c"]]]\n')
        out = self.dir / "out.pptx"
        build_slides.build(spec, out)
        self.assertEqual(self.style_id(Presentation(out).slides[0]), DECK_STYLE)

    def test_restyle_cli_writes_a_new_deck_touching_only_listed_slides(self):
        out = self.dir / "restyled.pptx"
        restyle_tables.main([str(self.template), "--pattern-slide", "3", "--slides", "4", "-o", str(out)])
        prs = Presentation(out)
        self.assertEqual(self.style_id(prs.slides[3]), DECK_STYLE)
        with self.assertRaises(SystemExit):
            restyle_tables.main([str(self.template), "--pattern-slide", "3", "--slides", "4",
                                 "-o", str(self.template)])


if __name__ == "__main__":
    unittest.main()
