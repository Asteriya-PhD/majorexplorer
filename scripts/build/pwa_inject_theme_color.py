#!/usr/bin/env python3
"""PWA Tier 2 - 批量给详情页 HTML 注入 theme-color meta 标签

根据每个专业的 theme_color.primary, 在 head 注入:
<meta name="theme-color" content="#XXXXXX">

跳过 (shell 页面已有统一 #B8323A):
- index.html, majors.html, search.html, wishlist.html, preferences.html, recommendations.html
- m/index.html, m/catalog.html, m/recommendations.html, m/search.html, m/wishlist.html, m/me.html
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
PUBLIC = ROOT / "public"
CURATED = ROOT / "skills/gaokao-major-explorer/data/curated"

SHELL_PAGES = {
    "index.html", "majors.html", "search.html", "wishlist.html",
    "preferences.html", "recommendations.html", "me.html",
    "m/index.html", "m/catalog.html", "m/recommendations.html",
    "m/search.html", "m/wishlist.html", "m/me.html",
    "offline.html", "m/offline.html",
}

# 排除非专业页面 (测试/scaffold/对比页/模板)
NON_MAJOR_PAGES = {
    "A", "B", "C", "D", "TEMPLATE", "compare", "disclaimer",
    "actuarial-final",  # 已是独立主题
    "business-administration-demo",
    "public-security-demo",
    "cybersecurity",  # scaffold
    "arabic",  # scaffold (实际有独立 JSON 但名字带 scaffold)
    "art-history-theory",
    "energy-storage-science-engineering-2",
    "food-science-and-engineering",
    "integrated-circuit-design-systems-cross",
    "criminal-investigation-economics",
}

VIEWPORT_LINE = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
THEME_COLOR_LINE = '<meta name="theme-color" content="{color}">'


def load_color_mapping():
    """从 curated JSON 加载 slug → theme_color.primary 映射 (含 style fallback)"""
    mapping = {}
    style_to_color = {}
    for json_file in CURATED.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            slug = data.get("slug")
            tc = data.get("theme_color", {})
            style = data.get("style")
            color = tc.get("primary") if isinstance(tc, dict) else None
            if style and not color and style not in style_to_color:
                pass  # 下面统一填默认 style 映射
            if slug and color:
                mapping[slug] = color
            if style and color and style not in style_to_color:
                style_to_color[style] = color
        except Exception as e:
            print(f"⚠️  {json_file.name}: {e}")

    # 内置 style fallback (13 个学科主题色, 已知)
    FALLBACK = {
        "cs": "#5B5B47", "eng": "#5B5B47", "sci": "#1E5E72",
        "humanities": "#6B4F35", "law": "#3A3A3A", "gongan": "#3A3A3A",
        "medicine": "#8B2424", "education": "#5C7C4A", "finance": "#5A4632",
        "business": "#4A4564", "administration": "#4A4564",
        "arts": "#8B3A62", "agri": "#6B7A3F",
    }
    for s, c in FALLBACK.items():
        style_to_color.setdefault(s, c)

    # 第二遍: 给缺颜色的 slug 用 style fallback
    for json_file in CURATED.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            slug = data.get("slug")
            if slug and slug not in mapping:
                style = data.get("style")
                if style and style in style_to_color:
                    mapping[slug] = style_to_color[style]
        except Exception:
            pass

    return mapping


def already_has_theme_color(html: str) -> bool:
    return bool(re.search(r'<meta\s+name="theme-color"', html, re.IGNORECASE))


def inject(html: str, color: str) -> tuple[str, bool]:
    """注入 theme-color, 返回 (new_html, changed)"""
    if already_has_theme_color(html):
        return html, False
    if VIEWPORT_LINE not in html:
        # Fallback: 插入到 <head> 后第一个位置
        return html.replace("<head>", f"<head>\n{THEME_COLOR_LINE.format(color=color)}", 1), True
    return html.replace(VIEWPORT_LINE, VIEWPORT_LINE + "\n" + THEME_COLOR_LINE.format(color=color), 1), True


def main():
    print(f"📂 加载 curated JSON → theme_color mapping...")
    color_map = load_color_mapping()
    print(f"   找到 {len(color_map)} 个专业颜色")

    # 统计
    total = 0
    injected = 0
    skipped_no_color = 0
    skipped_shell = 0
    skipped_already_has = 0
    failed = []

    for html_file in PUBLIC.rglob("*.html"):
        rel = html_file.relative_to(PUBLIC).as_posix()
        if rel in SHELL_PAGES:
            skipped_shell += 1
            continue
        # 排除 /m/ 子目录下 (mobile 自己的页面, 但已包含在 shell)
        if rel.startswith("m/"):
            skipped_shell += 1
            continue
        stem = html_file.stem
        if stem in NON_MAJOR_PAGES:
            skipped_no_color += 1
            failed.append((rel, "non-major/scaffold"))
            continue
        total += 1

        slug = stem  # e.g. "computer-science" from "computer-science.html"
        color = color_map.get(slug)
        if not color:
            skipped_no_color += 1
            failed.append((rel, "no color in curated"))
            continue

        html = html_file.read_text(encoding="utf-8")
        new_html, changed = inject(html, color)
        if not changed:
            skipped_already_has += 1
            continue
        if new_html == html:
            continue  # nothing actually changed
        html_file.write_text(new_html, encoding="utf-8")
        injected += 1

    print(f"\n========== 注入完成 ==========")
    print(f"✅ 已注入 theme-color: {injected}")
    print(f"⏭️  跳过 shell 页面: {skipped_shell}")
    print(f"⏭️  已有 theme-color: {skipped_already_has}")
    print(f"⚠️  跳过 (无 curated 颜色): {skipped_no_color}")
    print(f"📁 总详情 HTML: {total}")
    if failed[:10]:
        print(f"\n前 10 个无颜色失败:")
        for rel, reason in failed[:10]:
            print(f"  - {rel}: {reason}")


if __name__ == "__main__":
    main()