import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import powerpoint  # noqa: E402
import preview_slides  # noqa: E402
from fixtures import make_image, make_template  # noqa: E402


class PreviewUnitTests(unittest.TestCase):
    def test_contact_sheet_grid(self):
        with tempfile.TemporaryDirectory() as d:
            pages = [make_image(Path(d) / f"slide-{i:02d}.png", (320, 180)) for i in range(1, 6)]
            sheet = preview_slides.contact_sheet(pages, Path(d) / "contact.png", columns=3)
            with Image.open(sheet) as im:
                w, h = im.size
        self.assertGreater(w, 3 * 200)
        self.assertGreater(h, 2 * 100)  # 5 pages, 3 columns → 2 rows

    def test_mac_staging_dir_is_inside_powerpoint_sandbox(self):
        self.assertIn("com.microsoft.Powerpoint", str(powerpoint.MAC_STAGING))

    def test_default_preview_dir(self):
        p = Path("/x/task/out/deck-260930.pptx")
        self.assertEqual(preview_slides.default_preview_dir(p), Path("/x/task/out/preview/deck-260930"))


@unittest.skipUnless(os.environ.get("CC_SLIDES_POWERPOINT") == "1",
                     "set CC_SLIDES_POWERPOINT=1 to drive real PowerPoint")
class PowerPointIntegrationTests(unittest.TestCase):
    def test_preview_renders_every_slide(self):
        with tempfile.TemporaryDirectory() as d:
            deck = make_template(Path(d))
            pages, sheet = preview_slides.preview(deck, Path(d) / "preview")
            self.assertEqual(len(pages), 2)
            self.assertTrue(sheet.exists())


if __name__ == "__main__":
    unittest.main()
