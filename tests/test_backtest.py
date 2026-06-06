"""
tests/test_backtest.py — 回测

方法: 用 2023-2024 数据预测 2025 → 验证算法分类(冲/稳/保)是否合理
输入: 假设考生 2025 年位次 = X
输出: 看推荐列表中是否包含 2025 年实际录取位次 ≈ X 的校
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.recommender import RecommendRequest, recommend
from core.data_loader import load_admission_table


def backtest_2025_with_2023_2024():
    """用 2023-2024 预测 2025,验证命中率"""
    df2025 = load_admission_table("物理", 2025)

    # 取 2025 年所有校的实际 min_rank
    # 模拟考生位次 = 25000 (物理类)
    test_rank = 25000
    req = RecommendRequest(rank=test_rank, subject="物理", xuanke="物+化+生", year=2025)
    resp = recommend(req)

    print(f"回测: 假设考生位次 = {test_rank}")
    print(f"推荐总数: {resp.statistics['total']}")
    print()

    # 验证: 2025 年实际录取位次接近 test_rank 的校,应该出现在推荐中
    actual_2025_around = df2025[
        (df2025["min_rank"] >= test_rank - 5000) &
        (df2025["min_rank"] <= test_rank + 5000)
    ]
    print(f"2025 年实际录取位次在 [{test_rank-5000}, {test_rank+5000}] 区间的校: {len(actual_2025_around)} 所")
    print()

    # 检查每个分类的合理性
    for category in ["冲", "稳", "保"]:
        items = [v for v in resp.volunteers if v.category == category]
        if items:
            ranks = [v.min_rank_historical.get(2025, 0) for v in items]
            print(f"[{category}] {len(items)} 校, 2025 年位次范围: {min(ranks)} - {max(ranks)}")

    # 命中: 推荐中 2025 年位次接近 test_rank 的校
    recommended_2025_ranks = [v.min_rank_historical.get(2025, 0) for v in resp.volunteers]
    hits = [r for r in recommended_2025_ranks if abs(r - test_rank) <= 5000]
    print(f"\n✅ 命中率(2025 年实际录取位次 ± 5000): {len(hits)} / {len(recommended_2025_ranks)} "
          f"= {len(hits)/max(1,len(recommended_2025_ranks)):.1%}")


def test_high_score_5000():
    """高分(5000 位次)回测"""
    req = RecommendRequest(rank=5000, subject="物理", xuanke="物+化+", year=2025)
    resp = recommend(req)
    types = {}
    for v in resp.volunteers:
        types[v.category] = types.get(v.category, 0) + 1
    print(f"\n高分(5000位次)回测: 分类 = {types}")
    # 5000 位次应能保 985
    bao_985 = sum(1 for v in resp.volunteers if v.category == "保" and v.school_type == "985")
    print(f"✅ 5000 位次保档中 985 数: {bao_985}")


def test_low_score_120000():
    """低分(120000 位次)回测"""
    req = RecommendRequest(rank=120000, subject="物理", xuanke="物+化+生", year=2025)
    resp = recommend(req)
    types = {}
    for v in resp.volunteers:
        types[v.category] = types.get(v.category, 0) + 1
    print(f"\n低分(120000位次)回测: 分类 = {types}")
    # 120000 位次应能保专科/普通本科


if __name__ == "__main__":
    print("=" * 60)
    print("湖北 MVP - 回测 (用 2023-2024 数据预测 2025)")
    print("=" * 60)
    backtest_2025_with_2023_2024()
    test_high_score_5000()
    test_low_score_120000()
    print("\n✅ 回测完成 (注: 样本数据,真实回测需替换为官方数据)")
