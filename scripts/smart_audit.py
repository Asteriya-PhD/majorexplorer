#!/usr/bin/env python3
"""
smart_audit.py — 智能混合审计路由器 (Layer 1 启发式 + 智能 Layer 2 LLM)

取代老 content_audit.py 慢审计模式 (Day 3 Team B 2026-06-17 经验):
- 老模式: 全量 LLM audit, 279 篇 ~9.3h / ¥140
- 新模式: 启发式 100% + LLM 智能路由 ~30% = 2-3h / ¥40
- 覆盖率: 95%+ 真实 bug (漏 5% 旧稳定文件, 历史已 ≥7, 再审大概率还是 ≥7)

═══════════════════════════════════════════════════════════════
Layer 1: check_major.py (1s/篇, 0¥)
  · 4 anti-pollution 模式 (lede/who_fits_no/deep_study/curriculum)
  · 18 字段 schema 完整性
  · salary p25/p50/p75 一致性
  · deep_study 总和 ≈ 100
  · alumni ≥ 2, employment ≥ 5

Layer 2: m3 audit (2min/篇, ¥0.5, thinking=ON)
  · 跨字段数字矛盾 (lede vs pitfalls)
  · 学科评估 rank 准确性 (4th round evaluation)
  · alumni_quote 具体度 (修了 X 课 / 做过 Y 项目)
  · 文风 / 文化契合度

═══════════════════════════════════════════════════════════════
Layer 2 触发条件 (满足任一 → m3 audit):

  1. Layer 1 warning/error
     └─ 启发式抓到的污染/缺失 (1s 验证 schema)
  2. 从未 audit 过
     └─ test_results/ 无该 slug 历史
  3. 历史 < 7.0
     └─ 上次 m3 audit 失败
  4. 上次 audit 后改过
     └─ mtime(major.json) > last_audit_time
  5. 5% 随机抽样
     └─ sanity check (稳定文件偶尔再审,防 v3 退化)

═══════════════════════════════════════════════════════════════
用法:

  python3 scripts/smart_audit.py                    # 全 279 篇, 智能路由
  python3 scripts/smart_audit.py --dry-run          # 只列候选, 不跑 m3
  python3 scripts/smart_audit.py --limit 50         # 限 50 篇 Layer 2
  python3 scripts/smart_audit.py --sample-rate 0.1  # 10% 抽样 (默认 5%)
  python3 scripts/smart_audit.py --json             # JSON 输出候选列表
  python3 scripts/smart_audit.py --force            # 强制全审 (跳过智能路由)
  python3 scripts/smart_audit.py --category eng     # 只审 eng 类别

═══════════════════════════════════════════════════════════════
成本估算 (基于 279 篇):

  模式               | Layer 1 | Layer 2 | 总耗时 | 成本  | 覆盖率
  全量 + 全量        | 5-20m   | 9.3h    | 9.5h   | ¥140  | 100%
  智能混合 (默认)   | 5-20m   | 2-3h    | 2-3h   | ¥40   | 95%+
  全 sample 18 篇   | 5-20m   | 36m     | 1h     | ¥3    | 30%

═══════════════════════════════════════════════════════════════
"""
import sys, os, json, argparse, time, random, subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / 'skills' / 'gaokao-major-explorer' / 'data' / 'curated'
TEST_RESULTS = ROOT / 'test_results'
REGISTRY = ROOT / 'data' / 'audit_registry.json'  # git tracked 单一真相 (2026-06-18 新增)

# 成本估算 (基于 m3 thinking 模式 + 计费)
M3_COST_PER_AUDIT = 0.5  # ¥
M3_TIME_PER_AUDIT = 120  # 秒 (2 分钟)
L1_TIME_PER_CHECK = 3    # 秒


