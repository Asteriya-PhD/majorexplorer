#!/usr/bin/env python3
"""
fix_pitfalls_whofits.py — 用 m3 重写被 deepseek 金融话术污染的 pitfalls + who_fits_yes/no.

背景: 49 篇 day1 中 45 篇的 pitfalls[2] 包含同样模板 "头部岗位 (如精算师/CFA/四大事务所) 持证是硬门槛"
      (m3 也学了这个错模板, 估计来自训练数据交叉污染)
      2 篇 (光电/物联网) 的 who_fits_yes/no 也被污染 (经济/持证上岗/案例分析)

检测: 关键词扫 pitfalls[].reality/truth + who_fits_yes/no
修复: 用 m3 重新生成 完全属于 "${title}" 专业的 3 条 pitfalls + 3 条 who_fits_yes + 2 条 who_fits_no

用法:
  python3 scripts/batches/fix_pitfalls_whofits.py --csv scripts/batches/day1_v1.csv
"""
import sys, os, json, csv, argparse, re, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scf"))

from synth.llm import M3Client  # noqa: E402

CUR = ROOT / "skills/gaokao-major-explorer/data/curated"

# 金融/经管污染关键词
FIN_KEYWORDS = [
    "精算师", "CFA", "四大事务所", "持证上岗", "注册会计师", "CPA", "ACCA", "FRM",
    "证券从业", "基金从业", "金融分析师", "金融工程", "金融数学", "经济学",
    "管理咨询", "战略咨询", "MBB", "麦肯锡", "BCG", "Bain", "贝恩",
    "投行", "券商", "银行风控", "审计师", "税务师", "注会", "财会",
    "案例分析", "建模能力", "估值建模", "量化交易", "量化研究", "对冲基金",
    "二级市场", "一级市场", "考证/读研", "无耐心考证", "金融专业",
]


def has_fin_contam(text: str) -> bool:
    return any(kw in text for kw in FIN_KEYWORDS)


def detect_contam(data: dict) -> dict:
    """返回 {field: [具体污染位置]}."""
    contam = {"pitfalls": [], "who_fits_yes": [], "who_fits_no": []}
    pitfalls = data.get("overview_v2", {}).get("pitfalls", [])
    for i, p in enumerate(pitfalls):
        if isinstance(p, dict):
            for k in ("myth", "reality", "truth", "detail"):
                if k in p and has_fin_contam(p[k]):
                    contam["pitfalls"].append(i)
                    break
    ov = data.get("overview_v2", {})
    for k in ("who_fits_yes", "who_fits_no"):
        lst = ov.get(k, [])
        if isinstance(lst, list):
            for s in lst:
                if isinstance(s, str) and has_fin_contam(s):
                    contam[k].append(0)
                    break
    return {k: v for k, v in contam.items() if v}


FIX_PROMPT = """你是中国高考专业内容修复员. 下面这份"专业深度报告 JSON"中的 pitfalls (避坑指南) 和 who_fits_yes/no (适合/不适合人群) 字段被错误地填充了"金融/经管/CFA/精算师"的内容, 与 ${title} 专业完全不匹配.

【专业】: {title} (style={style})
【style 决定整体调性】

【⚠️ 严格禁止话术 - 包含即视为输出失败】:
精算师 / CFA / FRM / CPA / ACCA / 金融分析师 / 金融工程 / 金融数学 / 持证上岗 / 注册会计师 / 投行 / 券商 / 银行风控 / 审计师 / 税务师 / 注会 / 财会 / 案例分析 / 建模能力 / 估值建模 / 量化交易 / 量化研究 / 对冲基金 / 二级市场 / 一级市场 / 管理咨询 / 战略咨询 / MBB / 麦肯锡 / BCG / 贝恩 / 考证 / 读研 / 金融专业 / 经济学 / 证券从业 / 基金从业 / 四大事务所

【错误示范 (坚决不要这么写)】:
❌ "头部岗位 (如精算师/CFA/四大事务所) 持证是硬门槛"  ← 这是金融话术, 写进非金融专业 = 失败
❌ "能接受 4 年制本硕博长跑, 或愿意持证上岗"  ← "持证上岗" 4 字也是金融话术
❌ "对学科基础课程 (数学/统计/经济) 有兴趣"  ← 经济/统计不适用所有专业

【任务】: 重新生成下面 3 个字段, 输出**完全属于"${title}"专业**的内容:

1. pitfalls: 3 条 "myth → reality" (大众误区 → 真实情况), 每条 25-60 字
   - 必须是 ${title} 专业**独有**的坑, 给出真实场景 (e.g. 光电 → "Zemax 光学设计软件自学 6 个月起步"; 中医 → "《黄帝内经》背诵压力 vs 现代医学比例; 师承 vs 学院派分流"; 机械 → "传统机械岗收缩但电控+仿真延伸能扛住转型")
   - myth 也必须有专业特征, 不是说"毕业=高薪"这种空话

2. who_fits_yes: 3 条适合读这个专业的人 (10-30 字)
   - 必须有专业特征 (e.g. "对物理光学/激光原理不排斥", "能接受车间/倒班", "愿意啃 5 年才能精通的硬核教材")
   - 避免 "持证上岗/经济/案例分析" 等金融经管话术

3. who_fits_no: 2 条不适合读这个专业的人 (10-30 字)
   - 必须有专业特征 (e.g. "怕物理光学/电磁场", "不能接受长期实验室", "晕血晕手术", "看不了 200 页技术文档")
   - 避免 "考证/案例分析/经济" 等金融经管话术

【参考该专业其他字段 (用于提炼专业特征)】:
{reference}

【输出严格 JSON 格式】:
{{
  "pitfalls": [
    {{"myth": "...", "reality": "..."}},
    {{"myth": "...", "reality": "..."}},
    {{"myth": "...", "reality": "..."}}
  ],
  "who_fits_yes": ["...", "...", "..."],
  "who_fits_no": ["...", "..."]
}}
只输出 JSON, 不要 markdown 代码块, 不要任何额外文本.
"""


