"""Build a multi-size Windows icon from the approved ClipMint project mark.

This runs at packaging time only; Pillow is not required by end users.
"""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parent.parent
source = root / "assets" / "ClipMint.png"
target = root / "assets" / "ClipMint.ico"
with Image.open(source) as image:
    rgba = image.convert("RGBA")
    rgba.save(target, format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(96,96)])
print(f"Built Windows icon: {target}")
