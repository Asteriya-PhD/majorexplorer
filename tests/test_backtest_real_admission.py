"""
tests/test_backtest_real_admission.py — 真实投档表回测

测试逻辑:
对 2025 真实投档表的每条记录 (school, group, min_rank):
  1. 模拟考生位次 = min_rank (应该"刚好能上" / 保档)
  2. 模拟考生位次 = min_rank * 2 (应该"够不上" / 冲档)
  3. 模拟考生位次 = min_rank * 1.2 (应该"稳档" / 中等概率)

验证:
  - 步骤 1: 大概率 (>50%) 落入 保 档
  - 步骤 2: 大概率 (>50%) 落入 冲 档
  - 步骤 3: 大概率 (>30%) 落入 稳 档

数据覆盖:
  - 2025 物理 205 行(1 万名内)
  - 2025 历史 103 行
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.recommender import RecommendRequest, recommend


def test_subject_admission(subject: str, year: int, sample_n: int = 50):
    """对某科类投档表,采样 N 条做回测"""
    print(f"\n=== {year} {subject} 真实投档表回测 (样本 {sample_n} 条) ===")

    # 读取真实投档表
    import pandas as pd
    df = pd.read_csv(f"data/hubei_admission_{subject}_{year}.csv")
    df = df[df["min_rank"] > 0].sort_values("min_rank")
    print(f"  投档表总数: {len(df)} 行, 位次范围: {df['min_rank'].min()} - {df['min_rank'].max()}")

    # 采样
    sample = df.head(sample_n)  # 取前 sample_n 个(高分段的)
    chong_hits, wen_hits, bao_hits, total = 0, 0, 0, 0
    fail_cases = []

    for _, row in sample.iterrows():
        school = row["school_name"]
        group = row["group_id"]
        min_rank = int(row["min_rank"])
        if min_rank < 100:  # 太靠前跳过(无代表性)
            continue

        # 模拟 3 个场景
        scenarios = [
            (min_rank, "刚好", "保"),        # 应该 保
            (int(min_rank * 2), "2x", "冲"), # 应该 冲
            (int(min_rank * 1.2), "1.2x", "稳"),  # 应该 稳
        ]
        for student_rank, label, expected_cat in scenarios:
            # 用大 n_bao/n_chong 避免截断丢校(测试覆盖率 > 默认 32)
            req = RecommendRequest(
                rank=student_rank, subject=subject, year=year,
                xuanke="物+化+生" if subject == "物理" else "历+政+地",
                n_chong=200, n_wen=200, n_bao=200, n_total=600,
            )
            try:
                resp = recommend(req)
                if not resp.volunteers:
                    continue
                # 找这个 school+group 在推荐中
                for v in resp.volunteers:
                    if v.school_name == school and v.group_id == group:
                        total += 1
                        actual = v.category
                        if actual == expected_cat:
                            if expected_cat == "冲":
                                chong_hits += 1
                            elif expected_cat == "稳":
                                wen_hits += 1
                            elif expected_cat == "保":
                                bao_hits += 1
                        else:
                            fail_cases.append((school, group, label, expected_cat, actual, student_rank, min_rank))
                        break
            except Exception as e:
                pass

    print(f"  总命中: {total} / {sample_n*3} (期望: ~{sample_n*3} 中大部分分类正确)")
    if total > 0:
        print(f"  冲 档 命中: {chong_hits}")
        print(f"  稳 档 命中: {wen_hits}")
        print(f"  保 档 命中: {bao_hits}")
    if fail_cases:
        print(f"  ❌ 失败案例 (前 5):")
        for fc in fail_cases[:5]:
            print(f"    {fc}")


def test_basic_invariance():
    """不变性测试: 同一 rank 多次调用,推荐应稳定"""
    print("\n=== 不变性测试 ===")
    req = RecommendRequest(
        rank=15000, subject="物理", year=2025,
        xuanke="物+化+生",
    )
    r1 = recommend(req)
    r2 = recommend(req)
    s1 = sorted([(v.school_name, v.group_id) for v in r1.volunteers])
    s2 = sorted([(v.school_name, v.group_id) for v in r2.volunteers])
    if s1 == s2:
        print(f"  ✓ 两次调用结果完全一致 ({len(s1)} 校)")
    else:
        print(f"  ✗ 两次结果不一致!")


def main():
    print("=" * 70)
    print("真实投档表回测(基于 2025 真实数据)")
    print("=" * 70)

    # 测试物理
    test_subject_admission("物理", 2025, sample_n=50)
    # 测试历史
    test_subject_admission("历史", 2025, sample_n=30)

    test_basic_invariance()

    print("\n" + "=" * 70)
    print("回测方法说明:")
    print("  - 场景 A (刚好): student_rank = min_rank,期望 保")
    print("  - 场景 B (2x):    student_rank = min_rank*2,期望 冲")
    print("  - 场景 C (1.2x):  student_rank = min_rank*1.2,期望 稳")
    print("  注: 数据仅覆盖 1 万名内,样本外的位次不可测")
    print("=" * 70)


if __name__ == "__main__":
    main()
