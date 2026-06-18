#!/usr/bin/env python3
"""
content_audit.py — 用 m3 (主模型) 评估一批专业的**内容质量** (非结构).

跟 audit_content_relevance 区别:
  - audit_content_relevance: deepseek/mimo 评 0-10, 偏 schema 漂移检查
  - content_audit:           m3 评 0-10, 偏 内容深度/真实性/具体性/区分度

评分维度 (1-10 整体):
  1. lede 是否有"主语+独特洞察" (而不是通用空话)
  2. salary 数字是否符合该专业实际 (应届 5-30 万, 资深 30-100 万)
  3. curriculum 是否对得上这个专业 (不串到其他专业)
  4. top_schools 是不是真的在这个专业强 (避免随机名校)
  5. alumni_quotes 是否具体 (有"我修了 X 课"细节, 不是空话)
  6. deep_study 路径分布是否合理 (不会 90% 都读研, 也不会 90% 都就业)
  7. pitfalls 是否是"只有这个专业才有的坑" (不是通用的"学习累"等)

用法:
  python3 scripts/batches/content_audit.py --csv scripts/batches/engineering_a_v1.csv
  python3 scripts/batches/content_audit.py --slugs optoelectronic-information-science-engineering
"""
import sys, os, json, csv, argparse, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scf"))

from synth.llm import M3Client  # noqa: E402

CUR = ROOT / "skills/gaokao-major-explorer/data/curated"

AUDIT_PROMPT = """你是中国高考专业内容质量评估员. 严格检查下面这份"专业深度报告 JSON"的内容质量 (不是格式/结构).

【专业】: {title}
【style】: {style}

【要审计的字段 (按重要性排序)】:
1. lede (前 100 字摘要) — 是否有"主语 + 独特洞察"? 还是"X 是一个重要专业, 培养 Y 能力"这种空话?
2. salary 数字 — 数字范围是否符合该专业实际? 应届生 (一线) 5-25 万, 资深 30-100 万. 太离谱 = 失真.
3. curriculum 课程 — 是否真的属于这个专业? (e.g. 通信工程的课应该出现"信号与系统/通信原理", 不能是"法理学")
4. top_schools — 这些学校真的在这个专业强吗? 避免"清北复交 通用名校"凑数.
5. alumni_quotes — 是否有具体细节 (修了什么课/做过什么项目)? 还是空话"这个专业很好"?
6. deep_study 路径分布 — 5-7 条路径百分比加起来 ≈ 100. 不会 90% 都读研, 也不会全是"直接就业".
7. pitfalls — 是否是"只有这个专业才有的坑"? 还是通用的"学习累"?

【JSON 数据】:
{json_str}

【输出 JSON 格式】 (必须严格按此输出):
{{
  "overall_score": <0-10 整数, 7+ 算合格>,
  "verdict": "<优秀/合格/可接受/差评>",
  "highlights": ["写得好的 1-2 点"],
  "issues": [
    {{"field": "lede", "score": 8, "issue": "具体哪里有问题"}},
    {{"field": "salary", "score": 6, "issue": "应届生 30 万过高"}},
    ...
  ],
  "fix_suggestion": "1-2 句总结, 怎么改"
}}
"""


