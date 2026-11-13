"""Gothic ClipMint native Qt interface, Windows x64 alpha.

Independent implementation. Does not modify or load the Linux edition's archive.
No developer telemetry, network service, or auto-update mechanism.
"""
from __future__ import annotations

from datetime import datetime
import io
import json
import os
from pathlib import Path
import sys

from PySide6.QtCore import QBuffer, QIODevice, QMimeData, QPoint, QRect, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QColor, QCursor, QDrag, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
    QPushButton, QSystemTrayIcon, QTabBar, QVBoxLayout, QWidget,
)

from .history import History, default_data_dir
from .drag_export import DragImageExport
from .drag_mime import mime_for_drag
from .hotkeys import WindowsHotkey
from .recording import Recorder
from .screenshot import RegionSelector
from .style import CSS


def asset(name: str) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / "assets" / name


def labeled(text: str, name: str = "micro") -> QLabel:
    out = QLabel(text)
    out.setObjectName(name)
    out.setWordWrap(True)
    return out


def rule(parent: QVBoxLayout):
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet("background:#78505e; border:0")
    parent.addWidget(line)


def make_panel() -> tuple[QFrame, QVBoxLayout]:
    box = QFrame()
    box.setObjectName("panel")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(13, 14, 13, 14)
    lay.setSpacing(10)
    return box, lay


class ClipList(QListWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return
        row = self.owner.history.get(int(item.data(Qt.ItemDataRole.UserRole)))
        if row is None:
            return
        try:
            mime = mime_for_drag(row, self.owner._drag_exports)
        except (OSError, ValueError) as exc:
            self.owner.status.showMessage(f"Cannot drag this item: {exc}", 5000)
            return
        if mime is None:
            self.owner.status.showMessage("This item is unavailable for dragging", 4000)
            return
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)


