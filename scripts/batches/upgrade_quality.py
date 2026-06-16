#!/usr/bin/env python3
"""upgrade_quality.py — Day 1+2 精品质量升级

对每篇 major JSON, 用 mimo 重写 4 个核心字段:
  1. deep_study: 从 3-column (books/cert/skills) 改为 5-7 路径分布 (key=pct int, sum=100)
  2. alumni_quotes: 3 条引用, 每条含具体课程名 + 项目细节 + 数据
  3. overview_v2.pitfalls: 扩到 4-5 条, 每条 myth+reality 均为本专业独有
  4. employment_direction: 修百分比 sum=100 + 修正错配 (如临床医学生去向)

用法:
  python3 scripts/batches/upgrade_quality.py --csv scripts/batches/day2_batch1.csv
  python3 scripts/batches/upgrade_quality.py --slugs intelligent-vehicle-engineering fintech
"""
import json, sys, time, csv, argparse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/batches"))
from auto_fix_pipeline import MiMoFixer

CUR = ROOT / "skills/gaokao-major-explorer/data/curated"

UPGRADE_PROMPT = """你是中国高考专业内容升级员. 把 "{title}" 专业 ({style}) 的报告从 6/10 升到 9/10.

【核心问题 - Round 2 深度升级】
1. alumni_quotes 太模板化: 3 条都遵循"修了X课+做Y项目+拿Z offer", 必须改为 3 个不同角度:
   · 第 1 条: 课程细节 + 课堂项目 (大几修了什么核心课 + 课设做了什么)
   · 第 2 条: 实习/竞赛转折 (大几实习/竞赛, 关键决策点, 转折体验)
   · 第 3 条: 行业观察/反思 (工作 3-5 年后, 对专业的反思/对比/后悔/惊喜)
2. alumni_quotes 学校必须出现在 top_schools 中, 课程必须出现在 curriculum 中 (数据自洽)
3. deep_study 与 employment_direction 严重重复 — 改为纯「继续深造」路径:
   · 国内读研 (具体方向/学校) / 出国读硕/博 / 跨专业考研 / 直接就业 (不要) / 考公/选调 / 创业
   · 5-6 条, sum=100
4. curriculum 删重复 (公共必修 + 通用专业核心 重复的课) + 补核心课 (本专业缺的关键课)
5. lede 重写为「独特洞察」: 不是"X是Y交叉学科", 而是抓住本专业的核心矛盾/反常识点
6. hero_quote 删除假署名 ("—— 基于教育部XX指南" 等), 改为不署名或真实权威

【真实数据要求】
- top_schools: 列出该专业**实际强校** (非通用 985)
- alumni 课程: 本专业**真实核心课** (上面 Round 1 已成功, 继续用)
- alumni 公司: 真实头部企业
- 就业数据: 应届 8-15万 / 3年 15-25万 / 5年 25-45万 (按 style 调整)
- hero_quote: 30-50 字短句, 不要用冒号分隔长句, 不要假出处

【输出严格 JSON 格式】:
{{"lede": "30-80 字独特洞察, 不是模板定义 (1 句话, 不重复 summary)", "hero_quote": "30-50 字, 无假署名, 无冒号长句", "curriculum": {{"公共必修": [...], "通用专业核心": [...去重, 补缺...], "5 校特色选修": [...]}}, "deep_study": {{"国内读研 (X方向)": 30, "出国读硕": 20, "考公/选调": 15, ...}} (注意: 是深造路径不是就业), "alumni_quotes": [{{"year": "2018", "current": "公司 · 岗位", "quote": "第1条: 大几修了《X课》, 课设做了Y (具体内容). 关键收获: Z", "source": "XX大学 2018届"}}, {{"year": "2020", "current": "公司 · 岗位", "quote": "第2条: 大几在X公司实习, 转折点: Y. 关键决策: Z", "source": "XX大学 2020届"}}, {{"year": "2019", "current": "公司 · 岗位", "quote": "第3条: 工作3-5年, 对专业的反思/对比: Y. 后悔/惊喜: Z", "source": "XX大学 2019届"}}]}}

只输出 JSON, 不要 markdown."""

# 路径必须稳定 (每次跑出相同结果)
FIXED_PROMPT_TAIL = "\n【格式】: deep_study 必须是 {{'路径名 (细分)': 百分比}} dict, sum=100. employment_direction 必须是 list of {{name, dest, pct, desc}}, pct sum=100. alumni_quotes 3 条, 每条 year+current+quote+source. pitfalls 4-5 条, 每条 myth+reality. 不允许任何非上述字段. 【只输出 1 个 JSON 对象】:"

