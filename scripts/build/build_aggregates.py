#!/usr/bin/env python3
"""
build_aggregates.py — 从 3 个真相源聚合 1 个小 JSON (运行时只用它)

真相源 (git tracked):
  - public/data/manifest.json              ← curated list (601 majors)
  - public/data/discipline_hierarchy.json  ← 教育部 13/92/880 框架
  - public/data/chsi_majors.json           ← 868 chsi pool + 阳光高考评分

派生:
  - public/data/aggregates.json  (~3KB, runtime 唯一 fetch 源)
      totals { menjia_count, subclass_count, major_count, curated_count, html_count, chsi_rated_count }
      by_menjia { code: { name, pool, curated, html, pct } }
      coverage_pct, updated_at, version

用法:
  python3 scripts/build/build_aggregates.py             # 写文件
  python3 scripts/build/build_aggregates.py --check     # 只检查不写 (CI 用)
  python3 scripts/build/build_aggregates.py --stats     # 打印人类可读 summary

防退化:
  - 任何 hardcoded "13"/"92"/"880+"/"457+" 在 HTML pre-commit 时 reject
  - aggregates.json 时间戳必须 >= manifest.json 时间戳
"""
from __future__ import annotations
import argparse
import datetime
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "public" / "data" / "manifest.json"
HIERARCHY = ROOT / "public" / "data" / "discipline_hierarchy.json"
CHSI = ROOT / "public" / "data" / "chsi_majors.json"
PUBLIC_HTML = ROOT / "public"
OUT = ROOT / "public" / "data" / "aggregates.json"

# 系统页 (不算 curated 也不影响门类数)
SYSTEM_PAGES = {
    "index.html", "majors.html", "404.html",
    "account.html", "favorites.html", "compare.html", "sitemap.html",
    "disclaimer.html", "manifest.html", "offline.html",
    "preferences.html", "privacy.html", "recommendations.html",
    "search.html", "strategy.html",
}


def load_sources():
    if not MANIFEST.exists():
        sys.exit(f"❌ {MANIFEST} 不存在")
    if not HIERARCHY.exists():
        sys.exit(f"❌ {HIERARCHY} 不存在")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hier = json.loads(HIERARCHY.read_text(encoding="utf-8"))
    chsi = json.loads(CHSI.read_text(encoding="utf-8")) if CHSI.exists() else []
    return manifest, hier, chsi


def build_title_to_menjia(hier: dict) -> dict[str, str]:
    """title → 真实 menjia_code (Day 24 fix: 反查 hierarchy)."""
    out = {}
    for code, d in (hier.get("门类") or {}).items():
        for sc in (d.get("sub_classes") or {}).values():
            for name in (sc.get("majors") or []):
                out[name] = code
    return out


def build_html_index(manifest_slugs: set[str]) -> tuple[set[str], set[str]]:
    """扫 public/*.html, 返 (existing_slug_set, phantom_slug_set)."""
    existing, phantom = set(), set()
    for f in PUBLIC_HTML.glob("*.html"):
        if f.name in SYSTEM_PAGES:
            continue
        stem = f.stem
        if stem in manifest_slugs:
            existing.add(stem)
        else:
            phantom.add(stem)
    return existing, phantom


def parse_baseline(hier: dict) -> dict:
    """从 hierarchy.frame 解析教育部 PDF 基线数字 (13/92/880+38).

    hierarchy 是 '教学版' 只列代表性专业 (676), 基线走 frame 字段.
    """
    frame = hier.get("frame", "") or ""
    out = {"menjia_baseline": 13, "subclass_baseline": 92,
           "major_baseline": 880, "new_2026": 38, "source": "frame"}
    m = re.search(r"(\d+)\s*学科门类", frame)
    if m: out["menjia_baseline"] = int(m.group(1))
    m = re.search(r"(\d+)\s*专业类", frame)
    if m: out["subclass_baseline"] = int(m.group(1))
    m = re.search(r"[~约]?\s*(\d+)\s*种本科专业", frame)
    if m: out["major_baseline"] = int(m.group(1))
    m = re.search(r"新增\s*(\d+)", frame)
    if m: out["new_2026"] = int(m.group(1))
    return out


