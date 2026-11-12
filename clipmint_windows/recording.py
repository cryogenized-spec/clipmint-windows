"""Optional, local Windows desktop-region FFmpeg recording (gdigrab)."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def gdigrab_args(ffmpeg: str, output: Path, x: int, y: int, width: int, height: int,
                 fps: int = 15) -> list[str]:
    if width < 32 or height < 32:
        raise ValueError("Recording region too small")
    if not 1 <= fps <= 60:
        raise ValueError("Invalid frame rate")
    # MP4/h264 requires even dimensions for yuv420p.
    width -= width % 2
    height -= height % 2
    return [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "gdigrab", "-framerate", str(fps),
        "-offset_x", str(x), "-offset_y", str(y),
        "-video_size", f"{width}x{height}", "-i", "desktop",
        "-an", "-c:v", "libx264", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", str(output),
    ]


class Recorder:
    def __init__(self):
        self.process: subprocess.Popen | None = None
        self.output: Path | None = None
        self._log = None

    def start(self, rect: tuple[int, int, int, int], folder: Path) -> Path:
        if self.process:
            raise RuntimeError("Already recording")
        ffmpeg = shutil.which("ffmpeg.exe") or shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("FFmpeg for Windows is not installed or not on PATH")
        folder.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix="recording-", suffix=".mp4", dir=folder)
        os.close(fd)
        self.output = Path(name)
        self._log = open(self.output.with_suffix(".log"), "wb")
        try:
            kwargs = {}
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            self.process = subprocess.Popen(
                gdigrab_args(ffmpeg, self.output, *rect), stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=self._log, **kwargs,
            )
        except Exception:
            self._log.close()
            self._log = None
            self.output.unlink(missing_ok=True)
            self.output = None
            raise
        return self.output

    def stop(self) -> Path:
        if not self.process:
            raise RuntimeError("No active recording")
        proc, output = self.process, self.output
        try:
            if proc.stdin and proc.poll() is None:
                try:
                    proc.stdin.write(b"q\n")
                    proc.stdin.flush()
                except OSError:
                    pass
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=4)
            if proc.returncode != 0 or not output or output.stat().st_size == 0:
                raise RuntimeError("FFmpeg failed to produce a valid recording; inspect its local log")
            return output
        finally:
            self.process = None
            self.output = None
            if self._log:
                self._log.close()
                self._log = None

    def abort(self):
        if not self.process:
            return
        proc = self.process
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
        self.process = None
        self.output = None
        if self._log:
            self._log.close()
            self._log = None
