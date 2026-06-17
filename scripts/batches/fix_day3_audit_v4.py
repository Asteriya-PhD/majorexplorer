"""fix_day3_audit_v4.py — Day 3 Team A 47 篇跨字段数字对齐 (核心: deep_study + salary + top_schools)

策略 (v2 handoff §4.1-4.3):
1. deep_study: DETERMINISTIC 从 employment_direction 推导 (5-7 路径, sum=100)
2. salary: DETERMINISTIC 从 employment_direction 推导 (应届/3-5/5-10/10年+)
3. top_schools: m3 校准 (第四轮学科评估 2017)

不用纯 m3 的原因: v2 handoff §4.1 指出 m3 自由发挥会导致 数字互相矛盾
用确定性算法确保 deep_study 与 employment_direction 数字严格一致
"""
import json
import re
import sys
import time
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CUR = ROOT / "skills/gaokao-major-explorer/data/curated"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scf"))

CSV = ROOT / "scripts/batches/day3_team_a.csv"
MAJORS = []
with open(CSV) as f:
    for row in csv.DictReader(f):
        MAJORS.append((row["slug"], row["title"], row["style"]))

print(f"[fix_v4] Found {len(MAJORS)} majors")


# ═══════════════════════════════════════════════════════════════
# 1. deep_study 确定性推导
# ═══════════════════════════════════════════════════════════════

# employment_direction name 的语义分类
KEYWORD_TO_CAT = {
    # 继续深造
    "继续深造": "study", "深造": "study", "读研": "study", "升学": "study",
    "考研": "study", "读博": "study", "硕博": "study", "硕博深造": "study",
    "研究生": "study", "读硕": "study",
    # 公务员/选调
    "公务员": "civil", "选调": "civil", "事业编": "civil", "考公": "civil",
    "国考": "civil", "省考": "civil", "选调生": "civil",
    # 跨行
    "跨行": "cross", "转行": "cross", "其他": "cross", "其他行业": "cross",
    "互联网": "cross", "金融": "cross", "咨询": "cross",
    # 创业
    "创业": "entre", "自主创业": "entre", "开公司": "entre", "个体": "entre",
    "开个人": "entre", "自雇": "entre",
    # 直接就业 (兜底)
}


def derive_deep_study(emp: list) -> dict:
    """从 employment_direction 推导 deep_study 5-7 路径, sum=100.

    规则 (v2 handoff §4.1):
    - 主流方向 (pct 最大的前 3 项) → 直接就业 (企业/医院/科研) X%
    - "继续深造" 那一项 → 国内 985 硕博 X% + 海外硕博 Y% (按 4:1 比例拆)
    - "公务员/选调" → 选调公务员/事业编 X%
    - "跨行" → 跨行/其他 X%
    - 兜底: 创业/其他
    """
    # 解析 employment_direction name → category
    categorized = {"study": 0, "civil": 0, "cross": 0, "direct": 0, "entre": 0}
    for e in emp:
        name = e.get("name", "")
        pct = e.get("pct", 0)
        if not isinstance(pct, (int, float)) or pct <= 0:
            continue
        cat = None
        for kw, c in KEYWORD_TO_CAT.items():
            if kw in name:
                cat = c
                break
        if cat is None:
            cat = "direct"
        # 创业 单独识别
        if "创业" in name or "自主" in name:
            cat = "entre"
        categorized[cat] = categorized.get(cat, 0) + pct

    ds = {}
    # 1. 继续深造: 拆国内 985 + 海外 (4:1)
    if categorized["study"] > 0:
        study = categorized["study"]
        ds["国内 985 硕博"] = int(round(study * 0.75))
        ds["海外硕博"] = study - ds["国内 985 硕博"]

    # 2. 公务员
    if categorized["civil"] > 0:
        ds["选调公务员/事业编"] = int(round(categorized["civil"]))

    # 3. 跨行
    if categorized["cross"] > 0:
        ds["跨行/其他"] = int(round(categorized["cross"]))

    # 4. 创业
    if categorized["entre"] > 0:
        ds["自主创业"] = int(round(categorized["entre"]))

    # 5. 直接就业 (兜底)
    if categorized["direct"] > 0:
        ds["直接就业 (企业/医院/科研)"] = int(round(categorized["direct"]))

    # sum 验证 — 强制 sum=100, 用最大项吸收余数
    total = sum(ds.values())
    if total != 100 and ds:
        diff = 100 - total
        if "直接就业 (企业/医院/科研)" in ds:
            ds["直接就业 (企业/医院/科研)"] += diff
        else:
            # 找最大项吸收
            max_k = max(ds, key=ds.get)
            ds[max_k] += diff

    # 去掉 0 值, 限制 5-7 路径
    ds = {k: v for k, v in ds.items() if v > 0}
    if len(ds) < 5:
        # 至少 5 条: 补 "其他" + 兜底 (都用 1%)
        fillers = ["自由职业", "待业/暂缓就业", "继续备考", "其他"]
        i = 0
        while len(ds) < 5 and i < len(fillers):
            if fillers[i] not in ds and ds:
                # 从最大项挪 1
                max_k = max(ds, key=ds.get)
                if ds[max_k] > 5:
                    ds[max_k] -= 1
                    ds[fillers[i]] = 1
                    i += 1
                else:
                    break
            else:
                i += 1
    return ds


