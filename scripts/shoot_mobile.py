"""
shoot_mobile.py — 跑 N 主题 × M 设备的移动端截图.

用法:
    python3 scripts/shoot_mobile.py

输出: .tmp-hero/mobile/<style>_<device>.png

策略: 一个 chromium 实例 + per-major 独立 context (设备 emulation), 串行但快.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CURATED = ROOT / "skills/gaokao-major-explorer/data/curated"
OUT = ROOT / ".tmp-hero/mobile"
OUT.mkdir(parents=True, exist_ok=True)

# style → 代表性 major slug
REPS = {
    "cs":             "computer-science",
    "eng":            "industrial-design",
    "finance":        "economics",
    "medicine":       "pharmacy",
    "law":            "law",
    "education":      "psychology",
    "sci":            "chemistry",
    "humanities":     "philosophy",
    "agri":           "horticulture",
    "arts":           "digital-media-arts",
    "administration": "library-science",
    "gongan":         "public-security-demo",
    "business":       "business-administration-demo",
}

# device name → playwright device key
DEVICES = {
    "iphone13": "iPhone 13",
    "ipad":    "iPad (gen 7)",
}


def main():
    only_styles = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    fail = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for style, slug in REPS.items():
            if only_styles and style not in only_styles:
                continue
            html = CURATED / f"{slug}.html"
            if not html.exists():
                print(f"[skip] {style}: {html.name} not found")
                continue
            url = "file://" + str(html)
            for dev_short, dev_key in DEVICES.items():
                out = OUT / f"{style}_{dev_short}.png"
                try:
                    ctx = b.new_context(**p.devices[dev_key])
                    pg = ctx.new_page()
                    pg.goto(url)
                    pg.wait_for_timeout(800)
                    # 三连截: hero (viewport) / mid (~第二屏) / cta (~末页 1 屏)
                    pg.screenshot(path=str(out.with_name(out.stem + "_hero.png")))
                    # 第二屏: 滚到 viewport 高度处
                    vh = pg.viewport_size["height"]
                    pg.evaluate(f"window.scrollTo(0, {vh})")
                    pg.wait_for_timeout(200)
                    pg.screenshot(path=str(out.with_name(out.stem + "_mid.png")))
                    # 末屏: 滚到 document 底部
                    pg.evaluate("window.scrollTo(0, document.body.scrollHeight - window.innerHeight)")
                    pg.wait_for_timeout(200)
                    pg.screenshot(path=str(out.with_name(out.stem + "_cta.png")))
                    ctx.close()
                    print(f"✅ {style:14s} {dev_short:8s} → {out.stem}_{{hero,mid,cta}}.png")
                except Exception as e:
                    fail.append((style, dev_short, str(e)))
                    print(f"❌ {style:14s} {dev_short:8s} → {e}")
        b.close()
    if fail:
        print(f"\n{len(fail)} failures")
        sys.exit(1)


if __name__ == "__main__":
    main()
