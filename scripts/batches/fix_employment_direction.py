#!/usr/bin/env python3
"""
fix_employment_direction.py — 用 m3 重写被污染的 employment_direction 字段.

检测条件: 出现工业设计/产品设计/UI/UX/IDEO/Frog/洛可可/中央美院/清华美院/设计院 关键词 → 标记污染.
修复: 用 m3 重新合成 5-7 条该专业**真正**的就业方向 + 百分比.

用法:
  python3 scripts/batches/fix_employment_direction.py --csv scripts/batches/engineering_a_v1.csv
  python3 scripts/batches/fix_employment_direction.py --slugs optoelectronic-information-science-engineering
"""
import sys, os, json, csv, argparse, re, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scf"))

from synth.llm import M3Client  # noqa: E402

CUR = ROOT / "skills/gaokao-major-explorer/data/curated"

# 工业设计污染关键词
CONTAM_KEYWORDS = [
    "UI/UX", "交互设计", "产品设计", "工业设计", "IDEO", "Frog",
    "洛可可", "中央美院", "清华美院", "交通工具设计", "家居家电设计",
    "设计咨询", "品牌策略", "设计院", "自由设计师", "互联网产品",
    "智能硬件 IoT", "产品经理", "字节/阿里/腾讯", "小鹏/比亚迪/大疆", "产品造型"
]

FIX_PROMPT = """你是中国高考专业内容修复员. 下面这份"专业深度报告 JSON"中的 employment_direction (就业方向) 字段被错误地填充了"工业设计/产品设计"的内容 (UI/UX/IDEO/Frog 等), 与专业完全不匹配.

【专业】: {title} (style={style})

【任务】: 重新生成 employment_direction 字段, 输出**完全属于"${title}"专业**的 5-7 条就业方向, 每条包含:
  - name: 方向名 (具体到岗位/行业, e.g. "光通信模块研发", "电网调度", "锂电材料工艺")
  - share: 占比 % (int, 5-30 之间, 5 条合计 ≈ 100)
  - companies: 该方向典型雇主 3-5 个 (具体公司名)
  - note: 一句话说明这方向的门槛/优势/转行难度

【必须避免的污染词】: UI/UX, IDEO, Frog, 洛可可, 中央美院, 清华美院, 产品设计, 工业设计, 交通工具设计, 家居家电设计, 设计咨询, 品牌策略, 自由设计师, 产品造型.

【参考该专业真实就业场景 (选 5-7 条最相关的, 不是照搬):
{reference}

【输出严格 JSON 格式】:
{{
  "employment_direction": [
    {{"name": "...", "share": 25, "companies": ["A", "B", "C"], "note": "..."}},
    ...
  ]
}}
只输出 JSON, 不要 markdown 代码块, 不要任何额外文本. 不要解释, 不要注释.
"""


def is_contaminated(data: dict) -> bool:
    """检测 employment_direction 字段是否被工业设计污染."""
    emp = data.get("employment_direction", [])
    if not emp:
        return False
    # 提取所有 text
    text = json.dumps(emp, ensure_ascii=False)
    hits = [k for k in CONTAM_KEYWORDS if k in text]
    return len(hits) >= 2  # 至少 2 个污染词才修


def fix_one(client: M3Client, slug: str, title: str, style: str) -> dict:
    p = CUR / f"{slug}.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    reference = ""
    # 用 alumni_quotes 提取 hint
    for q in data.get("alumni_quotes", []):
        if isinstance(q, dict) and q.get("current"):
            reference += f"- {q.get('current','')}: {q.get('quote','')[:100]}\n"
    # 用 top_companies 提取 hint
    companies = data.get("top_companies", [])
    if isinstance(companies, list):
        for c in companies[:5]:
            if isinstance(c, dict):
                reference += f"- 典型雇主: {c.get('name','')}\n"
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
    new_emp = result.get("employment_direction", [])
    if not new_emp or not isinstance(new_emp, list):
        return {"slug": slug, "error": "result 没有 employment_direction 字段"}
    data["employment_direction"] = new_emp
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "slug": slug,
        "title": title,
        "new_count": len(new_emp),
        "total_share": sum(d.get("share", 0) for d in new_emp if isinstance(d, dict)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--slugs", nargs="*")
    ap.add_argument("--force", action="store_true", help="强制重写 (不检测污染)")
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

    # 1) 检测哪些需要修
    to_fix = []
    for slug, title, style in pairs:
        p = CUR / f"{slug}.json"
        if not p.exists():
            print(f"  ⏭️  {slug}: missing")
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        if args.force or is_contaminated(d):
            to_fix.append((slug, title, style))
            print(f"  ⚠️  {slug} ({title}): 污染")
        else:
            print(f"  ✅ {slug} ({title}): 干净")

    if not to_fix:
        print("\n✅ 全部干净, 无需修复")
        return

    print(f"\n🔧 准备修复 {len(to_fix)} 篇 (auditor=m3, thinking=ON)")
    client = M3Client(enable_thinking=True)
    results = []
    for i, (slug, title, style) in enumerate(to_fix, 1):
        print(f"\n[{i}/{len(to_fix)}] 修复 {title} ({style})")
        try:
            r = fix_one(client, slug, title, style)
        except Exception as e:
            r = {"slug": slug, "error": f"{type(e).__name__}: {e}"}
        if "error" in r:
            print(f"  ❌ {r['error']}")
        else:
            total = r.get("total_share", 0)
            count = r.get("new_count", 0)
            ok = "✅" if 95 <= total <= 105 else f"⚠️ total={total}%"
            print(f"  {ok} 写入 {count} 条 employment_direction (合计 {total}%)")
        results.append(r)

    ok = [r for r in results if "error" not in r]
    print(f"\n{'='*60}\n汇总: {len(ok)}/{len(results)} 修复成功")
    if ok:
        bad = [r for r in ok if not (95 <= r.get("total_share", 0) <= 105)]
        if bad:
            print("⚠️ 占比不约 100% 的:")
            for r in bad:
                print(f"  - {r['title']}: {r['total_share']}%")


if __name__ == "__main__":
    main()
