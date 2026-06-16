"""Scraper for chsi 专业详情 (major detail page).

For each major with `has_intro=True` (from majors_list.json), pulls:
  - 专业简介 (introduction)
  - 主干课程 (main courses, list)
  - 培养目标 (training goal)
  - 就业方向 (career directions)
  - 考研方向 (graduate-study directions)
  - 相近专业 (similar majors)
  - 开设院校数 + top 院校列表

Reads `data/raw/majors_list.json`, writes one file per major under
`data/raw/major_detail/{spec_id}.json`. Resumable: skips files that
already exist.

Run:
  scrapers/chsi/.venv/bin/python scrapers/chsi/majors_detail.py [--limit N]

Plan: chsi Phase 2 §2 Step 3.1 (~36 min for 766 majors, resumable).
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
LIST_FILE = RAW_DIR / "majors_list.json"
OUT_DIR = RAW_DIR / "major_detail"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)
RATE_DELAY = 0.5
JITTER = 0.4

PUA_RE = re.compile(r"[-​-‍﻿]")
WS_RE = re.compile(r"\s+")


def _clean(s: str | None) -> str | None:
    if not s:
        return s
    out = PUA_RE.sub("", s)
    out = WS_RE.sub(" ", out).strip()
    return out or None


def parse_detail(html: str) -> dict:
    """Pull major detail fields from /zyk/zybk/detail/{spec_id}.

    chsi actual structure (verified 2026-06-14):
      - 1st col-content: introduction (本专业学生...)
      - 相近专业 section: anchor links to other majors
      - 本专业推荐人数较多的高校: pattern `school + score + 人数`
      - 该专业学生考研方向: comma-joined major names (until 已毕业人员从业方向)
      - 职业 anchors: xz.chsi.com.cn/occupation/occudetail.action → career list
    """
    soup = BeautifulSoup(html, "lxml")
    out: dict = {}

    # ── 1. Introduction: 1st .col-content block, text ≥ 100 chars ──
    intro_blocks = soup.select(".col-content")
    for blk in intro_blocks:
        text = _clean(blk.get_text(" ", strip=True)) or ""
        if len(text) > 100 and ("本专业" in text or "学生" in text or "培养" in text):
            out["introduction"] = text
            break

    # ── 2. 相近专业 (similar majors): anchors to /zyk/zybk/detail/ after label ──
    sim_anchor = soup.find(string=re.compile(r"相近专业"))
    if sim_anchor:
        container = sim_anchor.find_parent("div")
        # Walk forward from the anchor (not container, since anchors may be in next siblings)
        scan_root = container.parent if container else soup
        # All anchor tags within reasonable distance from the label
        for a in scan_root.find_all("a", href=re.compile(r"/zyk/zybk/detail/\d+")):
            name = _clean(a.get_text(" ", strip=True))
            if name and 2 <= len(name) <= 20 and name not in out.get("similar_majors", []):
                out.setdefault("similar_majors", []).append(name)
            if len(out.get("similar_majors", [])) >= 10:
                break

    # ── 3. 推荐人数较多的院校 (opening schools) ──
    school_anchor = soup.find(string=re.compile(r"本专业推荐人数较多的高校"))
    if school_anchor:
        container = school_anchor.find_parent("div")
        # Collect all text after the anchor up to next section label
        all_text = ""
        for elem in (container.find_all_next(string=True, limit=400) if container else []):
            txt = elem or ""
            all_text += txt + "|"
            # Stop at next section boundary
            if "该专业学生考研方向" in txt or "已毕业人员从业方向" in txt:
                break
        # Pattern: 校名 + 分隔符 + 数字.x + 分隔符 + 数字 + 人
        # 分隔符 = | 或 , 或 空白 (chsi 用 " | " 或 " |  ")
        schools_with_score = []
        for m in re.finditer(r"([一-龥A-Za-z\d·]{3,25})\s*[\|,，\s]+([\d.]+)\s*[\|,，\s]+(\d+)\s*人", all_text):
            name = m.group(1).strip()
            score = m.group(2)
            cnt = m.group(3)
            # Filter out non-school names
            if name in ("本校学生实名推荐", "更多", "本校学生", "实名推荐", "本专业推荐人数较多的高校"):
                continue
            if "本专业" in name or "推荐" in name:
                continue
            schools_with_score.append({"name": name, "satisfaction": float(score), "followers": int(cnt)})
            if len(schools_with_score) >= 15:
                break
        if schools_with_score:
            out["opening_schools"] = schools_with_score
            out["opening_school_count"] = len(schools_with_score)

    # ── 4. 考研方向 (graduate study): major names until "已毕业人员从业方向" ──
    grad_anchor = soup.find(string=re.compile(r"该专业学生考研方向"))
    if grad_anchor:
        container = grad_anchor.find_parent("div")
        # Collect text after the anchor, stop at 已毕业人员从业方向
        chunk = ""
        for elem in (container.find_all_next(string=True, limit=50) if container else []):
            txt = elem or ""
            if "已毕业人员从业方向" in txt or "从业方向" in txt:
                break
            chunk += txt + ","
        # Each "major" separated by | or , or whitespace
        raw_items = re.split(r"[|,，\s]+", chunk)
        majors = []
        for item in raw_items:
            item = item.strip()
            if not item:
                continue
            # Skip section labels
            if item in ("该专业学生考研方向", "考研方向", "考研"):
                continue
            # Skip pure numbers
            if re.match(r"^[\d.]+$", item):
                continue
            # Skip too short / too long
            if not (2 <= len(item) <= 20):
                continue
            majors.append(item)
            if len(majors) >= 10:
                break
        if majors:
            out["graduate_directions"] = majors

    # ── 5. 就业方向 (career): occupation anchors ──
    career_links = soup.select('a[href*="xz.chsi.com.cn/occupation"]')
    careers = []
    seen = set()
    for a in career_links:
        name = _clean(a.get_text(" ", strip=True))
        href = a.get("href", "")
        occ_id = ""
        if "id=" in href:
            occ_id = href.split("id=")[-1].split("&")[0]
        if name and name not in seen:
            seen.add(name)
            careers.append({"name": name, "occupation_id": occ_id})
    if careers:
        out["career_directions"] = careers[:15]

    return out


async def fetch_one(page, major: dict) -> dict | None:
    url = major["detail_url"]
    t0 = time.time()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1800)
        html = await page.content()
    except Exception as e:
        print(f"  ❌ {major['name']:20} goto err: {e!s:.80}", file=sys.stderr)
        return None
    if len(html) < 5000:
        print(f"  ⚠ {major['name']:20} short body ({len(html)}b) — challenge stalled", file=sys.stderr)
        return None
    detail = parse_detail(html)
    elapsed = int((time.time() - t0) * 1000)
    merged = {**major, **detail, "fetched_at": int(time.time())}
    fields = len(detail)
    print(f"  ✅ {major['name']:20} ({elapsed:>4}ms, {fields} new fields)")
    return merged


async def main(limit: int):
    majors = json.loads(LIST_FILE.read_text(encoding="utf-8"))
    # Only majors with detail pages
    majors = [m for m in majors if m.get("has_intro")]
    if limit:
        majors = majors[:limit]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== major detail scrape: {len(majors)} majors ===", flush=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="chromium")
        ctx = await browser.new_context(
            user_agent=UA, viewport={"width": 1280, "height": 800},
            locale="zh-CN", timezone_id="Asia/Shanghai",
        )
        page = await ctx.new_page()
        # Warmup: hit home to pass JS challenge (实测 ≥ 4000ms 必要)
        await page.goto("https://gaokao.chsi.com.cn/zyk/zybk/", wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        t_total = time.time()
        ok = fail = skipped = 0
        for i, m in enumerate(majors):
            spec_id = m.get("spec_id") or f"spec{m.get('sch_id')}"
            out_path = OUT_DIR / f"{spec_id}.json"
            if out_path.exists():
                skipped += 1
                continue
            rec = await fetch_one(page, m)
            if rec is None:
                fail += 1
                continue
            out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
            ok += 1
            if (i + 1) % 50 == 0:
                print(f"  ... {i+1}/{len(majors)} processed", flush=True)
            if i + 1 < len(majors):
                await asyncio.sleep(RATE_DELAY + random.random() * JITTER)
        await browser.close()
    elapsed = time.time() - t_total
    print(f"\n=== done: {ok} ok / {fail} fail / {skipped} skipped in {elapsed:.1f}s → {OUT_DIR.relative_to(ROOT)} ===", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="cap # of majors (0 = no cap)")
    args = ap.parse_args()
    asyncio.run(main(args.limit))