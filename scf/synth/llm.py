"""
synth/llm.py — DeepSeek 客户端 (raw HTTP, 不用 anthropic SDK).

为什么不用 SDK: anthropic SDK 0.97+ 在某些环境下会自动注入 Claude 自家 auth token
(Authorization: Bearer sk-cp-...), 覆盖用户提供的 base_url + api_key, 导致
DeepSeek 端 401. 用 raw HTTP 完全可控.

DeepSeek Anthropic 兼容端点: https://api.deepseek.com/anthropic
  Headers:
    Content-Type: application/json
    x-api-key: <DEEPSEEK_API_KEY>
    anthropic-version: 2023-06-01

3 method:
  validate_is_major(name, ctx)         -> bool   0-shot 判定
  route_style(name, summary)           -> str    13-style 路由
  synthesize_json(name, style, ctx)    -> dict   严格 JSON 输出 (tool_use 模拟)
"""
from __future__ import annotations
import json
import os
import re
import urllib.request
import urllib.error
from typing import Any

from .validator import VALID_STYLES

DEEPSEEK_BASE = "https://api.deepseek.com/anthropic"
DEFAULT_MODEL = "deepseek-chat"  # DeepSeek-V3, anthropic 端点用这个名


class RetryableError(Exception):
    """可重试的 LLM 错误 (network / parse)."""


class PermanentError(Exception):
    """不可恢复错误 (key 错 / 配额满)."""


class DeepSeekClient:
    """DeepSeek raw HTTP 客户端 (Anthropic 兼容)."""

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise PermanentError("DEEPSEEK_API_KEY 未配置")
        self.model = model
        self.base_url = DEEPSEEK_BASE
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    # ── raw HTTP 调 LLM ──
    def _call(self, body: dict, expect_tool: bool = False) -> dict:
        url = f"{self.base_url}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:500]
            if e.code in (401, 403):
                raise PermanentError(f"DeepSeek auth 失败 ({e.code}): {err_body}") from e
            raise RetryableError(f"DeepSeek HTTP {e.code}: {err_body}") from e
        except urllib.error.URLError as e:
            raise RetryableError(f"DeepSeek 网络失败: {e}") from e

        # token 累计
        try:
            self.total_input_tokens += payload["usage"]["input_tokens"]
            self.total_output_tokens += payload["usage"]["output_tokens"]
        except (KeyError, TypeError):
            pass
        return payload

    # ── 1. validate_is_major ──
    def validate_is_major(self, name: str) -> tuple[bool, str]:
        prompt = f"""判断以下字符串是否为中国普通高等学校本科专业目录中的专业名 (包括 14 个学科门类下的所有本科专业, 不含专科/高职/职业培训):

输入: "{name}"

如果是本科专业, 用 JSON 回答: {{"is_major": true, "normalized": "标准专业全称中文"}}
如果不是 (比如是人名/公司名/无意义词/培训机构/专科专业), 用 JSON 回答: {{"is_major": false, "reason": "原因"}}

只输出 JSON, 不要 markdown 代码块, 不要多余解释."""
        try:
            payload = self._call({
                "model": self.model,
                "max_tokens": 200,
                "temperature": 0.0,
                "messages": [{"role": "user", "content": prompt}],
            })
        except (RetryableError, PermanentError):
            raise
        text = self._extract_text(payload)
        data = self._parse_json_loose(text, expect_keys=("is_major",))
        return bool(data.get("is_major")), str(data.get("normalized") or name)

    # ── 2. route_style ──
    def route_style(self, title: str, summary: str = "") -> str:
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
            payload = self._call({
                "model": self.model,
                "max_tokens": 200,
                "temperature": 0.0,
                "messages": [{"role": "user", "content": prompt}],
            })
        except (RetryableError, PermanentError):
            raise
        text = self._extract_text(payload)
        data = self._parse_json_loose(text, expect_keys=("style",))
        chosen = str(data.get("style", "")).strip()
        if chosen not in VALID_STYLES:
            raise RetryableError(f"route_style 返回非法 style: {chosen!r}")
        return chosen

    # ── 3. synthesize_json (用 tool_use 强制 JSON 输出) ──
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
        retry_note = ""
        if previous_errors:
            retry_note += "\n\n【上轮校验失败,必须修复】\n" + "\n".join(f"- {e}" for e in previous_errors)
        if previous_warnings:
            retry_note += "\n\n【上轮警告,建议修复】\n" + "\n".join(f"- {w}" for w in previous_warnings)

        tool = {
            "name": "emit_major_json",
            "description": "输出符合 schema 的完整 major JSON, 严禁任何其他文本.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "title": {"type": "string"},
                    "category": {"type": "string"},
                    "style": {"type": "string", "enum": list(VALID_STYLES)},
                    "degree": {"type": "string"},
                    "duration_years": {"type": "integer", "enum": [4, 5]},
                    "tags": {"type": "array", "items": {"type": "string"}, "minItems": 4},
                    "difficulty": {"type": "string"},
                    "updated_at": {"type": "string"},
                    "data_source": {"type": "string"},
                    "summary": {"type": "string"},
                    "hero_quote": {"type": "string"},
                    "hero_quote_sig": {"type": "string"},
                    "curriculum": {"type": "object"},
                    "top_schools": {"type": "array", "minItems": 5},
                    "salary": {"type": "object"},
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
            payload = self._call({
                "model": self.model,
                "max_tokens": 8000,
                "temperature": 0.4,
                "tools": [tool],
                "tool_choice": {"type": "tool", "name": "emit_major_json"},
                "messages": [{"role": "user", "content": prompt}],
            })
        except (RetryableError, PermanentError):
            raise

        # 抽 tool_use input
        for block in payload.get("content", []):
            if block.get("type") == "tool_use" and block.get("name") == "emit_major_json":
                return block["input"]
        # fallback: 抽 text 里的 JSON
        text = self._extract_text(payload)
        if text:
            try:
                return self._parse_json_loose(text, expect_keys=("title", "style"))
            except RetryableError:
                pass
        raise RetryableError("synthesize_json 未返回 tool_use 块且 text 也无 JSON")

    # ── 内部 ──
    def _extract_text(self, payload: dict) -> str:
        for block in payload.get("content", []):
            if block.get("type") == "text":
                return block.get("text", "")
        return ""

    def _parse_json_loose(self, text: str, expect_keys: tuple = ()) -> dict:
        # 1. 直接 parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # 2. 抽 ```json ... ``` 块
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        # 3. 抽第一个 {...}
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        raise RetryableError(f"LLM 返回非 JSON: {text[:200]}")

    def cost_estimate_cny(self) -> float:
        """DeepSeek-V3 定价: 1元/百万 input, 2元/百万 output."""
        return (self.total_input_tokens * 1 + self.total_output_tokens * 2) / 1_000_000


# ── 便捷 CLI 调试 ──
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python llm.py <major_name>")
        sys.exit(1)
    name = sys.argv[1]
    c = DeepSeekClient()
    is_major, normalized = c.validate_is_major(name)
    print(f"validate_is_major: ({is_major}, {normalized!r})")
    if is_major:
        style = c.route_style(normalized)
        print(f"route_style: {style}")
    print(f"\n成本估算: {c.cost_estimate_cny():.4f} 元 "
          f"(input {c.total_input_tokens}, output {c.total_output_tokens})")
