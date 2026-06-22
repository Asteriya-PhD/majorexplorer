#!/usr/bin/env python3
"""
A.3 18 字段 schema 缺失检查: 只报告, 不改

Usage:
  python3 scripts/check_schema_gaps.py
"""
import json
import sys
from pathlib import Path
from collections import Counter

CURATED = Path("skills/gaokao-major-explorer/data/curated")
REPORT_PATH = Path("data/schema_gaps.json")

# 实际 schema 字段 (per JSON sample 050104/050107/050108)
REQUIRED_FIELDS = [
    "title",
    "slug",
    "style",
    "category",
    "degree",
    "duration_years",
    "tags",
    "difficulty",
    "summary",
    "hero_quote",
    "hero_quote_sig",
    "lede",
    "overview_v2",
    "curriculum",
    "top_schools",
    "top_companies",
    "salary",
    "employment_direction",
    "alumni_quotes",
    "xuanke_req_list",
]


def main():
    files = sorted(CURATED.glob("*.json"))
    gap_records = []
    field_counter = Counter()

    for f in files:
        try:
            with f.open() as fp:
                data = json.load(fp)
        except Exception:
            gap_records.append({"slug": f.stem, "error": "JSON parse failed"})
            continue

        missing = []
        for field in REQUIRED_FIELDS:
            v = data.get(field)
            if v is None or v == "":
                if field == "overview_v2":
                    if "overview_v2" not in data and "overview" not in data:
                        missing.append(field)
                    continue
                missing.append(field)
                continue
            # list/dict empty check
            if isinstance(v, (list, dict)) and len(v) == 0:
                missing.append(f"{field} (empty)")

        if missing:
            for m in missing:
                clean = m.split(" ")[0]
                field_counter[clean] += 1
            gap_records.append({"slug": f.stem, "missing": missing})

    print(f"扫 {len(files)} 篇, gaps {len(gap_records)} 篇")
    print(f"By field: {dict(field_counter)}")
    print(f"\n样例 (前 15):")
    for r in gap_records[:15]:
        print(f"  {r['slug']:40s} missing: {r['missing']}")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w") as f:
        json.dump(
            {
                "total_files": len(files),
                "total_gaps": len(gap_records),
                "by_field": dict(field_counter),
                "records": gap_records,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\nReport → {REPORT_PATH}")


if __name__ == "__main__":
    main()