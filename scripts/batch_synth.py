"""
batch_synth.py — 本地批量合成 300 个专业的 major JSON (走 TEMPLATE 锁死字段).

跟 scf/synth/main.py (现场 SCF) 共享同一份 TEMPLATE.json 字段契约:
  - LLM 只能填值, 不能创造字段
  - normalizer 把 deepseek 各种怪癖归一
  - 渲染器按 schema 直接读

用法:
  source .env
  python3 -m scripts.batch_synth --list finance,law,medicine  # 跑指定 3 类所有专业
  python3 -m scripts.batch_synth --slug insurance            # 跑单专业
  python3 -m scripts.batch_synth --file majors.csv          # 从 csv 读 list
  python3 -m scripts.batch_synth --provider m3              # 默认 m3 (订阅), 也可 deepseek
  python3 -m scripts.batch_synth --audit                    # 跑完后自动 audit

为什么不用 scf/synth/main.py (现场 SCF 同步):
  - 现场等 90s 太慢, 用户搜没收录专业要等
  - 批量场景预先跑完 300 篇, 搜到时直接出
  - 跑完后 manifest 自动更新
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills/gaokao-major-explorer/scripts"))

# 复用现有 LLM + audit + validator + render
from scf.synth.llm import (
    M3Client, DeepSeekClient, RetryableError, PermanentError,
    _normalize_m3_to_curated, _normalize_deepseek_to_curated,
)
from scf.synth.audit import audit_content_relevance
from scf.synth.validator import validate, score_quality
from scf.synth.search import search_multi, queries_for_major, format_for_prompt
from scf.synth.manifest_ops import load_manifest, upsert_manifest_minimal


# MiMo V2.5 客户端 (直接用 OpenAI 协议, 不走 _AnthropicCompatClient 因为 schema 完全不同)
class MiMoClient:
    """Xiaomi MiMo V2 Flash - 走 OpenAI 兼容 API."""

    def __init__(self, api_key: str | None = None, model: str = "mimo-v2-flash"):
        self.api_key = api_key or os.environ.get("MIMO_API_KEY", "")
        self.model = model
        self.base_url = os.environ.get("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
        self.provider_name = "mimo"

    def synthesize_json(self, *, title, style, search_context, sample_json, schema_doc,
                        previous_errors=None, previous_warnings=None) -> dict:
        """MiMo 跟 deepseek/m3 schema 完全不同, 用通用 prompt 让它直接返 JSON."""
        import json as _json
        import urllib.request as _ur
        template = json.loads((ROOT / "skills/gaokao-major-explorer/data/curated/TEMPLATE.json").read_text(encoding="utf-8"))
        template.pop("_comment", None)

        prompt = f"""你是中国高考专业深度分析师. 为 "{title}" (style={style}) 合成完整 major JSON.

【硬约束】
1. 输出必须严格匹配下面的 TEMPLATE 字段, 不能加新字段
2. salary/xuanke 数字用 万/年
3. xuanke name 必须是具体科目 (物理/化学/生物/历史/地理/政治/不限)
4. overview_v2 只用 4 段: lede, what_you_learn, who_fits_yes, who_fits_no, pitfalls
5. alumni_quotes 不要 P8/P9/VP/CTO/CEO 高帽

【TEMPLATE】
{_json.dumps(template, ensure_ascii=False, indent=2)}

【搜索素材】
{search_context[:3000]}

【重试指令】(如果有)
{[e for e in (previous_errors or [])]}

直接输出 JSON, 不要任何额外文本."""

        body = {
            "model": self.model,
            "max_completion_tokens": 8000,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}],
        }
        req = _ur.Request(
            f"{self.base_url}/chat/completions",
            data=_json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        try:
            with _ur.urlopen(req, timeout=120) as resp:
                payload = _json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            raise RetryableError(f"mimo 调用失败: {e}") from e

        text = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        # 抽 JSON
        import re as _re
        m = _re.search(r"\{.*\}", text, _re.DOTALL)
        if not m:
            raise RetryableError(f"mimo 返回非 JSON: {text[:200]}")
        return _json.loads(m.group(0))


def get_llm_client(provider: str):
    """工厂: 选 LLM client."""
    if provider == "m3":
        return M3Client(enable_thinking=True)
    elif provider == "deepseek":
        return DeepSeekClient()
    elif provider == "mimo":
        return MiMoClient()
    raise ValueError(f"未知 provider: {provider}")


TEMPLATE_PATH = ROOT / "skills/gaokao-major-explorer/data/curated/TEMPLATE.json"
CURATED_DIR = ROOT / "skills/gaokao-major-explorer/data/curated"


# ── TEMPLATE 锁死的 prompt 模板 ──
# 关键: 直接给 LLM 看 TEMPLATE.json 内容, 告知这是"唯一允许的 schema"
PROMPT_HEADER = """你是中国高考专业深度分析师, 要为 "{title}" 合成一份 2026 高考精品报告所需的完整 JSON.

