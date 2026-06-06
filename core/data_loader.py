"""
core/data_loader.py — 加载 一分一段表 + 院校专业组投档表

多省支持: 通过 province 参数切换数据源
- 数据文件命名: data/{province}_rank_{subject}_{year}.csv
- 示例: data/hubei_rank_物理_2024.csv, data/guangdong_rank_物理_2024.csv
"""
from pathlib import Path
from functools import lru_cache
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"


def _normalize_rank_table(df: pd.DataFrame) -> pd.DataFrame:
    """清洗一分一段表: 把 '695-750' 这种范围字符串转成下界 695,分数强制 int"""
    df = df.copy()
    def parse_score(s):
        s = str(s).strip()
        if "-" in s:
            return int(s.split("-")[0])
        return int(s)
    df["score"] = df["score"].apply(parse_score)
    df["rank"] = df["rank"].astype(int)
    df["count"] = df["count"].astype(int)
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    return df


@lru_cache(maxsize=64)
def load_rank_table(province: str, subject: str, year: int) -> pd.DataFrame:
    """加载一分一段表
    Args:
        province: 省份(拼音或中文,如 'hubei' / '湖北')
        subject: '物理' or '历史'
        year: 高考年份
    Returns:
        DataFrame with columns [score(int), rank(int), count(int)], 按 score 降序
    """
    path = DATA_DIR / f"{province}_rank_{subject}_{year}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"未找到 {path.name}。可运行: python scripts/fetch_real_data.py --year {year} --subject {subject}"
        )
    df = pd.read_csv(path)
    return _normalize_rank_table(df)


@lru_cache(maxsize=64)
def load_admission_table(province: str, subject: str, year: int) -> pd.DataFrame:
    """加载院校专业组投档表
    Args:
        province: 省份
        subject: '物理' or '历史'
        year: 高考年份
    Returns:
        DataFrame with columns:
        [year, subject, school_name, school_type, group_id, xuanke_req,
         xuanke_subjects, plan_count, min_score, min_rank, tuition_yuan,
         city, is_special]
    """
    path = DATA_DIR / f"{province}_admission_{subject}_{year}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"未找到 {path.name}。"
        )
    return pd.read_csv(path)


def get_all_provinces() -> list[str]:
    """返回 data/ 下有的省份代码(去重,按拼音排序)"""
    provinces = set()
    for p in DATA_DIR.glob("*_rank_*.csv"):
        # 文件名: {province}_rank_{subject}_{year}.csv
        name = p.stem  # e.g. hubei_rank_物理_2024
        province = name.split("_rank_")[0]
        provinces.add(province)
    return sorted(provinces)


def get_all_subjects(province: str = None) -> list[str]:
    """返回可用的科类
    Args:
        province: 不传则取所有省的并集;传了则只查该省
    """
    if province:
        glob = f"{province}_rank_*.csv"
    else:
        glob = "*_rank_*.csv"
    subjects = set()
    for p in DATA_DIR.glob(glob):
        # 文件名: {province}_rank_{subject}_{year}.csv
        name = p.stem
        parts = name.split("_rank_")
        if len(parts) >= 2:
            subj_year = parts[1]
            subject = subj_year.rsplit("_", 1)[0]
            subjects.add(subject)
    return sorted(subjects)


def get_all_years(province: str = None) -> list[int]:
    """返回可用的年份
    Args:
        province: 不传则取所有省;传了则只查该省
    """
    if province:
        glob = f"{province}_rank_*.csv"
    else:
        glob = "*_rank_*.csv"
    years = set()
    for p in DATA_DIR.glob(glob):
        try:
            year = int(p.stem.rsplit("_", 1)[-1])
            years.add(year)
        except ValueError:
            pass
    return sorted(years)


def get_all_xuanke_options(province: str = "hubei") -> list[str]:
    """返回指定省的选科组合

    3+1+2 (湖北/广东/江苏/湖南/河北/重庆/辽宁/福建/海南): 12 种
    3+3 (北京/上海/天津/浙江/山东): 20 种
    """
    from .filter import (
        PROVINCES_3_PLUS_3, PROVINCES_3_PLUS_1_PLUS_2,
        get_all_xuanke_options_3_plus_3, get_all_xuanke_options_3_plus_1_plus_2,
    )
    if province in PROVINCES_3_PLUS_3:
        return get_all_xuanke_options_3_plus_3()
    if province in PROVINCES_3_PLUS_1_PLUS_2:
        return get_all_xuanke_options_3_plus_1_plus_2()
    return get_all_xuanke_options_3_plus_1_plus_2()  # default
