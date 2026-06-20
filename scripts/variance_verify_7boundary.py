#!/usr/bin/env python3
"""
variance_verify_7boundary.py — 97 篇 7-boundary variance verify (Day 8.5 B R2+R3)

Pipeline:
  1. Snapshot R1 scores from data/audit_registry.json
  2. Run R2: 97 slugs in 10 batches of ~10 via content_audit.py
  3. Run R3: same
  4. Read test_results/content_audit_*.json for R2+R3 scores
  5. Per slug: median(R1, R2, R3) → update audit_registry.json

Cost: ~¥80-120 (~97×2 m3 audits × ¥0.5)
Time: ~90-120 min (2 rounds × ~50 min sequential)

Usage:
  python3 scripts/variance_verify_7boundary.py                  # full run
  python3 scripts/variance_verify_7boundary.py --dry-run        # plan only
  python3 scripts/variance_verify_7boundary.py --round 2        # only R2
  python3 scripts/variance_verify_7boundary.py --median-only    # skip audits, just compute from existing test_results/
"""

import sys, os, json, subprocess, time, argparse, statistics
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / 'skills' / 'gaokao-major-explorer' / 'data' / 'curated'
TEST_RESULTS = ROOT / 'test_results'
REGISTRY = ROOT / 'data' / 'audit_registry.json'
SLUG_FILE = Path('/tmp/variance_7boundary_slugs.txt')

CONTENT_AUDIT = ROOT / 'scripts' / 'batches' / 'content_audit.py'


def load_slugs():
    """从 /tmp/variance_7boundary_slugs.txt 加载 (slug, style) 列表"""
    pairs = []
    for line in SLUG_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        slug, _, style = line.partition(':')
        pairs.append((slug.strip(), style.strip() or 'cs'))
    return pairs


def snapshot_registry():
    """从 registry 取 R1 scores (slug → score)"""
    if not REGISTRY.exists():
        return {}
    d = json.loads(REGISTRY.read_text())
    return {s: v.get('current_score') for s, v in d.get('majors', {}).items()
            if v.get('current_score') is not None}


def run_batch(slugs, round_num, batch_idx, total_batches):
    """跑一批 10 篇的 m3 audit via content_audit.py"""
    # 必须传 slug:style 否则 content_audit 默认 'cs' style
    args = [f'{s}:{st}' for s, st in slugs]
    print(f'\n{"="*80}')
    print(f'Round {round_num} · Batch {batch_idx}/{total_batches} · {len(slugs)} 篇')
    print(f'{"="*80}')
    print(' '.join(args[:3]) + (f' ... +{len(args)-3}' if len(args) > 3 else ''))

    before_ts = time.time()
    cmd = ['python3', str(CONTENT_AUDIT), '--slugs'] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    dur = time.time() - before_ts

    if r.returncode != 0:
        print(f'  ❌ exit={r.returncode}, stderr tail:')
        print(r.stderr[-500:] if r.stderr else '(empty)')
        return None

    # 找到新生成的 test_results/content_audit_*.json
    new_files = sorted(TEST_RESULTS.glob(f'content_audit_*.json'),
                       key=lambda f: f.stat().st_mtime, reverse=True)
    new_files = [f for f in new_files if f.stat().st_mtime >= before_ts - 1]
    out = new_files[0] if new_files else None
    print(f'  ✅ batch done in {dur:.0f}s, output: {out.name if out else "(missing)"}')
    return out


def collect_scores(test_result_file):
    """从 test_results/content_audit_*.json 提取 {slug: score}"""
    if not test_result_file or not test_result_file.exists():
        return {}
    data = json.loads(test_result_file.read_text())
    scores = {}
    for r in data:
        slug = r.get('slug')
        score = r.get('overall_score')
        if slug and score is not None and 'error' not in r:
            scores[slug] = score
    return scores


def compute_median_per_slug(r1, r2, r3):
    """Per slug: median across available rounds"""
    out = {}
    for slug in set(r1) | set(r2) | set(r3):
        scores = [s for s in (r1.get(slug), r2.get(slug), r3.get(slug)) if s is not None]
        if scores:
            out[slug] = round(statistics.median(scores), 1)
    return out


