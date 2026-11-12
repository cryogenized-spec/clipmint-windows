"""Standalone Windows x64 ClipMint entrypoint (separate from ClipMint Linux)."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLockFile

from clipmint_windows.history import History, default_data_dir
from clipmint_windows.ui import ClipMintWindow


def main() -> int:
    if sys.platform != "win32" and "--self-test" not in sys.argv:
        print("This edition is Windows-only; run the Linux ClipMint edition on Mint.", file=sys.stderr)
        return 2
    app = QApplication(sys.argv)
    app.setApplicationName("ClipMintWindows")
    app.setOrganizationName("ClipMint")
    app.setQuitOnLastWindowClosed(False)
    if "--self-test" in sys.argv:
        with tempfile.TemporaryDirectory() as td:
            w = ClipMintWindow(History(Path(td) / "test.sqlite3"), enable_hotkeys=False)
            assert w.windowTitle().startswith("ClipMint")
            w.history.add("TEXT", "self-test entry")
            assert len(w.history.list()) == 1
            w.refresh()
            w.quit_app()
        # A windowed PyInstaller EXE on Windows has no sys.stdout.
        if sys.stdout is not None:
            print("PASS: ClipMint Windows Qt UI and SQLite self-test")
        return 0
    data = default_data_dir()
    data.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(data / "instance.lock"))
    lock.setStaleLockTime(30_000)
    if not lock.tryLock(100):
        print("ClipMint Windows is already running. Restore it from the system tray.", file=sys.stderr)
        return 0
    try:
        win = ClipMintWindow()
        app.aboutToQuit.connect(win.cleanup)
        win.show()
        return app.exec()
    finally:
        lock.unlock()


if __name__ == "__main__":
    raise SystemExit(main())
