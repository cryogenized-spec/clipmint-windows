from pathlib import Path
import os
import unittest
from unittest.mock import patch

from clipmint_windows.history import default_data_dir


class IsolationTests(unittest.TestCase):
    def test_private_windows_folder_no_linux_archive(self):
        with patch.dict(os.environ, {"LOCALAPPDATA": r"C:\Users\tester\AppData\Local"}):
            result = str(default_data_dir()).replace("/", "\\")
            self.assertIn("ClipMintWindows", result)
            self.assertNotIn(".local\\share", result)

    def test_explicit_test_data_override(self):
        with patch.dict(os.environ, {"CLIPMINT_WINDOWS_DATA_DIR": "test-only-dir"}):
            self.assertEqual(default_data_dir(), Path("test-only-dir"))


if __name__ == "__main__":
    unittest.main()
