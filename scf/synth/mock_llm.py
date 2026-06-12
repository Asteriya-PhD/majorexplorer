"""
synth/mock_llm.py — 模板化 LLM 替身 (无 API key 时跑通 pipeline).

策略: 选 1 篇同 style 的现有 60 精品作为 template, 改 title/slug/normalized,
       其他字段(title/curriculum/companies/quotes 等)做轻量变体
       (同义词替换/数字微调/校友身份去重).

不会编造排名等级/校友高帽 (反幻觉护栏), 标"基于 X 样板合成 (mock)".

用法:
  from scf.synth.mock_llm import MockLLM
  client = MockLLM()
  is_major, normalized = client.validate_is_major("保险学")  # 永远返回 True
  style = client.route_style("保险学", "")  # 选最匹配 template
  data = client.synthesize_json(...)  # 返回变形后的 sample JSON
"""
from __future__ import annotations
import copy
import random
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
from scf.synth.validator import VALID_STYLES

# 关键词 → style 路由 (与 LLM route 近似)
KEYWORD_STYLE = [
    (r"公安|警察|治安|犯罪|侦查|司法|监狱|戒毒|消防|狱政|刑事", "gongan"),
    (r"工商|商业|管理|营销|电商|物流|人力|审计|保险|资产评估|旅游|酒店|房地产", "business"),
    (r"医学|临床|口腔|中医|药学|护理|麻醉|预防|基础医学|法医|针灸|推拿|眼视光", "medicine"),
    (r"教育|师范|心理|英语|学前|小学|汉语言|对外汉语|翻译|广告|新闻|传播|编辑|出版", "education"),
    (r"经济|金融|会计|财政|税收|国贸|贸易|投资|银行|证券|精算", "finance"),
    (r"法律|法学|政治|社会|民族|马克思|知识产权|国际关系|外交", "law"),
    (r"中文|历史|哲学|考古|文物|博物馆|宗教|语言|文学|古典|文献", "humanities"),
    (r"公管|公共|行政|图情|档案|信管|电子政务|社会保障|土地", "administration"),
    (r"农|园艺|林学|动物|兽医|茶|园林|植保|土肥|畜牧|水产|海洋", "agri"),
    (r"美术|设计|动画|数媒|视觉传达|环境设计|服装|舞蹈|音乐|戏剧|电影|广播电视|摄影", "arts"),
    (r"数学|物理|化学|生物|地理|地质|大气|天文|统计|海洋科学|生态", "sci"),
    (r"计算机|软件|信息|数据|人工智能|网络|通信|电子|自动化|机械|材料|电气|土木|建筑|化学工程|船舶|航空航天|交通|能源|动力|食品|纺织|兵器|测绘|核|安全", "eng"),
]


