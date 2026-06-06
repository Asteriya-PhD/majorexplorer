"""
core/rank_utils.py — 位次 ↔ 分数 互转
核心:不靠分数,靠位次。分数只是展示。
"""
import pandas as pd
from .data_loader import load_rank_table


def score_to_rank(score: int, province: str, subject: str, year: int) -> int:
    """分数 → 全省位次
    Args:
        score: 高考分数
        province: 省份(如 'hubei' / 'guangdong')
        subject: '物理' or '历史'
        year: 高考年份
    Returns:
        全省位次 (1-based, 1 = 第一名)
    """
    rt = load_rank_table(province, subject, year)
    candidates = rt[rt["score"] == score]
    if not candidates.empty:
        return int(candidates.iloc[0]["rank"])
    idx = (rt["score"] - score).abs().idxmin()
    return int(rt.iloc[idx]["rank"])


def rank_to_score(rank: int, province: str, subject: str, year: int) -> int:
    """全省位次 → 分数
    Args:
        rank: 全省位次 (1-based)
        province: 省份
        subject: '物理' or '历史'
        year: 高考年份
    Returns:
        对应分数(取整)
    """
    rt = load_rank_table(province, subject, year)
    idx = (rt["rank"] - rank).abs().idxmin()
    return int(rt.iloc[idx]["score"])


def rank_to_score_range(rank: int, province: str, subject: str, year: int, window: int = 100) -> tuple[int, int]:
    """位次 → 分数区间(±window 位次)
    用于估算录取概率时的不确定性
    """
    rt = load_rank_table(province, subject, year)
    lo_idx = (rt["rank"] - (rank - window)).abs().idxmin()
    hi_idx = (rt["rank"] - (rank + window)).abs().idxmin()
    return int(rt.iloc[lo_idx]["score"]), int(rt.iloc[hi_idx]["score"])
