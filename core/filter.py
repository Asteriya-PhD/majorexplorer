"""
core/filter.py — 三级硬过滤:选科 + 体检 + 招生计划存在性

支持 3+1+2 (湖北/广东/江苏等 8 省) 和 3+3 (京/沪/津/浙/鲁/琼) 两种高考模式。
"""
import pandas as pd
from .data_loader import load_admission_table
from typing import Iterable


# 3+3 省份清单
PROVINCES_3_PLUS_3 = {"beijing", "北京", "shanghai", "上海",
                      "tianjin", "天津", "zhejiang", "浙江",
                      "shandong", "山东", "hainan", "海南"}
# 3+1+2 省份
PROVINCES_3_PLUS_1_PLUS_2 = {"hubei", "湖北", "guangdong", "广东",
                              "jiangsu", "江苏", "hunan", "湖南",
                              "hebei", "河北", "chongqing", "重庆",
                              "liaoning", "辽宁", "fujian", "福建"}

# 6 选科 subject
ALL_SUBJECTS = {"物理", "化学", "生物", "地理", "政治", "历史"}
SUBJECT_ALIAS = {"物": "物理", "化": "化学", "生": "生物",
                 "地": "地理", "政": "政治", "历": "历史"}


def get_xuanke_mode(province: str) -> str:
    """3+1+2 or 3+3"""
    if province in PROVINCES_3_PLUS_3:
        return "3+3"
    if province in PROVINCES_3_PLUS_1_PLUS_2:
        return "3+1+2"
    return "3+1+2"  # default


def parse_xuanke(xuanke_str: str, mode: str = "3+1+2") -> dict:
    """解析选科组合

    Args:
        xuanke_str: 如 "物+化+生" / "历+政+地" / "物+" / "历+" / "化+生+地" (3+3)
        mode: "3+1+2" 或 "3+3"
    Returns:
        3+1+2: {首选: '物理' or '历史', 再选: ['化学', '生物']}
        3+3:   {选考: ['物理', '化学', '生物']}
    """
    parts = [SUBJECT_ALIAS.get(p.strip(), p.strip()) for p in xuanke_str.split("+") if p.strip()]
    parts = [p for p in parts if p in ALL_SUBJECTS]
    if not parts:
        return {"首选": None, "再选": []} if mode == "3+1+2" else {"选考": []}

    if mode == "3+3":
        return {"选考": parts}

    # 3+1+2: 第一个必须是 物 or 历(首选),后面是再选
    first = parts[0] if parts[0] in ("物理", "历史") else None
    rest = [p for p in parts[1:] if p in ("化学", "生物", "地理", "政治")]
    return {"首选": first, "再选": rest}


def match_xuanke(student_xuanke: str, required_subjects: str, mode: str = "3+1+2") -> bool:
    """判断学生选科是否满足专业组要求

    3+1+2 (湖北):
        首选 物理/历史 必须 match
        再选 是"或"关系(任选其一即可)
        "不限": 任何选科都可报
    3+3 (京/沪/津/浙):
        学生选 3 门,专业组要求通常为 "选考 XX,YY" (任选其一) 或 "选考 XX+YY" (必须都有)
        "不限": 任何选科都可报
    """
    req = str(required_subjects or "").strip()
    if not req or req in ("", "nan", "None"):
        return True
    if "不限" in req or "无要求" in req:
        return True

    if mode == "3+3":
        return _match_xuanke_3_plus_3(student_xuanke, req)
    return _match_xuanke_3_plus_1_plus_2(student_xuanke, req)


def _match_xuanke_3_plus_1_plus_2(student_xuanke: str, required_subjects: str) -> bool:
    req = str(required_subjects).strip()
    # 不限 任何选科都可报
    if "不限" in req or "无要求" in req or req in ("", "nan", "None"):
        return True
    s = parse_xuanke(student_xuanke, "3+1+2")
    if not s["首选"]:
        return False
    required = [x.strip() for x in req.split("|") if x.strip()]
    if not required:
        return True
    first_required = required[0]
    if s["首选"] not in first_required:
        return False
    if len(required) == 1:
        return True
    if not s["再选"]:
        return False
    rest_required = required[1:]
    return any(sub in rest_required for sub in s["再选"])


