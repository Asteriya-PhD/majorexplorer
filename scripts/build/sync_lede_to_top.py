#!/usr/bin/env python3
"""Day 36 P1-1: 553/625 lede 顶层 null → 从 overview_v2.lede 同步到顶层 lede.
一次跑完, idempotent.
"""
import json, glob, os

CURATED = "skills/gaokao-major-explorer/data/curated"
n_fixed = n_skipped = n_missing = 0

for path in glob.glob(f"{CURATED}/*.json"):
    slug = os.path.basename(path).replace(".json", "")
    with open(path) as f:
        try:
            d = json.load(f)
        except Exception:
            continue
    top_lede = d.get("lede")
    ov2 = d.get("overview_v2") or {}
    ov2_lede = ov2.get("lede") if isinstance(ov2, dict) else None

    if top_lede and isinstance(top_lede, str) and top_lede.strip():
        n_skipped += 1
        continue
    if not ov2_lede or not isinstance(ov2_lede, str) or not ov2_lede.strip():
        n_missing += 1
        continue
    d["lede"] = ov2_lede
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    n_fixed += 1

print(f"✅ synced top-level lede: {n_fixed}")
print(f"⏭️  already had lede: {n_skipped}")
print(f"⚠️  no overview_v2.lede to source from: {n_missing}")