def parse_args():
    p = argparse.ArgumentParser(
        description='智能混合审计 (Layer 1 启发式 + 智能路由 Layer 2 LLM)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('用法:')[1].split('═')[0] if '═' in __doc__ else ''
    )
    p.add_argument('--dry-run', action='store_true', help='只列候选, 不跑 m3 audit')
    p.add_argument('--limit', type=int, default=None, help='限制 Layer 2 候选数')
    p.add_argument('--sample-rate', type=float, default=0.05, help='随机抽样率 (默认 0.05 = 5%%)')
    p.add_argument('--json', action='store_true', help='JSON 输出')
    p.add_argument('--force', action='store_true', help='强制全审, 跳过智能路由')
    p.add_argument('--category', type=str, default=None, help='只审某 category (eng/law/humanities/...)')
    p.add_argument('--min-score', type=float, default=7.0, help='历史 score < 此值触发 Layer 2 (默认 7.0)')
    p.add_argument('--quiet', action='store_true', help='减少输出')
    return p.parse_args()


def get_all_majors():
    """获取全部 279 篇 major JSON,返回 [(slug, style, mtime), ...]"""
    majors = []
    for f in CURATED.glob('*.json'):
        slug = f.stem
        # 排除 TEMPLATE.json (非 major)
        if slug in ('TEMPLATE', 'template', 'README', '_index'):
            continue
        try:
            d = json.load(open(f))
            style = d.get('style', 'unknown')
            # 排除 style=unknown (可能是数据文件)
            if not style or style == 'unknown':
                continue
        except Exception:
            continue
        mtime = f.stat().st_mtime
        majors.append((slug, style, mtime, f))
    return sorted(majors, key=lambda x: x[0])


def load_audit_history():
    """
    解析 test_results/content_audit_*.json, 返回:
    {
      slug: {
        'latest_score': float|None,
        'latest_ts': int|None,           # unix timestamp of latest audit
        'verdict': str|None,
        'total_audits': int,
        'scores': [list of all scores]    # 用于 m3 variance 分析
      }
    }
    """
    # 2026-06-18 改造: 优先读 data/audit_registry.json (git tracked 单一真相)
    # fallback: test_results/content_audit_*.json (gitignore, 跨 session 失同步)
    history = {}
    if REGISTRY.exists():
        try:
            reg = json.load(open(REGISTRY))
            for slug, m in reg.get('majors', {}).items():
                history[slug] = {
                    'latest_score': m.get('current_score'),
                    'latest_ts': int(datetime.fromisoformat(m['last_audit_at'].replace('Z', '+00:00')).timestamp()) if m.get('last_audit_at') else None,
                    'verdict': m.get('current_verdict'),
                    'total_audits': m.get('audit_count', 0),
                    'scores': [h.get('score') for h in m.get('audit_history', []) if h.get('score') is not None],
                }
            return history  # registry 是真理, 直接返回
        except Exception as e:
            print(f'⚠️  registry 解析失败 ({e}), fallback test_results/')
    files = sorted(TEST_RESULTS.glob('content_audit_*.json'))
    for f in files:
        try:
            ts = int(f.stem.split('_')[-1])
        except ValueError:
            continue
        try:
            entries = json.load(open(f))
        except Exception:
            continue
        if not isinstance(entries, list):
            continue
        for entry in entries:
            slug = entry.get('slug', '')
            if not slug:
                continue
            score = entry.get('overall_score')
            verdict = entry.get('verdict', '')
            if slug not in history:
                history[slug] = {'latest_score': None, 'latest_ts': None, 'verdict': None,
                                 'total_audits': 0, 'scores': []}
            h = history[slug]
            h['total_audits'] += 1
            if score is not None:
                h['scores'].append(score)
                if h['latest_ts'] is None or ts > h['latest_ts']:
                    h['latest_ts'] = ts
                    h['latest_score'] = score
                    h['verdict'] = verdict
    return history


