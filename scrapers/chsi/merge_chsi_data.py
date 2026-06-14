"""Merge chsi raw data into public/data/ JSON files (non-destructive).

Reads:
  - data/raw/schools_list.json       (2950 chsi schools)
  - data/raw/majors_list.json        (868 chsi majors)
  - data/raw/school_detail/*.json    (per-school detail, if available)
  - public/data/colleges.json        (existing 1008 schools — used for join stats)

Writes:
  - public/data/chsi_schools.json    (2950 schools merged with detail-page fields)
  - public/data/chsi_majors.json     (868 majors)
  - public/data/chsi_merge_report.json (summary stats: coverage, overlap, gaps)

Non-destructive: never mutates existing `colleges.json` or `school_all_majors.json`.
Frontend can opt in to chsi_schools / chsi_majors when ready.

Run: scrapers/chsi/.venv/bin/python scrapers/chsi/merge_chsi_data.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data" / "raw"
PUBLIC_DATA = ROOT / "public" / "data"


def load_json(p: Path) -> object | None:
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    schools_list = load_json(RAW_DIR / "schools_list.json") or []
    majors_list = load_json(RAW_DIR / "majors_list.json") or []
    existing = load_json(PUBLIC_DATA / "colleges.json") or []
    detail_dir = RAW_DIR / "school_detail"

    # Load all detail files, keyed by edu_id
    details_by_eduid: dict[str, dict] = {}
    if detail_dir.exists():
        for f in detail_dir.glob("*.json"):
            d = load_json(f)
            if d and d.get("edu_id"):
                details_by_eduid[str(d["edu_id"])] = d

    # Merge: for each chsi school, attach detail fields if present
    merged_schools = []
    for s in schools_list:
        edu_id = str(s.get("edu_id") or "")
        det = details_by_eduid.get(edu_id, {})
        # Detail page fields override list fields where both present (more authoritative)
        merged = {**s, **{k: v for k, v in det.items() if k not in {"sch_id", "edu_id", "name", "detail_url"}}}
        merged_schools.append(merged)

    # Join stats vs existing colleges.json — by school NAME (existing uses internal
    # school_id 1-1200, chsi uses edu_id 10001+; only the name is comparable.)
    existing_by_name = {(c.get("name") or "").strip(): c for c in existing}
    chsi_names = {(s.get("name") or "").strip() for s in merged_schools}
    matched_in_existing = sum(1 for n in chsi_names if n in existing_by_name)
    chsi_only = len(chsi_names) - matched_in_existing
    existing_only = sum(1 for n in existing_by_name if n not in chsi_names)

    # Subset by degree
    by_degree: dict[str, int] = {}
    for s in merged_schools:
        d = s.get("degree") or "未知"
        by_degree[d] = by_degree.get(d, 0) + 1

    # Major stats
    majors_by_menjia: dict[str, int] = {}
    for m in majors_list:
        k = m.get("menjia_moe") or "?"
        majors_by_menjia[k] = majors_by_menjia.get(k, 0) + 1

    report = {
        "generated_at": int(time.time()),
        "chsi_schools_total": len(merged_schools),
        "chsi_schools_with_detail": len([s for s in merged_schools if s.get("address")]),
        "chsi_schools_with_detail_pct": round(
            100 * len([s for s in merged_schools if s.get("address")]) / max(1, len(merged_schools)), 1
        ),
        "chsi_majors_total": len(majors_list),
        "chsi_majors_with_intro": sum(1 for m in majors_list if m.get("has_intro")),
        "existing_colleges_total": len(existing),
        "join_matched": matched_in_existing,
        "join_chsi_only": chsi_only,
        "join_existing_only": existing_only,
        "by_degree": by_degree,
        "majors_by_menjia": majors_by_menjia,
    }

    PUBLIC_DATA.mkdir(parents=True, exist_ok=True)
    (PUBLIC_DATA / "chsi_schools.json").write_text(
        json.dumps(merged_schools, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PUBLIC_DATA / "chsi_majors.json").write_text(
        json.dumps(majors_list, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PUBLIC_DATA / "chsi_merge_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("=== chsi merge report ===")
    for k, v in report.items():
        print(f"  {k:35} {v}")


if __name__ == "__main__":
    main()
