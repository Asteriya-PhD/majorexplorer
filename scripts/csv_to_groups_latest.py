"""
scripts/csv_to_groups_latest.py — 广东/江苏 admission CSV → groups_latest JSON

输入: data/{province}_admission_{物理|历史}_2024.csv
输出: data/groups_latest_{province}_2024.json
       schema: {wuli: [...], lishi: [...]}, 每条统一字段 (跟湖北一致 + 新增 province/year/subject/plan_count/city/sg_code/xuanke_subjects_raw)

关键转换:
- 广东 xuanke_subjects: "化学" → 首选物理，再选化学 (单科)
                "不限" → 首选物理，不限 (再选空)
- 江苏 xuanke_subjects: "物理|化学" → 首选物理，再选物理和化学 (split |)
                          "化学" → 首选物理，再选化学
- sg_name: 沿用原 group_code 广东 "207" / 江苏 group_id "02" (3 位零填充)

用法:
  python3 scripts/csv_to_groups_latest.py --province guangdong --year 2024
  python3 scripts/csv_to_groups_latest.py --province jiangsu --year 2024
"""
import argparse
import csv
import json
from pathlib import Path
from statistics import median

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"

PROVINCE_CN = {"guangdong": "广东", "jiangsu": "江苏", "hubei": "湖北"}


def build_name_index() -> dict:
    """Load colleges.json → {school_name: chsi_edu_id}."""
    with open(DATA_DIR / "colleges.json", "r", encoding="utf-8") as f:
        colleges = json.load(f)
    idx = {}
    for c in colleges:
        idx[c["name"]] = c.get("school_id") or c.get("chsi_edu_id")
    return idx


def build_sg_info(subject_cn: str, xuanke_req: str, xuanke_subjects: str) -> str:
    """
    转 sg_info 为湖北格式: "首选物理，再选X"
    subject_cn: "物理" 或 "历史"
    xuanke_req: "不限" / "指定" / "化学" 等
    xuanke_subjects: "物理|化学" (江苏) / "化学" (广东) / "不限" (广东)
    """
    first = subject_cn  # "物理" or "历史"
    if xuanke_req == "不限" or xuanke_subjects in ("不限", ""):
        return f"首选{first}，再选不限"

    # 再选科目解析
    if "|" in xuanke_subjects:
        # 江苏格式: split("|") 用"和"连接
        parts = [p.strip() for p in xuanke_subjects.split("|") if p.strip()]
        return f"首选{first}，再选" + "和".join(parts)
    elif xuanke_subjects and xuanke_subjects != "不限":
        # 广东/江苏单科格式
        return f"首选{first}，再选{xuanke_subjects}"
    else:
        return f"首选{first}，再选不限"


def csv_to_groups(province: str, year: int, subject_cn: str, name_idx: dict) -> list:
    """读 admission CSV → 一组 group dict."""
    csv_path = DATA_DIR / f"{province}_admission_{subject_cn}_{year}.csv"
    out = []
    skip_no_school = 0
    skip_no_data = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                min_score = int(r.get("min_score") or 0)
                min_rank = int(r.get("min_rank") or 0)
                plan_count = int(r.get("plan_count") or 0)
            except (ValueError, TypeError):
                continue

            # filter: min_score/rank 必须有有效值 (gk100 top100 没计划数但有分数)
            if min_score <= 0 or min_rank <= 0:
                skip_no_data += 1
                continue

            school_name = r["school_name"].strip()
            school_id = name_idx.get(school_name)
            if not school_id:
                skip_no_school += 1
                continue

            xuanke_req = r.get("xuanke_req", "不限").strip()
            xuanke_subjects = r.get("xuanke_subjects", "").strip()
            group_code = r.get("group_code", r.get("group_id", "")).strip()
            sg_info = build_sg_info(subject_cn, xuanke_req, xuanke_subjects)

            out.append({
                "school_id": int(school_id) if str(school_id).isdigit() else school_id,
                "school_name": school_name,
                "sg_name": f"（{group_code.zfill(3) if group_code else '000'}）",
                "sg_code": group_code,
                "sg_info": sg_info,
                "xuanke_subjects_raw": xuanke_subjects,
                "special_group_id": "",  # 广东/江苏暂无
                "batch_name": "本科批",
                "min_score": min_score,
                "min_rank": min_rank,
                "plan_count": plan_count,
                "year": year,
                "subject": subject_cn,
                "city": r.get("city", "").strip() or "",
                "is_special": r.get("is_special", "否").strip() == "是",
                "province": province,
            })
    print(f"  [{province}/{subject_cn}/{year}] kept {len(out)}, skip_no_school={skip_no_school}, skip_no_data={skip_no_data}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--province", required=True, choices=["guangdong", "jiangsu"])
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()

    prov_cn = PROVINCE_CN[args.province]
    print(f"Building {prov_cn} {args.year} groups_latest...")
    name_idx = build_name_index()
    print(f"  name index: {len(name_idx)} schools")

    wuli = csv_to_groups(args.province, args.year, "物理", name_idx)
    lishi = csv_to_groups(args.province, args.year, "历史", name_idx)

    doc = {"wuli": wuli, "lishi": lishi}
    out_path = DATA_DIR / f"groups_latest_{args.province}_{args.year}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    print(f"✅ Wrote {out_path}: wuli={len(wuli)}, lishi={len(lishi)}")


if __name__ == "__main__":
    main()