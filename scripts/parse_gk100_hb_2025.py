"""
scripts/parse_gk100_hb_2025.py — 解析 高考100 湖北 2025 本科批 投档线

输入: data/_cache/gk100_hb_2025/{read_1998271|read_29807851}.html
输出: data/hubei_admission_{物理|历史}_2025_real_gk100.csv
       (追加, 不替换, 保留 synth 数据 — 用 data_source 区分)

源数据 (gk100.com):
- read_1998271.htm: 2025 湖北 各高校 投档线一览表
  - 一、历史类 (180 行, schema: 学校/科目/专业组/分数, 无位次)
  - 二、物理类 (PNG 图片, 不可解析, 走 29807851 补)
- read_29807851.htm: 2025 湖北 物理 TOP100 (204 行, schema: 学校/专业组/分数/位次)

位次: 历史无, 用 hubei_rank_历史_2025.csv 反查 score_to_rank. 物理含, 直接用.
"""
import sys
import re
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from core.rank_utils import score_to_rank  # noqa: E402

CACHE_DIR = PROJECT_DIR / "data" / "_cache" / "gk100_hb_2025"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = PROJECT_DIR / "data"


def parse_history_table(html_path: Path) -> list[dict]:
    """读 read_1998271.htm 拆 2 个 table (历史在前 180 行, 物理是 PNG 跳过)."""
    if not html_path.exists():
        return []
    html = html_path.read_text(encoding="utf-8", errors="replace")
    # 取 H2 一、..二、.. 之间
    h2_start = html.find("一、2025湖北各高校历史类")
    h2_end = html.find("二、2025湖北各高校物理类")
    if h2_start < 0 or h2_end < 0:
        return []
    seg = html[h2_start:h2_end]
    trs = re.findall(r"<tr[^>]*>(.*?)</tr>", seg, re.DOTALL)
    rows = []
    for tr in trs:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)
        tds = [re.sub(r"<[^>]+>", "", t).strip() for t in tds]
        if len(tds) < 4 or tds[0] == "学校名":
            continue
        school, subj, group, score = tds[0], tds[1], tds[2], tds[3]
        if not score.isdigit():
            continue
        rows.append({
            "school_name": school,
            "group_code": group,  # e.g. "第05组" or "第07组(国家专项)"
            "min_score": int(score),
            "min_rank": 0,  # 历史页无位次, 后续由 merge 用 score_to_rank 补
            "subject": "历史",
        })
    return rows


def parse_phys_top100(html_path: Path) -> list[dict]:
    """读 read_29807851.htm 物理 TOP100 (含位次)."""
    if not html_path.exists():
        return []
    html = html_path.read_text(encoding="utf-8", errors="replace")
    trs = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)
    rows = []
    for tr in trs:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)
        tds = [re.sub(r"<[^>]+>", "", t).strip() for t in tds]
        if len(tds) < 4 or tds[0] in ("学校名", ""):
            continue
        school, group, score, rank = tds[0], tds[1], tds[2], tds[3]
        if not (score.isdigit() and rank.isdigit()):
            continue
        rows.append({
            "school_name": school,
            "group_code": group,
            "min_score": int(score),
            "min_rank": int(rank),
            "subject": "物理",
        })
    return rows


def main():
    # 物理 TOP100
    phys_rows = parse_phys_top100(CACHE_DIR / "read_29807851.html")
    if phys_rows:
        df_phys = pd.DataFrame(phys_rows)
        df_phys["xuanke_req"] = "不限"  # TOP100 无选科信息
        df_phys["is_special"] = "否"
        df_phys["year"] = 2025
        df_phys["plan_count"] = 0
        out = DATA_DIR / "hubei_admission_物理_2025_real_gk100.csv"
        df_phys.to_csv(out, index=False)
        n_missing_rank = int((df_phys["min_rank"] == 0).sum())
        print(f"📦 {out.name}: {len(df_phys)} 行 (TOP100, 缺位次 {n_missing_rank})")
    else:
        print(f"⚠️ 物理源缺失, 期望 {CACHE_DIR / 'read_29807851.html'}")

    # 历史 180 行 (无位次)
    hist_rows = parse_history_table(CACHE_DIR / "read_1998271.html")
    if hist_rows:
        df_hist = pd.DataFrame(hist_rows)
        df_hist["xuanke_req"] = "不限"
        df_hist["is_special"] = "否"
        df_hist["year"] = 2025
        df_hist["plan_count"] = 0
        # 用 score_to_rank 反查 位次
        df_hist["min_rank"] = df_hist["min_score"].apply(
            lambda s: score_to_rank(int(s), "hubei", "历史", 2025)
        )
        out = DATA_DIR / "hubei_admission_历史_2025_real_gk100.csv"
        df_hist.to_csv(out, index=False)
        n_missing = int((df_hist["min_rank"] == 999999).sum())
        print(f"📦 {out.name}: {len(df_hist)} 行 (无位次, 反查 {n_missing} 缺)")
    else:
        print(f"⚠️ 历史源缺失, 期望 {CACHE_DIR / 'read_1998271.html'}")


if __name__ == "__main__":
    main()
