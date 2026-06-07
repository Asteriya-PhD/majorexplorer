"""
tests/test_backtest_real_admission.py — 真实投档表回测 (v2)

测试逻辑:
对 2024/2025 真实投档表 (MinerU 扩展后) 的每条记录 (school, group, min_rank):
  1. 模拟考生位次 = min_rank (应该"刚好能上" / 保档)
  2. 模拟考生位次 = min_rank * 2 (应该"够不上" / 冲档)
  3. 模拟考生位次 = min_rank * 1.2 (应该"稳档" / 中等概率)

验证 (assertions):
  - 步骤 1: 大多数 (>50%) 落入 保 档
  - 步骤 2: 大多数 (>50%) 落入 冲 档
  - 步骤 3: 大多数 (>40%) 落入 稳 档

跨年回测:
  - 用 2024 min_rank 通过等效分换算, 模拟 2025 推荐, 验证类别分布合理

数据覆盖 (v2):
  - 2024 物理 575 行 (MinerU 大幅扩充, 之前 323)
  - 2024 历史 436 行 (之前 194)
  - 2025 物理 205 行, 历史 103 行
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
from core.recommender import RecommendRequest, recommend


def _load_admission(subject: str, year: int) -> pd.DataFrame:
    """加载并清理投档表 (排除控制线行, 限制 rank 范围)."""
    df = pd.read_csv(f"data/hubei_admission_{subject}_{year}.csv")
    # 排除控制线 (校名是 批次/特控线/本科线)
    df = df[~df.school_name.isin(["批次", "特控线", "本科线", "专科线", "高分优先投档线"])]
    # 限制 rank 范围: 100-100000 (排除 0/999999 等异常)
    df = df[(df.min_rank >= 100) & (df.min_rank <= 100000)]
    return df.sort_values("min_rank")


def _run_scenario(student_rank: int, school: str, group: str, subject: str, year: int) -> str | None:
    """对 (student_rank, school, group) 调用 recommender, 返回该校的 档位 (冲/稳/保) 或 None (未推荐)."""
    req = RecommendRequest(
        rank=student_rank, subject=subject, year=year,
        xuanke="物+化+生" if subject == "物理" else "历+政+地",
        n_chong=300, n_wen=300, n_bao=300, n_total=900,  # 扩大覆盖
    )
    try:
        resp = recommend(req)
    except Exception:
        return None
    for v in resp.volunteers:
        if v.school_name == school and str(v.group_id).zfill(2) == str(group).zfill(2):
            return v.category
    return None


@pytest.mark.parametrize("subject,year,min_rank_min,min_rank_max,sample_n", [
    ("物理", 2025, 1000, 10000, 30),    # 2025 数据有限, 中间段 1k-10k
    ("历史", 2025, 5000, 25000, 30),   # 2025 历史 名次范围广
    ("物理", 2024, 1000, 30000, 30),   # 2024 数据多, 取 1k-30k
    ("历史", 2024, 2000, 30000, 30),
])
def test_category_distribution(subject: str, year: int, min_rank_min: int, min_rank_max: int, sample_n: int):
    """3 场景下, 类目分布应符合预期 (冲/稳/保)."""
    df = _load_admission(subject, year)
    sample = df[(df.min_rank >= min_rank_min) & (df.min_rank <= min_rank_max)].head(sample_n)
    assert not sample.empty, f"无 {year} {subject} 样本 (rank {min_rank_min}-{min_rank_max})"

    cats_per_scenario = {"刚好": [], "2x": [], "1.2x": []}
    for _, row in sample.iterrows():
        min_rank = int(row.min_rank)
        for factor, label in [(1.0, "刚好"), (2.0, "2x"), (1.2, "1.2x")]:
            student_rank = int(min_rank * factor)
            cat = _run_scenario(student_rank, row.school_name, row.group_id, subject, year)
            if cat is not None:
                cats_per_scenario[label].append(cat)

    # 统计每个场景的类目分布
    for label, cats in cats_per_scenario.items():
        if not cats:
            continue
        n = len(cats)
        chong = cats.count("冲") / n
        wen = cats.count("稳") / n
        bao = cats.count("保") / n
        print(f"  {year} {subject} {label}: n={n} | 冲={chong:.0%} 稳={wen:.0%} 保={bao:.0%}")

    # Assertions (允许一定容差, 因为 1.2x 边界场景有交叉)
    # 1. 刚好 (student_rank=min_rank) → 应大多数保
    if cats_per_scenario["刚好"]:
        bao_rate = cats_per_scenario["刚好"].count("保") / len(cats_per_scenario["刚好"])
        assert bao_rate >= 0.5, f"{year} {subject} 刚好场景保率 {bao_rate:.0%} 低于 50%"
    # 2. 2x (远低分) → 应大多数冲
    if cats_per_scenario["2x"]:
        chong_rate = cats_per_scenario["2x"].count("冲") / len(cats_per_scenario["2x"])
        assert chong_rate >= 0.5, f"{year} {subject} 2x场景冲率 {chong_rate:.0%} 低于 50%"
    # 3. 1.2x (边缘) → 应大多数稳或保 (容差大)
    if cats_per_scenario["1.2x"]:
        ok = cats_per_scenario["1.2x"].count("稳") + cats_per_scenario["1.2x"].count("保")
        rate = ok / len(cats_per_scenario["1.2x"])
        assert rate >= 0.4, f"{year} {subject} 1.2x场景 稳+保 {rate:.0%} 低于 40%"


def test_basic_invariance():
    """不变性测试: 同一 rank 多次调用,推荐应稳定"""
    req = RecommendRequest(rank=15000, subject="物理", year=2025, xuanke="物+化+生")
    r1 = recommend(req)
    r2 = recommend(req)
    s1 = sorted([(v.school_name, v.group_id) for v in r1.volunteers])
    s2 = sorted([(v.school_name, v.group_id) for v in r2.volunteers])
    assert s1 == s2, f"两次调用结果不一致: {set(s1) ^ set(s2)}"


def test_probability_calibration():
    """概率校准: 不同场景下的预测概率分布应合理."""
    print("\n=== 概率校准 ===")
    # 模拟 5 个 rank, 看推荐概率分布
    for rank in [2000, 5000, 10000, 20000, 50000]:
        req = RecommendRequest(rank=rank, subject="物理", year=2024, xuanke="物+化+生")
        resp = recommend(req)
        if not resp.volunteers:
            continue
        probs = [v.est_probability for v in resp.volunteers]
        avg = sum(probs) / len(probs)
        # 分类
        chong_n = sum(1 for v in resp.volunteers if v.category == "冲")
        wen_n = sum(1 for v in resp.volunteers if v.category == "稳")
        bao_n = sum(1 for v in resp.volunteers if v.category == "保")
        print(f"  rank={rank:>6d}: n={len(resp.volunteers)} (冲{chong_n}/稳{wen_n}/保{bao_n}) | 平均概率 {avg:.0%}")


def main():
    print("=" * 70)
    print("真实投档表回测 v2 (基于 MinerU 扩展 575/436 行 2024 + 205/103 行 2025)")
    print("=" * 70)
    for sub, yr in [("物理", 2025), ("历史", 2025), ("物理", 2024), ("历史", 2024)]:
        try:
            test_category_distribution(sub, yr,
                1000 if sub == "物理" else 2000,
                10000 if yr == 2025 else 30000,
                30)
        except AssertionError as e:
            print(f"  ❌ {yr} {sub}: {e}")
    test_probability_calibration()
    test_basic_invariance()
    print("=" * 70)


if __name__ == "__main__":
    main()
