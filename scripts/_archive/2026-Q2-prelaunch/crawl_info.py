#!/usr/bin/env python3
"""B 路线: 爬 1008 院校 info.json, 拿 data.special (top 10 主打专业 + 学科评估)"""
import json, time, urllib.request
from pathlib import Path

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'
SLEEP = 0.4

ROOT = Path('/Users/zhewenliu/Claude/gaokao-hubei-mvp')
OUT_DIR = ROOT / 'data' / 'info_raw'
OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG = ROOT / 'data' / 'info_crawl.log'

colleges = json.load(open(ROOT / 'data' / 'colleges.json'))
sids = [c['school_id'] for c in colleges]
print(f'[*] Total: {len(sids)} schools')

ok, fail, skipped = 0, 0, 0
start = time.time()
with open(LOG, 'w') as logf:
    for i, sid in enumerate(sids, 1):
        out = OUT_DIR / f'{sid}.json'
        if out.exists() and out.stat().st_size > 1000:
            skipped += 1
            continue
        url = f'https://static-data.gaokao.cn/www/2.0/school/{sid}/info.json'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read()
            with open(out, 'wb') as f:
                f.write(body)
            ok += 1
            msg = f'[ok] {sid} {len(body)}'
        except Exception as e:
            fail += 1
            msg = f'[FAIL] {sid}: {e}'
        logf.write(msg + '\n'); logf.flush()
        time.sleep(SLEEP)
        if i % 50 == 0:
            elapsed = time.time() - start
            eta = elapsed / i * (len(sids) - i)
            print(f'[{i}/{len(sids)}] ok={ok} fail={fail} skip={skipped}  elapsed={elapsed:.0f}s  eta={eta:.0f}s')

elapsed = time.time() - start
print(f'\n=== DONE === ok={ok} fail={fail} skip={skipped}  total_time={elapsed:.0f}s')
