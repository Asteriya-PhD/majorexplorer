"""
scripts/fetch_dxsbb_6261.py — 解析 dxsbb 6261 表格 (2024 湖北 一本 100物理+40历史)

dxsbb 6261 页面: https://www.dxsbb.com/news/6261.html
- table0: 100 物理 一本 (985/211/重点一本)
- table1: 40 历史 一本 (985/211/重点一本)

Schema: 年份 | 省份 | 科类 | 批次 | 院校名称 | 专业组 | 投档线

位次需要从 一分一段表 反查 (score → rank)
"""
import re
import urllib.request
import json
from datetime import datetime
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
LOG_DIR = PROJECT_DIR / "data" / "_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}


def fetch_table_6261() -> list[dict]:
    """Fetch 6261 page and parse 2 tables (100 物理 + 40 历史)"""
    url = "https://www.dxsbb.com/news/6261.html"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        txt = r.read().decode('utf-8', errors='replace')
    tables = re.findall(r'<table[^>]*>(.*?)</table>', txt, re.DOTALL)
    out = []
    for t in tables:
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL)
        for r in rows[1:]:  # skip header
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r, re.DOTALL)
            cells_clean = [re.sub(r'<[^>]+>', ' ', c).strip() for c in cells]
            if len(cells_clean) < 7:
                continue
            year, prov, subj, batch, school, group_code, score = cells_clean[:7]
            try:
                score_int = int(score)
            except ValueError:
                continue
            # group_code like "A14109" -> "09" (last 2 digits)
            m = re.search(r'(\d+)$', group_code)
            g = m.group(1)[-2:].zfill(2) if m else group_code.zfill(2)
            out.append({
                "year": int(year),
                "subject": subj,
                "school_name": school,
                "group_id": g,
                "group_code": group_code,
                "min_score": score_int,
            })
    return out


def score_to_rank(score: int, rank_table: pd.DataFrame, subject: str) -> int:
    """Convert score to rank using 一分一段表"""
    df = rank_table.copy()
    # Normalize score column (may have '695-750' ranges)
    def parse_score(s):
        s = str(s).strip()
        if "-" in s:
            return int(s.split("-")[0])
        return int(s)
    df["score_int"] = df["score"].apply(parse_score)
    # Find the row where score is the highest <= input
    eligible = df[df["score_int"] <= score]
    if eligible.empty:
        return 999999  # below all
    row = eligible.loc[eligible["score_int"].idxmax()]
    return int(row["rank"])


def main():
    print("📥 抓 dxsbb 6261 表格 (2024 湖北 一本)...")
    rows = fetch_table_6261()
    print(f"  解析: {len(rows)} 行")

    # 加载 一分一段表 (用于 score→rank 反查)
    rank_phys = pd.read_csv(DATA_DIR / "hubei_rank_物理_2024.csv")
    rank_hist = pd.read_csv(DATA_DIR / "hubei_rank_历史_2024.csv")

    # 拆物理/历史
    df_phys = pd.DataFrame([r for r in rows if r["subject"] == "物理"])
    df_hist = pd.DataFrame([r for r in rows if r["subject"] == "历史"])

    for df, rank_df, subj in [(df_phys, rank_phys, "物理"), (df_hist, rank_hist, "历史")]:
        df["min_rank"] = df["min_score"].apply(lambda s: score_to_rank(s, rank_df, subj))
        print(f"  {subj}: {len(df)} 行, score range {df['min_score'].min()}-{df['min_score'].max()}")

    out_phys = DATA_DIR / "hubei_admission_物理_2024_real_dxsbb6261.csv"
    out_hist = DATA_DIR / "hubei_admission_历史_2024_real_dxsbb6261.csv"
    df_phys.to_csv(out_phys, index=False)
    df_hist.to_csv(out_hist, index=False)
    print(f"📦 {out_phys.name} + {out_hist.name}")


if __name__ == "__main__":
    main()
