"""chsi 校名归一化 + join key.

Inputs:
  - public/data/colleges.json       (1008 schools, school_id)
  - public/data/chsi_schools.json   (2950 schools, edu_id)

Output:
  - public/data/colleges.json       (add chsi_edu_id, chsi_name_match)
  - public/data/chsi_schools.json   (add aliases)
  - docs/chsi-name-normalize-report.md

Strategy (per plan §1 Step 2.2):
  1. Full-width → half-width brackets (（） → ())
  2. Strip (xxx) suffix for matching (but preserve as alias)
  3. Known alias map (military + medical college renames)
  4. Multi-match: keep all (per plan §3 陷阱 2 — chsi lists them separately)

Plan §3 陷阱 4: 9 中外合办独立学院 (西南财特拉华 / 安徽大纽约石溪 etc) are NOT in chsi.
These 9 should keep college-fallback (no chsi_edu_id).

Run:
  python3 scripts/chsi_name_normalize.py
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DATA = ROOT / "public" / "data"
DOCS = ROOT / "docs"

COLLEGES_F = PUBLIC_DATA / "colleges.json"
CHSI_F = PUBLIC_DATA / "chsi_schools.json"
REPORT_F = DOCS / "chsi-name-normalize-report.md"


def norm_full(s: str) -> str:
    """全角→半角括号 + strip whitespace"""
    return s.replace("（", "(").replace("）", ")").strip()


def norm_strip_bracket(s: str) -> str:
    """Strip (xxx) / (xxx校区) / (xxx分校) suffix, keep base name."""
    return re.sub(r"[（(].*?[)）]", "", s).strip()


# Known alias (colleges.json name → chsi name)
KNOWN_ALIAS = {
    "复旦大学上海医学院": "复旦大学医学院",  # 院校合并改名
    "中国人民解放军陆军军医大学": "陆军军医大学",
    "中国人民解放军海军军医大学": "海军军医大学",
    "中国人民解放军空军军医大学": "空军军医大学",
    "第二军医大学": "海军军医大学",
    "第三军医大学": "陆军军医大学",
    "第四军医大学": "空军军医大学",
}


def make_variants(name: str) -> list[str]:
    """Generate all name variants for matching, preserving order of preference."""
    seen = []
    for v in [name, norm_full(name), norm_strip_bracket(name), norm_strip_bracket(norm_full(name))]:
        if v and v not in seen:
            seen.append(v)
    return seen


def main():
    colleges = json.loads(COLLEGES_F.read_text(encoding="utf-8"))
    chsi = json.loads(CHSI_F.read_text(encoding="utf-8"))

    # Build chsi lookup by all name variants
    chsi_by_name: dict[str, list[dict]] = {}
    for s in chsi:
        for v in make_variants(s.get("name", "")):
            chsi_by_name.setdefault(v, []).append(s)

    # Track join results
    matched: list[dict] = []  # {college_name, chsi_edu_id, chsi_name, strategy}
    conflicts: list[dict] = []  # one college → many chsi
    unmatched: list[str] = []  # colleges with no chsi match

    # Step 1: match colleges → chsi
    for c in colleges:
        cname = (c.get("name") or "").strip()
        if not cname:
            continue
        # Apply known alias first
        targets = [KNOWN_ALIAS.get(cname, cname)]
        for variant in make_variants(cname):
            if variant not in targets:
                targets.append(variant)
        # For each variant, find chsi match
        found: list[dict] = []
        strategy = None
        for t in targets:
            if t in chsi_by_name:
                found = chsi_by_name[t]
                strategy = t if t != cname else "exact"
                break
        if not found:
            unmatched.append(cname)
            continue
        edu_id = str(found[0].get("edu_id") or "")
        matched.append({
            "college_name": cname,
            "chsi_edu_id": edu_id,
            "chsi_name": found[0].get("name", ""),
            "strategy": strategy,
            "n_candidates": len(found),
        })
        if len(found) > 1:
            conflicts.append({
                "college_name": cname,
                "chsi_names": [f.get("name", "") for f in found],
            })
        # Write back to college
        c["chsi_edu_id"] = edu_id
        c["chsi_name_match"] = found[0].get("name", "")

    # Step 2: add aliases to chsi_schools.json for the matched schools
    # (Alias = any other name variant that successfully joined to this chsi entry)
    alias_map: dict[str, set[str]] = {}
    for m in matched:
        # If the college name differs from the chsi name, record as alias
        if m["college_name"] != m["chsi_name"]:
            alias_map.setdefault(m["chsi_edu_id"], set()).add(m["college_name"])

    for s in chsi:
        eid = str(s.get("edu_id") or "")
        if eid in alias_map:
            s["aliases"] = sorted(alias_map[eid])

    # Step 3: write outputs (use multi-line for cleaner git diff; original was one-line)
    COLLEGES_F.write_text(
        json.dumps(colleges, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    CHSI_F.write_text(
        json.dumps(chsi, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Step 4: build report
    matched_count = len(matched)
    unmatched_count = len(unmatched)
    total = len(colleges)
    hit_pct = 100 * matched_count / max(1, total)
    by_strategy = {}
    for m in matched:
        s = m["strategy"]
        # classify strategy into category
        if s == "exact":
            cat = "exact"
        elif m["college_name"] != m["chsi_name"]:
            cat = "normalized"
        else:
            cat = "other"
        by_strategy[cat] = by_strategy.get(cat, 0) + 1

    report = f"""# chsi 校名归一化报告 (Step 2.2)

