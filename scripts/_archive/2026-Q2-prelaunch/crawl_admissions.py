#!/usr/bin/env python3
"""
湖北高考志愿: 批量爬掌上高考 API 拿院校专业组投档数据
Target: 155 院校 (41 985 + 83 211 + 32 湖北普本) × 3 年 (2022/2023/2024) = 465 次
"""
import json, time, urllib.request, urllib.error, os, sys
from pathlib import Path

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'
HUBEI_PID = 42
YEARS = [2022, 2023, 2024]
SLEEP = 0.6  # 礼貌 sleep

ROOT = Path('/Users/zhewenliu/Claude/gaokao-hubei-mvp')
RAW_DIR = ROOT / 'data' / 'admissions_raw'
RAW_DIR.mkdir(parents=True, exist_ok=True)
LOG = ROOT / 'data' / 'crawl.log'

targets = json.load(open(ROOT / 'data' / 'target_schools.json'))['matched']
print(f'[*] Target schools: {len(targets)}, years: {YEARS}, total calls: {len(targets)*len(YEARS)}')

ok, empty, fail = 0, 0, 0
fail_list = []
start = time.time()

with open(LOG, 'w') as logf:
    for i, t in enumerate(targets, 1):
        sid, name = t['sid'], t['name']
        for yr in YEARS:
            out = RAW_DIR / f'{sid}_{yr}.json'
            if out.exists() and out.stat().st_size > 100:
                continue  # resume
            url = f'https://static-data.gaokao.cn/www/2.0/schoolspecialscore/{sid}/{yr}/{HUBEI_PID}.json'
            try:
                req = urllib.request.Request(url, headers={'User-Agent': UA})
                resp = urllib.request.urlopen(req, timeout=15)
                body = resp.read()
                if len(body) < 200:
                    empty += 1
                    msg = f'[empty] {sid}/{name}/{yr} = {len(body)} bytes'
                else:
                    with open(out, 'wb') as f:
                        f.write(body)
                    ok += 1
                    msg = f'[ok]    {sid}/{name}/{yr} = {len(body)} bytes'
            except Exception as e:
                fail += 1
                fail_list.append(f'{sid}/{name}/{yr}: {e}')
                msg = f'[FAIL]  {sid}/{name}/{yr}: {e}'
            logf.write(msg + '\n')
            logf.flush()
            time.sleep(SLEEP)
        if i % 10 == 0:
            elapsed = time.time() - start
            done = i * len(YEARS)
            total = len(targets) * len(YEARS)
            eta = elapsed / done * (total - done) if done else 0
            print(f'[{i}/{len(targets)}] ok={ok} empty={empty} fail={fail}  elapsed={elapsed:.0f}s  eta={eta:.0f}s')

elapsed = time.time() - start
print(f'\n=== Done ===  total={ok+empty+fail}  ok={ok}  empty={empty}  fail={fail}  time={elapsed:.0f}s')
print(f'Raw files: {RAW_DIR}')
print(f'Log: {LOG}')
if fail_list:
    print(f'\nFailures:')
    for f in fail_list[:20]:
        print(f'  {f}')

# Quick summary of harvested data
print(f'\n=== Raw harvest summary ===')
total_items = 0
schools_with_data = 0
import os
for fn in os.listdir(RAW_DIR):
    p = RAW_DIR / fn
    if p.stat().st_size < 500: continue
    try:
        d = json.load(open(p))
        data = d.get('data', {})
        if isinstance(data, dict):
            cnt = sum(len(v.get('item', [])) for v in data.values() if isinstance(v, dict))
            if cnt > 0:
                total_items += cnt
                schools_with_data += 1
    except: pass
print(f'Raw JSONs: {len(os.listdir(RAW_DIR))}')
print(f'School-years with data: {schools_with_data}')
print(f'Total profession-group items: {total_items}')
