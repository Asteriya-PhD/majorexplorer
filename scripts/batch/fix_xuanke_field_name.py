#!/usr/bin/env python3
"""
fix_xuanke_field_name.py — Day 50 A.1 FIELD-3 批量修

xuanke_req_list 里某项是 dict 但缺 `name` 字段, 实际是 subject/combo/item/course 之一.
修法: 按 subject/combo/item/course 顺序找第一个别名 alias, 重命名为 `name`,
      保留原字段 (向后兼容, renderer 已 defensive normalize).

用法:
  python3 scripts/batch/fix_xuanke_field_name.py --dry-run  # 仅统计, 不写
  python3 scripts/batch/fix_xuanke_field_name.py             # 真跑 (写盘)

退出码: 0 成功 / 1 有错误
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / 'skills' / 'gaokao-major-explorer' / 'data' / 'curated'

# 别名查找顺序 (按优先级)
ALIAS_ORDER = ['subject', 'combo', 'item', 'course']


def fix_one(data: dict) -> tuple[bool, list[str]]:
    """
    修一个 major dict. 返回 (modified, changes).
    changes 是描述字符串列表, 给人读.
    """
    xuanke = data.get('xuanke_req_list')
    if not isinstance(xuanke, list):
        return False, []

    changes: list[str] = []
    modified = False
    for i, item in enumerate(xuanke):
        if not isinstance(item, dict):
            continue
        if 'name' in item:
            continue
        # 找第一个 alias
        for alias in ALIAS_ORDER:
            if alias in item and isinstance(item[alias], (str, int, float)):
                item['name'] = str(item[alias])
                changes.append(f'xuanke[{i}]: {alias} → name ({item["name"][:40]!r})')
                modified = True
                break
        else:
            # 找不到任何 alias, 跳过
            changes.append(f'xuanke[{i}]: 缺 name 也无别名 (实际字段: {list(item.keys())})')

    return modified, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='只统计不写盘')
    args = ap.parse_args()

    if not CURATED.exists():
        print(f'❌ curated 目录不存在: {CURATED}', file=sys.stderr)
        return 1

    modified_files = 0
    total_changes = 0
    skipped = 0

    for p in sorted(CURATED.glob('*.json')):
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            print(f'⚠️  {p.name}: JSON 解析失败 {e}', file=sys.stderr)
            continue

        modified, changes = fix_one(data)
        if not modified:
            continue

        # 过滤掉"找不到别名"的 (它们不改)
        real_changes = [c for c in changes if '→' in c]
        skipped_changes = [c for c in changes if '→' not in c]

        if not real_changes:
            if skipped_changes:
                print(f'  ⏭️  {p.stem}: {len(skipped_changes)} 项无别名可改')
                skipped += len(skipped_changes)
            continue

        print(f'  ✏️  {p.stem}: {len(real_changes)} 项')
        for c in real_changes:
            print(f'      - {c}')

        if not args.dry_run:
            p.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
        modified_files += 1
        total_changes += len(real_changes)
        skipped += len(skipped_changes)

    print()
    print(f'── fix_xuanke_field_name {"(DRY RUN)" if args.dry_run else ""} ──')
    print(f'  修改文件: {modified_files}')
    print(f'  改名次数: {total_changes}')
    print(f'  跳过 (无别名): {skipped}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
