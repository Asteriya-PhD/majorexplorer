"""
生成符合湖北新高考 3+1+2 规律的样本数据。
仅用于 MVP 原型,生产前必须替换为真实数据。
"""
import random
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent
random.seed(42)
np.random.seed(42)


# ──────────────────────────────────────────────
# 1. 一分一段表生成
# ──────────────────────────────────────────────
# 湖北新高考: 物理类 + 历史类
# 锚点参考(2024 湖北物理类大致真实分布):
#   700+  ≈  100 人  (700分约对应 100 位次)
#   600   ≈  14000
#   580   ≈  27000
#   525 (一本线) ≈ 85000
#   400   ≈ 170000
#   200   ≈ 235000
# 物理类考生总数 ≈ 25万,历史类 ≈ 18万

# 锚点(从公开数据 + 经验): 分数 -> 位次
# 2024 湖北 物理类 大致真实分布
PHYSICS_ANCHORS_2024 = [
    (700, 100), (680, 250), (660, 800), (650, 1500),
    (640, 2800), (630, 4500), (620, 7000), (610, 10000), (600, 14000),
    (590, 19500), (580, 27000), (570, 36000), (560, 47000), (550, 60000),
    (540, 74000), (530, 88000), (525, 95000), (520, 103000), (510, 118000),
    (500, 132000), (490, 145000), (480, 158000), (470, 170000), (460, 180000),
    (450, 190000), (440, 198000), (430, 205000), (420, 211000), (410, 216000),
    (400, 220000), (380, 228000), (360, 233000), (340, 237000), (320, 240000),
    (300, 242000), (250, 245000), (200, 247000), (150, 248000),
]
# 2024 湖北 历史类
HISTORY_ANCHORS_2024 = [
    (680, 50), (660, 200), (650, 500), (640, 1000), (630, 1800), (620, 3000),
    (610, 4500), (600, 6500), (590, 9000), (580, 12500), (570, 17000),
    (560, 22000), (550, 28000), (540, 34000), (530, 41000), (520, 48000),
    (510, 55000), (500, 62000), (490, 70000), (480, 78000), (470, 86000),
    (460, 94000), (450, 102000), (440, 109000), (430, 116000), (420, 122000),
    (410, 128000), (400, 133000), (380, 142000), (360, 150000), (340, 156000),
    (320, 161000), (300, 165000), (250, 171000), (200, 175000), (150, 177000),
]


def interpolate_rank(score: int, anchors: list[tuple[int, int]]) -> int:
    """根据锚点 (score, rank) 表做线性插值
    score 超出范围返回边界值
    """
    if score >= anchors[0][0]:
        return anchors[0][1]
    if score <= anchors[-1][0]:
        return anchors[-1][1]
    # 找区间
    for i in range(len(anchors) - 1):
        s_hi, r_hi = anchors[i]
        s_lo, r_lo = anchors[i + 1]
        if s_lo <= score <= s_hi:
            # 线性插值
            if s_hi == s_lo:
                return r_hi
            t = (score - s_lo) / (s_hi - s_lo)
            return int(r_lo + t * (r_hi - r_lo))
    return anchors[-1][1]


def gen_rank_table(subject: str, year: int) -> pd.DataFrame:
    """生成一分一段表 DataFrame: columns=[score, rank, count]"""
    # 选基准年锚点 (用 2024 作为基准)
    if subject == "物理":
        anchors = PHYSICS_ANCHORS_2024
    else:
        anchors = HISTORY_ANCHORS_2024

    # 跨年微调: 每年考生人数 +3% / -2% 浮动
    year_shift = (year - 2024) * 0.03
    anchors = [(s, int(r * (1 + year_shift))) for s, r in anchors]

    scores = list(range(150, 701 if subject == "物理" else 681))
    ranks = [interpolate_rank(s, anchors) for s in scores]
    # 加 ±2% 随机扰动,看起来真实
    ranks = [max(1, int(r * random.uniform(0.98, 1.02))) for r in ranks]
    # 保证严格递减
    for i in range(1, len(ranks)):
        if ranks[i] >= ranks[i - 1]:
            ranks[i] = ranks[i - 1] - 1

    # 累计转 count
    counts = [ranks[0]] + [max(1, ranks[i - 1] - ranks[i]) for i in range(1, len(ranks))]
    return pd.DataFrame({"score": scores, "rank": ranks, "count": counts})


