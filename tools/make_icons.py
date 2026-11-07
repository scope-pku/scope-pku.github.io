#!/usr/bin/env python3
"""Regenerate the site icon set from a single square source PNG.

Usage:
    uv run --with pillow --with numpy tools/make_icons.py ~/path/to/icon.png

Writes into site/static/: favicon.ico (16/32/48), favicon-32.png, icon-192.png,
icon-512.png, icon-192-maskable.png, icon-512-maskable.png, apple-touch-icon.png
(opaque, iOS ignores transparency) and og-image.png (1200x630 share card).

Maskable icons get a full-bleed tile-coloured background with the mark inset to
the 80% safe zone, so Android's circle/squircle masks never clip the artwork.

The source may be either a tile on a plain white background or an already
transparent mark; both are detected automatically. White is removed by
flood-filling from the border, so interior white artwork (for example the dashed
line in the mark) survives, and the 1-3px ring around the removed area is
un-blended against the tile colour so rounded corners keep their anti-aliasing
instead of a white halo. Either way the artwork is then cropped to its visible
bounds and re-centred on a square canvas, so an off-centre export still produces
a centred icon set.
"""

from collections import Counter, deque
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "static"

CREAM = (253, 243, 233)
INK = (23, 32, 42)
MUTED = (70, 81, 92)
ACCENT = (140, 0, 0)
EYEBROW = (138, 127, 116)

FONT_DIR = Path("/usr/share/fonts/truetype/lato")
LATO_MEDIUM = FONT_DIR / "Lato-Medium.ttf"
LATO_BLACK = FONT_DIR / "Lato-Black.ttf"
LATO_REGULAR = FONT_DIR / "Lato-Regular.ttf"

WHITE_TOL = 14
SOFT_RADIUS = 3
LINE_RESIDUAL = 10


