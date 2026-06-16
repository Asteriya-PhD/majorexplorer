"""schema_fix_v4.py — Day 3 Team A schema 修复 (curriculum list[str] → list[dict])
- v4_medicine.py 期望 curriculum[k] = list of dict {name: "..."}
- m3 synth 输出 curriculum[k] = list of str "..."
- 还可能 top_companies 是 list of dict {name, type, note} vs str list
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
CUR = ROOT / "skills/gaokao-major-explorer/data/curated"

# 17 篇已知 schema 不匹配的 (从 render_batch 失败清单)
RENDER_FAILED = [
    "anesthesiology", "audiology-speech-rehabilitation", "basic-medicine",
    "biomedical-engineering", "clinical-engineering-technology", "clinical-medicine",
    "food-hygiene-nutrition", "forensic-medicine", "intelligent-construction",
    "intelligent-medical-engineering", "medical-imaging", "ophthalmology-optometry",
    "preventive-medicine", "psychiatry", "stomatology", "tcm-rehabilitation",
    "virtual-reality-technology",
]


def fix_curriculum(d):
    """把 curriculum[k] 从 list[str] 转 list[dict{name: str}]"""
    cur = d.get("curriculum", {})
    if not isinstance(cur, dict):
        return 0
    fixed = 0
    for k, v in list(cur.items()):
        if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
            cur[k] = [{"name": x} for x in v]
            fixed += 1
    return fixed


def fix_top_companies(d):
    """m3 输出 top_companies 已经是 list of dict, 但 v4 期望 dict {name: type}"""
    # 实际 v4_medicine.py 用 c.get("name", "") 所以 dict 列表已经 OK
    # 唯一问题是 str list (Day 1+2 旧版式), m3 都返 dict,无需修
    return 0


def fix_top_schools(d):
    """m3 输出 top_schools 是 list of dict {highlights, name, ranking_label, slug}
    v4 期望 {name, rank, tag},但 v4_medicine 用 s.get("name","") s.get("rank","") s.get("tag","")
    所以缺字段会显示空 — 不致命但难看,补默认"""
    if not isinstance(d.get("top_schools"), list):
        return 0
    fixed = 0
    # 处理 str list (如 "北京大学 (全国第一)")
    if d["top_schools"] and isinstance(d["top_schools"][0], str):
        new_list = []
        for s in d["top_schools"]:
            # 拆 "校名 (描述)" 成 {"name": "校名", "tag": "描述"}
            if "(" in s and ")" in s:
                name = s.split("(")[0].strip()
                tag = s.split("(", 1)[1].rstrip(")")
                new_list.append({"name": name, "rank": "★★★★☆", "tag": tag})
            else:
                new_list.append({"name": s, "rank": "★★★★☆", "tag": ""})
            fixed += 1
        d["top_schools"] = new_list
        return fixed
    for s in d["top_schools"]:
        if isinstance(s, dict):
            if "rank" not in s:
                s["rank"] = "★★★★☆"
                fixed += 1
            if "tag" not in s:
                s["tag"] = s.get("ranking_label", "") or s.get("highlights", "")[:80]
                fixed += 1
    return fixed


def fix_top_companies(d):
    """m3 输出 top_companies 可能是 list of str (Day 1+2 旧格式) 或 list of dict
    v4 期望 list of dict {name, ...}"""
    tc = d.get("top_companies")
    if not isinstance(tc, list) or not tc:
        return 0
    if isinstance(tc[0], str):
        # str list → dict list
        d["top_companies"] = [
            {"name": s, "tier": "B", "headcount": "", "salary": "", "sparkline": []}
            for s in tc
        ]
        return len(tc)
    # dict list 但缺字段
    fixed = 0
    for co in tc:
        if isinstance(co, dict):
            for k in ("tier", "headcount", "salary", "sparkline"):
                if k not in co:
                    co[k] = "" if k != "sparkline" else []
                    fixed += 1
    return fixed


def fix_alumni_quotes(d):
    """m3 输出 alumni_quotes 用 profile/school/(数据待补), v4 期望 year/current/source
    profile 类似 current (职位),school 类似 source,把 profile → current, school → source"""
    if not isinstance(d.get("alumni_quotes"), list):
        return 0
    fixed = 0
    for q in d["alumni_quotes"]:
        if isinstance(q, dict):
            if "profile" in q and "current" not in q:
                q["current"] = q.pop("profile")
                fixed += 1
            if "school" in q and "source" not in q:
                q["source"] = q.pop("school")
                fixed += 1
            if "year" not in q:
                q["year"] = ""
                fixed += 1
    return fixed


def fix_deep_study(d):
    """m3 输出 deep_study 可能是 list[str] (方向) 或 dict {research_directions, employment_directions, ...}
    v4 期望 dict {name: pct}"""
    ds = d.get("deep_study")
    if isinstance(ds, str):
        # m3 长字符串: 按段落或句子切, 每段作为 1 条
        # 用句号/分号/换行切
        import re
        sentences = re.split(r"[。;；\n]", ds)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 4]
        # 取前 8 段
        items = sentences[:8]
        d["deep_study"] = {f"路径 {i+1}: {s[:40]}": 0 for i, s in enumerate(items)}
        return 1
    if isinstance(ds, list):
        # m3 简化格式: 方向列表
        d["deep_study"] = {x: 0 for x in ds if isinstance(x, str)}
        return 1
    if isinstance(ds, dict):
        # m3 完整格式: {research_directions: [...], employment_directions: [...], ...}
        # 提取 research_directions 或 employment_directions 转 {name: 0}
        new_ds = {}
        for src_key in ("research_directions", "employment_directions", "master", "phd", "directions",
                        "海外路径", "考研方向", "postgrad_dir", "study_path"):
            if src_key in ds and isinstance(ds[src_key], list):
                items = [x for x in ds[src_key] if isinstance(x, str)]
                if items:
                    # 截短 name, 加 stage 前缀
                    for i, item in enumerate(items[:6]):
                        new_ds[f"{src_key} {i+1}: {item[:40]}"] = 0
        if new_ds:
            d["deep_study"] = new_ds
            return 1
        # 已 dict 但 value 全是 dict {p25,...} — 已是 v4 格式
        if any(isinstance(v, dict) and ("p25" in v or "p50" in v) for v in ds.values()):
            return 0
        # dict 但 value 是 int (旧 v4 格式 {name: pct}) — OK
        if all(isinstance(v, (int, float)) for v in ds.values()):
            return 0
        # dict 但 value 是 str — 转 {str: 0}
        if all(isinstance(v, str) for v in ds.values()):
            d["deep_study"] = {k: 0 for k in ds}
            return 1
        return 0
    return 0


def fix_salary(d):
    """m3 输出 salary 是 {currency, note, regions: {item: [...]}} 嵌套
    或旧 {entry_monthly_cny, year3_monthly_cny, ...} 扁平
    v4 期望 {stage_name: {p25, p50, p75, yoy}}"""
    sal = d.get("salary")
    if not isinstance(sal, dict):
        return 0
    # 先清掉残留 _note (上次 fix 加在 salary 里导致 .get 失败)
    if "_note" in sal:
        d["_salary_note"] = sal.pop("_note")
        return 1  # 算改了一次
    # 已有 v4 格式 (p25/p50/p75) — 确认没有 str vals
    if any(isinstance(v, dict) and "p50" in v for v in sal.values()):
        return 0  # 已经 OK
    # m3 嵌套格式
    if "regions" in sal and isinstance(sal["regions"], dict) and "item" in sal["regions"]:
        items = sal["regions"]["item"]
        if not items:
            return 0
        # items[0] = 一线城市数据, 取中位数
        new_salary = {}
        # 简化: 用 4 阶段 (entry / 3y / 5y / 10y+), 用一线城市数据生成
        first = items[0] if isinstance(items[0], dict) else {}
        # entry_resident_规培
        for stage, key in [("应届生", "entry_resident"), ("3-5年", "attending"), ("5-10年", "associate_chief"), ("10年+", "professor")]:
            val = None
            for k, v in first.items():
                if key in k.lower():
                    val = v
                    break
            if val:
                # 从 "约 8000-15000 元/月" 提取数字
                import re
                nums = re.findall(r"\d+", str(val))
                if len(nums) >= 2:
                    lo, hi = int(nums[0]), int(nums[1])
                    p25, p50, p75 = lo, (lo + hi) // 2, hi
                    new_salary[stage] = {"p25": p25, "p50": p50, "p75": p75, "yoy": 0}
        if new_salary:
            d["salary"] = new_salary
            return 1
    # 通用适配: 扫所有非 note key,把 "8-12 万/年" 或 "8000-12000 元/月" 转 {p25, p50, p75, yoy}
    import re
    def parse(s):
        s = str(s)
        if "万" in s and "年" in s:
            nums = re.findall(r"[\d.]+", s)
            if len(nums) >= 2:
                return int(float(nums[0]) * 10000 / 12), int(float(nums[1]) * 10000 / 12)
        nums = re.findall(r"\d+", s)
        if len(nums) >= 2:
            return int(nums[0]), int(nums[1])
        elif len(nums) == 1:
            v = int(nums[0])
            return v, v
        return 0, 0
    # 优先识别标准 key, 否则按出现顺序映射到 4 阶段
    STANDARD_KEYS = {
        "应届生": ["entry", "entry_monthly_cny", "entry_3y_cn_yuan", "avg_entry", "应届生 (一线)", "应届生"],
        "3-5年": ["year_3", "3y", "year3_monthly_cny", "mid_3_5y_cn_yuan", "avg_5y", "mid_5to10y_cn_yuan", "3-5年"],
        "5-10年": ["year_5", "5y", "year5_monthly_cny", "mid_5_10y_cn_yuan", "mid_5to10y_cn_yuan", "avg_5y", "5-10年"],
        "10年+": ["year_10", "10y", "senior_monthly_cny", "senior_10y_plus_cn_yuan", "top_percentile", "10年+", "10年+ (持证/资深)"],
    }
    new_salary = {}
    for stage, keys in STANDARD_KEYS.items():
        for k in keys:
            if k in sal and isinstance(sal[k], str):
                lo, hi = parse(sal[k])
                if lo > 0 or hi > 0:
                    new_salary[stage] = {"p25": lo, "p50": (lo + hi) // 2, "p75": hi, "yoy": 0}
                    break
    # 兜底: 把所有未识别的 stage 字符串 key 按出现顺序映射到 4 阶段
    used_keys = set()
    for keys in STANDARD_KEYS.values():
        used_keys.update(keys)
    leftover_keys = [k for k in sal.keys() if k not in used_keys and isinstance(sal[k], str) and any(c.isdigit() for c in sal[k])]
    fallback_stages = ["应届生", "3-5年", "5-10年", "10年+"]
    for i, k in enumerate(leftover_keys[:4]):
        if fallback_stages[i] not in new_salary:
            lo, hi = parse(sal[k])
            new_salary[fallback_stages[i]] = {"p25": lo, "p50": (lo + hi) // 2, "p75": hi, "yoy": 0}
    if new_salary:
        # 保留原 note (放顶层,避免 salary.items() 循环 .get 失败)
        if "note" in sal:
            d["_salary_note"] = sal["note"]
        d["salary"] = new_salary
        return 1
    return 0


def fix_xuanke(d):
    """xuanke_req_list 可能是 list[str] 或 list[dict]
    v4 期望 list[dict] {name, pct, level}"""
    xu = d.get("xuanke_req_list")
    if isinstance(xu, list) and xu and isinstance(xu[0], str):
        new = []
        for x in xu:
            # "物理 (必选, 工科通用)" → {name: "物理", level: "必选", pct: 50}
            import re
            m = re.match(r"^([^()]+)", x)
            name = m.group(1).strip().split("+")[0].strip() if m else x[:20]
            new.append({"name": name, "level": "必选", "pct": 50})
        d["xuanke_req_list"] = new
        return len(new)
    return 0


def fix_one(slug):
    p = CUR / f"{slug}.json"
    if not p.exists():
        return f"NO FILE: {slug}"
    d = json.loads(p.read_text())
    fc = fix_curriculum(d)
    fs = fix_top_schools(d)
    ftc = fix_top_companies(d)
    fa = fix_alumni_quotes(d)
    fds = fix_deep_study(d)
    fsal = fix_salary(d)
    fxu = fix_xuanke(d)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"✅ {slug} (cur={fc}, sch={fs}, co={ftc}, al={fa}, ds={fds}, sal={fsal}, xu={fxu})"


if __name__ == "__main__":
    for s in RENDER_FAILED:
        print(fix_one(s))