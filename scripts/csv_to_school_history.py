"""
scripts/csv_to_school_history.py — 粤苏 admission CSV → school_history v2 (union 3 省)

输入:
  data/{province}_admission_{物理|历史}_2024.csv (粤苏)
  data/school_history.json (现湖北 4 年, 不动作为 baseline)
  data/groups_latest_{province}_2024.json (粤苏生成)

输出:
  data/school_history_v2.json = 现湖北 + 粤苏 2024 聚合 (deep-merge by school_id → type → year)

聚合算法:
  按 (school_id, type, year) group admission rows:
    - group_count: distinct sg_name 数
    - min_score: min(min_score)
    - max_score: max(min_score)
    - median_score: median(min_score)
    - min_rank: min(min_rank)
    - max_rank: max(min_rank)
    - median_rank: median(min_rank)

合并策略: priority hubei > guangdong > jiangsu (湖北数据已完整,不覆盖)
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"

TYPE_MAP = {"物理": "物理类", "历史": "历史类"}


def aggregate_csv(province: str, year: int, subject_cn: str, name_idx: dict) -> dict:
    """
    读 CSV → {school_id: {group_count, min/max/median_score, min/max/median_rank}}
    """
    csv_path = DATA_DIR / f"{province}_admission_{subject_cn}_{year}.csv"
    by_school = defaultdict(list)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                min_score = int(r.get("min_score") or 0)
                min_rank = int(r.get("min_rank") or 0)
            except (ValueError, TypeError):
                continue
            if min_score <= 0 or min_rank <= 0:
                continue
            school_name = r["school_name"].strip()
            sid = name_idx.get(school_name)
            if not sid:
                continue
            by_school[sid].append({
                "min_score": min_score,
                "min_rank": min_rank,
                "sg": r.get("group_code", r.get("group_id", "")).strip(),
            })

    out = {}
    for sid, rows in by_school.items():
        scores = [r["min_score"] for r in rows]
        ranks = [r["min_rank"] for r in rows]
        out[sid] = {
            "group_count": len(set(r["sg"] for r in rows)),
            "min_score": min(scores),
            "max_score": max(scores),
            "median_score": round(median(scores), 1),
            "min_rank": min(ranks),
            "max_rank": max(ranks),
            "median_rank": round(median(ranks), 1),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provinces", nargs="+", default=["guangdong", "jiangsu"],
                    choices=["guangdong", "jiangsu"])
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--out", type=Path, default=DATA_DIR / "school_history_v2.json")
    args = ap.parse_args()

    # Load baseline (湖北 4 年)
    baseline_path = DATA_DIR / "school_history.json"
    with open(baseline_path, "r", encoding="utf-8") as f:
        history = json.load(f)
    print(f"Baseline (湖北): {len(history)} schools")

    # Load colleges name index
    with open(DATA_DIR / "colleges.json", "r", encoding="utf-8") as f:
        colleges = json.load(f)
    name_idx = {c["name"]: c.get("school_id") or c.get("chsi_edu_id") for c in colleges}

    # Aggregate by province
    collision_count = 0
    for prov in args.provinces:
        print(f"\nAggregating {prov} {args.year}...")
        for subj_cn, subj_type in TYPE_MAP.items():
            agg = aggregate_csv(prov, args.year, subj_cn, name_idx)
            print(f"  {subj_type}: aggregated {len(agg)} schools")
            for sid, stats in agg.items():
                sid_key = str(sid)
                # 初始化
                if sid_key not in history:
                    history[sid_key] = {"物理类": {}, "历史类": {}}
                if subj_type not in history[sid_key]:
                    history[sid_key][subj_type] = {}
                # 检查 collision (湖北已存在该年数据)
                year_str = str(args.year)
                if year_str in history[sid_key][subj_type]:
                    collision_count += 1
                    # skip — 湖北数据优先
                    continue
                history[sid_key][subj_type][year_str] = stats

    print(f"\nCollisions (湖北优先, skipped): {collision_count}")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False)
    print(f"✅ Wrote {args.out}: {len(history)} schools")


if __name__ == "__main__":
    main()