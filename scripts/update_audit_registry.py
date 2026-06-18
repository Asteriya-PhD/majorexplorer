#!/usr/bin/env python3
"""
update_audit_registry.py — 审计结果写入 data/audit_registry.json

用途: 任何 audit 工具 (content_audit.py / smart_audit.py / 手审) 跑完后,
     调本工具把结果登记进 data/audit_registry.json (git tracked 单一真相).

为什么需要: smart_audit.py 路由决策依赖"该 slug 上次 audit 分数", 跨 session 必须有
git tracked 单一来源, 否则分散在 test_results/ (gitignore) / .worktrees/ 副本 / 各 session
本地 log, agent 行动时看不到对方结果 → 重复劳动.

用法:
  # 单条登记 (从 JSON 文件读)
  python3 scripts/update_audit_registry.py --from-file test_results/content_audit_1781747659.json

  # 单条登记 (从 stdin 读 JSON)
  cat result.json | python3 scripts/update_audit_registry.py --from-stdin

  # 批量登记 (整个目录)
  python3 scripts/update_audit_registry.py --from-dir test_results/

  # 全量重建 (从 test_results/ 全部 content_audit_*.json 重新 import)
  python3 scripts/update_audit_registry.py --rebuild

  # 看当前状态
  python3 scripts/update_audit_registry.py --stats
"""
import argparse, json, glob, os, sys, datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data' / 'audit_registry.json'
TEST_RESULTS = ROOT / 'test_results'

def to_verdict(score):
    if score is None: return None
    if score >= 8: return '优秀'
    if score >= 7: return '合格'
    if score >= 6: return '可接受'
    return '需修'

def load_registry():
    if REGISTRY.exists():
        return json.load(open(REGISTRY))
    return {
        'version': '1.0',
        'updated_at': datetime.datetime.now().isoformat(),
        'totals': {}, 'stats': {},
        'majors': {},
    }

