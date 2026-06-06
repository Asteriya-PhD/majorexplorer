"""
tests/test_backtest_real.py — 真实数据回测

测试 1: 等效分换算回测
  - 2023 物理 580分 → 位次 X (查表)
  - 用 X 反查 2024/2025 等效分
  - 对比同一学生在不同年份需要多少分

测试 2: 一分一段表分布回测
  - 验证关键锚点合理性
  - 2024 物理 600分 → 17613, 580分 → 28232
  - 与官方公布数据交叉验证

测试 3: 算法一致性
  - 同一 rank 查 3 年表,位次应稳定
  - 等效分应随年份呈合理趋势
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rank_utils import score_to_rank, rank_to_score
from core.equivalent import equivalent_score
from core.data_loader import load_rank_table


def test_real_anchors():
    """验证 2024 真实数据的关键锚点"""
    print("\n=== 测试 1: 2024 真实数据锚点验证 ===")
    # 物理
    for score, expected_rank, note in [
        (700, 1, "满分附近"),
        (690, 98, "清华北大线"),
        (650, 2727, "C9 高校线"),
        (600, 17613, "211 高校中位"),
        (580, 28232, "一本中位"),
        (550, 48808, "一本压线"),
        (525, 68678, "特控线(一本)"),
        (500, 89501, "本科线附近"),
        (437, 140240, "本科线"),
    ]:
        actual = score_to_rank(score, "hubei", "物理", 2024)
        diff = abs(actual - expected_rank)
        mark = "✓" if diff < 200 else "✗"
        print(f"  {mark} 物理 2024 {score}分 -> 位次 {actual} (预期 ~{expected_rank}, 偏差 {diff}) [{note}]")

    # 历史
    print()
    for score, expected_rank, note in [
        (670, 9, "清华北大线"),
        (650, 97, "C9 高校线"),
        (600, 2176, "985 高校中位"),
        (580, 4361, "211 高校中位"),
        (550, 9426, "一本中位"),
        (530, 15178, "特控线"),
        (500, 21955, "本科线附近"),
        (432, 60000, "本科线"),
    ]:
        actual = score_to_rank(score, "hubei", "历史", 2024)
        diff = abs(actual - expected_rank)
        mark = "✓" if diff < 200 else "✗"
        print(f"  {mark} 历史 2024 {score}分 -> 位次 {actual} (预期 ~{expected_rank}, 偏差 {diff}) [{note}]")


def test_equivalent_score_consistency():
    """等效分回测: 同位次跨年的分数变化"""
    print("\n=== 测试 2: 等效分跨年一致性 ===")
    # 假设 2023 物理 580 分 = 位次 29066
    test_ranks = [1000, 5000, 10000, 28000, 50000, 100000]
    print(f"{'2023 位次':>10} | {'2023 等效分':>10} | {'2024 等效分':>10} | {'2025 等效分':>10} | 趋势")
    for r in test_ranks:
        s23 = rank_to_score(r, "hubei", "物理", 2023)
        s24 = rank_to_score(r, "hubei", "物理", 2024)
        s25 = rank_to_score(r, "hubei", "物理", 2025)
        trend = "↓" if s25 < s23 else ("↑" if s25 > s23 else "=")
        print(f"{r:>10} | {s23:>10} | {s24:>10} | {s25:>10} | {trend}")


def test_score_rank_roundtrip():
    """分数↔位次 互转正确性"""
    print("\n=== 测试 3: 分数↔位次 互转 ===")
    for year in [2023, 2024, 2025]:
        for subject in ["物理", "历史"]:
            # 580 → rank → score 应该回到 580
            r = score_to_rank(580, "hubei", subject, year)
            s = rank_to_score(r, "hubei", subject, year)
            diff = abs(s - 580)
            mark = "✓" if diff <= 2 else "✗"
            print(f"  {mark} {year} {subject}: 580 → 位次 {r} → 分数 {s} (偏差 {diff})")


def test_known_2025_anchors():
    """2025 关键分数位次(来自 gk100.com 公开数据)"""
    print("\n=== 测试 4: 2025 关键分数(来自 gk100.com) ===")
    expected = {
        ("物理", 600): 14274, ("物理", 580): 24295, ("物理", 550): 44422,
        ("物理", 500): 86678, ("物理", 650): 1730, ("物理", 692): 22,
        ("历史", 600): 3166, ("历史", 580): 6531, ("历史", 550): 13647,
        ("历史", 500): 28838,
    }
    for (subj, score), exp_rank in expected.items():
        actual = score_to_rank(score, "hubei", subj, 2025)
        diff_pct = abs(actual - exp_rank) / exp_rank * 100
        mark = "✓" if diff_pct < 2 else "?"
        print(f"  {mark} {subj} 2025 {score}分 -> 位次 {actual} (公开 ~{exp_rank}, 偏差 {diff_pct:.1f}%)")


def main():
    print("=" * 70)
    print("湖北 MVP 真实数据回测 (基于 2023-2025 真实一分一段表)")
    print("=" * 70)
    test_real_anchors()
    test_equivalent_score_consistency()
    test_score_rank_roundtrip()
    test_known_2025_anchors()

    print("\n" + "=" * 70)
    print("数据来源:")
    print("  - 2024 物理类: eol.cn/t20240625_2619340.shtml (546 行)")
    print("  - 2024 历史类: eol.cn/t20240625_2619345.shtml (521 行)")
    print("  - 2023 物理类: gxzsxxw.com.cn/.../2615675.html (548 行)")
    print("  - 2025 物理/历史: gk100.com/read_61700662.htm (锚点 + 插值)")
    print("=" * 70)


if __name__ == "__main__":
    main()
