"""POC scraper for chsi 院校库 (school list).

Pulls 100 schools (5 pages × 20 cards) from gaokao.chsi.com.cn/sch/.

- Uses patchright (stealth Chromium fork) to defeat 锐安信 JS challenge.
- 2 req/s rate limit (with random jitter) per CLAUDE memory `discipline-hierarchy-decisions-approved-2026-06-13`.
- Writes `data/raw/schools_list.json` (gitignored).
- Reuses one BrowserContext across pages — challenge cookies amortize.

Run: `scrapers/chsi/.venv/bin/python scrapers/chsi/schools_list.py [--pages N]`
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup
from patchright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_FILE = RAW_DIR / "schools_list.json"

BASE = "https://gaokao.chsi.com.cn"
LIST_URL_TMPL = f"{BASE}/sch/search--ss-on,option-qg,searchType-1,start-{{start}}.dhtml"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)
PAGE_SIZE = 20  # chsi default
RATE_DELAY = 0.5  # seconds between page navigations (≈ 2 req/s)
JITTER = 0.4

SCH_ID_RE = re.compile(r"schId-(\d+)")
EDU_ID_RE = re.compile(r"/xh/(\d+)\.")
# Strip leading Unicode Private-Use chars (iconfont glyphs leak from chsi spans)
PUA_PREFIX_RE = re.compile(r"^[-\s]+")


def _clean(s: str | None) -> str | None:
    if not s:
        return s
    return PUA_PREFIX_RE.sub("", s).strip() or None


def parse_card(item) -> dict | None:
    """Extract one school record from a `.sch-item` BS4 element. Returns None if unparseable."""
    name_a = item.select_one("a.name")
    if not name_a or not name_a.get("href"):
        return None
    href = name_a["href"]
    sch_id_m = SCH_ID_RE.search(href)
    if not sch_id_m:
        return None
    sch_id = int(sch_id_m.group(1))

    img = item.select_one("img")
    img_src = img.get("src", "") if img else ""
    edu_id_m = EDU_ID_RE.search(img_src)
    edu_id = edu_id_m.group(1) if edu_id_m else None

    # .sch-department — '<i> 北京 | 主管部门：教育部'
    dept = item.select_one("a.sch-department")
    province, governing = None, None
    if dept:
        txt = dept.get_text(" ", strip=True)
        # Drop iconfont leftover; expect "北京 | 主管部门： 教育部"
        parts = [p.strip() for p in txt.split("|")]
        if parts:
            province = parts[0]
        if len(parts) > 1:
            governing = parts[1].replace("主管部门：", "").strip()

    # .sch-level — '本科 | "双一流"建设高校'
    lvl = item.select_one("a.sch-level")
    degree, tier = None, None
    if lvl:
        ltxt = lvl.get_text(" ", strip=True)
        lparts = [p.strip() for p in ltxt.split("|")]
        if lparts:
            degree = lparts[0]
        if len(lparts) > 1:
            tier = lparts[1]

    # Satisfaction rating — hidden input value
    rating_in = item.select_one(".manyidu-star-box input[type=hidden]")
    rating = None
    if rating_in and rating_in.get("value"):
        try:
            rating = float(rating_in["value"])
        except ValueError:
            pass

    return {
        "sch_id": sch_id,
        "edu_id": edu_id,
        "name": _clean(name_a.get_text(strip=True)),
        "province": _clean(province),
        "governing": _clean(governing),
        "degree": _clean(degree),
        "tier": _clean(tier),
        "satisfaction": rating,
        "detail_url": BASE + href,
    }


async def fetch_page(page, start: int) -> list[dict]:
    """Navigate to one list page (offset=start) and parse all sch-item cards."""
    url = LIST_URL_TMPL.format(start=start)
    t0 = time.time()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"  goto err @start={start}: {e!s:.120}", file=sys.stderr)
        return []
    # JS challenge takes ~2-3s on first page, then cached.
    await page.wait_for_timeout(3000 if start == 0 else 1200)
    try:
        html = await page.content()
    except Exception as e:
        print(f"  content err @start={start}: {e!s:.120}", file=sys.stderr)
        return []
    elapsed = int((time.time() - t0) * 1000)
    if len(html) < 5000:
        print(f"  ⚠ start={start} short body ({len(html)}b, {elapsed}ms) — challenge may have stalled", file=sys.stderr)
        return []
    soup = BeautifulSoup(html, "lxml")
    items = soup.select("div.sch-item")
    records = [r for r in (parse_card(it) for it in items) if r]
    print(f"  start={start:>4} → {len(records):>2} schools ({elapsed}ms)")
    return records


async def main(pages: int):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out: list[dict] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="chromium")
        ctx = await browser.new_context(
            user_agent=UA,
            viewport={"width": 1280, "height": 800},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        page = await ctx.new_page()
        t_total = time.time()
        for i in range(pages):
            start = i * PAGE_SIZE
            recs = await fetch_page(page, start)
            out.extend(recs)
            if i + 1 < pages:
                await asyncio.sleep(RATE_DELAY + random.random() * JITTER)
        await browser.close()
    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    elapsed = time.time() - t_total
    print(f"\n=== done: {len(out)} schools in {elapsed:.1f}s → {OUT_FILE.relative_to(ROOT)} ===")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=5, help="# of list pages (20 schools each); POC=5 → 100 schools")
    args = ap.parse_args()
    asyncio.run(main(args.pages))
