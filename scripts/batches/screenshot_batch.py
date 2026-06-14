#!/usr/bin/env python3
"""批量截图 full-page 1440x900, 输出到 /tmp/gaokao_review/.

用法:
  python3 screenshot_batch.py                       # 默认 Batch 1 (14 张: 2 基准 + 12 法学)
  python3 screenshot_batch.py --csv path/to.csv     # 从 CSV 读 slug 列表
  python3 screenshot_batch.py --slugs slug1 slug2   # 单跑
"""
import sys, pathlib, csv, argparse
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp/skills/gaokao-major-explorer/data/curated")
OUT = pathlib.Path("/tmp/gaokao_review")
OUT.mkdir(parents=True, exist_ok=True)

# 基准 + 默认 Batch 1
DEFAULT_TARGETS = [
    "law", "public-order",  # 基准
    "international-law", "economic-law", "criminal-law", "civil-law-jurisprudence",
    "commercial-law", "administrative-law", "civil-procedure", "criminal-procedure",
    "prison-studies", "drug-control", "criminology", "foreign-police",
]

# Batch 2 基准 (Phase C 自动加, 别拼一起)
BATCH2_BASELINES = {
    "education": ["education", "preschool-education"],         # 教育基准
    "humanities": ["chinese-language-literature", "journalism-communication"],  # 文学基准
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="CSV with slug,title,style")
    ap.add_argument("--slugs", nargs="*", help="单跑 slug 列表")
    args = ap.parse_args()

    if args.csv:
        targets = []
        styles_seen = set()
        with open(args.csv) as f:
            for row in csv.DictReader(f):
                if row.get("slug"):
                    targets.append(row["slug"])
                    if row.get("style"):
                        styles_seen.add(row["style"])
        # 自动加该 style 的基准 (放最前以便对比)
        prepend = []
        for style in styles_seen:
            for base in BATCH2_BASELINES.get(style, []):
                if base not in targets and base not in prepend:
                    prepend.append(base)
        targets = prepend + targets
    elif args.slugs:
        targets = args.slugs
    else:
        targets = DEFAULT_TARGETS

    print(f"📸 准备截 {len(targets)} 张: {targets[:4]}...")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for slug in targets:
            src = ROOT / f"{slug}.html"
            out = OUT / f"{slug}.png"
            if not src.exists():
                print(f"  ⏭️  {slug}: html missing")
                continue
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            # 拦截 fonts.loli.net (外部 CSS @import 阻塞首屏渲染)
            page.route("**/fonts.loli.net/**", lambda r: r.abort())
            page.route("**/fonts.googleapis.com/**", lambda r: r.abort())
            page.route("**/fonts.gstatic.com/**", lambda r: r.abort())
            try:
                page.goto(f"file://{src}", wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1500)  # 让 chart.js / animation settle
                page.screenshot(path=str(out), full_page=True, timeout=30000)
                sz = out.stat().st_size
                print(f"  ✅ {slug:32s} → {out.name} ({sz//1024} KB)")
            except Exception as e:
                print(f"  ❌ {slug}: {type(e).__name__}: {str(e)[:200]}")
            finally:
                page.close()
        browser.close()

    print(f"\n完成: {len(list(OUT.glob('*.png')))} 张 PNG in {OUT}")


if __name__ == "__main__":
    main()
