"""Render the README images, drawn to scale from font5x7.py and the box dimensions.

  docs/marquee.png  one row of signs spelling WORD (default MARQUEE)
  docs/font.png     every glyph (A-Z, 0-9, dash, colon), nine signs per row

uv run --python 3.12 --with pillow cad/render_banner.py [WORD]
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from font5x7 import COLS, GLYPHS, ROWS, bulbs_on  # noqa: E402

# same geometry as cad/marquee_matrix.py (mm)
PITCH, EDGE, GLOBE_D = 60.0, 48.0, 40.0
W, H = (COLS - 1) * PITCH + 2 * EDGE, (ROWS - 1) * PITCH + 2 * EDGE   # 336 x 456

S = 0.7            # px per mm
GAP = 40           # px between signs
MARGIN = 70        # px around the row
SIDE = 9           # px of wood visible below/right of each face

BG = (24, 26, 28)
ACRYLIC = (10, 10, 11)
WOOD = (110, 70, 38)
OFF = (40, 37, 33)
OFF_HI = (58, 53, 46)
ON_CORE = (255, 249, 232)
ON_RIM = (255, 196, 99)
GLOW = (255, 170, 60)


def render(word: str, per_row: int = 0) -> Image.Image:
    pw, ph = round(W * S), round(H * S)
    n = per_row or len(word)
    rows = -(-len(word) // n)
    size = (2 * MARGIN + n * pw + (n - 1) * GAP + SIDE, 2 * MARGIN + rows * ph + (rows - 1) * GAP + SIDE)
    base = Image.new("RGB", size, BG)
    glow = Image.new("RGB", size, (0, 0, 0))
    d, g = ImageDraw.Draw(base), ImageDraw.Draw(glow)
    r = GLOBE_D / 2 * S

    for k, ch in enumerate(word):
        x0, y0 = MARGIN + (k % n) * (pw + GAP), MARGIN + (k // n) * (ph + GAP)
        d.rectangle([x0 + SIDE, y0 + SIDE, x0 + pw + SIDE, y0 + ph + SIDE], fill=WOOD)
        d.rectangle([x0, y0, x0 + pw, y0 + ph], fill=ACRYLIC)
        lit = set(bulbs_on(ch))
        for i in range(COLS * ROWS):
            row, col = divmod(i, COLS)
            cx, cy = x0 + (EDGE + col * PITCH) * S, y0 + (EDGE + row * PITCH) * S
            box = [cx - r, cy - r, cx + r, cy + r]
            if i in lit:
                d.ellipse(box, fill=ON_RIM)
                d.ellipse([cx - r * 0.72, cy - r * 0.72, cx + r * 0.6, cy + r * 0.6], fill=ON_CORE)
                g.ellipse([cx - r * 1.5, cy - r * 1.5, cx + r * 1.5, cy + r * 1.5], fill=GLOW)
            else:
                d.ellipse(box, fill=OFF)
                d.ellipse([cx - r * 0.6, cy - r * 0.65, cx + r * 0.1, cy + r * 0.05], fill=OFF_HI)

    halo = glow.filter(ImageFilter.GaussianBlur(r * 1.1))
    halo = Image.eval(halo, lambda v: int(v * 0.75))
    return ImageChops.add(base, halo)


if __name__ == "__main__":
    word = (sys.argv[1] if len(sys.argv) > 1 else "MARQUEE").upper()
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    render(word).save(docs / "marquee.png", optimize=True)
    glyphs = "".join(c for c in GLYPHS if c != " ")
    render(glyphs, per_row=9).save(docs / "font.png", optimize=True)
    print(docs / "marquee.png", docs / "font.png")