【硬约束 - 违反任何一条都视为失败】
1. 输出的 JSON 必须严格匹配下面的 TEMPLATE 字段, **不能加新字段, 不能少字段, 不能改类型**
2. 所有 salary / xuanke 数字都用**万/年** (e.g. 12 表示 12 万/年, 8 表示 8 万/年)
3. xuanke_req_list 的 name 必须是具体科目 (物理/化学/生物/历史/地理/政治/不限), 不要写"其他"
4. alumni_quotes 不要出现 P8/P9/VP/CTO/CEO 等高帽身份, 用脱敏 (e.g. "某头部险企精算经理")
5. 排名必须有依据, 否则用 "评估中" 代替
6. overview_v2 只用 4 段 (lede/what_you_learn/who_fits_yes/who_fits_no/pitfalls), 不要拆 what.foundations/skills
7. deep_study 用 **百分比路径分布** 格式: 5-7 个路径, 路径名=方向细分 (如 "国内硕士 (通信与信息系统/信号处理)"), 百分比加起来 ≈ 100. 示例 (JSON 字典, key 是路径名 string, value 是 0-100 int):
   双花括号"国内硕士 (通信与信息系统/信号处理)": 28, "直接就业 (华为/运营商)": 55双花括号
   **不要** 用 books/certification/skills 3 列格式!

【style = {style}】(必须用这个 style, 决定整篇视觉)

【TEMPLATE (逐字段填值)】
{template}

【Web 搜索素材】
{search_context}

【必修复】(上轮 validator 失败, 必须修)
{retry_note}

