"""
synth/llm.py — DeepSeek 客户端 (Anthropic SDK 兼容).

DeepSeek 提供 Anthropic 兼容端点, base_url = "https://api.deepseek.com/anthropic"
文档: https://api-docs.deepseek.com/guides/anthropic_api

3 method:
  validate_is_major(name, ctx)         -> bool   0-shot 判定
  route_style(name, summary)           -> str    13-style 路由
  synthesize_json(name, style, ctx)    -> dict   严格 JSON 输出

输出严控:
  - synthesize_json 强制 tool_choice, 失败抛 RetryableError 让上层反喂
  - token 计数在 response.usage 暴露
"""
from __future__ import annotations
import json
import os
import re
from typing import Any

try:
    from anthropic import Anthropic
except ImportError as e:  # noqa: F401
    raise ImportError(
        "synth.llm 需要 anthropic SDK, 请 pip install 'anthropic>=0.39'"
    ) from e

from .validator import VALID_STYLES

DEEPSEEK_BASE = "https://api.deepseek.com/anthropic"
DEFAULT_MODEL = "deepseek-chat"  # DeepSeek-V3


class RetryableError(Exception):
    """可重试的 LLM 错误 (network / parse)."""


class PermanentError(Exception):
    """不可恢复错误 (key 错 / 配额满)."""


