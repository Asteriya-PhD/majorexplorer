"""
tests/test_filter.py — core/filter.py 单元测试

覆盖:
- filter_schools 三级过滤: 选科 + 体检 + 学费
- match_xuanke 3+1+2 模式: 首选 + 再选
- match_xuanke "不限" 短路
- check_medical_constraints: 色盲/视力
- get_xuanke_mode 省份判定
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.filter import (  # noqa: E402
    filter_schools, match_xuanke, parse_xuanke, check_medical_constraints,
    get_xuanke_mode,
)


def _make_df(rows: list[dict]) -> pd.DataFrame:
    """构造测试用 投档表 (最少必要列)."""
    base = {
        "school_name": "测试大学", "school_type": "985", "group_id": "01",
        "xuanke_req": "不限", "xuanke_subjects": "不限",
        "plan_count": 30, "min_score": 600, "min_rank": 10000,
        "tuition_yuan": 5500, "city": "北京", "is_special": "否",
    }
    out = []
    for r in rows:
        row = {**base, **r}
        out.append(row)
    return pd.DataFrame(out)


# ───────────── match_xuanke 3+1+2 ─────────────


@pytest.mark.parametrize("student,req,expected", [
    # 不限: 任何选科都可
    ("物+化+生", "不限", True),
    ("物+化+生", "", True),
    ("历+政+地", "不限", True),
    # 3+1+2 数据格式: `|` 分隔 OR, e.g. "物理|化学" = 首选物理(再选化学)
    ("物+化+生", "物理|化学", True),     # 首选物理 in "物理|化学"
    ("物+化+生", "物理|生物", True),     # 首选物理 in "物理|生物"
    ("物+化+生", "物理", True),          # 单组 物理
    ("历+政+地", "物理|化学", False),    # 首选历 ∉ "物理|化学"
    ("物+化+生", "历史|化学", False),    # 首选物 ∉ "历史|化学"
])
def test_match_xuanke_3_plus_1_plus_2(student: str, req: str, expected: bool):
    """3+1+2 模式 选科匹配: 首选必须 match (in req 的第一组 `|` 分隔 token).

    数据格式约定: xuanke_subjects 字段用 `|` 分隔多组 OR 选项, 每组第一个 subject
    是 3+1+2 的 首选. filter 限定: 首选必须在第一组的 token 中.
    """
    actual = match_xuanke(student, req, mode="3+1+2")
    assert actual == expected, f"学生={student} req={req!r} 期望 {expected} 实际 {actual}"


def test_match_xuanke_unlimited_short_circuits():
    """不限 / 空 任何选科都可报 (短路)."""
    for s in ["物+化+生", "历+政+地", "物+", "历+"]:
        for req in ["不限", "", "无要求"]:
            assert match_xuanke(s, req, mode="3+1+2"), f"学生={s} req={req} 应通过"


# ───────────── get_xuanke_mode ─────────────


@pytest.mark.parametrize("province,expected", [
    ("hubei", "3+1+2"), ("湖北", "3+1+2"),
    ("guangdong", "3+1+2"), ("江苏", "3+1+2"),
    ("beijing", "3+3"), ("上海", "3+3"),
    ("浙江", "3+3"), ("山东", "3+3"),
    ("unknown", "3+1+2"),  # default
])
def test_get_xuanke_mode(province: str, expected: str):
    """省份 → 选科模式 (3+3 vs 3+1+2)."""
    assert get_xuanke_mode(province) == expected


# ───────────── check_medical_constraints ─────────────


def test_colorblind_blocks_medical():
    """色盲考生 报医学院 → 拒绝."""
    ok, msg = check_medical_constraints(
        {"色盲": "色盲", "视力": 5.0}, "北京大学医学部", "物理+化学"
    )
    assert ok is False
    assert "色盲" in msg


def test_colorblind_allows_non_medical():
    """色盲考生 报非医学院 → 允许."""
    ok, msg = check_medical_constraints(
        {"色盲": "色盲", "视力": 5.0}, "清华大学计算机", "物理+化学"
    )
    assert ok is True
    assert msg == ""


def test_low_vision_blocks_public_security():
    """视力 < 4.8 报公安类 → 拒绝."""
    ok, msg = check_medical_constraints(
        {"色盲": "无", "视力": 4.5}, "中国人民公安大学", "不限"
    )
    assert ok is False
    assert "视力" in msg


def test_normal_vision_passes():
    """正常体检 → 所有都通过."""
    ok, msg = check_medical_constraints(
        {"色盲": "无", "视力": 5.0}, "北京大学医学部", "物理+化学"
    )
    assert ok is True
    assert msg == ""


# ───────────── filter_schools 集成 ─────────────


def test_filter_schools_xuanke_blocks_wrong_subject():
    """filter_schools: 物+化+生 报 历史+政治 校 → 全部过滤."""
    df = _make_df([
        {"school_name": "X 大学 物理组", "xuanke_subjects": "物理+化学", "group_id": "01"},
        {"school_name": "Y 大学 历史组", "xuanke_subjects": "历史+政治", "group_id": "02"},
    ])
    out = filter_schools(df, student_xuanke="物+化+生")
    assert len(out) == 1
    assert out.iloc[0]["school_name"] == "X 大学 物理组"


def test_filter_schools_tuition_cap():
    """filter_schools: max_tuition=10000 滤掉高费校."""
    df = _make_df([
        {"school_name": "A 公立", "tuition_yuan": 5500, "group_id": "01"},
        {"school_name": "B 中外合办", "tuition_yuan": 58000, "group_id": "02"},
    ])
    out = filter_schools(df, student_xuanke="物+化+生", max_tuition=10000)
    assert len(out) == 1
    assert out.iloc[0]["school_name"] == "A 公立"


def test_filter_schools_colorblind_blocks_medical():
    """filter_schools: 色盲学生 滤掉医学院."""
    df = _make_df([
        {"school_name": "北京大学医学部", "group_id": "01"},
        {"school_name": "清华大学计算机", "group_id": "02"},
    ])
    out = filter_schools(
        df, student_xuanke="物+化+生",
        ti_eye={"色盲": "色盲", "视力": 5.0, "身高_cm": 170},
    )
    assert len(out) == 1
    assert out.iloc[0]["school_name"] == "清华大学计算机"


def test_filter_schools_all_three_filters_compose():
    """filter_schools: 选科 + 体检 + 学费 三级一起工作."""
    df = _make_df([
        # 通过选科, 通过体检, 学费 OK
        {"school_name": "A 物理 计算机", "xuanke_subjects": "物理+化学",
         "tuition_yuan": 5500, "group_id": "01"},
        # 通过选科, 但学费高
        {"school_name": "B 物理 中外合办", "xuanke_subjects": "物理+化学",
         "tuition_yuan": 58000, "group_id": "02"},
        # 选科不 match
        {"school_name": "C 历史 文学", "xuanke_subjects": "历史+政治",
         "tuition_yuan": 5500, "group_id": "03"},
    ])
    out = filter_schools(df, student_xuanke="物+化+生", max_tuition=10000)
    assert len(out) == 1
    assert out.iloc[0]["school_name"] == "A 物理 计算机"
