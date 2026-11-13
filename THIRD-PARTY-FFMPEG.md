# Bundled FFmpeg — Windows x64

ClipMint Windows portable alpha includes an independently built FFmpeg executable
for local screen recording. The user does **not** need a separate FFmpeg
installation or network connection to record video.

- Version: **FFmpeg 9.0.2**, Windows x64, static Essentials build by Gyan Doshi.
- Origin: https://www.gyan.dev/ffmpeg/builds/
- Exact upstream build archive:
  https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip
- Archive SHA-256 (checked by the **build workflow** before extraction):
  `60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba`
- FFmpeg corresponding source: https://github.com/FFmpeg/FFmpeg/tree/n9.0.2
- Upstream source commit reference: https://github.com/FFmpeg/FFmpeg/commit/946fcce07b
- Distribution/build information: https://www.gyan.dev/ffmpeg/builds/
- FFmpeg build configuration and enabled external libraries: inspect the included binary with `ffmpeg.exe -buildconf`.
- License: FFmpeg build is **GNU GPL version 3** (includes `libx264`). A copy of the GPLv3 text is shipped in `FFmpeg-GPLv3.txt` with the portable application.
- FFmpeg and ClipMint are **separate executable programs**. ClipMint launches FFmpeg as an external process. ClipMint's Python application is AGPL-3.0-only; FFmpeg retains its own licensing and third-party notices.

No FFmpeg executable is checked into the source repository. The independent
Windows GitHub Actions workflow downloads the fixed archive **during the build**,
verifies its SHA-256 hash, extracts only `ffmpeg.exe`, validates `gdigrab`
and `libx264`, and places that binary inside the frozen application package.

The GPL requires appropriate corresponding-source access when redistributing
binaries. Before any *general-public release*, verify that the hosted FFmpeg
source and its build scripts satisfy the distribution obligations, or publish the
required corresponding source alongside the binary. This build is a developer
alpha, not a signed or legally reviewed public release.

The approved ClipMint logo is separate artwork. The Linux-only Crimson/Kohaku
character illustrations have **not** been included in the Windows edition.
