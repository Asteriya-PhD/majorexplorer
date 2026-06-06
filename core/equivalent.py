"""
core/equivalent.py — 等效分/等效位次换算

核心:不同年份的"位次"在制度上是可比的(因为都是按总人数排),
但"分数"不可比(题难易度+报考人数+招生计划都在变)。

所以:
- 位次 → 位次: 跨年直接可比(分数波动被吸收)
- 位次 → 分数: 跨年不可直接比,必须查对应年份的一分一段表
"""
from .rank_utils import rank_to_score
from .data_loader import load_admission_table


def equivalent_score(rank: int, province: str, subject: str, target_year: int) -> int:
    """将某位次换算到目标年份的等效分数
    (即:在目标年份,需要考多少分才能排到这个位次)

    这是"等效分"的核心逻辑,优志愿等商业系统都这么做。
    """
    return rank_to_score(rank, province, subject, target_year)


def equivalent_rank_3year(province: str, subject: str, year: int, current_rank: int) -> dict:
    """取近 3 年的等效分对照
    用途:让用户看到"我这个位次,前 2 年分别要多少分"

    Returns:
        {2023: 580, 2024: 575, 2025: 580, ...}
    """
    from .data_loader import get_all_years
    years = get_all_years(province)
    result = {}
    for y in years:
        try:
            result[y] = rank_to_score(current_rank, province, subject, y)
        except Exception:
            pass
    return result


def historical_min_rank(school: str, group_id: str, province: str, subject: str, target_year: int = None) -> dict:
    """取某校某专业组近 3 年的最低位次
    Returns:
        {2023: 35000, 2024: 38000, 2025: 40000}
    """
    from .data_loader import get_all_years
    years = get_all_years(province)
    result = {}
    for y in years:
        try:
            df = load_admission_table(province, subject, y)
            row = df[(df["school_name"] == school) & (df["group_id"] == group_id)]
            if not row.empty:
                result[y] = int(row.iloc[0]["min_rank"])
        except Exception:
            pass
    return result
