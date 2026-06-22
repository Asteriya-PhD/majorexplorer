"""
scripts/parse_gk100_hb_2025_phys_full.py — 解析 物理 全表 (OCR 后)

输入: data/_cache/gk100_hb_2025/hb2025_phys_part{0,1,2,3,4}.md (MinerU Flash OCR 输出)
输出: data/hubei_admission_物理_2025_real_gk100_full.csv

schema (OCR 后):
  <table>
    <tr><td>学校名</td><td>首选科目</td><td>专业组</td><td>2025分数</td></tr>
    <tr><td>武汉大学</td><td>物理</td><td>第08组</td><td>645</td></tr>
    ...

约 400 行 (5 chunk × ~99 + 6 footer).
无位次 (gk100 在 PNG 中没列), 用 hubei_rank_物理_2025.csv score_to_rank 反查.
"""
import re
import sys
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from core.rank_utils import score_to_rank  # noqa: E402

CACHE_DIR = PROJECT_DIR / "data" / "_cache" / "gk100_hb_2025"
DATA_DIR = PROJECT_DIR / "data"


def parse_chunk_md(md_path: Path) -> list[dict]:
    if not md_path.exists():
        return []
    md = md_path.read_text(encoding="utf-8", errors="replace")
    trs = re.findall(r"<tr[^>]*>(.*?)</tr>", md, re.DOTALL)
    rows = []
    for tr in trs:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)
        tds = [re.sub(r"<[^>]+>", "", t).strip() for t in tds]
        if len(tds) < 4:
            continue
        school, subj, group, score = tds[0], tds[1], tds[2], tds[3]
        if school == "学校名" or not score.isdigit():
            continue
        if subj != "物理":
            continue
        rows.append({
            "school_name": school,
            "group_code": group,  # "第05组" / "第07组(国家专项)" / "第09组(民族班)"
            "min_score": int(score),
        })
    return rows


def main():
    all_rows = []
    for i in range(5):
        rows = parse_chunk_md(CACHE_DIR / f"hb2025_phys_part{i}.md")
        all_rows.extend(rows)
        print(f"  chunk {i}: {len(rows)} 行")
    print(f"  raw 总: {len(all_rows)} 行")

    # Dedup on (school_name, group_code)
    seen, deduped = set(), []
    for r in all_rows:
        k = (r["school_name"], r["group_code"])
        if k in seen:
            continue
        seen.add(k)
        deduped.append(r)
    print(f"  去重后: {len(deduped)} 行")

    # 补字段 + 反查 min_rank
    df = pd.DataFrame(deduped)
    df["min_rank"] = df["min_score"].apply(
        lambda s: score_to_rank(int(s), "hubei", "物理", 2025)
    )
    df["subject"] = "物理"
    df["xuanke_req"] = "不限"
    df["is_special"] = "否"
    df["year"] = 2025
    df["plan_count"] = 0
    n_missing = int((df["min_rank"] == 999999).sum())
    print(f"  缺 rank (反查失败): {n_missing}")

    out = DATA_DIR / "hubei_admission_物理_2025_real_gk100_full.csv"
    df.to_csv(out, index=False)
    print(f"📦 {out.name}: {len(df)} 行")

    # 报告
    scores = df["min_score"]
    ranks = df["min_rank"]
    print(f"  📊 score range: {scores.min()}-{scores.max()}, median {scores.median():.0f}")
    print(f"  📊 rank range: {ranks.min()}-{ranks.max()}, median {ranks.median():.0f}")


if __name__ == "__main__":
    main()
