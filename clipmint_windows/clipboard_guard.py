"""Tag only ClipMint's own clipboard writes, without dropping unrelated writes.

The old timer-based suppression swallowed the next clipboard event regardless
of who wrote it. A per-process random MIME marker instead identifies our own
archive-to-clipboard copies across delayed Qt/Windows dataChanged signals.
This marker is not a security boundary or a persistent secret.
"""
from __future__ import annotations

import secrets

from PySide6.QtCore import QMimeData


OWN_COPY_MIME = "application/x-clipmint-windows-internal-copy"


class OwnClipboardGuard:
    def __init__(self) -> None:
        self._token = secrets.token_bytes(16)

    def mark(self, mime: QMimeData) -> None:
        """Attach a random per-process identifier before setting the clipboard."""
        mime.setData(OWN_COPY_MIME, self._token)

    def is_own(self, mime: QMimeData | None) -> bool:
        """Do not block arbitrary writes just because their timing is close."""
        return bool(
            mime is not None
            and mime.hasFormat(OWN_COPY_MIME)
            and bytes(mime.data(OWN_COPY_MIME)) == self._token
        )
