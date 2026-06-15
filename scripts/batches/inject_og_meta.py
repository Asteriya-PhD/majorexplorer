#!/usr/bin/env python3
"""
inject_og_meta.py — 给 126 篇 HTML 注入 og:* meta tags.

策略: 用主题级 OG 图 (10 主题 × 2 字体, 已在 public/og/ og_hei/).
每 major 按 style 映射到对应 OG 图 URL. 不要给每个 major 单独生成 (昂贵).

memory 警告: 之前 "74 个 major HTML 全部注入 og:image 头是错" 是因为用了错的图或路径.
这里用 https://majorexplorer.pages.dev/og/{style}.png 绝对 URL (微信 / Twitter / FB 都 fetch 绝对 URL).
"""
import argparse, json, pathlib, re

ROOT = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp")
PUBLIC = ROOT / "public"
MANIFEST = ROOT / "public/data/manifest.json"
DOMAIN = "https://majorexplorer.pages.dev"

# style → og 图 (默认 og/, 字体 默认 STHeiti Medium 用 og_hei/)
STYLE_TO_OG = {
    "law": "law", "gongan": "gongan", "business": "business", "finance": "finance",
    "medicine": "medicine", "sci": "sci", "cs": "cs", "education": "education",
    "humanities": "humanities", "arts": "arts", "administration": "business",
    "eng": "eng", "agri": "arts", "default": "arts",
}


def build_og_tags(slug: str, title: str, style: str, summary: str) -> str:
    og_style = STYLE_TO_OG.get(style, "default")
    # 默认 og_hei/ (宋体 + 黑体双套, hei 更现代)
    img_url = f"{DOMAIN}/og_hei/{og_style}.png"
    safe_title = title.replace('"', '&quot;')
    safe_summary = (summary[:120] + "...") if len(summary) > 120 else summary
    safe_summary = safe_summary.replace('"', '&quot;')
    return f'''    <meta property="og:type" content="article">
    <meta property="og:title" content="{safe_title}专业介绍 2026 高考 | Major Explorer">
    <meta property="og:description" content="{safe_summary}">
    <meta property="og:image" content="{img_url}">
    <meta property="og:url" content="{DOMAIN}/{slug}.html">
    <meta property="og:site_name" content="Major Explorer">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{safe_title}专业介绍 2026 高考 | Major Explorer">
    <meta name="twitter:description" content="{safe_summary}">
    <meta name="twitter:image" content="{img_url}">'''


def inject(slug: str, d: dict, dry: bool = False) -> tuple[bool, str]:
    p = PUBLIC / f"{slug}.html"
    if not p.exists():
        return False, "no html"
    html = p.read_text(encoding="utf-8")
    # 已存在 og:image → 跳过
    if re.search(r'<meta[^>]*property=["\']og:image["\']', html, re.IGNORECASE):
        return False, "already has og:image"
    # 在 <title> 之后插入
    og_block = build_og_tags(
        slug,
        d.get("title", slug),
        d.get("style", "default"),
        d.get("summary", d.get("overview_v2", {}).get("lede", "") if isinstance(d.get("overview_v2"), dict) else ""),
    )
    new_html, n = re.subn(
        r'(<title>[^<]*</title>)',
        r'\1\n' + og_block,
        html,
        count=1,
    )
    if n == 0:
        return False, "no <title> found"
    if not dry:
        p.write_text(new_html, encoding="utf-8")
    return True, "injected"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    targets = [e for e in m["majors"]]
    injected = 0
    skipped = 0
    for e in targets:
        p = PUBLIC / f"{e['slug']}.html"
        if not p.exists():
            continue
        json_p = ROOT / f"skills/gaokao-major-explorer/data/curated/{e['slug']}.json"
        d = json.loads(json_p.read_text(encoding="utf-8")) if json_p.exists() else {}
        ok, msg = inject(e["slug"], d, args.dry_run)
        if ok:
            injected += 1
        else:
            skipped += 1
    print(f"{'📋 DRY-RUN' if args.dry_run else '✅'} inject: {injected}, skip: {skipped}")


if __name__ == "__main__":
    main()