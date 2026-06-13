"""
synth/llm.py — LLM 客户端 (raw HTTP, 不用 anthropic SDK).

为什么不用 SDK: anthropic SDK 0.97+ 在某些环境下会自动注入 Claude 自家 auth token
(Authorization: Bearer sk-cp-...), 覆盖用户提供的 base_url + api_key, 导致
DeepSeek/MiniMax 端 401. 用 raw HTTP 完全可控.

支持 2 个 provider (LLM_PROVIDER env var 选):
  - "m3"      → MiniMax-M3 (https://api.minimaxi.com/anthropic, token plan)
  - "deepseek" → DeepSeek-V3 (https://api.deepseek.com/anthropic)

Headers 通用:
  Content-Type: application/json
  x-api-key: <API_KEY>
  anthropic-version: 2023-06-01

3 method (同 interface, 工厂选 provider):
  validate_is_major(name, ctx)         -> tuple[bool, str]  0-shot 判定
  route_style(name, summary)           -> str               13-style 路由
  synthesize_json(name, style, ctx)    -> dict              严格 JSON 输出 (tool_use 模拟)

m3 专属:
  - 支持 enable_thinking=False 关掉 thinking 块提速 (默认 False, 速度优先)
  - response.content 会有 thinking + text 两类 block, 我们只取 text
"""
from __future__ import annotations
import json
import os
import re
import urllib.request
import urllib.error
from typing import Any

from .validator import VALID_STYLES

# ── Provider 端点 ──
M3_BASE = "https://api.minimaxi.com/anthropic"
M3_DEFAULT_MODEL = "MiniMax-M3"

DEEPSEEK_BASE = "https://api.deepseek.com/anthropic"
# V3 快过期, 改用 V4 Flash (快且便宜: 缓存命中 ¥0.02/M, 未命中 ¥1/M input)
DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-flash"


class RetryableError(Exception):
    """可重试的 LLM 错误 (network / parse)."""


class PermanentError(Exception):
    """不可恢复错误 (key 错 / 配额满)."""


# ─────────────────────────────────────────────────────────────
# 基础: Anthropic-compatible 客户端
# ─────────────────────────────────────────────────────────────
class _AnthropicCompatClient:
    """DeepSeek / MiniMax 共用 raw HTTP 客户端."""

    provider_name: str = "base"
    default_model: str = ""
    base_url: str = ""
    api_key_env: str = ""

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 enable_thinking: bool = False):
        self.api_key = api_key or os.environ.get(self.api_key_env, "")
        if not self.api_key:
            raise PermanentError(f"{self.api_key_env} 未配置")
        self.model = model or self.default_model
        self.enable_thinking = enable_thinking
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
        # m3 关 thinking 提速
        if not self.enable_thinking and self.provider_name == "m3":
            body.setdefault("thinking", {"type": "disabled"})

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:500]
            if e.code in (401, 403):
                raise PermanentError(
                    f"{self.provider_name} auth 失败 ({e.code}): {err_body}"
                ) from e
            raise RetryableError(f"{self.provider_name} HTTP {e.code}: {err_body}") from e
        except urllib.error.URLError as e:
            raise RetryableError(f"{self.provider_name} 网络失败: {e}") from e

        # token 累计
        try:
            usage = payload["usage"]
            self.total_input_tokens += usage["input_tokens"]
            self.total_output_tokens += usage["output_tokens"]
            # 记录 cache_read 给 deepseek 定价用
            self._last_cache_read = usage.get("cache_read_input_tokens", 0)
            self._last_usage = usage
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
        payload = self._call({
            "model": self.model,
            "max_tokens": 200,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": prompt}],
        })
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
        payload = self._call({
            "model": self.model,
            "max_tokens": 200,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": prompt}],
        })
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

        payload = self._call({
            "model": self.model,
            "max_tokens": 16000,  # m3 thinking 4096 + JSON 8000, 必须留足, 否则 stop_reason=max_tokens
            "temperature": 0.4,
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": "emit_major_json"},
            "messages": [{"role": "user", "content": prompt}],
        }, expect_tool=True)

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
        # debug: dump 完整 content 便于排查
        content_types = [b.get("type") for b in payload.get("content", [])]
        raise RetryableError(
            f"synthesize_json 未返回 tool_use 块且 text 也无 JSON "
            f"(content types: {content_types}, stop_reason: {payload.get('stop_reason')})"
        )

    # ── 内部 ──
    def _extract_text(self, payload: dict) -> str:
        """只取 text 块, 跳过 thinking 块 (m3 会返回 thinking + text)."""
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