def build(manifest: dict, hier: dict, chsi: list) -> dict:
    majors = manifest.get("majors") or []
    slug_set = {m["slug"] for m in majors}
    title_to_menjia = build_title_to_menjia(hier)
    html_existing, phantom_slugs = build_html_index(slug_set)
    baseline = parse_baseline(hier)

    # 各门类 curated (按 title 反查 hierarchy; orphan fallback 到 menjia_moe)
    menjia_curated: dict[str, int] = defaultdict(int)
    orphan_titles: list[str] = []
    for m in majors:
        title = m["title"]
        slug = m["slug"]
        code = title_to_menjia.get(title) or m.get("menjia_moe") or ""
        # 14 交叉学科不算 13 官方门类, 独立 bucket
        if code and code not in (hier.get("门类") or {}):
            code = "14"  # 统一
        if code:
            menjia_curated[code] += 1
        else:
            orphan_titles.append(title)
    if orphan_titles:
        print(f"⚠️  {len(orphan_titles)} 个 major 既不在 hierarchy 也没有 menjia_moe, "
              f"归到 14: {orphan_titles[:5]}")

    # HTML 按 menjia 分桶
    menjia_html: dict[str, int] = defaultdict(int)
    for slug in html_existing:
        m = next((x for x in majors if x["slug"] == slug), None)
        if not m:
            continue
        code = title_to_menjia.get(m["title"]) or m.get("menjia_moe") or ""
        if code and code not in (hier.get("门类") or {}):
            code = "14"
        if code:
            menjia_html[code] += 1

    # 各门类 pool (hierarchy 内列出的专业总数) + sub-class 数
    menjia_pool: dict[str, int] = defaultdict(int)
    menjia_subclass_count: dict[str, int] = defaultdict(int)
    menjia_pool_named: dict[str, int] = defaultdict(int)
    by_menjia: dict[str, dict] = {}
    menjia_block = hier.get("门类") or {}
    for code, d in sorted(menjia_block.items()):
        subs = d.get("sub_classes") or {}
        sub_n = len(subs)
        major_n = 0
        for sc in subs.values():
            major_n += len(sc.get("majors") or [])
        menjia_pool[code] = major_n
        menjia_subclass_count[code] = sub_n
        cur = menjia_curated.get(code, 0)
        html_n = menjia_html.get(code, 0)
        # pct: curated / pool (Day 24 截断: 显示用 min 避免视觉异常, 但 JSON 写真值)
        pct = round(100 * cur / major_n, 1) if major_n > 0 else 0.0
        by_menjia[code] = {
            "name": d.get("name", ""),
            "pool": major_n,
            "subclass_count": sub_n,
            "curated": cur,
            "html": html_n,
            "pct": pct,
        }

    # 14 交叉学科独立 bucket (hierarchy 没有, 但 manifest 有)
    if "14" in menjia_curated or "14" in menjia_html:
        by_menjia["14"] = {
            "name": "交叉学科",
            "pool": 0,  # hierarchy 无
            "subclass_count": 0,
            "curated": menjia_curated.get("14", 0),
            "html": menjia_html.get("14", 0),
            "pct": 0.0,
        }

    # 阳光高考评分覆盖
    chsi_rated = sum(1 for x in chsi if isinstance(x.get("satisfaction"), (int, float)))

    # 顶层 totals — major_count 用教育部基线 (frame 解析, 880), 不是 hierarchy 教学版 676
    # menjia_count: hierarchy 官方门类数 = 13 (排除 14 交叉独立桶)
    official_menjia_block = {c: d for c, d in menjia_block.items() if c in {"01","02","03","04","05","06","07","08","09","10","11","12","13"}}
    totals = {
        "menjia_count": len(official_menjia_block),         # 13
        "menjia_with_cross": len(menjia_block),            # 14 (含交叉)
        "subclass_count": baseline["subclass_baseline"],   # 92 (frame parse)
        "major_count": baseline["major_baseline"],         # 880 (frame parse)
        "major_count_hierarchy": sum(menjia_pool.values()),# 676 (教学版实际列出)
        "new_2026": baseline["new_2026"],                  # 38
        "curated_count": len(majors),                      # manifest
        "html_count": len(html_existing),
        "phantom_html_count": len(phantom_slugs),
        "system_html_count": sum(1 for f in PUBLIC_HTML.glob("*.html") if f.name in SYSTEM_PAGES),
        "chsi_rated_count": chsi_rated,
    }
    totals["coverage_pct"] = round(
        100 * totals["curated_count"] / totals["major_count"], 1
    ) if totals["major_count"] > 0 else 0.0
    totals["html_coverage_pct"] = round(
        100 * totals["html_count"] / totals["curated_count"], 1
    ) if totals["curated_count"] > 0 else 0.0

    # 静态 human description (build 时生成, runtime 不算)
    desc = (
        f"教育部《普通高等学校本科专业目录》全量: "
        f"{totals['menjia_count']} 学科门类 / {totals['subclass_count']} 专业类 / "
        f"~{totals['major_count']} 种本科专业 (2026 新增 {totals['new_2026']} 种). "
        f"我们已为 {totals['curated_count']} 主流专业写了深度精品报告 "
        f"({totals['coverage_pct']}% 覆盖率)."
    )

    aggregates = {
        "version": hier.get("version", "unknown"),
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "source_updated_at": manifest.get("updated_at", ""),
        "baseline_source": hier.get("source", ""),
        "totals": totals,
        "by_menjia": by_menjia,
        "slug_by_title": {m["title"]: m["slug"] for m in majors},
        "phantom_html_samples": sorted(phantom_slugs)[:10],
        "human": {
            "meta_description": desc,
            "toc_blurb": (
                f"我们已为 <strong>{totals['curated_count']} 个</strong> 主流专业 "
                f"写了深度精品报告 (✦ 标记可点开)"
            ),
            "lead": (
                f"《普通高等学校本科专业目录》全量 2 层结构 —— "
                f"<strong>{totals['menjia_count']} 个学科门类</strong> · "
                f"<strong>{totals['subclass_count']} 个专业类</strong> · "
                f"<strong>约 {totals['major_count']} 种本科专业</strong> "
                f"(2026 年新增 {totals['new_2026']} 种). "
                f"我们已为 <strong>{totals['curated_count']}+ 个</strong> "
                f"主流专业写了深度精品报告 (✦ 标记可点开); 其余专业附 "
                f"阳光高考官方满意度评分 ({totals['chsi_rated_count']} 个有评分)."
            ),
            "stats": {
                "menjia": totals["menjia_count"],
                "subclass": totals["subclass_count"],
                "major": f"{totals['major_count']}+",
                "curated": str(totals["curated_count"]),
            },
        },
    }
    return aggregates


