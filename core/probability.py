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
"""
import math
import numpy as np
import pandas as pd
from .equivalent import historical_min_rank
from .data_loader import get_all_years


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
    # 用 25% min_rank 作为隐含不确定性(1 std = 25% 名次)
    # 这样:
    #   1.0x (student=min)        → 0.76 (保)
    #   1.1x                       → 0.62 (稳)
    #   1.2x                       → 0.46 (稳)
    #   1.5x                       → 0.10 (冲)
    if std_rank < min_rank * 0.05:
        std_rank = min_rank * 0.25

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
