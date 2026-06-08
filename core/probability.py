"""
core/probability.py — 录取概率估算

核心思路:
- 录取是位次竞争。位次越靠前,越稳。
- 用历史 3 年位次估一个"录取位次区间"
- 学生位次落在这个区间的位置 → 概率

P(录取) = sigmoid( (学生位次 - 录取位次中位数) / 波动σ )
        (位次数字越小越好,所以是 student_rank - school_rank)
        (学生位次小于学校, → 分子为负 → sigmoid 偏小 → 概率低? 不对,反过来)
实际:
P(录取) = sigmoid( (录取位次中位数 - 学生位次) / σ )
        (学校录到 38000 位次,学生 35000 位次 → 分子正 → sigmoid > 0.5 → 高概率)

校准 (2026-06-08, scripts/calibrate_probability.py):
- 物理 std/μ = 0.289 (经验, vs 启发式 0.25 → 116%)
- 历史 std/μ = 0.367 (经验, vs 启发式 0.25 → 147%)
- JS/GD 单年数据,沿用启发式
"""
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from .equivalent import historical_min_rank
from .data_loader import get_all_years

# ─────────────────────────────────────
# 校准 加载 (一次, 启动期)
# ─────────────────────────────────────
_CALIBRATION_PATH = Path(__file__).parent.parent / "data" / "_logs" / "probability_calibration.json"
_DEFAULT_SIGMA_FRAC = 0.25  # 启发式 fallback


@lru_cache(maxsize=1)
def _load_calibration() -> dict[str, float]:
    """加载 probability_calibration.json 校准系数. 文件缺失时返回空 dict (全部用启发式)."""
    if not _CALIBRATION_PATH.exists():
        return {}
    try:
        data = json.loads(_CALIBRATION_PATH.read_text(encoding="utf-8"))
        return {k: float(v) for k, v in data.get("factors", {}).items()}
    except Exception:
        return {}


def _sigma_frac(subject: str) -> float:
    """per-subject std/μ 系数. 优先用校准 (e.g. 物理 0.29, 历史 0.37), fallback 0.25."""
    cal = _load_calibration()
    return cal.get(subject, _DEFAULT_SIGMA_FRAC)


def estimate_admission_probability(
    student_rank: int,
    school_name: str,
    group_id: str,
    province: str,
    subject: str,
) -> dict:
    """估算录取概率

    Returns:
        {
            "probability": 0.42,        # 0-1
            "category": "稳",           # 冲/稳/保
            "historical_ranks": {2023: 35000, 2024: 38000, 2025: 40000},
            "median_rank": 38000,
            "std_rank": 2500,
        }
    """
    hist = historical_min_rank(school_name, group_id, province, subject)
    if not hist:
        # 没有历史数据,中概率
        return {
            "probability": 0.5,
            "category": "稳",
            "historical_ranks": {},
            "median_rank": None,
            "std_rank": None,
            "warning": "无历史数据",
        }

    ranks = list(hist.values())
    # 用 min 而不是 median 作为 cutoff (高考真实语义: 历史最低位次 = "能进的边缘")
    min_rank = float(min(ranks))
    median_rank = float(np.median(ranks))
    std_rank = float(np.std(ranks)) if len(ranks) > 1 else 0

    # 当数据 <3 年时,std=0 → probability 永远 50%,导致"刚好"归"稳"不归"保"
    # 用 校准后的 std/μ 比 (per subject):
    #   物理: 0.289, 历史: 0.367 (2026-06-08 scripts/calibrate_probability.py 实测)
    #   启发式 0.25 作 fallback (JS/GD 无多年重叠数据)
    # 这样:
    #   1.0x (student=min)        → 0.76 (保)
    #   1.1x                       → 0.62 (稳)
    #   1.2x                       → 0.46 (稳)
    #   1.5x                       → 0.10 (冲)
    sigma_frac = _sigma_frac(subject)
    if std_rank < min_rank * 0.05:
        std_rank = min_rank * sigma_frac

    # z: 学生位次 越靠前 (越小), z 越负, prob 越高
    z = (student_rank - min_rank) / std_rank
    # 高斯 CDF: P(学生位次 ≤ 录取位次) = Φ(-z)
    # 边界校准: student=min_rank → ~76% (不是 50%)
    # 偏移 0.7 对应于 Φ(0.7) = 0.758
    z_shifted = -z + 0.7
    probability = 0.5 * (1 + math.erf(z_shifted / math.sqrt(2)))
    probability = max(0.0, min(1.0, probability))

    # 分类
    if probability < 0.30:
        category = "冲"
    elif probability < 0.70:
        category = "稳"
    else:
        category = "保"

    return {
        "probability": round(probability, 3),
        "category": category,
        "historical_ranks": hist,
        "min_rank": int(min_rank),
        "median_rank": int(median_rank),
        "std_rank": int(std_rank),
    }
