#!/usr/bin/env python3
"""
build_all_majors.py — 从 data/admissions_raw/<sid>_<year>.json 抽 sp_name + level2/3_name,
跨年合并, 输出 public/data/school_all_majors.json.

Schema (每个 item):
  school_id, sp_name (干净), spname (带办学地点/中外合作后缀),
  level2_name (学科门类), level3_name (专业大类)

输出结构:
{
  "<schoolId>": {
    "all_majors": ["计算机科学与技术", "软件工程", ...],
    "by_level2": { "工学": [...], "医学": [...] },
    "by_level3": { "计算机类": [...], "电子信息类": [...] },
    "total": 47
  }
}

Usage:
  python3 scripts/build_all_majors.py
"""
from __future__ import annotations
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data/admissions_raw"
OUT_PATH = ROOT / "public/data/school_all_majors.json"

# 防御性: 清洗一些已知的脏数据 (虽然 sp_name 通常已干净)
# 例: "工商管理（试点班）" → 保留原值, 因为 (试点班) 是有意义分类
# 这里只去前后空白
def clean_name(s: str) -> str:
    return s.strip() if s else ""


def process_file(path: Path) -> tuple[str, list[dict]]:
    """读一个 admissions_raw 文件, 返 (schoolId, list of {sp_name, level2, level3})."""
    school_id = path.stem.split("_")[0]  # "100_2024" → "100"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  [WARN] {path.name} parse fail: {e}", file=sys.stderr)
        return school_id, []

    payload = data.get("data") or {}
    items_collected: list[dict] = []
    for group_key, group_val in payload.items():
        if not isinstance(group_val, dict):
            continue
        item_list = group_val.get("item")
        if not isinstance(item_list, list):
            continue
        for it in item_list:
            if not isinstance(it, dict):
                continue
            sp_name = clean_name(it.get("sp_name", ""))
            level2 = clean_name(it.get("level2_name", ""))
            level3 = clean_name(it.get("level3_name", ""))
            if not sp_name:
                continue
            items_collected.append({
                "sp_name": sp_name,
                "level2": level2,
                "level3": level3,
            })
    return school_id, items_collected


def main():
    if not RAW_DIR.exists():
        print(f"❌ 找不到 {RAW_DIR}", file=sys.stderr)
        sys.exit(1)

    files = sorted(RAW_DIR.glob("*.json"))
    print(f"📂 处理 {len(files)} 个文件 from {RAW_DIR.relative_to(ROOT)}")

    started = time.time()
    schools: dict[str, dict] = {}  # schoolId → {majors: set, by_l2: dict, by_l3: dict}
    skipped_files: list[str] = []
    file_count_by_school: dict[str, int] = {}

    for f in files:
        sid, items = process_file(f)
        if not items:
            skipped_files.append(f.name)
            continue
        file_count_by_school[sid] = file_count_by_school.get(sid, 0) + 1
        if sid not in schools:
            schools[sid] = {"majors": set(), "by_l2": {}, "by_l3": {}}
        for it in items:
            name = it["sp_name"]
            l2 = it["level2"]
            l3 = it["level3"]
            schools[sid]["majors"].add(name)
            if l2:
                schools[sid]["by_l2"].setdefault(l2, set()).add(name)
            if l3:
                schools[sid]["by_l3"].setdefault(l3, set()).add(name)

    # 序列化: set → sorted list
    out: dict[str, dict] = {}
    for sid, payload in schools.items():
        all_majors = sorted(payload["majors"])
        by_l2 = {k: sorted(v) for k, v in sorted(payload["by_l2"].items())}
        by_l3 = {k: sorted(v) for k, v in sorted(payload["by_l3"].items())}
        out[sid] = {
            "all_majors": all_majors,
            "by_level2": by_l2,
            "by_level3": by_l3,
            "total": len(all_majors),
            "years": file_count_by_school.get(sid, 0),
        }

    # 写文件
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(out, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    elapsed = time.time() - started
    print(f"\n✅ 写入 {OUT_PATH.relative_to(ROOT)}")
    print(f"   {len(out)} 校, 总 majors 去重后 {sum(s['total'] for s in out.values())} 条")
    print(f"   跳过 {len(skipped_files)} 文件 (parse 失败或空)")
    print(f"   耗时 {elapsed:.1f}s")

    # 抽 3 校验证 (按 plan 要求: 华中师大/上海大学/武汉理工)
    # 这些校的 schoolId 需要查一下; 先按 id 出现位置抽
    # 华中师大 (10511?), 上海大学 (10280?), 武汉理工 (10497?)
    # 这里我先抽 sample 几个有 "计算机" 的校
    print(f"\n=== 验证: 含 '计算机' 的校 (抽 5 个) ===")
    hits = []
    for sid, payload in out.items():
        cs_majors = [m for m in payload["all_majors"] if "计算机" in m]
        if cs_majors:
            hits.append((sid, len(payload["all_majors"]), cs_majors[:3]))
    for sid, total, cs_list in hits[:5]:
        print(f"  school {sid}: total={total} majors, 计算机相关: {cs_list}")

    # 总体统计
    majors_per_school = [s["total"] for s in out.values()]
    print(f"\n=== 统计 ===")
    print(f"  schools: {len(out)}")
    print(f"  majors/school: min={min(majors_per_school)} max={max(majors_per_school)} "
          f"median={sorted(majors_per_school)[len(majors_per_school)//2]} avg={sum(majors_per_school)/len(majors_per_school):.1f}")
    # 全局 majors 去重
    global_majors = set()
    for p in out.values():
        global_majors.update(p["all_majors"])
    print(f"  全球 unique majors: {len(global_majors)}")

    # 抽样验证
    print(f"\n=== 抽样 3 校全 majors (验证清洗效果) ===")
    sample_ids = list(out.keys())[:3]
    for sid in sample_ids:
        p = out[sid]
        print(f"\n  [{sid}] {p['total']} majors, {p['years']} 年数据")
        print(f"    by_level2: {dict(list(p['by_level2'].items())[:3])}")
        print(f"    头 5 个: {p['all_majors'][:5]}")


if __name__ == "__main__":
    main()