# ──────────────────────────────────────────────
# 2. 院校专业组投档表生成
# ──────────────────────────────────────────────
# 湖北热门招生院校(含本省 985/211 + 省外热门)
SCHOOLS = [
    # (校名, 类型, 层次分数基准, 在湖北是否招生)
    ("武汉大学", "985", 640, True, 100),
    ("华中科技大学", "985", 638, True, 120),
    ("中南财经政法大学", "211", 600, True, 80),
    ("华中师范大学", "211", 590, True, 90),
    ("武汉理工大学", "211", 580, True, 150),
    ("华中农业大学", "211", 570, True, 100),
    ("中国地质大学(武汉)", "211", 575, True, 80),
    ("中南民族大学", "普通", 540, True, 60),
    ("湖北大学", "普通", 535, True, 120),
    ("武汉科技大学", "普通", 540, True, 200),
    ("三峡大学", "普通", 510, True, 80),
    ("长江大学", "普通", 500, True, 150),
    ("武汉工程大学", "普通", 520, True, 100),
    ("湖北工业大学", "普通", 525, True, 120),
    ("武汉纺织大学", "普通", 500, True, 60),
    ("江汉大学", "普通", 495, True, 80),
    ("武汉商学院", "普通", 480, True, 40),
    ("黄冈师范学院", "普通", 470, True, 30),
    # 省外 985
    ("北京大学", "985", 695, True, 5),
    ("清华大学", "985", 698, True, 8),
    ("复旦大学", "985", 680, True, 15),
    ("上海交通大学", "985", 685, True, 20),
    ("浙江大学", "985", 675, True, 25),
    ("中国科学技术大学", "985", 670, True, 10),
    ("南京大学", "985", 670, True, 15),
    ("中国人民大学", "985", 675, True, 8),
    ("北京航空航天大学", "985", 665, True, 30),
    ("同济大学", "985", 655, True, 20),
    ("东南大学", "985", 650, True, 30),
    ("武汉大学(国家专项)", "985", 630, True, 30),
    ("南开大学", "985", 655, True, 15),
    ("天津大学", "985", 650, True, 25),
    ("中山大学", "985", 635, True, 40),
    ("华南理工大学", "985", 630, True, 50),
    ("厦门大学", "985", 635, True, 20),
    ("山东大学", "985", 615, True, 60),
    ("四川大学", "985", 620, True, 80),
    ("重庆大学", "985", 615, True, 50),
    ("中南大学", "985", 615, True, 80),
    ("湖南大学", "985", 610, True, 60),
    ("西北工业大学", "985", 630, True, 30),
    ("西安交通大学", "985", 645, True, 25),
    ("哈尔滨工业大学", "985", 645, True, 30),
    ("大连理工大学", "985", 625, True, 40),
    ("东北大学", "985", 600, True, 50),
    ("吉林大学", "985", 605, True, 80),
    ("兰州大学", "985", 595, True, 30),
    # 省外 211
    ("北京邮电大学", "211", 645, True, 20),
    ("中央财经大学", "211", 640, True, 15),
    ("对外经济贸易大学", "211", 640, True, 10),
    ("北京外国语大学", "211", 635, True, 8),
    ("中国政法大学", "211", 640, True, 10),
    ("上海财经大学", "211", 625, True, 15),
    ("华东理工大学", "211", 605, True, 40),
    ("东华大学", "211", 580, True, 30),
    ("上海大学", "211", 600, True, 50),
    ("苏州大学", "211", 605, True, 30),
    ("南京理工大学", "211", 605, True, 40),
    ("南京航空航天大学", "211", 615, True, 30),
    ("河海大学", "211", 595, True, 50),
    ("江南大学", "211", 580, True, 40),
    ("南京师范大学", "211", 590, True, 20),
    ("南京农业大学", "211", 580, True, 30),
    ("中国矿业大学", "211", 575, True, 50),
    ("华中农业大学(中外合作)", "211", 555, True, 20),
    ("华中师范大学(国家专项)", "211", 580, True, 30),
    ("中南财经政法大学(中外合作)", "211", 580, True, 15),
    ("中国地质大学(武汉)(中外合作)", "211", 565, True, 15),
    ("武汉理工大学(中外合作)", "211", 570, True, 20),
    ("华中科技大学(中外合作)", "985", 615, True, 15),
    ("武汉大学(中外合作)", "985", 620, True, 10),
    # 省外 普通一本
    ("深圳大学", "普通", 605, True, 50),
    ("广州大学", "普通", 575, True, 50),
    ("广东工业大学", "普通", 555, True, 60),
    ("杭州电子科技大学", "普通", 590, True, 60),
    ("浙江工业大学", "普通", 575, True, 50),
    ("南京邮电大学", "普通", 595, True, 50),
    ("重庆邮电大学", "普通", 580, True, 60),
    ("西安邮电大学", "普通", 565, True, 50),
    ("长沙理工大学", "普通", 565, True, 80),
    ("湘潭大学", "普通", 555, True, 100),
    ("湖北经济学院", "普通", 490, True, 60),
    ("武汉轻工大学", "普通", 495, True, 50),
    ("武汉理工大学(国家专项)", "211", 570, True, 30),
    # 压线保底院校
    ("武汉学院", "普通", 470, True, 50),
    ("武昌首义学院", "普通", 460, True, 60),
    ("湖北经济学院(中外合作)", "普通", 460, True, 20),
    ("武汉城市学院", "普通", 450, True, 40),
    ("武汉东湖学院", "普通", 455, True, 40),
    ("湖北工程学院新技术学院", "普通", 445, True, 30),
    # 专科
    ("武汉职业技术学院", "专科", 420, True, 200),
    ("武汉船舶职业技术学院", "专科", 415, True, 150),
    ("湖北职业技术学院", "专科", 410, True, 200),
    ("黄冈职业技术学院", "专科", 405, True, 150),
]

