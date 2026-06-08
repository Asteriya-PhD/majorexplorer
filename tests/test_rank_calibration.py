"""
tests/test_rank_calibration.py — rank 表校准回归测试

防 合成 rank 表 vs 真实一分一段 系统性偏差.
GD 历史 2026-06-08 发现 -51% 偏, JS 物理 1.9-6.2x 偏, JS 历史 478 本科线 0.52x 偏,
修锚点后归零.

数据:
- GD 真实: data/guangdong_admission_{物理|历史}_2024_real_eeagd.csv
- JS 真实: sina 2024-06-25 发布 8 物理 / 6 历史 anchor
  (http://www.zgjssw.gov.cn/yaowen/202406/t20240625_8347277.shtml)
- 合成: data/{province}_rank_{物理|历史}_2024.csv (score_to_rank)

阈值: anchor 点 log_ratio 全部 ≤ ±0.05 (gen_rank 线性插值, anchor 点应 0 偏差).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.rank_utils import score_to_rank  # noqa: E402

DATA_DIR = Path(__file__).parent.parent / "data"
TOLERANCE = 0.05  # log_ratio 阈值 (10^x = 0.89 ~ 1.12x)


@pytest.mark.parametrize("subject", ["物理", "历史"])
def test_guangdong_rank_calibration(subject: str):
    """广东 2024 rank 表校准: 真实投档位次 vs 合成表偏差 ≤ 5% log."""
    src = DATA_DIR / f"guangdong_admission_{subject}_2024_real_eeagd.csv"
    if not src.exists():
        pytest.skip(f"{src.name} 缺失 (需先跑 parse_eeagd + merge)")
    df = pd.read_csv(src)
    df = df[(df["min_score"] >= 450) & (df["min_score"] <= 650) & (df["min_rank"] >= 1)].copy()
    if df.empty:
        pytest.skip(f"{subject} 校准样本为空")
    synth_ranks = [score_to_rank(int(s), "guangdong", subject, 2024) for s in df["min_score"]]
    df["synth_rank"] = synth_ranks
    df["log_ratio"] = np.log10(df["min_rank"] / df["synth_rank"].clip(lower=1))
    median_log = float(df["log_ratio"].median())
    print(f"\n  GD {subject} 校准: n={len(df)} | median_log={median_log:+.3f} | factor={10**median_log:.3f}x")
    assert abs(median_log) <= TOLERANCE, (
        f"GD {subject} 校准偏差超阈值: median_log={median_log:+.3f}, 阈值 ±{TOLERANCE}"
    )
    in_band = (df["log_ratio"].abs() <= 0.15).sum() / len(df)
    assert in_band >= 0.70, f"GD {subject} 仅 {in_band:.0%} 样本在 ±0.15 内 (期望 ≥ 70%)"


# 江苏 2024 真实一分一段 anchor (sina 2024-06-25 官方发布)
JS_PHYS_ANCHORS_2024 = [
    (680, 371), (660, 2475), (640, 8014), (630, 12125),
    (600, 30768), (570, 58417), (540, 93432), (462, 187958),
]
JS_HIST_ANCHORS_2024 = [
    (640, 327), (600, 4028), (580, 8377),
    (560, 14582), (530, 26805), (478, 50966),
]


@pytest.mark.parametrize("subject,anchors", [
    ("物理", JS_PHYS_ANCHORS_2024),
    ("历史", JS_HIST_ANCHORS_2024),
])
def test_jiangsu_rank_calibration_anchors(subject: str, anchors: list):
    """江苏 2024 rank 表校准: 稀疏 anchor (8 物理 / 6 历史) 偏差 ≤ 5% log.

    gen_rank 线性插值, anchor 点应 0 偏差. 跑全 anchor, 全通过才算校准完.
    """
    diffs = []
    for score, real_cum in anchors:
        synth = score_to_rank(score, "jiangsu", subject, 2024)
        log_ratio = float(np.log10(real_cum / max(synth, 1)))
        diffs.append((score, real_cum, synth, log_ratio))
    df = pd.DataFrame(diffs, columns=["score", "real", "synth", "log_ratio"])
    print(f"\n  JS {subject} anchor 校准 ({len(anchors)} 点):")
    for _, r in df.iterrows():
        print(f"    score={int(r['score']):>3}: real={int(r['real']):>7} synth={int(r['synth']):>7} "
              f"log10={r['log_ratio']:+.3f}")
    max_abs = float(df["log_ratio"].abs().max())
    assert max_abs <= TOLERANCE, (
        f"JS {subject} anchor 校准偏差超阈值: max |log_ratio|={max_abs:.3f}, 阈值 ±{TOLERANCE}. "
        f"最大偏差点: {df.loc[df['log_ratio'].abs().idxmax()].to_dict()}"
    )
