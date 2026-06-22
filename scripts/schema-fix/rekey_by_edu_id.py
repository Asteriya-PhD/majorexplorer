"""Re-key 3 recommender data files by chsi_edu_id instead of school_id.

Inputs:
  - public/data/colleges.json (1008 schools, has chsi_edu_id from Step 2.2)
  - public/data/school_all_majors.json (128, keyed by school_id)
  - public/data/school_history.json (1008, keyed by school_id)
  - public/data/school_specialties.json (1004, keyed by school_id)

Outputs:
  - public/data/school_all_majors.json (re-keyed by edu_id)
  - public/data/school_history.json (re-keyed by edu_id, fallback prefix)
  - public/data/school_specialties.json (re-keyed by edu_id, fallback prefix)
  - data/raw/rekey_report.json (audit)

Fallback strategy (per plan §3 陷阱 4):
  - 9 中外合办独立学院 + 河北石油职业技术大学 = 9 schools without chsi_edu_id
  - Use prefix "sch_<school_id>" to distinguish from chsi edu_ids (5-digit numbers)

Plan §2 Step 3.4 (B 激进).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PUBLIC_DATA = ROOT / "public" / "data"
RAW_DIR = ROOT / "data" / "raw"

FILES = ["school_all_majors.json", "school_history.json", "school_specialties.json"]


def main():
    colleges = json.loads((PUBLIC_DATA / "colleges.json").read_text(encoding="utf-8"))
    sid_to_eid = {}
    fallback_sids = []
    for c in colleges:
        sid = c.get("school_id")
        eid = c.get("chsi_edu_id")
        if sid is None:
            continue
        if eid:
            sid_to_eid[str(sid)] = str(eid)
        else:
            fallback_sids.append((str(sid), c.get("name", "")))

    report = {
        "generated_at": int(time.time()),
        "sid_to_eid_count": len(sid_to_eid),
        "fallback_schools": [{"school_id": s, "name": n} for s, n in fallback_sids],
        "files": {},
    }

    for fname in FILES:
        path = PUBLIC_DATA / fname
        if not path.exists():
            print(f"⚠ {fname} not found, skip")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        old_keys = list(data.keys())
        new_data = {}
        mapped = 0
        fallback = 0
        for k in old_keys:
            if k in sid_to_eid:
                new_key = sid_to_eid[k]
                mapped += 1
            else:
                # Check if it's already a valid edu_id (numeric 5-digit)
                if k.isdigit() and len(k) == 5:
                    new_key = k
                    mapped += 1
                else:
                    # Fallback: prefix with sch_
                    new_key = f"sch_{k}"
                    fallback += 1
            new_data[new_key] = data[k]
        # Write
        path.write_text(json.dumps(new_data, ensure_ascii=False), encoding="utf-8")
        report["files"][fname] = {
            "old_count": len(old_keys),
            "mapped_to_eid": mapped,
            "fallback_prefixed": fallback,
            "new_count": len(new_data),
        }
        print(f"✓ {fname}: {len(old_keys)} → {len(new_data)} (mapped {mapped}, fallback {fallback})")

    (RAW_DIR / "rekey_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n=== rekey done: report → data/raw/rekey_report.json ===")
    print(f"  sid_to_eid mappings: {len(sid_to_eid)}")
    print(f"  fallback schools: {len(fallback_sids)}")
    for s, n in fallback_sids:
        print(f"    sch_{s}: {n}")


if __name__ == "__main__":
    main()