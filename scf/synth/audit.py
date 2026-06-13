"""
synth/audit.py — 内容相关性审计 (反 LLM 漂移护栏)

为什么需要这个:
  validator.py 只查字段格式 (curriculum ≥3 块, salary p25≤p75 等),
  查不出 "title 是保险学但内容是审计学" 的致命漂移.
  本模块让另一个 LLM (deepseek-v4-flash 便宜, 或 mimo-v2-flash 换思路)
  当审计员, 给每段打 0-10 分 + 标记漂移段.

用法:
  from scf.synth.audit import audit_content_relevance
  result = audit_content_relevance(data, title="保险学", auditor="deepseek")
  if result.overall_score < 8:
      print(f"漂移: {result.drift_segments}, 重生成")

4 组对照实验里这就是 B/C/D 组的 "审计员" 调用.
"""
from __future__ import annotations
import json
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Any
import urllib.request


# ── 审计结果数据类 ──
@dataclass
class SectionAudit:
    """单段审计结果."""
    name: str               # 字段名 (如 summary/curriculum/hero_quote)
    score: int              # 0-10, 10 = 完全在讲 X 专业
    reason: str             # 一句话理由
    drift: bool = False     # 是否明显漂移到其他专业


@dataclass
class AuditResult:
    """整体审计结果."""
    title: str
    auditor: str            # 用的什么 LLM (deepseek / mimo)
    overall_score: float    # 各段加权平均, 0-10
    passed: bool            # overall_score >= 8 算过
    sections: list[SectionAudit] = field(default_factory=list)
    drift_segments: list[str] = field(default_factory=list)  # 漂移段名
    raw_response: str = ""  # LLM 原话, debug 用
    cost_cny: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["sections"] = [asdict(s) for s in self.sections]
        return d


# ── 提取要审计的字段 (按重要性排序) ──
FIELDS_TO_AUDIT = [
    # (字段名, 最大字符数, 权重)
    ("title", 50, 3.0),                    # 标题最关键
    ("summary", 300, 3.0),                 # 总结也要紧
    ("hero_quote", 200, 2.0),              # hero 金句
    ("category", 50, 1.5),                 # 学科门类
    ("curriculum", 1200, 2.5),             # 课程 (拼成摘要送审)
    ("top_schools", 400, 1.5),             # 院校
    ("salary", 400, 1.0),                  # 薪资
    ("employment_direction", 400, 1.5),    # 就业方向
    ("alumni_quotes", 600, 2.0),           # 校友访谈 (高漂移区)
    ("overview_v2", 800, 2.5),             # 速览 (新模块)
]


def _extract_field_text(data: dict, field_name: str, max_chars: int) -> str:
    """把字段转成可读文本片段给审计员."""
    val = data.get(field_name)
    if val is None:
        return "(空)"
    if isinstance(val, str):
        return val[:max_chars]
    if isinstance(val, list):
        items = []
        for item in val[:8]:  # 至多 8 项
            if isinstance(item, dict):
                name = item.get("name") or item.get("dest") or item.get("school") or ""
                desc = item.get("desc") or item.get("quote") or item.get("tag") or ""
                items.append(f"- {name}: {desc}"[:200])
            else:
                items.append(str(item)[:100])
        return "\n".join(items)[:max_chars]
    if isinstance(val, dict):
        # curriculum / salary / overview_v2 等
        parts = []
        for k, v in list(val.items())[:10]:
            if isinstance(v, list):
                parts.append(f"[{k}]")
                for item in v[:5]:
                    if isinstance(item, dict):
                        parts.append(f"  - {item.get('name', '')}")
                    else:
                        parts.append(f"  - {item}")
            elif isinstance(v, dict):
                parts.append(f"[{k}] {json.dumps(v, ensure_ascii=False)[:200]}")
            else:
                parts.append(f"[{k}] {str(v)[:100]}")
        return "\n".join(parts)[:max_chars]
    return str(val)[:max_chars]


# ── 审计 prompt ──
AUDIT_PROMPT = """你是高考专业内容审计员. 任务: 检查以下 JSON 是否真的在描述 "{title}" 这个专业.

【专业】{title}

【逐段内容】

{field_blocks}

【评判规则】
- 10 分: 完全在讲 {title}, 内容准确 (课程/方向/院校都跟 {title} 强相关)
- 7-9 分: 主体是 {title}, 有少量泛化表述但不离谱
- 4-6 分: 50/50, 有明显涉及其他专业的痕迹 (比如讲会计时大量谈审计)
- 0-3 分: 内容明显是另一个专业, 不是 {title}

【特别警惕】相似专业互串:
  保险学 ↔ 金融学 ↔ 审计学 ↔ 会计学 ↔ 工商管理
  计算机科学 ↔ 软件工程 ↔ 人工智能 ↔ 数据科学
  临床医学 ↔ 基础医学 ↔ 麻醉学 ↔ 医学影像学
  法学 ↔ 政治学 ↔ 社会学 ↔ 马克思主义理论

【输出格式】只输出严格 JSON, 不要 markdown:
{{
  "sections": [
    {{"name": "summary", "score": 9, "reason": "聚焦风险定价+精算, 保险专属", "drift": false}},
    {{"name": "curriculum", "score": 10, "reason": "精算+保险原理都是保险学核心课", "drift": false}},
    {{"name": "alumni_quotes", "score": 3, "reason": "全在谈审计和会计师事务所, 与保险学无关", "drift": true}}
  ]
}}"""


def _build_prompt(title: str, data: dict) -> str:
    """拼审计 prompt."""
    blocks = []
    for fname, maxc, _ in FIELDS_TO_AUDIT:
        text = _extract_field_text(data, fname, maxc)
        blocks.append(f"## {fname}\n{text}\n")
    return AUDIT_PROMPT.format(title=title, field_blocks="\n".join(blocks))


