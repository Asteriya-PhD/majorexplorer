#!/usr/bin/env python3
"""
variance_median_r1r2.py — 取 R1+R2 median, 更新 audit_registry.json

(因 R3 只跑了 1 批, 用户决定 R2 跑完即停, 改为 2-point median)
"""
import json, statistics
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data' / 'audit_registry.json'
TEST_RESULTS = ROOT / 'test_results'

# R2 batch files (按完成时间排序, 10 批共 97 篇)
R2_FILES = [
    'content_audit_1781882560.json',  # 23:22 B1 (10)
    'content_audit_1781883739.json',  # 23:42 B2 (10)
    'content_audit_1781884229.json',  # 23:50 B3 (10)
    'content_audit_1781884669.json',  # 23:57 B4 (10)
    'content_audit_1781885536.json',  # 00:12 B5 (10)
    'content_audit_1781886155.json',  # 00:22 B6 (10)
    'content_audit_1781886885.json',  # 00:34 B7 (10)
    'content_audit_1781887343.json',  # 00:42 B8 (10)
    'content_audit_1781888047.json',  # 00:54 B9 (10)
    'content_audit_1781888501.json',  # 01:01 B10 (7)
]


def collect_r2():
    """从 R2 文件收集 {slug: score}"""
    out = {}
    for f in R2_FILES:
        path = TEST_RESULTS / f
        if not path.exists():
            print(f'  ⚠️  missing: {f}')
            continue
        data = json.loads(path.read_text())
        for r in data:
            slug = r.get('slug')
            score = r.get('overall_score')
            err = r.get('error')
            if slug and score is not None and not err:
                if slug in out:
                    print(f'  ⚠️  duplicate {slug} in R2 (taking first)')
                    continue
                out[slug] = score
    return out


def main():
    if not REGISTRY.exists():
        print('❌ registry missing')
        return
    d = json.loads(REGISTRY.read_text())
    majors = d.get('majors', {})

    # R1 from pre-variance git snapshot (correct, not affected by auto-sync)
    r1_path = Path('/tmp/r1_snapshot_pre_variance.json')
    if r1_path.exists():
        r1 = json.loads(r1_path.read_text())
    else:
        print('⚠️  /tmp/r1_snapshot_pre_variance.json missing, fallback to registry')
        r1 = {s: v.get('current_score') for s, v in majors.items()
              if v.get('current_score') is not None and 7.0 <= v.get('current_score') < 8.0}

    # R2 from test_results
    r2 = collect_r2()

    print(f'R1: {len(r1)} 篇 7-boundary (registry)')
    print(f'R2: {len(r2)} 篇 (test_results)')

    # Median per slug
    medians = {}
    detail = []
    for slug in set(r1) | set(r2):
        scores = [s for s in (r1.get(slug), r2.get(slug)) if s is not None]
        if len(scores) >= 1:
            med = round(statistics.median(scores), 1)
            medians[slug] = med
            detail.append((slug, r1.get(slug), r2.get(slug), med))

    print(f'\nMedian 计算: {len(medians)} 篇')

    # Bucket
    promoted = []  # 7 → ≥8
    demoted = []   # 7 → <7
    stable_high = []  # 7 → 7
    stable_low = []  # <7 → <7
    no_r1 = []  # 没 R1
    for slug, r1s, r2s, med in detail:
        if r1s is None:
            no_r1.append((slug, r2s, med))
        elif med >= 8 and r1s < 8:
            promoted.append((slug, r1s, r2s, med))
        elif med < 7 and r1s >= 7:
            demoted.append((slug, r1s, r2s, med))
        elif r1s >= 7:
            stable_high.append((slug, r1s, r2s, med))
        else:
            stable_low.append((slug, r1s, r2s, med))

    print(f'\n📊 Variance Verify R1+R2 结果:')
    print(f'  7 → ≥8 promoted: {len(promoted)}')
    print(f'  7 → <7 demoted  : {len(demoted)}')
    print(f'  7 → 7 stable    : {len(stable_high)}')
    print(f'  <7 stable       : {len(stable_low)}')
    print(f'  无 R1 (新 audit): {len(no_r1)}')

    if promoted:
        print(f'\n🌟 7→8 promoted ({len(promoted)}):')
        for slug, r1s, r2s, med in sorted(promoted, key=lambda x: -x[3]):
            print(f'  {slug:50s} R1={r1s} R2={r2s} → med={med}')
    if demoted:
        print(f'\n⚠️  7→<7 demoted ({len(demoted)}):')
        for slug, r1s, r2s, med in demoted:
            print(f'  {slug:50s} R1={r1s} R2={r2s} → med={med}')

    # R1 vs R2 disagreement (variance)
    variance_high = [(s, a, b) for s, a, b in [(slug, r1.get(slug), r2.get(slug))
                     for slug in set(r1) & set(r2)] if a is not None and b is not None and abs(a - b) >= 1]
    if variance_high:
        print(f'\n📈 R1 vs R2 disagreement (≥1 分, {len(variance_high)}):')
        for slug, a, b in sorted(variance_high, key=lambda x: -abs(x[1]-x[2]))[:15]:
            print(f'  {slug:50s} R1={a} R2={b}  Δ={b-a:+.0f}')

    # Update registry
    updated = 0
    for slug, med in medians.items():
        if slug in majors:
            old = majors[slug].get('current_score')
            majors[slug]['current_score'] = med
            majors[slug]['variance_verify'] = {
                'rounds': 2,
                'method': 'median(r1, r2)',
                'r1_score': r1.get(slug),
                'r2_score': r2.get(slug),
                'median': med,
            }
            majors[slug]['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            if old != med:
                updated += 1

    # Distribution
    buckets = {'8+': 0, '7-8': 0, '6-7': 0, '<6': 0}
    for v in majors.values():
        s = v.get('current_score')
        if s is None: continue
        if s >= 8: buckets['8+'] += 1
        elif s >= 7: buckets['7-8'] += 1
        elif s >= 6: buckets['6-7'] += 1
        else: buckets['<6'] += 1
    d['distribution'] = buckets
    d['last_variance_verify'] = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'method': 'median(r1, r2) — R2 跑完即停, R3 未完整',
        'majors_count': len(medians),
        'updated_count': updated,
        'promoted': len(promoted),
        'demoted': len(demoted),
    }

    REGISTRY.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    print(f'\n✅ Registry updated: {updated} 篇分数变化')
    print(f'📊 新分布: {buckets}')


if __name__ == '__main__':
    main()