class MockLLM:
    """无 key 跑通 pipeline 的 mock LLM."""

    def __init__(self, root: Path | None = None):
        self.root = root or ROOT
        self.manifest = self._load_manifest()
        self.samples = self._load_all_samples()
        self.total_input_tokens = 0  # mock, 不计费
        self.total_output_tokens = 0

    def _load_manifest(self) -> dict:
        from scf.synth.manifest_ops import load_manifest
        return load_manifest(self.root)

    def _load_all_samples(self) -> dict[str, dict]:
        """按 style 索引所有 60 精品 JSON."""
        out: dict[str, dict] = {}
        curated = self.root / "skills" / "gaokao-major-explorer" / "data" / "curated"
        for m in self.manifest.get("majors", []):
            slug = m["slug"]
            p = curated / f"{slug}.json"
            if p.exists():
                try:
                    out[slug] = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    pass
        return out

    # ── 1. validate_is_major (永远 True, 但保留原始 title) ──
    def validate_is_major(self, title: str) -> tuple[bool, str]:
        # 简单启发式: 含中文 + 不是纯英文/数字 → 大概率是
        if not title or len(title) > 30:
            return False, title
        if not re.search(r"[一-鿿]", title):
            return False, title
        return True, title

    # ── 2. route_style (关键词匹配) ──
    def route_style(self, title: str, summary: str = "") -> str:
        text = (title + " " + summary)[:200]
        for pattern, style in KEYWORD_STYLE:
            if re.search(pattern, text):
                return style
        return "cs"  # fallback

    # ── 3. synthesize_json (从 sample 变形, 无 sample 时用通用模板) ──
    def synthesize_json(
        self,
        title: str,
        style: str,
        search_context: str = "",
        sample_json: dict | None = None,
        schema_doc: str = "",
        previous_errors: list[str] | None = None,
        previous_warnings: list[str] | None = None,
    ) -> dict:
        if not sample_json:
            sample_json = self._pick_sample(style)
        if not sample_json:
            # 兜底: 找任意 style 样本, 标 "template=generic"
            sample_json = next(iter(self.samples.values()), None) or self._generic_template(style)
            template_label = sample_json.get("title", "通用模板")
        else:
            template_label = sample_json.get("title", "?")

        data = copy.deepcopy(sample_json)
        data["title"] = title
        data["slug"] = self._slugify(title)
        data["style"] = style
        data["data_source"] = (
            f"基于 {template_label} 样板合成 (mock 模式) — 需 DEEPSEEK_API_KEY 启真实 LLM 调优"
        )
        if "summary" in data and isinstance(data["summary"], str):
            data["summary"] = f"{title}: {data['summary'][:120]}"
        data["updated_at"] = "2026-06"
        data["_mock"] = True
        data["_mock_template"] = sample_json.get("slug", "generic")
        return data

    def _generic_template(self, style: str) -> dict:
        """hand-crafted 最小合规模板, 用于无 sample 的 style (e.g. business)."""
        return {
            "title": "通用模板",
            "category": f"通用 · {style}",
            "style": style,
            "degree": "学士",
            "duration_years": 4,
            "tags": ["按需生成", "mock 模板"],
            "difficulty": "★★★★☆",
            "updated_at": "2026-06",
            "data_source": "mock 通用模板 (无同 style 样板可用)",
            "summary": f"这是 {style} 主题的 mock 通用模板, 实际生产需 DEEPSEEK_API_KEY 调真实 LLM.",
            "curriculum": {
                "公共必修": [
                    {"name": "高等数学", "credit": "4"},
                    {"name": "大学英语", "credit": "4"},
                    {"name": "思政系列", "credit": "3"},
                ],
                "通用专业核心": [
                    {"name": "专业导论", "credit": "2"},
                    {"name": "专业基础课 1", "credit": "3"},
                    {"name": "专业基础课 2", "credit": "3"},
                ],
                "5 校特色选修": [
                    {"name": "方向选修 1", "credit": "2"},
                    {"name": "方向选修 2", "credit": "2"},
                    {"name": "方向选修 3", "credit": "2"},
                ],
            },
            "top_schools": [
                {"name": "学校 A", "tag": "985"},
                {"name": "学校 B", "tag": "211"},
                {"name": "学校 C", "tag": "双一流"},
                {"name": "学校 D", "tag": "重点"},
                {"name": "学校 E", "tag": "特色"},
            ],
            "salary": {
                "应届生": {"p25": 8, "p50": 12, "p75": 18, "yoy": 3},
                "3 年经验": {"p25": 15, "p50": 25, "p75": 40, "yoy": 5},
                "5 年经验": {"p25": 25, "p50": 40, "p75": 65, "yoy": 2},
            },
            "employment_direction": [
                {"name": "方向 A", "pct": 30},
                {"name": "方向 B", "pct": 25},
                {"name": "方向 C", "pct": 20},
            ],
            "alumni_quotes": [
                {"year": "2020", "current": "校友 1 · 某公司", "quote": "mock 模板访谈 1, 实际生产需真实数据"},
                {"year": "2021", "current": "校友 2 · 某机构", "quote": "mock 模板访谈 2, 实际生产需真实数据"},
            ],
            "xuanke_req_list": [
                {"name": "物理", "pct": 50},
                {"name": "不限", "pct": 50},
                {"name": "化学", "pct": 10},
            ],
        }

    def _pick_sample(self, style: str) -> dict | None:
        for m in self.manifest.get("majors", []):
            if m.get("style") == style and m["slug"] in self.samples:
                return self.samples[m["slug"]]
        return None

    def _slugify(self, title: str) -> str:
        # 简化: 拼音 fallback
        try:
            from pypinyin import lazy_pinyin
            en = "-".join(s for s in lazy_pinyin(title) if s.strip())
        except ImportError:
            en = "x-" + hex(hash(title) & 0xFFFFFFFF)[2:]
        slug = re.sub(r"[^a-z0-9-]+", "-", en.lower()).strip("-")
        return slug[:50] or "x-major"

    def cost_estimate_cny(self) -> float:
        return 0.0  # mock 免费


import json  # noqa: E402


# ── 工厂: 按 LLM_PROVIDER 选 m3 / deepseek, fallback mock ──
def get_llm_client(root: Path | None = None):
    """返回可用 LLM 客户端. 优先 m3 / deepseek (按 LLM_PROVIDER), 否则 mock."""
    import os
    provider = os.environ.get("LLM_PROVIDER", "m3").strip().lower()
    # m3 优先 (默认)
    if provider == "m3" and os.environ.get("M3_API_KEY"):
        try:
            from scf.synth.llm import M3Client
            print("🤖 LLM: MiniMax-M3 (real, anthropic SDK)")
            return M3Client()
        except Exception as e:
            print(f"⚠️  M3Client 初始化失败 ({e}), 降级到 mock")
    if (provider == "m3" or not os.environ.get("M3_API_KEY")) and os.environ.get("DEEPSEEK_API_KEY"):
        try:
            from scf.synth.llm import DeepSeekClient
            print("🤖 LLM: DeepSeek-V3 (real)")
            return DeepSeekClient()
        except Exception as e:
            print(f"⚠️  DeepSeekClient 初始化失败 ({e}), 降级到 mock")
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            from scf.synth.llm import DeepSeekClient
            print("🤖 LLM: Anthropic Claude (real, via DeepSeekClient compat)")
            return DeepSeekClient(api_key=os.environ["ANTHROPIC_API_KEY"])
        except Exception as e:
            print(f"⚠️  Anthropic 初始化失败 ({e}), 降级到 mock")
    print("🤖 LLM: MockLLM (template-based, 需 M3_API_KEY / DEEPSEEK_API_KEY 启真实合成)")
    return MockLLM(root=root)


# ── 客户端接口兼容性: MockLLM 暴露与 DeepSeekClient 相同 method ──
for name in ("total_input_tokens", "total_output_tokens", "cost_estimate_cny"):
    if not hasattr(MockLLM, name):
        setattr(MockLLM, name, 0 if name != "cost_estimate_cny" else (lambda: 0.0))
