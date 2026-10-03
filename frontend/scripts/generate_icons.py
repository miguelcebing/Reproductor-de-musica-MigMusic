"""Generate the PWA icons for MigMusic (favicon, 192/512, maskable, Apple).

Run from the `frontend/` directory with Pillow installed:

    python scripts/generate_icons.py

The script is committed so the icons can be regenerated without design tools;
the produced PNGs under `public/icons/` are the artefacts the app ships.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

BACKGROUND = (10, 13, 20)  # #0A0D14 (tokens.css dark surface)
ACCENT = (168, 85, 247)  # #A855F7 (nebula violet)
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "public" / "icons"

MASTER = 1024


def _draw_note(draw: ImageDraw.ImageDraw, scale: float, offset: tuple[int, int]) -> None:
    """Draw a single music note (head, stem, flag) scaled onto the canvas."""
    ox, oy = offset

    def point(x: float, y: float) -> tuple[float, float]:
        return (ox + x * scale, oy + y * scale)

    # Note head: a slightly wide ellipse in the lower-left area.
    draw.ellipse(
        [point(300, 620), point(520, 810)],
        fill=ACCENT,
    )
    # Stem: vertical bar rising from the head's right side.
    draw.rectangle([point(490, 240), point(530, 700)], fill=ACCENT)
    # Flag: a small filled triangle leaning right from the stem top.
    draw.polygon([point(530, 240), point(700, 300), point(530, 400)], fill=ACCENT)


def _master_icon(padding_ratio: float) -> Image.Image:
    """Render the master icon; `padding_ratio` shrinks the note for maskable safe zones."""
    image = Image.new("RGBA", (MASTER, MASTER), BACKGROUND + (255,))
    draw = ImageDraw.Draw(image)
    scale = 1.0 - padding_ratio
    offset = int(MASTER * padding_ratio / 2)
    _draw_note(draw, scale, (offset, offset))
    return image


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    standard = _master_icon(padding_ratio=0.0)
    standard.resize((192, 192), Image.LANCZOS).save(OUTPUT_DIR / "icon-192.png")
    standard.resize((512, 512), Image.LANCZOS).save(OUTPUT_DIR / "icon-512.png")
    standard.resize((180, 180), Image.LANCZOS).save(OUTPUT_DIR / "apple-touch-icon.png")

    # Maskable icons need the glyph inside the inner ~80% safe zone.
    maskable = _master_icon(padding_ratio=0.28)
    maskable.resize((512, 512), Image.LANCZOS).save(OUTPUT_DIR / "maskable-512.png")

    for icon in sorted(OUTPUT_DIR.glob("*.png")):
        print(f"wrote {icon.relative_to(OUTPUT_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
