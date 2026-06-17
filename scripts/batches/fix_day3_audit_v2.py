"""fix_day3_audit_v2.py — Day 3 Team A 47 篇加 deep_study + 重写 lede, 目标 audit >= 9/10

- 给 47 篇加 deep_study 字段 (5-7 路径 + 百分比加和=100)
- 重写 lede 让其有"主谓+独特洞察"
- 清理 pitfalls 串台 (历史 m3 synth 篇)
- 使用 m3 _call() 直接调用, 避免 synthesize_json schema 复杂
"""
import json
import sys
import time
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
CUR = ROOT / "skills/gaokao-major-explorer/data/curated"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scf"))

from synth.llm import M3Client  # noqa

import csv
CSV = ROOT / "scripts/batches/day3_team_a.csv"
MAJORS = []
with open(CSV) as f:
    for row in csv.DictReader(f):
        MAJORS.append((row["slug"], row["title"], row["style"]))

print(f"[fix_v2] Found {len(MAJORS)} majors")


PROMPT = """你是中国高考专业内容质量提升员. 基于已有数据,生成:
1. deep_study: 5-7 条深造/就业路径, 每条必须有具体百分比 (int), 加和=100.
2. new_lede: 1 句话 (50-100 字), 主谓完整 + 独特洞察 + 1-2 个关键数据点, 避免数据堆砌.
3. pitfalls_fix: 5 对 myth/reality, 该专业特有 (不是金融/会计等串台词).

【专业】: {title} ({style})
【已有数据摘要】:
{json_str}

【输出严格 JSON 格式】 (不要任何其他文字):
{{
  "deep_study": {{"国内 985 硕博": 35, "海外硕博": 8, "直接就业央国企": 25, "选调公务员": 8, "创业": 4, "跨行": 5, "其他": 15}},
  "new_lede": "...",
  "pitfalls_fix": ["myth 1", "reality 1", "myth 2", "reality 2", "myth 3", "reality 3", "myth 4", "reality 4", "myth 5", "reality 5"]
}}
注意: deep_study 必须加和=100; new_lede 必须有主谓+独特洞察; pitfalls_fix 5 对是该专业真实坑.
"""


def call_m3(client, prompt):
    """直接调用 m3, 返回解析的 dict 或 None."""
    body = {
        "max_tokens": 8000,
        "temperature": 0.7,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = client._call(body)
    # Extract text from content list (skip thinking blocks)
    content_list = resp.get("content", [])
    text = ""
    for block in content_list:
        if block.get("type") == "text":
            text += block.get("text", "")
    # Find JSON block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        json_str = m.group(1)
    else:
        # Try to find raw JSON
        m = re.search(r"\{[^{}]*\"deep_study\"[^{}]*\}", text, re.DOTALL)
        if m:
            json_str = m.group(0)
        else:
            # Last resort: try the whole text
            json_str = text
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def fix_one(client, slug, title, style):
    p = CUR / f"{slug}.json"
    data = json.loads(p.read_text())
    slim = {
        "title": data.get("title", title),
        "style": data.get("style"),
        "employment_direction": data.get("employment_direction", [])[:5],
        "current_lede": (data.get("overview_v2") or {}).get("lede", ""),
        "existing_deep_study": data.get("deep_study"),
        "current_pitfalls": (data.get("overview_v2") or {}).get("pitfalls", [])[:3],
    }
    json_str = json.dumps(slim, ensure_ascii=False, indent=2)[:3500]
    prompt = PROMPT.format(title=title, style=style, json_str=json_str)

    resp = call_m3(client, prompt)
    if not resp:
        return False, "no response"

    # Update data
    if "deep_study" in resp and isinstance(resp["deep_study"], dict):
        ds = resp["deep_study"]
        # Normalize to int and sum to 100
        ds_int = {k: int(round(float(v))) for k, v in ds.items()}
        total = sum(ds_int.values())
        if total > 0 and abs(total - 100) > 1:
            ds_int = {k: round(v * 100 / total) for k, v in ds_int.items()}
            # Fix rounding error
            diff = 100 - sum(ds_int.values())
            if ds_int:
                first_key = list(ds_int.keys())[0]
                ds_int[first_key] += diff
        data["deep_study"] = ds_int

    if "new_lede" in resp and isinstance(resp["new_lede"], str) and len(resp["new_lede"]) > 10:
        if "overview_v2" not in data:
            data["overview_v2"] = {}
        data["overview_v2"]["lede"] = resp["new_lede"]

    if "pitfalls_fix" in resp and isinstance(resp["pitfalls_fix"], list) and len(resp["pitfalls_fix"]) >= 10:
        new_pitfalls = []
        for i in range(0, len(resp["pitfalls_fix"]), 2):
            if i + 1 < len(resp["pitfalls_fix"]):
                new_pitfalls.append({"myth": resp["pitfalls_fix"][i], "reality": resp["pitfalls_fix"][i + 1]})
        if len(new_pitfalls) >= 5:
            if "overview_v2" not in data:
                data["overview_v2"] = {}
            data["overview_v2"]["pitfalls"] = new_pitfalls

    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, "ok"


def main():
    print("[fix_v2] starting...")
    client = M3Client(enable_thinking=True)
    ok = 0
    fail = 0
    fail_slugs = []
    start = time.time()
    for i, (slug, title, style) in enumerate(MAJORS, 1):
        t0 = time.time()
        try:
            success, msg = fix_one(client, slug, title, style)
            dt = time.time() - t0
            if success:
                ok += 1
                print(f"  [{i:2d}/47] OK   {slug:50s} {dt:.1f}s")
            else:
                fail += 1
                fail_slugs.append(slug)
                print(f"  [{i:2d}/47] FAIL {slug:50s} {msg} {dt:.1f}s")
        except Exception as e:
            fail += 1
            fail_slugs.append(slug)
            print(f"  [{i:2d}/47] ERR  {slug:50s} {e}")
    elapsed = time.time() - start
    print(f"\n[fix_v2] done: {ok}/{len(MAJORS)} OK, {fail} failed, {elapsed:.0f}s")
    if fail_slugs:
        print(f"Failed slugs: {fail_slugs}")


if __name__ == "__main__":
    main()
