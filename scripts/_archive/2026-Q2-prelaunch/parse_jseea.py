"""
scripts/parse_jseea.py — 解析 江苏 2024 本科批 XLS (jseea.cn 官方)

输入: data/_cache/jseea_2024/js2024_{物理|历史}.xls
输出: data/jiangsu_admission_{物理|历史}_2024_real_jseea.csv

XLS schema (row 0-4 是标题/表头, row 5+ 是数据):
  col 0: 院校代号 (e.g. "1101")
  col 1: 院校、专业组（再选科目要求） (e.g. "南京大学03专业组(不限)")
  col 2: 投档最低分 (e.g. "638")
  col 3-8: 同分排序项 (语数成绩/语数最高/外语/首选/再选最高/志愿号)

min_rank: XLS 未直接给位次, 用 jiangsu_rank_{subject}_2024.csv 反查 score_to_rank.
"""
import re
import sys
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))
from merge_real_2024_gd_js import score_to_rank, load_rank_table  # noqa: E402

DATA_DIR = PROJECT_DIR / "data"
CACHE_DIR = DATA_DIR / "_cache" / "jseea_2024"

# 院校专业组解析: "南京大学03专业组(不限)" → (南京大学, 03, 不限)
#                "中国民用航空飞行学院01专业组(不限)" → 同样
_GROUP_RE = re.compile(r"^(.+?)(\d{2})专业组\(([^)]*)\)\s*$")


def parse_group_cell(cell: str) -> tuple[str, str, str] | None:
    """解析 col 1 单元格 → (school_name, group_id, xuanke_req). 失败返回 None."""
    if not isinstance(cell, str):
        return None
    m = _GROUP_RE.match(cell.strip())
    if not m:
        return None
    name, gid, xuanke = m.group(1).strip(), m.group(2), m.group(3).strip()
    # 防御: name 末位可能含 空格, 去掉
    name = re.sub(r"\s+", "", name)
    # xuanke 标准化: 限 "不限" / "化学" / "思想政治" / "地理" / "生物" 或组合 "化学,生物"
    if not xuanke or xuanke == "无":
        xuanke = "不限"
    return name, gid, xuanke


def parse_xls(xls_path: Path, subject: str) -> list[dict]:
    if not xls_path.exists():
        return []
    df = pd.read_excel(xls_path, header=None, skiprows=5)
    rank_df = load_rank_table(subject)
    rows, skipped = [], 0
    for _, r in df.iterrows():
        school_code = str(r.iloc[0]).strip() if pd.notna(r.iloc[0]) else ""
        cell = str(r.iloc[1]).strip() if pd.notna(r.iloc[1]) else ""
        score_val = r.iloc[2]
        # 过滤: 院校代号 4 位数字, 投档分是数字 (col dtype=float64 → "594.0")
        if not (school_code.isdigit() and len(school_code) == 4):
            skipped += 1
            continue
        try:
            score_int = int(round(float(score_val)))
        except (ValueError, TypeError):
            skipped += 1
            continue
        parsed = parse_group_cell(cell)
        if not parsed:
            skipped += 1
            continue
        name, gid, xuanke = parsed
        rows.append({
            "school_code": school_code,
            "school_name": name,
            "group_code": gid,
            "group_id": gid,
            "xuanke_req": xuanke,
            "plan_count": 30,  # XLS 未给
            "admitted": 0,     # XLS 未给
            "min_score": score_int,
            "min_rank": score_to_rank(score_int, rank_df),
            "year": 2024,
            "subject": subject,
            "is_special": "否",
        })
    if skipped:
        print(f"  ⚠️ {xls_path.name}: 跳过 {skipped} 行 (院校代号非 4 位/分数非数字/组名不匹配)")
    return rows


def main():
    summary = {}
    for subject, fname in [("物理", "js2024_physical.xls"), ("历史", "js2024_history.xls")]:
        xls = CACHE_DIR / fname
        rows = parse_xls(xls, subject)
        if not rows:
            print(f"⚠️ {xls} 缺失或无数据")
            continue
        # Dedup on (school_name, group_id)
        seen, deduped = set(), []
        for r in rows:
            k = (r["school_name"], r["group_id"])
            if k in seen:
                continue
            seen.add(k)
            deduped.append(r)
        df = pd.DataFrame(deduped)
        out = DATA_DIR / f"jiangsu_admission_{subject}_2024_real_jseea.csv"
        df.to_csv(out, index=False)
        n0 = len(rows)
        n1 = len(deduped)
        # 统计 min_rank=999999 (rank 表反查失败) 的行数
        n_missing_rank = int((df["min_rank"] == 999999).sum())
        print(f"📦 {out.name}: {n1} 行 (raw {n0} 去重 {n0 - n1}, 缺 rank {n_missing_rank})")
        summary[subject] = {"rows": n1, "missing_rank": n_missing_rank}
    return summary


if __name__ == "__main__":
    main()