def save_registry(reg):
    reg['updated_at'] = datetime.datetime.now().isoformat()
    # 重新算 stats
    score_dist = defaultdict(int)
    for v in reg['majors'].values():
        score_dist[v.get('current_verdict') or 'unknown'] += 1
    reg['stats'] = {
        'audited_3+': sum(1 for v in reg['majors'].values() if v['audit_count'] >= 3),
        'audited_once': sum(1 for v in reg['majors'].values() if v['audit_count'] == 1),
        'currently_8+': score_dist.get('优秀', 0),
        'currently_7-8': score_dist.get('合格', 0),
        'currently_6-7': score_dist.get('可接受', 0),
        'currently_below_6': score_dist.get('需修', 0),
    }
    reg.setdefault('totals', {})['audited'] = len(reg['majors'])
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    json.dump(reg, open(REGISTRY, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    return reg

def parse_audit_file(path):
    """从 content_audit_{ts}.json 抽 [{slug, title, overall_score, verdict, ...}]"""
    try:
        ts = int(Path(path).stem.split('_')[-1])
    except (ValueError, IndexError):
        ts = int(datetime.datetime.now().timestamp())
    dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat()
    try:
        d = json.load(open(path))
    except Exception as e:
        print(f'⚠️  无法解析 {path}: {e}')
        return []
    items = d if isinstance(d, list) else [d]
    out = []
    for item in items:
        slug = item.get('slug')
        if not slug: continue
        out.append({
            'slug': slug,                   # 关键: 保留 slug 供 apply_entries 用
            'title': item.get('title', slug),
            'date': dt, 'timestamp': ts,
            'source_file': Path(path).name,
            'score': item.get('overall_score'),
            'verdict': item.get('verdict'),
            'highlights': item.get('highlights', [])[:3],
            'issues': item.get('issues', []),
            'fix_suggestion': item.get('fix_suggestion'),
            'error': item.get('error'),
        })
    return out

def apply_entries(reg, entries, manifest_by_slug):
    for entry in entries:
        slug = entry['slug']
        m_entry = manifest_by_slug.get(slug, {})
        if slug not in reg['majors']:
            reg['majors'][slug] = {
                'title': m_entry.get('title', slug),
                'style': m_entry.get('style', ''),
                'discipline': m_entry.get('discipline', ''),
                'audit_count': 0,
                'current_score': None,
                'current_verdict': None,
                'last_audit_at': None,
                'tier_history': [],
                'audit_history': [],
            }
        r = reg['majors'][slug]
        r['title'] = r.get('title') or m_entry.get('title', slug)
        r['style'] = r.get('style') or m_entry.get('style', '')
        r['discipline'] = r.get('discipline') or m_entry.get('discipline', '')
        r['audit_count'] += 1
        r['audit_history'].append(entry)
        # 更新 latest
        if r['last_audit_at'] is None or entry['timestamp'] > datetime.datetime.fromisoformat(r['last_audit_at'].replace('Z', '+00:00')).timestamp():
            r['current_score'] = entry['score']
            r['current_verdict'] = to_verdict(entry['score'])
            r['last_audit_at'] = entry['date']

def cmd_rebuild():
    """全量重建: 扫 test_results/ 全部 content_audit_*.json"""
    files = sorted(glob.glob(str(TEST_RESULTS / 'content_audit_*.json')))
    print(f'扫到 {len(files)} 个 content_audit_*.json')
    # 加载 manifest
    manifest_by_slug = {}
    if (ROOT / 'public/data/manifest.json').exists():
        m = json.load(open(ROOT / 'public/data/manifest.json'))
        manifest_by_slug = {x['slug']: x for x in m['majors']}
    reg = {
        'version': '1.0',
        'updated_at': datetime.datetime.now().isoformat(),
        'totals': {
            'majors': len(manifest_by_slug),
            'audited': 0,
            'never_audited': 0,
            'external_audited': 0,
        },
        'stats': {},
        'majors': {},
    }
    for f in files:
        entries = parse_audit_file(f)
        apply_entries(reg, entries, manifest_by_slug)
    audited = set(reg['majors'].keys())
    reg['totals']['audited'] = len(audited)
    reg['totals']['never_audited'] = len(manifest_by_slug) - len(audited & set(manifest_by_slug.keys()))
    reg['totals']['external_audited'] = len(audited - set(manifest_by_slug.keys()))
    save_registry(reg)
    print(f'✅ 重建: {reg["totals"]}')

def cmd_from_file(path):
    reg = load_registry()
    manifest_by_slug = {}
    if (ROOT / 'public/data/manifest.json').exists():
        m = json.load(open(ROOT / 'public/data/manifest.json'))
        manifest_by_slug = {x['slug']: x for x in m['majors']}
    entries = parse_audit_file(path)
    apply_entries(reg, entries, manifest_by_slug)
    save_registry(reg)
    print(f'✅ 登记 {len(entries)} 条进 registry')

def cmd_from_dir(path):
    reg = load_registry()
    manifest_by_slug = {}
    if (ROOT / 'public/data/manifest.json').exists():
        m = json.load(open(ROOT / 'public/data/manifest.json'))
        manifest_by_slug = {x['slug']: x for x in m['majors']}
    files = sorted(glob.glob(f'{path}/content_audit_*.json'))
    total = 0
    for f in files:
        entries = parse_audit_file(f)
        apply_entries(reg, entries, manifest_by_slug)
        total += len(entries)
    save_registry(reg)
    print(f'✅ 批量登记 {total} 条 (来自 {len(files)} 个文件)')

def cmd_from_stdin():
    reg = load_registry()
    manifest_by_slug = {}
    if (ROOT / 'public/data/manifest.json').exists():
        m = json.load(open(ROOT / 'public/data/manifest.json'))
        manifest_by_slug = {x['slug']: x for x in m['majors']}
    data = json.load(sys.stdin)
    # 输入格式: 单个或 list
    if isinstance(data, dict):
        # 单个 audit, 包成 list
        items = [data]
    else:
        items = data
    entries = []
    ts = int(datetime.datetime.now().timestamp())
    dt = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    for item in items:
        slug = item.get('slug')
        if not slug: continue
        entries.append({
            'date': dt, 'timestamp': ts,
            'source_file': 'stdin',
            'score': item.get('overall_score'),
            'verdict': item.get('verdict'),
            'highlights': item.get('highlights', [])[:3],
            'issues': item.get('issues', []),
            'fix_suggestion': item.get('fix_suggestion'),
        })
    apply_entries(reg, entries, manifest_by_slug)
    save_registry(reg)
    print(f'✅ stdin 登记 {len(entries)} 条')

def cmd_stats():
    reg = load_registry()
    print('=== audit_registry.json 当前状态 ===')
    print(f'updated_at: {reg.get("updated_at")}')
    print(f'totals: {reg.get("totals")}')
    print(f'stats: {reg.get("stats")}')
    print()
    # Top 5 多次 audit
    by_count = sorted(reg['majors'].items(), key=lambda x: -x[1]['audit_count'])[:5]
    print('=== 多次 audit 排行 ===')
    for s, m in by_count:
        print(f'  {s}: {m["audit_count"]} 次, 当前 {m["current_score"]}/10 ({m["current_verdict"]})')

def main():
    p = argparse.ArgumentParser(description='更新 audit_registry.json (git tracked 单一真相)')
    p.add_argument('--rebuild', action='store_true', help='全量重建 (扫 test_results/ 全部)')
    p.add_argument('--from-file', help='从单个 content_audit_{ts}.json 登记')
    p.add_argument('--from-dir', help='从目录批量登记')
    p.add_argument('--from-stdin', action='store_true', help='从 stdin 读 JSON')
    p.add_argument('--stats', action='store_true', help='看当前状态')
    args = p.parse_args()

    if args.rebuild:
        cmd_rebuild()
    elif args.from_file:
        cmd_from_file(args.from_file)
    elif args.from_dir:
        cmd_from_dir(args.from_dir)
    elif args.from_stdin:
        cmd_from_stdin()
    elif args.stats:
        cmd_stats()
    else:
        p.print_help()

if __name__ == '__main__':
    main()