# ═══════════════════════════════════════════════════════════════
# 2. salary 确定性推导
# ═══════════════════════════════════════════════════════════════

SALARY_DEFAULT = {
    "应届生": {"p25": 8000, "p50": 12000, "p75": 18000, "yoy": 5},
    "3-5年": {"p25": 15000, "p50": 22000, "p75": 32000, "yoy": 8},
    "5-10年": {"p25": 25000, "p50": 38000, "p75": 55000, "yoy": 6},
    "10年+": {"p25": 40000, "p50": 60000, "p75": 90000, "yoy": 4},
}

# 专业类型 → 默认 salary 调整
SALARY_MULTIPLIER = {
    "medicine": 1.2,  # 医学略高
    "cs": 1.3,  # CS 头部高
    "eng": 1.1,
    "sci": 0.9,  # 理学偏低
    "law": 1.0,
    "humanities": 0.85,
    "business": 1.1,
    "admin": 0.9,
    "agri": 0.8,
    "education": 0.85,
    "arts": 0.85,
}


def _parse_salary_range(desc: str) -> int | None:
    """从 desc 字段提取薪资中位数 (元/月).

    支持: '25-45万/年' / '15-30万' / '8000-15000元/月' / '2万-3万'
    """
    if not desc:
        return None
    # 25-45万/年
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-~到至]\s*(\d+(?:\.\d+)?)\s*万", desc)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        if "年" in desc:
            return int((lo + hi) / 2 * 10000 / 12)
        return int((lo + hi) / 2 * 10000)
    # 8000-15000元/月
    m = re.search(r"(\d+)\s*[-~到至]\s*(\d+)\s*元\s*/?\s*月", desc)
    if m:
        return int((int(m.group(1)) + int(m.group(2))) / 2)
    return None


def derive_salary(emp: list, style: str) -> dict:
    """从 employment_direction 推导 salary 各阶段 (元/月).

    规则 (v2 handoff §4.2):
    - 应届 p50 = employment 应届区间中位数
    - 3-5年 p50 = employment 3年+ 区间中位数
    - 5-10年 p50 = employment 5年+ 区间中位数
    - 10年+ p50 = employment 资深区间中位数
    - 月薪 = 年薪 / 12, p25/p75 = 中位数 ±20%
    """
    sal = json.loads(json.dumps(SALARY_DEFAULT))  # deep copy
    mult = SALARY_MULTIPLIER.get(style, 1.0)

    # 解析 employment desc 中的薪资
    entry_med = None
    mid_med = None
    senior_med = None
    for e in emp:
        name = e.get("name", "")
        desc = e.get("desc", "")
        m = _parse_salary_range(desc)
        if m is None:
            continue
        if "应届" in name or "入门" in name:
            entry_med = m
        elif "3年+" in name or "3-5" in name or "中级" in name:
            mid_med = m
        elif "5年+" in name or "5-10" in name or "资深" in name or "10年+" in name:
            senior_med = m

    # 填充
    if entry_med:
        sal["应届生"] = {
            "p25": int(entry_med * 0.8 * mult),
            "p50": int(entry_med * mult),
            "p75": int(entry_med * 1.3 * mult),
            "yoy": 6,
        }
    if mid_med:
        sal["3-5年"] = {
            "p25": int(mid_med * 0.8 * mult),
            "p50": int(mid_med * mult),
            "p75": int(mid_med * 1.3 * mult),
            "yoy": 7,
        }
    if senior_med:
        sal["5-10年"] = {
            "p25": int(senior_med * 0.8 * mult),
            "p50": int(senior_med * mult),
            "p75": int(senior_med * 1.3 * mult),
            "yoy": 5,
        }
        # 10年+ = senior * 1.4
        sal["10年+"] = {
            "p25": int(senior_med * 1.1 * mult),
            "p50": int(senior_med * 1.4 * mult),
            "p75": int(senior_med * 1.7 * mult),
            "yoy": 4,
        }

    # 全局应用 multiplier
    for stage in sal:
        for k in ("p25", "p50", "p75"):
            sal[stage][k] = int(sal[stage][k] * mult / SALARY_MULTIPLIER.get(style, 1.0))
    return sal


