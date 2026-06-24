#!/usr/bin/env python3
"""regen_top_companies.py — 重生 18 篇占位符 top_companies.

Bug 背景: Day 3 Team A commit 13d3b3f9 m3 synth 占位符
{ tier: "B", headcount: "", salary: "", sparkline: [] },
18 篇专业还有这个 bug (11 篇 salary/headcount 全空, 7 篇 salary 写的是公司名).

策略: 调 LLM (默认 DeepSeek, m3 不可用时 fallback) 重生 top_companies 数组,
8-12 条真实头部雇主 + 真实 tier (S/A/B) + 真实薪资 (p25-p50-p75 范围) +
headcount 星标 + sparkline 5 元素.

用法:
  # Dry-run (1 个, 不写)
  python3 scripts/schema-fix/regen_top_companies.py --dry-run intelligent-medical-engineering

  # 真跑 (批量, 3 worker 并行)
  python3 scripts/schema-fix/regen_top_companies.py --workers 3 --slugs <slug1> <slug2> ...

  # 默认 18 篇
  python3 scripts/schema-fix/regen_top_companies.py
"""
import argparse
import json
import os
import re
import sys
import time
import concurrent.futures
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
CURATED = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"
MANIFEST = ROOT / "public" / "data" / "manifest.json"

# 18 bug 篇 (按 plan)
ALL_BUG_SLUGS = [
    # Subgroup A (tier=B, salary="", headcount="")
    "audiology-speech-rehabilitation",
    "basic-medicine",
    "biomedical-engineering",
    "clinical-engineering-technology",
    "food-hygiene-nutrition",
    "forensic-medicine",
    "intelligent-construction",
    "intelligent-medical-engineering",
    "medical-imaging",
    "ophthalmology-optometry",
    "preventive-medicine",
    # Subgroup B (tier=B, salary/headcount 错位)
    "bioinformatics",
    "blockchain-engineering",
    "food-science-engineering",
    "intelligent-manufacturing-engineering",
    "intelligent-vehicle-engineering",
    "network-space-security",
    "smart-agriculture",
]


def load_manifest():
    """读 manifest, 取 slug → style 映射."""
    m = json.loads(MANIFEST.read_text())
    return {x["slug"]: x for x in m.get("majors", [])}


def build_prompt(title: str, style: str, slug: str) -> str:
    """针对单专业的 top_companies 重生 prompt."""
    style_hint = {
        "medicine": "医学/医疗 (医院/药企/医疗器械/医疗 AI)",
        "eng": "工科 (制造业/建筑/汽车/能源)",
        "cs": "计算机/AI/网安/区块链/数据",
        "agri": "农学/食品/智慧农业",
        "sci": "理学 (生物/化学/物理)",
    }.get(style, "通用")

    return f"""你是 Major Explorer 内容团队. 为中国高考本科专业 "{title}" (style={style}, 行业={style_hint}) 重新生成 top_companies 字段.

## 严格要求

1. **数量 8-12 条**, 太短会扣分.
2. **真实公司** — 用 2024-2026 真实存在的雇主, 避免泛型"国家电网"除非真的对口. 优先本行业头部 + 跨界热门.
3. **tier 三档**:
   - S: 中央/央企/上市龙头/院士工作站 (e.g. 中国医药集团, 华大基因, 迈瑞医疗, 联影智能, 华为, 字节跳动, 腾讯, 阿里, 比亚迪, 中国电信, 中科院系所)
   - A: 头部独角兽/大厂事业部/上市公司二级 (e.g. 推想科技, 数坤科技, 卫宁健康, 东软集团, 蚂蚁集团, 微众银行, 商汤, 旷视, 寒武纪)
   - B: 中等门槛 (e.g. 中小型科技公司, 区域龙头, 创业公司)
4. **headcount 星标** (1-5 个 ★): S=★★★★★, A=★★★★, B=★★★, 招人多的可+1
5. **salary 字符串** 必须含 p25-p50-p75 数字范围 + 单位 (万/年), 格式:
   "应届 X-Y 万 / 3年+ Y-Z 万 / 5年+ Z-W 万 (行业说明)"
   例: "应届 18-28万 / 3年+ 35-50万 / 5年+ 60-100万 (高端医疗影像, 股权激励可观)"
6. **sparkline** 5 元素 [int*5]: 表示近 5 年招聘量趋势, 增长行业用 [3,4,5,5,5] / [3,4,5,6,7], 平稳用 [3,3,4,4,4], 收缩用 [5,4,3,3,3]. 各公司 sparkline 不要完全一样.
7. **针对本专业**: 不要套"互联网大厂"或"金融咨询", 要跟 "{title}" 真正对口.

## 输出格式 (严格 JSON, 严禁其他文本)

```json
[
  {{"name": "<公司名>", "tier": "S|A|B", "headcount": "★★★★★", "salary": "<p25-p50-p75 范围 + 行业说明>", "sparkline": [3,4,5,5,5]}},
  ...
]
```

## 重要
- 只输出一个 JSON 数组, 严禁 markdown ```json 包裹外的解释
- salary 不允许为空字符串, 必须含数字+万
- sparkline 必须是 5 个整数
- 如果该专业有医院/研究所/政府部门作为雇主, 也可加入 (但优先公司)"""


