"""Platform-neutral data-store regression tests; run on Windows CI too."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from clipmint_windows.history import History, likely_sensitive


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.td = TemporaryDirectory()
        self.hist = History(Path(self.td.name) / "db.sqlite3")

    def tearDown(self):
        self.hist.close()
        self.td.cleanup()

    def test_text_saved_and_deduplicated(self):
        a = self.hist.add("TEXT", "example snippet")
        b = self.hist.add("TEXT", "example snippet")
        self.assertEqual(a, b)
        self.assertEqual(len(self.hist.list()), 1)

    def test_no_empty_or_oversized_text(self):
        self.assertIsNone(self.hist.add("TEXT", ""))
        self.assertIsNone(self.hist.add("TEXT", "x" * 300_001))
        self.assertEqual(len(self.hist.list()), 0)

    def test_best_effort_secrets_excluded(self):
        for secret in ("password: p@ssword123", "otp=123456", "-----BEGIN PRIVATE KEY-----"):
            self.assertTrue(likely_sensitive(secret))
            self.assertIsNone(self.hist.add("TEXT", secret))
        self.assertEqual(len(self.hist.list()), 0)

    def test_search_is_literal_no_wildcard_expansion(self):
        self.hist.add("TEXT", "a_percent_%_in_text")
        self.hist.add("TEXT", "a regular record")
        self.assertEqual(len(self.hist.list("%")), 1)
        self.assertEqual(len(self.hist.list("_")), 1)

    def test_collections_isolated(self):
        self.hist.add("TEXT", "work thing", collection="Work")
        self.hist.add("TEXT", "personal thing", collection="Personal")
        self.assertEqual(len(self.hist.list(collection="Work")), 1)
        self.assertEqual(len(self.hist.list(collection="Personal")), 1)
        self.assertEqual(len(self.hist.list(collection="Temporary")), 0)

    def test_duplicate_value_kept_separate_per_collection(self):
        a = self.hist.add("TEXT", "one value", collection="Work")
        b = self.hist.add("TEXT", "one value", collection="Personal")
        self.assertNotEqual(a, b)
        self.assertEqual(len(self.hist.list()), 2)

    def test_pin_and_delete(self):
        a = self.hist.add("TEXT", "pinned snippet")
        self.hist.set_pin(a, True)
        self.assertTrue(self.hist.get(a)["pinned"])
        self.hist.delete(a)
        self.assertIsNone(self.hist.get(a))

    def test_png_size_limit(self):
        self.assertIsNone(self.hist.add("IMAGE", image=b"a" * 10_000_001))
        self.assertIsNone(self.hist.add("IMAGE", image=b""))

    def test_reopen_survives(self):
        self.hist.add("TEXT", "persist me")
        self.hist.close()
        self.hist = History(Path(self.td.name) / "db.sqlite3")
        self.assertEqual(self.hist.list()[0]["body"], "persist me")

    def test_invalid_collection_and_kind_rejected(self):
        with self.assertRaises(ValueError):
            self.hist.add("TEXT", "x", collection="Missing")
        with self.assertRaises(ValueError):
            self.hist.add("PASSWORD", "x")


if __name__ == "__main__":
    unittest.main()