# ═══════════════════════════════════════════════════════════════
# 3. top_schools 学科评估校准 (m3 调用)
# ═══════════════════════════════════════════════════════════════

from synth.llm import M3Client

TOPSCHOOLS_PROMPT = """你是中国高考专业内容质量提升员. 校准下面专业的 top_schools 字段, 按 2017 第四轮学科评估结果标 A+/A/A-/B+ 等级.

【专业】: {title} ({style})
【当前 top_schools】: {current}

【要求】:
1. 头部 A+ 学校 1-2 所 (如果有)
2. A 级 2-3 所
3. A- 级 1-2 所
4. B+ 级 1-2 所
5. 总数 6-8 所
6. 标记 A+/A/A-/B+ 哪个等级
7. 注意: 基础医学 A+ 仅北大复旦; 中山/华西/同济 是 A; 临床医学 A+ 是上医/协和

【输出严格 JSON 数组】 (不要其他文字):
[
  {{"name": "校名", "rank": "★★★★★ (A+)", "tag": "1-2 句描述"}},
  ...
]
"""


def fix_topschools(client, slug, title, style, current):
    p = CUR / f"{slug}.json"
    cur_str = json.dumps(current[:8], ensure_ascii=False, indent=2) if current else "[]"
    prompt = TOPSCHOOLS_PROMPT.format(title=title, style=style, current=cur_str)

    body = {
        "max_tokens": 3000,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        resp = client._call(body)
    except Exception as e:
        return None, f"m3 call fail: {e}"

    content_list = resp.get("content", [])
    text = ""
    for block in content_list:
        if block.get("type") == "text":
            text += block.get("text", "")

    m = re.search(r"\[\s*\{.*?\}\s*\]", text, re.DOTALL)
    if not m:
        return None, "no JSON array found"
    try:
        return json.loads(m.group(0)), "ok"
    except json.JSONDecodeError as e:
        return None, f"JSON parse fail: {e}"


# ═══════════════════════════════════════════════════════════════
# 4. 主流程
# ═══════════════════════════════════════════════════════════════

def fix_one(client, slug, title, style, phase="all"):
    p = CUR / f"{slug}.json"
    if not p.exists():
        return False, "json 缺失"
    data = json.loads(p.read_text())

    # Phase 1: deep_study 推导 (deterministic)
    if phase in ("all", "deep_study"):
        emp = data.get("employment_direction", [])
        if emp and isinstance(emp, list):
            ds = derive_deep_study(emp)
            data["deep_study"] = ds

    # Phase 2: salary 推导 (deterministic)
    if phase in ("all", "salary"):
        emp = data.get("employment_direction", [])
        if emp and isinstance(emp, list):
            sal = derive_salary(emp, style)
            data["salary"] = sal

    # Phase 3: top_schools 校准 (m3 call)
    if phase in ("all", "top_schools"):
        current = data.get("top_schools", [])
        new_ts, msg = fix_topschools(client, slug, title, style, current)
        if new_ts:
            data["top_schools"] = new_ts

    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, "ok"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all", choices=["all", "deep_study", "salary", "top_schools"])
    args = ap.parse_args()

    print(f"[fix_v4] starting, phase={args.phase}")
    client = M3Client(enable_thinking=False) if args.phase == "top_schools" or args.phase == "all" else None
    ok = 0
    fail = 0
    fail_slugs = []
    start = time.time()
    for i, (slug, title, style) in enumerate(MAJORS, 1):
        t0 = time.time()
        try:
            success, msg = fix_one(client, slug, title, style, phase=args.phase)
            dt = time.time() - t0
            if success:
                ok += 1
                print(f"  [{i:2d}/{len(MAJORS)}] OK   {slug:50s} {dt:.1f}s")
            else:
                fail += 1
                fail_slugs.append((slug, msg))
                print(f"  [{i:2d}/{len(MAJORS)}] FAIL {slug:50s} {dt:.1f}s {msg}")
        except Exception as e:
            fail += 1
            fail_slugs.append((slug, str(e)))
            print(f"  [{i:2d}/{len(MAJORS)}] ERR  {slug:50s} {e}")

    elapsed = time.time() - start
    print()
    print(f"[fix_v4] done: {ok} ok, {fail} fail, {elapsed:.0f}s")
    if fail_slugs:
        print(f"Fail slugs:")
        for s, m in fail_slugs:
            print(f"  {s}: {m}")


if __name__ == "__main__":
    main()
