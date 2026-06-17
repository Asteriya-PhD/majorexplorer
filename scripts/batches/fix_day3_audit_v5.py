"""fix_day3_audit_v5.py — Day 3 Team A 47 篇 curriculum 特色课补全 + lede 主谓完整句微改

策略 (v2 handoff §4.4-4.5):
1. curriculum: m3 补全 5-10 门特色课 (基于行业需求)
2. lede: m3 微改 第一句 (主谓完整, 30-50 字, 1 个独特洞察, 不要数据堆砌)

Phase 拆开跑, 失败可单跑
"""
import json
import re
import sys
import time
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CUR = ROOT / "skills/gaokao-major-explorer/data/curated"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scf"))

CSV = ROOT / "scripts/batches/day3_team_a.csv"
MAJORS = []
with open(CSV) as f:
    for row in csv.DictReader(f):
        MAJORS.append((row["slug"], row["title"], row["style"]))

print(f"[fix_v5] Found {len(MAJORS)} majors")


from synth.llm import M3Client


CURRICULUM_PROMPT = """你是中国高考专业课程顾问. 基于该专业的核心方向, 补全 5-10 门特色课.

【专业】: {title} ({style})
【当前 curriculum (前 12 条)】: {current}
【专业核心方向】: {core_directions}

【要求】:
1. 补全的课必须是该专业**特色课** (机器视觉/单细胞测序/法律卷宗 — 别的专业不开)
2. 避免: 通用基础课 (高数/英语/思政) — 这些不算特色
3. 输出 5-10 门, 简短课程名 (3-12 字), 不要解释
4. 严格 JSON 数组输出, 不要其他文字

【输出】:
["课程1", "课程2", "课程3", ...]
"""


LEDE_PROMPT = """你是中国高考专业文案编辑. 重写下面专业的 lede 第一句, 让其符合"主谓完整句 + 独特洞察"标准.

【专业】: {title} ({style})
【当前 lede】: {current}
【核心数据点 (可挑 1 个用)】: {data_points}

【要求】:
1. 主谓完整 (有主语+谓语+宾语), 不要电报体
2. 1 个独特洞察 (不只描述"是什么", 说"为什么特别"或"踩什么坑")
3. 30-50 字 (原 lede 可能 80-150 字, 缩到 30-50)
4. 不要纯数字堆砌 ("35%/18%/12%...")
5. 1 句话, 句号结尾
6. 严格 JSON 输出: {{"new_lede": "..."}}
"""


