#!/usr/bin/env python3
"""repair_top_schools_rank.py — 一次性修复所有 curated JSON 的 top_schools.rank 字段格式

Day 17 反向治理: render_mobile.py 的 normalize_rank() 已兜底所有格式 (运行时),
但 synth 阶段会持续产出新 major, 长期应统一 JSON 数据本身, 让渲染端无需兼容.

## 规整规则 (canonical format):

| 输入 | 修复为 | 原因 |
|------|-------|------|
| `"A+"` / `"A"` / `"A-"` / `"B+"` (bare letter) | `"★★★★★ (A+)"` 等 (5★ + letter) | 显式星级 + 字母, 信息密度最高 |
| `"★★★★★ (A+)"` (星+括号) | 不变 | 已 canonical |
| `"★★★★★"` (纯星) | 不变 | 已 canonical (render 端映射) |
| `tag` 含 `A+` 但 rank 空 | 提取 tag 字母 → `"★★★★☆ (A+)"` (4★) | 4★ 表明"无精确评估, 仅 tag 提及" |
| `1` / `2` / `3` (int 序号) | `""` (空字符串) | 序号不是评估, 不假装有数据, render 显示 "—" |
| `""` / `None` / 缺字段 | `""` | 同上 |

## 用法:

```bash
# Dry-run, 只看不改
python3 scripts/repair_top_schools_rank.py --dry-run

# 真跑
python3 scripts/repair_top_schools_rank.py

# 指定单个文件
python3 scripts/repair_top_schools_rank.py skills/gaokao-major-explorer/data/curated/business-administration.json
```
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURATED_DIR = ROOT / "skills/gaokao-major-explorer/data/curated"

# Star → eval 映射 (5 颗实心 ★ → A+, 0 → B-)
STAR_TO_EVAL = ["B-", "B", "B+", "A-", "A", "A+"]
# Eval → stars 映射 (canonical "★★★★★ (A+)" 用 5 颗实心)
EVAL_TO_STAR = {"A+": "★★★★★", "A": "★★★★★", "A-": "★★★★☆",
                "B+": "★★★★☆", "B": "★★★☆☆", "B-": "★★★☆☆",
                "C+": "★★☆☆☆", "C": "★☆☆☆☆", "C-": "★☆☆☆☆", "D": "☆☆☆☆☆"}

# 5 策略 canonical 化
def to_canonical(rank, tag=""):
    """返回 (canonical_string, change_type). change_type: 'kept'/'fixed'/'cleared'"""
    # 空
    if rank is None or rank == "":
        # 兜底用 tag
        m = re.search(r"\b([ABCDF][+\-]?)\b", tag or "")
        if m:
            ev = m.group(1)
            star = EVAL_TO_STAR.get(ev, "★★★★☆")
            return f"{star} ({ev})", "fixed_from_tag"
        return "", "kept_empty"
    # int 序号
    if isinstance(rank, int):
        return "", "cleared_int"
    rank = str(rank).strip()
    # 纯字母 → 5★+括号
    m = re.fullmatch(r"([ABCDF][+\-]?)", rank)
    if m:
        ev = m.group(1)
        return f"{EVAL_TO_STAR.get(ev, '★★★★★')} ({ev})", "fixed_bare_letter"
    # 星+括号 → 不变
    if re.search(r"\(([ABCDF][+\-]?)\)", rank):
        return rank, "kept_parens"
    # 纯星 → 不变 (render 端映射)
    if "★" in rank:
        return rank, "kept_stars"
    # tag 兜底
    m = re.search(r"\b([ABCDF][+\-]?)\b", tag or "")
    if m:
        ev = m.group(1)
        star = EVAL_TO_STAR.get(ev, "★★★★☆")
        return f"{star} ({ev})", "fixed_from_tag"
    return rank, "kept_other"


def repair_file(json_path, dry_run=False):
    """修复单个 JSON 文件的 top_schools.rank 字段, 返回变更列表."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    schools = data.get("top_schools", [])
    if not schools:
        return []
    changes = []
    for i, s in enumerate(schools):
        old = s.get("rank", "")
        tag = s.get("tag", "")
        new, change_type = to_canonical(old, tag)
        if new != str(old) if old is not None else new != "":
            changes.append({
                "idx": i,
                "name": s.get("name", ""),
                "old": old,
                "new": new,
                "type": change_type,
            })
            if not dry_run and change_type != "kept_empty":
                s["rank"] = new
    if changes and not dry_run:
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changes


def main():
    ap = argparse.ArgumentParser(description="修复 curated JSON 的 top_schools.rank 字段")
    ap.add_argument("--dry-run", action="store_true", help="只看不改")
    ap.add_argument("files", nargs="*", help="指定文件 (默认全部 curated/*.json)")
    args = ap.parse_args()

    # 收集目标文件
    if args.files:
        targets = [Path(f) for f in args.files]
    else:
        targets = sorted(CURATED_DIR.glob("*.json"))

    # 统计
    total_files = 0
    total_changes = 0
    type_counts = {}

    print(f"📂 扫描 {len(targets)} 个 JSON ...")
    for path in targets:
        if not path.exists():
            print(f"⚠️  {path}: 不存在")
            continue
        changes = repair_file(path, dry_run=args.dry_run)
        if changes:
            total_files += 1
            total_changes += len(changes)
            for c in changes:
                type_counts[c["type"]] = type_counts.get(c["type"], 0) + 1
            if args.dry_run:
                print(f"\n📝 {path.name} ({len(changes)} 处变更):")
                for c in changes[:5]:  # 最多显示 5 处
                    print(f"  [{c['idx']}] {c['name'][:20]}: {repr(c['old'])[:30]} → {repr(c['new'])[:30]} ({c['type']})")
                if len(changes) > 5:
                    print(f"  ... +{len(changes)-5} more")

    mode = "DRY-RUN" if args.dry_run else "DONE"
    print(f"\n========== [{mode}] ==========")
    print(f"📁 扫描文件: {len(targets)}")
    print(f"📝 变更文件: {total_files}")
    print(f"✏️  总变更: {total_changes}")
    if type_counts:
        print(f"\n变更类型分布:")
        for t, n in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {t}: {n}")
    if args.dry_run:
        print(f"\n💡 真跑: python3 {__file__}")
    else:
        print(f"\n✅ 已写回 JSON. 下次 render_mobile.py 跑会用新数据.")


if __name__ == "__main__":
    main()