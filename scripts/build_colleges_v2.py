"""Build colleges_v2.json: merge 1008 colleges.json + 1968 chsi-only schools.

Output: public/data/colleges_v2.json
  - 1008 existing colleges (with chsi_edu_id from Step 2.2)
  - 1968 new chsi-only schools (synthesize school_id starting from 10001)

Plan §2 Step 3.4 (B 激进 v0 — 安全的实现):
  - 不动 school_all_majors / school_history / school_specialties / groups_latest
  - recommender 做双 lookup (edu_id 优先, school_id 兜底)
  - 9 中外合办独立学院 (8 在原 colleges, 1 河北石油) 保留 school_id, 不参与 chsi_edu_id 映射
"""

from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DATA = ROOT / "public" / "data"

OUT_F = PUBLIC_DATA / "colleges_v2.json"


def main():
    colleges = json.loads((PUBLIC_DATA / "colleges.json").read_text(encoding="utf-8"))
    chsi = json.loads((PUBLIC_DATA / "chsi_schools.json").read_text(encoding="utf-8"))

    # Existing colleges with chsi_edu_id mapping
    existing_by_eid = {c["chsi_edu_id"]: c for c in colleges if c.get("chsi_edu_id")}
    # existing_by_name for fuzzy match of chsi-only schools that may already be there
    existing_by_name = {c["name"]: c for c in colleges}

    # Next synthetic school_id (start from 10001 to avoid collision with existing 1-1200)
    next_sid = 10001
    used_sids = {c["school_id"] for c in colleges if c.get("school_id")}

    added = []
    skipped = 0
    for s in chsi:
        eid = str(s.get("edu_id") or "")
        if not eid:
            continue
        if eid in existing_by_eid:
            skipped += 1
            continue
        name = (s.get("name") or "").strip()
        # synthesize school_id
        while next_sid in used_sids:
            next_sid += 1
        sid = next_sid
        used_sids.add(sid)
        next_sid += 1
        # Normalize fields to colleges.json schema (subset)
        new_college = {
            "school_id": sid,
            "name": name,
            "province": s.get("province") or "",
            "city": "",
            "county": "",
            "type": "",
            "nature": "",
            "f985": 0,
            "f211": 0,
            "dual_class": "",
            "level": "本科" if s.get("degree") == "本科" else (s.get("degree") or ""),
            "tier": s.get("tier") or "",
            "chsi_edu_id": eid,
            "chsi_name_match": name,
            "chsi_governing": s.get("governing") or "",
            "chsi_satisfaction": s.get("satisfaction") or 0,
            "chsi_only": True,  # marker: not in original colleges.json
        }
        added.append(new_college)
        existing_by_eid[eid] = new_college  # also register to avoid future dups

    colleges_v2 = colleges + added
    OUT_F.write_text(json.dumps(colleges_v2, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"=== colleges_v2.json built ===")
    print(f"  original colleges: {len(colleges)}")
    print(f"  chsi-only added: {len(added)}")
    print(f"  skipped (already in colleges): {skipped}")
    print(f"  total: {len(colleges_v2)}")
    print(f"  → {OUT_F.relative_to(ROOT)}")
    # Sample
    print(f"\n=== sample of 5 added ===")
    for c in added[:5]:
        print(f"  school_id={c['school_id']} edu_id={c['chsi_edu_id']} {c['name']} ({c['province']}, {c['chsi_governing']})")


if __name__ == "__main__":
    main()