def call_m3(client, prompt, max_tokens=8000):
    # m3 thinking 块非常 verbose, 必须留足 max_tokens 给 text
    # (4000 不够, 8000 稳)
    body = {
        "max_tokens": max_tokens,
        "temperature": 0.5,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        resp = client._call(body)
    except Exception as e:
        return None, f"m3 call fail: {e}"
    content_list = resp.get("content", [])
    text = ""
    for block in content_list:
        if block.get("type") == "text":
            text += block.get("text", "")
    return text, "ok"


def fix_curriculum_one(client, slug, title, style):
    p = CUR / f"{slug}.json"
    data = json.loads(p.read_text())
    cur = data.get("curriculum", {})
    if isinstance(cur, dict):
        # 合并所有课程到一个 list
        all_courses = []
        for k, v in cur.items():
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        all_courses.append(item.get("name", str(item)))
                    else:
                        all_courses.append(str(item))
        current_str = json.dumps(all_courses[:12], ensure_ascii=False)
    else:
        current_str = "[]"

    # 核心方向 (从 employment_direction 提取)
    emp = data.get("employment_direction", [])
    core_directions = " / ".join([e.get("name", "") for e in emp[:5]])

    prompt = CURRICULUM_PROMPT.format(
        title=title, style=style, current=current_str, core_directions=core_directions
    )
    text, msg = call_m3(client, prompt)  # 用默认 max_tokens=8000
    if not text:
        return None, msg

    # 1. 先试直接 json.loads
    try:
        new_courses = json.loads(text.strip())
        if isinstance(new_courses, list) and len(new_courses) >= 3:
            return new_courses[:10], "ok"
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. 剥离 markdown 包装
    clean = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()

    # 3. 先试 clean json.loads
    try:
        new_courses = json.loads(clean)
        if isinstance(new_courses, list) and len(new_courses) >= 3:
            return new_courses[:10], "ok"
    except (json.JSONDecodeError, ValueError):
        pass

    # 4. 提取 [ ... ] 块 (any content)
    m = re.search(r"\[[^\[\]]*\]", clean, re.DOTALL)
    if not m:
        return None, "no JSON array found"
    try:
        new_courses = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return None, f"JSON parse fail: {e}"
    if not isinstance(new_courses, list):
        return None, "not a list"
    if len(new_courses) < 3:
        return None, f"too few items ({len(new_courses)})"
    return new_courses[:10], "ok"


def fix_lede_one(client, slug, title, style):
    p = CUR / f"{slug}.json"
    data = json.loads(p.read_text())
    cur_lede = (data.get("overview_v2") or {}).get("lede", "")

    # 提取关键数据点
    emp = data.get("employment_direction", [])
    sal = data.get("salary", {})
    data_points = []
    if emp:
        top = sorted(emp, key=lambda x: -x.get("pct", 0))[:2]
        data_points.extend([f"{e['name']} {e['pct']}%" for e in top])
    if sal and "应届生" in sal:
        data_points.append(f"应届 {sal['应届生']['p50']} 元/月")
    if sal and "3-5年" in sal:
        data_points.append(f"3-5年 {sal['3-5年']['p50']} 元/月")
    dp_str = "; ".join(data_points) or "(无数据点)"

    prompt = LEDE_PROMPT.format(
        title=title, style=style, current=cur_lede[:300], data_points=dp_str
    )
    text, msg = call_m3(client, prompt)  # 用默认 max_tokens=8000
    if not text:
        return None, msg

    # 剥离 markdown 包装
    clean = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()

    # 1. 先试直接 json.loads
    try:
        obj = json.loads(clean)
        if isinstance(obj, dict) and "new_lede" in obj:
            return obj["new_lede"], "ok"
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. 提取 { ... "new_lede" ... } 块 (宽松: 允许内层双引号未转义)
    #    用正向查找: "new_lede": " 之后, 找最后一个 " 后跟 }
    m = re.search(r'"?new_lede"?\s*:\s*"(.+?)"\s*\}', clean, re.DOTALL)
    if m:
        return m.group(1).strip(), "ok"

    # 3. fallback: 找 "new_lede": "..." 用 greedy 匹配
    m = re.search(r'"new_lede"\s*:\s*"(.+)"', clean, re.DOTALL)
    if m:
        return m.group(1).strip().rstrip('"').rstrip(',').rstrip('"').strip(), "ok"

    return None, "no JSON object found"


def fix_one(client, slug, title, style, phase="all"):
    p = CUR / f"{slug}.json"
    if not p.exists():
        return False, "json 缺失"
    data = json.loads(p.read_text())

    changes = []

    # Phase 1: curriculum
    if phase in ("all", "curriculum"):
        new_courses, msg = fix_curriculum_one(client, slug, title, style)
        if new_courses:
            # 添加到 curriculum.特色课 (新 key)
            if "curriculum" not in data:
                data["curriculum"] = {}
            data["curriculum"]["特色课"] = [{"name": c} for c in new_courses]
            changes.append(f"+特色课({len(new_courses)})")
        else:
            changes.append(f"!curriculum:{msg}")

    # Phase 2: lede
    if phase in ("all", "lede"):
        new_lede, msg = fix_lede_one(client, slug, title, style)
        if new_lede and 20 <= len(new_lede) <= 120:
            if "overview_v2" not in data:
                data["overview_v2"] = {}
            data["overview_v2"]["lede"] = new_lede
            changes.append("+lede")
        else:
            changes.append(f"!lede:{msg}")

    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, ", ".join(changes) if changes else "no change"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all", choices=["all", "curriculum", "lede"])
    args = ap.parse_args()

    print(f"[fix_v5] starting, phase={args.phase}")
    client = M3Client(enable_thinking=False)
    ok = 0
    fail = 0
    fail_slugs = []
    start = time.time()
    for i, (slug, title, style) in enumerate(MAJORS, 1):
        t0 = time.time()
        try:
            success, msg = fix_one(client, slug, title, style, phase=args.phase)
            dt = time.time() - t0
            if success:
                ok += 1
                print(f"  [{i:2d}/{len(MAJORS)}] OK   {slug:50s} {dt:.1f}s | {msg}")
            else:
                fail += 1
                fail_slugs.append((slug, msg))
                print(f"  [{i:2d}/{len(MAJORS)}] FAIL {slug:50s} {dt:.1f}s {msg}")
        except Exception as e:
            fail += 1
            fail_slugs.append((slug, str(e)))
            print(f"  [{i:2d}/{len(MAJORS)}] ERR  {slug:50s} {e}")

    elapsed = time.time() - start
    print()
    print(f"[fix_v5] done: {ok} ok, {fail} fail, {elapsed:.0f}s")
    if fail_slugs:
        print(f"Fail slugs:")
        for s, m in fail_slugs[:10]:
            print(f"  {s}: {m}")


if __name__ == "__main__":
    main()
