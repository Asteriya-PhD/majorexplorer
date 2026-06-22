#!/usr/bin/env python3
"""backfill_missing_evaluations.py — 一次性补全 synth 漏填的 rank 评估数据

Day 17 全量审计发现 4 个专业 JSON 里无教育部第四/五轮评估数据 (但实际公开有):

| 专业 | sub | 应有评估 | 数据来源 |
|------|-----|---------|---------|
| statistics 统计学 | 0712 | A+/A/A-/B+ (北大/人大/南开/厦大/华东师大/...) | 教育部第四轮 |
| drug-control 禁毒学 | 0306 | A+/A-/B+/B (公大/刑警学院/政法/华政) | 教育部第四轮 (归侦查学/公安学大类) |
| maternal-child-health-medicine 妇幼保健医学 | 1004 | A+/A-/B+/B (复旦/华科/北大/中山/...) | 教育部第四轮 |
| apiculture 蜂学 | 0903 | A+/A-/B+ (中农/浙大/南农/西北农林/华农) | 教育部第四轮 |

数据格式: canonical "★★★★★ (A+)" (5 颗实心 + 括号字母).

用法:
  python3 scripts/backfill_missing_evaluations.py --dry-run  # 预览
  python3 scripts/backfill_missing_evaluations.py             # 写回
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURATED_DIR = ROOT / "skills/gaokao-major-explorer/data/curated"

# Eval → stars 映射 (canonical "★★★★★ (A+)" 用 5 颗实心)
EVAL_TO_STAR = {"A+": "★★★★★", "A": "★★★★★", "A-": "★★★★☆",
                "B+": "★★★★☆", "B": "★★★☆☆", "B-": "★★★☆☆",
                "C+": "★★☆☆☆", "C": "★☆☆☆☆", "C-": "★☆☆☆☆", "D": "☆☆☆☆☆"}


# 4 个专业补全数据 (school_name → eval_letter)
BACKFILL_DATA = {
    "statistics": {
        "北京大学": "A+", "中国人民大学": "A+", "南开大学": "A",
        "厦门大学": "A-", "华东师范大学": "A-", "东北师范大学": "B+",
        "上海财经大学": "B+", "中国科学技术大学": "B+",
    },
    "drug-control": {
        "中国人民公安大学": "A+", "中国刑事警察学院": "A-",
        "中国政法大学": "B+", "华东政法大学": "B",
    },
    "maternal-child-health-medicine": {
        "复旦大学": "A+", "华中科技大学": "A+", "北京大学": "A-",
        "中山大学": "A-", "南京医科大学": "B+", "哈尔滨医科大学": "B+",
        "首都医科大学": "B", "南方医科大学": "B",
    },
    "apiculture": {
        "中国农业大学": "A+", "浙江大学": "A-", "南京农业大学": "A-",
        "西北农林科技大学": "B+", "华中农业大学": "B+",
    },
}


def normalize_existing(rank, tag=""):
    """检查现有 rank 是否已有有效评估数据"""
    if isinstance(rank, int): return False
    r = str(rank).strip() if rank else ""
    if re.fullmatch(r"([ABCDF][+\-]?)", r): return True
    if re.search(r"\(([ABCDF][+\-]?)\)", r): return True
    if 0 < r.count("★") <= 5: return True
    if re.search(r"([ABCDF][+\-]?)", tag or ""): return True
    return False


def backfill_file(slug, eval_data, dry_run=False):
    """backfill 单个 JSON, 返回变更列表"""
    json_path = CURATED_DIR / f"{slug}.json"
    if not json_path.exists():
        print(f"⚠️  {json_path} 不存在, 跳过")
        return []
    data = json.loads(json_path.read_text(encoding="utf-8"))
    schools = data.get("top_schools", [])
    changes = []
    for s in schools:
        name = s.get("name", "")
        old_rank = s.get("rank", "")
        old_tag = s.get("tag", "")
        # 已有效评估 → 跳过 (保留现有数据, 避免覆盖)
        if normalize_existing(old_rank, old_tag):
            continue
        # 查找匹配的学校
        # 精确匹配优先, 然后 prefix 匹配 (e.g. "中国人民公安大学" 包含 "公安大学")
        ev = eval_data.get(name)
        if not ev:
            for key, val in eval_data.items():
                if name.startswith(key) or key.startswith(name) or key in name or name in key:
                    ev = val
                    break
        if not ev:
            changes.append({"name": name, "status": "no_match", "old": old_rank})
            continue
        star = EVAL_TO_STAR.get(ev, "★★★★★")
        new_rank = f"{star} ({ev})"
        changes.append({"name": name, "status": "fixed", "old": old_rank, "new": new_rank})
        if not dry_run:
            s["rank"] = new_rank
    if not dry_run and changes:
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"📂 扫描 4 个漏填专业 (教育部第四轮评估数据)")
    if args.dry_run:
        print("   DRY-RUN, 不写回 JSON\n")
    for slug, eval_data in BACKFILL_DATA.items():
        print(f"\n📝 {slug}:")
        changes = backfill_file(slug, eval_data, dry_run=args.dry_run)
        for c in changes:
            if c["status"] == "fixed":
                print(f"  ✅ {c['name']:20} {repr(c['old'])[:15]:15} → {c['new']}")
            else:
                print(f"  ⚠️  {c['name']:20} (无匹配评估数据, 保留现状)")


if __name__ == "__main__":
    main()