#!/usr/bin/env python3
"""
auto_fix_pipeline.py — 字段级自动 fix 一条龙 (Opt 3).

流程: synth (mimo) → 字段级污染检测 → 字段级 m3 fix → 重检测 → 部署

用法:
  python3 scripts/batches/auto_fix_pipeline.py --csv scripts/batches/day1_resynth_mimo.csv
  python3 scripts/batches/auto_fix_pipeline.py --slugs optoelectronic-information-science-engineering
"""
import sys, os, json, csv, argparse, re, time, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scf"))
sys.path.insert(0, str(ROOT / "scripts/batches"))

from synth.llm import M3Client  # noqa: E402
from contam_dict import detect_contamination  # noqa: E402

CUR = ROOT / "skills/gaokao-major-explorer/data/curated"


# ── MiMo 客户端 (字段级 fix 用, 比 m3 简洁快速) ──
class MiMoFixer:
    def __init__(self):
        import urllib.request, urllib.error
        self.api_key = os.environ.get("MIMO_API_KEY", "")
        self.base_url = os.environ.get("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
        self.model = os.environ.get("MIMO_MODEL", "mimo-v2-flash")

    def fix(self, prompt: str) -> dict:
        import urllib.request as _ur
        import json as _json
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
            return {"error": f"mimo 调用失败: {e}"}
        text = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return {"error": f"mimo 非 JSON: {text[:200]}"}
        try:
            return _json.loads(m.group(0))
        except Exception as e:
            return {"error": f"JSON parse: {e}: {text[:200]}"}


# ── 字段级 fix 模板 (mimo 用的) ──
FIX_FIELD_PROMPT = """你是中国高考专业内容修复员. 重新生成 "{title}" 专业 ({style}) 的 "{field}" 字段.

【当前内容 (有污染, 必须替换)】:
{current}

【污染词 (严禁出现)】: {forbidden}

【修复要求 - 严格遵守】:
1. 严格属于 "{title}" 专业, 不是任何其他专业
2. 必须用真实的公司名/岗位/技术术语/具体场景
3. 避免泛化模板 ("行业头部" "Top 10" "央企国企" "咨询审计")
4. 长度/数量与原内容一致 (e.g. 5-7 条 employment_direction, 3 条 pitfalls)
5. 不确定的字段填 "数据待补"

【输出严格 JSON 格式, 字段名 = {field}】: 只输出 JSON, 不要 markdown.
"""


def fix_field(fixer, title: str, style: str, field: str, current, forbidden: list) -> dict:
    """字段级 fix: 用 mimo 重写一个字段."""
    prompt = FIX_FIELD_PROMPT.format(
        title=title, style=style, field=field,
        current=json.dumps(current, ensure_ascii=False, indent=2)[:4000],
        forbidden=", ".join(forbidden[:10]),
    )
    return fixer.fix(prompt)


def get_field(data: dict, field: str):
    """从 JSON 拿字段值, 支持 nested paths like overview_v2.pitfalls."""
    parts = field.split(".")
    val = data
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p)
        else:
            return None
    return val


def set_field(data: dict, field: str, value):
    """设置字段值, 支持 nested paths."""
    parts = field.split(".")
    obj = data
    for p in parts[:-1]:
        if p not in obj:
            obj[p] = {}
        obj = obj[p]
    obj[parts[-1]] = value
    return data


def auto_fix_one(fixer, slug: str, force_full: bool = False, max_rounds: int = 3) -> dict:
    """单 major 自动 fix 流程: 多轮检测+fix 直到无 strong 污染."""
    p = CUR / f"{slug}.json"
    if not p.exists():
        return {"slug": slug, "error": "json 缺失"}
    data = json.loads(p.read_text(encoding="utf-8"))
    title = data.get("title", slug)
    style = data.get("style", "")

    all_fixed = []
    for round_i in range(max_rounds):
        # 1) 检测
        issues = detect_contamination(data, title, style)
        strong_issues = [i for i in issues if i[1] == "strong"]
        if not strong_issues and not force_full:
            break

        # 2) 字段级 fix (只修 strong)
        round_fixed = []
        for field, level, hits in strong_issues:
            current = get_field(data, field)
            if current is None:
                continue
            result = fix_field(fixer, title, style, field, current, hits)
            if "error" in result:
                round_fixed.append({"field": field, "status": "fail", "error": result["error"]})
                continue
            new_val = result.get(field)
            if new_val is None:
                for v in result.values():
                    if isinstance(v, (list, dict)):
                        new_val = v
                        break
            if new_val is not None:
                set_field(data, field, new_val)
                round_fixed.append({"field": field, "status": "ok", "new": str(new_val)[:100]})
        all_fixed.extend(round_fixed)
        if not any(f["status"] == "ok" for f in round_fixed):
            break

    # 3) 写回
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4) 重检测
    issues_after = detect_contamination(data, title, style)
    return {
        "slug": slug,
        "title": title,
        "fixed_fields": all_fixed,
        "rounds": round_i + 1,
        "remaining_strong": len([i for i in issues_after if i[1] == "strong"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--slugs", nargs="*")
    ap.add_argument("--force", action="store_true", help="强制 re-fix (不跳过 clean)")
    args = ap.parse_args()

    pairs = []
    if args.csv:
        with open(args.csv) as f:
            for row in csv.DictReader(f):
                if row.get("slug"):
                    pairs.append((row["slug"], row.get("title", "")))
    if args.slugs:
        for s in args.slugs:
            title = json.loads((CUR / f"{s}.json").read_text()).get("title", s)
            pairs.append((s, title))

    if not pairs:
        print("❌ no input")
        return

    print(f"🔧 字段级 auto-fix pipeline: {len(pairs)} 篇 (mimo 字段级 fix)")
    fixer = MiMoFixer()
    results = []
    for i, (slug, title) in enumerate(pairs, 1):
        try:
            r = auto_fix_one(fixer, slug, force_full=args.force)
        except Exception as e:
            r = {"slug": slug, "error": f"{type(e).__name__}: {e}"}
        status = r.get("status", "fixed")
        if status == "clean":
            print(f"[{i}/{len(pairs)}] ✅ {title}: clean")
        elif "error" in r:
            print(f"[{i}/{len(pairs)}] ❌ {title}: {r['error']}")
        else:
            n_fixed = len([f for f in r.get("fixed_fields", []) if f.get("status") == "ok"])
            n_remain = r.get("remaining_strong", 0)
            print(f"[{i}/{len(pairs)}] 🔧 {title}: fixed {n_fixed} fields, {n_remain} remaining")
        results.append(r)

    ok = [r for r in results if "error" not in r]
    clean = [r for r in ok if r.get("status") == "clean"]
    fixed = [r for r in ok if r.get("status") == "fixed"]
    print(f"\n{'='*60}")
    print(f"汇总: {len(ok)}/{len(results)} OK | {len(clean)} clean | {len(fixed)} fixed")
    if fixed:
        all_clean = [r for r in fixed if r.get("remaining_strong", 0) == 0]
        print(f"完全 clean: {len(all_clean)}/{len(fixed)}")


if __name__ == "__main__":
    main()
