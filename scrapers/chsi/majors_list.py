"""POC scraper for chsi 专业库 (major library).

Strategy: chsi exposes 2 JSON APIs (no token required when context is warmed up):
- /zyk/zybk/xkCategory/{N}        → 门类 → 专业类列表
- /zyk/zybk/specialityesByCategory/{M} → 专业类 → 专业列表

So we can hit them directly (no HTML parsing). Crawl pattern:
  for menjia 105001..105014 (13 门类, skip 105011 = 军事学 empty):
    for sc in /xkCategory/{menjia}:
      for major in /specialityesByCategory/{sc.key}:
        record (zydm, zymc, specId, zymyd, hasZyjs)

Writes `data/raw/majors_list.json` (single file, all ~880 majors).

Run:
  scrapers/chsi/.venv/bin/python scrapers/chsi/majors_list.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

from patchright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_FILE = RAW_DIR / "majors_list.json"

BASE = "https://gaokao.chsi.com.cn"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)
# 13 学科门类 codes — empirically 105001..105014, skipping 105011 (军事学, empty)
MENJIA_CODES = [f"10500{i}" if i < 10 else f"1050{i}" for i in range(1, 15)]
# Map chsi categoryCode → 教育部门类 code (01..14)
CODE_TO_MOE = {
    "105001": "01", "105002": "02", "105003": "03", "105004": "04",
    "105005": "05", "105006": "06", "105007": "07", "105008": "08",
    "105009": "09", "105010": "10", "105011": "11", "105012": "12",
    "105013": "13", "105014": "14",
}


async def fetch_json(page, url: str) -> dict | None:
    """Use page.evaluate to fetch JSON in-context (carries the JS-challenge cookies)."""
    try:
        result = await page.evaluate(
            """async (url) => {
                const r = await fetch(url);
                return { status: r.status, body: await r.text() };
            }""",
            url,
        )
    except Exception as e:
        print(f"  evaluate err: {e!s:.80}", file=sys.stderr)
        return None
    if result["status"] != 200:
        print(f"  ⚠ {url} → {result['status']}", file=sys.stderr)
        return None
    try:
        return json.loads(result["body"])
    except json.JSONDecodeError as e:
        print(f"  ⚠ {url} → bad JSON: {e}", file=sys.stderr)
        return None


async def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    all_majors: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="chromium")
        ctx = await browser.new_context(
            user_agent=UA, viewport={"width": 1280, "height": 800},
            locale="zh-CN", timezone_id="Asia/Shanghai",
        )
        page = await ctx.new_page()
        # Warmup
        await page.goto(f"{BASE}/zyk/zybk/", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        t0 = time.time()
        for menjia in MENJIA_CODES:
            sub = await fetch_json(page, f"{BASE}/zyk/zybk/xkCategory/{menjia}")
            if not sub or not sub.get("flag"):
                print(f"  ⚠ skip 门类 {menjia}")
                continue
            sub_classes = sub.get("msg") or []
            # Filter out empty placeholder entries (e.g. 105011 has 0, 105014 has "-")
            sub_classes = [sc for sc in sub_classes if sc.get("name") and sc["name"] != "-"]
            moe = CODE_TO_MOE.get(menjia, menjia)
            print(f"门类 {moe} ({menjia}) → {len(sub_classes)} 专业类")
            for sc in sub_classes:
                resp = await fetch_json(page, f"{BASE}/zyk/zybk/specialityesByCategory/{sc['key']}")
                if not resp or not resp.get("flag"):
                    continue
                majors = resp.get("msg") or []
                for m in majors:
                    all_majors.append({
                        "moe_code": m.get("zydm"),
                        "name": m.get("zymc"),
                        "spec_id": m.get("specId"),
                        "satisfaction": float(m["zymyd"]) if m.get("zymyd") else None,
                        "has_intro": bool(m.get("hasZyjs")),
                        "menjia_moe": moe,
                        "menjia_chsi": menjia,
                        "subclass_chsi": sc["key"],
                        "subclass_name": sc["name"],
                        "detail_url": f"{BASE}/zyk/zybk/detail/{m['specId']}",
                    })
                print(f"  {sc['key']} {sc['name']:14} {len(majors):>3} 专业")
        await browser.close()

    elapsed = time.time() - t0
    OUT_FILE.write_text(json.dumps(all_majors, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== done: {len(all_majors)} majors in {elapsed:.1f}s → {OUT_FILE.relative_to(ROOT)} ===")


if __name__ == "__main__":
    asyncio.run(main())
