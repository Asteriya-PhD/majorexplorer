#!/usr/bin/env python3
"""为微信公众号封面图添加标题文字"""
from PIL import Image, ImageDraw, ImageFont
import os

BASE = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(BASE, "assets/A_warm__intimate_night_scene___2026-06-27T08-46-07.png")
OUTPUT = os.path.join(BASE, "assets/2026-06-27_cover_final.png")

# --- config ---
TARGET_W, TARGET_H = 900, 383

LINE1 = "出分夜，写给睡不着的高三家长"
LINE2 = ""

# --- load & resize ---
img = Image.open(INPUT).convert("RGB")
img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)
draw = ImageDraw.Draw(img)

# --- try to load a nice Chinese font ---
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]

font_path = None
for fp in FONT_CANDIDATES:
    if os.path.exists(fp):
        font_path = fp
        break

if font_path is None:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()
else:
    font_title = ImageFont.truetype(font_path, 36)
    font_sub = ImageFont.truetype(font_path, 24)

# --- measure text for dark overlay ---
bbox1 = draw.textbbox((0, 0), LINE1, font=font_title)
bbox2 = draw.textbbox((0, 0), LINE2, font=font_sub)
tw1, th1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]
tw2, th2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]

padding_top = 28
gap = 10
pad_x = 24
overlay_y1 = padding_top - 6
overlay_y2 = padding_top + th1 + gap + th2 + 6

# --- semi-transparent dark overlay for readability ---
overlay = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)
# Top gradient bar
for i in range(overlay_y2 - overlay_y1):
    alpha = max(0, 140 - int(i * 140 / (overlay_y2 - overlay_y1 + 1)))
    overlay_draw.line(
        [(0, overlay_y1 + i), (TARGET_W, overlay_y1 + i)],
        fill=(10, 10, 18, alpha)
    )
# Extra darker band right behind text
overlay_draw.rectangle(
    [(0, overlay_y1), (TARGET_W, overlay_y2)],
    fill=(8, 8, 16, 120)
)

img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

# --- draw text ---
x1 = (TARGET_W - tw1) / 2
y1 = padding_top

# Line 1 with slight shadow
shadow_color = (0, 0, 0)
text_color = (255, 255, 252)
for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
    draw.text((x1 + dx, y1 + dy), LINE1, font=font_title, fill=shadow_color)
draw.text((x1, y1), LINE1, font=font_title, fill=text_color)

# Line 2
x2 = (TARGET_W - tw2) / 2
y2 = y1 + th1 + gap
for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
    draw.text((x2 + dx, y2 + dy), LINE2, font=font_sub, fill=shadow_color)
draw.text((x2, y2), LINE2, font=font_sub, fill=text_color)

# --- "图片由AI生成" bottom-right watermark ---
watermark = "图片由AI生成"
font_wm = ImageFont.truetype(font_path, 10) if font_path else ImageFont.load_default()
bbox_wm = draw.textbbox((0, 0), watermark, font=font_wm)
wm_w = bbox_wm[2] - bbox_wm[0]
wm_h = bbox_wm[3] - bbox_wm[1]
wm_x = TARGET_W - wm_w - 10
wm_y = TARGET_H - wm_h - 8
# very light semi-transparent bg
wm_overlay = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
wm_od = ImageDraw.Draw(wm_overlay)
wm_od.rectangle(
    [(wm_x - 3, wm_y - 1), (wm_x + wm_w + 3, wm_y + wm_h + 1)],
    fill=(0, 0, 0, 55)
)
img = Image.alpha_composite(img.convert("RGBA"), wm_overlay).convert("RGB")
draw = ImageDraw.Draw(img)
draw.text((wm_x, wm_y), watermark, font=font_wm, fill=(160, 160, 160, 120))

# --- save ---
img.save(OUTPUT, "PNG", optimize=True)
print(f"✅ Saved: {OUTPUT}")
print(f"   Size: {img.size}")
