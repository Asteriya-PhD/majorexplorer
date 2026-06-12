"""
synth/prompts.py — 3 个 prompt 模板 (synthesize / validate / route).

直接拼字符串, 不引入 jinja2 (减少 SCF 部署包大小).
LLM 调用在 llm.py, 本文件只管 prompt 内容.
"""
from __future__ import annotations
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_DOC = (ROOT / "docs" / "SYNTH_SCHEMA.md").read_text(encoding="utf-8")


# ── 1. synthesize (主合成 prompt, 在 llm.py 已经硬编码) ──
# 这里只暴露辅助函数, 避免 prompt 分散两处


def load_schema_doc() -> str:
    """返回 docs/SYNTH_SCHEMA.md 内容, 注入到 LLM prompt."""
    return SCHEMA_DOC


def load_sample_for_style(root: Path, style: str) -> dict:
    """
    选 1 篇同 style 的现有 60 精品作为 1-shot sample.
    优先选 tags 含 "按需生成" 标记的不在,
    否则从 manifest.majors 里筛同 style 的第一篇.
    """
    from scf.synth.manifest_ops import load_manifest
    m = load_manifest(root)
    candidates = [x for x in m.get("majors", []) if x.get("style") == style]
    if not candidates:
        return {}
    sample = candidates[0]
    slug = sample["slug"]
    json_path = root / "skills" / "gaokao-major-explorer" / "data" / "curated" / f"{slug}.json"
    if not json_path.exists():
        return {}
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def summarize_sample(data: dict, max_chars: int = 4000) -> str:
    """把 sample JSON 摘要为 LLM 参考 (截断长 list)."""
    if not data:
        return "(无同 style 样板, 请按 schema 自行构建)"
    out = {
        "title": data.get("title"),
        "category": data.get("category"),
        "degree": data.get("degree"),
        "duration_years": data.get("duration_years"),
        "tags": data.get("tags"),
        "difficulty": data.get("difficulty"),
        "summary": data.get("summary", "")[:200],
        "hero_quote": data.get("hero_quote"),
        "curriculum": _truncate_curriculum(data.get("curriculum", {})),
        "top_schools": (data.get("top_schools") or [])[:8],
        "salary": data.get("salary", {}),
        "employment_direction": (data.get("employment_direction") or [])[:5],
        "alumni_quotes": _truncate_quotes(data.get("alumni_quotes") or []),
        "xuanke_req_list": data.get("xuanke_req_list"),
        "deep_study": data.get("deep_study"),
    }
    s = json.dumps(out, ensure_ascii=False, indent=2)
    if len(s) > max_chars:
        s = s[:max_chars] + "\n...(截断)..."
    return s


def _truncate_curriculum(c: dict) -> dict:
    """每块只保留前 3 门课."""
    return {
        k: (v[:3] if isinstance(v, list) else v)
        for k, v in c.items()
    } if isinstance(c, dict) else {}


def _truncate_quotes(qs: list) -> list:
    """每条 quote 截前 100 字."""
    out = []
    for q in qs[:3]:
        if isinstance(q, dict):
            qq = dict(q)
            if "quote" in qq and len(qq["quote"]) > 100:
                qq["quote"] = qq["quote"][:100] + "..."
            out.append(qq)
    return out


# ── 2. 反喂 prompt: 把 validator 错误拼成修复指令 ──
def build_retry_prompt(errors: list[str], warnings: list[str]) -> str:
    """
    拼"上轮失败, 这是修复指令"片段, 注入到 synthesize_json 的 retry_note.
    """
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


# ── 3. 路由 prompt (与 llm.py 内一致, 留作 debug 用) ──
ROUTE_PROMPT = """为以下本科专业选择一个最适合的展示主题 (style), 用于网页视觉风格:

专业: {title}
简介: {summary}

可选 style 及其代表: {style_desc}

返回 JSON: {{"style": "<{style_list}>", "reason": "一句话理由"}}

只输出 JSON, 不要 markdown, 不要多余解释."""


# ── 4. validate_is_major prompt ──
VALIDATE_PROMPT = """判断以下字符串是否为中国普通高等学校本科专业目录中的专业名 (包括 14 个学科门类下的所有本科专业, 不含专科/高职/职业培训):

输入: "{name}"

如果是本科专业, 用 JSON 回答: {{"is_major": true, "normalized": "标准专业全称中文"}}
如果不是 (比如是人名/公司名/无意义词/培训机构/专科专业), 用 JSON 回答: {{"is_major": false, "reason": "原因"}}

只输出 JSON, 不要 markdown 代码块, 不要多余解释."""


STYLE_DESC = (
    "cs=计算机/AI/软件/数据;eng=工科/机械/电子/材料/船舶;"
    "medicine=医学/药学/护理/口腔/中医;education=教育/心理/英语/新闻;"
    "finance=经济/金融/会计/工商/国贸/保险;law=法学/政治/社会学;"
    "humanities=中文/历史/哲学/考古/翻译/广告;administration=公管/图情/信管/人力;"
    "agri=农学/园艺/林学/动物/茶学;arts=美术/设计/动画/数媒;"
    "sci=数学/物理/化学/生物/地理/地质/大气;gongan=公安/司法/警察/治安/犯罪;"
    "business=工商管理类(保险/审计/营销/物流/电商等)"
)
