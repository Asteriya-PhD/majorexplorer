"""
synth/test_validator.py — validator 单测.

跑: cd <project_root> && python -m pytest scf/synth/test_validator.py -v
或: python scf/synth/test_validator.py
"""
import json
import sys
from pathlib import Path

# 让 import 找得到 scf 包
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "gaokao-major-explorer" / "scripts"))
sys.path.insert(0, str(ROOT))

from scf.synth.validator import validate, score_quality, format_for_retry, VALID_STYLES


# ── 完整 60-精品样本: anesthesiology.json (从 curated 目录) ──
SAMPLE_PATH = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated" / "anesthesiology.json"


def test_sample_passes():
    """60 精品样板 anesthesiology.json 应校验通过."""
    data = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    ok, errors, warnings = validate(data)
    assert ok, f"60 精品样本校验失败:\n{format_for_retry(errors, warnings)}"
    print(f"✅ anesthesiology.json: ok={ok}, errors={len(errors)}, warnings={len(warnings)}")
    qs = score_quality(data)
    print(f"   quality_score = {qs['quality_score']}")
    assert qs["quality_score"] >= 0.7, f"60 精品质量分应 ≥0.7, 实际 {qs['quality_score']}"


def test_minimal_valid_synth():
    """最小合规样本 (LLM 一次过的目标输出)."""
    minimal = {
        "slug": "insurance",
        "title": "保险学",
        "category": "经济学 · 金融学类",
        "style": "finance",
        "degree": "经济学学士",
        "duration_years": 4,
        "tags": ["精算", "稳定", "考证", "央企"],
        "difficulty": "★★★★☆",
        "updated_at": "2026-06",
        "data_source": "Web 搜索综合",
        "summary": "保险学是金融学的精算 + 风控分支, 对接银行/保险/资管三大去向, 精算师门槛高但天花板高。",
        "curriculum": {
            "公共必修": [
                {"name": "高等数学 A", "credit": "5"},
                {"name": "大学英语", "credit": "4"},
                {"name": "思政", "credit": "3"},
            ],
            "通用专业核心": [
                {"name": "保险学原理", "credit": "4"},
                {"name": "概率论", "credit": "4"},
                {"name": "计量经济学", "credit": "3"},
            ],
            "5 校特色选修": [
                {"name": "精算实务", "credit": "3"},
                {"name": "再保险", "credit": "2"},
                {"name": "风险管理", "credit": "3"},
            ],
        },
        "top_schools": [
            {"name": "中央财经大学", "tag": "211"},
            {"name": "西南财经大学", "tag": "211"},
            {"name": "对外经济贸易大学", "tag": "211"},
            {"name": "中南财经政法大学", "tag": "211"},
            {"name": "东北财经大学", "tag": "双一流"},
        ],
        "salary": {
            "应届生": {"p25": 10, "p50": 15, "p75": 22, "yoy": 3},
            "3 年经验": {"p25": 18, "p50": 28, "p75": 40, "yoy": 5},
            "5 年经验": {"p25": 30, "p50": 50, "p75": 80, "yoy": 2},
        },
        "employment_direction": [
            {"name": "保险/精算", "pct": 35},
            {"name": "银行/资管", "pct": 25},
            {"name": "互联网金融", "pct": 20},
        ],
        "alumni_quotes": [
            {"year": "2019", "current": "中国人寿 · 精算师", "quote": "精算不是算术, 是概率 + 财务 + 监管的三角, 适合数学好且愿意坐得住的人。"},
            {"year": "2020", "current": "平安集团 · 风控", "quote": "保险学给我最大的礼物是把不确定性量化的能力, 跨界去任何金融子行业都吃得开。"},
        ],
        "xuanke_req_list": [
            {"name": "物理", "pct": 60},
            {"name": "不限", "pct": 40},
            {"name": "化学", "pct": 10},
        ],
    }
    ok, errors, warnings = validate(minimal)
    assert ok, f"最小合规样本校验失败:\n{format_for_retry(errors, warnings)}"
    qs = score_quality(minimal)
    assert qs["quality_score"] >= 0.6, f"最小样本质量分应 ≥0.6, 实际 {qs['quality_score']}"
    print(f"✅ minimal valid synth: ok={ok}, quality={qs['quality_score']}")


