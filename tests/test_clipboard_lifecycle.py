"""Windows clipboard ownership and close-to-tray regression tests.

Offscreen Qt is adequate for tagged MIME and lifecycle unit assertions; the
interactive tray and cross-process clipboard still need a physical Windows test.
"""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QApplication

from clipmint_windows.clipboard_guard import OWN_COPY_MIME, OwnClipboardGuard
from clipmint_windows.history import History
from clipmint_windows.ui import ClipMintWindow


class ClipboardGuardTests(unittest.TestCase):
    def test_token_matches_only_our_mime_data(self):
        guard = OwnClipboardGuard()
        owned = QMimeData()
        owned.setText("record")
        guard.mark(owned)
        self.assertTrue(guard.is_own(owned))
        self.assertTrue(owned.hasText())
        self.assertEqual(owned.text(), "record")

        foreign = QMimeData()
        foreign.setText("different copied item")
        self.assertFalse(guard.is_own(foreign))
        foreign.setData(OWN_COPY_MIME, b"not-the-right-token")
        self.assertFalse(guard.is_own(foreign))

    def test_new_process_token_does_not_mask_external_items(self):
        previous = OwnClipboardGuard()
        current = OwnClipboardGuard()
        mime = QMimeData()
        previous.mark(mime)
        self.assertTrue(previous.is_own(mime))
        self.assertFalse(current.is_own(mime))


class ClipboardWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.win = ClipMintWindow(
            History(Path(self.tmp.name) / "test.sqlite3"),
            enable_hotkeys=False,
        )

    def tearDown(self):
        if not self.win._cleaned_up:
            self.win.cleanup()
        self.win.deleteLater()
        self.app.processEvents()
        self.tmp.cleanup()

    def test_internal_copy_never_creates_record_in_another_collection(self):
        self.win.history.add("TEXT", "work archived value", collection="Work")
        self.win.refresh()
        self.win.clips.setCurrentRow(0)
        self.assertIsNotNone(self.win._selected_id)
        self.win.copy_selected()
        # Simulate late dataChanged delivery after switching tabs.
        self.win.tabs.setCurrentIndex(1)
        self.win.clipboard_changed()
        self.assertEqual(len(self.win.history.list(collection="Personal")), 0)

    def test_external_copy_after_own_copy_is_not_discarded(self):
        self.win.history.add("TEXT", "work archived value", collection="Work")
        self.win.refresh()
        self.win.clips.setCurrentRow(0)
        self.win.copy_selected()
        self.win.tabs.setCurrentIndex(1)
        QApplication.clipboard().setText("new external item")
        self.app.processEvents()
        self.win.clipboard_changed()
        entries = self.win.history.list(collection="Personal")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["body"], "new external item")

    def test_pause_does_not_capture_copies_made_while_paused(self):
        self.win.pause.setChecked(False)
        QApplication.clipboard().setText("do not capture while paused")
        self.app.processEvents()
        self.assertFalse(self.win.monitoring)
        self.assertEqual(len(self.win.history.list()), 0)
        self.win.pause.setChecked(True)
        self.assertEqual(len(self.win.history.list()), 0)
        QApplication.clipboard().setText("new copy while resumed")
        self.app.processEvents()
        self.assertEqual([row["body"] for row in self.win.history.list()],
                         ["new copy while resumed"])

    def test_no_system_tray_close_quits_instead_of_running_invisibly(self):
        # Force no usable tray even if the CI runner has a notification area.
        self.win._tray = None
        self.win.close()
        self.assertTrue(self.win._cleaned_up)
        self.assertTrue(self.win._quit_requested)


if __name__ == "__main__":
    unittest.main()