class ClipMintWindow(QMainWindow):
    def __init__(self, history: History | None = None, enable_hotkeys: bool = True):
        super().__init__()
        self.history = history or History()
        self.recorder = Recorder()
        self._drag_exports = DragImageExport()
        self.monitoring = True
        self._quit_requested = False
        self._cleaned_up = False
        self._suppress_next = False
        self._selected_id: int | None = None
        self._selector: RegionSelector | None = None
        self._record_start_pending = False
        self._tray: QSystemTrayIcon | None = None
        self._hotkeys: WindowsHotkey | None = None
        self.setWindowTitle("ClipMint — Clipboard & Capture [Windows alpha]")
        icon = QIcon(str(asset("ClipMint.ico")))
        if icon.isNull():
            icon = QIcon(str(asset("ClipMint.png")))
        self.setWindowIcon(icon)
        self.resize(1320, 865)
        self.setMinimumSize(980, 680)
        self.setStyleSheet(CSS)
        self._build()
        self._install_tray()
        QApplication.clipboard().dataChanged.connect(self.clipboard_changed)
        # Do not archive the current clipboard at launch. New changes only.
        self.refresh()
        if enable_hotkeys and os.name == "nt":
            self._hotkeys = WindowsHotkey(self)
            self._hotkeys.activated.connect(self.take_area_screenshot)
            self._hotkeys.registration_failed.connect(
                lambda: self.status.showMessage("Global Ctrl+Shift+S unavailable (already assigned)", 5000))
            self._hotkeys.start()

    def _build(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(14, 12, 14, 14)
        outer.setSpacing(11)

        head = QHBoxLayout()
        star = labeled("✧", "section")
        star.setStyleSheet("font-size:31px;color:#d7ab83")
        head.addWidget(star)
        title = labeled("ClipMint", "brand")
        head.addWidget(title)
        head.addWidget(labeled("クリップミント  /  WINDOWS X64 ALPHA", "japanese"))
        head.addStretch()
        head.addWidget(labeled("●  LOCAL / OFFLINE", "status"))
        outer.addLayout(head)
        rule(outer)

        body = QHBoxLayout()
        body.setSpacing(9)
        outer.addLayout(body, 1)
        portrait, p = make_panel()
        portrait.setMinimumWidth(220)
        portrait.setMaximumWidth(300)
        p.addWidget(labeled("FILE / 001    CHARACTER", "micro"))
        icon = QLabel()
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(QPixmap(str(asset("ClipMint.png"))).scaled(
            245, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        p.addWidget(icon, 1)
        p.addWidget(labeled("CRIMSON ARCHIVE", "section"))
        p.addWidget(labeled("Windows edition  •  independent archive", "micro"))
        rule(p)
        p.addWidget(labeled("Private local storage. The Linux Mint database is never read or modified.", "micro"))
        body.addWidget(portrait, 3)

        timeline, tl = make_panel()
        timeline.setMinimumWidth(310)
        tl.addWidget(labeled("01 / YOUR COLLECTION", "micro"))
        tl.addWidget(labeled("Clipboard  ·  クリップボード", "section"))
        self.tabs = QTabBar()
        for tab in ("Work", "Personal", "Temporary"):
            self.tabs.addTab(tab)
        self.tabs.currentChanged.connect(self.refresh)
        tl.addWidget(self.tabs)
        self.search = QLineEdit()
        self.search.setPlaceholderText("⌕  Search the archive...")
        self.search.textChanged.connect(self.refresh)
        tl.addWidget(self.search)
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(labeled("SHOW", "micro"))
        self.kind = QComboBox()
        for x in ("All", "TEXT", "IMAGE", "FILES"):
            self.kind.addItem(x)
        self.kind.currentIndexChanged.connect(self.refresh)
        filter_bar.addWidget(self.kind)
        self.count = labeled("0 / 0", "micro")
        filter_bar.addWidget(self.count)
        tl.addLayout(filter_bar)
        self.clips = ClipList(self)
        self.clips.itemSelectionChanged.connect(self.show_selected)
        tl.addWidget(self.clips, 1)
        body.addWidget(timeline, 4)

        preview, pl = make_panel()
        preview.setMinimumWidth(270)
        pl.addWidget(labeled("Selected item  ·  プレビュー", "section"))
        self.preview_label = QLabel("Select a clipboard entry to preview")
        self.preview_label.setObjectName("preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.preview_label.setMinimumHeight(210)
        pl.addWidget(self.preview_label, 3)
        self.selected_name = labeled("No selection", "section")
        pl.addWidget(self.selected_name)
        rule(pl)
        pl.addWidget(labeled("FILE DETAILS / 詳細", "subhead"))
        self.details = labeled("Type —     Saved —     Collection —", "micro")
        pl.addWidget(self.details)
        pl.addStretch(1)
        act = QHBoxLayout()
        self.copy_button = QPushButton("COPY")
        self.copy_button.setObjectName("light")
        self.copy_button.clicked.connect(self.copy_selected)
        act.addWidget(self.copy_button)
        self.pin_button = QPushButton("PIN")
        self.pin_button.clicked.connect(self.pin_selected)
        act.addWidget(self.pin_button)
        self.delete_button = QPushButton("DELETE")
        self.delete_button.clicked.connect(self.delete_selected)
        act.addWidget(self.delete_button)
        pl.addLayout(act)
        body.addWidget(preview, 4)

        modules, ml = make_panel()
        modules.setMinimumWidth(115)
        modules.setMaximumWidth(160)
        ml.addWidget(labeled("MODULES", "micro"))
        for title, handler in (
            ("▤  Clipboard", lambda: self.search.setFocus()),
            ("▣  Screenshots", self.open_screenshots),
            ("◉  Recordings", self.open_recordings),
            ("⚙  Settings", self.show_settings),
        ):
            b = QPushButton(title)
            b.setObjectName("module")
            b.clicked.connect(handler)
            ml.addWidget(b)
        ml.addStretch()
        self.pause = QCheckBox("Monitor")
        self.pause.setChecked(True)
        self.pause.toggled.connect(self.toggle_monitor)
        ml.addWidget(self.pause)
        body.addWidget(modules, 2)

        foot = QHBoxLayout()
        self.status = self.statusBar()
        self.status.showMessage("Ready · clipboard monitoring active · history stored locally")
        self.video_button = QPushButton("●  Record Video   /  MP4")
        self.video_button.setObjectName("primary")
        self.video_button.clicked.connect(self.toggle_video)
        foot.addWidget(self.video_button, 2)
        self.shot_button = QPushButton("▣  Screenshot Area   /   CAPTURE")
        self.shot_button.setObjectName("light")
        self.shot_button.clicked.connect(self.take_area_screenshot)
        foot.addWidget(self.shot_button, 2)
        outer.addLayout(foot)

    def _install_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray = QSystemTrayIcon(self.windowIcon(), self)
        menu = QMenu()
        show = QAction("Open ClipMint", self)
        show.triggered.connect(self.restore)
        menu.addAction(show)
        screenshot = QAction("Capture area", self)
        screenshot.triggered.connect(self.take_area_screenshot)
        menu.addAction(screenshot)
        quit_action = QAction("Quit ClipMint", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(lambda *_: self.restore())
        self._tray.setToolTip("ClipMint Windows alpha")
        self._tray.show()

    def active_collection(self) -> str:
        return self.tabs.tabText(self.tabs.currentIndex())

    def refresh(self, *_args):
        if not hasattr(self, "clips"):
            return
        prior = self._selected_id
        self.clips.clear()
        k = self.kind.currentText()
        entries = self.history.list(self.search.text(), "" if k == "All" else k,
                                    collection=self.active_collection())
        for row in entries:
            s = row["body"].replace("\n", " ") if row["kind"] != "IMAGE" else "Screenshot / clipboard image"
            if row["kind"] == "FILES":
                try:
                    s = ", ".join(Path(x).name for x in json.loads(row["body"]))
                except (ValueError, TypeError):
                    s = "File references"
            prefix = "★ " if row["pinned"] else ""
            item = QListWidgetItem(f"{prefix}[{row['kind']}]  {s[:82]}")
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.clips.addItem(item)
            if row["id"] == prior:
                self.clips.setCurrentItem(item)
        self.count.setText(f"{len(entries)} shown")
        if not self.clips.currentItem():
            self._selected_id = None
            self.selected_name.setText("No selection")
            self.preview_label.setText("Select a clipboard entry to preview")
            self.preview_label.setPixmap(QPixmap())
            self.details.setText("Type —     Saved —     Collection —")

    def show_selected(self):
        item = self.clips.currentItem()
        if not item:
            return
        self._selected_id = int(item.data(Qt.ItemDataRole.UserRole))
        row = self.history.get(self._selected_id)
        if row is None:
            return
        self.selected_name.setText(row["kind"] + (" ★" if row["pinned"] else ""))
        self.pin_button.setText("UNPIN" if row["pinned"] else "PIN")
        self.details.setText(
            f"Type: {row['kind']}\nSaved: {datetime.fromtimestamp(row['created_utc']).strftime('%Y-%m-%d %H:%M')}\n"
            f"Collection: {row['collection']}\nStored locally · NOT encrypted")
        if row["kind"] == "IMAGE":
            pix = QPixmap()
            if pix.loadFromData(row["image"], "PNG"):
                self.preview_label.setPixmap(pix.scaled(
                    480, 330, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
            else:
                self.preview_label.setText("Image unavailable")
        else:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText(row["body"][:2800])

    def clipboard_changed(self):
        if self._suppress_next:
            self._suppress_next = False
            return
        if not self.monitoring:
            return
        cb = QApplication.clipboard()
        mime = cb.mimeData()
        if not mime:
            return
        ident = None
        if mime.hasImage():
            im = cb.image()
            if not im.isNull():
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                if im.save(buffer, "PNG"):
                    ident = self.history.add("IMAGE", image=bytes(buffer.data()),
                                             collection=self.active_collection())
                buffer.close()
        elif mime.hasUrls():
            paths = [u.toLocalFile() for u in mime.urls() if u.isLocalFile()]
            if paths:
                ident = self.history.add("FILES", json.dumps(paths, ensure_ascii=False),
                                         collection=self.active_collection())
        elif mime.hasText():
            text = mime.text()
            ident = self.history.add("TEXT", text, collection=self.active_collection())
        if ident is not None:
            self.refresh()
            self.status.showMessage("Saved new clipboard entry locally", 3500)

    def copy_selected(self):
        if self._selected_id is None:
            return
        row = self.history.get(self._selected_id)
        if row is None:
            return
        mime = QMimeData()
        if row["kind"] == "IMAGE":
            pix = QPixmap()
            if not pix.loadFromData(row["image"], "PNG"):
                return
            mime.setImageData(pix.toImage())
        elif row["kind"] == "FILES":
            mime.setUrls([QUrl.fromLocalFile(p) for p in json.loads(row["body"])])
        else:
            mime.setText(row["body"])
        self._suppress_next = True
        QApplication.clipboard().setMimeData(mime)
        QTimer.singleShot(250, self._clear_clipboard_suppression)
        self.status.showMessage("Copied to clipboard · without re-archiving", 3500)

    def _clear_clipboard_suppression(self):
        self._suppress_next = False

    def pin_selected(self):
        if self._selected_id is None:
            return
        row = self.history.get(self._selected_id)
        if row:
            self.history.set_pin(self._selected_id, not row["pinned"])
            self.refresh()

    def delete_selected(self):
        if self._selected_id is None:
            return
        self.history.delete(self._selected_id)
        self._selected_id = None
        self.refresh()

    def toggle_monitor(self, checked: bool):
        self.monitoring = checked
        self.status.showMessage("Monitoring active" if checked else "Clipboard monitoring PAUSED")

    def restore(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _select_region(self, callback):
        if self._selector is not None:
            return
        self.hide()
        def ready():
            screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
            if screen is None:
                self.restore()
                return
            snapshot = screen.grabWindow(0)
            self._selector = RegionSelector(screen, snapshot)
            self._selector.selected.connect(lambda rect, pix: self._region_chosen(rect, pix, screen, callback))
            self._selector.cancelled.connect(self._cancel_selection)
            self._selector.show()
            self._selector.raise_()
            self._selector.setFocus()
        QTimer.singleShot(400, ready)

    def _region_chosen(self, rect: QRect, snapshot: QPixmap, screen, callback):
        self._selector = None
        QTimer.singleShot(200, lambda: callback(rect, snapshot, screen))

    def _cancel_selection(self):
        self._selector = None
        self.restore()

    def take_area_screenshot(self):
        if self.recorder.process:
            self.status.showMessage("Stop the current video before capturing", 3500)
            return
        self._select_region(self._save_screenshot)

    def _save_screenshot(self, rect: QRect, snapshot: QPixmap, screen):
        ratio = snapshot.devicePixelRatio() or 1.0
        crop = QRect(int(rect.x() * ratio), int(rect.y() * ratio),
                     int(rect.width() * ratio), int(rect.height() * ratio))
        selection = snapshot.copy(crop)
        if selection.isNull():
            QMessageBox.warning(self, "Capture failed", "The selected region could not be captured.")
            self.restore()
            return
        folder = default_data_dir() / "Screenshots"
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / (datetime.now().strftime("Screenshot-%Y%m%d-%H%M%S-%f") + ".png")
        if not selection.save(str(output), "PNG"):
            QMessageBox.warning(self, "Save failed", "Could not save the screenshot.")
        else:
            data = output.read_bytes()
            self.history.add("IMAGE", image=data, collection=self.active_collection())
            self.refresh()
            self.status.showMessage(f"Screenshot saved: {output}", 10000)
        self.restore()

    def toggle_video(self):
        if self.recorder.process:
            try:
                output = self.recorder.stop()
                self.status.showMessage(f"Recording saved: {output}", 12000)
                QMessageBox.information(self, "Video saved", f"Recorded MP4 to:\n{output}")
            except Exception as exc:
                QMessageBox.warning(self, "Recording failed", str(exc))
            finally:
                self.video_button.setText("●  Record Video   /  MP4")
            return
        self._select_region(self._begin_recording)

    def _begin_recording(self, rect: QRect, snapshot: QPixmap, screen):
        ratio = snapshot.devicePixelRatio() or 1.0
        # Known limitation: mixed-DPI multi-monitor coordinates need field verification.
        x = int(screen.geometry().left() * ratio + rect.left() * ratio)
        y = int(screen.geometry().top() * ratio + rect.top() * ratio)
        try:
            output = self.recorder.start(
                (x, y, int(rect.width() * ratio), int(rect.height() * ratio)),
                default_data_dir() / "Recordings")
            self.video_button.setText("■  Stop Recording  /  SAVE")
            self.status.showMessage("Recording · click STOP to save MP4")
        except Exception as exc:
            QMessageBox.warning(self, "Recording unavailable", str(exc))
        self.restore()

    def open_screenshots(self):
        self._open_folder(default_data_dir() / "Screenshots")

    def open_recordings(self):
        self._open_folder(default_data_dir() / "Recordings")

    def _open_folder(self, folder: Path):
        folder.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(folder))
        else:
            self.status.showMessage(f"Folder: {folder}", 6000)

    def show_settings(self):
        QMessageBox.information(self, "ClipMint Windows alpha — settings",
            "This edition is independent of Linux Mint.\n\n"
            "History: %LOCALAPPDATA%\\ClipMintWindows\\history.sqlite3\n"
            "Storage: PLAINTEXT (not encrypted).\n"
            "Network: no analytics or auto-updates.\n"
            "Monitoring: toggle via the right-hand sidebar.\n"
            "Screenshot hotkey: Ctrl+Shift+S (if available).\n"
            "Recording: bundled FFmpeg included offline; no separate installation.\n\n"
            "No Windows installer or automatic startup is enabled in this alpha.")

    def closeEvent(self, event):
        if self._tray and not self._quit_requested:
            self.hide()
            event.ignore()
        else:
            event.accept()

    def cleanup(self):
        if self._cleaned_up:
            return
        self._cleaned_up = True
        self._quit_requested = True
        if self.recorder.process:
            self.recorder.abort()
        if self._hotkeys:
            self._hotkeys.stop()
        self._drag_exports.cleanup()
        self.history.close()

    def quit_app(self):
        self.cleanup()
        QApplication.quit()
