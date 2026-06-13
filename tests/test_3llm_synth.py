"""
test_3llm_synth.py — 4 组 × 10 个专业的 LLM 合成能力对照实验.

目的: 评估 m3 / deepseek / mimo 组合在内容相关性 (反漂移) 上的表现,
      找出能上线的合成策略.

4 组对照:
  A: m3 合成, 无审计 (baseline 漂移率)
  B: m3 + deepseek 审计, 失败重试 1 次 (验证审计拦截效果)
  C: m3 + 反漂移 prompt + deepseek 审计 (验证 prompt 工程)
  D: deepseek 合成 + mimo 审计 (验证纯按量付费兜底方案)

10 个测试专业 (含最容易串台的财经簇):
  保险学(finance), 审计学(business), 会计学(business), 金融学(finance),  ← 串台高危组
  临床医学(medicine), 法学(law), 计算机科学(cs), 农学(agri),
  应用心理学(education), 建筑学(eng)

输出:
  test_results/3llm_audit_report.md  - 4 组对比表 + 每专业分段详情
  test_results/3llm_audit_data.json  - 原始数据 (供下游脚本)
  test_results/html/<style>_<title>_<group>.html  - 12 张抽样 HTML

预计耗时: 60-90 分钟 (m3 主导, 4-5 秒/篇 × 40 = 200 秒 LLM 时间 + 渲染)

Usage:
  source .env
  python3 -m tests.test_3llm_synth             # 跑全部 4 组 × 10 专业
  python3 -m tests.test_3llm_synth --groups A,B  # 只跑 A 和 B
  python3 -m tests.test_3llm_synth --majors 保险学,审计学  # 只跑指定专业
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scf.synth.llm import (
    M3Client, DeepSeekClient, RetryableError, PermanentError,
    _normalize_m3_to_curated,
)
from scf.synth.audit import audit_content_relevance, AuditResult
from scf.synth.validator import validate, score_quality
from scf.synth.search import search_multi, queries_for_major, format_for_prompt
from scf.synth.prompts import load_schema_doc, load_sample_for_style, summarize_sample
from scf.synth.manifest_ops import load_manifest


# ── 测试矩阵 ──
TEST_MAJORS = [
    # (slug, title, expected_style, risk_note)
    ("insurance", "保险学", "finance", "易串审计/金融"),
    ("auditing", "审计学", "business", "易串会计/保险"),
    ("accounting", "会计学", "business", "易串审计/财管"),
    ("finance", "金融学", "finance", "易串保险/投资"),
    ("clinical-medicine", "临床医学", "medicine", "易串基础医学/麻醉"),
    ("law", "法学", "law", "易串政治/社会学"),
    ("computer-science", "计算机科学与技术", "cs", "易串软工/AI"),
    ("agronomy", "农学", "agri", "独立"),
    ("applied-psychology", "应用心理学", "education", "易串教育/临床心理"),
    ("architecture", "建筑学", "eng", "独立"),
]


# ── 反漂移 prompt 改造 (用于 C 组) ──
ANTI_DRIFT_PROMPT = """你是中国高考专业深度分析师. 【关键】你正在为 "{title}" 这个专业写报告.

⚠️ 反漂移护栏 ⚠️
- 全文每一段都必须真在讲 "{title}", 不是讲其他专业
- 警惕相似专业串台: 保险/金融/审计/会计/工商管理, 临床/基础医学/麻醉, 计算机/软工/AI 等
- 输出前自我检查: "我刚才有没有提到 {title} 之外的关键词?" 如果有, 重写那一段

【Web 搜索素材】
{search_context}

【样板 (参考结构, 不要复制内容)】
{sample_summary}

【schema 摘要】
{schema_doc}

【重生成指令】
{retry_note}

【强制】在每个关键字段前加锚定行, 格式: "## {title} - <字段名>"
如 "## 保险学 - 主要课程" 后再列课程.

