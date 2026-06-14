"""Bundle chsi major_detail raw files → public/data/chsi_major_details.json.

Input: data/raw/major_detail/{spec_id}.json (per-major chsi scraped detail)
Output: public/data/chsi_major_details.json (~30KB lightweight, browser-loadable)

Schema: { [major_name]: {
    spec_id, satisfaction,
    careers: [{name, occupation_id}, ...] (top 5),
    similar_majors: [name, ...] (top 5),
    opening_schools_count: int,
    top_opening_schools: [{name, satisfaction}, ...] (top 3),
    intro_excerpt: string (first 80 chars),
  } }

Used by Step 3.3 (灰 chip hover popover).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "major_detail"
OUT_F = ROOT / "public" / "data" / "chsi_major_details.json"

# name → spec_id mapping (from majors_list.json)
MAJORS_LIST = ROOT / "data" / "raw" / "majors_list.json"


def main():
    # Load name → spec_id from majors_list
    majors_list = json.loads(MAJORS_LIST.read_text(encoding="utf-8"))
    name_by_eid = {str(m.get("spec_id")): m.get("name", "") for m in majors_list if m.get("spec_id")}

    bundled = {}
    n_files = 0
    for f in RAW_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        n_files += 1
        name = d.get("name") or name_by_eid.get(f.stem) or ""
        if not name:
            continue
        # Extract fields
        careers_raw = d.get("career_directions") or []
        careers = []
        if isinstance(careers_raw, list):
            for c in careers_raw[:5]:
                if isinstance(c, dict):
                    careers.append(c.get("name", ""))
                else:
                    careers.append(str(c))
        similar = d.get("similar_majors") or []
        if isinstance(similar, list):
            similar = [str(s) for s in similar[:5]]
        schools_raw = d.get("opening_schools") or []
        schools = []
        if isinstance(schools_raw, list):
            for s in schools_raw[:3]:
                if isinstance(s, dict):
                    schools.append({"name": s.get("name", ""), "sat": s.get("satisfaction")})
        intro = d.get("introduction") or ""
        bundled[name] = {
            "spec_id": d.get("spec_id"),
            "satisfaction": d.get("satisfaction") or 0,
            "careers": careers,
            "similar_majors": similar,
            "opening_schools_count": d.get("opening_school_count") or len(schools_raw),
            "top_opening_schools": schools,
            "intro_excerpt": intro[:80] if intro else "",
        }

    OUT_F.write_text(json.dumps(bundled, ensure_ascii=False), encoding="utf-8")
    print(f"=== bundled chsi major details ===")
    print(f"  raw files: {n_files}")
    print(f"  bundled majors: {len(bundled)}")
    print(f"  → {OUT_F.relative_to(ROOT)}")
    import os
    print(f"  size: {os.path.getsize(OUT_F)} bytes ({os.path.getsize(OUT_F)/1024:.1f} KB)")


if __name__ == "__main__":
    main()