# 选科要求模板(简化为 4 类: 不限 / 物+化 / 物理 / 历史)
XUANKE_TEMPLATES = [
    ("不限", "01", []),  # (display, code, required_subjects)
    ("物理", "02", ["物理"]),
    ("物理+化学", "03", ["物理", "化学"]),
    ("历史", "04", ["历史"]),
    ("物理+化学+生物", "05", ["物理", "化学", "生物"]),
    ("物理+地理", "06", ["物理", "地理"]),
    ("物理+化学/生物", "07", ["物理", "化学", "生物"]),  # 二选一
    ("物理+化学/地理", "08", ["物理", "化学", "地理"]),
]


def gen_admission_table(subject: str, year: int) -> pd.DataFrame:
    """生成院校专业组投档表 DataFrame
    columns: [year, subject, school_name, school_type, group_code, xuanke_req,
              xuanke_subjects, plan_count, min_score, min_rank, est_proba, tuition_yuan, city]
    """
    # 决定 985/211 校在 985 类中,普通本科压线,分数基准不同
    rows = []
    rank_table = gen_rank_table(subject, year)

    def score_to_rank(s: int) -> int:
        # 找最近分数
        idx = (rank_table["score"] - s).abs().idxmin()
        return int(rank_table.iloc[idx]["rank"])

    for school, stype, base_score, _, plan in SCHOOLS:
        # 每年 3-5 个专业组
        n_groups = random.randint(3, 5) if subject == "物理" else random.randint(2, 4)
        for g in range(n_groups):
            template = random.choice(XUANKE_TEMPLATES)
            xuanke_display, xuanke_code, xuanke_subjects = template
            # 不同专业组有不同分数(±15 分波动)
            offset = random.randint(-15, 15)
            min_score = max(150, base_score + offset + random.randint(-5, 5))
            min_rank = score_to_rank(min_score)
            # 招生计划(每年微调 ±10%)
            plan_count = max(1, int(plan * random.uniform(0.9, 1.1) / n_groups))
            # 城市
            city = "武汉" if school.startswith("武汉") or school.startswith("华中") or school.startswith("中南") or school.startswith("湖北") or school.startswith("黄冈") or school.startswith("三峡") or school.startswith("长江") or school.startswith("江汉") else random.choice(["北京", "上海", "南京", "杭州", "广州", "深圳", "天津", "西安", "成都", "重庆", "厦门", "长沙", "青岛", "大连", "哈尔滨", "沈阳", "兰州"])
            # 中外合作学费高
            tuition = random.randint(45000, 80000) if "中外合作" in school else random.randint(4500, 8000)

            rows.append({
                "year": year,
                "subject": subject,
                "school_name": school,
                "school_type": stype,
                "group_id": f"{school[:4]}{g+1:02d}",  # 简化 group_id
                "xuanke_req": xuanke_display,
                "xuanke_subjects": "|".join(xuanke_subjects) if xuanke_subjects else "",
                "plan_count": plan_count,
                "min_score": min_score,
                "min_rank": min_rank,
                "tuition_yuan": tuition,
                "city": city,
                "is_special": "是" if "中外合作" in school or "国家专项" in school or "提前批" in school else "否",
            })
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# 3. 主入口
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating 湖北 一分一段表 (2023-2025, 物理+历史)...")
    for year in [2023, 2024, 2025]:
        for subject in ["物理", "历史"]:
            rt = gen_rank_table(subject, year)
            path = DATA_DIR / f"hubei_rank_{subject}_{year}.csv"
            rt.to_csv(path, index=False)
            print(f"  ✓ {path.name} ({len(rt)} rows)")

    print("\nGenerating 湖北 院校专业组投档表 (2023-2025, 物理+历史)...")
    for year in [2023, 2024, 2025]:
        for subject in ["物理", "历史"]:
            at = gen_admission_table(subject, year)
            path = DATA_DIR / f"hubei_admission_{subject}_{year}.csv"
            at.to_csv(path, index=False)
            print(f"  ✓ {path.name} ({len(at)} rows)")

    print("\n✅ All sample data generated.")
    print("⚠️  These are NOT real Hubei data. Replace with 湖北省教育考试院 official data before production.")