def write(agg: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(agg, ensure_ascii=False, indent=1), encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"✅ {OUT.relative_to(ROOT)} ({size_kb:.1f}KB)")
    print(f"   {agg['totals']}")


def check(agg: dict) -> int:
    """CI 用: 比对磁盘上 aggregates.json vs 当前 manifest, 不一致 exit 1.

    注意: agg 参数是刚 build 出来的 (跟 manifest 100% 一致, 不会失败).
    真正检查的是磁盘上 ON_DISK_AGG 跟 manifest 是否一致.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_curated = len(manifest.get("majors") or [])
    on_disk = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    on_disk_curated = on_disk.get("totals", {}).get("curated_count")
    actual_curated = agg["totals"]["curated_count"]
    rc = 0
    if on_disk_curated is None:
        print(f"❌ aggregates.json 缺失或不完整, 请跑 build_aggregates.py")
        rc = 1
    elif on_disk_curated != expected_curated:
        print(f"❌ aggregates drift: manifest={expected_curated} on-disk={on_disk_curated}")
        print(f"   修法: python3 scripts/build/build_all.py")
        rc = 1
    else:
        print(f"✅ aggregate 与 manifest 一致: curated={on_disk_curated}")
    return rc


def print_stats(agg: dict) -> None:
    t = agg["totals"]
    print(f"\n=== Total ===")
    print(f"  门类:    {t['menjia_count']}")
    print(f"  专业类:  {t['subclass_count']}")
    print(f"  总专业:  {t['major_count']}")
    print(f"  精品:    {t['curated_count']} ({t['coverage_pct']}% 覆盖率)")
    print(f"  HTML:    {t['html_count']} ({t['html_coverage_pct']}% 占精品)")
    print(f"  Phantom: {t['phantom_html_count']} (orphan html, 需 cleanup)")
    print(f"  CHSI 评: {t['chsi_rated_count']} (有阳光高考评分)")
    print(f"\n=== By menjia ===")
    print(f"  {'code':<5} {'name':<8} {'pool':>5} {'cur':>4} {'html':>4} {'pct':>6}")
    for code in sorted(agg["by_menjia"].keys()):
        d = agg["by_menjia"][code]
        print(f"  {code:<5} {d['name']:<8} {d['pool']:>5} {d['curated']:>4} {d['html']:>4} {d['pct']:>5}%")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true", help="CI: 比对 manifest, 不一致 exit 1")
    p.add_argument("--stats", action="store_true", help="打印人类可读统计")
    args = p.parse_args()

    manifest, hier, chsi = load_sources()
    agg = build(manifest, hier, chsi)

    if args.check:
        sys.exit(check(agg))
    write(agg)
    if args.stats:
        print_stats(agg)


if __name__ == "__main__":
    main()
