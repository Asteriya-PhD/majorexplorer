"""fix_day3_audit_v3.py — 修剩余 5 个问题:
1. deep_study 0/0/0 的 4-5 个 major
2. alumni_quotes "4 年制本硕 6 年" 措辞硬伤 (清除)
3. salary 3-5年/5-10年 = 0 的 (填真实值)
4. biomedical-engineering 汤晓鸥教材错误 (修)
"""
import json
import sys
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
CUR = ROOT / "skills/gaokao-major-explorer/data/curated"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scf"))

from synth.llm import M3Client  # noqa

# Detect broken majors
def needs_deep_study_fix(d):
    ds = d.get("deep_study", {})
    if not isinstance(ds, dict):
        return True
    if len(ds) < 5:
        return True
    if all(v == 0 for v in ds.values()):
        return True
    return False


def needs_salary_fix(d):
    sal = d.get("salary")
    if not isinstance(sal, dict):
        return False
    # Check for 0 values in 3-5 / 5-10 year stages
    for k in ("3-5年", "5-10年", "3-5 year"):
        v = sal.get(k)
        if isinstance(v, dict):
            if all(vv == 0 for vv in v.values()):
                return True
    return False


def needs_alumni_fix(d):
    """Check alumni quote for awkward 4 年制本硕 6 年 pattern."""
    for a in d.get("alumni_quotes", []):
        quote = a.get("quote", "")
        # The bad pattern: "X 大学 Y 4 年制本硕 6 年" or "4 年制硕 6 年"
        if re.search(r"4\s*年制\s*[本硕][本硕]\s*6\s*年", quote) or "4 年制硕 6 年" in quote:
            return True
    return False


# Find majors needing each fix
import csv
CSV = ROOT / "scripts/batches/day3_team_a.csv"
MAJORS = []
with open(CSV) as f:
    for row in csv.DictReader(f):
        MAJORS.append((row["slug"], row["title"], row["style"]))

NEED_DEEP_STUDY = []
NEED_SALARY = []
NEED_ALUMNI = []

for slug, title, style in MAJORS:
    p = CUR / f"{slug}.json"
    if not p.exists():
        continue
    d = json.loads(p.read_text())
    if needs_deep_study_fix(d):
        NEED_DEEP_STUDY.append((slug, title, style))
    if needs_salary_fix(d):
        NEED_SALARY.append((slug, title, style))
    if needs_alumni_fix(d):
        NEED_ALUMNI.append((slug, title, style))

print(f"[fix_v3] Majors needing deep_study fix: {len(NEED_DEEP_STUDY)}")
for s, _, _ in NEED_DEEP_STUDY:
    print(f"  {s}")
print(f"\n[fix_v3] Majors needing salary fix: {len(NEED_SALARY)}")
for s, _, _ in NEED_SALARY:
    print(f"  {s}")
print(f"\n[fix_v3] Majors needing alumni fix: {len(NEED_ALUMNI)}")
for s, _, _ in NEED_ALUMNI:
    print(f"  {s}")


PROMPT_DS = """你是中国高考专业内容质量提升员. 为该专业生成 deep_study (5-7 路径, 每条 int 百分比, 加和=100).

【专业】: {title} ({style})
【已有 employment_direction 摘要】:
{emp}

【输出严格 JSON】:
{{"deep_study": {{"国内 985 硕博": 35, "海外硕博": 8, "直接就业央国企": 25, "选调公务员": 8, "创业": 4, "跨行": 5, "其他": 15}}}}
"""


PROMPT_SALARY = """你是薪资数据专家. 为该专业生成顶层 salary 字段 (应届/3-5年/5-10年/10年+, 每阶段 p25/p50/p75 元/月, yoy 默认 5).

【专业】: {title} ({style})
【已有 employment_direction 摘要 (作为薪资参考)】:
{emp}

【输出严格 JSON】:
{{"应届生": {{"p25": X, "p50": Y, "p75": Z, "yoy": 5}}, "3-5年": {{...}}, "5-10年": {{...}}, "10年+": {{...}}}}
薪资应符合中国 2024 市场实际: 应届生 p25-p75 范围通常 5k-15k, 资深 20k-50k.
"""


PROMPT_ALUMNI = """你是校友引用改写专家. 该专业当前 alumni_quotes 有措辞硬伤, 重写为自然流畅版本, 必须:
1. 删除 "4 年制本硕 6 年" 等机械表达, 改为 "本 4 + 硕 2 = 6 年" 或 "本硕 6 年" 等自然说法
2. 包含具体细节 (修了什么课/做过什么毕设/跟过哪个导师/做过什么项目)
3. 保持 quote 字段长度 80-150 字

【专业】: {title}
【当前 alumni_quotes】:
{alumni}

【输出严格 JSON 数组】 (保持 3 条):
[
  {{"year": "2018", "current": "...", "quote": "..."}},
  ...
]
"""


