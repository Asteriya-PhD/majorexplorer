#!/usr/bin/env python3
"""Day 36 P1-24: 68 majors 缺 data_source 字段 → 批量回填 \"人工精编\".
"""
import json, glob, os

CURATED = "skills/gaokao-major-explorer/data/curated"
n_fixed = 0

for path in glob.glob(f"{CURATED}/*.json"):
    with open(path) as f:
        d = json.load(f)
    if d.get("data_source"):
        continue
    d["data_source"] = "人工精编"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    n_fixed += 1

print(f"✅ backfilled data_source: {n_fixed}")
