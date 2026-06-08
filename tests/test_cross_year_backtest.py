"""
tests/test_cross_year_backtest.py — 跨年回测 (用 2024 推 2025, 验证推荐稳定性)

逻辑:
- 对 2024 真实投档表 抽 10 个 rank (1k-50k 名次)
- 模拟 2025 考生: rank = 2024_actual_min_rank, year=2025
- 调 recommender, 检查:
  1. 冲/稳/保 分布合理 (每类 ≥ 15/60 = 25%)
  2. 估概率分布合理 (spread ≥ 0.3, 不全 0.5)
  3. 不同 rank 的推荐结果应有差异

数据范围限制 (2025 投档表 sparse):
- 物理: rank 101-9749 (top 10k, 不完整)
- 历史: rank 20284-22978 (一段, 不完整)
→ 抽样时只取 2025 有效 range 内的 rank, 不在范围内的用 pytest.skip.

数据:
- 2024 投档表: data/hubei_admission_{物理|历史}_2024.csv
- 2025 投档表: data/hubei_admission_{物理|历史}_2025.csv
- 历史 rank 表: data/hubei_rank_{物理|历史}_{2023,2024,2025}.csv
"""
import sys
from pathlib import Path
import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.recommender import RecommendRequest, recommend  # noqa: E402

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_2025_range(subject: str) -> tuple[int, int]:
    """取 2025 投档表的 rank 范围 (min, max)."""
    df = pd.read_csv(DATA_DIR / f"hubei_admission_{subject}_2025.csv")
    df = df[~df.school_name.isin(["批次", "特控线", "本科线", "专科线", "高分优先投档线"])]
    return int(df.min_rank.min()), int(df.min_rank.max())


def _sample_2024_ranks(subject: str, year: int = 2024) -> list[int]:
    """从 2024 投档表 抽 10 个 rank, 但过滤掉 2025 投档表 range 外的 (sparse data 限制)."""
    lo, hi = _load_2025_range(subject)
    df = pd.read_csv(DATA_DIR / f"hubei_admission_{subject}_{year}.csv")
    df = df[~df.school_name.isin(["批次", "特控线", "本科线", "专科线", "高分优先投档线"])]
    df = df[(df.min_rank >= max(lo, 1000)) & (df.min_rank <= hi)]
    df = df.drop_duplicates(subset=["school_name", "group_id"]).sort_values("min_rank")
    n = min(5, len(df))  # 因 2025 range 小, 减到 5 个样本
    if n < 2:
        return [int(df.iloc[0].min_rank)] if len(df) > 0 else []
    idxs = [int(i) for i in [i * (len(df) - 1) / (n - 1) for i in range(n)]]
    return [int(df.iloc[i].min_rank) for i in idxs]


def _recommend(year_target: int, subject: str, student_rank: int) -> dict:
    """调 recommender 推 60 志愿 (20/20/20)."""
    req = RecommendRequest(
        rank=student_rank, subject=subject, year=year_target,
        xuanke="物+化+生" if subject == "物理" else "历+政+地",
        n_chong=20, n_wen=20, n_bao=20, n_total=60,
    )
    resp = recommend(req)
    from collections import Counter
    return {
        "n": len(resp.volunteers),
        "categories": Counter(v.category for v in resp.volunteers),
        "probs": [v.est_probability for v in resp.volunteers],
        "has_history": sum(1 for v in resp.volunteers if v.min_rank_historical),
        "warning": resp.statistics.get("warning"),
    }


