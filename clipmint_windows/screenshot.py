"""Qt screen-region selector for the Windows prototype (active monitor only)."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class RegionSelector(QWidget):
    selected = Signal(object, object)  # QRect in local DIPs; screen QPixmap
    cancelled = Signal()

    def __init__(self, screen, snapshot: QPixmap):
        super().__init__(None)
        self.screen = screen
        self.snapshot = snapshot
        self.start_point: QPoint | None = None
        self.end_point: QPoint | None = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.drawPixmap(self.rect(), self.snapshot)
        p.fillRect(self.rect(), QColor(12, 7, 16, 115))
        if self.start_point is not None and self.end_point is not None:
            rect = QRect(self.start_point, self.end_point).normalized()
            # A less-tinted selected region, with an unmistakable red border.
            p.drawPixmap(rect, self.snapshot, rect)
            p.setPen(QPen(QColor("#ff4564"), 3))
            p.drawRect(rect)
            p.setPen(QColor("#fff0dc"))
            p.drawText(rect.topLeft() + QPoint(5, -6), f"{rect.width()} × {rect.height()}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.position().toPoint()
            self.end_point = self.start_point
            self.update()

    def mouseMoveEvent(self, event):
        if self.start_point is not None:
            self.end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.start_point is not None:
            self.end_point = event.position().toPoint()
            rect = QRect(self.start_point, self.end_point).normalized().intersected(self.rect())
            if rect.width() >= 8 and rect.height() >= 8:
                self.hide()
                self.selected.emit(rect, self.snapshot)
            else:
                self.hide()
                self.cancelled.emit()
            self.deleteLater()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()
            self.deleteLater()
        else:
            super().keyPressEvent(event)