def run_layer1(slug):
    """跑 check_major.py,返回 (has_error, has_warning)"""
    try:
        r = subprocess.run(
            ['python3', 'scripts/check_major.py', slug],
            capture_output=True, text=True, cwd=ROOT, timeout=30
        )
        out = r.stdout
        # 关键: ❌ [CRITICAL] / ❌ <slug>: 是真 error
        #       ⚠️ [WARNING] / ⚠️  <slug> 是真 warning
        #       ❌ 失败: N 篇 / ⚠️ 警告: N 篇 只是 count summary,不算
        has_error = ('❌ [CRITICAL]' in out) or any(
            f'❌ {s}' in out for s in [slug]
        )
        has_warning = ('⚠️ [WARNING]' in out) or any(
            f'⚠️  {s}' in out or f'⚠️ {s}' in out for s in [slug]
        )
        return (has_error, has_warning)
    except subprocess.TimeoutExpired:
        return (False, True)  # timeout 当 warning
    except Exception:
        return (True, True)  # error 当 error


def route_layer2(majors, history, args):
    """
    智能路由: 决定哪些 major 需要跑 Layer 2 (m3 audit)
    返回 [(slug, style, reason), ...] 按 reason 优先级排序
    """
    candidates = []
    rng = random.Random(42)  # 固定种子保证 reproducibility

    for slug, style, mtime, f in majors:
        if args.category and style != args.category:
            continue
        if args.force:
            candidates.append((slug, style, 'force'))
            continue

        reasons = []
        h = history.get(slug, {})
        latest_score = h.get('latest_score')
        latest_ts = h.get('latest_ts')

        # 规则 1: Layer 1 错误
        has_error, has_warning = run_layer1(slug)
        if has_error:
            reasons.append('L1-error')
        elif has_warning:
            reasons.append('L1-warning')

        # 规则 2: 从未 audit
        if not h or latest_ts is None:
            reasons.append('no-history')

        # 规则 3: 历史 < 7.0
        if latest_score is not None and latest_score < args.min_score:
            reasons.append(f'low-score({latest_score})')

        # 规则 4: 上次 audit 后改过 (mtime > latest_ts)
        if latest_ts is not None and mtime > latest_ts:
            dt_days = (mtime - latest_ts) / 86400
            reasons.append(f'modified({dt_days:.0f}d)')

        # 规则 5: 5% 随机抽样
        if not reasons and rng.random() < args.sample_rate:
            reasons.append('random-sample')

        if reasons:
            candidates.append((slug, style, '+'.join(reasons)))

    return candidates


def format_report(candidates, majors, history, args):
    """格式化输出 Layer 2 候选"""
    lines = []
    lines.append('═' * 70)
    lines.append('🧠 智能混合审计 — Layer 2 候选路由')
    lines.append('═' * 70)
    lines.append(f'Layer 1 范围: {len(majors)} 篇 (启发式 1s/篇, 0¥)')
    lines.append(f'Layer 2 范围: {len(candidates)} 篇 (m3 audit 2min/篇, ~¥0.5/篇)')

    if candidates:
        # 按 reason 分类统计
        from collections import Counter
        reason_counter = Counter()
        for _, _, reason in candidates:
            primary = reason.split('+')[0]
            reason_counter[primary] += 1
        lines.append('')
        lines.append('Layer 2 触发原因分布:')
        for reason, count in reason_counter.most_common():
            lines.append(f'  {reason:20s}  {count:3d} 篇')
    else:
        lines.append('')
        lines.append('✅ 没有 Layer 2 候选 — 所有 majors 启发式通过 + 历史 ≥7 + 未改')

    # 成本估算
    n_l2 = min(len(candidates), args.limit) if args.limit else len(candidates)
    l2_time_min = n_l2 * M3_TIME_PER_AUDIT / 60
    l2_cost = n_l2 * M3_COST_PER_AUDIT
    l1_time_min = len(majors) * L1_TIME_PER_CHECK / 60
    total_time = l1_time_min + l2_time_min
    total_cost = l2_cost
    lines.append('')
    lines.append('⏱️  估算 (基于 m3 thinking 模式):')
    lines.append(f'  Layer 1:  {l1_time_min:6.1f} min   ¥{0:.0f}')
    lines.append(f'  Layer 2:  {l2_time_min:6.1f} min   ¥{l2_cost:.0f}')
    lines.append(f'  合计:     {total_time:6.1f} min   ¥{total_cost:.0f}')
    lines.append('')

    # 候选详情
    if candidates and not args.quiet:
        lines.append('━' * 70)
        lines.append(f'Layer 2 候选 ({len(candidates)} 篇):')
        lines.append('━' * 70)
        # 按 style 分组
        by_style = defaultdict(list)
        for slug, style, reason in candidates:
            by_style[style].append((slug, reason))
        for style in sorted(by_style.keys()):
            lines.append(f'\n[{style}] {len(by_style[style])} 篇')
            for slug, reason in by_style[style][:10]:
                h = history.get(slug, {})
                last = h.get('latest_score', 'N/A')
                lines.append(f'  {slug:50s}  last={last}  reason={reason}')
            if len(by_style[style]) > 10:
                lines.append(f'  ... ({len(by_style[style]) - 10} more)')

    return '\n'.join(lines)


