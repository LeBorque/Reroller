# Python 3.14 | scripts/build_icon.py | Windows application icon packaging
from pathlib import Path

from PIL import Image, ImageOps


def build_icon():
    assets = Path(__file__).resolve().parent.parent / "assets"
    with Image.open(assets / "reroller_icon.png") as source:
        artwork = ImageOps.contain(source.convert("RGBA"), (256, 256), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (256, 256))
    canvas.alpha_composite(artwork, ((256 - artwork.width) // 2, (256 - artwork.height) // 2))
    destination = assets / "reroller_icon.ico"
    canvas.save(destination, format="ICO", sizes=[(size, size) for size in (16, 20, 24, 32, 40, 48, 64, 128, 256)])
    print(destination)


if __name__ == "__main__":
    build_icon()
