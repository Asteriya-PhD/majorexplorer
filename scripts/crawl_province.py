#!/usr/bin/env python3
"""
湖北高考志愿 — 用 zjzw.cn 的 province endpoint 一次拉全省所有院校
覆盖: 2022/2023/2024/2025 × ~6700 records/yr = ~27000 总条目
含字段: school + 城市 + f985/f211 标签 + 专业组 + 选科 + 投档线 + 位次
"""
import json, time, urllib.request, urllib.error
from pathlib import Path

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'
HUBEI_PID = 42
YEARS = [2022, 2023, 2024, 2025]
SIZE = 20
SLEEP = 0.6
RETRY = 3
RETRY_WAIT = 5

ROOT = Path('/Users/zhewenliu/Claude/gaokao-hubei-mvp')
OUT_DIR = ROOT / 'data' / 'province_raw'
OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG = ROOT / 'data' / 'province_crawl.log'

def fetch(url):
    for attempt in range(RETRY):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read())
        except Exception as e:
            if attempt < RETRY - 1:
                time.sleep(RETRY_WAIT)
                continue
            raise

start = time.time()
with open(LOG, 'w') as logf:
    for year in YEARS:
        all_items = []
        # First page: get numFound
        url = f'https://api.zjzw.cn/web/api/?local_province_id={HUBEI_PID}&page=1&size={SIZE}&uri=apidata/api/gk/score/province&year={year}'
        try:
            d = fetch(url)
            data = d.get('data', {})
            if not isinstance(data, dict):
                msg = f'[FAIL] year={year} page=1 returned list, abort'
                print(msg); logf.write(msg+'\n'); continue
            numFound = data.get('numFound', 0)
            items = data.get('item', [])
            all_items.extend(items)
            total_pages = (numFound + SIZE - 1) // SIZE
            msg = f'[year {year}] numFound={numFound}, pages={total_pages}'
            print(msg); logf.write(msg+'\n'); logf.flush()
            time.sleep(SLEEP)

            # Remaining pages
            for page in range(2, total_pages + 1):
                url = f'https://api.zjzw.cn/web/api/?local_province_id={HUBEI_PID}&page={page}&size={SIZE}&uri=apidata/api/gk/score/province&year={year}'
                try:
                    d = fetch(url)
                    data = d.get('data', {})
                    if isinstance(data, dict):
                        items = data.get('item', [])
                        all_items.extend(items)
                    if page % 50 == 0:
                        elapsed = time.time() - start
                        msg = f'  [{year}] page {page}/{total_pages}  items={len(all_items)}  elapsed={elapsed:.0f}s'
                        print(msg); logf.write(msg+'\n'); logf.flush()
                except Exception as e:
                    msg = f'  [{year}] page {page} FAIL: {e}'
                    logf.write(msg+'\n')
                time.sleep(SLEEP)

            # Save year file
            out = OUT_DIR / f'hubei_{year}.json'
            with open(out, 'w') as f:
                json.dump({'year': year, 'province_id': HUBEI_PID,
                          'count': len(all_items), 'items': all_items},
                          f, ensure_ascii=False)
            msg = f'[year {year}] DONE  saved {len(all_items)} items → {out}'
            print(msg); logf.write(msg+'\n'); logf.flush()
        except Exception as e:
            msg = f'[year {year}] CATASTROPHIC FAIL: {e}'
            print(msg); logf.write(msg+'\n')

elapsed = time.time() - start
final_msg = f'\n=== ALL DONE === time={elapsed:.0f}s'
print(final_msg)
with open(LOG, 'a') as f:
    f.write(final_msg)
    # Summary
    for year in YEARS:
        p = OUT_DIR / f'hubei_{year}.json'
        if p.exists():
            d = json.load(open(p))
            line = f'  hubei_{year}.json: {d["count"]} items'
            print(line); f.write('\n'+line)