def test_missing_required_fails():
    """缺必填字段 → 失败."""
    broken = {"slug": "x", "title": "X"}
    ok, errors, warnings = validate(broken)
    assert not ok
    assert any("缺必填字段" in e for e in errors)
    assert any("缺强必填字段" in e for e in errors)
    print(f"✅ missing required → 失败 ({len(errors)} errors)")


def test_invalid_style_fails():
    """style 不在白名单 → 失败."""
    bad = {"slug": "x", "title": "X", "style": "unknown_style"}
    ok, errors, _ = validate(bad)
    assert not ok
    assert any("style 不合法" in e for e in errors)
    print("✅ invalid style → 失败")


def test_invalid_duration_fails():
    """duration_years 不是 4/5 → 失败."""
    bad = {"slug": "x", "title": "X", "duration_years": 3}
    ok, errors, _ = validate(bad)
    assert not ok
    assert any("duration_years" in e for e in errors)
    print("✅ invalid duration → 失败")


def test_curriculum_min_blocks():
    """curriculum <3 块 → 失败."""
    bad = {
        "slug": "x", "title": "X", "style": "cs", "curriculum": {
            "公共必修": [{"name": "高数", "credit": "5"}]
        }
    }
    ok, errors, _ = validate(bad)
    assert not ok
    assert any("curriculum 至少 3 块" in e for e in errors)
    print("✅ curriculum <3 块 → 失败")


def test_salary_p25_gt_p75_warns():
    """salary p25 > p75 异常 → 失败."""
    bad = {
        "slug": "x", "title": "X", "style": "finance",
        "salary": {"应届生": {"p25": 100, "p50": 50, "p75": 20, "yoy": 0}},
    }
    ok, errors, _ = validate(bad)
    assert not ok
    assert any("p25 > p75" in e for e in errors)
    print("✅ salary p25>p75 → 失败")


def test_high_salary_warns():
    """应届 P50 > 80 异常高 → warning."""
    bad = {
        "slug": "x", "title": "X", "style": "finance",
        "salary": {"应届生": {"p25": 60, "p50": 100, "p75": 150, "yoy": 0}},
    }
    ok, errors, warnings = validate(bad)
    assert any("异常高" in w for w in warnings), f"应有 warning, 实际 {warnings}"
    print(f"✅ 应届 P50 异常高 → warning ({len(warnings)} warnings)")


def test_hallucination_quote_p8_warns():
    """校友身份含 P8 → warning."""
    bad = {
        "slug": "x", "title": "X", "style": "cs",
        "alumni_quotes": [{"year": "2020", "current": "阿里 P8 · 架构师", "quote": "..."}],
    }
    ok, errors, warnings = validate(bad)
    assert any("P8" in w for w in warnings)
    print("✅ 校友高帽 → warning")


def test_top_schools_min_5():
    """top_schools <5 → 失败."""
    bad = {
        "slug": "x", "title": "X", "style": "cs",
        "top_schools": [{"name": "清华"}, {"name": "北大"}],
    }
    ok, errors, _ = validate(bad)
    assert not ok
    assert any("top_schools 至少 5" in e for e in errors)
    print("✅ top_schools <5 → 失败")


def test_overview_v2_optional_warning():
    """overview_v2 缺某些子项 → warning (非阻塞)."""
    bad = {
        "slug": "x", "title": "X", "style": "cs",
        "overview_v2": {
            "lede": "...",
            "what": {"foundations": ["a"]},  # <3
            "fit": {"yes": ["a"]},  # <3
        },
    }
    ok, errors, warnings = validate(bad)
    assert any("foundations" in w for w in warnings)
    print(f"✅ overview_v2 缺项 → warning (ok={ok})")


def test_valid_styles_count():
    """13 个合法 style."""
    assert len(VALID_STYLES) == 13
    assert "gongan" in VALID_STYLES and "business" in VALID_STYLES
    print(f"✅ VALID_STYLES = {len(VALID_STYLES)} 个")


# ── 直接跑 (不依赖 pytest) ──
def run_all():
    tests = [
        test_valid_styles_count,
        test_sample_passes,
        test_minimal_valid_synth,
        test_missing_required_fails,
        test_invalid_style_fails,
        test_invalid_duration_fails,
        test_curriculum_min_blocks,
        test_salary_p25_gt_p75_warns,
        test_high_salary_warns,
        test_hallucination_quote_p8_warns,
        test_top_schools_min_5,
        test_overview_v2_optional_warning,
    ]
    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"❌ {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"💥 {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n=== {passed} passed, {failed} failed ===")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
