"""Add menjia_moe field to manifest.json 精品 majors.

Inputs:
  - public/data/manifest.json (95 精品)
  - public/data/chsi_majors.json (868 chsi majors, has menjia_moe)

Output:
  - public/data/manifest.json (with new menjia_moe + menjia_name fields)

Auto-map: title match (86/95)
Manual fallback: 9 unmatched (法学 sub-styles + 师范 + 新闻传播)
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PUBLIC_DATA = ROOT / "public" / "data"

MANIFEST_F = PUBLIC_DATA / "manifest.json"
CHSI_MAJORS_F = PUBLIC_DATA / "chsi_majors.json"

# 门类代码 → 名称
MENJIA_NAMES = {
    "01": "哲学",
    "02": "经济学",
    "03": "法学",
    "04": "教育学",
    "05": "文学",
    "06": "历史学",
    "07": "理学",
    "08": "工学",
    "09": "农学",
    "10": "医学",
    "12": "管理学",
    "13": "艺术学",
    "14": "交叉学科",
}

# 手工映射 (title → menjia_moe): 9 unmatched
MANUAL_MENJIA = {
    "师范教育 (数学/语文/英语 等)": "04",  # 教育学
    "新闻传播学": "05",  # 文学
    "经济法": "03",
    "民法": "03",
    "商法": "03",
    "行政法": "03",
    "民事诉讼法": "03",
    "刑事诉讼法": "03",
    "刑事法学": "03",
}


def main():
    manifest = json.loads(MANIFEST_F.read_text(encoding="utf-8"))
    chsi = json.loads(CHSI_MAJORS_F.read_text(encoding="utf-8"))

    # Build title → menjia_moe map from chsi
    by_name = {}
    for m in chsi:
        if m.get("name") and m.get("menjia_moe"):
            by_name[m["name"]] = m["menjia_moe"]

    majors = manifest.get("majors", [])
    auto = manual = unmatched = 0
    for m in majors:
        title = m.get("title", "")
        # Try auto first
        menjia = by_name.get(title)
        if menjia:
            auto += 1
        elif title in MANUAL_MENJIA:
            menjia = MANUAL_MENJIA[title]
            manual += 1
        else:
            unmatched += 1
            menjia = None
        if menjia:
            m["menjia_moe"] = menjia
            m["menjia_name"] = MENJIA_NAMES.get(menjia, menjia)

    MANIFEST_F.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"=== manifest menjia_moe updated ===")
    print(f"  total: {len(majors)}")
    print(f"  auto-mapped: {auto}")
    print(f"  manual-mapped: {manual}")
    print(f"  unmatched: {unmatched}")
    if unmatched:
        for m in majors:
            if "menjia_moe" not in m:
                print(f"    ⚠ unmatched: {m.get('title')}")

    # Distribution
    from collections import Counter
    dist = Counter(m.get("menjia_moe") for m in majors)
    print(f"\n  门类分布:")
    for k in sorted(dist.keys()):
        print(f"    {k} {MENJIA_NAMES.get(k, '?')}: {dist[k]}")


if __name__ == "__main__":
    main()