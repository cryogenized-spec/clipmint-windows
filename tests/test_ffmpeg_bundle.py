"""Offline FFmpeg resolution and build provenance tests."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from clipmint_windows.recording import ffmpeg_executable
from tools.prepare_ffmpeg import SHA256, URL, download_verified


class FFmpegBundleTests(unittest.TestCase):
    def test_source_artifact_is_pinned_to_fixed_hash(self):
        self.assertTrue(URL.endswith("/ffmpeg-9.0.2-essentials_build.zip"))
        self.assertEqual(len(SHA256), 64)

    def test_checksum_checked_before_consumption(self):
        payload = b"sample only for test"
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "download.zip"
            with patch("tools.prepare_ffmpeg.urlopen", return_value=BytesIO(payload)):
                download_verified("https://example.invalid/archive.zip", sha256(payload).hexdigest(), p)
            self.assertEqual(p.read_bytes(), payload)
            with patch("tools.prepare_ffmpeg.urlopen", return_value=BytesIO(payload)):
                with self.assertRaises(ValueError):
                    download_verified("https://example.invalid/archive.zip", "0" * 64, p)
            self.assertFalse(p.exists())

    def test_frozen_application_uses_only_its_bundled_binary(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "tools" / "ffmpeg.exe"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"dummy exe")
            with patch("sys._MEIPASS", tmp, create=True), patch(
                "shutil.which", side_effect=AssertionError("PATH must not be inspected")
            ):
                self.assertEqual(ffmpeg_executable(), str(path))

    def test_missing_frozen_binary_fails_closed(self):
        with TemporaryDirectory() as tmp:
            with patch("sys._MEIPASS", tmp, create=True), patch(
                "shutil.which", side_effect=AssertionError("PATH must not be inspected")
            ):
                with self.assertRaisesRegex(RuntimeError, "Bundled FFmpeg missing"):
                    ffmpeg_executable()


if __name__ == "__main__":
    unittest.main()