def _match_xuanke_3_plus_3(student_xuanke: str, required_subjects: str) -> bool:
    """3+3 选科匹配

    院校要求格式示例:
        "物理,化学"     - 选考 物理 或 化学 (任一)
        "物理+化学"     - 必须选 物理 和 化学
        "物理,化学+生物" - 选考 (物理 或 化学) 且 选了生物
        "不限"          - 任何选科
    """
    s = parse_xuanke(student_xuanke, "3+3")
    if not s["选考"]:
        return False
    student_subjects = set(s["选考"])
    req = str(required_subjects).strip()
    if "不限" in req or "无要求" in req or "无" == req:
        return True
    # split by + into clauses; each clause can be ,-separated OR
    clauses = [c.strip() for c in req.replace("或", ",").split("+") if c.strip()]
    for clause in clauses:
        # each clause = OR of subjects; need at least one in student
        options = [o.strip() for o in clause.split(",") if o.strip()]
        # Normalize: 物 → 物理 etc
        options = [SUBJECT_ALIAS.get(o, o) for o in options]
        if not any(opt in student_subjects for opt in options):
            return False
    return True


def check_medical_constraints(ti_eye: dict, school_special: str, xuanke_req: str) -> tuple[bool, str]:
    """检查体检/身体条件限制"""
    if ti_eye.get("色盲") == "色盲":
        if any(k in school_special for k in ["医", "生", "化", "公安"]):
            return False, "色盲考生不能报医学/生物/化学/公安类"
    if ti_eye.get("色盲") == "色弱":
        if any(k in school_special for k in ["医", "化"]) and "医学" in school_special:
            return False, "色弱考生部分医学专业受限"
    vision = ti_eye.get("视力", 5.0)
    if vision < 4.8 and "公安" in school_special:
        return False, "公安类要求裸眼视力 ≥ 4.8"
    return True, ""


def filter_schools(
    df: pd.DataFrame,
    student_xuanke: str,
    ti_eye: dict = None,
    max_tuition: int = None,
    province: str = "hubei",
) -> pd.DataFrame:
    """对院校专业组表做硬过滤

    Args:
        df: 投档表
        student_xuanke: 学生选科
        ti_eye: 体检限制
        max_tuition: 最高学费(元/年), None = 不限
        province: 省份(决定 3+1+2 vs 3+3 模式)
    Returns:
        过滤后的 DataFrame
    """
    if ti_eye is None:
        ti_eye = {"色盲": "无", "视力": 5.0, "身高_cm": 170}

    mode = get_xuanke_mode(province)

    # 1. 选科过滤
    mask = df.apply(
        lambda r: match_xuanke(student_xuanke, str(r.get("xuanke_subjects", "")), mode),
        axis=1
    )
    df = df[mask].copy()

    # 2. 体检过滤
    def _ti_check(row):
        ok, _ = check_medical_constraints(ti_eye, str(row.get("school_name", "")), str(row.get("xuanke_req", "")))
        return ok
    mask = df.apply(_ti_check, axis=1)
    df = df[mask].copy()

    # 3. 学费过滤
    if max_tuition is not None:
        df = df[df["tuition_yuan"] <= max_tuition]

    return df.reset_index(drop=True)


def get_all_xuanke_options_3_plus_3() -> list[str]:
    """3+3 模式 20 种选科组合 (从 6 选 3 = C(6,3) = 20)"""
    from itertools import combinations
    subs = ["物", "化", "生", "地", "政", "历"]
    return ["+".join(c) for c in combinations(subs, 3)]


def get_all_xuanke_options_3_plus_1_plus_2() -> list[str]:
    """3+1+2 模式 12 种选科组合"""
    return [
        "物+化+生", "物+化+地", "物+化+政", "物+化+",
        "物+生+地", "物+生+政", "物+生+",
        "物+地+政", "物+地+", "物+政+",
        "物+",
        "历+政+地", "历+政+生", "历+政+",
        "历+地+生", "历+地+",
        "历+生+",
        "历+",
    ]
