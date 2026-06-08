"""
scripts/generate_sample_rank_gd_js.py — 生成广东/江苏 一分一段表 (基于公开真实分布锚点)

广东 2024 物理类锚点 (官方公开):
  700 ≈ 50
  600 ≈ 18000
  580 ≈ 33000
  525 (特控线) ≈ 80000
  400 ≈ 230000
  总数 ≈ 38万
广东 2024 历史类锚点 (2026-06-08 校准修正, 真实 eea.gd 投档表反查):
  原锚点 (官方发布粗略) → 校准后锚点 (median_log10=-0.31, 倍数 0.49)
  700 ≈ 10 → 5
  600 ≈ 4000 → 1960
  580 ≈ 10000 → 4900
  525 ≈ 40000 → 19600
  400 ≈ 180000 → 88200
  总数 ≈ 30万
  校准来源: data/_logs/rank_calibration_2024_guangdong.md (1432 真实样本)

江苏 2024 物理类 (2026-06-08 校准修正, sina 2024-06-25 官方发布锚点):
  原锚点 (估算) → 校准后 (8 个真实 anchor)
  700 ≈ 30 → 30
  680 ≈ 100 → 371
  660 ≈ 400 → 2475
  640 ≈ 1500 → 8014
  630 ≈ 5000 → 12125
  600 ≈ 16000 → 30768
  570 ≈ 58000 → 58417
  540 ≈ 65000 → 93432
  525 ≈ 80000 → 105000 (estimate)
  462 (本科线) ≈ 180000 → 187958
  400 ≈ 230000 → 230000
  总数 ≈ 32万
  校准来源: data/_logs/rank_calibration_2024.md (jiangsu 物理 段)

江苏 2024 历史类 (2026-06-08 校准修正, sina 2024-06-25 官方发布锚点):
  原锚点 (估算) → 校准后 (6 个真实 anchor)
  700 ≈ 5 → 5
  640 ≈ 200 → 327
  600 ≈ 2500 → 4028
  580 ≈ 8000 → 8377 (接近, 略调)
  560 ≈ 15000 → 14582
  530 ≈ 23000 → 26805
  525 ≈ 30000 → 28000 (estimate)
  500 ≈ 50000 → 38000 (estimate)
  478 (本科线) ≈ 150000 → 50966 (修后锚点, synth 原 150k 严重高估)
  450 ≈ 110000 → 60000
  400 ≈ 150000 → 80000
  300 ≈ 170000 → 110000
  总数 ≈ 11万 (原估算 18万 过高, 真实 11万左右)
  校准来源: data/_logs/rank_calibration_2024.md (jiangsu 历史 段)
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

    # 广东 历史 (校准后, 2026-06-08 eea.gd 反查, 倍数 0.49)
    gd_hist_anchors = [
        (700, 5), (680, 15), (660, 49), (640, 147), (620, 490),
        (600, 1960), (580, 4900), (560, 9800), (540, 14700), (525, 19600),
        (500, 34300), (480, 49000), (450, 68600), (400, 88200), (300, 112700),
        (200, 132300), (150, 147000),
    ]
    df = gen_rank(gd_hist_anchors, 300000)
    out = DATA_DIR / "guangdong_rank_历史_2024.csv"
    df.to_csv(out, index=False)
    print(f"📦 {out.name}: {len(df)} 行")

    # 江苏 物理 (校准后, 2026-06-08 sina 8 个真实 anchor)
    js_phys_anchors = [
        (700, 30), (680, 371), (660, 2475), (640, 8014), (630, 12125),
        (600, 30768), (580, 35000), (570, 58417), (540, 93432), (525, 105000),
        (500, 130000), (480, 165000), (462, 187958), (450, 195000), (400, 230000),
        (300, 280000), (200, 310000), (150, 320000),
    ]
    df = gen_rank(js_phys_anchors, 320000)
    out = DATA_DIR / "jiangsu_rank_物理_2024.csv"
    df.to_csv(out, index=False)
    print(f"📦 {out.name}: {len(df)} 行")

    # 江苏 历史 (校准后, 2026-06-08 sina 6 个真实 anchor, 478 本科线 150k→51k)
    js_hist_anchors = [
        (700, 5), (680, 25), (660, 100), (640, 327), (620, 1200),
        (600, 4028), (580, 8377), (560, 14582), (540, 21000), (530, 26805),
        (525, 28000), (500, 38000), (490, 44000), (478, 50966), (460, 56000),
        (450, 60000), (430, 67000), (400, 80000), (380, 88000), (360, 95000),
        (340, 100000), (300, 110000), (200, 120000), (150, 125000),
    ]
    df = gen_rank(js_hist_anchors, 125000)
    out = DATA_DIR / "jiangsu_rank_历史_2024.csv"
    df.to_csv(out, index=False)
    print(f"📦 {out.name}: {len(df)} 行")


if __name__ == "__main__":
    main()
