#!/usr/bin/env python3
"""
fix_salary_note_residual.py — Day 56 A.4 SAL-NOTE-1 残留 42 处手审迁移

把非 senior stage 的 note 内容**迁移**到对应 senior stage 的 note 末尾
(以分类前缀标识: [应届分线] / [段位细分] / [经验范围] / [元数据])
然后删除原 note.

为什么这样修:
  - 规则: note 只允许 senior stage (元数据放 senior 头部说明区)
  - 数据真实性: 42 处都是真实段位/分线数据, 不能直接删
  - 语义保留: 头部例外 / 顶端区间 / 应届分线 等都是读者关心信息
  - 简化: 不拆 employment_direction (太碎, 4 个去向 × 41 处 风险大)
    也不做"合并到 lede" (lede 是核心定位, 跟 stage 段位说明 性质不同)

用法:
  python3 scripts/batch/fix_salary_note_residual.py --dry-run
  python3 scripts/batch/fix_salary_note_residual.py
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / 'skills' / 'gaokao-major-explorer' / 'data' / 'curated'

# 资深判定 (跟 render_quality.py:65 一致)
SENIOR_KW = ['10年', '资深', '高级', '专家', '合伙人', '管理层', '主编']

# 排序 rank 跟 render_quality.py:52-63 一致
STAGE_RANK = [
    ('应届', 0),
    ('0-2', 1),
    ('1-3', 2),
    ('2年', 2),
    ('3年', 3),
    ('5年', 4),
    ('8年', 5),
    ('10年', 6),
    ('资深', 6),
    ('主编', 6),
]


def stage_rank(stage_name: str) -> int | None:
    for kw, rank in STAGE_RANK:
        if kw in stage_name:
            return rank
    return None


def is_senior(stage_name: str) -> bool:
    return any(kw in stage_name for kw in SENIOR_KW)


def categorize_note(stage_name: str, note: str) -> str:
    """给 note 一个分类前缀, 标明语义来源"""
    if '一线' in note or '二三线' in note or '县乡' in note or '基层' in note or '海外' in note:
        return '应届分线'
    if '骨干' in note or '总监' in note or '起薪' in note or '车间主任' in note or '区域经理' in note or '中职教研' in note:
        return '段位细分'
    if '经验' in note or '持证' in note or '占比' in note or '占比' in note or '顶端' in note or '1%' in note:
        return '经验范围'
    if '数据' in note or '估算' in note or '蓝皮书' in note or '麦可思' in note:
        return '元数据'
    return '段位细分'


def find_target_senior_stage(salary: dict, source_stage: str) -> str | None:
    """找最近的 senior stage. 优先 rank 最接近的"""
    src_rank = stage_rank(source_stage)
    if src_rank is None:
        # 没法分类, 找第一个 senior
        for s in salary:
            if is_senior(s):
                return s
        return None
    # 找 rank >= src_rank 的 senior
    best = None
    best_dist = 999
    for s in salary:
        if not is_senior(s):
            continue
        r = stage_rank(s)
        if r is None:
            continue
        dist = abs(r - src_rank)
        if dist < best_dist:
            best_dist = dist
            best = s
    return best


def fix_one(data: dict) -> tuple[int, list[str]]:
    sal = data.get('salary')
    if not isinstance(sal, dict):
        return 0, []

    migrated = 0
    msgs: list[str] = []

    for stage_name, vals in list(sal.items()):
        if not isinstance(vals, dict):
            continue
        note = vals.get('note')
        if not note:
            continue
        if is_senior(stage_name):
            continue

        # 找 target senior stage
        target = find_target_senior_stage(sal, stage_name)
        if not target:
            msgs.append(f'⚠️  {stage_name}: 无 senior stage 承接, 跳过')
            continue

        category = categorize_note(stage_name, note)
        # 拼到 senior note 末尾
        target_vals = sal[target]
        if 'note' in target_vals and target_vals['note']:
            target_vals['note'] = target_vals['note'].rstrip() + f' | [{category} · {stage_name}] {note}'
        else:
            target_vals['note'] = f'[{category} · {stage_name}] {note}'

        # 删原 note
        del vals['note']
        migrated += 1
        msgs.append(f'{stage_name} → {target} [{category}]: {note[:50]}')

    return migrated, msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    files = 0
    total = 0

    for p in sorted(CURATED.glob('*.json')):
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            print(f'⚠️  {p.name}: {e}', file=sys.stderr)
            continue

        m, msgs = fix_one(data)
        if not m:
            continue

        for m_ in msgs:
            print(f'  {p.stem}: {m_}')

        if not args.dry_run:
            p.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
        files += 1
        total += m

    print()
    print(f'── fix_salary_note_residual {"(DRY RUN)" if args.dry_run else ""} ──')
    print(f'  修改文件: {files}')
    print(f'  迁移 note: {total}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