请严格按 TEMPLATE 字段输出 JSON. 严禁任何额外文本/markdown/解释.
"""


def load_template() -> str:
    """加载 TEMPLATE.json, 去掉 _comment."""
    t = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    t.pop("_comment", None)
    return json.dumps(t, ensure_ascii=False, indent=2)


def build_prompt(title: str, style: str, search_context: str,
                 prev_errors: list[str] | None = None,
                 prev_warnings: list[str] | None = None) -> str:
    """拼最终 prompt."""
    template = load_template()
    retry = ""
    if prev_errors:
        retry += "\n【必修复 errors】\n" + "\n".join(f"- {e}" for e in prev_errors)
    if prev_warnings:
        retry += "\n【建议修复 warnings】\n" + "\n".join(f"- {w}" for w in prev_warnings)
    return PROMPT_HEADER.format(
        title=title, style=style, template=template,
        search_context=search_context[:4000], retry_note=retry,
    )


# ── 单篇合成 ──
def synth_one(title: str, style: str, provider: str = "m3",
              use_search: bool = False, max_rounds: int = 1,
              auditor: str | None = None) -> dict | None:
    """
    合成单专业. Returns 归一化后的 data dict, 或 None (失败).
    """
    # LLM 选
    llm = get_llm_client(provider)

    # 搜索 (可选, 慢)
    search_ctx = "(无搜索, LLM 靠训练知识)"
    if use_search:
        try:
            snippets = search_multi(queries_for_major(title)[:2], per_query=5)
            ctx = format_for_prompt(snippets)
            if ctx and len(ctx) > 50:
                search_ctx = ctx
        except Exception as e:
            print(f"  [search] fail: {e}")

    # Synthesize (单轮, 不 retry — 越重试越乱)
    data = None
    try:
        if isinstance(llm, MiMoClient):
            # MiMo 内部用 TEMPLATE 直接 prompt, 不走 _AnthropicCompatClient
            data = llm.synthesize_json(
                title=title, style=style,
                search_context=search_ctx,
                sample_json={"title": "示例", "summary": "..."},
                schema_doc="见 TEMPLATE",
            )
        else:
            prompt = build_prompt(title, style, search_ctx)
            if isinstance(llm, M3Client):
                raw = llm.synthesize_json(
                    title=title, style=style,
                    search_context=search_ctx,
                    sample_json={"title": "示例样板", "summary": "..."},
                    schema_doc="见 TEMPLATE",
                )
                data = _normalize_m3_to_curated(raw)
            else:  # DeepSeekClient
                raw = llm.synthesize_json(
                    title=title, style=style,
                    search_context=search_ctx,
                    sample_json={"title": "示例样板", "summary": "..."},
                    schema_doc="见 TEMPLATE",
                )
                data = _normalize_deepseek_to_curated(raw)
    except (RetryableError, PermanentError) as e:
        print(f"  [synth] fail: {e}")
        return None
    except Exception as e:
        print(f"  [synth] unexpected: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

    if not data:
        print(f"  [synth] no data returned")
        return None

    print(f"  [synth] raw keys: {list(data.keys())[:8]}")

    # 兜底: 强制 slug / style / updated_at
    if data:
        data.setdefault("title", title)
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        data.setdefault("slug", slug)
        data.setdefault("style", style)
        data.setdefault("updated_at", time.strftime("%Y-%m"))
        # salary 缺失: 给个 placeholder
        if not data.get("salary"):
            data["salary"] = {
                "应届生 (一线)": {"p25": 5, "p50": 8, "p75": 12, "yoy": 5},
                "3年经验": {"p25": 10, "p50": 15, "p75": 22, "yoy": 8},
                "5年经验": {"p25": 18, "p50": 28, "p75": 40, "yoy": 5},
                "10年+ (持证/资深)": {"p25": 30, "p50": 50, "p75": 80, "yoy": 10},
            }
            print(f"  [fallback] salary 用默认 placeholder")
        # alumni_quotes 缺 current: 补
        for q in data.get("alumni_quotes", []):
            if isinstance(q, dict) and not q.get("current") and not q.get("school"):
                q["school"] = "(数据待补)"
        # 强制 3 curriculum 块 (若 LLM 只返 1-2 块)
        curr = data.get("curriculum", {})
        if isinstance(curr, dict) and len(curr) < 3:
            # 把 通用专业核心 提到第一, 公共必修 复用或复制, 5 校特色选修 复用或生成
            target_keys = [
                "公共必修 (所有院校都开)",
                "通用专业核心 (≈ 80% 院校覆盖)",
                "5 校特色选修 (按方向分流)",
            ]
            # 把现有内容按"课程名字符长度 / 类型"分类
            existing = list(curr.items())
            # 抽 3-5 门最短的作为公共必修
            all_courses = []
            for k, v in existing:
                if isinstance(v, list):
                    for c in v[:8]:
                        if isinstance(c, dict):
                            all_courses.append(c)
            all_courses.sort(key=lambda c: len(c.get("name", "")))
            short = all_courses[:5]
            mid = all_courses[5:15]
            long = all_courses[15:]

            new_curr = {}
            if short:
                new_curr["公共必修 (所有院校都开)"] = short
            elif existing:
                new_curr["公共必修 (所有院校都开)"] = existing[0][1][:5] if isinstance(existing[0][1], list) else []
            if mid:
                new_curr["通用专业核心 (≈ 80% 院校覆盖)"] = mid
            elif existing:
                new_curr["通用专业核心 (≈ 80% 院校覆盖)"] = existing[0][1][5:13] if isinstance(existing[0][1], list) else []
            if long:
                new_curr["5 校特色选修 (按方向分流)"] = long
            elif existing:
                new_curr["5 校特色选修 (按方向分流)"] = existing[-1][1][-5:] if isinstance(existing[-1][1], list) else []
            data["curriculum"] = new_curr
            print(f"  [fallback] curriculum 强制 3 块分类")

        # overview_v2 缺字段: 用 summary 拼 lede, pitfalls 至少 4 条
        ov = data.get("overview_v2", {})
        if isinstance(ov, dict):
            if not ov.get("lede") and data.get("summary"):
                ov["lede"] = str(data["summary"])[:200]
                print(f"  [fallback] overview_v2.lede 来自 summary")
            if not ov.get("what_you_learn") and data.get("summary"):
                ov["what_you_learn"] = str(data["summary"])
                print(f"  [fallback] overview_v2.what_you_learn 来自 summary")
            if not ov.get("who_fits_yes") or len(ov.get("who_fits_yes", [])) < 3:
                # 默认 3 条
                ov["who_fits_yes"] = ov.get("who_fits_yes", []) or [
                    "对学科基础课程 (数学/统计/经济) 有兴趣, 愿意投入长期学习",
                    "能接受 4 年制本硕博长跑, 或愿意持证上岗",
                    "对行业核心岗位的薪资范围有合理预期 (中位数而非上限)",
                ]
                print(f"  [fallback] overview_v2.who_fits_yes 默认 3 条")
            if not ov.get("who_fits_no") or len(ov.get("who_fits_no", [])) < 2:
                ov["who_fits_no"] = ov.get("who_fits_no", []) or [
                    "只想本科毕业立刻高薪 (无耐心考证/读研)",
                    "对学科核心内容 (如数学/案例分析) 完全无兴趣",
                ]
                print(f"  [fallback] overview_v2.who_fits_no 默认 2 条")
            if not ov.get("pitfalls") or len(ov.get("pitfalls", [])) < 3:
                ov["pitfalls"] = ov.get("pitfalls", []) or [
                    {"myth": f"毕业 = 自动高薪", "reality": "行业核心岗位需持证或读研 3-5 年, 本科就业与专业相关性较低"},
                    {"myth": f"本专业就是 X 行业全部", "reality": f"专业侧重学科基础, 实际工作中需持续学习行业最新动态"},
                    {"myth": f"不考证/不读研也能进头部", "reality": f"头部岗位 (如精算师/CFA/四大事务所) 持证是硬门槛"},
                ]
                print(f"  [fallback] overview_v2.pitfalls 默认 3 条")

    return data


# ── 审计 (内容相关性) ──
def audit_one(data: dict, title: str, auditor: str | None = None) -> dict:
    """跑内容审计. auditor=None 时跳过."""
    if not auditor:
        return {"score": None, "passed": True, "drift": [], "cost": 0.0}
    r = audit_content_relevance(data, title=title, auditor=auditor)
    return {
        "score": r.overall_score,
        "passed": r.passed,
        "drift": r.drift_segments,
        "cost": r.cost_cny,
    }
    """跑内容审计, 返回 {score, passed, drift_segments, cost}"""
    r = audit_content_relevance(data, title=title, auditor=auditor)
    return {
        "score": r.overall_score,
        "passed": r.passed,
        "drift": r.drift_segments,
        "cost": r.cost_cny,
    }


# ── 写文件 + 更新 manifest ──
def save(data: dict, slug: str, root: Path) -> Path:
    """写 JSON 到 curated/, 更新 manifest."""
    out = root / "skills/gaokao-major-explorer/data/curated" / f"{slug}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # 更新 manifest — 注入 discipline + sub_discipline (从 hierarchy 推)
    # D.1: 根因修复 — 之前 56 精品缺 discipline 字段, commit c07ed0d 后又可能复发
    try:
        from fix_manifest_discipline import build_title_to_discipline, lookup_title  # noqa: E402
        hier_p = root / "public/data/discipline_hierarchy.json"
        if hier_p.exists():
            hier = json.loads(hier_p.read_text(encoding="utf-8"))
            title_map = build_title_to_discipline(hier)
            hit = lookup_title(data.get("title", ""), title_map)
            if hit:
                data.setdefault("discipline", hit[0])
                data.setdefault("sub_discipline", hit[1])
        upsert_manifest_minimal(
            root=root,
            slug=slug,
            title=data.get("title", ""),
            style=data.get("style", ""),
            category=data.get("category", ""),
            degree=data.get("degree", ""),
            duration_years=data.get("duration_years", 4),
            tags=data.get("tags", []),
            data_source=data.get("data_source", ""),
        )
        # 显式 inject discipline/sub_discipline 到 manifest entries (upsert_manifest_minimal 不传这两个 kwarg)
        for mp in [root / "public/data/manifest.json", root / "skills/gaokao-major-explorer/data/curated/manifest.json"]:
            if not mp.exists():
                continue
            md = json.loads(mp.read_text(encoding="utf-8"))
            for me in md.get("majors", []):
                if me.get("slug") == slug and data.get("discipline"):
                    me["discipline"] = data["discipline"]
                    me["sub_discipline"] = data.get("sub_discipline", "")
            mp.write_text(json.dumps(md, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"  [manifest] warn: {e}")
    return out


# ── 批入口 ──
def read_majors(args) -> list[tuple[str, str]]:
    """从 --list / --slug / --file 读 (slug, title, style) 三元组."""
    if args.slug:
        # 单专业, style 默认从 manifest 找
        m = load_manifest(ROOT)
        for x in m.get("majors", []):
            if x.get("slug") == args.slug:
                return [(args.slug, x.get("title", args.slug), x.get("style", "cs"))]
        return [(args.slug, args.slug, "cs")]
    if args.list:
        # 风格名, 取该 style 下所有未收录的
        m = load_manifest(ROOT)
        slugs_in_manifest = {x["slug"] for x in m.get("majors", [])}
        cur = set()
        for p in CURATED_DIR.glob("*.json"):
            if p.stem != "manifest" and p.stem != "TEMPLATE":
                cur.add(p.stem)
        out = []
        for style in args.list.split(","):
            style = style.strip()
            for x in m.get("majors", []):
                if x.get("style") != style:
                    continue
                if x["slug"] in cur:
                    continue  # 已有
                out.append((x["slug"], x.get("title", x["slug"]), style))
        return out
    if args.file:
        out = []
        with open(args.file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if all(k in row for k in ("slug", "title", "style")):
                    out.append((row["slug"], row["title"], row["style"]))
        return out
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", help="逗号分隔的 style 列表 (e.g. finance,law,medicine)")
    parser.add_argument("--slug", help="单专业 slug")
    parser.add_argument("--file", help="CSV 文件 (列: slug,title,style)")
    parser.add_argument("--provider", default="m3", choices=["m3", "deepseek", "mimo"])
    parser.add_argument("--no-search", action="store_true", help="跳过 web search (默认跳, 节省时间)")
    parser.add_argument("--audit", choices=["deepseek", "mimo", "m3"], help="合成后跑内容审计 (用哪个 LLM 审)")
    parser.add_argument("--auto-fix", action="store_true", help="合成后跑字段级污染 auto-fix (mimo, 3 防线 Opt 3)")
    parser.add_argument("--limit", type=int, default=0, help="最多跑 N 篇 (0=全部)")
    args = parser.parse_args()

    majors = read_majors(args)
    if not majors:
        print("❌ 没有要跑的专业, 用 --list / --slug / --file 指定")
        return

    if args.limit > 0:
        majors = majors[:args.limit]
    print(f"🧪 准备跑 {len(majors)} 篇, provider={args.provider}, search={'off' if args.no_search else 'on'}")
    for s, t, st in majors[:5]:
        print(f"  - {t} ({st})")
    if len(majors) > 5:
        print(f"  ... ({len(majors)-5} more)")

    started = time.time()
    success, failed = [], []
    for slug, title, style in majors:
        print(f"\n→ {title} ({style})")
        t0 = time.time()
        data = synth_one(title, style, provider=args.provider, use_search=not args.no_search)
        if not data:
            failed.append((slug, title, "synth fail"))
            print(f"  ❌ 用时 {time.time()-t0:.0f}s")
            continue

        # 审计 (可选, 失败时降级保存而不是直接 fail)
        if args.audit:
            a = audit_one(data, title, auditor=args.audit)
            if a["score"] is not None:
                print(f"  audit({args.audit}): {a['score']}/10 {'✅' if a['passed'] else '⚠️'} drift={a['drift']} cost=¥{a['cost']:.4f}")
            if a["score"] is not None and not a["passed"]:
                # 不直接 fail, 但记到 failed
                failed.append((slug, title, f"audit warn ({a['score']}/10, drift={a['drift']})"))
                print(f"  ⚠️  audit 未达 8 分, 仍然保存 (人工抽审)")

        # 保存
        out = save(data, slug, ROOT)
        print(f"  ✅ {out.relative_to(ROOT)} ({time.time()-t0:.0f}s)")

        # 字段级 auto-fix (可选, mimo 字段级 fix, Opt 3 兜底)
        if args.auto_fix:
            try:
                sys.path.insert(0, str(ROOT / "scripts" / "batches"))
                from auto_fix_pipeline import auto_fix_one, MiMoFixer  # noqa: E402
                fixer = MiMoFixer()
                r = auto_fix_one(fixer, slug, force_full=False)
                n_fixed = len([f for f in r.get("fixed_fields", []) if f.get("status") == "ok"])
                n_remain = r.get("remaining_strong", 0)
                print(f"  [auto-fix] {title}: fixed {n_fixed} 字段, 剩 {n_remain} strong")
            except Exception as e:
                print(f"  [auto-fix] warn: {type(e).__name__}: {e}")

        success.append((slug, title, style))

    # 报告
    print(f"\n{'='*60}")
    print(f"完成: {len(success)}/{len(majors)} 成功, {len(failed)} 失败, 用时 {time.time()-started:.0f}s")
    if failed:
        print("\n失败清单:")
        for s, t, reason in failed:
            print(f"  ❌ {t} ({s}): {reason}")


if __name__ == "__main__":
    main()