"""
scripts/convert_yfyd.py — 一分一段表 → yfyd JSON 转换器

输入格式 (CSV 或 JSON 任选):
  CSV:  score,rank,count (与 guangdong_rank_*.csv 一致)
  JSON: [{score:..., rank:..., count:...}, ...]  或 {"wuli": [...], "lishi": [...]}

输出格式 (与 data/yfyd_2025.json schema 一致):
  {
    "year": 2026,
    "province": "广东",
    "source": "<来源 URL 或公告标题>",
    "wuli": {"subject_type": "物理类", "rows": [{score, rank, count}, ...]},
    "lishi": {"subject_type": "历史类", "rows": [...]}
  }

用法:
  # 单文件 (广东 2026 物理)
  python3 scripts/convert_yfyd.py \
    --wuli data/guangdong_rank_物理_2026.csv \
    --lishi data/guangdong_rank_历史_2026.csv \
    --year 2026 \
    --province 广东 \
    --source "广东省教育考试院 2026 一分一段表 (eea.gd.gov.cn)" \
    --out data/yfyd_guangdong_2026.json

  # 合并到主 yfyd_2026.json (湖北 + 广东 同年)
  python3 scripts/convert_yfyd.py \
    --wuli data/hubei_rank_物理_2026.csv \
    --lishi data/hubei_rank_历史_2026.csv \
    --province 湖北 \
    --source "..." \
    --merge-into data/yfyd_2026.json
"""
import argparse
import csv
import json
import sys
from pathlib import Path


def _parse_score(raw: str) -> int:
    """Parse score field. Supports ranges like '695-750' → midpoint 722 (top scorers bucket)."""
    raw = raw.strip()
    if "-" in raw:
        parts = raw.split("-")
        try:
            lo, hi = int(parts[0]), int(parts[1])
            return (lo + hi) // 2
        except ValueError:
            pass
    return int(raw)


def load_csv(path: Path) -> list[dict]:
    """Load score,rank,count CSV → [{score:int, rank:int, count:int}] sorted desc by score."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                rows.append({
                    "score": _parse_score(r["score"]),
                    "rank": int(r["rank"]),
                    "count": int(r.get("count", 0)),
                })
            except (ValueError, KeyError) as e:
                print(f"⚠️  skip row {r}: {e}", file=sys.stderr)
    # Sort desc by score (highest score first)
    rows.sort(key=lambda x: -x["score"])
    return rows


def load_json(path: Path) -> list[dict]:
    """Load JSON list or {wuli/lishi: [...]} dict."""
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    if isinstance(d, list):
        return d
    if isinstance(d, dict) and "rows" in d:
        return d["rows"]
    raise ValueError(f"Unknown JSON shape in {path}")


def load_any(path: Path) -> list[dict]:
    """Auto-detect CSV vs JSON."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv(path)
    if suffix == ".json":
        return load_json(path)
    # Try CSV first, fallback JSON
    try:
        return load_csv(path)
    except Exception:
        return load_json(path)


def main():
    ap = argparse.ArgumentParser(description="一分一段 → yfyd JSON 转换器")
    ap.add_argument("--wuli", type=Path, required=True, help="物理类一分一段 (CSV 或 JSON)")
    ap.add_argument("--lishi", type=Path, required=True, help="历史类一分一段 (CSV 或 JSON)")
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--province", type=str, required=True, help="省份中文名 (广东/湖北/江苏)")
    ap.add_argument("--source", type=str, required=True, help="数据源描述 (公告标题/URL)")
    ap.add_argument("--out", type=Path, help="输出独立 yfyd JSON 路径")
    ap.add_argument("--merge-into", type=Path, help="合并入已有 yfyd JSON (按 province 区分字段)")
    args = ap.parse_args()

    wuli_rows = load_any(args.wuli)
    lishi_rows = load_any(args.lishi)

    # Validate rank monotonicity (rank must be non-decreasing as score decreases)
    for name, rows in [("wuli", wuli_rows), ("lishi", lishi_rows)]:
        prev_rank = 0
        for r in rows:
            if r["rank"] < prev_rank:
                print(f"⚠️  {name} rank regressed: {prev_rank} → {r['rank']} at score {r['score']}", file=sys.stderr)
            prev_rank = r["rank"]

    yfyd_doc = {
        "year": args.year,
        "province": args.province,
        "source": args.source,
        "wuli": {"subject_type": "物理类", "rows": wuli_rows},
        "lishi": {"subject_type": "历史类", "rows": lishi_rows},
    }

    if args.merge_into:
        # Merge into multi-province yfyd file (结构: {year, sources: {prov: source}, provinces: {prov: {wuli, lishi}}})
        merge_path: Path = args.merge_into
        if merge_path.exists():
            with open(merge_path, "r", encoding="utf-8") as f:
                merged = json.load(f)
        else:
            merged = {"year": args.year, "sources": {}, "provinces": {}}
        merged.setdefault("year", args.year)
        merged.setdefault("sources", {})
        merged.setdefault("provinces", {})
        merged["year"] = args.year
        merged["sources"][args.province] = args.source
        merged["provinces"][args.province] = {
            "wuli": yfyd_doc["wuli"],
            "lishi": yfyd_doc["lishi"],
        }
        merge_path.parent.mkdir(parents=True, exist_ok=True)
        with open(merge_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"✅ Merged {args.province} → {merge_path}")
        print(f"   wuli: {len(wuli_rows)} rows, lishi: {len(lishi_rows)} rows")
        return

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(yfyd_doc, f, ensure_ascii=False, indent=2)
        print(f"✅ Wrote {args.out}")
        print(f"   wuli: {len(wuli_rows)} rows, lishi: {len(lishi_rows)} rows")
        return

    # Default: stdout
    json.dump(yfyd_doc, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()