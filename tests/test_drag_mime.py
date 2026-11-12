"""Windows drag/drop regression tests (Qt offscreen on Windows CI).

A browser file input needs a real local-file URL, not only an image MIME value.
These tests inspect the actual QMimeData produced by ClipMint, but cannot
replace a hands-on Firefox/Windows file-upload acceptance test.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from clipmint_windows.drag_export import DragImageExport, MAX_DRAG_PNG_BYTES
from clipmint_windows.drag_mime import mime_for_drag


def sample_png() -> bytes:
    image = QImage(8, 8, QImage.Format.Format_ARGB32)
    image.fill(0xFFC12F53)
    buffer = QBuffer()
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        raise AssertionError("Unable to open Qt PNG buffer")
    if not image.save(buffer, "PNG"):
        raise AssertionError("Unable to write PNG")
    return bytes(buffer.data())


class DragMimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_image_drag_exposes_png_file_and_native_pixels(self):
        exporter = DragImageExport()
        png = sample_png()
        self.assertIsNone(exporter._temporary)  # nothing exported before drag
        mime = mime_for_drag({"id": 42, "kind": "IMAGE", "image": png}, exporter)
        self.assertIsNotNone(mime)
        self.assertTrue(mime.hasImage())
        self.assertTrue(mime.hasUrls())
        self.assertEqual(len(mime.urls()), 1)
        target = Path(mime.urls()[0].toLocalFile())
        self.assertEqual(target.suffix, ".png")
        self.assertEqual(target.read_bytes(), png)
        self.assertEqual(mime.imageData().width(), 8)
        exporter.cleanup()
        self.assertFalse(target.exists())

    def test_text_drag_is_copy_only_text_with_no_temporary_file(self):
        exporter = DragImageExport()
        mime = mime_for_drag({"id": 11, "kind": "TEXT", "body": "ClipMint copy"}, exporter)
        self.assertTrue(mime.hasText())
        self.assertFalse(mime.hasUrls())
        self.assertEqual(mime.text(), "ClipMint copy")
        self.assertIsNone(exporter._temporary)
        exporter.cleanup()

    def test_file_drag_ignores_unavailable_paths(self):
        with TemporaryDirectory() as folder:
            keep = Path(folder) / "example.txt"
            keep.write_text("demo", encoding="utf-8")
            missing = Path(folder) / "missing.txt"
            mime = mime_for_drag({"id": 9, "kind": "FILES",
                                  "body": json.dumps([str(missing), str(keep)])},
                                 DragImageExport())
            self.assertTrue(mime.hasUrls())
            self.assertEqual([u.toLocalFile() for u in mime.urls()], [str(keep)])

    def test_invalid_records_fail_closed(self):
        exporter = DragImageExport()
        self.assertIsNone(mime_for_drag({"id": 3, "kind": "IMAGE", "image": b"bad"}, exporter))
        self.assertIsNone(mime_for_drag({"id": 4, "kind": "FILES", "body": "bad json"}, exporter))
        self.assertIsNone(mime_for_drag({"id": 5, "kind": "TEXT", "body": ""}, exporter))
        self.assertIsNone(exporter._temporary)

    def test_export_rejects_wrong_type_id_or_size(self):
        exporter = DragImageExport()
        with self.assertRaises(ValueError):
            exporter.export_png(0, sample_png())
        with self.assertRaises(ValueError):
            exporter.export_png(8, b"not png")
        with self.assertRaises(ValueError):
            exporter.export_png(8, bytes((137,80,78,71,13,10,26,10)) + b"X" * MAX_DRAG_PNG_BYTES)
        self.assertIsNone(exporter._temporary)


if __name__ == "__main__":
    unittest.main()
