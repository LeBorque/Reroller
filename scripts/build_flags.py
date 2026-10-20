# Python 3.14 | scripts/build_flags.py | SVG language icons for Tkinter
from io import BytesIO
from pathlib import Path

from PIL import Image
from resvg_py import svg_to_bytes


def build_flags():
    assets = Path(__file__).resolve().parent.parent / "assets"
    for country, width in (("se", 32), ("us", 38)):
        rendered = svg_to_bytes(svg_path=str(assets / f"{country}.svg"), width=width * 4)
        with Image.open(BytesIO(rendered)) as source:
            artwork = source.convert("RGBA").resize((width, 20), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (38, 24))
        canvas.alpha_composite(artwork, ((38 - width) // 2, 2))
        destination = assets / f"flag_{country}.png"
        canvas.save(destination)
        print(destination)


if __name__ == "__main__":
    build_flags()
