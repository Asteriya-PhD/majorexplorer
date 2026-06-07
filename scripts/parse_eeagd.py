"""
scripts/parse_eeagd.py — 解析 广东 2024 PDF (eea.gd.gov.cn via huaue 镜像)

输入: data/_cache/eeagd_2024/gd2024_{历史|物理}.md
输出: data/guangdong_admission_{历史|物理}_2024_real_eeagd.csv

格式 (MinerU 解析后的 HTML 表格):
  <tr>
    <td>10001</td>     院校代码
    <td>北京大学</td>  院校名称
    <td>201</td>       专业组代码
    <td>24</td>        计划数
    <td>24</td>        投档人数
    <td>662</td>       投档最低分
    <td>32</td>        投档最低排位
  </tr>
"""
import re
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
CACHE_DIR = DATA_DIR / "_cache" / "eeagd_2024"


def parse_row(tr: str) -> dict | None:
    """解析单个 <tr> → dict."""
    tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)
    if len(tds) < 7:
        return None
    cells = [re.sub(r"<[^>]+>", " ", t).strip() for t in tds]
    school_code = cells[0]
    school_name = cells[1]
    group_code = cells[2]  # e.g. "201" or "W201" or "201-1"
    plan_count = cells[3]
    admitted = cells[4]
    score = cells[5]
    rank = cells[6]
    # 跳过表头
    if not school_code.isdigit() or len(school_code) != 5:
        return None
    if not score.isdigit():
        return None
    if not rank.isdigit():
        return None
    # group_id 取 group_code 最后 2 位
    g_num = re.sub(r"[^\d]", "", group_code)
    group_id = g_num[-2:].zfill(2) if g_num else "01"
    return {
        "school_code": school_code,
        "school_name": school_name,
        "group_code": group_code,
        "group_id": group_id,
        "plan_count": int(plan_count) if plan_count.isdigit() else 30,
        "admitted": int(admitted) if admitted.isdigit() else 0,
        "min_score": int(score),
        "min_rank": int(rank),
    }


def parse_md(md_path: Path, subject: str, year: int = 2024) -> list[dict]:
    if not md_path.exists():
        return []
    raw = md_path.read_text(encoding="utf-8", errors="replace")
    trs = re.findall(r"<tr[^>]*>(.*?)</tr>", raw, re.DOTALL)
    rows = []
    skipped = 0
    for tr in trs:
        rec = parse_row(tr)
        if rec:
            rec["year"] = year
            rec["subject"] = subject
            rec["xuanke_req"] = "不限"  # 该 PDF 未直接给选科, 后续可从其他源补
            rec["is_special"] = "否"   # PDF 未给备注
            rows.append(rec)
        else:
            skipped += 1
    if skipped:
        print(f"  ⚠️ {md_path.name}: 跳过 {skipped} 行 (非数据行)")
    return rows


def main():
    summary = {}
    for subject, fname in [("物理", "gd2024_物理.md"), ("历史", "gd2024_历史.md")]:
        md = CACHE_DIR / fname
        rows = parse_md(md, subject)
        if not rows:
            print(f"⚠️ {md} 缺失或无数据")
            continue
        # Dedup on (school_name, group_code)
        seen = set()
        deduped = []
        for r in rows:
            k = (r["school_name"], r["group_code"])
            if k in seen:
                continue
            seen.add(k)
            deduped.append(r)
        df = pd.DataFrame(deduped)
        out = DATA_DIR / f"guangdong_admission_{subject}_2024_real_eeagd.csv"
        df.to_csv(out, index=False)
        print(f"📦 {out.name}: {len(df)} 行 (raw {len(rows)} 去重 {len(rows) - len(deduped)})")
        summary[subject] = len(df)
    return summary


if __name__ == "__main__":
    main()
