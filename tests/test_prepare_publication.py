import datetime
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_publication import (
    check,
    draft_status,
    prepare_post,
    publication_date,
)


class PreparePublicationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "post.md"

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_post(self, status="Status: draft"):
        self.path.write_text(
            "\n".join(
                [
                    "Title: Example",
                    "Date: 2026-01-01 12:00 +0800",
                    "Category: Review",
                    "Tags: Example",
                    "Slug: example",
                    "Authors: Wei Lee",
                    status,
                    "",
                    "Body",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def test_prepare_post_removes_draft_and_updates_date(self):
        self.write_post()

        changed = prepare_post(self.path, "2026-06-30 18:20 +0800")

        self.assertTrue(changed)
        content = self.path.read_text(encoding="utf-8")
        self.assertIn("Date: 2026-06-30 18:20 +0800", content)
        self.assertNotIn("Status:", content)
        self.assertTrue(content.endswith("\n"))

    def test_prepare_post_is_idempotent_after_preparation(self):
        self.write_post()
        prepare_post(self.path, "2026-06-30 18:20 +0800")

        self.assertFalse(prepare_post(self.path, "2026-06-30 18:21 +0800"))

    def test_check_rejects_changed_draft(self):
        self.write_post()

        self.assertEqual(check([self.path]), 1)
        self.assertTrue(draft_status(self.path))

    def test_publication_date_uses_taiwan_timezone(self):
        utc = datetime.datetime(2026, 6, 30, 10, 20, tzinfo=datetime.UTC)

        self.assertEqual(publication_date(utc), "2026-06-30 18:20 +0800")


if __name__ == "__main__":
    unittest.main()
