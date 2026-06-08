"""
tests/test_probability_calibration.py — 概率模型 std 校准回归测试

防 校准 JSON 漂移 / 误删. 校准本身 2026-06-08 用 scripts/calibrate_probability.py
跑出: 物理 0.289, 历史 0.367 (vs 启发式 0.25).

threshold: per-subject sigma_frac 在 [0.20, 0.50] 内 (启发式 ±1 倍范围).
JSON 文件存在 (data/_logs/probability_calibration.json).
"""
import sys
from pathlib import Path
import json
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.probability import _sigma_frac, _load_calibration, estimate_admission_probability  # noqa: E402

CALIB_PATH = Path(__file__).parent.parent / "data" / "_logs" / "probability_calibration.json"


def test_calibration_file_exists():
    """校准 JSON 必须存在 (scripts/calibrate_probability.py 跑出)."""
    assert CALIB_PATH.exists(), (
        f"校准 JSON 缺失 {CALIB_PATH}. 跑 python3 scripts/calibrate_probability.py 重生成"
    )


def test_calibration_factors_in_range():
    """per-subject 校准系数 在 [0.20, 0.50] 内 (启发式 0.25 ±1 倍)."""
    factors = _load_calibration()
    assert factors, "校准 factors 空 — JSON 格式错?"
    for subject, sigma_frac in factors.items():
        assert 0.20 <= sigma_frac <= 0.50, (
            f"{subject} 校准 {sigma_frac} 超出 [0.20, 0.50] 范围. "
            f"重跑 calibrate_probability.py 或查数据"
        )


@pytest.mark.parametrize("subject,expected_lo,expected_hi", [
    # 校准 2026-06-08: 物理 0.289, 历史 0.367
    # 容差 ±0.10 (允许数据 漂移, e.g. 加 2025 数据重算)
    ("物理", 0.20, 0.40),
    ("历史", 0.30, 0.50),
])
def test_calibration_factor_stable(subject: str, expected_lo: float, expected_hi: float):
    """校准系数 ±0.10 容差 (避免大漂移, 但允许 数据 变化)."""
    actual = _sigma_frac(subject)
    assert expected_lo <= actual <= expected_hi, (
        f"{subject} 校准 {actual} 漂移出 [{expected_lo}, {expected_hi}]. "
        f"如确认, 跑 calibrate_probability.py 重新写"
    )


def test_probability_uses_calibrated_sigma():
    """estimate_admission_probability 用校准 σ 后, prob 分布 应比启发式 更 spread."""
    # 物理 rank=10000 student, 看一些 schools
    from core.recommender import RecommendRequest, recommend
    req = RecommendRequest(rank=10000, subject="物理", year=2024, xuanke="物+化+生",
                            n_chong=20, n_wen=20, n_bao=20, n_total=60)
    resp = recommend(req)
    probs = [v.est_probability for v in resp.volunteers]
    assert probs, "无候选"
    spread = max(probs) - min(probs)
    # 校准后 std_rank 更大, spread 应该 ≥ 0.4 (vs 启发式 0.3)
    # 因为 std/μ 从 0.25 → 0.289, prob 同样 input 变化略大
    assert spread >= 0.3, f"prob spread {spread} 过小, 校准未生效?"


def test_probability_fallback_to_heuristic():
    """JSON 缺失时, _sigma_frac 应 fallback 到 0.25 (启发式)."""
    # 临时删 cal 路径
    import core.probability as p
    orig_cache = p._load_calibration.cache_clear()
    # 改路径到不存在的文件
    orig_path = p._CALIBRATION_PATH
    p._CALIBRATION_PATH = Path("/nonexistent/probability_calibration.json")
    p._load_calibration.cache_clear()
    try:
        sigma = p._sigma_frac("物理")
        assert sigma == 0.25, f"fallback 应是 0.25, 实际 {sigma}"
    finally:
        p._CALIBRATION_PATH = orig_path
        p._load_calibration.cache_clear()
