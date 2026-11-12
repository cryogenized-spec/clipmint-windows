"""Temporary, local-file bridge for Windows drag-to-upload targets.

Qt image clipboard data alone is not a file attachment. Windows browser upload
fields generally need a real file URL/CF_HDROP-compatible drag. Write a PNG only
when the user actively starts an IMAGE drag; never export history at launch.

All drag files live in a private per-process temporary directory and are cleaned
up on an ordinary application exit. A process crash can leave temporary data
behind, as with other temporary files; users should not drag sensitive images.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_DRAG_PNG_BYTES = 10_000_000


class DragImageExport:
    def __init__(self) -> None:
        self._temporary: TemporaryDirectory | None = None

    def export_png(self, item_id: int, data: bytes) -> Path:
        if not isinstance(item_id, int) or item_id < 1:
            raise ValueError("Invalid clipboard record ID")
        if not isinstance(data, bytes) or not data.startswith(PNG_SIGNATURE):
            raise ValueError("Only valid PNG clipboard records may be exported")
        if len(data) > MAX_DRAG_PNG_BYTES:
            raise ValueError("Drag image is larger than the permitted limit")
        if self._temporary is None:
            self._temporary = TemporaryDirectory(prefix="ClipMintWindows-drag-")
        # No user-supplied names/path components; hash avoids collisions after edits.
        name = f"clipmint-image-{item_id}-{sha256(data).hexdigest()[:12]}.png"
        path = Path(self._temporary.name) / name
        if not path.exists():
            path.write_bytes(data)
        return path

    def cleanup(self) -> None:
        if self._temporary is not None:
            try:
                self._temporary.cleanup()
            except OSError:
                # Windows may temporarily hold uploaded files open. Never abort
                # application shutdown over a best-effort cache cleanup.
                pass
            self._temporary = None
