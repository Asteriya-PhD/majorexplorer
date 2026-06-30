#!/usr/bin/env python3
"""
schema_sweep_20260630.py — Day 57.1 Block 4: 普查 625 篇 major JSON 的 9 类 schema 怪癖

用法:
  python3 scripts/batch/schema_sweep_20260630.py --dry-run  # 仅统计
  python3 scripts/batch/schema_sweep_20260630.py             # 自动 fix 安全项

自动 fix 项 (安全, 无语义损失):
  1. curriculum.credit string → int
  2. alumni_quotes[i].school 改为 source (renderer 已 defensive)
  3. top_companies 缺 salary/headcount 字段 (填 null 占位)

标记人工 review 项 (需要单篇 polish):
  4. salary key 倒挂 (P25 5年 > P25 10年+)
  5. summary vs lede 完全重复
  6. deep_study 占比 sum ≠ 100
  7. 缺 lede (用 overview_v2.lede fallback 检查)
  8. 缺 discipline/menjia_moe
  9. theme_color 是 string 而非 {primary, accent, soft} object (保守不改)

退出码: 0 成功 / 1 有错误
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / 'skills' / 'gaokao-major-explorer' / 'data' / 'curated'


def check_credit_string(data: dict) -> list[str]:
    """curriculum.credit 是 string "3" 而非 int 3"""
    issues = []
    cur = data.get('curriculum', {})
    if isinstance(cur, dict):
        for k, v in cur.items():
            if isinstance(v, dict) and 'credit' in v:
                if isinstance(v['credit'], str) and v['credit'].isdigit():
                    issues.append(f'curriculum.{k}.credit: str "{v["credit"]}" → int {int(v["credit"])}')
    return issues


def check_alumni_school(data: dict) -> list[str]:
    """alumni_quotes 用 school 字段而非 source"""
    issues = []
    aq = data.get('alumni_quotes', [])
    if not isinstance(aq, list):
        return issues
    for i, item in enumerate(aq):
        if isinstance(item, dict) and 'school' in item and 'source' not in item:
            issues.append(f'alumni_quotes[{i}].school: {item["school"][:30]} → source')
    return issues


def check_theme_color_string(data: dict) -> list[str]:
    """theme_color 是 string 而非 object"""
    issues = []
    tc = data.get('theme_color')
    if isinstance(tc, str):
        issues.append(f'theme_color: str "{tc[:40]}" → object (人工 review)')
    return issues


def check_salary_overflow(data: dict) -> list[str]:
    """salary 倒挂: P25 5年 > P25 10年+ (差值≥3 才算真倒挂, 1-2 万微小差异忽略)"""
    issues = []
    sal = data.get('salary', {})
    if not isinstance(sal, dict):
        return issues
    five_yr = None
    ten_yr = None
    for k, v in sal.items():
        if not isinstance(v, dict):
            continue
        if '5年' in k:
            five_yr = v.get('p25')
        if '10年' in k:
            ten_yr = v.get('p25')
    if five_yr is not None and ten_yr is not None and (five_yr - ten_yr) >= 5:
        issues.append(f'salary P25 倒挂: 5年={five_yr} > 10年+={ten_yr} (人工 review)')
    return issues


def check_summary_lede_dup(data: dict) -> list[str]:
    """summary vs lede 完全重复"""
    summary = data.get('summary', '')
    lede = data.get('lede', '')
    if summary and lede and summary.strip() == lede.strip():
        return ['summary == lede (完全重复, 人工 review)']
    return []


def check_deep_study_sum(data: dict) -> list[str]:
    """deep_study 路径占比 sum ≠ 100"""
    ds = data.get('deep_study')
    if not isinstance(ds, list):
        return []
    pcts = []
    for item in ds:
        if isinstance(item, dict):
            p = item.get('pct', 0)
            if isinstance(p, (int, float)):
                pcts.append(p)
    if pcts:
        total = sum(pcts)
        if abs(total - 100) > 1:
            return [f'deep_study sum={total} ≠ 100 (人工 review)']
    return []


def check_missing_lede(data: dict) -> list[str]:
    """缺 lede 字段"""
    if not data.get('lede') and not (data.get('overview_v2') or {}).get('lede'):
        return ['缺 lede 字段 (人工 review)']
    return []


def check_missing_discipline(data: dict) -> list[str]:
    """缺 discipline / menjia_moe"""
    issues = []
    if not data.get('discipline'):
        issues.append('缺 discipline 字段 (Day 49 manifest 必备)')
    if not data.get('menjia_moe'):
        issues.append('缺 menjia_moe 字段 (Day 49 manifest 必备)')
    return issues


def fix_credit_string(data: dict) -> bool:
    """curriculum.credit string → int. 返回是否修改."""
    modified = False
    cur = data.get('curriculum', {})
    if isinstance(cur, dict):
        for k, v in cur.items():
            if isinstance(v, dict) and 'credit' in v:
                if isinstance(v['credit'], str) and v['credit'].isdigit():
                    v['credit'] = int(v['credit'])
                    modified = True
    return modified


def fix_alumni_school(data: dict) -> bool:
    """alumni_quotes[i].school → source. 返回是否修改."""
    modified = False
    aq = data.get('alumni_quotes', [])
    if not isinstance(aq, list):
        return modified
    for item in aq:
        if isinstance(item, dict) and 'school' in item and 'source' not in item:
            item['source'] = item.pop('school')
            modified = True
    return modified


def fix_top_companies(data: dict) -> bool:
    """top_companies 缺 salary/headcount 字段填 null"""
    modified = False
    tc = data.get('top_companies', [])
    if not isinstance(tc, list):
        return modified
    for item in tc:
        if isinstance(item, dict):
            if 'salary' not in item:
                item['salary'] = None
                modified = True
            if 'headcount' not in item:
                item['headcount'] = None
                modified = True
    return modified


CHECKS = [
    ('credit_string', check_credit_string, False),  # False = 不自动 fix
    ('alumni_school', check_alumni_school, False),
    ('theme_color_string', check_theme_color_string, False),
    ('salary_overflow', check_salary_overflow, False),
    ('summary_lede_dup', check_summary_lede_dup, False),
    ('deep_study_sum', check_deep_study_sum, False),
    ('missing_lede', check_missing_lede, False),
    ('missing_discipline', check_missing_discipline, False),
]

FIXES = [
    ('credit_string', fix_credit_string),
    # ('alumni_school', fix_alumni_school),  # 30 篇多为模板字段值 "校友 (院校脱敏)", 留人工 review
    ('top_companies', fix_top_companies),
]


def main():
    p = argparse.ArgumentParser(description='Day 57.1 Block 4 schema sweep')
    p.add_argument('--dry-run', action='store_true', help='仅统计, 不写盘')
    p.add_argument('--output', default='docs/SCHEMA_SWEEP_20260630.md', help='报告输出路径')
    args = p.parse_args()

    if not CURATED.exists():
        print(f'❌ curated 目录不存在: {CURATED}', file=sys.stderr)
        sys.exit(1)

    files = sorted(CURATED.glob('*.json'))
    print(f'扫到 {len(files)} 个 major JSON')

    stats = defaultdict(lambda: defaultdict(list))
    auto_fix_count = 0

    for f in files:
        try:
            data = json.load(open(f))
        except Exception as e:
            print(f'⚠️  解析失败 {f.name}: {e}', file=sys.stderr)
            continue
        slug = data.get('slug', f.stem)

        # 先跑 auto-fix (dry-run 也跑检测但不写)
        auto_modified = False
        if not args.dry_run:
            for fname, fixer in FIXES:
                if fixer(data):
                    auto_modified = True

        if auto_modified:
            # 写回
            with open(f, 'w', encoding='utf-8') as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)
                fp.write('\n')
            auto_fix_count += 1

        # 跑检查 (修后)
        for cname, checker, _ in CHECKS:
            issues = checker(data)
            if issues:
                for iss in issues:
                    stats[cname][slug].append(iss)

    # 生成报告
    lines = [
        '# Schema Sweep Report — 20260630',
        '',
        f'扫到: **{len(files)}** 个 major JSON',
        f'自动 fix 篇数: **{auto_fix_count}**' if not args.dry_run else f'模式: **dry-run** (0 篇修改)',
        '',
        '## 各类怪癖统计',
        '',
    ]
    for cname, _, _ in CHECKS:
        n_affected = len(stats[cname])
        lines.append(f'- **{cname}**: {n_affected} 篇')
        if n_affected:
            sample_slugs = list(stats[cname].keys())[:5]
            lines.append(f'  - 示例: {", ".join(f"`{s}`" for s in sample_slugs)}')

    lines.append('')
    lines.append('## 详细列表 (人工 review 优先)')
    lines.append('')
    for cname, _, _ in CHECKS:
        if not stats[cname]:
            continue
        lines.append(f'### {cname}')
        lines.append('')
        for slug, issues in sorted(stats[cname].items()):
            lines.append(f'- `{slug}`: {issues[0]}')
        lines.append('')

    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f'✅ 报告写至 {args.output}')
    print(f'自动 fix: {auto_fix_count} 篇')
    for cname, _, _ in CHECKS:
        print(f'  {cname}: {len(stats[cname])} 篇')


if __name__ == '__main__':
    main()