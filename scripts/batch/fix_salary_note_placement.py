#!/usr/bin/env python3
"""
fix_salary_note_placement.py — Day 51 A.2 SAL-NOTE-1 批量修

非 senior stage 含 `note` 是语义错位 (note 应仅 senior). 批量删纯错位 note:
- 数据来源 ("基于 X 数据估算..."): 元数据, 隐含在 salary 来源
- 应届分线 ("一线 X / 二三线 Y"): 语义在 stage name 已体现
- 段位说明 ("骨干 10-15 万 / 总监 20-32 万"): 重复 stage 范围
保留 (需手审): 经验范围 + 其他真实数据 (42 处 留给下个 session)

用法:
  python3 scripts/batch/fix_salary_note_placement.py --dry-run
  python3 scripts/batch/fix_salary_note_placement.py
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / 'skills' / 'gaokao-major-explorer' / 'data' / 'curated'

# 触发删除的关键词 (任一命中即视为纯错位 note)
DELETE_KEYWORDS = [
    '数据',          # 数据来源
    '估算',          # 数据估算
    '蓝皮书',        # 麦可思蓝皮书
    '麦可思',        # 数据源
    '一线',          # 应届分线 (一线/二三线)
    '二三线',        # 应届分线
    '县乡',          # 应届分线 (县乡/基层)
    '骨干',          # 段位说明 (研发骨干 10-15 万)
    '总监',          # 段位说明 (技术总监 20-32 万)
    '起薪',          # 段位说明 (起薪 X-Y 万)
    '起 薪',         # 容错空格
]


def is_senior_stage(stage_name: str) -> bool:
    return any(kw in stage_name for kw in ['10年', '资深', '高级', '专家', '合伙人', '管理层', '主编'])


def should_delete_note(note: str) -> bool:
    """判定 note 是否属纯错位可删类型"""
    return any(kw in note for kw in DELETE_KEYWORDS)


def fix_one(data: dict) -> tuple[int, list[str], list[str]]:
    """
    修一个 major dict.
    返回 (deleted_count, deleted_msgs, kept_msgs).
    """
    sal = data.get('salary', {})
    if not isinstance(sal, dict):
        return 0, [], []

    deleted = 0
    deleted_msgs: list[str] = []
    kept_msgs: list[str] = []

    for stage_name, vals in list(sal.items()):
        if not isinstance(vals, dict):
            continue
        note = vals.get('note')
        if not note:
            continue
        if is_senior_stage(stage_name):
            continue  # senior 不动
        # 非 senior 含 note → 检查是否可删
        if should_delete_note(note):
            del vals['note']
            deleted += 1
            deleted_msgs.append(f'{stage_name}: {note[:60]!r}')
        else:
            kept_msgs.append(f'{stage_name}: {note[:60]!r}')

    return deleted, deleted_msgs, kept_msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if not CURATED.exists():
        print(f'❌ curated 不存在: {CURATED}', file=sys.stderr)
        return 1

    files_modified = 0
    total_deleted = 0
    total_kept = 0

    for p in sorted(CURATED.glob('*.json')):
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            print(f'⚠️  {p.name}: JSON 解析失败 {e}', file=sys.stderr)
            continue

        deleted, dmsgs, kmsg = fix_one(data)
        if not deleted:
            total_kept += len(kmsg)
            continue

        for m in dmsgs:
            print(f'  🗑  {p.stem} :: {m}')

        if not args.dry_run:
            p.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

        files_modified += 1
        total_deleted += deleted
        total_kept += len(kmsg)

    print()
    print(f'── fix_salary_note_placement {"(DRY RUN)" if args.dry_run else ""} ──')
    print(f'  修改文件: {files_modified}')
    print(f'  删除 note: {total_deleted}')
    print(f'  保留 (手审): {total_kept}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
