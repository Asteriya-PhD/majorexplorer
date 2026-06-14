"""POC scraper for chsi 院校详情 (school detail page).

For each school (from schools_list.json), pulls the 院校特性 header block:
  - 教育行政主管部门 / 院校特性 / 所在地 / 详细地址
  - 官方网址 / 招生网址 / 官方电话
  - followers count
  - social media accounts (WeChat / Weibo / Baidu)

Reads `data/raw/schools_list.json`, writes one file per school under
`data/raw/school_detail/{edu_id}.json`. Resumable: skips files that
already exist.

Run:
  scrapers/chsi/.venv/bin/python scrapers/chsi/school_detail.py [--limit N] [--filter 985|211|双一流|本科]
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
LIST_FILE = RAW_DIR / "schools_list.json"
OUT_DIR = RAW_DIR / "school_detail"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)
RATE_DELAY = 0.5
JITTER = 0.4

# Iconfont glyphs leak from chsi spans
PUA_RE = re.compile(r"[-​-‍﻿]")
WS_RE = re.compile(r"\s+")
NUM_RE = re.compile(r"(\d[\d,]*)\s*人关注")
# Field patterns inside the header text block
FIELDS = {
    "governing": re.compile(r"教育行政主管部门：\s*([^\s]+)"),
    "tier": re.compile(r"院校特性：\s*(.+?)(?=\s+所在地|\s+详细地址|$)"),
    "province": re.compile(r"所在地：\s*([^\s]+)"),
    "address": re.compile(r"详细地址：\s*(.+?)(?=\s+官方网址|\s+招生网址|\s+官方电话|$)"),
    "website": re.compile(r"官方网址：\s*(\S+)"),
    "admission_url": re.compile(r"招生网址：\s*(\S+)"),
    "phone": re.compile(r"官方电话：\s*(\S+)"),
}


def _clean(s: str | None) -> str | None:
    if not s:
        return s
    out = PUA_RE.sub("", s)
    out = WS_RE.sub(" ", out).strip()
    return out or None


def parse_detail(html: str) -> dict:
    """Pull header fields + social accounts from one detail page."""
    soup = BeautifulSoup(html, "lxml")
    header = soup.select_one(".yxxx-header-content")
    out: dict = {}
    if header:
        text = _clean(header.get_text(" ", strip=True)) or ""
        followers_m = NUM_RE.search(text)
        if followers_m:
            try:
                out["followers"] = int(followers_m.group(1).replace(",", ""))
            except ValueError:
                pass
        for key, pat in FIELDS.items():
            m = pat.search(text)
            if m:
                out[key] = _clean(m.group(1))

    # social media (left = 微信/微博, right = 百家号/...)
    socials = {}
    for it in soup.select(".info-left-item, .info-right-item"):
        txt = _clean(it.get_text(" ", strip=True)) or ""
        # e.g. "微信 名称：北京大学招生办 微信号：gotopku1898"
        head = txt.split(" ", 1)[0] if txt else ""
        if head and head != "新媒体":
            socials[head] = txt
    if socials:
        out["socials"] = socials

    return out


async def fetch_one(page, school: dict) -> dict | None:
    """Fetch+parse one school's detail page. Returns merged record or None on failure."""
    url = school["detail_url"]
    t0 = time.time()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1500)
        html = await page.content()
    except Exception as e:
        print(f"  ❌ {school['name']:20} goto err: {e!s:.80}", file=sys.stderr)
        return None
    if len(html) < 5000:
        print(f"  ⚠ {school['name']:20} short body ({len(html)}b) — challenge stalled", file=sys.stderr)
        return None
    detail = parse_detail(html)
    elapsed = int((time.time() - t0) * 1000)
    merged = {**school, **detail, "fetched_at": int(time.time())}
    print(f"  ✅ {school['name']:20} ({elapsed:>4}ms, {len(detail)} new fields)")
    return merged


def _passes_filter(s: dict, flt: str | None) -> bool:
    if not flt:
        return True
    if flt == "本科":
        return s.get("degree") == "本科"
    if flt in ("985", "211", "双一流"):
        return flt in (s.get("tier") or "")
    return True


async def main(limit: int, flt: str | None):
    schools = json.loads(LIST_FILE.read_text(encoding="utf-8"))
    schools = [s for s in schools if _passes_filter(s, flt)]
    if limit:
        schools = schools[:limit]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== detail scrape: {len(schools)} schools (filter={flt!r}, limit={limit}) ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="chromium")
        ctx = await browser.new_context(
            user_agent=UA, viewport={"width": 1280, "height": 800},
            locale="zh-CN", timezone_id="Asia/Shanghai",
        )
        page = await ctx.new_page()
        # Warmup goto so JS challenge cookies are set
        await page.goto("https://gaokao.chsi.com.cn/sch/", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        t_total = time.time()
        ok = fail = skipped = 0
        for i, s in enumerate(schools):
            edu_id = s.get("edu_id") or f"sch{s['sch_id']}"
            out_path = OUT_DIR / f"{edu_id}.json"
            if out_path.exists():
                skipped += 1
                continue
            rec = await fetch_one(page, s)
            if rec is None:
                fail += 1
                continue
            out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
            ok += 1
            if i + 1 < len(schools):
                await asyncio.sleep(RATE_DELAY + random.random() * JITTER)
        await browser.close()
    elapsed = time.time() - t_total
    print(f"\n=== done: {ok} ok / {fail} fail / {skipped} skipped in {elapsed:.1f}s → {OUT_DIR.relative_to(ROOT)} ===")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="cap # of schools (0 = no cap)")
    ap.add_argument(
        "--filter",
        choices=["本科", "985", "211", "双一流"],
        default=None,
        help="filter schools (本科 = bachelor only; 双一流 = top-tier)",
    )
    args = ap.parse_args()
    asyncio.run(main(args.limit, args.filter))