def fix_one(client: M3Client, slug: str, title: str, style: str, fields: list) -> dict:
    p = CUR / f"{slug}.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    reference = ""
    # 用校友引用 + 课程 + 雇主提取专业特征
    for q in data.get("alumni_quotes", [])[:2]:
        if isinstance(q, dict):
            reference += f"- 校友: {q.get('current','')}: {q.get('quote','')[:100]}\n"
    for c in data.get("curriculum", {}).get("通用专业核心", [])[:5]:
        if isinstance(c, dict):
            reference += f"- 核心课: {c.get('name','')}\n"
    for c in data.get("top_companies", [])[:3]:
        if isinstance(c, dict):
            reference += f"- 雇主: {c.get('name','')}\n"
    if not reference:
        reference = "(无 hint)"

    prompt = FIX_PROMPT.format(title=title, style=style, reference=reference)
    payload = client._call({
        "model": client.model,
        "max_tokens": 16000,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}],
    })
    text = client._extract_text(payload)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {"slug": slug, "error": f"非 JSON: {text[:200]}"}
    try:
        result = json.loads(m.group(0))
    except Exception as e:
        return {"slug": slug, "error": f"JSON parse: {e}: {text[:200]}"}

    # 写回
    ov = data.setdefault("overview_v2", {})
    if "pitfalls" in fields and "pitfalls" in result:
        ov["pitfalls"] = result["pitfalls"]
    if "who_fits_yes" in fields and "who_fits_yes" in result:
        ov["who_fits_yes"] = result["who_fits_yes"]
    if "who_fits_no" in fields and "who_fits_no" in result:
        ov["who_fits_no"] = result["who_fits_no"]
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "slug": slug,
        "title": title,
        "fixed_fields": fields,
        "pitfalls_count": len(result.get("pitfalls", [])),
        "who_yes_count": len(result.get("who_fits_yes", [])),
        "who_no_count": len(result.get("who_fits_no", [])),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--slugs", nargs="*")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    pairs = []
    if args.csv:
        with open(args.csv) as f:
            for row in csv.DictReader(f):
                if row.get("slug"):
                    pairs.append((row["slug"], row.get("title", ""), row.get("style", "")))
    if args.slugs:
        for s in args.slugs:
            slug, _, style = s.partition(":")
            title = json.loads((CUR / f"{slug}.json").read_text()).get("title", slug)
            pairs.append((slug, title, style or "cs"))

    if not pairs:
        print("❌ no input")
        return

    # 1) 检测
    to_fix = []
    for slug, title, style in pairs:
        p = CUR / f"{slug}.json"
        if not p.exists():
            print(f"  ⏭️  {slug}: missing")
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        contam = detect_contam(d)
        if args.force or contam:
            fields = list(contam.keys()) if contam else ["pitfalls", "who_fits_yes", "who_fits_no"]
            to_fix.append((slug, title, style, fields))
            print(f"  ⚠️  {slug} ({title}): {fields}")
        else:
            print(f"  ✅ {slug} ({title}): 干净")

    if not to_fix:
        print("\n✅ 全部干净")
        return

    print(f"\n🔧 准备修复 {len(to_fix)} 篇 (auditor=m3, thinking=ON)")
    client = M3Client(enable_thinking=True)
    results = []
    for i, (slug, title, style, fields) in enumerate(to_fix, 1):
        print(f"\n[{i}/{len(to_fix)}] {title} ({style}) fields={fields}")
        try:
            r = fix_one(client, slug, title, style, fields)
        except Exception as e:
            r = {"slug": slug, "error": f"{type(e).__name__}: {e}"}
        if "error" in r:
            print(f"  ❌ {r['error']}")
        else:
            print(f"  ✅ 修复 {r['fixed_fields']}: pitfalls={r['pitfalls_count']}, who_yes={r['who_yes_count']}, who_no={r['who_no_count']}")
        results.append(r)

    ok = [r for r in results if "error" not in r]
    print(f"\n{'='*60}\n汇总: {len(ok)}/{len(results)} 修复成功")


if __name__ == "__main__":
    main()
