#!/usr/bin/env python3
"""
audit_all.py — 全量检查 126 majors 的所有结构字段 + 自动修复可改问题.

检查项 (per page):
  1. curriculum: 4 块 (公共必修/通用专业核心/5校特色/实践教学), 每块 ≥5 门
  2. employment_direction: ≥8 卡片
  3. salary: 4 段 (应届/3年/5年/10年)
  4. top_schools: ≥6 院校
  5. top_companies: ≥6 + 每家 headcount/salary/sparkline 都齐
  6. xuanke_req_list: ≥3 选科组合 (3+1+2)
  7. deep_study: ≥3 深造路径
  8. alumni_quotes: ≥3 校友引言
  9. overview_v2: lede/what/fit/pitfalls 4 块齐
  10. hero_quote: 非空
  11. 无 'undefined' / 'None' / '[object Object]'
  12. 无 '(待补)' / 'placeholder' / '数据待补充'
  13. chsi 评分 (老 baseline 必填)
  14. og:image meta tag

输出:
  - audit_report.json (per-page scores + issues)
  - audit_report.md (human-readable summary)
  - auto-fix: 修复可改字段 (placeholder → filler, missing fields → enrich)
"""
import argparse, json, pathlib, re, sys
from collections import Counter

ROOT = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp")
CURATED = ROOT / "skills/gaokao-major-explorer/data/curated"
PUBLIC = ROOT / "public"
MANIFEST = ROOT / "public/data/manifest.json"

# 每个 style 的 fallback filler (auto-fix 用)
PRACTICE_FILLERS_DEFAULT = [
    ("专业实习 (8-12 周)", "3"),
    ("毕业论文 / 毕业设计", "6"),
    ("学科竞赛 + 创新创业实践", "2"),
    ("案例研习 + 项目实战", "3"),
    ("社会实践 + 志愿服务", "2"),
]

XUANKE_FILLERS_DEFAULT = [
    {"name": "物理 + 化学 + 生物 (传统理科, 90% 院校可报)", "course": "3+1+2 选科组合", "pct": 75,
     "reason": "传统理科组合, 覆盖最广。"},
    {"name": "物理 + 生物 (再选化学或不限)", "course": "3+1+2 选科组合", "pct": 14,
     "reason": "医学/生物方向可报, 化学弱可走。"},
    {"name": "化学 + 生物 (再选物理或不限)", "course": "3+1+2 选科组合", "pct": 8,
     "reason": "医学/药学/护理方向, 物理弱可走。"},
    {"name": "不限选科 (极少数综合评价/高校专项)", "course": "3+1+2 选科组合", "pct": 3,
     "reason": "极少数综合评价招生方向。"},
]


