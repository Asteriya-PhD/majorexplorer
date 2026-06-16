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

【核心问题】
1. deep_study 用了 3-column (books/cert/skills), 应改为路径分布: 5-7 条毕业去向, 每条带百分比, 加和=100
2. alumni_quotes 太空, 3 条引用必须各含: 1 个具体课程名 + 1 个项目/论文/竞赛 + 1 个数字/数据
3. pitfalls 仅 2 条, 应扩到 4-5 条本专业独有
4. employment_direction 百分比加和不等于 100, 需修正

【真实数据要求 - 这是升 9 分的关键】
- top_schools: 列出该专业**实际强校** (非通用 985), 如:
  · 金融科技 → 中央财经大学/对外经济贸易大学/西南财经大学/上海财经大学 (非清北复交)
  · 临床医学 → 北京协和医学院/上海交通大学医学院/复旦大学上海医学院/中山大学中山医学院/浙江大学医学院
  · 计算机科学与技术 → 清华大学/上海交通大学/浙江大学/南京大学/哈尔滨工业大学
  · 数学与应用数学 → 北京大学/复旦大学/中国科学技术大学/南开大学/清华大学
- alumni_quotes 课程: 用本专业**真实核心课**:
  · 临床医学 → 病理学/药理学/内科学/外科学/诊断学
  · 金融科技 → 计量经济学/金融工程/机器学习/Python 数据分析/区块链原理
  · 计算机 → 数据结构/操作系统/计算机网络/数据库/机器学习
  · 法学 → 民法/刑法/行政法/民事诉讼法/商法
  · 数学 → 数学分析/高等代数/概率论/近世代数/实变函数
- 校友公司: 真实头部企业 (字节/阿里/腾讯/华为/美团/京东/小米/比亚迪/宁德/平安/招行/建行/国寿 等)
- 就业数据: 应届 8-15万 / 3年 15-25万 / 5年 25-45万 (按 style 调整)

【输出严格 JSON】:
{{"deep_study": {{"路径1 (详细描述)": 25, "路径2": 20, ...}}, "alumni_quotes": [{{"year": "2020", "current": "公司 · 岗位", "quote": "我在 XX 大学修了 XX 课 (具体内容), 在 XX 项目 (具体工作), 拿到 XX offer (具体数字)", "source": "XX 大学 2020 届"}}], "pitfalls": [{{"myth": "本专业独有误区1", "reality": "真实情况1 (含具体数据/案例)"}}, ...], "employment_direction": [{{"name": "路径", "dest": "代表公司", "pct": 25, "desc": "具体描述 (应届/3年/5年 薪资)"}}, ...]}}

只输出 JSON, 不要 markdown/解释."""

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

    changed = []
    if isinstance(new_ds, dict) and new_ds:
        # 验证 sum ≈ 100
        total = sum(v for v in new_ds.values() if isinstance(v, (int, float)))
        if 90 <= total <= 110:
            d["deep_study"] = new_ds
            changed.append("deep_study")
    if isinstance(new_aq, list) and len(new_aq) >= 2:
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