# ─────────────────────────────────────────────────────────────
# Provider 实现
# ─────────────────────────────────────────────────────────────
class M3Client(_AnthropicCompatClient):
    """MiniMax-M3 (token plan, https://api.minimaxi.com/anthropic).

    用官方 anthropic SDK (raw HTTP 跑 m3 有 bug: tool_use 时 content=null, 漏数据).
    DeepSeek 仍走 raw HTTP (SDK 0.97+ 在 DeepSeek 端会注入 Claude auth, 401).
    """
    provider_name = "m3"
    default_model = M3_DEFAULT_MODEL
    base_url = M3_BASE
    api_key_env = "M3_API_KEY"

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 enable_thinking: bool = True):
        # m3 必须开 thinking 才能输出 rich content (关闭后字段大量空, 质量崩)
        super().__init__(api_key=api_key, model=model, enable_thinking=enable_thinking)
        # 延迟 import SDK, 避免 DeepSeek-only 环境装不上 anthropic
        try:
            import anthropic
        except ImportError as e:
            raise PermanentError(
                "M3Client 需要 anthropic SDK: pip install anthropic>=0.40"
            ) from e
        self._sdk = anthropic.Anthropic(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    def _call(self, body: dict, expect_tool: bool = False) -> dict:
        """走 anthropic SDK, 把 response 适配成 raw HTTP 的 dict 格式 (兼容 synthesize_json 抽 tool_use)."""
        # body → SDK 参数
        kwargs = {
            "model": body.get("model", self.model),
            "max_tokens": body.get("max_tokens", 16000),
            "messages": body.get("messages", []),
        }
        if "temperature" in body:
            kwargs["temperature"] = body["temperature"]
        if "system" in body:
            kwargs["system"] = body["system"]
        if "tools" in body:
            kwargs["tools"] = body["tools"]
        if "tool_choice" in body:
            kwargs["tool_choice"] = body["tool_choice"]
        # thinking 显式传 (默认 enabled, 显式传更稳)
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": 4096}

        try:
            msg = self._sdk.messages.create(**kwargs)
        except Exception as e:
            err = str(e)
            if "401" in err or "403" in err or "authentication" in err.lower():
                raise PermanentError(f"m3 auth 失败: {err[:200]}") from e
            raise RetryableError(f"m3 调用失败: {err[:200]}") from e

        # SDK Message → dict (含 content list + usage + stop_reason)
        content_list = []
        for block in msg.content:
            bd = block.model_dump() if hasattr(block, "model_dump") else dict(block)
            content_list.append(bd)

        payload = {
            "id": getattr(msg, "id", ""),
            "type": "message",
            "role": "assistant",
            "model": getattr(msg, "model", self.model),
            "content": content_list,
            "stop_reason": str(getattr(msg, "stop_reason", "end_turn")),
            "usage": {
                "input_tokens": msg.usage.input_tokens,
                "output_tokens": msg.usage.output_tokens,
                "cache_read_input_tokens": getattr(msg.usage, "cache_read_input_tokens", 0) or 0,
            },
        }

        # token 累计
        self.total_input_tokens += payload["usage"]["input_tokens"]
        self.total_output_tokens += payload["usage"]["output_tokens"]
        return payload

    def cost_estimate_cny(self) -> float:
        """MiniMax-M3 token plan 定价: 暂按 ¥0.05/千 input + ¥0.20/千 output 估算
        (实际账单以官方为准, 这里仅供监控体量)."""
        return (self.total_input_tokens * 0.05 + self.total_output_tokens * 0.20) / 1000

    def synthesize_json(self, *args, **kwargs) -> dict:
        """Override: 拿 m3 输出后, 调 _normalize 转成 curated schema (curriculum 拆 item 包装, employment_direction 改 key 名)."""
        raw = super().synthesize_json(*args, **kwargs)
        return _normalize_m3_to_curated(raw)


class DeepSeekClient(_AnthropicCompatClient):
    """DeepSeek-V4-Flash (https://api.deepseek.com/anthropic).

    注意: V4 Flash 默认 thinking on, 但 thinking mode 不支持 tool_choice,
    会返回 400. synthesize_json 必须显式禁 thinking.
    """
    provider_name = "deepseek"
    default_model = DEEPSEEK_DEFAULT_MODEL
    base_url = DEEPSEEK_BASE
    api_key_env = "DEEPSEEK_API_KEY"

    def synthesize_json(self, *args, **kwargs) -> dict:
        """Override: deepseek 走 raw HTTP 不带 thinking + 自动 normalize 到 curated schema."""
        raw = _AnthropicCompatClient.synthesize_json(self, *args, **kwargs)
        return _normalize_deepseek_to_curated(raw)

    def _call(self, body: dict, expect_tool: bool = False) -> dict:
        # V4 Flash + tool_choice 不兼容 thinking, 必须显式禁
        if expect_tool:
            body.setdefault("thinking", {"type": "disabled"})
        return super()._call(body, expect_tool=expect_tool)

    def cost_estimate_cny(self) -> float:
        """DeepSeek V4 Flash 定价: 缓存命中 ¥0.02/M, 未命中 ¥1/M input, 输出 ~¥2/M."""
        usage = getattr(self, "_last_usage", None)
        if usage is None:
            return 0.0
        cache_read = getattr(self, "_last_cache_read", 0)
        in_t = self.total_input_tokens - cache_read
        return (cache_read * 0.02 + in_t * 1.0 + self.total_output_tokens * 2.0) / 1_000_000


# ─────────────────────────────────────────────────────────────
# 工厂
# ─────────────────────────────────────────────────────────────
def get_client(enable_thinking: bool = False):
    """按 LLM_PROVIDER env 选 client (默认 m3)."""
    provider = os.environ.get("LLM_PROVIDER", "m3").strip().lower()
    if provider == "m3":
        return M3Client(enable_thinking=enable_thinking)
    elif provider == "deepseek":
        return DeepSeekClient()
    else:
        raise PermanentError(f"未知 LLM_PROVIDER: {provider!r} (可选: m3 / deepseek)")


# ─────────────────────────────────────────────────────────────
# m3 → curated schema 转换器 (Post-process 兼容层)
# ─────────────────────────────────────────────────────────────
def _normalize_m3_to_curated(data: dict) -> dict:
    """m3 输出 schema 略不同于 curated (animation.json 等), 渲染前需归一化.

    已知 m3 quirks:
      - curriculum: {category: {"item": [...]}} → {category: [...]}
      - deep_study: {key: {"item": [...]}} → {key: [...]} (深造内容也同款)
      - salary 各阶段 yoy 字符串转 int (m3 经常把数字返成字符串)
      - salary 顺序乱 (m3 不按 career stage 排) → 按 应届→3年→5年→10年+ 排
      - employment_direction: [{name, dest, share, note}] → [{name, dest, desc, pct}]
      - alumni_quotes 缺 current (只有 name) → 用 name/school 填 current
      - xuanke_req_list: [{subject, level, note}] → [{name=subject, pct=level→int, note}]
    """
    if not isinstance(data, dict):
        return data

    # ── curriculum 拆 item 包装 ──
    curr = data.get("curriculum")
    if isinstance(curr, dict):
        for cat, val in list(curr.items()):
            if isinstance(val, dict) and "item" in val and isinstance(val["item"], list):
                curr[cat] = val["item"]

    # ── deep_study 拆 item 包装, KEEP 原始 list/dict 内容 (不压缩!) ──
    ds = data.get("deep_study")
    if isinstance(ds, dict):
        for k, val in list(ds.items()):
            # 拆 item 包装 (m3 风格)
            if isinstance(val, dict) and "item" in val and isinstance(val["item"], list):
                ds[k] = val["item"]
            # 嵌套 sub-dict 也拆 (如 certification 内部)
            elif isinstance(val, dict):
                for sub_k, sub_v in list(val.items()):
                    if isinstance(sub_v, dict) and "item" in sub_v and isinstance(sub_v["item"], list):
                        val[sub_k] = sub_v["item"]
            # m3 返 dict {name, difficulty, why} → 包装成 list[str] (description + detail)
            if isinstance(ds.get(k), dict):
                d = ds[k]
                bullets = []
                if d.get("name"):
                    bullets.append(d["name"])
                if d.get("difficulty"):
                    bullets.append(f"难度: {d['difficulty']}")
                if d.get("why"):
                    bullets.append(f"为什么重要: {d['why']}")
                ds[k] = bullets if bullets else ["推荐"]

    # ── overview_v2: m3 返 {what_you_learn, who_fits, pitfalls} (字符串), 转成 curated 嵌套结构 ──
    ov = data.get("overview_v2")
    if isinstance(ov, dict):
        # what_you_learn (str) → 拆成段 (按 。 或 \n 切)
        wyl = ov.get("what_you_learn")
        if isinstance(wyl, str) and wyl.strip():
            # 按句号切
            segs = re.split(r"[。\n]+", wyl)
            segs = [s.strip() for s in segs if s.strip() and len(s.strip()) > 5]
            ov.setdefault("what", {})
            if "foundations" not in ov["what"]:
                ov["what"]["foundations"] = segs[:3] if segs else [wyl[:200]]
            if "directions" not in ov["what"]:
                ov["what"]["directions"] = segs[3:6] if len(segs) > 3 else segs
        # who_fits (str) → 拆成段
        wf = ov.get("who_fits")
        if isinstance(wf, str) and wf.strip():
            segs = re.split(r"[。\n]+", wf)
            segs = [s.strip() for s in segs if s.strip() and len(s.strip()) > 5]
            ov.setdefault("fit", {})
            if not ov["fit"].get("yes"):
                ov["fit"]["yes"] = segs[:3] if segs else [wf[:200]]
        # pitfalls (str) → 按 ❌ 或 "误区 N" 切, 转成 list[{myth, reality}]
        pf = ov.get("pitfalls")
        if isinstance(pf, str) and pf.strip():
            # 尝试按 ❌ 切
            if "❌" in pf:
                parts = re.split(r"❌", pf)
                new_pf = []
                for p in parts:
                    p = p.strip()
                    if not p:
                        continue
                    # 找 "→" 或 "正确" 之类分隔符
                    if "→" in p:
                        myth, reality = p.split("→", 1)
                        new_pf.append({"myth": myth.strip(), "reality": reality.strip()})
                    else:
                        new_pf.append({"myth": p[:50], "reality": p})
                if new_pf:
                    ov["pitfalls"] = new_pf
            elif "误区" in pf:
                # 按 "误区N" 切
                parts = re.split(r"误区\s*\d*[：:]?", pf)
                new_pf = []
                for p in parts:
                    p = p.strip()
                    if p:
                        new_pf.append({"myth": p[:50], "reality": p})
                if new_pf:
                    ov["pitfalls"] = new_pf

    # ── salary 排序 + yoy 转 int ──
    salary = data.get("salary")
    if isinstance(salary, dict):
        # yoy str → int
        for stage, vals in list(salary.items()):
            if isinstance(vals, dict) and isinstance(vals.get("yoy"), str):
                try:
                    vals["yoy"] = int(vals["yoy"])
                except (ValueError, TypeError):
                    vals["yoy"] = 0
        # 排序: 应届(0) → 3年(3) → 5年(5) → 10年+/持证(8-10) → 其他(99)
        def _stage_sort_key(stage_name: str) -> int:
            s = stage_name.lower()
            if "应届" in s or "junior" in s or "0" in s and "年" in s:
                return 0
            # 抽第一个数字
            m = re.search(r"(\d+)", stage_name)
            if m:
                n = int(m.group(1))
                return n
            if "持证" in s or "资深" in s or "高级" in s:
                return 8
            return 99
        sorted_salary = dict(sorted(salary.items(), key=lambda kv: _stage_sort_key(kv[0])))
        data["salary"] = sorted_salary

    # ── employment_direction key 改名 + 类型转换 ──
    eds = data.get("employment_direction")
    if isinstance(eds, list):
        new_eds = []
        for ed in eds:
            if not isinstance(ed, dict):
                continue
            new_ed = dict(ed)
            # share (如 "40%") → pct (int 40)
            if "share" in new_ed and "pct" not in new_ed:
                share = new_ed.pop("share")
                if isinstance(share, str):
                    try:
                        new_ed["pct"] = int(share.rstrip("%").strip())
                    except (ValueError, TypeError):
                        new_ed["pct"] = -1
                elif isinstance(share, (int, float)):
                    new_ed["pct"] = int(share)
            # note → desc
            if "note" in new_ed and "desc" not in new_ed:
                new_ed["desc"] = new_ed.pop("note")
            new_eds.append(new_ed)
        data["employment_direction"] = new_eds

    # ── alumni_quotes 缺 current → 用 name + school 拼 ──
    aq = data.get("alumni_quotes")
    if isinstance(aq, list):
        for q in aq:
            if isinstance(q, dict) and not q.get("current"):
                name = q.get("name", "")
                school = q.get("school", "")
                q["current"] = f"{name} @ {school}" if school else name
            if isinstance(q, dict) and not q.get("year"):
                # 从 school 里抽 "2019 届" / "2022 届" 这种
                school = q.get("school", "")
                m = re.search(r"(\d{4})\s*届", school)
                if m:
                    q["year"] = m.group(1) + " 届"

    # ── xuanke_req_list: m3 用 {subject, level, note}, render 要 {name, pct} ──
    xr = data.get("xuanke_req_list")
    if isinstance(xr, list):
        for x in xr:
            if not isinstance(x, dict):
                continue
            # subject → name
            if "subject" in x and "name" not in x:
                x["name"] = x["subject"]
            # level → pct: "多数校要求" → 80, "多数不限制" → 50, "极少数" → 10, 否则取数字
            if "level" in x and "pct" not in x:
                level = x["level"]
                if isinstance(level, str):
                    if "多数" in level or "大部分" in level:
                        x["pct"] = 80
                    elif "少数" in level or "部分" in level:
                        x["pct"] = 40
                    elif "极少" in level or "个别" in level:
                        x["pct"] = 10
                    else:
                        # 尝试从字符串抽数字
                        m = re.search(r"(\d+)", level)
                        x["pct"] = int(m.group(1)) if m else 50
                elif isinstance(level, (int, float)):
                    x["pct"] = int(level)

    return data


# ─────────────────────────────────────────────────────────────
# DeepSeek → curated schema 转换器 (Post-process 兼容层)
# ─────────────────────────────────────────────────────────────
def _normalize_deepseek_to_curated(data: dict) -> dict:
    """DeepSeek V4 Flash 输出 schema 跟 m3 / curated 都不同, 渲染前需归一化.

    已知 DeepSeek quirks (从 D 组 10 篇实战中发现):
      - salary: {note, stages:[{stage, salary_range, description}]} → {stage_name: {p25,p50,p75,yoy}}
        salary_range "8-15 万/年" → p25=8, p50=12, p75=15 (中位数取平均)
      - deep_study: 自由 key (intro/undergrad_plan/cert_plan/core_skills/certificates/...)
        → {books, certification, internships, skills}
      - deep_study.certificates: [{name, why, difficulty}] → list[str] "name (难度: X)"
      - deep_study.recommended_books: [{title, author, desc}] → list[str] "《title》— desc"
      - alumni_quotes: 偶尔含 {name, background, insight} 而非 {quote}, 改名
      - xuanke_req_list: 偶尔返 [{subject, ratio, requirement_note}], 改名
      - overview_v2.pitfalls: m3 兼容层已处理, 这里补一下直接 list[dict] 但缺字段
    """
    if not isinstance(data, dict):
        return data

    # ── salary: {note, stages:[...]} → {stage: {p25,p50,p75,yoy}} ──
    salary = data.get("salary")
    if isinstance(salary, dict) and "stages" in salary and isinstance(salary["stages"], list):
        new_salary = {}
        for s in salary["stages"]:
            if not isinstance(s, dict):
                continue
            stage = str(s.get("stage", s.get("name", "未命名"))).strip()
            # 抽数字 from "8-15 万/年" → (8, 15)
            rng = str(s.get("salary_range", ""))
            nums = re.findall(r"(\d+(?:\.\d+)?)", rng)
            p25, p50, p75 = 0, 0, 0
            if len(nums) >= 2:
                p25 = int(float(nums[0]))
                p75 = int(float(nums[1]))
                p50 = (p25 + p75) // 2
            elif len(nums) == 1:
                p50 = p25 = p75 = int(float(nums[0]))
            new_salary[stage] = {
                "p25": p25,
                "p50": p50,
                "p75": p75,
                "yoy": 5,  # 默认值, deepseek 不返 yoy
                "desc": str(s.get("description", ""))[:200],
            }
        if new_salary:
            data["salary"] = new_salary

    # ── deep_study: 自由 key → curated 标准 (关键: 合并为长字符串, 不要每段拆 1 项) ──
    ds = data.get("deep_study")
    if isinstance(ds, dict):
        new_ds = {"books": [], "certification": [], "internships": [], "skills": []}
        for k, v in ds.items():
            k_lower = k.lower()
            # 分类
            if any(x in k_lower for x in ("cert", "资格证", "证书", "certificate")):
                target = "certification"
            elif any(x in k_lower for x in ("intern", "实习", "实习规划")):
                target = "internships"
            elif any(x in k_lower for x in ("skill", "技能", "能力", "core_skills")):
                target = "skills"
            elif any(x in k_lower for x in ("book", "书", "阅读", "undergrad", "grad_plan", "study", "规划", "intro", "background", "overview")):
                target = "books"
            else:
                # 杂项 → 塞 books (与读书规划相关)
                target = "books"

            # 关键: 把同 key 的多段内容拼成 1 段长字符串, 不要拆成 list
            parts = []
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict):
                        # 优先取 name/desc/text/title 拼成单行
                        sub = []
                        if item.get("name"): sub.append(str(item["name"]))
                        if item.get("title"): sub.append(f"《{item['title']}》")
                        if item.get("author"): sub.append(f"— {item['author']}")
                        if item.get("difficulty"): sub.append(f"难度: {item['difficulty']}")
                        if item.get("why"): sub.append(f"为什么: {item['why']}")
                        if item.get("value"): sub.append(str(item["value"]))
                        if item.get("level"): sub.append(f"({item['level']})")
                        if item.get("cost"): sub.append(f"费用: {item['cost']}")
                        if item.get("description"): sub.append(str(item["description"]))
                        if item.get("desc"): sub.append(str(item["desc"]))
                        if item.get("text"): sub.append(str(item["text"]))
                        if sub:
                            parts.append(" ".join(sub))
            elif isinstance(v, dict):
                sub = []
                if v.get("name"): sub.append(str(v["name"]))
                if v.get("description"): sub.append(str(v["description"]))
                if v.get("desc"): sub.append(str(v["desc"]))
                if v.get("text"): sub.append(str(v["text"]))
                if sub:
                    parts.append(" ".join(sub))

            if parts:
                # 合并为 1 段长字符串 (curated 格式), 限 500 字
                combined = " / ".join(p for p in parts if p)[:500]
                new_ds[target].append(combined)

        # 合并 books 里多个 item 为单条 (1-2 段长)
        for k in new_ds:
            if len(new_ds[k]) > 2:
                # 超过 2 项就合并前 N 项
                new_ds[k] = [" / ".join(new_ds[k])[:800]]

        # 过滤空 list
        data["deep_study"] = {k: v for k, v in new_ds.items() if v}

    # ── alumni_quotes: {background, insight} 改 {quote} ──
    aq = data.get("alumni_quotes")
    if isinstance(aq, list):
        for q in aq:
            if isinstance(q, dict) and not q.get("quote"):
                if q.get("insight"):
                    q["quote"] = str(q.pop("insight"))[:300]
                elif q.get("background"):
                    q["quote"] = str(q.pop("background"))[:300]

    # ── xuanke_req_list: 多种格式 → {name, pct, note} ──
    # DeepSeek 实战中常用 3 种格式:
    #   A. {subject, ratio, requirement_note}      ← 字段版
    #   B. {province, req, note}                  ← 按省份版 (D 组实战发现!)
    #   C. {name, pct, note}                       ← 标准版
    xr = data.get("xuanke_req_list")
    if isinstance(xr, list):
        new_xr = []
        for x in xr:
            if not isinstance(x, dict):
                continue
            nx = dict(x)

            # 省份版 → 抽 req 关键词
            if "province" in x and "req" in x and "name" not in nx:
                # 从 req 抽 "物理"/"历史"/"化学"/"生物" 等关键词
                req_str = str(x.get("req", ""))
                # 优先级: 物理/历史/化学/生物/不限/政治/地理
                found_subj = None
                for subj in ["物理", "历史", "化学", "生物", "政治", "地理", "不限"]:
                    if subj in req_str:
                        found_subj = subj
                        break
                # 抽 "X+Y" 组合
                if not found_subj:
                    m = re.search(r"([物理历史化学生物政治地理不限])[+/]([物理历史化学生物政治地理不限])", req_str)
                    if m:
                        found_subj = f"{m.group(1)}+{m.group(2)}"
                if not found_subj:
                    found_subj = "其他"

                # 派生 pct: 关键词 "必选" → 100, "均可" → 80, "建议" → 60, 默认 50
                pct = 50
                if "必选" in req_str or "要求" in req_str and "必" in req_str:
                    pct = 100
                elif "均可" in req_str or "不限" in req_str or "文理兼收" in req_str:
                    pct = 80
                elif "建议" in req_str:
                    pct = 60

                nx["name"] = found_subj
                nx["pct"] = pct
                if "note" not in nx and "note" in x:
                    nx["note"] = x["note"]
                # province 留作参考
                nx["province"] = x["province"]
                nx["req_text"] = req_str

            # 课程版 (law 实测) → {course, reason} 抽 course 作 name, reason 作 note
            elif "course" in x and "name" not in nx:
                nx["name"] = str(x["course"])
                if "reason" in x and "note" not in nx:
                    nx["note"] = str(x["reason"])
                # 默认 80 (因为"门槛"暗示普遍要求)
                if "pct" not in nx:
                    reason_str = str(x.get("reason", ""))
                    if "门槛" in reason_str or "必" in reason_str or "强" in reason_str:
                        nx["pct"] = 90
                    elif "建议" in reason_str:
                        nx["pct"] = 60
                    else:
                        nx["pct"] = 80

            # 字段版 → 改名
            if "subject" in x and "name" not in nx:
                nx["name"] = x["subject"]
            if "ratio" in x and "pct" not in nx:
                ratio = x["ratio"]
                if isinstance(ratio, str):
                    m = re.search(r"(\d+)", ratio)
                    nx["pct"] = int(m.group(1)) if m else 50
                elif isinstance(ratio, (int, float)):
                    nx["pct"] = int(ratio)
            if "requirement_note" in x and "note" not in nx:
                nx["note"] = x.pop("requirement_note")

            # 兜底: 缺 name / pct
            if "name" not in nx:
                nx["name"] = str(x.get("subject", x.get("province", "其他")))
            if "pct" not in nx:
                nx["pct"] = 0

            new_xr.append(nx)
        data["xuanke_req_list"] = new_xr

    # ── overview_v2: 强制 {what:{foundations,directions,skills}, fit:{yes,no}, pitfalls:[{myth,reality}]} ──
    ov = data.get("overview_v2")
    if isinstance(ov, dict):
        # what 归一
        what = ov.get("what", {})
        if not isinstance(what, dict):
            what = {}
        new_what = {
            "foundations": what.get("foundations") or what.get("learn") or what.get("intro") or [],
            "directions": what.get("directions") or what.get("branches") or what.get("subfields") or [],
            "skills": what.get("skills") or what.get("abilities") or what.get("competencies") or [],
        }
        # title 字段丢掉
        what.pop("title", None)
        ov["what"] = new_what

        # fit 归一
        fit = ov.get("fit", {})
        if not isinstance(fit, dict):
            fit = {}
        ov["fit"] = {
            "yes": fit.get("yes") or [],
            "no": fit.get("no") or [],
        }

        # pitfalls 归一
        pf = ov.get("pitfalls", [])
        if not isinstance(pf, list):
            pf = []
        new_pf = []
        for p in pf:
            if isinstance(p, dict) and p.get("myth") and p.get("reality"):
                new_pf.append({"myth": p["myth"], "reality": p["reality"]})
        ov["pitfalls"] = new_pf

    # ── salary: 强制 4 阶段 (应届 / 3年 / 5年 / 10年+), 单位归一万/年 ──
    salary = data.get("salary")
    if isinstance(salary, dict) and salary:
        new_salary = {}

        # 严格检测 元/月: 必须有 note 明确说"元/月"/"规培"/"月薪", 数字 < 1000 不能作为唯一依据
        sample_vals = [v for v in salary.values() if isinstance(v, dict)]
        is_monthly = False
        if sample_vals:
            sample_note = " ".join(str(v.get("note", "")) for v in sample_vals)
            sample_p50s = [v.get("p50", 0) for v in sample_vals if isinstance(v.get("p50"), (int, float)) and v.get("p50") > 0]
            is_monthly = (
                "元/月" in sample_note or
                "月薪" in sample_note or
                "规培" in sample_note
            ) and not any(s > 1000 for s in sample_p50s)  # 元/月 AND 没有任何 > 1000 的值

        def classify_stage(s: str) -> str:
            s_lower = s.lower()
            if "应届" in s or "junior" in s_lower or "0-" in s or s.strip().startswith("0年") or "规培" in s:
                return "应届生 (一线)"
            if "10" in s or "15" in s or "20" in s or "资深" in s or "高级" in s or "senior" in s_lower or "持证" in s or "合伙人" in s or "主任" in s or "副主" in s or "正高" in s:
                return "10年+ (持证/资深)"
            m = re.search(r"(\d+)\s*年", s)
            if m:
                years = int(m.group(1))
                if years >= 8:
                    return "10年+ (持证/资深)"
                if years >= 4:
                    return "5年经验"
                if years >= 2:
                    return "3年经验"
            return s

        for stage, vals in salary.items():
            if not isinstance(vals, dict):
                continue
            mapped = classify_stage(str(stage))
            if is_monthly:
                vals = dict(vals)
                for k in ("p25", "p50", "p75"):
                    if k in vals and isinstance(vals[k], (int, float)) and vals[k] > 0:
                        vals[k] = round(vals[k] * 12 / 10000, 1)
            new_salary[mapped] = vals

        # 合并同名 (取较大值)
        merged = {}
        for stage, vals in new_salary.items():
            if stage in merged:
                for k in ("p25", "p50", "p75"):
                    if k in vals and vals[k] > 0:
                        merged[stage][k] = max(merged[stage].get(k, 0), vals.get(k, 0))
            else:
                merged[stage] = dict(vals)

        canonical_order = ["应届生 (一线)", "3年经验", "5年经验", "10年+ (持证/资深)"]
        ordered = {k: merged[k] for k in canonical_order if k in merged}
        for k, v in merged.items():
            if k not in ordered:
                ordered[k] = v
        data["salary"] = ordered

    return data


# ── 便捷 CLI 调试 ──
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python llm.py <major_name>")
        print(f"当前 LLM_PROVIDER: {os.environ.get('LLM_PROVIDER', 'm3')}")
        sys.exit(1)
    name = sys.argv[1]
    c = get_client()
    is_major, normalized = c.validate_is_major(name)
    print(f"validate_is_major: ({is_major}, {normalized!r})")
    if is_major:
        style = c.route_style(normalized)
        print(f"route_style: {style}")
    print(f"\n成本估算: {c.cost_estimate_cny():.4f} 元 "
          f"(input {c.total_input_tokens}, output {c.total_output_tokens})")
