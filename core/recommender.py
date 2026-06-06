"""
core/recommender.py — 96 志愿主流程

输入: 学生的位次 + 选科 + 体检 + 偏好
输出: 96 个志愿,分冲/稳/保
"""
from typing import Optional
import pandas as pd
from pydantic import BaseModel, Field

from .data_loader import load_admission_table
from .filter import filter_schools
from .probability import estimate_admission_probability


class RecommendRequest(BaseModel):
    """推荐请求"""
    province: str = Field("hubei", description="省份(拼音: hubei/guangdong/jiangsu/...)")
    rank: int = Field(..., description="全省位次 (1=第一名, 数字越小越好)")
    subject: str = Field(..., description="科类: 物理 or 历史")
    year: int = Field(2025, description="高考年份")
    xuanke: str = Field(..., description="选科组合, 如 '物+化+生'")
    ti_eye: dict = Field(default_factory=lambda: {"色盲": "无", "视力": 5.0, "身高_cm": 170})
    city_preference: Optional[list[str]] = Field(None, description="偏好城市列表, 如 ['武汉', '北京', '上海']")
    avoid_schools: Optional[list[str]] = Field(None, description="排除的院校")
    avoid_special: bool = Field(False, description="是否排除中外合作/国家专项等特殊类型")
    max_tuition: Optional[int] = Field(None, description="最高学费(元/年)")
    # 张雪峰式策略加权输入
    student_goal: Optional[str] = Field(None, description="学生目标: 考公/考研/就业/考编/稳定/兴趣")
    family_bg: Optional[str] = Field(None, description="家庭背景: 富裕/普通/困难")
    n_total: int = Field(96, description="总志愿数(默认 96)")
    n_chong: int = Field(32, description="冲档志愿数(默认 32)")
    n_wen: int = Field(32, description="稳档志愿数(默认 32)")
    n_bao: int = Field(32, description="保档志愿数(默认 32)")


class VolunteerItem(BaseModel):
    """单个志愿"""
    rank: int                                # 96 志愿中的序号
    school_name: str
    school_type: str
    group_id: str
    xuanke_req: str
    min_score: int
    min_rank_historical: dict                # 历年最低位次
    est_probability: float
    category: str                            # 冲/稳/保
    city: str
    tuition_yuan: int
    plan_count: int
    advice: str = ""                         # 简短建议
    strategy_note: str = ""                  # 张雪峰式策略建议(基于 student_goal + family_bg)


class RecommendResponse(BaseModel):
    """推荐响应"""
    student_summary: dict
    candidates_total: int                    # 过滤后候选总数
    volunteers: list[VolunteerItem]
    statistics: dict


def recommend(req: RecommendRequest) -> RecommendResponse:
    """主推荐函数"""

    # 1. 加载当年的投档表
    df = load_admission_table(req.province, req.subject, req.year)

    # 2. 硬过滤: 选科 + 体检 + 学费 + 排除校
    df = filter_schools(
        df,
        student_xuanke=req.xuanke,
        ti_eye=req.ti_eye,
        max_tuition=req.max_tuition,
    )

    if req.avoid_schools:
        df = df[~df["school_name"].isin(req.avoid_schools)]

    if req.avoid_special:
        df = df[df["is_special"] == "否"]

    if req.city_preference:
        # 不强制过滤,只是给偏好城市的项加分
        df = df.copy()
        df["_city_score"] = df["city"].apply(
            lambda c: 2 if c in req.city_preference else (1 if any(p in c for p in req.city_preference) else 0)
        )
    else:
        df = df.copy()
        df["_city_score"] = 0

    candidates_total = len(df)

    # 3. 对每个候选估算录取概率
    results = []
    for _, row in df.iterrows():
        prob_info = estimate_admission_probability(
            student_rank=req.rank,
            school_name=row["school_name"],
            group_id=row["group_id"],
            province=req.province,
            subject=req.subject,
        )
        # 跳过无历史数据的(避免全是 0.5 中概率)
        if prob_info.get("warning"):
            continue
        results.append({
            **row.to_dict(),
            "probability": prob_info["probability"],
            "category": prob_info["category"],
            "historical_ranks": prob_info["historical_ranks"],
            "median_rank": prob_info["median_rank"],
        })

    if not results:
        return RecommendResponse(
            student_summary={
                "province": req.province,
                "rank": req.rank,
                "subject": req.subject,
                "year": req.year,
                "xuanke": req.xuanke,
                "student_goal": req.student_goal,
                "family_bg": req.family_bg,
            },
            candidates_total=candidates_total,
            volunteers=[],
            statistics={"chong": 0, "wen": 0, "bao": 0, "total": 0,
                        "warning": "无候选院校,可能是选科/体检/学费过严,或数据缺失"},
        )

    results_df = pd.DataFrame(results)

    # 4. 排序: 城市偏好 > 学校层次 > 概率
    results_df["_layer_score"] = results_df["school_type"].map(
        {"985": 4, "211": 3, "普通": 2, "专科": 1}
    ).fillna(0)
    results_df["_rank_score"] = results_df["median_rank"]  # 位次越靠前越好(数字小)
    # 排序: 城市偏好 > 学校层次 > 概率
    # 学校层次是主要因素(985 > 211 > 普通),概率只做微调
    # 这样 北大 985 (0.73 prob) 不会被 不知名 985 (1.0 prob) 排到后面
    results_df["_sort_key"] = (
        results_df["_city_score"] * 100000    # 城市偏好 (大者优先)
        + results_df["_layer_score"] * 10000  # 学校层次 (大者优先,主导)
        + results_df["probability"] * 10      # 概率 (微调,不影响层次)
    )
    results_df = results_df.sort_values("_sort_key", ascending=False).reset_index(drop=True)

    # 5. 按冲稳保分组,每组取前 n 个
    chong_df = results_df[results_df["category"] == "冲"].head(req.n_chong)
    wen_df = results_df[results_df["category"] == "稳"].head(req.n_wen)
    bao_df = results_df[results_df["category"] == "保"].head(req.n_bao)

    # 6. 拼成 96 志愿(冲→稳→保)
    final = []
    seq = 0
    for df_part, cat_zh in [(chong_df, "冲"), (wen_df, "稳"), (bao_df, "保")]:
        for _, row in df_part.iterrows():
            seq += 1
            advice = _build_advice(row, cat_zh)
            strategy_note = _build_strategy_note(
                row, cat_zh,
                student_goal=req.student_goal,
                family_bg=req.family_bg,
            )
            final.append(VolunteerItem(
                rank=seq,
                school_name=row["school_name"],
                school_type=row["school_type"],
                group_id=str(row["group_id"]),
                xuanke_req=row["xuanke_req"],
                min_score=int(row["min_score"]),
                min_rank_historical=row["historical_ranks"],
                est_probability=float(row["probability"]),
                category=cat_zh,
                city=row["city"],
                tuition_yuan=int(row["tuition_yuan"]),
                plan_count=int(row["plan_count"]),
                advice=advice,
                strategy_note=strategy_note,
            ))

    return RecommendResponse(
        student_summary={
            "province": req.province,
            "rank": req.rank,
            "subject": req.subject,
            "year": req.year,
            "xuanke": req.xuanke,
            "student_goal": req.student_goal,
            "family_bg": req.family_bg,
        },
        candidates_total=candidates_total,
        volunteers=final,
        statistics={
            "chong": len(chong_df),
            "wen": len(wen_df),
            "bao": len(bao_df),
            "total": len(final),
        },
    )


