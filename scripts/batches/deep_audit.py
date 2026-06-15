#!/usr/bin/env python3
"""
deep_audit.py — 深度质量排查, 不只是结构, 还看内容质量.

维度 (每个 0-100):
  - 数据多样性 (tier 分布是否丰富 / 学校排名是否多样 / 课程名是否去重)
  - 内容特异性 (是否通用模板 / 是否 major-specific)
  - 文本长度 (overview/alumni/quote 长度)
  - 真实感 (数字是否合理 / 字段是否齐全)
"""
import argparse, json, pathlib, re
from collections import Counter

ROOT = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp")
CURATED = ROOT / "skills/gaokao-major-explorer/data/curated"


def deep_audit_one(slug: str) -> dict:
    json_path = CURATED / f"{slug}.json"
    if not json_path.exists():
        return {"slug": slug, "issues": ["missing"]}
    d = json.loads(json_path.read_text(encoding="utf-8"))
    issues = []
    metrics = {}

    # 1. curriculum 课程重复
    cur = d.get("curriculum", {})
    dup_courses = {}
    for block, items in cur.items():
        if not isinstance(items, list): continue
        names = [c.get("name", "") if isinstance(c, dict) else str(c) for c in items]
        dupes = [n for n, c in Counter(names).items() if c > 1]
        if dupes:
            dup_courses[block] = dupes
            issues.append(f"curriculum: 课程重复 in {block}: {dupes[:3]}")
    metrics["dup_courses_count"] = sum(len(v) for v in dup_courses.values())

    # 2. companies 重复 + tier 单一
    comps = d.get("top_companies", [])
    if isinstance(comps, list):
        comp_names = [c.get("name", "") if isinstance(c, dict) else c for c in comps]
        dup_companies = [n for n, c in Counter(comp_names).items() if c > 1]
        if dup_companies:
            issues.append(f"companies: 名称重复: {dup_companies[:3]}")
        metrics["dup_companies_count"] = len(dup_companies)

        # tier 分布
        tiers = [c.get("tier", "B") for c in comps if isinstance(c, dict)]
        metrics["tier_distribution"] = dict(Counter(tiers))
        unique_tiers = len(set(tiers))
        if unique_tiers == 1:
            issues.append(f"companies: tier 单一 ({tiers[0]} only, 无差异化)")
        metrics["unique_tiers"] = unique_tiers

    # 3. schools 重复
    schools = d.get("top_schools", [])
    if isinstance(schools, list):
        school_names = [s.get("name", "") if isinstance(s, dict) else s for s in schools]
        dup_schools = [n for n, c in Counter(school_names).items() if c > 1]
        if dup_schools:
            issues.append(f"schools: 名称重复: {dup_schools[:3]}")

    # 4. employment 重复
    dirs = d.get("employment_direction", [])
    if isinstance(dirs, list):
        dir_names = [x.get("name", "") if isinstance(x, dict) else x for x in dirs]
        dup_dirs = [n for n, c in Counter(dir_names).items() if c > 1]
        if dup_dirs:
            issues.append(f"employment: 名称重复: {dup_dirs[:3]}")

    # 5. alumni 重复
    quotes = d.get("alumni_quotes", [])
    if isinstance(quotes, list):
        quote_currents = [q.get("current", "") if isinstance(q, dict) else "" for q in quotes]
        dup_quotes = [c for c, n in Counter(quote_currents).items() if c and n > 1]
        if dup_quotes:
            issues.append(f"alumni: 校友去向重复: {dup_quotes[:3]}")

    # 6. 通用模板检测
    GENERIC_CURRICULUM = ["核心课程 (待补)", "方向分流课程 (待补)", "法学基础课程 (placeholder)"]
    for block, items in cur.items():
        if isinstance(items, list):
            for c in items:
                if isinstance(c, dict) and c.get("name") in GENERIC_CURRICULUM:
                    issues.append(f"curriculum: {block} 含通用模板 '{c.get('name')}'")
                    break

    # 7. salary 数字合理性
    sal = d.get("salary", {})
    if isinstance(sal, dict):
        for k, v in sal.items():
            if isinstance(v, dict):
                p50 = v.get("p50", 0)
                if p50 and (p50 < 3 or p50 > 200):
                    issues.append(f"salary: {k} p50={p50} 异常 (<3 或 >200)")

    # 8. overview_v2 lede 长度
    ov = d.get("overview_v2", {})
    if isinstance(ov, dict):
        lede = ov.get("lede", "")
        if isinstance(lede, str):
            metrics["lede_len"] = len(lede)
            if len(lede) < 50:
                issues.append(f"overview: lede 过短 ({len(lede)} 字)")

    # 9. alumni 数量 (软阈值)
    metrics["alumni_count"] = len(quotes) if isinstance(quotes, list) else 0

    # 10. hero_quote 长度
    hq = d.get("hero_quote", "")
    metrics["hero_quote_len"] = len(str(hq))

    return {
        "slug": slug,
        "style": d.get("style", ""),
        "issues": issues,
        "metrics": metrics,
        "n_issues": len(issues),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    m = json.loads((ROOT / "public/data/manifest.json").read_text(encoding="utf-8"))
    targets = [e["slug"] for e in m["majors"]]
    if args.limit: targets = targets[:args.limit]

    results = [deep_audit_one(s) for s in targets]
    # Issue 类别分布
    issue_cat = Counter()
    for r in results:
        for iss in r["issues"]:
            cat = iss.split(":")[0]
            issue_cat[cat] += 1

    print(f"📋 深度审计 {len(results)} 篇\n")
    print(f"=== Issue 类别 (前 10) ===")
    for cat, n in issue_cat.most_common(10):
        print(f"  {cat}: {n} 篇")
    print()

    # 各种 issue 详细列
    issue_detail = Counter()
    for r in results:
        for iss in r["issues"]:
            # 简化为第 2 段描述
            key = iss.split(":")[1].strip()[:50] if ":" in iss else iss
            issue_detail[key] += 1
    print(f"=== Issue 具体模式 (前 15) ===")
    for k, n in issue_detail.most_common(15):
        print(f"  {n}× {k}")
    print()

    # 严重度分级
    no_issues = [r for r in results if r["n_issues"] == 0]
    minor = [r for r in results if 1 <= r["n_issues"] <= 2]
    major = [r for r in results if r["n_issues"] >= 3]
    print(f"=== 严重度 ===")
    print(f"  干净: {len(no_issues)} 篇")
    print(f"  小问题 (1-2): {len(minor)} 篇")
    print(f"  大问题 (≥3): {len(major)} 篇")
    print()

    print(f"=== 大问题篇 (top 20) ===")
    for r in sorted(major, key=lambda x: -x["n_issues"])[:20]:
        print(f"  {r['slug']:30s} ({r['style']:14s}) {r['n_issues']} issues")
        for iss in r["issues"][:4]:
            print(f"      - {iss}")

    # 写报告
    out = {
        "total": len(results),
        "issue_categories": dict(issue_cat),
        "issue_patterns": dict(issue_detail),
        "clean": len(no_issues),
        "minor": len(minor),
        "major": len(major),
        "results": sorted(results, key=lambda x: -x["n_issues"]),
    }
    rp = ROOT / "test_results/deep_audit.json"
    rp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📊 报告: {rp}")


if __name__ == "__main__":
    main()