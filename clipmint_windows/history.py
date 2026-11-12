"""Small, local-only SQLite clipboard archive for the Windows prototype.

No migration from the Linux edition. Clipboard contents are stored unencrypted.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import sqlite3
import time

MAX_TEXT_CHARS = 300_000
MAX_IMAGE_BYTES = 10_000_000
MAX_UNPINNED = 700

SENSITIVE_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    re.compile(r"\b(?:password|passphrase|otp|2fa|verification code)\s*[:=]\s*\S+", re.I),
)


def likely_sensitive(text: str) -> bool:
    """Best-effort exclusion, not a reliable password or secret detector."""
    return any(regex.search(text) for regex in SENSITIVE_PATTERNS)


def default_data_dir() -> Path:
    override = os.environ.get("CLIPMINT_WINDOWS_DATA_DIR")
    if override:
        return Path(override)
    root = os.environ.get("LOCALAPPDATA")
    if not root:
        root = str(Path.home() / "AppData" / "Local")
    return Path(root) / "ClipMintWindows"


class History:
    def __init__(self, db_path: Path | str | None = None):
        self.path = Path(db_path) if db_path else default_data_dir() / "history.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK(kind IN ('TEXT','IMAGE','FILES')),
                body TEXT NOT NULL DEFAULT '',
                image BLOB,
                digest TEXT NOT NULL,
                created_utc INTEGER NOT NULL,
                collection TEXT NOT NULL DEFAULT 'Work',
                pinned INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_clips_created ON clips(created_utc DESC);
            CREATE INDEX IF NOT EXISTS idx_clips_digest ON clips(digest);
        """)
        self.db.commit()

    def add(self, kind: str, body: str = "", image: bytes | None = None,
            collection: str = "Work") -> int | None:
        if collection not in {"Work", "Personal", "Temporary"}:
            raise ValueError("Invalid collection")
        if kind not in {"TEXT", "IMAGE", "FILES"}:
            raise ValueError("Unsupported clipboard item kind")
        if kind == "IMAGE":
            if not image or len(image) > MAX_IMAGE_BYTES:
                return None
            source = image
        else:
            if not body or len(body) > MAX_TEXT_CHARS or likely_sensitive(body):
                return None
            source = (kind + "\0" + body).encode("utf-8", "replace")
        digest = hashlib.sha256(source).hexdigest()
        prior = self.db.execute("SELECT id FROM clips WHERE digest=? AND collection=? LIMIT 1", (digest, collection)).fetchone()
        now = int(time.time())
        if prior:
            self.db.execute("UPDATE clips SET created_utc=? WHERE id=?", (now, prior["id"]))
            self.db.commit()
            return prior["id"]
        cur = self.db.execute(
            "INSERT INTO clips(kind,body,image,digest,created_utc,collection) VALUES (?,?,?,?,?,?)",
            (kind, body, image, digest, now, collection),
        )
        row_id = cur.lastrowid
        # Keep pinned items regardless of age. Remove unpinned items exceeding cap.
        self.db.execute("""
            DELETE FROM clips WHERE id IN (
                SELECT id FROM clips WHERE pinned=0
                ORDER BY created_utc DESC, id DESC LIMIT -1 OFFSET ?
            )
        """, (MAX_UNPINNED,))
        self.db.commit()
        return row_id

    def list(self, search: str = "", kind: str = "", limit: int = 250,
             collection: str = ""):
        conditions: list[str] = []
        args: list[object] = []
        if search:
            conditions.append("body LIKE ? ESCAPE '\\'")
            # Escape LIKE wildcards instead of interpreting search terms as patterns.
            literal = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            args.append("%" + literal + "%")
        if kind:
            if kind not in {"TEXT", "IMAGE", "FILES"}:
                raise ValueError("Unknown kind")
            conditions.append("kind=?")
            args.append(kind)
        if collection:
            if collection not in {"Work", "Personal", "Temporary"}:
                raise ValueError("Invalid collection")
            conditions.append("collection=?")
            args.append(collection)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        args.append(max(1, min(int(limit), 1000)))
        return self.db.execute(
            "SELECT id,kind,body,image,created_utc,pinned,collection FROM clips" + where +
            " ORDER BY pinned DESC, created_utc DESC, id DESC LIMIT ?", args,
        ).fetchall()

    def get(self, item_id: int):
        return self.db.execute("SELECT * FROM clips WHERE id=?", (item_id,)).fetchone()

    def set_pin(self, item_id: int, pinned: bool) -> None:
        with self.db:
            self.db.execute("UPDATE clips SET pinned=? WHERE id=?", (int(pinned), item_id))

    def delete(self, item_id: int) -> None:
        with self.db:
            self.db.execute("DELETE FROM clips WHERE id=?", (item_id,))

    def close(self):
        self.db.close()
