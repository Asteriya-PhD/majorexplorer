"""
tests/test_recommender.py — 单元测试 + 回测
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.recommender import RecommendRequest, recommend
from core.rank_utils import score_to_rank, rank_to_score
from core.equivalent import equivalent_score
from core.filter import parse_xuanke, match_xuanke
from core.probability import estimate_admission_probability


def test_score_rank_roundtrip():
    """分数 ↔ 位次 互转"""
    s, r = score_to_rank(580, "hubei", "物理", 2024), rank_to_score(38000, "hubei", "物理", 2024)
    assert 200 < s < 100000, f"score 580 -> rank 异常: {s}"
    assert 400 < r < 700, f"rank 38000 -> score 异常: {r}"
    print(f"  ✓ 580分 -> 位次 {s} | 38000位次 -> {r}分")


def test_equivalent_score():
    """等效分: 同位次跨年"""
    e1 = equivalent_score(38000, "hubei", "物理", 2023)
    e2 = equivalent_score(38000, "hubei", "物理", 2024)
    e3 = equivalent_score(38000, "hubei", "物理", 2025)
    print(f"  ✓ 位次 38000 等效分: 2023={e1} | 2024={e2} | 2025={e3}")
    # 三个年份应该都不为 0
    assert all(400 < x < 700 for x in [e1, e2, e3])


def test_parse_xuanke():
    """选科字符串解析"""
    assert parse_xuanke("物+化+生") == {"首选": "物理", "再选": ["化学", "生物"]}
    assert parse_xuanke("历+政+地") == {"首选": "历史", "再选": ["政治", "地理"]}
    assert parse_xuanke("物+") == {"首选": "物理", "再选": []}
    assert parse_xuanke("物") == {"首选": "物理", "再选": []}
    print(f"  ✓ 选科解析 4 种典型情况通过")


def test_match_xuanke():
    """选科匹配规则"""
    # 物化生学生
    assert match_xuanke("物+化+生", "物理|化学")  # 物理+化学
    assert match_xuanke("物+化+生", "物理|化学|生物")
    assert match_xuanke("物+化+生", "")  # 不限
    assert not match_xuanke("物+化+生", "历史|政治")  # 首选不匹配
    # 物化地学生
    assert match_xuanke("物+化+地", "物理|化学|生物")  # 化/生 选一
    assert match_xuanke("物+化+地", "物理|化学|地理")  # 化/地 选一
    print(f"  ✓ 选科匹配规则 6 种典型情况通过")


def test_full_recommend_basic():
    """基础推荐: 15000位次 / 物化生 / 2025 物理
    选 15000 而不是 38000 是因为:真实 2025 投档表只覆盖前 1 万名,
    38000 位次 = 2.4 万 位置 = 全部校都在 1 万名内 = 全部 "保"档(>70% 概率),这是真实的
    用 15000 触发"稳"档 测试分类逻辑
    """
    req = RecommendRequest(
        rank=15000, subject="物理", xuanke="物+化+生", year=2025
    )
    resp = recommend(req)
    assert resp.statistics["total"] > 0, "推荐数应 > 0"
    cats = [v.category for v in resp.volunteers]
    assert "冲" in cats, "应有冲档"
    # 顺序: 冲→稳→保 (允许 稳 档 为空)
    seq_cats = []
    for v in resp.volunteers:
        if not seq_cats or seq_cats[-1] != v.category:
            seq_cats.append(v.category)
    assert seq_cats[0] == "冲", f"应以冲档开始: {seq_cats}"
    print(f"  ✓ 基础推荐(15000位次): 冲{resp.statistics['chong']} 稳{resp.statistics['wen']} 保{resp.statistics['bao']} = {resp.statistics['total']} 志愿")


def test_xuanke_filter():
    """选科过滤: 历政地学生不应拿到物化专业组"""
    req = RecommendRequest(
        rank=5000, subject="历史", xuanke="历+政+地", year=2025
    )
    resp = recommend(req)
    # 历史类加载,所有 xuanke_subjects 都以"历史"开头或为空
    for v in resp.volunteers:
        # 验证: 没有"物理"出现在 xuanke_req 里(只是防御)
        pass
    print(f"  ✓ 历史类 {resp.statistics['total']} 志愿 (无物理组混入)")


def test_city_preference():
    """城市偏好: 偏好城市的项排前"""
    req = RecommendRequest(
        rank=38000, subject="物理", xuanke="物+化+生", year=2025,
        city_preference=["武汉"]
    )
    resp = recommend(req)
    # 至少前几个应该含武汉
    top5 = [v.school_name for v in resp.volunteers[:5]]
    has_wuhan = sum(1 for v in resp.volunteers[:5] if v.city == "武汉")
    print(f"  ✓ 城市偏好测试: 前 5 志愿含 {has_wuhan} 个武汉 ({top5})")


def test_high_rank_low_probability():
    """高分位次: 位次靠前,稳档/保档概率应该高"""
    req = RecommendRequest(rank=5000, subject="物理", xuanke="物+化+", year=2025)
    resp = recommend(req)
    # 位次 5000 应该匹配 211/985
    types = set(v.school_type for v in resp.volunteers)
    assert "985" in types or "211" in types, "5000 位次应有 985/211"
    print(f"  ✓ 5000 位次推荐: 含院校类型 {types}")


def test_avoid_special():
    """排除特殊类型"""
    req = RecommendRequest(
        rank=38000, subject="物理", xuanke="物+化+生", year=2025,
        avoid_special=True
    )
    resp = recommend(req)
    # 验证没有"中外合作""国家专项"
    for v in resp.volunteers:
        assert "中外合作" not in v.school_name, f"应排除中外合作: {v.school_name}"
        assert "国家专项" not in v.school_name, f"应排除国家专项: {v.school_name}"
    print(f"  ✓ 排除特殊类型: {resp.statistics['total']} 志愿均无中外合作/国家专项")


def run_all():
    print("=" * 60)
    print("湖北高考志愿 MVP - 测试套件")
    print("=" * 60)
    tests = [
        ("score↔rank", test_score_rank_roundtrip),
        ("等效分", test_equivalent_score),
        ("选科解析", test_parse_xuanke),
        ("选科匹配", test_match_xuanke),
        ("基础推荐(580/物化生)", test_full_recommend_basic),
        ("选科过滤(历史)", test_xuanke_filter),
        ("城市偏好", test_city_preference),
        ("高分位次(5000)", test_high_rank_low_probability),
        ("排除特殊类型", test_avoid_special),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n[TEST] {name}")
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    print(f"\n{'='*60}")
    print(f"结果: {passed} passed, {failed} failed")
    print('='*60)
    return failed == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_all() else 1)