# ── 调用 LLM (deepseek / mimo, 都 OpenAI 兼容; m3 走 anthropic) ──
def _call_auditor(prompt: str, auditor: str) -> tuple[str, float]:
    """
    调审计 LLM, 返 (raw_text, cost_cny).
    auditor ∈ {"deepseek", "mimo"}
    """
    auditor = auditor.lower()
    if auditor == "deepseek":
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/anthropic")
        model = os.environ.get("DEEPSEEK_AUDIT_MODEL", "deepseek-v4-flash")
        url = f"{base_url}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        body = {
            "model": model,
            "max_tokens": 2000,
            "temperature": 0.0,  # 审计要确定性
            "messages": [{"role": "user", "content": prompt}],
        }
    elif auditor == "mimo":
        api_key = os.environ.get("MIMO_API_KEY", "")
        base_url = os.environ.get("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
        model = os.environ.get("MIMO_MODEL", "mimo-v2-flash")
        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        body = {
            "model": model,
            "max_completion_tokens": 2000,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": prompt}],
        }
    else:
        raise ValueError(f"未知 auditor: {auditor} (可选: deepseek / mimo)")

    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"{auditor} 审计调用失败: {e}") from e

    # 抽文本
    text = ""
    if auditor == "deepseek":
        for block in payload.get("content", []):
            if block.get("type") == "text":
                text = block.get("text", "")
                break
        usage = payload.get("usage", {})
        in_t = usage.get("input_tokens", 0)
        out_t = usage.get("output_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)
        # V4 Flash 定价: 缓存命中 ¥0.02/M, 未命中 ¥1/M input, 输出 ~¥2/M (估算)
        cost = (cache_read * 0.02 + (in_t - cache_read) * 1.0 + out_t * 2.0) / 1_000_000
    else:  # mimo (OpenAI 格式)
        choices = payload.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "")
        usage = payload.get("usage", {})
        in_t = usage.get("prompt_tokens", 0)
        out_t = usage.get("completion_tokens", 0)
        # mimo 降价后约 deepseek 水平 (按 ¥1/M input, ¥2/M output 估)
        cost = (in_t * 1.0 + out_t * 2.0) / 1_000_000
    return text, cost


def _parse_audit_response(text: str, weights: dict[str, float]) -> tuple[list[SectionAudit], float]:
    """解 LLM 返回的 JSON, 加权算总分."""
    # 1. 直接 parse
    data = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        pass
    # 2. 抽 ```json ... ```
    if data is None:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    # 3. 抽第一个 {...}
    if data is None:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                pass

    if data is None or "sections" not in data:
        # 解析失败 → 所有段都按低分 (5) 处理, 触发人工复核
        return [SectionAudit(name="<parse_fail>", score=5, reason=f"LLM 返回非 JSON: {text[:100]}")], 5.0

    sections = []
    total_weight = 0.0
    weighted_sum = 0.0
    for s in data.get("sections", []):
        if not isinstance(s, dict):
            continue
        sec = SectionAudit(
            name=str(s.get("name", "?")),
            score=int(s.get("score", 5)),
            reason=str(s.get("reason", "")),
            drift=bool(s.get("drift", False)),
        )
        sections.append(sec)
        w = weights.get(sec.name, 1.0)
        total_weight += w
        weighted_sum += sec.score * w

    overall = weighted_sum / total_weight if total_weight else 5.0
    return sections, round(overall, 2)


def audit_content_relevance(
    data: dict,
    title: str,
    auditor: str = "deepseek",
    pass_threshold: float = 8.0,
) -> AuditResult:
    """
    主入口: 审计一个 JSON 是否真在讲 `title` 专业.

    Returns:
        AuditResult 含:
          - overall_score (0-10): 加权平均
          - passed: overall >= pass_threshold
          - drift_segments: 漂移段名 (drift=True 的)
          - sections: 每段详细
          - cost_cny: 本次审计花费
    """
    prompt = _build_prompt(title, data)
    text, cost = _call_auditor(prompt, auditor)
    weights = {fname: w for fname, _, w in FIELDS_TO_AUDIT}
    sections, overall = _parse_audit_response(text, weights)
    drift_segs = [s.name for s in sections if s.drift]
    return AuditResult(
        title=title,
        auditor=auditor,
        overall_score=overall,
        passed=overall >= pass_threshold and not drift_segs,
        sections=sections,
        drift_segments=drift_segs,
        raw_response=text,
        cost_cny=round(cost, 6),
    )


# ── CLI ──
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python audit.py <path/to/major.json> [auditor]")
        print("  auditor: deepseek (默认) / mimo")
        sys.exit(1)
    path = sys.argv[1]
    auditor = sys.argv[2] if len(sys.argv) > 2 else "deepseek"
    data = json.loads(open(path, encoding="utf-8").read())
    title = data.get("title", "")
    print(f"审计 {title} 用 {auditor}...")
    r = audit_content_relevance(data, title=title, auditor=auditor)
    print(f"\n=== 总分 {r.overall_score}/10 {'✅ 通过' if r.passed else '❌ 不通过'} ===")
    print(f"花费: ¥{r.cost_cny:.4f}")
    if r.drift_segments:
        print(f"漂移段: {r.drift_segments}")
    print(f"\n分段:")
    for s in r.sections:
        flag = "🚨" if s.drift else ("✓" if s.score >= 8 else "⚠️")
        print(f"  {flag} {s.name:25s} {s.score:>2d}/10  {s.reason[:80]}")