"""
tests/test_rank_calibration.py — 广东 rank 表校准回归测试

防 合成 rank 表 vs eea.gd 真实投档位次 系统性偏差. 历史 2026-06-08
发现 GD 历史 偏 -51% (median_log10=-0.31), 修锚点后归零 (≤ ±0.05).

数据:
- 真实: data/guangdong_admission_{物理|历史}_2024_real_eeagd.csv
- 合成: data/guangdong_rank_{物理|历史}_2024.csv (score_to_rank)

阈值: 总体 median_log10(真实/合成) 在 ±0.05 内 (即 0.89x ~ 1.12x).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.rank_utils import score_to_rank  # noqa: E402

DATA_DIR = Path(__file__).parent.parent / "data"
TOLERANCE = 0.05  # median_log_ratio 阈值 (10^x = 0.89 ~ 1.12)


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
    factor = 10**median_log
    print(f"\n  GD {subject} 校准: n={len(df)} | median_log={median_log:+.3f} | factor={factor:.3f}x")
    # 主断言: 总体偏差在 ±0.05 内
    assert abs(median_log) <= TOLERANCE, (
        f"GD {subject} 校准偏差超阈值: median_log={median_log:+.3f} (factor={factor:.3f}x), "
        f"阈值 ±{TOLERANCE}. 重新跑 scripts/calibrate_rank.py 查报告"
    )
    # 次断言: 至少 70% 样本的 log_ratio 在 ±0.15 内
    in_band = (df["log_ratio"].abs() <= 0.15).sum() / len(df)
    assert in_band >= 0.70, f"GD {subject} 仅 {in_band:.0%} 样本在 ±0.15 内 (期望 ≥ 70%)"