**生成时间**: {time.strftime("%Y-%m-%d %H:%M:%S")}

## 命中率

| 指标 | 值 |
|---|---|
| 总 colleges | {total} |
| 已 join chsi | {matched_count} |
| 未 join (fallback colleges) | {unmatched_count} |
| **命中率** | **{hit_pct:.1f}%** ({matched_count}/{total}) |
| 多对一冲突 | {len(conflicts)} |

## 归一策略分布

| 策略 | 数量 |
|---|---|
"""
    for cat, n in sorted(by_strategy.items(), key=lambda x: -x[1]):
        report += f"| {cat} | {n} |\n"

    report += f"""
## 已 normal 命中 (colleges 命名微差)

| college 名 | chsi 名 | 策略 |
|---|---|---|
"""
    norm_hits = [m for m in matched if m["college_name"] != m["chsi_name"]]
    for m in norm_hits[:30]:
        report += f"| {m['college_name']} | {m['chsi_name']} | `{m['strategy']}` |\n"
    if len(norm_hits) > 30:
        report += f"| ... 及其他 {len(norm_hits) - 30} 个 |\n"

    report += f"""
## 未命中 ({len(unmatched)} 个, 计划作为 colleges fallback)

chsi 没有收录, 必须 fallback 到 colleges.json (per 计划 §3 陷阱 4):

| college 名 | 推测类别 |
|---|---|
"""
    for n in unmatched:
        report += f"| {n} | 中外合办 / 独立学院 |\n"

    if conflicts:
        report += f"""
## 冲突 (1 college → 多个 chsi 候选)

chsi 把 (北京)/(武汉) 等括号校当独立学校, 保留为多对一 (per 计划 §3 陷阱 2):

| college 名 | chsi 候选 |
|---|---|
"""
        for c in conflicts[:10]:
            report += f"| {c['college_name']} | {', '.join(c['chsi_names'])} |\n"
        if len(conflicts) > 10:
            report += f"| ... 及其他 {len(conflicts) - 10} 个 |\n"

    report += f"""
## 文件改动

| 文件 | 状态 |
|---|---|
| `public/data/colleges.json` | 加 `chsi_edu_id` + `chsi_name_match` 字段 |
| `public/data/chsi_schools.json` | 加 `aliases` 字段 |

## Plan

§1 Step 2.2 (1-2h, 估时实际 < 5min). 目标命中率 ≥ 999/1008.
"""

    DOCS.mkdir(parents=True, exist_ok=True)
    REPORT_F.write_text(report, encoding="utf-8")

    print(f"=== name normalize done ===")
    print(f"  total colleges: {total}")
    print(f"  matched: {matched_count} ({hit_pct:.1f}%)")
    print(f"  unmatched: {unmatched_count}")
    print(f"  conflicts: {len(conflicts)}")
    print(f"  strategy: {by_strategy}")
    print(f"  → {REPORT_F.relative_to(ROOT)}")


if __name__ == "__main__":
    main()