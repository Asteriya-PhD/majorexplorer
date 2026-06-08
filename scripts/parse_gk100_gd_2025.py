"""
scripts/parse_gk100_gd_2025.py — 解析 广东 2025 本科批 投档线 (OCR 后)

输入: data/_cache/gk100_gd_2025/{e41ae71b4b77b4e1,e23307f0ba23a6df,7044fd76eda4768e}_part*.md
       (MinerU Flash OCR 输出)
输出: data/guangdong_admission_{物理|历史}_2025_real_gk100.csv

源数据 (gk100 read_32927314.htm):
- 物理: 2 PNG 拼接 (e41ae71b4b77b4e1 顶部 + e23307f0ba23a6df 底部)
- 历史: 1 PNG (7044fd76eda4768e)

OCR schema:
  <tr>
    <td>学校名</td>
    <td>专业组</td>
    <td>2025分数</td>
    <td>2025位次</td>
  </tr>

学校名 可能含括号 (e.g. "中山大学（216组）" 拆成 校名 + 组号, 但 OCR 拆开)
实际 schema (gk100):
  学校名 | 专业组 | 2025分数 | 2025位次

位次: 直接给 (e.g. 3575, 1730), 不需 score_to_rank 反查.
"""
import re
import sys
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
CACHE_DIR = PROJECT_DIR / "data" / "_cache" / "gk100_gd_2025"
DATA_DIR = PROJECT_DIR / "data"

# 物理 PNGs (顶部 + 底部), 历史 1 个
PHYS_STEMS = ["e41ae71b4b77b4e1", "e23307f0ba23a6df"]
HIST_STEM = "7044fd76eda4768e"


def parse_chunk_md(md_path: Path) -> list[dict]:
    if not md_path.exists():
        return []
    md = md_path.read_text(encoding="utf-8", errors="replace")
    trs = re.findall(r"<tr[^>]*>(.*?)</tr>", md, re.DOTALL)
    rows = []
    for tr in trs:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)
        tds = [re.sub(r"<[^>]+>", "", t).strip() for t in tds]
        # GD 2025 schema: 学校名 | 首选科目 | 专业组 | 2025分数 | 2025位次 (5 列)
        if len(tds) < 5 or tds[0] in ("学校名", ""):
            continue
        school, group, score, rank = tds[0], tds[2], tds[3], tds[4]
        if not (score.isdigit() and rank.isdigit()):
            continue
        rows.append({
            "school_name": school,
            "group_code": group,  # e.g. "221组" / "201组(内地香港合作办学)"
            "min_score": int(score),
            "min_rank": int(rank),
        })
    return rows


def parse_subject(stems: list[str], subject: str) -> pd.DataFrame:
    """合并多个 stem 的所有 chunk, dedup, 输出 DataFrame."""
    all_rows = []
    for stem in stems:
        chunks = sorted(CACHE_DIR.glob(f"{stem}_part*.md"))
        for c in chunks:
            rows = parse_chunk_md(c)
            all_rows.extend(rows)
            print(f"  {c.name}: {len(rows)} 行")
    print(f"  raw 总 ({subject}): {len(all_rows)} 行")
    # Dedup on (school, group)
    seen, deduped = set(), []
    for r in all_rows:
        k = (r["school_name"], r["group_code"])
        if k in seen:
            continue
        seen.add(k)
        deduped.append(r)
    print(f"  去重 ({subject}): {len(deduped)} 行")
    df = pd.DataFrame(deduped)
    df["subject"] = subject
    df["xuanke_req"] = "不限"
    df["is_special"] = "否"
    df["year"] = 2025
    df["plan_count"] = 0
    return df


def main():
    # 物理
    df_phys = parse_subject(PHYS_STEMS, "物理")
    if not df_phys.empty:
        out = DATA_DIR / "guangdong_admission_物理_2025_real_gk100.csv"
        df_phys.to_csv(out, index=False)
        print(f"\n📦 {out.name}: {len(df_phys)} 行")
        print(f"  📊 score range: {df_phys['min_score'].min()}-{df_phys['min_score'].max()}, "
              f"median {df_phys['min_score'].median():.0f}")
        print(f"  📊 rank range: {df_phys['min_rank'].min()}-{df_phys['min_rank'].max()}, "
              f"median {df_phys['min_rank'].median():.0f}")

    # 历史
    df_hist = parse_subject([HIST_STEM], "历史")
    if not df_hist.empty:
        out = DATA_DIR / "guangdong_admission_历史_2025_real_gk100.csv"
        df_hist.to_csv(out, index=False)
        print(f"\n📦 {out.name}: {len(df_hist)} 行")
        print(f"  📊 score range: {df_hist['min_score'].min()}-{df_hist['min_score'].max()}, "
              f"median {df_hist['min_score'].median():.0f}")
        print(f"  📊 rank range: {df_hist['min_rank'].min()}-{df_hist['min_rank'].max()}, "
              f"median {df_hist['min_rank'].median():.0f}")


if __name__ == "__main__":
    main()
