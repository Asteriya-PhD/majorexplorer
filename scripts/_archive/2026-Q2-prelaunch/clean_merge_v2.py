#!/usr/bin/env python3
"""
v2 清洗: 数据按"院校层级"聚合 (跨年稳定), 专业组明细仅按"当年"保留

输出:
  - colleges.json                1008 院校元数据 (含层次/城市/性质)
  - school_history.json          每院校 × 物理/历史 × 年份的统计 (min, p10, median 位次/分数)
  - groups_latest.json           2025 年每个专业组明细 (供推荐结果页展示)
  - province_lines.json          各年省控线 (从 proscore 字段提取)
"""
import json, os
from collections import defaultdict
from pathlib import Path
from statistics import median

ROOT = Path('/Users/zhewenliu/Claude/gaokao-hubei-mvp')
RAW_DIR = ROOT / 'data' / 'province_raw'
OUT_DIR = ROOT / 'data'
YEARS = [2022, 2023, 2024, 2025]

# 1. 加载
all_items = []
for yr in YEARS:
    d = json.load(open(RAW_DIR / f'hubei_{yr}.json'))
    all_items.extend(d['items'])
print(f'[load] {len(all_items)} items')

# 2. 院校元数据
colleges = {}
for item in sorted(all_items, key=lambda x: x.get('year', 0)):
    sid = item.get('school_id')
    if not sid: continue
    colleges[sid] = {
        'school_id': sid,
        'name': item.get('name'),
        'province': item.get('province_name'),
        'city': item.get('city_name'),
        'county': item.get('county_name'),
        'type': item.get('type_name'),
        'nature': item.get('nature_name'),
        'f985': item.get('f985', 0),
        'f211': item.get('f211', 0),
        'dual_class': item.get('dual_class_name', ''),
        'level': item.get('level_name', ''),
    }
C9 = ['清华大学','北京大学','复旦大学','上海交通大学','浙江大学',
      '南京大学','中国科学技术大学','哈尔滨工业大学','西安交通大学']
def tier(c):
    if c.get('name') in C9: return 'C9'
    if c.get('f985') == 1: return '985'
    if c.get('f211') == 1: return '211'
    if '双一流' in (c.get('dual_class') or ''): return '双一流'
    if c.get('nature') == '公办': return '公办本科'
    return '民办/独立'
for c in colleges.values():
    c['tier'] = tier(c)

# 3. school_history: 每院校 × first_km × year 的统计
# first_km: 70000=物理 70004=历史
sh = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
# sh[sid][first_km][year] = [item, item, ...]
for item in all_items:
    sid = item.get('school_id')
    fk = item.get('first_km')
    yr = item.get('year')
    if not (sid and fk in (70000, 70004) and yr): continue
    sh[sid][fk][yr].append(item)

school_history = {}
for sid, by_fk in sh.items():
    school_history[sid] = {}
    for fk, by_yr in by_fk.items():
        type_name = '物理类' if fk == 70000 else '历史类'
        by_year_stats = {}
        for yr, items in by_yr.items():
            mins = [i.get('min') for i in items if isinstance(i.get('min'), (int,float))]
            sects = [i.get('min_section') for i in items
                     if isinstance(i.get('min_section'), (int,float))]
            if not mins: continue
            by_year_stats[yr] = {
                'group_count': len(items),
                'min_score': min(mins),
                'max_score': max(mins),  # 最高的"最低投档线"
                'median_score': median(mins),
                'min_rank': min(sects) if sects else None,       # 最难进的专业组的位次
                'max_rank': max(sects) if sects else None,       # 最容易进的专业组的位次
                'median_rank': median(sects) if sects else None,
            }
        if by_year_stats:
            school_history[sid][type_name] = by_year_stats
print(f'[school_history] {len(school_history)} schools have history')

# 4. groups_latest: 2025 年每个专业组明细
groups_latest = {'wuli': [], 'lishi': []}
for item in all_items:
    if item.get('year') != 2025: continue
    fk = item.get('first_km')
    bucket = 'wuli' if fk == 70000 else 'lishi' if fk == 70004 else None
    if not bucket: continue
    groups_latest[bucket].append({
        'school_id': item.get('school_id'),
        'school_name': item.get('name'),
        'sg_name': item.get('sg_name'),
        'sg_info': item.get('sg_info'),
        'special_group_id': item.get('special_group'),
        'batch_name': item.get('local_batch_name'),
        'min_score': item.get('min'),
        'min_rank': item.get('min_section'),
        'diff': item.get('diff'),
    })
# Sort by min_score desc
groups_latest['wuli'].sort(key=lambda g: -(g['min_score'] or 0))
groups_latest['lishi'].sort(key=lambda g: -(g['min_score'] or 0))
print(f'[groups_latest] wuli={len(groups_latest["wuli"])}  lishi={len(groups_latest["lishi"])}')

# 5. province_lines: 各年省控线
prov_lines = defaultdict(lambda: defaultdict(set))
for item in all_items:
    yr = item.get('year')
    fk = item.get('first_km')
    ps = item.get('proscore')
    if yr and fk in (70000, 70004) and isinstance(ps, (int,float)):
        prov_lines[yr][('物理类' if fk == 70000 else '历史类')].add(int(ps))
# 同一年同一科类应该只有一个 proscore (省控线)
province_lines = {}
for yr, by_type in prov_lines.items():
    province_lines[yr] = {t: sorted(s) for t, s in by_type.items()}

# 6. Write
def write_json(name, obj):
    p = OUT_DIR / name
    with open(p, 'w') as f:
        json.dump(obj, f, ensure_ascii=False)
    print(f'[write] {name}  ({os.path.getsize(p)/1024:.0f} KB)')

write_json('colleges.json', list(colleges.values()))
write_json('school_history.json', school_history)
write_json('groups_latest.json', groups_latest)
write_json('province_lines.json', province_lines)

# 7. Tier breakdown
from collections import Counter
tier_cnt = Counter(c['tier'] for c in colleges.values())
print(f'\n[tier] {dict(tier_cnt)}')

# 8. SAMPLE — 验证 schema 可用
print(f'\n=== 武大 物理类 历年 ===')
whu_sid = next(sid for sid, c in colleges.items() if c['name'] == '武汉大学')
for yr, s in sorted(school_history[whu_sid]['物理类'].items()):
    print(f"  {yr}: 专业组数={s['group_count']}  分数 [{s['min_score']}~{s['max_score']}] 中位={s['median_score']}  位次 [{s['min_rank']}~{s['max_rank']}] 中位={s['median_rank']}")

print(f'\n=== 华科 物理类 历年 ===')
hust_sid = next(sid for sid, c in colleges.items() if c['name'] == '华中科技大学')
for yr, s in sorted(school_history[hust_sid]['物理类'].items()):
    print(f"  {yr}: 专业组数={s['group_count']}  分数 [{s['min_score']}~{s['max_score']}] 中位={s['median_score']}  位次 [{s['min_rank']}~{s['max_rank']}] 中位={s['median_rank']}")

print(f'\n=== 湖北大学 物理类 历年 ===')
hbu_sid = next(sid for sid, c in colleges.items() if c['name'] == '湖北大学')
for yr, s in sorted(school_history[hbu_sid]['物理类'].items()):
    print(f"  {yr}: 专业组数={s['group_count']}  分数 [{s['min_score']}~{s['max_score']}] 中位={s['median_score']}  位次 [{s['min_rank']}~{s['max_rank']}] 中位={s['median_rank']}")

print(f'\n=== 各年省控线 ===')
for yr in sorted(province_lines.keys()):
    print(f"  {yr}: {province_lines[yr]}")