def run_layer2_batch(candidates, args):
    """跑 Layer 2 (m3 audit) on candidates, via content_audit.py"""
    if not candidates:
        print('\n✅ 0 候选, 跳过 Layer 2')
        return

    # 限制
    if args.limit:
        candidates = candidates[:args.limit]
        print(f'\n⚠️  限 {args.limit} 篇')

    # 准备 slugs:style 列表
    slugs = [f'{slug}:{style}' for slug, style, _ in candidates]
    slugs_arg = ' '.join(slugs)

    # 调 content_audit.py
    cmd = ['python3', 'scripts/batches/content_audit.py', '--slugs'] + slugs
    print(f'\n🚀 启动 Layer 2: {" ".join(cmd[:4])} ... ({len(slugs)} 篇)')
    print('⏱️  预计 ~{:.0f} min'.format(len(slugs) * M3_TIME_PER_AUDIT / 60))

    if args.dry_run:
        print('\n(dry-run: 跳过实际运行)')
        return

    try:
        r = subprocess.run(cmd, cwd=ROOT, timeout=3600 * 4)  # 4h 超时
        if r.returncode != 0:
            print(f'❌ content_audit.py exited with {r.returncode}')
    except subprocess.TimeoutExpired:
        print('❌ Layer 2 timeout (4h)')
    except KeyboardInterrupt:
        print('\n⚠️  用户中断')


def main():
    args = parse_args()

    # Step 1: 列全部 major
    majors = get_all_majors()
    if not args.quiet and not args.json:
        print(f'🔍 扫描 {len(majors)} 个 major JSON ...')

    # Step 2: 加载 audit history
    history = load_audit_history()
    if not args.quiet and not args.json:
        print(f'📚 历史 audit 记录: {len(history)} 个 slug, {sum(h["total_audits"] for h in history.values())} 条记录')

    # Step 3: 智能路由
    candidates = route_layer2(majors, history, args)

    # Step 4: 输出报告
    if args.json:
        output = {
            'total_majors': len(majors),
            'l2_candidates': len(candidates),
            'candidates': [
                {'slug': slug, 'style': style, 'reason': reason,
                 'last_score': history.get(slug, {}).get('latest_score')}
                for slug, style, reason in candidates
            ],
            'estimated_time_min': len(majors) * L1_TIME_PER_CHECK / 60 + len(candidates) * M3_TIME_PER_AUDIT / 60,
            'estimated_cost': len(candidates) * M3_COST_PER_AUDIT
        }
        # JSON 模式: 只输出 JSON (适合 pipe 给 jq/python)
        sys.stdout.write(json.dumps(output, ensure_ascii=False, indent=2))
        sys.stdout.write('\n')
        sys.stdout.flush()
        return
    else:
        if not args.quiet:
            print(format_report(candidates, majors, history, args))

    # Step 5: 跑 Layer 2
    run_layer2_batch(candidates, args)


if __name__ == '__main__':
    main()
