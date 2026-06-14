#!/usr/bin/env python3
"""批量截图 14 张 (2 基准 + 12 待审) full-page 1440x900, 输出到 /tmp/gaokao_review/."""
import sys, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp/skills/gaokao-major-explorer/data/curated")
OUT = pathlib.Path("/tmp/gaokao_review")
OUT.mkdir(parents=True, exist_ok=True)

# 基准 + 12 待审
BASE_LAW = "law"  # 法学
BASE_GONGAN = "public-order"  # 治安学
TARGETS = [
    BASE_LAW, BASE_GONGAN,
    "international-law", "economic-law", "criminal-law", "civil-law-jurisprudence",
    "commercial-law", "administrative-law", "civil-procedure", "criminal-procedure",
    "prison-studies", "drug-control", "criminology", "foreign-police",
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for slug in TARGETS:
        src = ROOT / f"{slug}.html"
        out = OUT / f"{slug}.png"
        if not src.exists():
            print(f"  ⏭️  {slug}: html missing")
            continue
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            page.goto(f"file://{src}", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)  # 让 chart.js / animation settle
            page.screenshot(path=str(out), full_page=True, timeout=60000)
            sz = out.stat().st_size
            print(f"  ✅ {slug:30s} → {out.name} ({sz//1024} KB)")
        except Exception as e:
            print(f"  ❌ {slug}: {type(e).__name__}: {e}")
        finally:
            page.close()
    browser.close()

print(f"\n完成: {len(list(OUT.glob('*.png')))} 张 PNG in {OUT}")