"""Re-key groups_latest.json: each group record's school_id → edu_id (or sch_<sid> fallback).

Plan §2 Step 3.4 v1 (B 激进完整版).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PUBLIC_DATA = ROOT / "public" / "data"

OUT_F = PUBLIC_DATA / "groups_latest.json"


def main():
    colleges = json.loads((PUBLIC_DATA / "colleges.json").read_text(encoding="utf-8"))
    sid_to_key = {}
    for c in colleges:
        sid = str(c.get("school_id") or "")
        eid = c.get("chsi_edu_id")
        if sid:
            sid_to_key[sid] = str(eid) if eid else f"sch_{sid}"

    gl = json.loads(OUT_F.read_text(encoding="utf-8"))
    total_mapped = 0
    total_fallback = 0
    unmapped_sids = set()
    for bucket in ("wuli", "lishi"):
        records = gl.get(bucket) or []
        for r in records:
            sid = str(r.get("school_id") or "")
            if sid in sid_to_key:
                new_key = sid_to_key[sid]
                if new_key.startswith("sch_"):
                    total_fallback += 1
                else:
                    total_mapped += 1
                r["_legacy_school_id"] = int(sid) if sid.isdigit() else sid
                r["school_id"] = new_key
            else:
                unmapped_sids.add(sid)
                # Keep as is

    OUT_F.write_text(json.dumps(gl, ensure_ascii=False), encoding="utf-8")
    print(f"=== groups_latest rekey done ===")
    print(f"  mapped to edu_id: {total_mapped}")
    print(f"  fallback sch_<sid>: {total_fallback}")
    print(f"  unmapped sids: {len(unmapped_sids)}")
    if unmapped_sids:
        for s in list(unmapped_sids)[:10]:
            print(f"    {s}")


if __name__ == "__main__":
    main()