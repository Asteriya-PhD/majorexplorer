#!/usr/bin/env python3
"""
fix_manifest_discipline.py — 修 manifest.majors[*].discipline 字段缺失的 bug.

历史 bug: upsert_manifest_minimal() (scf/synth/manifest_ops.py:129) 不传 discipline,
导致所有 batch_synth 出来的 56 精品都缺 discipline 字段.
discipline 是 majors.html 2 层 chip + chsi diff 报告 + 覆盖率统计的核心.

修法:
  1. 从 public/data/discipline_hierarchy.json 推每个 title → discipline code 映射
  2. 遍历 manifest.majors, 凡 discipline 字段空 + title 匹配的, 自动 inject
  3. 双 manifest 同步 (public/data/manifest.json + skills/gaokao-major-explorer/data/curated/manifest.json)
  4. 二次保险: title 匹配不上时, 记 list 提示人工修 (罕见, 主要是老 baseline 用 category 推测)

用法:
  python3 scripts/fix_manifest_discipline.py              # 全量修
  python3 scripts/fix_manifest_discipline.py --dry-run   # 只看不写
  python3 scripts/fix_manifest_discipline.py --slug primary-education  # 单跑
"""
import argparse, json, pathlib, re, sys

ROOT = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp")
HIER = ROOT / "public/data/discipline_hierarchy.json"
MANIFESTS = [
    ROOT / "public/data/manifest.json",
    ROOT / "skills/gaokao-major-explorer/data/curated/manifest.json",
]


def build_title_to_discipline(hier):
    """从 discipline_hierarchy.json 构建 title → discipline_code 映射 (7xL 子类粒度)."""
    out = {}  # title → (code, sub_code)
    for code, info in hier["门类"].items():
        for sub_code, sub in info.get("sub_classes", {}).items():
            for major in sub.get("majors", []):
                # 用 norm title 匹配 (去括号 / 全角空格)
                norm = major.strip()
                if norm in out:
                    continue  # 第一个 sub_class 命中, 跨 sub_class 重名暂忽略
                out[norm] = (code, sub_code)
    return out


def lookup_title(title, mapping):
    """title 模糊匹配, 处理 (XX类) / 全角空格 / 法学缩写 等小变种."""
    if not title:
        return None
    if title in mapping:
        return mapping[title]
    # 去除括号注解
    t = re.sub(r"\s*[（(].*?[)）]\s*", "", title).strip()
    if t in mapping:
        return mapping[t]
    # 全角空格 → 半角
    t2 = t.replace("　", " ")
    if t2 in mapping:
        return mapping[t2]
    # 法学类硬映射 (Batch 1 早期 slug, hierarchy 0301 不全)
    LAW_HARDMAP = {
        "国际法": ("03", "0301"),
        "民法": ("03", "0301"),
        "经济法": ("03", "0301"),
        "商法": ("03", "0301"),
        "行政法": ("03", "0301"),
        "民事诉讼法": ("03", "0301"),
        "刑事诉讼法": ("03", "0301"),
        "刑事法学": ("03", "0301"),
        "禁毒学": ("03", "0306"),  # 公安学类 (gongan 主题)
    }
    if t2 in LAW_HARDMAP:
        return LAW_HARDMAP[t2]
    # sub-string: title 包含 hierarchy 的某 major 全名
    for hier_title, codes in mapping.items():
        if len(hier_title) >= 3 and hier_title in t2:
            return codes
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只看不写")
    ap.add_argument("--slug", help="单跑一个 slug")
    args = ap.parse_args()

    hier = json.loads(HIER.read_text(encoding="utf-8"))
    title_map = build_title_to_discipline(hier)
    print(f"📚 hierarchy 推得 {len(title_map)} 个 title → (disc, sub_disc) 映射")

    targets = MANIFESTS
    total_fixed, total_remaining = 0, []
    for mp in targets:
        m = json.loads(mp.read_text(encoding="utf-8"))
        fixed_here = 0
        for entry in m["majors"]:
            if args.slug and entry["slug"] != args.slug:
                continue
            if entry.get("discipline"):
                continue  # 已有
            hit = lookup_title(entry.get("title", ""), title_map)
            if hit:
                disc, sub = hit
                entry["discipline"] = disc
                entry["sub_discipline"] = sub
                fixed_here += 1
            else:
                total_remaining.append((entry["slug"], entry.get("title", "")))
        if fixed_here:
            print(f"  ✏️  {mp.relative_to(ROOT)}: {fixed_here} 个补 discipline")
        else:
            print(f"  ✓  {mp.relative_to(ROOT)}: 0 (已同)")
        if not args.dry_run:
            mp.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
        total_fixed += fixed_here

    print(f"\n汇总: 补 {total_fixed} 个 discipline 字段")
    if total_remaining:
        uniq = sorted(set(total_remaining))
        print(f"未匹配 (title 在 hierarchy 没找到, 需人工): {len(uniq)} 个")
        for s, t in uniq[:10]:
            print(f"  · {s:30s} '{t}'")
        if len(uniq) > 10:
            print(f"  ... +{len(uniq) - 10} more")


if __name__ == "__main__":
    main()