def _load_env():
    """从 .env 加载凭据 (如果 env 没设)."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        # 只在未设时填 (避免覆盖 shell 已设值)
        os.environ.setdefault(k, v)


_load_env()


def call_llm(prompt: str) -> list | None:
    """调 LLM, 返回 list[dict] 或 None (失败). 优先 DeepSeek (配置好), 备 m3."""
    text = None
    # 尝试 DeepSeek (raw HTTP, 已配置)
    try:
        import requests
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        base_url = "https://api.deepseek.com/anthropic"
        if api_key:
            r = requests.post(
                f"{base_url}/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "max_tokens": 4000,
                    "temperature": 0.4,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=90,
            )
            if r.status_code == 200:
                data = r.json()
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        break
            else:
                print(f"    [deepseek] HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
    except Exception as e:
        print(f"    [deepseek] 调用失败: {e}", file=sys.stderr)

    # 备 m3 (anthropic SDK, 需 M3_API_KEY)
    if text is None:
        m3_key = os.environ.get("M3_API_KEY", "")
        m3_base = os.environ.get("M3_BASE_URL", "https://api.minimaxi.com/anthropic")
        if m3_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=m3_key, base_url=m3_base)
                msg = client.messages.create(
                    model=os.environ.get("M3_MODEL", "MiniMax-M3"),
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}],
                )
                for block in msg.content:
                    if hasattr(block, "type") and block.type == "text":
                        text = block.text
                        break
            except Exception as e:
                print(f"    [m3] 调用失败: {e}", file=sys.stderr)

    if text is None:
        return None

    # 抽 JSON 数组
    return parse_top_companies_array(text)


def parse_top_companies_array(text: str) -> list | None:
    """从 LLM 文本抽 JSON array."""
    # 1. 抽 ```json ... ``` 块
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # 2. 直接 parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # 3. 抽第一个 [...]
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def validate_entry(c: dict) -> tuple[bool, str]:
    """校验单条 schema. 返回 (ok, reason)."""
    if not isinstance(c, dict):
        return False, f"not dict: {type(c).__name__}"
    if not c.get("name", "").strip():
        return False, "missing name"
    if c.get("tier") not in ("S", "A", "B"):
        return False, f"bad tier: {c.get('tier')!r}"
    if not c.get("headcount", "").strip():
        return False, "empty headcount"
    salary = c.get("salary", "")
    if not salary or not re.search(r"\d+\s*[-~到至]\s*\d+\s*万", salary):
        return False, f"salary missing range: {salary[:50]!r}"
    spark = c.get("sparkline", [])
    if not isinstance(spark, list) or len(spark) != 5 or not all(isinstance(x, int) for x in spark):
        return False, f"bad sparkline: {spark!r}"
    return True, "ok"


def regen_one(slug: str, manifest: dict, dry_run: bool) -> dict:
    """重生单篇. 返回 result dict {slug, ok, ...}."""
    info = manifest.get(slug, {})
    title = info.get("title", slug)
    style = info.get("style", "sci")
    path = CURATED / f"{slug}.json"
    if not path.exists():
        return {"slug": slug, "ok": False, "reason": "file not found"}

    original = json.loads(path.read_text())
    original_tc = original.get("top_companies", [])

    prompt = build_prompt(title, style, slug)
    result = call_llm(prompt)
    if result is None:
        return {"slug": slug, "ok": False, "reason": "LLM call failed"}

    # 校验
    valid = [c for c in result if validate_entry(c)[0]]
    invalid = [c for c in result if not validate_entry(c)[0]]

    if len(valid) < 6:
        return {
            "slug": slug, "ok": False, "reason": f"only {len(valid)} valid entries",
            "valid": valid, "invalid": invalid,
        }

    if dry_run:
        return {
            "slug": slug, "ok": True, "dry_run": True,
            "n_original": len(original_tc), "n_new": len(valid),
            "new": valid,
        }

    # 写回 (保留其他字段)
    original["top_companies"] = valid[:12]  # 截断到 12
    path.write_text(json.dumps(original, ensure_ascii=False, indent=2))
    return {
        "slug": slug, "ok": True, "n_original": len(original_tc), "n_new": len(valid),
        "invalid_skipped": len(invalid),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs_pos", nargs="*", help="slugs (positional, optional)")
    ap.add_argument("--slugs", nargs="*", help="slugs to process (default: all 18 bug files)")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true", help="print diff, don't write")
    args = ap.parse_args()
    # 兼容 positional 和 --slugs 两种用法
    slugs = args.slugs or args.slugs_pos or ALL_BUG_SLUGS
    manifest = load_manifest()

    print(f"Processing {len(slugs)} slugs with {args.workers} workers (dry_run={args.dry_run})")
    print(f"LLM provider: deepseek={'✓' if os.environ.get('DEEPSEEK_API_KEY') else '✗'} m3={'✓' if os.environ.get('M3_API_KEY') else '✗'}")

    t0 = time.time()
    results = []
    if args.workers <= 1:
        for s in slugs:
            r = regen_one(s, manifest, args.dry_run)
            results.append(r)
            status = "✓" if r["ok"] else "✗"
            extra = f" ({r.get('reason','')})" if not r["ok"] else f" n={r.get('n_new','?')}"
            print(f"  {status} {s}{extra}")
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(regen_one, s, manifest, args.dry_run): s for s in slugs}
            for fut in concurrent.futures.as_completed(futs):
                r = fut.result()
                results.append(r)
                status = "✓" if r["ok"] else "✗"
                extra = f" ({r.get('reason','')})" if not r["ok"] else f" n={r.get('n_new','?')}"
                print(f"  {status} {r['slug']}{extra}")

    elapsed = time.time() - t0
    ok = sum(1 for r in results if r["ok"])
    print(f"\nDone: {ok}/{len(results)} ok in {elapsed:.1f}s")
    if not args.dry_run:
        failed = [r for r in results if not r["ok"]]
        if failed:
            print("\nFailed slugs (need manual fix):")
            for r in failed:
                print(f"  - {r['slug']}: {r.get('reason','?')}")


if __name__ == "__main__":
    main()