def _build_advice(row, category: str) -> str:
    """生成单条志愿的简短建议"""
    bits = []
    if row["school_type"] == "985":
        bits.append("985 高校")
    elif row["school_type"] == "211":
        bits.append("211 高校")
    if "中外合作" in row["school_name"]:
        bits.append(f"学费 {int(row['tuition_yuan']/10000)}万/年,家境宽裕可考虑")
    if row["is_special"] == "是":
        bits.append("特殊类型,需核对招生章程")
    if category == "冲":
        bits.append("可冲一冲,但建议放后面")
    elif category == "保":
        bits.append("稳妥保底,建议服从调剂")
    return " · ".join(bits) if bits else "正常志愿"


def _build_strategy_note(row, category: str, student_goal: str = None, family_bg: str = None) -> str:
    """张雪峰式策略建议: 根据学生目标 + 家庭背景,生成针对性文字
    (不改变冲稳保分类,只影响建议文本)"""
    bits = []
    school = str(row.get("school_name", ""))
    school_type = str(row.get("school_type", ""))
    is_special = str(row.get("is_special", ""))
    tuition = int(row.get("tuition_yuan", 0) or 0)
    city = str(row.get("city", ""))

    if student_goal == "考公":
        if school_type in ("985", "211"):
            bits.append(f"985/211 考公选调优势大,{'985' if school_type=='985' else '211'}院校可参加央选/省选")
        elif school_type == "普通":
            bits.append("普通本科考公竞争激烈,建议同步准备省考/事业单位")
    elif student_goal == "就业":
        if school_type in ("985", "211"):
            bits.append("985/211 校招资源丰富,500 强宣讲密度高")
        else:
            bits.append("建议关注该校校企合作/实习基地")
    elif student_goal == "考研":
        if school_type in ("985", "211"):
            bits.append("保研率高,985/211 通常 15-30% 推免率")
        else:
            bits.append("该校需重点关注升学率,部分双非 5-10%")
    elif student_goal == "稳定":
        if any(k in school for k in ["师范", "医学", "电力", "地质"]):
            bits.append("稳定方向对口")
        elif school_type in ("985", "211"):
            bits.append("211 校招时体制内单位多")
    elif student_goal == "考编":
        if school_type in ("985", "211"):
            bits.append("可走定向选调/人才引进通道")
        else:
            bits.append("考编需关注该校师范类/医学类专业组")

    if family_bg == "困难":
        if tuition > 30000:
            bits.append(f"学费 {tuition/10000:.0f}万/年偏高,建议谨慎")
        if city not in ("武汉",) and category == "保":
            bits.append("异地保底需考虑生活成本")

    return " · ".join(bits)
