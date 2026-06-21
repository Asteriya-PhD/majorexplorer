#!/usr/bin/env python3
"""
A.2 Schema 漂移统一: 旧 key → 新 key + list[str] → list[dict]

Usage:
  python3 scripts/normalize_schema.py         # dry-run
  python3 scripts/normalize_schema.py --apply  # 实际改
"""
import json
import sys
from pathlib import Path
from collections import Counter

CURATED = Path("skills/gaokao-major-explorer/data/curated")
REPORT_PATH = Path("data/schema_drift.json")

RENAMES = {
    "通用专业核心": "通用专业核心 (≈ 80% 院校覆盖)",
    "公共必修": "公共必修 (所有院校都开)",
    "5 校特色选修": "5 校特色选修 (按方向分流)",
}


def normalize_curriculum(cur):
    """curriculum dict: rename keys + convert list[str] to list[{name, credit}]."""
    if not isinstance(cur, dict):
        return cur, 0
    changes = 0
    new_cur = {}
    for k, v in cur.items():
        new_k = RENAMES.get(k, k)
        if new_k != k:
            changes += 1
        # If v is list[str], convert to list[{name, credit}]
        if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
            v = [{"name": x, "credit": 0} for x in v]
            changes += len(v)
        new_cur[new_k] = v
    return new_cur, changes


def main():
    apply_mode = "--apply" in sys.argv
    files = sorted(CURATED.glob("*.json"))
    drift_records = []
    rename_counter = Counter()
    list_conv_counter = 0

    for f in files:
        try:
            with f.open() as fp:
                data = json.load(fp)
        except Exception:
            continue

        cur = data.get("curriculum")
        if not isinstance(cur, dict):
            continue

        old_keys = set(cur.keys())
        new_cur, changes = normalize_curriculum(cur)
        if changes == 0:
            continue

        if apply_mode:
            data["curriculum"] = new_cur
            with f.open("w") as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)

        for k in old_keys:
            if k in RENAMES:
                rename_counter[RENAMES[k]] += 1
        drift_records.append(
            {
                "slug": f.stem,
                "old_keys": [k for k in old_keys if k in RENAMES],
                "new_keys": [RENAMES[k] for k in old_keys if k in RENAMES],
                "changes": changes,
            }
        )

    print(f"扫 {len(files)} 篇, drift {len(drift_records)} 篇")
    print(f"By renamed key: {dict(rename_counter)}")
    print(f"\n样例 (前 10):")
    for r in drift_records[:10]:
        print(
            f"  {r['slug']:40s} {r['old_keys']} → {r['new_keys']} (changes={r['changes']})"
        )

    if not apply_mode:
        print(f"\n[DRY-RUN] 加 --apply 实际改")
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with REPORT_PATH.open("w") as f:
            json.dump(
                {
                    "total_files": len(files),
                    "total_drift": len(drift_records),
                    "by_rename": dict(rename_counter),
                    "records": drift_records,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"[DRY-RUN] Report → {REPORT_PATH}")
        return

    print(f"\n[APPLIED] 改 {len(drift_records)} 篇")


if __name__ == "__main__":
    main()