def upgrade_one(fixer, slug):
    p = CUR / f"{slug}.json"
    if not p.exists():
        return slug, "missing"
    d = json.loads(p.read_text())
    title = d["title"]
    style = d["style"]
    category = d.get("category", "")
    degree = d.get("degree", "")
    duration = d.get("duration_years", 4)

    # 收集现有 context
    summary = d.get("summary", "")[:300]
    employment = d.get("employment_direction", [])
    alumni = d.get("alumni_quotes", [])
    pitfalls = d.get("overview_v2", {}).get("pitfalls", [])
    deep_study = d.get("deep_study", {})

    prompt = f"""{UPGRADE_PROMPT}

【当前数据 (作为参考)】
- 类别: {category}
- 学位: {degree} ({duration} 年)
- 摘要: {summary}
- 现有就业: {json.dumps(employment[:5], ensure_ascii=False)[:400]}
- 现有校友: {json.dumps(alumni[:2], ensure_ascii=False)[:300]}
- 现有 pitfalls: {json.dumps(pitfalls[:3], ensure_ascii=False)[:300]}
- 现有 deep_study: {json.dumps(deep_study, ensure_ascii=False)[:200]}

{FIXED_PROMPT_TAIL}"""

    for attempt in range(3):
        r = fixer.fix(prompt)
        if "error" not in r:
            break
        time.sleep(5)
    if "error" in r:
        return slug, f"mimo err: {r['error'][:60]}"

    # 写回: 验证 + 写
    new_ds = r.get("deep_study")
    new_aq = r.get("alumni_quotes")
    new_pit = r.get("pitfalls")
    new_emp = r.get("employment_direction")
    new_lede = r.get("lede")
    new_hero = r.get("hero_quote")
    new_curr = r.get("curriculum")

    changed = []
    if isinstance(new_ds, dict) and new_ds:
        total = sum(v for v in new_ds.values() if isinstance(v, (int, float)))
        if 90 <= total <= 110:
            d["deep_study"] = new_ds
            changed.append("deep_study")
    if isinstance(new_aq, list) and len(new_aq) >= 3:
        d["alumni_quotes"] = new_aq[:4]
        changed.append("alumni_quotes")
    if isinstance(new_pit, list) and len(new_pit) >= 3:
        if "overview_v2" not in d: d["overview_v2"] = {}
        d["overview_v2"]["pitfalls"] = new_pit[:5]
        changed.append("pitfalls")
    if isinstance(new_emp, list) and len(new_emp) >= 3:
        total = sum(x.get("pct", 0) for x in new_emp if isinstance(x, dict))
        if 95 <= total <= 105:
            d["employment_direction"] = new_emp
            changed.append("employment_direction")
    if isinstance(new_lede, str) and 20 <= len(new_lede) <= 200:
        if "overview_v2" not in d: d["overview_v2"] = {}
        d["overview_v2"]["lede"] = new_lede
        changed.append("lede")
    if isinstance(new_hero, str) and 10 <= len(new_hero) <= 150:
        # 移除假署名
        d["hero_quote"] = new_hero
        changed.append("hero_quote")
    if isinstance(new_curr, dict) and new_curr:
        # 必须含 3 个特殊 key
        if all(k in new_curr for k in ["公共必修", "通用专业核心", "5 校特色选修"]):
            d["curriculum"] = new_curr
            changed.append("curriculum")

    if changed:
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return slug, f"✅ {','.join(changed)} (4 字段目标)" if changed else "no valid change"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--slugs", nargs="*")
    args = ap.parse_args()

    targets = []
    if args.csv:
        with open(args.csv) as f:
            for r in csv.DictReader(f):
                if r.get("slug"): targets.append(r["slug"])
    if args.slugs:
        targets += args.slugs
    targets = sorted(set(targets))
    if not targets:
        print("❌ no input")
        return

    print(f"🚀 升级 {len(targets)} 篇, mimo 字段级重写")
    fixer = MiMoFixer()
    ok, fail, no_change = [], [], []
    for i, slug in enumerate(targets, 1):
        s, status = upgrade_one(fixer, slug)
        print(f"[{i}/{len(targets)}] {s}: {status}")
        if "✅" in status: ok.append(s)
        elif "mimo err" in status: fail.append((s, status))
        else: no_change.append(s)
        time.sleep(1)  # 避免 429

    print(f"\n{'='*60}")
    print(f"✅ 升级成功: {len(ok)}")
    print(f"⚠️  无变化:  {len(no_change)}")
    print(f"❌ 失败:    {len(fail)}")
    if fail:
        for s, e in fail: print(f"  {s}: {e}")


if __name__ == "__main__":
    main()