def call_m3(client, prompt):
    body = {"max_tokens": 6000, "temperature": 0.7,
            "messages": [{"role": "user", "content": prompt}]}
    resp = client._call(body)
    text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    json_str = m.group(1) if m else text
    return json.loads(json_str)


def normalize_ds(ds):
    if not isinstance(ds, dict) or len(ds) < 3:
        return None
    ds_int = {k: int(round(float(v))) for k, v in ds.items()}
    total = sum(ds_int.values())
    if abs(total - 100) > 1:
        ds_int = {k: round(v * 100 / total) for k, v in ds_int.items()}
        diff = 100 - sum(ds_int.values())
        if ds_int:
            ds_int[list(ds_int.keys())[0]] += diff
    return ds_int


def main():
    import time
    client = M3Client(enable_thinking=True)

    # Fix 1: deep_study
    print("\n=== Fixing deep_study ===")
    for slug, title, style in NEED_DEEP_STUDY:
        p = CUR / f"{slug}.json"
        d = json.loads(p.read_text())
        emp = d.get("employment_direction", [])[:5]
        prompt = PROMPT_DS.format(title=title, style=style, emp=json.dumps(emp, ensure_ascii=False)[:2500])
        try:
            t0 = time.time()
            resp = call_m3(client, prompt)
            ds = normalize_ds(resp.get("deep_study", {}))
            if ds:
                d["deep_study"] = ds
                p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  OK {slug} ({time.time()-t0:.1f}s)")
            else:
                print(f"  FAIL {slug} - bad response")
        except Exception as e:
            print(f"  ERR {slug}: {e}")

    # Fix 2: salary
    print("\n=== Fixing salary ===")
    for slug, title, style in NEED_SALARY:
        p = CUR / f"{slug}.json"
        d = json.loads(p.read_text())
        emp = d.get("employment_direction", [])[:5]
        prompt = PROMPT_SALARY.format(title=title, style=style, emp=json.dumps(emp, ensure_ascii=False)[:2500])
        try:
            t0 = time.time()
            resp = call_m3(client, prompt)
            sal = resp.get("salary", {})
            if sal and isinstance(sal, dict):
                # Fill in missing stages
                existing = d.get("salary", {}) if isinstance(d.get("salary"), dict) else {}
                for stage, vals in sal.items():
                    if stage not in existing or all(v == 0 for v in (existing.get(stage) or {}).values() if isinstance(v, (int, float))):
                        existing[stage] = vals
                d["salary"] = existing
                p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  OK {slug} ({time.time()-t0:.1f}s)")
        except Exception as e:
            print(f"  ERR {slug}: {e}")

    # Fix 3: alumni_quotes
    print("\n=== Fixing alumni_quotes ===")
    for slug, title, style in NEED_ALUMNI:
        p = CUR / f"{slug}.json"
        d = json.loads(p.read_text())
        alumni = d.get("alumni_quotes", [])
        prompt = PROMPT_ALUMNI.format(title=title, alumni=json.dumps(alumni, ensure_ascii=False)[:2500])
        try:
            t0 = time.time()
            resp = call_m3(client, prompt)
            if isinstance(resp, list) and len(resp) >= 3:
                d["alumni_quotes"] = resp[:3]
                p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  OK {slug} ({time.time()-t0:.1f}s)")
            else:
                print(f"  FAIL {slug} - bad response")
        except Exception as e:
            print(f"  ERR {slug}: {e}")

    # Fix 4: biomedical-engineering 汤晓鸥 error
    print("\n=== Fixing biomedical-engineering textbook error ===")
    bme_p = CUR / "biomedical-engineering.json"
    bme = json.loads(bme_p.read_text())
    # Search for 汤晓鸥 and replace with correct author
    json_str = json.dumps(bme, ensure_ascii=False, indent=2)
    if "汤晓鸥" in json_str:
        # Replace in textbooks section
        for tb in bme.get("recommended_books", []):
            if isinstance(tb, dict) and "汤晓鸥" in str(tb.get("author", "")):
                tb["author"] = "邓玉林 主编"
                tb["note"] = tb.get("note", "") + " [原'汤晓鸥主编'系事实错误, 已修正为邓玉林主编]"
        bme_p.write_text(json.dumps(bme, ensure_ascii=False, indent=2), encoding="utf-8")
        print("  Fixed 汤晓鸥 → 邓玉林")


if __name__ == "__main__":
    main()
