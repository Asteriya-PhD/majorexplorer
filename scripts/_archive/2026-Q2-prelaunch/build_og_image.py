#!/usr/bin/env python3
"""
build_og_image.py — Generate the default OG (Open Graph) image for Major Explorer.

Output: assets/og-default.png  (1200x630, the standard OG dimension)

Design:
  - Deep navy background (#0F1B2D) with cream text (#FAEFD8) and a warm gold
    accent (#E8C547) — matches the project's existing CS / academic palette.
  - Centered title "Major Explorer" in Bodoni-style serif (fallback to default
    serif if unavailable).
  - Chinese subtitle "高考专业方向调研" in PingFang.
  - Smaller tagline "60 个专业 · 1 个网站 · 选对方向".
  - A small typographic rule + corner stamp for visual interest.

Run:
    python3 scripts/build_og_image.py
    python3 scripts/build_og_image.py --out assets/og-default.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS = REPO_ROOT / "assets"

# Standard OG dimensions.
W, H = 1200, 630

# Palette — matches Major Explorer CS / academic theme.
BG = (15, 27, 45)        # deep navy
CREAM = (250, 239, 216)  # warm cream
GOLD = (232, 197, 71)    # warm gold accent
MUTED = (172, 168, 154)  # muted cream/grey for fine print

# Font paths — macOS system fonts that ship with Chinese support.
FONT_DIRS = [
    Path("/System/Library/Fonts/Supplemental"),
    Path("/System/Library/Fonts"),
    Path("/Library/Fonts"),
    Path("/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData"),
]


def find_font(filename_substr: str) -> Path | None:
    for d in FONT_DIRS:
        if not d.is_dir():
            continue
        for p in d.rglob("*"):
            if p.is_file() and filename_substr.lower() in p.name.lower():
                return p
    return None


def load_font(path: Path | None, size: int) -> ImageFont.FreeTypeFont:
    if path and path.exists():
        try:
            return ImageFont.truetype(str(path), size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def draw_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    image_w: int = W,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (image_w - tw) // 2 - bbox[0]
    draw.text((x, y), text, font=font, fill=fill)


def render(out_path: Path) -> None:
    img = Image.new("RGB", (W, H), color=BG)
    draw = ImageDraw.Draw(img)

    # ----- decorative geometry -----
    # Top-left rule (gold, thin).
    draw.rectangle([(80, 80), (320, 84)], fill=GOLD)
    # Bottom-right rule (gold, thin).
    draw.rectangle([(W - 320, H - 84), (W - 80, H - 80)], fill=GOLD)

    # Top-left small stamp text.
    stamp_font = load_font(find_font("PingFang"), 22)
    draw.text((80, 100), "MAJOR · EXPLORER", font=stamp_font, fill=GOLD)

    # Bottom-right small caption.
    caption_font = load_font(find_font("PingFang"), 22)
    cap = "gaokao · hubei · 2026"
    bbox = draw.textbbox((0, 0), cap, font=caption_font)
    cw = bbox[2] - bbox[0]
    draw.text((W - 80 - cw, H - 110), cap, font=caption_font, fill=MUTED)

    # ----- main title -----
    # Prefer a serif feel (Bodoni), fall back to Times.
    title_font = load_font(
        find_font("Bodoni") or find_font("Times") or find_font("STHeiti"),
        124,
    )
    title = "Major Explorer"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    th = bbox[3] - bbox[1]
    draw_centered(draw, title, y=(H // 2) - th - 30, font=title_font, fill=CREAM)

    # ----- chinese subtitle -----
    cn_font = load_font(find_font("PingFang"), 60)
    subtitle = "高考专业方向调研"
    bbox = draw.textbbox((0, 0), subtitle, font=cn_font)
    sh = bbox[3] - bbox[1]
    draw_centered(draw, subtitle, y=(H // 2) + 30, font=cn_font, fill=CREAM)

    # ----- tagline -----
    tag_font = load_font(find_font("PingFang"), 30)
    tag = "60 个专业 · 1 个网站 · 选对方向"
    bbox = draw.textbbox((0, 0), tag, font=tag_font)
    tg = bbox[3] - bbox[1]
    draw_centered(draw, tag, y=(H // 2) + 30 + sh + 40, font=tag_font, fill=GOLD)

    # ----- save -----
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    print(f"Wrote {out_path} ({W}x{H}, {(out_path.stat().st_size / 1024):.1f} KB)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build og-default.png")
    parser.add_argument(
        "--out",
        default=str(ASSETS / "og-default.png"),
        help="Output path (default: <repo>/assets/og-default.png).",
    )
    args = parser.parse_args()
    render(Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