class DeepSeekClient:
    """DeepSeek 客户端封装."""

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise PermanentError("DEEPSEEK_API_KEY 未配置")
        self.client = Anthropic(api_key=self.api_key, base_url=DEEPSEEK_BASE)
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    # ── 1. 验证是否本科专业 ──
    def validate_is_major(self, name: str) -> tuple[bool, str]:
        """
        0-shot 判定 name 是否为中国本科专业.

        Returns: (is_major, normalized_name)
            - is_major: True/False
            - normalized_name: 若是,返回标准中文全称;若否,返回原 name
        """
        prompt = f"""判断以下字符串是否为中国普通高等学校本科专业目录中的专业名 (包括 14 个学科门类下的所有本科专业, 不含专科/高职/职业培训):

输入: "{name}"

如果是本科专业, 用 JSON 回答: {{"is_major": true, "normalized": "标准专业全称中文"}}
如果不是 (比如是人名/公司名/无意义词/培训机构/专科专业), 用 JSON 回答: {{"is_major": false, "reason": "原因"}}

只输出 JSON, 不要 markdown 代码块, 不要多余解释."""

        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            raise RetryableError(f"DeepSeek API 失败: {e}") from e

        self._track_usage(resp)
        text = self._extract_text(resp)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # 尝试从 markdown 块抽取
            m = re.search(r"\{[^{}]+\}", text, re.DOTALL)
            if not m:
                raise RetryableError(f"validate_is_major 返回非 JSON: {text[:200]}")
            data = json.loads(m.group(0))
        return bool(data.get("is_major")), str(data.get("normalized") or name)

    # ── 2. 主题路由 ──
    def route_style(self, title: str, summary: str = "") -> str:
        """
        0-shot 把专业路由到 13 个合法 style 之一.
        """
        style_list = "|".join(sorted(VALID_STYLES))
        style_desc = (
            "cs=计算机/AI/软件/数据;eng=工科/机械/电子/材料/船舶;"
            "medicine=医学/药学/护理/口腔/中医;education=教育/心理/英语/新闻;"
            "finance=经济/金融/会计/工商/国贸/保险;law=法学/政治/社会学;"
            "humanities=中文/历史/哲学/考古/翻译/广告;administration=公管/图情/信管/人力;"
            "agri=农学/园艺/林学/动物/茶学;arts=美术/设计/动画/数媒;"
            "sci=数学/物理/化学/生物/地理/地质/大气;gongan=公安/司法/警察/治安/犯罪;"
            "business=工商管理类(保险/审计/营销/物流/电商等)"
        )
        prompt = f"""为以下本科专业选择一个最适合的展示主题 (style), 用于网页视觉风格:

专业: {title}
简介: {summary or "(无)"}

可选 style 及其代表: {style_desc}

返回 JSON: {{"style": "<{style_list}>", "reason": "一句话理由"}}

只输出 JSON, 不要 markdown, 不要多余解释."""

        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            raise RetryableError(f"DeepSeek route_style 失败: {e}") from e

        self._track_usage(resp)
        text = self._extract_text(resp)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{[^{}]+\}", text, re.DOTALL)
            if not m:
                raise RetryableError(f"route_style 返回非 JSON: {text[:200]}")
            data = json.loads(m.group(0))
        chosen = str(data.get("style", "")).strip()
        if chosen not in VALID_STYLES:
            raise RetryableError(f"route_style 返回非法 style: {chosen!r}")
        return chosen

    # ── 3. 合成 JSON ──
    def synthesize_json(
        self,
        title: str,
        style: str,
        search_context: str,
        sample_json: dict,
        schema_doc: str,
        previous_errors: list[str] | None = None,
        previous_warnings: list[str] | None = None,
    ) -> dict:
        """
        用 LLM 合成符合 schema 的完整 major JSON.
        失败时: 前一轮 errors 反喂, 让 LLM 修复 (≤3 轮).
        """
        retry_note = ""
        if previous_errors:
            retry_note += "\n\n【上轮校验失败,必须修复】\n" + "\n".join(f"- {e}" for e in previous_errors)
        if previous_warnings:
            retry_note += "\n\n【上轮警告,建议修复】\n" + "\n".join(f"- {w}" for w in previous_warnings)

        # 用 tool_choice 强制 JSON 输出 (Anthropic SDK 0.39+ 支持 tool_use)
        tool = {
            "name": "emit_major_json",
            "description": "输出符合 schema 的完整 major JSON, 严禁任何其他文本.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "kebab-case 英文 slug"},
                    "title": {"type": "string", "description": "标准中文专业全称"},
                    "category": {"type": "string", "description": "学科门类 · 专业类"},
                    "style": {"type": "string", "enum": list(VALID_STYLES)},
                    "degree": {"type": "string"},
                    "duration_years": {"type": "integer", "enum": [4, 5]},
                    "tags": {"type": "array", "items": {"type": "string"}, "minItems": 4},
                    "difficulty": {"type": "string"},
                    "updated_at": {"type": "string", "description": "YYYY-MM"},
                    "data_source": {"type": "string"},
                    "summary": {"type": "string", "description": "50-200 字 Hero lede"},
                    "hero_quote": {"type": "string"},
                    "hero_quote_sig": {"type": "string"},
                    "curriculum": {
                        "type": "object",
                        "description": "3 块以上, 含 公共必修/通用专业核心/5 校特色选修 3 个特殊 key",
                    },
                    "top_schools": {"type": "array", "minItems": 5},
                    "salary": {"type": "object", "description": "≥3 stage, 每 stage 含 p25/p50/p75/yoy"},
                    "employment_direction": {"type": "array", "minItems": 3},
                    "alumni_quotes": {"type": "array", "minItems": 2},
                    "xuanke_req_list": {"type": "array", "minItems": 3},
                    "deep_study": {"type": "object"},
                    "top_companies": {"type": "array"},
                    "overview_v2": {"type": "object"},
                },
                "required": ["slug", "title", "category", "style", "degree",
                             "duration_years", "tags", "summary", "curriculum",
                             "top_schools", "salary", "employment_direction",
                             "alumni_quotes", "xuanke_req_list"],
            },
        }

        prompt = f"""你是中国高考专业深度分析师, 要为 "{title}" 合成一份 2026 高考精品报告所需的完整 JSON.

**目标 style**: {style}

【Web 搜索原始素材 (提炼后)】
{search_context[:6000]}

【参考样板: 同 style 的现有精品 JSON 摘要】
{json.dumps(sample_json, ensure_ascii=False)[:4000]}

【输出 schema 规范摘要】
{schema_doc[:3000]}
{retry_note}

【反幻觉护栏】
- 排名/校友身份/薪资异常高时必须标"基于 2024 公开数据估算"或"未知"
- alumni_quotes 严禁出现 P8/P9/VP/CTO/CEO 等高帽身份
- 校友访谈标"基于 X 平台公开访谈综合"
- 学科评估等级 A+/A/B+ 必须有出处, 否则标"评估中"

请调用 emit_major_json tool 输出完整 JSON (严禁任何额外文本)."""

        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                temperature=0.4,
                tools=[tool],
                tool_choice={"type": "tool", "name": "emit_major_json"},
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            raise RetryableError(f"DeepSeek synthesize 失败: {e}") from e

        self._track_usage(resp)
        for block in resp.content:
            if block.type == "tool_use" and block.name == "emit_major_json":
                return block.input
        raise RetryableError("synthesize_json 未返回 tool_use 块")

    # ── 内部: 提取文本 / 累计 token ──
    def _extract_text(self, resp) -> str:
        for block in resp.content:
            if block.type == "text":
                return block.text
        return ""

    def _track_usage(self, resp):
        try:
            self.total_input_tokens += resp.usage.input_tokens
            self.total_output_tokens += resp.usage.output_tokens
        except Exception:
            pass

    def cost_estimate_cny(self) -> float:
        """DeepSeek-V3 定价: 1元/百万 token (input), 2元/百万 (output) [2026 估算]."""
        return (self.total_input_tokens * 1 + self.total_output_tokens * 2) / 1_000_000


# ── 便捷: 本地 CLI 调试 ──
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python llm.py <major_name>")
        sys.exit(1)
    name = sys.argv[1]
    c = DeepSeekClient()
    is_major, normalized = c.validate_is_major(name)
    print(f"validate_is_major: {is_major}, normalized={normalized!r}")
    if is_major:
        style = c.route_style(normalized)
        print(f"route_style: {style}")
    print(f"\n成本估算: {c.cost_estimate_cny():.4f} 元 (input {c.total_input_tokens}, output {c.total_output_tokens})")
