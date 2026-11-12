"""Windows clipboard-history drag MIME construction.

Images carry both QImage data for image editors and a real on-disk PNG file URL
for native/Firefox upload fields. URLs are populated only during an explicit drag.
No files or clipboard records are sent over the network by ClipMint.
"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QMimeData, QUrl
from PySide6.QtGui import QPixmap

from .drag_export import DragImageExport


def mime_for_drag(row, exporter: DragImageExport) -> QMimeData | None:
    kind = row["kind"]
    mime = QMimeData()
    if kind == "IMAGE":
        data = row["image"]
        if not isinstance(data, bytes):
            return None
        pix = QPixmap()
        if not pix.loadFromData(data, "PNG"):
            return None
        # MIME image allows editor drops; URL makes HTML <input type=file>
        # and Windows Explorer-style drop targets see an actual PNG file.
        path = exporter.export_png(int(row["id"]), data)
        mime.setImageData(pix.toImage())
        mime.setUrls([QUrl.fromLocalFile(str(path))])
    elif kind == "FILES":
        try:
            paths = json.loads(row["body"])
        except (TypeError, ValueError):
            return None
        if not isinstance(paths, list):
            return None
        urls = [
            QUrl.fromLocalFile(str(Path(p)))
            for p in paths
            if isinstance(p, str) and p and Path(p).exists()
        ]
        if not urls:
            return None
        mime.setUrls(urls)
    elif kind == "TEXT":
        if not isinstance(row["body"], str) or not row["body"]:
            return None
        mime.setText(row["body"])
    else:
        return None
    return mime
