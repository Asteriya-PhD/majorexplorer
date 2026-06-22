#!/usr/bin/env python3
"""
render_og_cover.py — 生成公众号推文首页图 (横版 900x383, 2.35:1)

Output: public/wechat-cover.png
风格: 跟 og/cs.png 同色 (深蓝科技感), 适合公众号头条封面
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "public" / "wechat-cover.png"
W, H = 900, 383

FONTS = [
    Path("/System/Library/Fonts/Supplemental"),
    Path("/System/Library/Fonts"),
    Path("/Library/Fonts"),
]


def find_font(name: str) -> Path | None:
    for d in FONTS:
        if d.is_dir():
            for p in d.rglob("*"):
                if p.is_file() and name.lower() in p.name.lower():
                    return p
    return None


def font(name_substr: str, size: int) -> ImageFont.FreeTypeFont:
    p = find_font(name_substr)
    if p and p.exists():
        try:
            return ImageFont.truetype(str(p), size=size)
        except OSError:
            pass
    for fb in ["STHeiti Medium", "STHeiti", "Times"]:
        p = find_font(fb)
        if p and p.exists():
            try:
                return ImageFont.truetype(str(p), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def render():
    BG = (15, 18, 32)         # cs 主题深蓝
    TEXT = (240, 240, 245)
    ACCENT = (88, 166, 255)    # 蓝
    GOLD = (180, 130, 50)     # 古铜金

    img = Image.new("RGB", (W, H), color=BG)
    draw = ImageDraw.Draw(img)

    me_font = font("STHeiti", 22)
    vol_font = font("Times", 22)
    title_font = font("STHeiti Medium", 68)   # 主标题 (缩到 68pt 避免重叠)
    sub_font = font("STHeiti", 22)             # 副标题
    data_font = font("STHeiti Medium", 22)     # 数据
    label_font = font("STHeiti", 14)           # 标签

    # ── 顶部: 品牌 + 卷号 ──
    draw.text((40, 30), "M·E · MAJOR EXPLORER", font=me_font, fill=GOLD)
    vol_text = "VOL. 2026"
    vol_w = draw.textlength(vol_text, font=vol_font)
    draw.text((W - 40 - vol_w, 35), vol_text, font=vol_font, fill=GOLD)
    draw.rectangle([(40, 65), (W - 40, 67)], fill=GOLD)

    # ── 居中主标题 ──
    title = "看清专业, 再谈志愿"
    tw = draw.textlength(title, font=title_font)
    title_x = (W - tw) // 2
    title_y = 100
    draw.text((title_x, title_y), title, font=title_font, fill=TEXT)

    # ── 居中副标题 (2 行) ──
    sub1 = "让 18 岁高三生看清 70+ 主流本科专业"
    sub2 = "选对未来 4 年大学 + 30 年职业"
    for i, s in enumerate([sub1, sub2]):
        sw = draw.textlength(s, font=sub_font)
        draw.text(((W - sw) // 2, title_y + 95 + i * 32), s, font=sub_font, fill=ACCENT if i == 0 else TEXT)

    # ── 底部: 域名 + 公益 (固定位置) ──
    footer_y = H - 50
    draw.text((40, footer_y), "majorexplorer.com", font=font("Times", 26), fill=TEXT)
    donate_w = 110
    draw.rectangle([(W - 40 - donate_w, footer_y - 8), (W - 40, footer_y + 32)], fill=ACCENT)
    draw.text((W - 40 - donate_w + 28, footer_y), "公 益", font=font("STHeiti", 20), fill=BG)

    img.save(OUT, "PNG", optimize=True)
    print(f"✅ Wrote {OUT} ({W}x{H}, {(OUT.stat().st_size/1024):.0f} KB)")


if __name__ == "__main__":
    render()