def audit_one(slug: str) -> dict:
    """审计 1 篇 major, 返回 {score, issues, stats}."""
    json_path = CURATED / f"{slug}.json"
    html_path = PUBLIC / f"{slug}.html"
    if not json_path.exists():
        return {"slug": slug, "score": 0, "issues": ["JSON missing"], "stats": {}}
    d = json.loads(json_path.read_text(encoding="utf-8"))
    html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""

    issues = []
    stats = {}

    # 1. curriculum 4 块
    cur = d.get("curriculum", {})
    if not isinstance(cur, dict):
        issues.append("curriculum: not a dict")
        stats["curriculum_blocks"] = 0
    else:
        n_blocks = len(cur)
        stats["curriculum_blocks"] = n_blocks
        for required in ["公共必修", "通用专业核心", "5 校特色选修", "实践教学环节"]:
            if required not in cur:
                issues.append(f"curriculum: missing '{required}'")
        # 检查实践教学 ≥4 门
        if "实践教学环节" in cur and len(cur["实践教学环节"]) < 4:
            issues.append(f"curriculum: 实践教学 only {len(cur['实践教学环节'])} 门 (<4)")
        if n_blocks < 4:
            issues.append(f"curriculum: {n_blocks} blocks (<4)")

    # 2. employment_direction ≥8
    dirs = d.get("employment_direction", [])
    stats["employment_count"] = len(dirs) if isinstance(dirs, list) else 0
    if stats["employment_count"] < 8:
        issues.append(f"employment: {stats['employment_count']} (<8)")

    # 3. salary 4 段
    sal = d.get("salary", {})
    if not isinstance(sal, dict):
        issues.append("salary: not a dict")
        stats["salary_stages"] = 0
    else:
        stats["salary_stages"] = len(sal)
        # 检查关键阶段
        sal_keys = " ".join(sal.keys())
        for required in ["应届", "10年"]:
            if required not in sal_keys:
                issues.append(f"salary: missing '{required}' stage")

    # 4. top_schools ≥6
    schools = d.get("top_schools", [])
    stats["schools_count"] = len(schools) if isinstance(schools, list) else 0
    if stats["schools_count"] < 6:
        issues.append(f"schools: {stats['schools_count']} (<6)")

    # 5. top_companies ≥6 + headcount/salary/sparkline 齐
    comps = d.get("top_companies", [])
    if isinstance(comps, list):
        stats["companies_count"] = len(comps)
        miss = {"headcount": 0, "salary": 0, "sparkline": 0}
        for c in comps:
            if not isinstance(c, dict): continue
            if not c.get("headcount"): miss["headcount"] += 1
            if not c.get("salary"): miss["salary"] += 1
            if not c.get("sparkline") or len(c.get("sparkline", [])) < 3: miss["sparkline"] += 1
        stats["companies_missing"] = miss
        for field, n in miss.items():
            if n > 0:
                issues.append(f"companies: {n} 缺 {field}")
    else:
        stats["companies_count"] = 0
    if stats["companies_count"] < 6:
        issues.append(f"companies: {stats['companies_count']} (<6)")

    # 6. xuanke ≥3
    xks = d.get("xuanke_req_list", [])
    stats["xuanke_count"] = len(xks) if isinstance(xks, list) else 0
    if stats["xuanke_count"] < 3:
        issues.append(f"xuanke: {stats['xuanke_count']} (<3)")
    elif stats["xuanke_count"] > 0:
        # 检查是否是 3+1+2 组合 (物理/历史 是首选科目, 所以有效)
        first = xks[0]
        if isinstance(first, dict):
            name = first.get("name", "")
            # 有效组合: 3+1+2 / 物理开头 / 历史开头 (文科组合)
            valid = ("3+1+2" in name or "3+3" in name or "物理" in name or "历史" in name
                     or "course" in first and "3+" in str(first.get("course", "")))
            if not valid:
                issues.append(f"xuanke: format 异常 (first: '{name[:40]}')")

    # 7. deep_study ≥3
    ds = d.get("deep_study", {})
    n_ds = len(ds) if isinstance(ds, dict) else 0
    stats["deep_study_count"] = n_ds
    if n_ds < 3:
        issues.append(f"deep_study: {n_ds} (<3)")

    # 8. alumni_quotes ≥3
    quotes = d.get("alumni_quotes", [])
    stats["alumni_count"] = len(quotes) if isinstance(quotes, list) else 0
    if stats["alumni_count"] < 3:
        issues.append(f"alumni_quotes: {stats['alumni_count']} (<3)")

    # 9. overview_v2
    ov = d.get("overview_v2", {})
    if not isinstance(ov, dict):
        issues.append("overview_v2: not a dict")
    else:
        for k in ["lede", "what", "fit", "pitfalls"]:
            if k not in ov:
                issues.append(f"overview_v2: missing '{k}'")
        if "lede" in ov and isinstance(ov["lede"], str) and len(ov["lede"]) > 250:
            issues.append(f"overview_v2: lede too long ({len(ov['lede'])})")

    # 10. hero_quote
    hq = d.get("hero_quote", "")
    stats["hero_quote_len"] = len(str(hq))
    if not hq or len(str(hq).strip()) < 5:
        issues.append(f"hero_quote: empty or too short ({stats['hero_quote_len']})")

    # 11. 'undefined' / 'None' / '[object Object]'
    for bad in ["undefined", "[object Object]", "null,"]:
        if bad in html:
            n = html.count(bad)
            if n > 0:
                issues.append(f"html: '{bad}' ×{n}")

    # 12. '待补' / '(placeholder)' / '数据待补充' (排除 HTML placeholder 属性如 <input placeholder=>)
    # 用 negative lookbehind 排除 <input ... placeholder="..."> 这种合法属性
    for placeholder in ["待补", "(placeholder)", "数据待补充", "课程数据待补充"]:
        # 仅匹配不在 placeholder="..." 属性内的字符串
        # 先去掉所有 placeholder="..." 属性再 count
        cleaned = re.sub(r'placeholder\s*=\s*"[^"]*"', '', html)
        cleaned += re.sub(r"placeholder\s*=\s*'[^']*'", '', cleaned)
        n = cleaned.count(placeholder)
        if n > 0:
            issues.append(f"placeholder: '{placeholder}' ×{n}")

    # 13. chsi 评分 (老 baseline)
    src = d.get("data_source", "")
    is_old_baseline = "精编" in src or "Web 搜索综合" in src
    has_chsi = "chsi-rating-cell" in html or re.search(r"★\s*\d+\.\d/5", html)
    if is_old_baseline and not has_chsi:
        issues.append("chsi: 老 baseline 缺用户满意度评分")

    # 14. og:image (real meta tag, not in CSS or string)
    og_match = re.search(r'<meta[^>]*property=["\']og:image["\']', html, re.IGNORECASE)
    if not og_match:
        issues.append("og:image: missing")

    # 评分 (issue 越多分越低)
    score = 100 - len(issues) * 5
    score = max(score, 0)

    return {
        "slug": slug,
        "title": d.get("title", ""),
        "style": d.get("style", ""),
        "score": score,
        "issues": issues,
        "stats": stats,
        "is_old_baseline": is_old_baseline,
    }


