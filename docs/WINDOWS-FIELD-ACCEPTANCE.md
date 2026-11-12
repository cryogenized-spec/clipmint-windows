# ClipMint Windows x64 — physical acceptance test

Use a spare Windows 11 x64 user profile. Treat this prototype as **unsigned experimental software**. Avoid using real passwords, sensitive clipboard contents, customer files or private recordings during tests.

1. Verify ZIP SHA-256, extract to a disposable directory and launch the `.exe` without administrator privileges. Check titlebar/taskbar icon and the approved ClipMint emblem.
2. Copy ordinary Unicode text, a URL, an image and a local test file; confirm the expected record type is created once and that the preview is correct.
3. Test Work/Personal/Temporary isolation, literal search with `%` and `_`, pin/unpin, delete and persistence after Quit/restart.
4. Pause monitoring, copy synthetic test content, resume monitoring and confirm content copied while paused is **not** backfilled.
5. Copy a synthetic string `password: test1234` and confirm it is not stored. Note that the filter is incomplete by design.
6. Restore an archived TEXT or IMAGE to the clipboard and paste into Notepad or Paint; check that the archive does not create a duplicate entry from its own copy.
7. Copy a local file reference and test dragging it into a file-aware target. Test link/text drag into an editable field. Drag an archived IMAGE directly onto a Firefox/Chromium `<input type=file>` and verify it appears as a PNG upload, *without* using the File Open dialog. Confirm unrelated files were not exported. On normal Quit confirm this session's temporary drag PNG is gone; after a crash, inspect the user TEMP directory for leftover `ClipMintWindows-drag-` folders. Record target compatibility rather than assuming universal support.
8. Press `Ctrl+Shift+S` while the app is minimized. Make a synthetic region screenshot, press Esc to cancel another attempt, and confirm the file is saved locally without bringing up an extra window.
9. With a separately installed `ffmpeg.exe` supporting `gdigrab` and `libx264`, record a short rectangle; stop it, play the MP4, and check no FFmpeg process remains.
10. If multiple monitors use different DPI scale factors, document the monitor arrangement and compare selected boundaries with the captured pixels. Mark mixed-DPI unreliable until individually fixed.
11. Test the system tray: close-to-tray retains monitoring; explicit Quit terminates monitoring and the process. Relaunch and verify local history survives.
12. Confirm the Linux Mint ClipMint installation and data are unchanged. There must be no Linux database path or updater shared with Windows.

Record the exact Windows edition Git commit, SHA-256 of the built ZIP, Windows version, test operator, and pass/fail for each item before promoting beyond alpha.
