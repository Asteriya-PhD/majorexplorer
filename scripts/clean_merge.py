#!/usr/bin/env python3
"""
清洗合并 4 年 16000 条投档数据 → 两份输出:
  - colleges.json   880 院校元数据
  - admissions_clean.json  按 (school_id, special_group, type) 聚合 4 年历史
"""
import json
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path('/Users/zhewenliu/Claude/gaokao-hubei-mvp')
RAW_DIR = ROOT / 'data' / 'province_raw'
OUT_DIR = ROOT / 'data'
YEARS = [2022, 2023, 2024, 2025]

# 1. 加载 4 年原始数据
all_items = []
for yr in YEARS:
    d = json.load(open(RAW_DIR / f'hubei_{yr}.json'))
    print(f'[load] {yr}: {len(d["items"])} items')
    all_items.extend(d['items'])
print(f'[load] TOTAL: {len(all_items)} items across {len(YEARS)} years')

# 2. 院校元数据 (按 school_id dedup, 用最新年的数据)
colleges = {}
for item in sorted(all_items, key=lambda x: x.get('year', 0)):  # 老到新, 后写覆盖
    sid = item.get('school_id')
    if not sid: continue
    colleges[sid] = {
        'school_id': sid,
        'name': item.get('name'),
        'province': item.get('province_name'),
        'city': item.get('city_name'),
        'county': item.get('county_name'),
        'type': item.get('type_name'),         # 综合 / 理工 / 师范 ...
        'nature': item.get('nature_name'),     # 公办 / 民办
        'f985': item.get('f985', 0),
        'f211': item.get('f211', 0),
        'dual_class': item.get('dual_class_name', ''),
        'level': item.get('level_name', ''),    # 本科 / 专科
    }
print(f'[colleges] {len(colleges)} unique schools')

# 3. 院校层次 tier 分级 (推荐引擎权重 γ 用)
def tier(c):
    if c.get('f985') == 1: return 'C9' if c.get('name') in [
        '清华大学','北京大学','复旦大学','上海交通大学','浙江大学',
        '南京大学','中国科学技术大学','哈尔滨工业大学','西安交通大学'] else '985'
    if c.get('f211') == 1: return '211'
    if '双一流' in (c.get('dual_class') or ''): return '双一流'
    if c.get('nature') == '公办': return '公办本科'
    return '民办/独立'
tier_count = defaultdict(int)
for sid, c in colleges.items():
    c['tier'] = tier(c)
    tier_count[c['tier']] += 1
print(f'[tier] {dict(tier_count)}')

# 4. admissions: 聚合 4 年, key = (school_id, special_group, first_km)
# first_km: 70000=物理类 70004=历史类
groups = defaultdict(lambda: {
    'school_id': None, 'school_name': None,
    'special_group': None, 'sg_name': None, 'sg_info': None,
    'first_km': None, 'type_name': None,
    'batch_id': None, 'batch_name': None,
    'history': {}
})
for item in all_items:
    sid = item.get('school_id')
    sg = item.get('special_group')
    fk = item.get('first_km')
    if not (sid and sg and fk): continue
    key = (sid, sg, fk)
    g = groups[key]
    g['school_id'] = sid
    g['school_name'] = item.get('name')
    g['special_group'] = sg
    g['sg_name'] = item.get('sg_name')
    g['sg_info'] = item.get('sg_info')
    g['first_km'] = fk
    g['type_name'] = item.get('local_type_name')  # 物理类/历史类
    g['batch_id'] = item.get('local_batch_id')
    g['batch_name'] = item.get('local_batch_name')
    yr = item.get('year')
    # 投档线 + 位次
    g['history'][str(yr)] = {
        'min': item.get('min'),
        'min_section': item.get('min_section'),
        'filing': item.get('filing'),
        'diff': item.get('diff'),
        'proscore': item.get('proscore'),  # 省控线
    }
print(f'[groups] {len(groups)} unique (school × special_group × first_km) tuples')

# 5. 统计有几年数据
yr_distribution = defaultdict(int)
for g in groups.values():
    yr_distribution[len(g['history'])] += 1
print(f'[history coverage] {dict(yr_distribution)}')

# 6. 拆为物理/历史两个文件
admissions = {'wuli': [], 'lishi': []}
for g in groups.values():
    bucket = 'wuli' if g['first_km'] == 70000 else 'lishi' if g['first_km'] == 70004 else None
    if not bucket: continue
    admissions[bucket].append(g)
# 按 2025 投档线降序
def sort_key(g):
    h = g['history'].get('2025') or g['history'].get('2024') or {}
    return -(h.get('min') or 0)
admissions['wuli'].sort(key=sort_key)
admissions['lishi'].sort(key=sort_key)
print(f'[split] wuli={len(admissions["wuli"])}  lishi={len(admissions["lishi"])}')

# 7. 写入文件
out_colleges = OUT_DIR / 'colleges.json'
with open(out_colleges, 'w') as f:
    json.dump(list(colleges.values()), f, ensure_ascii=False)
print(f'[write] {out_colleges}  ({os.path.getsize(out_colleges)/1024:.0f} KB)')

out_wuli = OUT_DIR / 'admissions_wuli.json'
with open(out_wuli, 'w') as f:
    json.dump(admissions['wuli'], f, ensure_ascii=False)
print(f'[write] {out_wuli}  ({os.path.getsize(out_wuli)/1024:.0f} KB)')

out_lishi = OUT_DIR / 'admissions_lishi.json'
with open(out_lishi, 'w') as f:
    json.dump(admissions['lishi'], f, ensure_ascii=False)
print(f'[write] {out_lishi}  ({os.path.getsize(out_lishi)/1024:.0f} KB)')

# 8. Sample
print('\n=== SAMPLE: 武汉大学 物理类 专业组 (top 3) ===')
whu_wuli = [g for g in admissions['wuli'] if g['school_name'] == '武汉大学'][:3]
for g in whu_wuli:
    print(f"  {g['school_name']} {g['sg_name']} {g['sg_info']}")
    for yr in YEARS:
        h = g['history'].get(str(yr))
        if h:
            print(f"    {yr}: min={h['min']}  位次={h['min_section']}  diff={h['diff']}")

print('\n=== SAMPLE: 清华大学 物理类 ===')
qh = [g for g in admissions['wuli'] if g['school_name'] == '清华大学']
for g in qh:
    print(f"  {g['sg_name']} {g['sg_info']}")
    for yr in YEARS:
        h = g['history'].get(str(yr))
        if h:
            print(f"    {yr}: min={h['min']}  位次={h['min_section']}")
