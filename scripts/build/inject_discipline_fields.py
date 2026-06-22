#!/usr/bin/env python3
"""
scripts/inject_discipline_fields.py — 给 manifest + 74 curated JSON 加 discipline + sub_discipline 字段

提取策略:
1. 读 public/data/discipline_hierarchy.json, 建反向索引 (门类名→code, 专业类名→code)
2. 处理 public/data/manifest.json (有 category 字段,直接正则解析 "门类 · 专业类")
3. 处理 skills/.../curated/manifest.json (同上)
4. 处理 74 个 skills/.../curated/*.json (无 category, 用 slug 关联 manifest)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HIER = ROOT / "public/data/discipline_hierarchy.json"


def load_hierarchy():
    """读 hierarchy.json, 建反向索引"""
    hier = json.load(open(HIER, encoding="utf-8"))
    disc_name_to_code = {}  # "工学" → "08"
    sub_name_to_code = {}   # "电子信息类" → "0807"
    sub_name_to_disc = {}   # "电子信息类" → "08"
    for code, disc in hier["门类"].items():
        disc_name_to_code[disc["name"]] = code
        for sub_code, sub in disc["sub_classes"].items():
            sub_name_to_code[sub["name"]] = sub_code
            sub_name_to_disc[sub["name"]] = code
    return disc_name_to_code, sub_name_to_code, sub_name_to_disc


def parse_category(cat: str, disc_map, sub_map):
    """'工学 · 电子信息类' 或 '工学 · 机械类/交通运输类' 或 '工学 · 设计学类 (机械类交叉)' → (disc_code, sub_code)

    括号注释会被自动去除,多 sub 类取第一个匹配
    """
    if not cat:
        return None, None
    # 去掉括号注释 (机械类交叉)
    cat = re.sub(r'\s*\([^)]*\)\s*', '', cat).strip()
    parts = re.split(r'\s*·\s*', cat)
    if len(parts) != 2:
        return None, None
    disc_name, sub_part = parts
    disc_code = disc_map.get(disc_name)
    if not disc_code:
        return None, None
    # 多 sub 时取第一个
    for sub_name in sub_part.split('/'):
        sub_name = sub_name.strip()
        sub_code = sub_map.get(sub_name)
        if sub_code:
            return disc_code, sub_code
    return disc_code, None


def inject_manifest(path: Path, disc_map, sub_map):
    """处理 manifest 文件 (有 majors 数组 + 每个 entry 有 category)"""
    data = json.load(open(path, encoding="utf-8"))
    majors = data.get("majors", [])
    ok = partial = fail = 0
    for entry in majors:
        cat = entry.get("category", "")
        disc, sub = parse_category(cat, disc_map, sub_map)
        entry["discipline"] = disc
        entry["sub_discipline"] = sub
        if disc and sub:
            ok += 1
        elif disc:
            partial += 1
        else:
            fail += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return ok, partial, fail


def inject_curated_individual(curated_dir: Path, slug_to_codes, disc_map, sub_map):
    """处理 76 个 curated/*.json (含未上线/demos):
    1. 优先用 slug 关联 manifest
    2. fallback 用 category 字段直接解析
    """
    ok = partial = fail = 0
    failed_slugs = []
    for json_file in sorted(curated_dir.glob("*.json")):
        if json_file.name == "manifest.json" or json_file.name.endswith(".bak"):
            continue
        data = json.load(open(json_file, encoding="utf-8"))
        slug = data.get("slug")
        codes = slug_to_codes.get(slug)
        if codes and codes[0]:
            disc, sub = codes
            ok_count = 1 if disc and sub else (0.5 if disc else 0)
        else:
            # fallback: 用 category 字段直接解析
            cat = data.get("category", "")
            disc, sub = parse_category(cat, disc_map, sub_map)
        data["discipline"] = disc
        data["sub_discipline"] = sub
        if disc and sub:
            ok += 1
        elif disc:
            partial += 1
        else:
            fail += 1
            failed_slugs.append((slug, data.get("title", "")))
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return ok, partial, fail, failed_slugs


if __name__ == "__main__":
    disc_map, sub_map, _ = load_hierarchy()
    print(f"门类名 → code: {len(disc_map)} 个")
    print(f"专业类名 → code: {len(sub_map)} 个")
    print()

    # 1) 处理 manifest (权威源)
    manifest_public = ROOT / "public/data/manifest.json"
    manifest_curated = ROOT / "skills/gaokao-major-explorer/data/curated/manifest.json"

    print("=== Stage 1: 处理 manifest.json ===")
    for path in [manifest_public, manifest_curated]:
        ok, partial, fail = inject_manifest(path, disc_map, sub_map)
        total = ok + partial + fail
        print(f"  {path.relative_to(ROOT)}: OK={ok} partial={partial} fail={fail} (total {total})")

    # 2) 重建 slug → (disc, sub) 映射
    manifest_data = json.load(open(manifest_public, encoding="utf-8"))
    slug_to_codes = {}
    for e in manifest_data["majors"]:
        slug_to_codes[e["slug"]] = (e.get("discipline"), e.get("sub_discipline"))

    # 3) 处理 74 个 curated JSON
    print("\n=== Stage 2: 处理 curated/*.json (slug 关联 + category fallback) ===")
    curated_dir = ROOT / "skills/gaokao-major-explorer/data/curated"
    ok, partial, fail, failed_slugs = inject_curated_individual(curated_dir, slug_to_codes, disc_map, sub_map)
    print(f"  curated/*.json: OK={ok} partial={partial} fail={fail}")
    if failed_slugs:
        print(f"  仍未映射 ({len(failed_slugs)}):")
        for s, t in failed_slugs[:10]:
            print(f"    - slug='{s}' title='{t}'")
        if len(failed_slugs) > 10:
            print(f"    ... ({len(failed_slugs) - 10} more)")

    # 4) 验证
    print("\n=== Stage 3: 验证覆盖率 ===")
    all_curated = list(curated_dir.glob("*.json"))
    missing_disc = 0
    missing_sub = 0
    for jf in all_curated:
        if jf.name == "manifest.json":
            continue
        d = json.load(open(jf, encoding="utf-8"))
        if not d.get("discipline"):
            missing_disc += 1
        if not d.get("sub_discipline"):
            missing_sub += 1
    print(f"  curated/*.json: {len(all_curated) - 1} 个, 缺 discipline={missing_disc}, 缺 sub_discipline={missing_sub}")