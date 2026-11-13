"""Acquire a pinned, integrity-verified FFmpeg Windows x64 binary at BUILD time.

No ClipMint runtime download. The resulting portable package includes ffmpeg.exe.
Gyan Doshi's Windows release essentials 9.0.2 contains gdigrab and libx264.
This script intentionally extracts only one executable from the upstream ZIP.
Build fails closed on checksum mismatch or missing codec/device.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.request import Request, urlopen
from zipfile import ZipFile, BadZipFile

VERSION = "9.0.2"
URL = "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip"
SHA256 = "60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba"
GPL_SOURCE_URL = "https://raw.githubusercontent.com/FFmpeg/FFmpeg/n9.0.2/COPYING.GPLv3"
MAX_DOWNLOAD = 150 * 1024 * 1024


def download_verified(url: str, digest: str, destination: Path) -> None:
    digest = digest.lower()
    sha = hashlib.sha256()
    total = 0
    req = Request(url, headers={"User-Agent": "ClipMint-Windows-build/0.1"})
    with urlopen(req, timeout=90) as response, destination.open("wb") as out:
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_DOWNLOAD:
                raise ValueError("Unexpectedly large FFmpeg archive")
            out.write(chunk)
            sha.update(chunk)
    if sha.hexdigest() != digest:
        destination.unlink(missing_ok=True)
        raise ValueError("FFmpeg archive SHA-256 mismatch; packaging refused")


def unpack_ffmpeg(archive: Path, destination: Path) -> None:
    with ZipFile(archive) as z:
        matches = [
            item for item in z.infolist()
            if item.filename.replace("\\", "/").lower().endswith("/bin/ffmpeg.exe")
            and not item.is_dir()
        ]
        if len(matches) != 1 or not 10_000_000 < matches[0].file_size < 300_000_000:
            raise ValueError("Unrecognized FFmpeg essentials ZIP layout")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with z.open(matches[0], "r") as src, destination.open("wb") as out:
            shutil.copyfileobj(src, out)
    if destination.stat().st_size < 10_000_000:
        raise ValueError("FFmpeg executable was not extracted")


def fetch_gpl_text(destination: Path) -> None:
    req = Request(GPL_SOURCE_URL, headers={"User-Agent": "ClipMint-Windows-build/0.1"})
    with urlopen(req, timeout=30) as res:
        data = res.read(200_000)
    if not 20_000 < len(data) < 200_000 or b"GNU GENERAL PUBLIC LICENSE" not in data:
        raise ValueError("Could not verify FFmpeg GPLv3 text")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    target = root / "vendor" / "ffmpeg.exe"
    license_path = root / "vendor" / "licenses" / "FFmpeg-GPLv3.txt"
    with tempfile.TemporaryDirectory(prefix="clipmint-ffmpeg-build-") as tmp:
        archive = Path(tmp) / "ffmpeg-essentials.zip"
        download_verified(URL, SHA256, archive)
        unpack_ffmpeg(archive, target)
    fetch_gpl_text(license_path)
    output = subprocess.run([str(target), "-hide_banner", "-encoders"],
                            capture_output=True, text=True, check=True, timeout=30)
    if "libx264" not in output.stdout:
        raise RuntimeError("Bundled FFmpeg lacks required libx264 encoder")
    devices = subprocess.run([str(target), "-hide_banner", "-devices"],
                             capture_output=True, text=True, check=True, timeout=30)
    if "gdigrab" not in devices.stdout:
        raise RuntimeError("Bundled FFmpeg lacks required gdigrab input")
    print(f"Verified FFmpeg {VERSION}, gdigrab and libx264; bundled for Windows x64")


if __name__ == "__main__":
    main()
