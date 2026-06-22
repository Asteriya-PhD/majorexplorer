#!/usr/bin/env python3
"""Batch fix top_companies string→dict schema across curated JSONs.

Skips intelligent-marine-equipment (already hand-fixed).
For each remaining major with top_companies as list[str]:
  - Convert to {name, tier, headcount, salary, sparkline}
  - tier: S if 中央/央企/国企/部委/国家, A if 500强/上市/头部, else B
  - name: first segment before "(" or "/" (main entity)
  - salary: rest of string (parenthetical subsidiaries / context)
  - headcount: ★★★★★ if S, ★★★★ if A, ★★★ else
  - sparkline: default [3,3,4,4,4]
"""
import json, glob, os, re, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CURATION = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"
PUBLIC = ROOT / "public"

SKIP = {"intelligent-marine-equipment"}

TIER_S = r"中央|央企|国企|部委|国家|国务院|中国\s*\w*集团|中国\s*\w*院|中国\s*\w*部"
TIER_A = r"500\s*强|上市|头部|龙头|知名"
HEADCOUNT_S = "★★★★★"
HEADCOUNT_A = "★★★★"
HEADCOUNT_B = "★★★"
DEFAULT_SPARK = [3, 3, 4, 4, 4]
GROW_SPARK = [3, 4, 5, 5, 5]


def split_name(raw: str):
    """Split '中国船舶集团（江南造船、外高桥造船）' → ('中国船舶集团', '江南造船、外高桥造船')."""
    s = raw.strip()
    m = re.match(r"^([^（(]+)([（(].*)$", s)
    if m:
        return m.group(1).strip(), m.group(2).strip("（()").strip()
    if "/" in s:
        parts = s.split("/", 1)
        return parts[0].strip(), parts[1].strip()
    return s, ""


def infer_tier(name: str, salary: str) -> str:
    text = name + " " + salary
    if re.search(TIER_S, text):
        return "S"
    if re.search(TIER_A, text):
        return "A"
    return "B"


def convert_one(raw: str) -> dict:
    name, rest = split_name(raw)
    tier = infer_tier(name, rest)
    headcount = {"S": HEADCOUNT_S, "A": HEADCOUNT_A, "B": HEADCOUNT_B}[tier]
    sparkline = GROW_SPARK if tier in ("S", "A") else DEFAULT_SPARK
    salary_text = rest if rest else raw
    return {
        "name": name,
        "tier": tier,
        "headcount": headcount,
        "salary": salary_text,
        "sparkline": sparkline,
    }


def main():
    fixed = 0
    skipped = 0
    files = sorted(glob.glob(str(CURATION / "*.json")))
    for f in files:
        slug = Path(f).stem
        if slug in SKIP:
            skipped += 1
            continue
        try:
            d = json.load(open(f))
        except Exception as e:
            print(f"  ! {slug}: load failed {e}")
            continue
        tc = d.get("top_companies", [])
        if not tc:
            continue
        # Already dicts?
        if all(isinstance(c, dict) for c in tc):
            skipped += 1
            continue
        # Has strings → convert
        new_tc = []
        for c in tc:
            if isinstance(c, str):
                new_tc.append(convert_one(c))
            else:
                new_tc.append(c)
        d["top_companies"] = new_tc
        json.dump(d, open(f, "w"), ensure_ascii=False, indent=2)
        print(f"  ✓ {slug}: {len(new_tc)} companies converted")
        fixed += 1
    print(f"\nFixed: {fixed}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