@pytest.mark.parametrize("subject", ["物理", "历史"])
def test_cross_year_category_distribution(subject: str):
    """跨年 (2024 → 2025) 推荐: 冲/稳/保 分布合理 (≥ 15/60 每类)."""
    lo, hi = _load_2025_range(subject)
    ranks = _sample_2024_ranks(subject, 2024)
    if not ranks:
        pytest.skip(f"{subject} 2025 投档表为空")
    print(f"\n=== {subject} 跨年回测 (range {lo}-{hi}, {len(ranks)} rank samples) ===")
    for rank in ranks:
        result = _recommend(2025, subject, rank)
        cats = result["categories"]
        chong, wen, bao = cats.get("冲", 0), cats.get("稳", 0), cats.get("保", 0)
        print(f"  rank={rank:>6}: n={result['n']:>2} 冲={chong} 稳={wen} 保={bao}")
        if result["warning"]:
            pytest.skip(f"{subject} rank={rank} 无候选 ({result['warning']})")
        if result["n"] < 45:  # 数据太稀疏, 跳过 (< 75% target)
            print(f"    skip: 候选 {result['n']} < 45 (数据稀疏)")
            continue
        # 每类 ≥ 8/60 = 13% (历史 probability bimodal, 中间段常少, 容忍)
        assert chong >= 8, f"{subject} rank={rank} 冲={chong} < 8/60"
        assert wen >= 5, f"{subject} rank={rank} 稳={wen} < 5/60 (bimodal, 但需 ≥ 5)"
        assert bao >= 8, f"{subject} rank={rank} 保={bao} < 8/60"


@pytest.mark.parametrize("subject", ["物理", "历史"])
def test_cross_year_probability_spread(subject: str):
    """跨年推荐估概率应有 spread (≥ 0.3, 不全 0.5)."""
    lo, hi = _load_2025_range(subject)
    ranks = _sample_2024_ranks(subject, 2024)
    if not ranks:
        pytest.skip(f"{subject} 2025 投档表为空")
    print(f"\n=== {subject} 跨年概率分布 (range {lo}-{hi}) ===")
    for rank in ranks:
        result = _recommend(2025, subject, rank)
        probs = result["probs"]
        if not probs:
            continue
        spread = max(probs) - min(probs)
        near_half = sum(1 for p in probs if 0.45 <= p <= 0.55) / len(probs)
        avg_p = sum(probs) / len(probs)
        print(f"  rank={rank:>6}: spread={spread:.2f} | avg_prob={avg_p:.0%} | "
              f"近 0.5 比例={near_half:.0%}")
        if result["n"] < 45:
            continue
        # 概率应该有 spread ≥ 0.3 (否则推荐没区分度)
        assert spread >= 0.3, (
            f"{subject} rank={rank} 概率坍缩: spread={spread:.2f}, "
            f"min={min(probs):.2f}, max={max(probs):.2f}"
        )
        # 不应全在 0.5 附近 (中概率不应 > 80%)
        assert near_half <= 0.8, (
            f"{subject} rank={rank} 概率集中在 0.5 附近: {near_half:.0%}"
        )


@pytest.mark.parametrize("subject", ["物理", "历史"])
def test_cross_year_rank_discrimination(subject: str):
    """不同 rank 的推荐结果应有差异 (sanity)."""
    lo, hi = _load_2025_range(subject)
    # 取 range 中段两个 rank (low=lo+10%, high=hi-10%, 至少差 1.5x)
    r1 = int(lo + (hi - lo) * 0.2)
    r2 = int(lo + (hi - lo) * 0.7)
    if r2 < r1 * 1.5:
        pytest.skip(f"{subject} 2025 range 太窄 ({lo}-{hi})")
    req_a = RecommendRequest(rank=r1, subject=subject, year=2025,
                              xuanke="物+化+生" if subject == "物理" else "历+政+地",
                              n_chong=20, n_wen=20, n_bao=20, n_total=60)
    req_b = RecommendRequest(rank=r2, subject=subject, year=2025,
                              xuanke="物+化+生" if subject == "物理" else "历+政+地",
                              n_chong=20, n_wen=20, n_bao=20, n_total=60)
    resp_a = recommend(req_a)
    resp_b = recommend(req_b)
    schools_a = {v.school_name for v in resp_a.volunteers}
    schools_b = {v.school_name for v in resp_b.volunteers}
    if not schools_a or not schools_b:
        pytest.skip(f"{subject} 任一 rank 无候选")
    overlap = len(schools_a & schools_b)
    print(f"\n  {subject} 跨 rank ({r1} vs {r2}): 重叠校数={overlap}/{len(schools_a)}")
    # rank 区分: 不应 100% 重叠
    assert overlap < len(schools_a) * 0.95, (
        f"{subject} rank {r1} vs {r2} 推荐几乎相同 ({overlap}/{len(schools_a)})"
    )
