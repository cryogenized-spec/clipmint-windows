# ClipMint — Windows x64 (independent alpha)

A **standalone** Windows port prototype of ClipMint, with a separate directory, Windows-specific data storage, CI workflow, assets and release identity. It does **not** install to or modify the ClipMint Linux application. It is based on the approved ClipMint Crimson Archive visual palette, not a copy of the Linux runtime.

**Status: developer alpha / not a public release.** The code has platform-neutral unit tests, but the complete GUI, Win32 global hotkey, FFmpeg recording, multi-monitor capture and portable EXE still require real Windows x64 acceptance testing. No digitally signed installer is supplied.

## Working in this alpha

- Gothic, gold, crimson and Japanese-captioned native PySide6/Qt interface.
- Clipboard monitoring while the process is active, with TEXT, IMAGE and local FILES support.
- Three isolated collections: Work, Personal and Temporary; search, deduplication, preview, pin, delete and copy.
- Local SQLite history in `%LOCALAPPDATA%\ClipMintWindows\history.sqlite3`, **plaintext by default**. No Linux database migration or shared configuration.
- User-controlled monitoring checkbox, best-effort exclusion of obvious password/private-key strings (not a security boundary).
- Single-monitor rectangle selection for screenshots, saved under `ClipMintWindows\Screenshots` and also archived in SQLite if within the 10 MB image cap.
- Optional Windows MP4 region recording using a **user-installed FFmpeg for Windows**, `gdigrab` and `libx264`. No FFmpeg is downloaded silently or shipped.
- Optional global `Ctrl+Shift+S` screenshot shortcut using Win32 `RegisterHotKey`, if the combination is free. No keyboard hooks or code injection.
- Local drag-copy of supported text, image data and file references. Drop targets vary; screenshots are not yet turned into temporary CF_HDROP upload files.
- Optional system tray. An explicit Quit ends monitoring.

## Requirements

Windows 11 x64 is the initial target; Windows 10 x64 is **not yet verified**. Python 3.12 x64 is used when building from source, with PySide6 and PyInstaller. To record, you must install a trustworthy Windows FFmpeg build yourself and put its `ffmpeg.exe` on your PATH. Recording is optional; other features do not require FFmpeg.

## Run directly (developer environment)

Open PowerShell in this Windows edition's directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py
```

## Build a portable Windows x64 application

```powershell
.\build-windows.ps1
```

A successful build produces `artifacts\ClipMint-Windows-x64-alpha.zip`. Extract the ZIP and run `ClipMint-Windows.exe` inside it. The `.exe` is **unsigned**. Only execute binaries you trust, and check the produced SHA-256 value. No elevated permissions are required by the application itself.

Alternatively, initialize this directory as its **own new GitHub repository** (suggested name `cryogenized-spec/clipmint-windows`) and push the files. Its independent `.github/workflows/windows-x64.yml` builds on GitHub's `windows-2025` runner and uploads a downloadable CI artifact. The workflow does **not** create public releases or change `clipmint-linux`.

## Known limitations / privacy

- Best-effort credential filtering does **not** detect all secrets. Do not rely on ClipMint as a password manager. Pause monitoring before working with sensitive information.
- Clipboard history is **plaintext** on disk; it is not encrypted or isolated from other processes running as your Windows user. The experimental Linux vault and encrypted-history options are **not yet ported**.
- Captures are single-monitor initially. Mixed-DPI multi-monitor coordinate translation, desktop permission prompts, GPU capture and Win32 drag/drop need physical-machine verification.
- No Windows update service, automatic startup, code signing, MSIX/installer, or automatic network access.
- Unverified third-party Crimson/Kohaku illustration assets from the Linux edition have intentionally **not** been bundled. The approved ClipMint logo/icon is included; a character artwork panel can be restored later after confirming artwork redistribution rights.
- Windows edition is currently a feature-focused alpha, **not yet complete feature parity** with Linux ClipMint. Recording works only if an appropriate FFmpeg binary and H.264 encoder are separately available.

## Separate code and licensing

This Windows edition is an independent source tree, designed to be maintained as its own repository and to ship separate packages. New code is designated `AGPL-3.0-only`, consistent with the main ClipMint source project. Preserve attribution and review any reused artwork or third-party components before public redistribution. The full GNU AGPL-3.0-only license text is included in `LICENSE`; do not treat the separate project artwork as automatically licensed under it.