def cut_background(src: Path) -> Image.Image:
    rgb = Image.open(src).convert("RGB")
    w, h = rgb.size
    if w != h:
        raise SystemExit(f"source must be square, got {w}x{h}")

    arr = np.asarray(rgb).astype(np.float64)
    white = np.array([254.0, 254.0, 254.0])
    tile = np.array(list(Counter(rgb.getdata()).most_common(3)[1][0]), dtype=np.float64)
    direction = tile - white

    def near_white(px: tuple[int, int, int]) -> bool:
        return min(px) >= 255 - WHITE_TOL

    outside = np.zeros((h, w), dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    border = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
    border += [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    for x, y in border:
        if near_white(rgb.getpixel((x, y))) and not outside[y, x]:
            outside[y, x] = True
            queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not outside[ny, nx] and near_white(rgb.getpixel((nx, ny))):
                outside[ny, nx] = True
                queue.append((nx, ny))

    ring = np.zeros((h, w), dtype=bool)
    for dy in range(-SOFT_RADIUS, SOFT_RADIUS + 1):
        for dx in range(-SOFT_RADIUS, SOFT_RADIUS + 1):
            ring |= np.roll(np.roll(outside, dy, 0), dx, 1)
    ring &= ~outside

    along = np.tensordot(arr - white, direction, axes=([2], [0])) / np.dot(direction, direction)
    projected = white + np.clip(along, 0, 1)[..., None] * direction
    residual = np.linalg.norm(arr - projected, axis=2)
    soft = ring & (residual < LINE_RESIDUAL)

    alpha = np.full((h, w), 255.0)
    alpha[outside] = 0.0
    alpha[soft] = np.clip(along[soft], 0, 1) * 255.0

    colour = np.where(outside[..., None], tile, arr)
    return Image.fromarray(np.dstack([colour, alpha]).astype(np.uint8), "RGBA")


MARK_MARGIN = 0.06
MASKABLE_SAFE_ZONE = 0.78


def normalise(mark: Image.Image, margin: float = MARK_MARGIN) -> Image.Image:
    """Crop to the visible artwork and centre it on a transparent square canvas."""
    bounds = mark.getchannel("A").getbbox()
    if bounds is None:
        raise SystemExit("source has no visible pixels")
    mark = mark.crop(bounds)
    side = round(max(mark.size) * (1 + 2 * margin))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(mark, ((side - mark.width) // 2, (side - mark.height) // 2), mark)
    return canvas


def load_source(src: Path, margin: float = MARK_MARGIN) -> Image.Image:
    probe = Image.open(src).convert("RGBA")
    w, h = probe.size
    corners = [probe.getpixel(p)[3] for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    mark = probe if min(corners) == 0 else cut_background(src)
    return normalise(mark, margin)


def build_maskable(icon: Image.Image, size: int) -> Image.Image:
    card = Image.new("RGB", (size, size), CREAM)
    inner = round(size * MASKABLE_SAFE_ZONE)
    offset = (size - inner) // 2
    mark = icon.resize((inner, inner), Image.LANCZOS)
    card.paste(mark, (offset, offset), mark)
    return card


def build_share_card(icon: Image.Image) -> Image.Image:
    card = Image.new("RGB", (1200, 630), CREAM)
    draw = ImageDraw.Draw(card)
    draw.rectangle([0, 0, 1200, 8], fill=ACCENT)

    mark = icon.resize((300, 300), Image.LANCZOS)
    card.paste(mark, (90, 175), mark)

    eyebrow = ImageFont.truetype(str(LATO_MEDIUM), 22)
    title = ImageFont.truetype(str(LATO_BLACK), 78)
    subtitle = ImageFont.truetype(str(LATO_REGULAR), 31)
    small = ImageFont.truetype(str(LATO_MEDIUM), 22)

    x = 440
    draw.text((x, 168), "PEKING UNIVERSITY  \u00b7  SCHOOL OF PHYSICS", font=eyebrow, fill=EYEBROW)
    draw.text((x, 205), "SCOPE Group", font=title, fill=INK)
    y = 310
    for line in ("Simulation of Condensed-Matter Order", "and Phase Evolution"):
        draw.text((x, y), line, font=subtitle, fill=MUTED)
        y += 42
    draw.rectangle([x, y + 18, x + 72, y + 21], fill=ACCENT)
    draw.text((x, y + 50), "lmxu.cc", font=small, fill=EYEBROW)
    return card


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    source = Path(sys.argv[1]).expanduser()
    icon = load_source(source)
    OUT.mkdir(parents=True, exist_ok=True)

    # Small sizes get less breathing room: a glyph-only mark with the same
    # margin as the 512px icon reads as a smudge in a browser tab.
    small_icon = load_source(source, margin=0.01)
    small_icon.resize((32, 32), Image.LANCZOS).save(OUT / "favicon-32.png")
    sixteen = small_icon.resize((16, 16), Image.LANCZOS)
    forty_eight = small_icon.resize((48, 48), Image.LANCZOS)
    thirty_two = Image.open(OUT / "favicon-32.png")
    thirty_two.save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=[sixteen, forty_eight])
    icon.resize((192, 192), Image.LANCZOS).save(OUT / "icon-192.png")
    icon.resize((512, 512), Image.LANCZOS).save(OUT / "icon-512.png")
    build_maskable(icon, 192).save(OUT / "icon-192-maskable.png")
    build_maskable(icon, 512).save(OUT / "icon-512-maskable.png")

    touch = Image.new("RGB", (180, 180), CREAM)
    scaled = icon.resize((180, 180), Image.LANCZOS)
    touch.paste(scaled, (0, 0), scaled)
    touch.save(OUT / "apple-touch-icon.png")

    build_share_card(icon).save(OUT / "og-image.png")
    print("wrote", ", ".join(sorted(p.name for p in OUT.glob("*icon*")) + ["favicon.ico", "favicon-32.png", "og-image.png"]))


if __name__ == "__main__":
    main()