def audit_one(client: M3Client, slug: str, title: str, style: str) -> dict:
    p = CUR / f"{slug}.json"
    if not p.exists():
        return {"slug": slug, "title": title, "error": "json 缺失"}
    data = json.loads(p.read_text(encoding="utf-8"))
    # 截断过大的字段 (避免 token 爆)
    data_copy = dict(data)
    if "curriculum" in data_copy and isinstance(data_copy["curriculum"], dict):
        for k, v in data_copy["curriculum"].items():
            if isinstance(v, list) and len(v) > 10:
                data_copy["curriculum"][k] = v[:8] + ["..."]
    if "top_schools" in data_copy and isinstance(data_copy["top_schools"], list):
        data_copy["top_schools"] = data_copy["top_schools"][:10]
    json_str = json.dumps(data_copy, ensure_ascii=False, indent=2)
    if len(json_str) > 6000:
        json_str = json_str[:6000] + "\n... (truncated)"

    prompt = AUDIT_PROMPT.format(title=title, style=style, json_str=json_str)
    payload = client._call({
        "model": client.model,
        "max_tokens": 16000,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    })
    text = client._extract_text(payload)
    # 抽 JSON
    import re
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {"slug": slug, "title": title, "error": f"audit 返回非 JSON: {text[:200]}"}
    try:
        result = json.loads(m.group(0))
    except Exception as e:
        return {"slug": slug, "title": title, "error": f"JSON parse: {e}: {text[:200]}"}
    result["slug"] = slug
    result["title"] = title
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="CSV (列: slug,title,style)")
    ap.add_argument("--slugs", nargs="*", help="slug:style (e.g. mechanical-engineering:eng)")
    ap.add_argument("--limit", type=int, default=0)
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

    if args.limit:
        pairs = pairs[:args.limit]

    client = M3Client(enable_thinking=True)
    print(f"🔍 内容质量审计: {len(pairs)} 篇, auditor=m3, enable_thinking=True")
    print(f"{'='*80}")

    results = []
    for i, (slug, title, style) in enumerate(pairs, 1):
        print(f"\n[{i}/{len(pairs)}] {title} ({style})")
        try:
            r = audit_one(client, slug, title, style)
        except Exception as e:
            r = {"slug": slug, "title": title, "error": f"{type(e).__name__}: {e}"}
        if "error" in r:
            print(f"  ❌ {r['error']}")
        else:
            score = r.get("overall_score", "?")
            verdict = r.get("verdict", "?")
            issues_count = len(r.get("issues", []))
            print(f"  📊 {score}/10  {verdict}  ({issues_count} 项问题)")
            for iss in r.get("issues", []):
                s = iss.get("score")
                if s is None or s < 7:
                    print(f"    ⚠️  {iss.get('field','')} ({iss.get('score','?')}/10): {iss.get('issue','')}")
        results.append(r)

    # 汇总
    ok = [r for r in results if "error" not in r]
    if ok:
        avg = sum(r.get("overall_score", 0) for r in ok) / len(ok)
        print(f"\n{'='*80}")
        print(f"汇总: {len(ok)}/{len(results)} 审计成功, 平均分 {avg:.2f}/10")
        # 列出 < 7 的需要修复
        bad = [r for r in ok if (r.get("overall_score") or 0) < 7]
        if bad:
            print(f"\n需修复 (score < 7):")
            for r in bad:
                print(f"  ❌ {r.get('title', r.get('slug'))}: {r.get('overall_score')}/10 — {r.get('fix_suggestion', '')}")
    else:
        print(f"\n❌ 0 篇审计成功")

    # 输出 JSON 报告
    out = ROOT / "test_results" / f"content_audit_{int(time.time())}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 详细报告: {out}")

    # ──────────────────────────────────────────────────────────
    # 自动 sync 进 data/audit_registry.json (git tracked 单一真相)
    # 失败不中断: audit 已落盘, registry 是派生视图
    # ──────────────────────────────────────────────────────────
    import subprocess
    reg_script = ROOT / "scripts" / "update_audit_registry.py"
    if reg_script.exists():
        try:
            r = subprocess.run(
                ["python3", str(reg_script), "--from-file", str(out)],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode == 0:
                print(f"🔗 已 sync → data/audit_registry.json: {r.stdout.strip()}")
            else:
                print(f"⚠️  update_audit_registry 退出 {r.returncode}: {r.stderr.strip()[:200]}")
        except Exception as e:
            print(f"⚠️  registry sync 失败: {e} (audit 报告 {out.name} 已落盘, 可手动 python3 scripts/update_audit_registry.py --from-file {out.name})")
    else:
        print(f"⚠️  未找到 {reg_script}, 跳过 registry sync")


if __name__ == "__main__":
    main()
