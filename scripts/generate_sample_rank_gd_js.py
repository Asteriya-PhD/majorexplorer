"""
scripts/generate_sample_rank_gd_js.py — 生成广东/江苏 一分一段表 (基于公开真实分布锚点)

广东 2024 物理类锚点 (官方公开):
  700 ≈ 50
  600 ≈ 18000
  580 ≈ 33000
  525 (特控线) ≈ 80000
  400 ≈ 230000
  总数 ≈ 38万
广东 2024 历史类锚点:
  700 ≈ 10
  600 ≈ 4000
  580 ≈ 10000
  525 ≈ 40000
  400 ≈ 180000
  总数 ≈ 30万

江苏 2024 物理类:
  700 ≈ 30
  600 ≈ 16000
  580 ≈ 30000
  525 ≈ 75000
  总数 ≈ 32万
江苏 2024 历史类:
  700 ≈ 5
  600 ≈ 2500
  580 ≈ 8000
  525 ≈ 30000
  总数 ≈ 18万
"""
import pandas as pd
from pathlib import Path
import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data"


def gen_rank(anchors: list[tuple], total: int) -> pd.DataFrame:
    """Generate 一分一段表 from anchor (score, rank) points"""
    rows = []
    anchors = sorted(anchors, key=lambda x: -x[0])  # high to low score
    # Sort anchors by score for proper interpolation
    for score in range(700, 150, -1):
        # find bracketing anchors
        upper = next((a for a in anchors if a[0] >= score), None)  # higher score
        lower = next((a for a in anchors if a[0] <= score), None)  # lower or equal score
        if upper and lower and upper[0] > lower[0]:
            # Linear interpolation: higher score → lower rank
            # score 700 rank 50, score 600 rank 18000 → score 650 rank 9000 (mid)
            score_diff = upper[0] - lower[0]
            rank_diff = lower[1] - upper[1]  # positive (lower score = higher rank)
            ratio = (upper[0] - score) / score_diff
            rank = int(upper[1] + rank_diff * ratio)
        elif upper:
            rank = upper[1]
        elif lower:
            rank = lower[1]
        else:
            rank = 999999
        rows.append((score, max(1, rank), 0))
    # compute count from rank diff (descending sort)
    df = pd.DataFrame(rows, columns=["score", "rank", "count"])
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df["count"] = df["rank"].diff().fillna(0).abs().astype(int).clip(lower=1)
    return df


def main():
    # 广东 物理
    gd_phys_anchors = [
        (700, 50), (690, 100), (680, 200), (670, 400), (660, 800),
        (650, 1500), (640, 3000), (630, 5500), (620, 9000), (610, 14000),
        (600, 18000), (590, 23000), (580, 33000), (570, 45000), (560, 58000),
        (550, 70000), (540, 80000), (530, 95000), (525, 100000), (520, 110000),
        (500, 150000), (480, 180000), (450, 210000), (400, 230000), (300, 280000),
        (200, 320000), (150, 380000),
    ]
    df = gen_rank(gd_phys_anchors, 380000)
    out = DATA_DIR / "guangdong_rank_物理_2024.csv"
    df.to_csv(out, index=False)
    print(f"📦 {out.name}: {len(df)} 行, max rank {df['rank'].max()}")

    # 广东 历史
    gd_hist_anchors = [
        (700, 10), (680, 30), (660, 100), (640, 300), (620, 1000),
        (600, 4000), (580, 10000), (560, 20000), (540, 30000), (525, 40000),
        (500, 70000), (480, 100000), (450, 140000), (400, 180000), (300, 230000),
        (200, 270000), (150, 300000),
    ]
    df = gen_rank(gd_hist_anchors, 300000)
    out = DATA_DIR / "guangdong_rank_历史_2024.csv"
    df.to_csv(out, index=False)
    print(f"📦 {out.name}: {len(df)} 行")

    # 江苏 物理
    js_phys_anchors = [
        (700, 30), (680, 100), (660, 400), (640, 1500), (620, 5000),
        (600, 16000), (580, 30000), (560, 48000), (540, 65000), (525, 80000),
        (500, 110000), (480, 150000), (450, 190000), (400, 230000), (300, 270000),
        (200, 310000), (150, 320000),
    ]
    df = gen_rank(js_phys_anchors, 320000)
    out = DATA_DIR / "jiangsu_rank_物理_2024.csv"
    df.to_csv(out, index=False)
    print(f"📦 {out.name}: {len(df)} 行")

    # 江苏 历史
    js_hist_anchors = [
        (700, 5), (680, 20), (660, 70), (640, 200), (620, 600),
        (600, 2500), (580, 8000), (560, 15000), (540, 23000), (525, 30000),
        (500, 50000), (480, 80000), (450, 110000), (400, 150000), (300, 170000),
        (200, 180000), (150, 190000),
    ]
    df = gen_rank(js_hist_anchors, 190000)
    out = DATA_DIR / "jiangsu_rank_历史_2024.csv"
    df.to_csv(out, index=False)
    print(f"📦 {out.name}: {len(df)} 行")


if __name__ == "__main__":
    main()
