"""
synth/validator.py — JSON schema 校验 + 5 维质量分.

与 docs/SYNTH_SCHEMA.md 严格对齐.
校验失败时返回 (False, issues[]) 供反喂 prompt.
"""
from __future__ import annotations
from typing import Any

# 13 个合法 style (与 generate_dashboard.py:16 STYLE_TOKENS 一致)
VALID_STYLES = {
    "cs", "eng", "medicine", "education", "finance", "law",
    "humanities", "sci", "administration", "agri", "arts",
    "gongan", "business",
}

# curriculum 3 个特殊 key (渲染器 line 67-75 严格识别)
CURRICULUM_SPECIAL_KEYS = {"公共必修", "通用专业核心", "5 校特色选修"}


# ── 顶层必填字段 ──
REQUIRED_TOP = [
    "slug", "title", "category", "style", "degree", "duration_years",
    "tags", "summary", "curriculum", "top_schools",
]
# 强必填 (缺则视觉崩坏)
STRICT_REQUIRED = [
    "salary", "employment_direction", "alumni_quotes",
    "xuanke_req_list", "data_source", "difficulty", "updated_at",
]


def _is_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def validate(data: dict) -> tuple[bool, list[str], list[str]]:
    """
    校验合成 JSON.

    Returns:
        (ok, errors, warnings)
        - ok: True/False
        - errors: 阻塞性错误,必须修复 (缺必填字段等)
        - warnings: 提示性警告,LLM 可选修复 (如校友身份含高帽)
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        return False, ["JSON 顶层不是对象"], []

    # ── 必填字段 ──
    for k in REQUIRED_TOP:
        if k not in data:
            errors.append(f"缺必填字段: {k}")

    for k in STRICT_REQUIRED:
        if k not in data:
            errors.append(f"缺强必填字段: {k}")

    # ── slug / title 格式 ──
    slug = data.get("slug", "")
    if slug and not isinstance(slug, str):
        errors.append("slug 不是字符串")
    if slug and not slug.replace("-", "").replace("_", "").isalnum():
        warnings.append(f"slug 含特殊字符: {slug!r} (建议仅 kebab-case)")

    # ── style 白名单 ──
    style = data.get("style")
    if style and style not in VALID_STYLES:
        errors.append(f"style 不合法: {style!r}, 必须是 {sorted(VALID_STYLES)}")

    # ── duration_years ──
    dur = data.get("duration_years")
    if dur is not None and (not _is_int(dur) or dur not in (4, 5)):
        errors.append(f"duration_years 必须是 4 或 5, 当前 {dur!r}")

    # ── tags ──
    tags = data.get("tags", [])
    if tags and (not isinstance(tags, list) or len(tags) < 4):
        errors.append(f"tags 必须是 list 且 ≥4 个, 当前 {len(tags) if isinstance(tags, list) else type(tags)}")
    elif tags and not all(_is_str(t) for t in tags):
        errors.append("tags 含有空字符串或非字符串元素")

    # ── summary 字数 ──
    summary = data.get("summary", "")
    if isinstance(summary, str):
        if len(summary) < 30:
            warnings.append(f"summary 过短 ({len(summary)} 字), 建议 50-200 字")
        if len(summary) > 300:
            warnings.append(f"summary 过长 ({len(summary)} 字), 建议 ≤200 字")

    # ── curriculum 块 ──
    curriculum = data.get("curriculum", {})
    if isinstance(curriculum, dict):
        if len(curriculum) < 3:
            errors.append(f"curriculum 至少 3 块, 当前 {len(curriculum)} 块")
        for block_name, courses in curriculum.items():
            if not isinstance(courses, list):
                errors.append(f"curriculum[{block_name!r}] 不是 list")
                continue
            if len(courses) < 3:
                errors.append(f"curriculum[{block_name!r}] 至少 3 门课, 当前 {len(courses)}")
            for i, c in enumerate(courses):
                if not isinstance(c, dict):
                    errors.append(f"curriculum[{block_name!r}][{i}] 不是 dict")
                    continue
                if not _is_str(c.get("name", "")):
                    errors.append(f"curriculum[{block_name!r}][{i}].name 缺失或空")
                credit = c.get("credit", "")
                if not (isinstance(credit, (str, int)) and str(credit).strip()):
                    errors.append(f"curriculum[{block_name!r}][{i}].credit 缺失")
    else:
        if "curriculum" in data:
            errors.append("curriculum 不是 dict")

    # ── top_schools ──
    top_schools = data.get("top_schools", [])
    if isinstance(top_schools, list):
        if len(top_schools) < 5:
            errors.append(f"top_schools 至少 5 个, 当前 {len(top_schools)}")
        for i, s in enumerate(top_schools):
            if not isinstance(s, dict):
                errors.append(f"top_schools[{i}] 不是 dict")
                continue
            if not _is_str(s.get("name", "")):
                errors.append(f"top_schools[{i}].name 缺失")
    elif "top_schools" in data:
        errors.append("top_schools 不是 list")

    # ── salary 三段 ──
    salary = data.get("salary", {})
    if isinstance(salary, dict):
        if len(salary) < 3:
            errors.append(f"salary 至少 3 阶段, 当前 {len(salary)}")
        for stage, vals in salary.items():
            if not isinstance(vals, dict):
                errors.append(f"salary[{stage!r}] 不是 dict")
                continue
            for f in ("p25", "p50", "p75"):
                if f not in vals or not isinstance(vals[f], (int, float)):
                    errors.append(f"salary[{stage!r}].{f} 缺失或非数字")
            if vals.get("p25", 0) > vals.get("p75", 0):
                errors.append(f"salary[{stage!r}] p25 > p75 异常")
            # 异常高薪警告
            if vals.get("p50", 0) > 80 and stage == "应届生":
                warnings.append(f"salary[{stage!r}] 应届 P50={vals.get('p50')} 异常高, 确认是真实数据")
    elif "salary" in data:
        errors.append("salary 不是 dict")

    # ── employment_direction ──
    directions = data.get("employment_direction", [])
    if isinstance(directions, list):
        if len(directions) < 3:
            errors.append(f"employment_direction 至少 3 项, 当前 {len(directions)}")
        for i, d in enumerate(directions):
            if not isinstance(d, dict):
                errors.append(f"employment_direction[{i}] 不是 dict")
                continue
            if not _is_str(d.get("name", "")):
                errors.append(f"employment_direction[{i}].name 缺失")
            pct = d.get("pct", -1)
            if not isinstance(pct, int) or not 0 <= pct <= 100:
                errors.append(f"employment_direction[{i}].pct 必须是 0-100 整数")
    elif "employment_direction" in data:
        errors.append("employment_direction 不是 list")

    # ── alumni_quotes ──
    quotes = data.get("alumni_quotes", [])
    if isinstance(quotes, list):
        if len(quotes) < 2:
            errors.append(f"alumni_quotes 至少 2 条, 当前 {len(quotes)}")
        for i, q in enumerate(quotes):
            if not isinstance(q, dict):
                errors.append(f"alumni_quotes[{i}] 不是 dict")
                continue
            if not _is_str(q.get("current", "")):
                errors.append(f"alumni_quotes[{i}].current 缺失")
            if not _is_str(q.get("quote", "")):
                errors.append(f"alumni_quotes[{i}].quote 缺失")
            # 反幻觉: 标"高帽"身份
            current = q.get("current", "")
            for high in ("P8", "P9", "VP", "CTO", "CEO"):
                if high in current:
                    warnings.append(f"alumni_quotes[{i}].current 含高帽身份 {high!r}, 确认真实性")
    elif "alumni_quotes" in data:
        errors.append("alumni_quotes 不是 list")

    # ── xuanke_req_list ──
    xuanke = data.get("xuanke_req_list", [])
    if isinstance(xuanke, list):
        if len(xuanke) < 3:
            errors.append(f"xuanke_req_list 至少 3 项, 当前 {len(xuanke)}")
    elif "xuanke_req_list" in data:
        errors.append("xuanke_req_list 不是 list")

    # ── difficulty 格式 ──
    diff = data.get("difficulty", "")
    if isinstance(diff, str) and diff:
        if not (1 <= diff.count("★") <= 5):
            warnings.append(f"difficulty 星级数异常: {diff!r} (期望 1-5 颗 ★)")

    # ── overview_v2 选填校验 ──
    if "overview_v2" in data:
        ov = data["overview_v2"]
        if not isinstance(ov, dict):
            errors.append("overview_v2 不是 dict")
        else:
            what = ov.get("what", {})
            if not isinstance(what, dict):
                errors.append("overview_v2.what 不是 dict (LLM 偶尔返回 string)")
            else:
                for k, mn in (("foundations", 3), ("directions", 3), ("skills", 3)):
                    arr = what.get(k, [])
                    if isinstance(arr, list) and len(arr) < mn:
                        warnings.append(f"overview_v2.what.{k} 推荐 ≥{mn} 项, 当前 {len(arr)}")
            # fit 必须是 dict (含 yes/no list), 不能是 string
            fit = ov.get("fit", {})
            if not isinstance(fit, dict):
                errors.append(
                    f"overview_v2.fit 必须是 dict (含 yes/no), 当前是 "
                    f"{type(fit).__name__}; LLM 误把 fit 合成长 string"
                )
            else:
                if not isinstance(fit.get("yes"), list) or len(fit["yes"]) < 3:
                    errors.append("overview_v2.fit.yes 必须是 list 且 ≥3 项")
                if not isinstance(fit.get("no"), list) or len(fit["no"]) < 2:
                    errors.append("overview_v2.fit.no 必须是 list 且 ≥2 项")
            # pitfalls 必须是 list[dict], 不能是 string
            pitfalls = ov.get("pitfalls", [])
            if not isinstance(pitfalls, list):
                errors.append(
                    f"overview_v2.pitfalls 必须是 list[{{myth, reality}}], "
                    f"当前是 {type(pitfalls).__name__}; LLM 误把 pitfalls 合成长 string"
                )
            elif len(pitfalls) < 2:
                errors.append(
                    f"overview_v2.pitfalls 至少 2 个误区, 当前 {len(pitfalls)}; "
                    f"LLM 偶尔返回空 list → render 写 ❌ title/❌ content 占位符"
                )
            else:
                for i, p in enumerate(pitfalls):
                    if not isinstance(p, dict) or not _is_str(p.get("myth", "")) or not _is_str(p.get("reality", "")):
                        errors.append(f"overview_v2.pitfalls[{i}] 必须是 dict 含 myth/reality 字符串")
                        break
                    if i >= 4:  # 看前 4 个就够
                        break

    return len(errors) == 0, errors, warnings


# ── 5 维质量分 (0-1) ──
def score_quality(data: dict) -> dict[str, float]:
    """
    5 维质量评分 (无 LLM 调用,纯规则).
    返回 dict: {data_completeness, anti_hallucination, visual_richness,
                language_fluency_proxy, format_conformance}

    整体 quality_score = 5 维加权均值.
    """
    scores: dict[str, float] = {}

    # 1. 数据完整性 (40%)
    completeness = 0.0
    total = 0.0
    for k in REQUIRED_TOP + STRICT_REQUIRED:
        total += 1
        if k in data and data[k]:
            completeness += 1
    # 长度奖励
    curriculum = data.get("curriculum", {})
    if isinstance(curriculum, dict) and len(curriculum) >= 3:
        total += 1
        completeness += 1
    if isinstance(data.get("top_schools"), list) and len(data["top_schools"]) >= 5:
        total += 1
        completeness += 1
    if "overview_v2" in data:
        total += 0.5
        completeness += 0.5
    scores["data_completeness"] = round(completeness / total, 3) if total else 0.0

    # 2. 反幻觉 (20%) — 反向分:warning 越多分越低
    ok, _, warnings = validate(data)
    hallucination = max(0.0, 1.0 - len(warnings) * 0.15)
    scores["anti_hallucination"] = round(hallucination, 3)

    # 3. 视觉丰富度 (15%) — sections 越多越丰富
    richness = 0.0
    for k in ("top_schools", "top_companies", "alumni_quotes",
              "employment_direction", "xuanke_req_list", "deep_study"):
        v = data.get(k, [])
        if isinstance(v, list) and len(v) >= 3:
            richness += 1
        elif isinstance(v, dict) and len(v) >= 2:
            richness += 1
    scores["visual_richness"] = round(min(1.0, richness / 5), 3)

    # 4. 语言流畅 proxy (15%) — summary/quote 长度合理
    fluency = 0.0
    summary = data.get("summary", "")
    if isinstance(summary, str) and 50 <= len(summary) <= 200:
        fluency += 0.5
    elif isinstance(summary, str) and len(summary) > 30:
        fluency += 0.25
    for q in data.get("alumni_quotes", []):
        if isinstance(q, dict) and 30 <= len(q.get("quote", "")) <= 300:
            fluency += 0.25
            break
    scores["language_fluency_proxy"] = round(min(1.0, fluency), 3)

    # 5. 格式合规 (10%) — 必填字段类型 + style 白名单
    conform = 0.0
    if data.get("style") in VALID_STYLES:
        conform += 0.4
    if data.get("duration_years") in (4, 5):
        conform += 0.2
    if isinstance(data.get("slug"), str) and data["slug"]:
        conform += 0.2
    if isinstance(data.get("tags"), list) and len(data["tags"]) >= 4:
        conform += 0.2
    scores["format_conformance"] = round(conform, 3)

    scores["quality_score"] = round(
        scores["data_completeness"] * 0.40
        + scores["anti_hallucination"] * 0.20
        + scores["visual_richness"] * 0.15
        + scores["language_fluency_proxy"] * 0.15
        + scores["format_conformance"] * 0.10,
        3,
    )
    return scores


# ── 便捷: 失败时给反喂 prompt 用的问题描述 ──
def format_for_retry(errors: list[str], warnings: list[str]) -> str:
    """把 errors/warnings 拼成 LLM 友好的反喂 prompt 片段."""
    lines = []
    if errors:
        lines.append("【必修复】以下字段缺失或格式错误, 必须按规范补充后重生成整篇 JSON:")
        for e in errors:
            lines.append(f"  ❌ {e}")
    if warnings:
        lines.append("【建议修复】以下项若数据允许请补充, 不允许则忽略:")
        for w in warnings:
            lines.append(f"  ⚠️  {w}")
    if not errors and not warnings:
        lines.append("✅ 校验通过, 无需修改.")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: python validator.py <path/to/major.json>")
        sys.exit(1)
    data = json.loads(open(sys.argv[1], encoding="utf-8").read())
    ok, errs, warns = validate(data)
    print(f"ok={ok}, errors={len(errs)}, warnings={len(warns)}")
    print(format_for_retry(errs, warns))
    print("\n质量分:")
    for k, v in score_quality(data).items():
        print(f"  {k:30s} {v}")