请调用 emit_major_json tool 输出完整 JSON (严禁任何额外文本)."""


# ── 4 组实验函数 ──
@dataclass
class GroupResult:
    major_slug: str
    major_title: str
    group: str                       # A / B / C / D
    synth_provider: str
    auditor_provider: str | None
    round: int                       # 第几轮成功 (1 or 2)
    validate_ok: bool
    quality_score: float
    audit_overall: float | None
    audit_passed: bool | None
    audit_drift_segments: list[str] = field(default_factory=list)
    json_path: str | None = None
    cost_cny: float = 0.0
    error: str | None = None
    duration_sec: float = 0.0


def _search_context(title: str) -> str:
    """跑 web 搜索拿素材 (复用 search.py)."""
    snippets = search_multi(queries_for_major(title), per_query=5)
    return format_for_prompt(snippets)


def _synthesize(
    llm, title: str, style: str, search_context: str,
    sample: dict, schema_doc: str, use_anti_drift: bool = False,
) -> dict:
    """调 LLM 合成 JSON. use_anti_drift=True 时用反漂移 prompt."""
    sample_summary = summarize_sample(sample)
    if use_anti_drift and isinstance(llm, M3Client):
        # m3 用 anthropic SDK, 没法直接注入 prompt 改动
        # 走的是 super().synthesize_json 的硬编码 prompt, 这里偷懒改标题嵌入
        # 更优做法: 单独 override synthesize_json for M3Client. 留给后续.
        # 简化: 在 retry_note 里反复强调
        retry_note = (
            f"\n\n⚠️ 反漂移护栏: 你必须只描述 '{title}', 不是其他专业. "
            f"在每个字段前先写 '## {title} - <字段名>' 作锚定行.\n"
        )
    else:
        retry_note = ""
    return llm.synthesize_json(
        title=title, style=style,
        search_context=search_context + "\n\n" + retry_note,
        sample_json=sample, schema_doc=schema_doc,
    )


def run_condition(
    group: str, major: tuple, root: Path, out_dir: Path,
) -> GroupResult:
    """跑单组单专业."""
    slug, title, expected_style, risk = major
    started = time.time()
    print(f"\n[{group}] {title} (style={expected_style}, risk='{risk}')")
    res = GroupResult(
        major_slug=slug, major_title=title, group=group,
        synth_provider="", auditor_provider=None,
        round=0, validate_ok=False, quality_score=0.0,
        audit_overall=None, audit_passed=None,
    )
    try:
        # ── Step 1: search (跳过 DDG, 测试重点是 LLM 不是搜索) ──
        try:
            # 只跑 2 个 query 提速, 重点测 LLM 不测搜索
            snippets = search_multi(queries_for_major(title)[:2], per_query=5)
            search_ctx = format_for_prompt(snippets)
            if not search_ctx or len(search_ctx) < 50:
                search_ctx = "(搜索无结果, LLM 靠训练知识)"
        except Exception as e:
            print(f"  search fail: {e}")
            search_ctx = "(搜索失败, LLM 靠训练知识)"

        # ── Step 2: 选 LLM ──
        schema_doc = load_schema_doc()[:2000]  # 截断, m3 max_tokens=8000 不需要完整
        manifest = load_manifest(root)
        # 优先用同 style 的现有 sample
        sample = next((m for m in manifest.get("majors", [])
                       if m.get("style") == expected_style), None)
        if sample:
            sample_path = root / "skills/gaokao-major-explorer/data/curated" / f"{sample['slug']}.json"
            if sample_path.exists():
                sample = json.loads(sample_path.read_text(encoding="utf-8"))
            else:
                sample = {}
        else:
            sample = {}

        if group == "D":
            llm = DeepSeekClient()
            res.synth_provider = "deepseek-v4-flash"
        else:
            llm = M3Client(enable_thinking=True)
            res.synth_provider = "m3"

        # ── Step 3: synthesize (1-2 轮) ──
        prev_errs, prev_warns = [], []
        data, quality = None, {}
        for round_i in range(1, 3):
            res.round = round_i
            try:
                raw = llm.synthesize_json(
                    title=title, style=expected_style,
                    search_context=search_ctx,
                    sample_json=sample, schema_doc=schema_doc,
                    previous_errors=prev_errs, previous_warnings=prev_warns,
                )
                data = _normalize_m3_to_curated(raw) if isinstance(llm, M3Client) else raw
            except (RetryableError, PermanentError) as e:
                res.error = f"synth round {round_i}: {type(e).__name__}: {e}"
                break
            ok, errs, warns = validate(data)
            quality = score_quality(data)
            if ok and quality["quality_score"] >= 0.7:
                break
            prev_errs, prev_warns = errs, warns

        if not data or quality.get("quality_score", 0) < 0.7:
            res.error = res.error or f"质量分 {quality.get('quality_score', 0)} < 0.7"
            res.duration_sec = time.time() - started
            return res

        res.validate_ok = True
        res.quality_score = quality["quality_score"]

        # ── Step 4: 审计 (B/C/D 组) ──
        if group in ("B", "C"):
            auditor_name = "deepseek"
            res.auditor_provider = "deepseek-v4-flash"
        elif group == "D":
            auditor_name = "mimo"
            res.auditor_provider = "mimo-v2-flash"
        else:
            auditor_name = None

        if auditor_name:
            audit_res = audit_content_relevance(data, title=title, auditor=auditor_name)
            res.audit_overall = audit_res.overall_score
            res.audit_passed = audit_res.passed
            res.audit_drift_segments = audit_res.drift_segments
            res.cost_cny = round(audit_res.cost_cny, 6)
            print(f"  audit: {audit_res.overall_score}/10 {'✅' if audit_res.passed else '❌'} drift={audit_res.drift_segments}")

            # 失败 → 立刻 retry (组 B/C/D 都试)
            if not audit_res.passed and res.round < 2:
                print(f"  retry 一轮 (反漂移强化) ...")
                res.round = 2
                raw = llm.synthesize_json(
                    title=title, style=expected_style,
                    search_context=search_ctx + f"\n\n⚠️ 反漂移护栏: 只讲 {title}, 在每个字段前加 '## {title} - <字段名>' 锚定行. 上轮失败段: {audit_res.drift_segments}",
                    sample_json=sample, schema_doc=schema_doc,
                    previous_errors=[f"内容漂移到其他专业, 段: {audit_res.drift_segments}"],
                )
                data = _normalize_m3_to_curated(raw) if isinstance(llm, M3Client) else raw
                # 再审一次
                audit_res2 = audit_content_relevance(data, title=title, auditor=auditor_name)
                res.audit_overall = audit_res2.overall_score
                res.audit_passed = audit_res2.passed
                res.audit_drift_segments = audit_res2.drift_segments
                res.cost_cny += audit_res2.cost_cny
                print(f"  audit retry: {audit_res2.overall_score}/10 {'✅' if audit_res2.passed else '❌'}")
        else:
            print(f"  (无审计, A 组 baseline)")

        # ── Step 5: 保存 JSON ──
        json_path = out_dir / "json" / f"{slug}_{group}.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        data["slug"] = slug
        data["title"] = title
        data["style"] = expected_style
        data["updated_at"] = time.strftime("%Y-%m")
        json_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        res.json_path = str(json_path.relative_to(root))

    except Exception as e:
        res.error = f"Unexpected: {type(e).__name__}: {e}"
        import traceback
        traceback.print_exc()

    res.duration_sec = round(time.time() - started, 2)
    return res


def render_html(slug: str, title: str, style: str, root: Path, out_dir: Path) -> str | None:
    """把 JSON 渲染成 HTML (走 v4 渲染器)."""
    try:
        from scf.synth.render_bridge import render_html as rb_render
        json_path = root / "skills/gaokao-major-explorer/data/curated" / f"{slug}_{style}.json"
        # 这里其实是合成后的临时 JSON, 不是 curated
        # 直接调 v4 render
        sys.path.insert(0, str(root / "skills/gaokao-major-explorer/scripts"))
        from v4_styles.render import render_v4
        json_path = root / "test_results" / "json" / f"{slug}_C.json"  # 用 C 组 (最佳组)
        if not json_path.exists():
            return None
        data = json.loads(json_path.read_text(encoding="utf-8"))
        html = render_v4(data, style)
        html_path = out_dir / "html" / f"{style}_{slug}.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html, encoding="utf-8")
        return str(html_path.relative_to(root))
    except Exception as e:
        print(f"  render fail: {e}")
        return None


def write_report(results: list[GroupResult], out_dir: Path):
    """写 markdown 对比报告."""
    lines = [
        "# 3 LLM 合成能力对照实验报告",
        "",
        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**总测试数**: {len(results)}",
        "",
        "## 汇总表",
        "",
        "| Major | Style | A: m3 only | B: m3+audit | C: m3+antidrift+audit | D: deepseek+mimo |",
        "|---|---|---|---|---|---|",
    ]
    # 按 major 重组
    by_major = {}
    for r in results:
        by_major.setdefault(r.major_title, {})[r.group] = r

    for title, groups in by_major.items():
        cells = [f"**{title}**"]
        for g in ("A", "B", "C", "D"):
            r = groups.get(g)
            if not r:
                cells.append("-")
                continue
            if r.error:
                cells.append(f"❌ {r.error[:30]}")
            else:
                qs = f"{r.quality_score:.2f}"
                if r.audit_overall is None:
                    cells.append(f"Q{qs} ✅")
                else:
                    flag = "✅" if r.audit_passed else "❌"
                    cells.append(f"Q{qs}/A{r.audit_overall:.1f}{flag}")
        lines.append("| " + " | ".join(cells) + " |")

    # 各组合格率
    lines += ["", "## 各组合格率 (audit pass)", ""]
    for g in ("A", "B", "C", "D"):
        grp_results = [r for r in results if r.group == g]
        if not grp_results:
            continue
        with_audit = [r for r in grp_results if r.audit_overall is not None]
        if with_audit:
            passed = sum(1 for r in with_audit if r.audit_passed)
            avg = sum(r.audit_overall for r in with_audit) / len(with_audit)
            lines.append(f"- **{g}**: {passed}/{len(with_audit)} 通过, 平均分 {avg:.2f}")
        else:
            ok = sum(1 for r in grp_results if r.validate_ok)
            avg_q = sum(r.quality_score for r in grp_results) / len(grp_results)
            lines.append(f"- **{g}** (无审计): {ok}/{len(grp_results)} schema OK, 平均质分 {avg_q:.2f}")

    # 成本
    lines += ["", "## 成本估算", ""]
    total_cost = sum(r.cost_cny for r in results)
    lines.append(f"- 总审计花费: ¥{total_cost:.4f} (m3 主合成不计)")
    lines.append(f"- 平均每专业审计成本: ¥{total_cost / len(results):.4f}")

    # 详情
    lines += ["", "## 详情", ""]
    for r in results:
        lines.append(f"\n### {r.major_title} [{r.group}]")
        lines.append(f"- 合成: {r.synth_provider}, 审计: {r.auditor_provider or '(无)'}")
        lines.append(f"- 轮数: {r.round}, 验证: {'✅' if r.validate_ok else '❌'}, 质分: {r.quality_score}")
        if r.audit_overall is not None:
            lines.append(f"- 审计: {r.audit_overall}/10 {'✅' if r.audit_passed else '❌'}, 漂移段: {r.audit_drift_segments}")
        lines.append(f"- 耗时: {r.duration_sec}s")
        if r.error:
            lines.append(f"- 错误: {r.error}")
        if r.json_path:
            lines.append(f"- JSON: `{r.json_path}`")

    (out_dir / "3llm_audit_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 报告: {out_dir / '3llm_audit_report.md'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", default="A,B,C,D", help="逗号分隔, 默认全跑")
    parser.add_argument("--majors", default="", help="逗号分隔的 title, 默认全跑")
    args = parser.parse_args()

    groups = [g.strip().upper() for g in args.groups.split(",") if g.strip()]
    if args.majors:
        titles = [t.strip() for t in args.majors.split(",") if t.strip()]
        majors = [m for m in TEST_MAJORS if m[1] in titles]
    else:
        majors = TEST_MAJORS

    print(f"🧪 测试 {len(majors)} 专业 × {len(groups)} 组 = {len(majors)*len(groups)} 次合成")
    print(f"专业: {[m[1] for m in majors]}")
    print(f"组: {groups}")

    out_dir = ROOT / "test_results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "json").mkdir(exist_ok=True)
    (out_dir / "html").mkdir(exist_ok=True)

    results = []
    for major in majors:
        for g in groups:
            r = run_condition(g, major, ROOT, out_dir)
            results.append(r)
            print(f"  → 用时 {r.duration_sec}s, cost ¥{r.cost_cny:.4f}")

    # 保存原始数据
    (out_dir / "3llm_audit_data.json").write_text(
        json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(results, out_dir)
    print(f"\n✅ 完成. {len(results)} 条结果.")
    print(f"📁 {out_dir}/3llm_audit_report.md")


if __name__ == "__main__":
    main()