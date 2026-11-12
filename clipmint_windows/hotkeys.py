"""Optional user-scoped native RegisterHotKey support for Windows.

Does not install hooks, inject code, or intercept other applications' keystrokes.
The hotkey registration can legitimately fail if another program owns it.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import threading
from PySide6.QtCore import QObject, Signal

MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
VK_S = 0x53


class WindowsHotkey(QObject):
    activated = Signal()
    registration_failed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._ready = threading.Event()

    def start(self):
        if os.name != "nt" or self._thread is not None:
            return
        self._thread = threading.Thread(target=self._pump, name="ClipMint-Hotkey", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=2)

    def _pump(self):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_uint, ctypes.c_uint]
        user32.RegisterHotKey.restype = wintypes.BOOL
        user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, ctypes.c_uint, ctypes.c_uint]
        user32.GetMessageW.restype = ctypes.c_int
        kernel32.GetCurrentThreadId.restype = wintypes.DWORD
        self._thread_id = int(kernel32.GetCurrentThreadId())
        # Windows creates this thread's message queue when PeekMessage is called.
        msg = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)
        ok = bool(user32.RegisterHotKey(None, 0xC17, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_S))
        self._ready.set()
        if not ok:
            self.registration_failed.emit()
            return
        try:
            while True:
                result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result <= 0:
                    break
                if msg.message == WM_HOTKEY and msg.wParam == 0xC17:
                    self.activated.emit()
        finally:
            user32.UnregisterHotKey(None, 0xC17)

    def stop(self):
        if os.name != "nt" or self._thread_id is None:
            return
        ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=1)
        self._thread = None
        self._thread_id = None
