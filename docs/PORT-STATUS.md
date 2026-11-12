# Windows x64 port — engineering status, 12 Nov 2026

**Edition:** `ClipMint-Windows` (standalone, separate from `clipmint-linux`).
**Source revision:** alpha prototype `0.1.0a1`.
**Build format:** PyInstaller `--onedir` portable x64 ZIP; not an installer.
**Release approval:** NOT APPROVED. This ZIP contains source code and build instructions, not a Windows executable.

## Completed in the separate Windows source tree

- [x] Approved crimson/gold ClipMint icon included as Windows `.ico` and `.png`.
- [x] Native Qt UI in the original gothic crimson/rose/gold palette; Japanese labels.
- [x] Windows-only data path; no cross-read or migration of the Linux database.
- [x] SQLite history, literal search, image/text/file captures, collections, pinned items and item preview.
- [x] User-toggleable monitoring, best-effort sensitive-content filtering and no network telemetry.
- [x] Region screenshot selector using Qt `QScreen.grabWindow`.
- [x] Optional FFmpeg `gdigrab` adapter for MP4 region recording.
- [x] Experimental Win32 `RegisterHotKey` path without keyboard interception.
- [x] Dedicated Windows PowerShell build script and GitHub Actions Windows x64 workflow.
- [x] Unit tests for history, collections, privacy exclusions, isolation and recording command construction.

## Verification evidence

- [x] Python files compile via `compileall` in Linux development environment.
- [x] 14 platform-independent unit tests pass in Linux development environment.
- [ ] Qt UI self-test **on Windows** (PySide6 unavailable in current working environment).
- [ ] PyInstaller frozen `.exe` smoke test **on Windows**.
- [ ] Actual Windows 11 desktop clipboard, multi-process copy/paste and tray test.
- [ ] Actual Windows screen capture / mixed DPI / multi-monitor test.
- [ ] Actual Windows FFmpeg MP4 video sample playback test.
- [ ] Desktop icon/dock display and drag/drop into Firefox upload targets.
- [ ] Independent reviewer check on local SQLite privacy, shortcuts, and licensing.

## Milestones

**W0 — Source and packaging scaffold:** implemented. Package exists as `ClipMint-Windows-x64-source-alpha.zip`. Build workflow only runs after this source is pushed to its own GitHub repository.

**W1 — CI-built portable Windows executable:** pending (private Windows GitHub repository creation, GitHub runner execution and artifact verification). Running `build-windows.ps1` locally on Windows x64 is an alternative.

**W2 — Field acceptance and feature parity:** pending (reliability of clipboard ownership, drag into native applications, screen selection, DPI scaling, FFmpeg recording, startup and safe Quit). No claim of full Linux parity yet.

**W3 — Public Windows beta:** pending (complete AGPL license text, artifact rights, Win32 validation, code signing or clear unsigned warnings, installation/updating policy and user approval).

## Separation contract

- Do not edit `cryogenized-spec/clipmint-linux` when developing the Windows edition.
- Keep Windows code in a separate `clipmint-windows` repository and use its own CI artifacts/releases.
- Store Windows history only under `%LOCALAPPDATA%\ClipMintWindows`.
- Do not import Linux `X11`, `xdotool`, Cinnamon binding files, or `clipmint` Linux package.
- Port shared improvements deliberately via review rather than implicitly syncing production data or OS-specific modules.