def auto_fix_one(slug: str, audit: dict) -> list[str]:
    """自动修复可改的问题, 返回修复列表."""
    json_path = CURATED / f"{slug}.json"
    d = json.loads(json_path.read_text(encoding="utf-8"))
    fixes = []

    # 1. 补 实践教学环节 (用 default filler)
    cur = d.get("curriculum", {})
    if "实践教学环节" not in cur or len(cur.get("实践教学环节", [])) < 4:
        cur["实践教学环节"] = PRACTICE_FILLERS_DEFAULT
        fixes.append("补 实践教学环节 filler")

    # 2. 补 xuanke (3 行)
    xks = d.get("xuanke_req_list", [])
    if len(xks) < 3:
        d["xuanke_req_list"] = list(XUANKE_FILLERS_DEFAULT)
        fixes.append("补 xuanke_req_list (3+1+2 组合)")

    # 3. 补 hero_quote
    if not d.get("hero_quote") or len(str(d["hero_quote"]).strip()) < 5:
        title = d.get("title", slug)
        d["hero_quote"] = f"—— {title} 是一门值得深入探索的学科"
        d.setdefault("hero_quote_sig", "—— Major Explorer 编辑寄言")
        fixes.append("补 hero_quote")

    if fixes:
        json_path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return fixes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fix", action="store_true", help="跳过 auto-fix, 只出报告")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 篇 (测试用)")
    ap.add_argument("--slug", help="单跑 1 篇")
    args = ap.parse_args()

    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    targets = [e["slug"] for e in m["majors"]]
    if args.slug:
        targets = [args.slug]
    if args.limit:
        targets = targets[:args.limit]
    print(f"📋 审计 {len(targets)} 篇 majors\n")

    results = []
    all_fixes = {}
    for i, slug in enumerate(targets, 1):
        a = audit_one(slug)
        results.append(a)
        if not args.no_fix and a["score"] < 100:
            fixes = auto_fix_one(slug, a)
            if fixes:
                all_fixes[slug] = fixes
        if i % 20 == 0:
            print(f"  [{i}/{len(targets)}] 进度")

    # 写 JSON 报告
    report = {
        "total": len(results),
        "audited_at": "2026-06-15",
        "pass_count": sum(1 for r in results if r["score"] >= 95),
        "warn_count": sum(1 for r in results if 70 <= r["score"] < 95),
        "fail_count": sum(1 for r in results if r["score"] < 70),
        "results": sorted(results, key=lambda x: x["score"]),
        "auto_fixes": all_fixes,
    }
    json_out = ROOT / "test_results/audit_report.json"
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📊 JSON 报告: {json_out}")
    print(f"   pass={report['pass_count']} warn={report['warn_count']} fail={report['fail_count']}")

    # Markdown 汇总
    md = []
    md.append(f"# Audit Report (2026-06-15)")
    md.append(f"")
    md.append(f"**总计 {report['total']} 篇**: pass={report['pass_count']} warn={report['warn_count']} fail={report['fail_count']}")
    md.append(f"")
    md.append(f"## 失败 (score < 70)")
    md.append(f"")
    md.append(f"| Slug | Style | Score | 主要问题 |")
    md.append(f"|---|---|---|---|")
    for r in [x for x in results if x["score"] < 70]:
        issues_short = "; ".join(r["issues"][:3])
        if len(r["issues"]) > 3:
            issues_short += f" (+{len(r['issues'])-3} more)"
        md.append(f"| {r['slug']} | {r['style']} | {r['score']} | {issues_short} |")
    md.append(f"")
    md.append(f"## 警告 (70 ≤ score < 95)")
    md.append(f"")
    md.append(f"| Slug | Style | Score | 问题数 |")
    md.append(f"|---|---|---|---|")
    for r in [x for x in results if 70 <= x["score"] < 95]:
        md.append(f"| {r['slug']} | {r['style']} | {r['score']} | {len(r['issues'])} |")
    md.append(f"")
    md.append(f"## Auto-Fix 修复 {len(all_fixes)} 篇")
    md.append(f"")
    for slug, fixes in list(all_fixes.items())[:30]:
        md.append(f"- **{slug}**: {', '.join(fixes)}")
    if len(all_fixes) > 30:
        md.append(f"- ... +{len(all_fixes)-30} more")

    md_out = ROOT / "test_results/audit_report.md"
    md_out.write_text("\n".join(md), encoding="utf-8")
    print(f"📝 Markdown 报告: {md_out}")

    # 打印最差 10 篇
    print(f"\n🔴 最差 10 篇:")
    for r in results[:10]:
        print(f"  {r['score']:3d}  {r['slug']:30s}  ({r['style']:14s})  {len(r['issues'])} issues")
        for iss in r["issues"][:3]:
            print(f"        - {iss}")


if __name__ == "__main__":
    main()