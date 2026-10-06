"""Tests for scripts/clear_ongoing.py.

Run with either:

    python -m unittest discover tests
    python -m pytest tests

The script's whole job is to delete a round folder, so the tests are mostly about
refusals: an archive that is missing a file, holds a different version of one, or is not
an archived round at all must stop the deletion. Each test builds its own tree under a
temporary root — the real `archived/` tree is never touched.
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import clear_ongoing  # noqa: E402  # pyright: ignore[reportMissingImports]

SLUG = "example-thread"

# A round as it sits in ongoing/, and the same round as archived: identical except that
# final.md became reply.md, and meta.md joins it at archive time.
ROUND = {
    "original.txt": "From: someone@example.com\n\nBody.\n",
    "draft.md": "Hi,\n\nDraft.\n",
    "final.md": "Hi,\n\nSent.\n",
    "meta.md": "---\nround: 1\n---\n\nSummary.\n",
    SLUG + ".eml": "Subject: example\n\nHi,\n\nSent.\n",
}


def archived(round_files: dict[str, str]) -> dict[str, str]:
    """The archived form of a round: final.md renamed to reply.md."""
    return {
        ("reply.md" if name == "final.md" else name): content
        for name, content in round_files.items()
    }


class ClearOngoingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.archive_root = self.root / "archived"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, directory: Path, files: dict[str, str]) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            (directory / name).write_text(content, encoding="utf-8")
        return directory

    def round_dir(self, slug: str = SLUG, files: dict[str, str] | None = None) -> Path:
        return self.write(self.root / "ongoing" / slug, files if files is not None else ROUND)

    def archive_dir(
        self, date: str, slug: str = SLUG, files: dict[str, str] | None = None
    ) -> Path:
        directory = self.archive_root.joinpath(*date.split("-"), slug)
        return self.write(directory, files if files is not None else archived(ROUND))

    def test_clears_a_round_the_archive_covers(self) -> None:
        source = self.round_dir()
        archive = self.archive_dir("2026-09-23")

        used, removed = clear_ongoing.clear_round(source, self.archive_root)

        self.assertEqual(used, archive)
        self.assertEqual(removed, sorted(ROUND))
        self.assertFalse(source.exists())

    def test_dry_run_keeps_the_round(self) -> None:
        source = self.round_dir()
        self.archive_dir("2026-09-23")

        used, removed = clear_ongoing.clear_round(source, self.archive_root, dry_run=True)

        self.assertTrue(used.is_dir())
        self.assertEqual(len(removed), len(ROUND))
        self.assertTrue(source.exists())

    def test_refuses_when_a_file_differs(self) -> None:
        source = self.round_dir()
        stale = archived(ROUND) | {"original.txt": "From: someone@example.com\n\nEdited.\n"}
        self.archive_dir("2026-09-23", files=stale)

        with self.assertRaises(clear_ongoing.ClearError) as caught:
            clear_ongoing.clear_round(source, self.archive_root)

        self.assertIn("original.txt differs", str(caught.exception))
        self.assertTrue(source.exists())

    def test_refuses_when_a_file_is_missing(self) -> None:
        source = self.round_dir()
        partial = archived(ROUND)
        del partial[SLUG + ".eml"]
        self.archive_dir("2026-09-23", files=partial)

        with self.assertRaises(clear_ongoing.ClearError) as caught:
            clear_ongoing.clear_round(source, self.archive_root)

        self.assertIn(f"{SLUG}.eml is missing", str(caught.exception))
        self.assertTrue(source.exists())

    def test_refuses_a_directory_that_is_not_an_archived_round(self) -> None:
        source = self.round_dir()
        # Every file matches, but the round was never archived: no meta.md, no reply.md.
        self.archive_dir("2026-09-23", files={"original.txt": ROUND["original.txt"]})

        with self.assertRaises(clear_ongoing.ClearError) as caught:
            clear_ongoing.clear_round(source, self.archive_root)

        self.assertIn("no reply.md", str(caught.exception))
        self.assertIn("no meta.md", str(caught.exception))
        self.assertTrue(source.exists())

    def test_refuses_when_no_archive_exists(self) -> None:
        source = self.round_dir()

        with self.assertRaises(clear_ongoing.ClearError) as caught:
            clear_ongoing.clear_round(source, self.archive_root)

        self.assertIn("no archived round found", str(caught.exception))
        self.assertTrue(source.exists())

    def test_refuses_a_folder_that_is_not_under_ongoing(self) -> None:
        source = self.round_dir(slug="elsewhere")
        source.rename(self.root / "elsewhere")
        self.archive_dir("2026-09-23")

        with self.assertRaises(clear_ongoing.ClearError) as caught:
            clear_ongoing.clear_round(self.root / "elsewhere", self.archive_root)

        self.assertIn("not a round folder directly under ongoing/", str(caught.exception))
        self.assertTrue((self.root / "elsewhere").exists())

    def test_picks_the_newest_covering_archive(self) -> None:
        source = self.round_dir()
        self.archive_dir("2026-09-22")
        newest = self.archive_dir("2026-09-23")

        used, _ = clear_ongoing.clear_round(source, self.archive_root)

        self.assertEqual(used, newest)

    def test_same_day_repeat_round_is_matched_by_suffix(self) -> None:
        source = self.round_dir(slug=SLUG + "-r2")
        archive = self.archive_dir("2026-09-23", slug=SLUG + "-r2")

        used, _ = clear_ongoing.clear_round(source, self.archive_root)

        self.assertEqual(used, archive)


class ArchiveCandidatesTests(unittest.TestCase):
    def test_orders_oldest_path_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for date, slug in (
                ("2026-09-23", SLUG),
                ("2026-07-30", SLUG),
                ("2026-09-23", SLUG + "-r2"),
            ):
                (root.joinpath(*date.split("-"), slug)).mkdir(parents=True)

            found = [path.name for path in clear_ongoing.archive_candidates(root, SLUG)]

            self.assertEqual(found, [SLUG, SLUG, SLUG + "-r2"])

    def test_ignores_a_different_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "2026" / "09" / "23" / "other-thread").mkdir(parents=True)

            self.assertEqual(clear_ongoing.archive_candidates(root, SLUG), [])


if __name__ == "__main__":
    unittest.main()