def update_registry(medians, rounds_metadata):
    """更新 audit_registry.json: 每 slug 用 median score"""
    d = json.loads(REGISTRY.read_text())
    majors = d.setdefault('majors', {})
    updated = 0
    for slug, score in medians.items():
        if slug in majors:
            old_score = majors[slug].get('current_score')
            majors[slug]['current_score'] = score
            majors[slug]['variance_verify'] = rounds_metadata
            majors[slug]['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            if old_score != score:
                updated += 1

    # 更新顶部统计
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
        'majors_count': len(medians),
        'updated_count': updated,
    }

    REGISTRY.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    return updated


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--round', type=int, choices=[2, 3], help='只跑某一轮')
    p.add_argument('--median-only', action='store_true', help='跳过 audit, 只算 median')
    p.add_argument('--batch-size', type=int, default=10)
    args = p.parse_args()

    pairs = load_slugs()
    print(f'📋 加载 {len(pairs)} 篇 7-boundary slugs')

    # 切批
    batches = [pairs[i:i + args.batch_size] for i in range(0, len(pairs), args.batch_size)]
    print(f'📦 分 {len(batches)} 批 × {args.batch_size} 篇/批')

    if args.dry_run:
        for i, b in enumerate(batches, 1):
            print(f'  Batch {i}: {len(b)} 篇 ({b[0][0]} ... {b[-1][0]})')
        return

    # Snapshot R1
    r1 = snapshot_registry()
    r1_in_scope = {s: r1.get(s) for s, _ in pairs}
    print(f'\n📸 R1 snapshot: {sum(1 for v in r1_in_scope.values() if v is not None)}/{len(pairs)} 有 score')

    r2, r3 = {}, {}
    r2_files, r3_files = [], []

    if args.median_only:
        # 找最新 2 个 content_audit 输出
        candidates = sorted(TEST_RESULTS.glob('content_audit_*.json'),
                            key=lambda f: f.stat().st_mtime, reverse=True)
        if len(candidates) >= 2:
            r3_files = [candidates[0]]
            r2_files = [candidates[1]]
            print(f'  R2 file: {r2_files[0].name}')
            print(f'  R3 file: {r3_files[0].name}')
    else:
        # 跑 R2
        if args.round in (2, None):
            print(f'\n🚀 Round 2 启动 ({len(batches)} 批 × ~5 min)')
            r2_results = []
            for i, b in enumerate(batches, 1):
                out = run_batch(b, 2, i, len(batches))
                if out: r2_results.append(out)
            r2_files = r2_results
            print(f'\n✅ Round 2 完: {len(r2_results)}/{len(batches)} 批成功')

        # 跑 R3
        if args.round in (3, None):
            print(f'\n🚀 Round 3 启动 ({len(batches)} 批 × ~5 min)')
            r3_results = []
            for i, b in enumerate(batches, 1):
                out = run_batch(b, 3, i, len(batches))
                if out: r3_results.append(out)
            r3_files = r3_results
            print(f'\n✅ Round 3 完: {len(r3_results)}/{len(batches)} 批成功')

    # 收集 scores
    r2_scores = {}
    for f in r2_files:
        r2_scores.update(collect_scores(f))
    r3_scores = {}
    for f in r3_files:
        r3_scores.update(collect_scores(f))

    print(f'\n📊 收集到 R2: {len(r2_scores)} 篇, R3: {len(r3_scores)} 篇')

    # 计算 median
    medians = compute_median_per_slug(r1_in_scope, r2_scores, r3_scores)
    print(f'📐 计算 median: {len(medians)} 篇')

    # 报告
    promoted = []  # 7 → 8
    demoted = []   # 7 → <7
    stable = []
    for slug, score in medians.items():
        old = r1_in_scope.get(slug)
        if old is not None:
            if score >= 8 and old < 8:
                promoted.append((slug, old, score))
            elif score < 7 and old >= 7:
                demoted.append((slug, old, score))
            else:
                stable.append((slug, old, score))

    print(f'\n📈 Variance Verify 结果:')
    print(f'  R1 → median:')
    print(f'    7 → 8+ : {len(promoted)} 篇')
    print(f'    7 → <7 : {len(demoted)} 篇 (注: R1 history 不一定真的 7, 见 raw scores)')
    print(f'    稳定    : {len(stable)} 篇')

    if promoted:
        print(f'\n  🌟 7→8 promoted ({len(promoted)}):')
        for slug, old, new in sorted(promoted, key=lambda x: -x[2])[:15]:
            print(f'    {slug:50s} {old} → {new}')
    if demoted:
        print(f'\n  ⚠️  7→<7 demoted ({len(demoted)}):')
        for slug, old, new in demoted:
            print(f'    {slug:50s} {old} → {new}')

    # 更新 registry
    rounds_meta = {
        'rounds': 3,
        'method': 'median(r1, r2, r3)',
        'r2_audits': len(r2_scores),
        'r3_audits': len(r3_scores),
    }
    updated = update_registry(medians, rounds_meta)
    print(f'\n✅ Registry updated: {updated} 篇分数变化')
    print(f'   写入: {REGISTRY}')

    # 最终分布
    d = json.loads(REGISTRY.read_text())
    print(f'\n📊 新分布: {d.get("distribution", {})}')


if __name__ == '__main__':
    main()