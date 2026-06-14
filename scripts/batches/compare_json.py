#!/usr/bin/env python3
"""JSON 字段对比脚本: 12 篇待审 vs 2 篇基准, 自动列差异.

输出:
  - 字段完整度表 (top-level keys / overview_v2 keys / curriculum blocks)
  - salary schema 类型 (数字表 vs 散文)
  - 数据量 (校友数 / 院校数 / 雇主数 / 课程门数)
  - 自动 FAIL/WARN/PASS 评级
"""
import json, pathlib, sys

CUR = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp/skills/gaokao-major-explorer/data/curated")

BASES = {
    "law": "law",
    "public-order": "gongan",
}

TARGETS = [
    ("international-law", "law"),
    ("economic-law", "law"),
    ("criminal-law", "law"),
    ("civil-law-jurisprudence", "law"),
    ("commercial-law", "law"),
    ("administrative-law", "law"),
    ("civil-procedure", "law"),
    ("criminal-procedure", "law"),
    ("prison-studies", "gongan"),
    ("drug-control", "gongan"),
    ("criminology", "gongan"),
    ("foreign-police", "gongan"),
]


def inspect(slug: str, style: str | None = None) -> dict:
    p = CUR / f"{slug}.json"
    if not p.exists():
        return {"slug": slug, "_missing": True}
    d = json.loads(p.read_text())
    style = d.get("style", style or "?")
    ov = d.get("overview_v2", {})
    cur = d.get("curriculum", {})
    sal = d.get("salary", {})
    # salary schema 检测 (忽略 __note__)
    if isinstance(sal, dict):
        sal_num = {k: v for k, v in sal.items() if k != "__note__"}
        if all(isinstance(v, dict) and "p50" in v for v in sal_num.values()):
            sal_type = "数字表"
        elif any(k in sal for k in ("entry", "mid", "senior")):
            sal_type = "散文"
        else:
            sal_type = f"未知({list(sal_num.keys())[:3]})"
    else:
        sal_type = "空"

    # 课程统计
    cur_total = 0
    cur_blocks = 0
    if isinstance(cur, dict):
        cur_blocks = len(cur)
        for v in cur.values():
            if isinstance(v, list):
                cur_total += len(v)
            elif isinstance(v, dict):
                cur_total += len(v)
    elif isinstance(cur, list):
        cur_total = len(cur)

    return {
        "slug": slug,
        "style": style,
        "top_keys": len(d),
        "ov_keys": len(ov) if isinstance(ov, dict) else 0,
        "salary_keys": len(sal) if isinstance(sal, dict) else 0,
        "salary_type": sal_type,
        "alumni_n": len(d.get("alumni_quotes", [])),
        "schools_n": len(d.get("top_schools", [])),
        "companies_n": len(d.get("top_companies", [])),
        "employment_n": len(d.get("employment_direction", [])),
        "curriculum_blocks": cur_blocks,
        "curriculum_courses": cur_total,
        "summary_len": len(d.get("summary", "")),
        "hero_quote_len": len(d.get("hero_quote", "")),
        "data_source": (d.get("data_source") or "")[:50],
    }


def score(info: dict, ref: dict) -> tuple[str, list[str]]:
    """对比一篇 vs 同 style 基准. 返回 (grade, issues)."""
    issues = []
    # 字段完整度
    if info["top_keys"] < ref["top_keys"] - 3:
        issues.append(f"top_keys={info['top_keys']} < 基准 {ref['top_keys']}")
    if info["ov_keys"] < ref["ov_keys"] - 2:
        issues.append(f"ov_keys={info['ov_keys']} < 基准 {ref['ov_keys']}")
    # salary schema
    if info["salary_type"] != ref["salary_type"]:
        issues.append(f"salary 不一致: 待审={info['salary_type']} 基准={ref['salary_type']}")
    # 数量
    if info["alumni_n"] < 2:
        issues.append(f"alumni {info['alumni_n']} < 2")
    if info["schools_n"] < 4:
        issues.append(f"schools {info['schools_n']} < 4")
    if info["curriculum_courses"] < 8:
        issues.append(f"课程数 {info['curriculum_courses']} < 8")
    if info["summary_len"] < 80:
        issues.append(f"summary {info['summary_len']} 字 < 80")
    if info["hero_quote_len"] < 10:
        issues.append(f"hero_quote {info['hero_quote_len']} 字过短")
    grade = "FAIL" if issues else "PASS"
    return grade, issues


def main():
    print("=" * 100)
    print("基准对比 (与 law / public-order 同 style 对照)")
    print("=" * 100)
    bases = {slug: inspect(slug) for slug in BASES}
    for slug, info in bases.items():
        print(f"\n📐 基准 {slug} (style={info['style']})")
        for k in ["top_keys", "ov_keys", "salary_type", "salary_keys", "alumni_n",
                  "schools_n", "companies_n", "employment_n",
                  "curriculum_blocks", "curriculum_courses", "summary_len"]:
            print(f"    {k:20s} {info[k]}")

    print("\n" + "=" * 100)
    print("12 篇待审 (按 style 选对应基准)")
    print("=" * 100)
    print(f"{'slug':30s} {'style':8s} {'salary':12s} {'ov':>3s} {'alum':>4s} {'sch':>3s} {'com':>3s} {'emp':>3s} {'cur_b':>5s} {'cur_n':>5s} {'sum':>4s} {'grade':6s} {'issues'}")
    fails = []
    for slug, st in TARGETS:
        info = inspect(slug, st)
        ref = bases.get("law" if st == "law" else "public-order", {})
        grade, issues = score(info, ref)
        marker = "❌" if grade == "FAIL" else "✅"
        print(f"{marker} {slug:28s} {info['style']:8s} {info['salary_type']:12s} {info['ov_keys']:>3d} {info['alumni_n']:>4d} {info['schools_n']:>3d} {info['companies_n']:>3d} {info['employment_n']:>3d} {info['curriculum_blocks']:>5d} {info['curriculum_courses']:>5d} {info['summary_len']:>4d} {grade:6s} {'; '.join(issues)[:80]}")
        if grade == "FAIL":
            fails.append((slug, issues))

    print(f"\n{'='*100}\nFAIL 总数: {len(fails)}/12\n{'='*100}")
    for slug, issues in fails:
        print(f"\n❌ {slug}")
        for i in issues:
            print(f"    - {i}")


if __name__ == "__main__":
    main()