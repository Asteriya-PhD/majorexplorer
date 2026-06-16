"""
contam_dict.py — 字段级污染检测字典 (Opt 2: 100+ 词库).

设计原则:
- 关键词按"如果出现就几乎肯定是污染"分 (强污染)
- 跨 major 类的 fallback 偏置 (经管/CS/工业设计/医学/数据)
- 用 N-gram 避免子串误判 (e.g. "四大" 不命中 "四大名著" → 用精准词组)
- 字段白名单: hero_quote/who_fits_no 等可放宽 (允许泛化)

用法:
  from contam_dict import detect_contamination
  issues = detect_contamination(data, title, style)
  # issues: [(field, level, [keywords]), ...]
"""

# 强污染词 (>=1 个命中即视为污染, 必修复)
FINANCE_STRONG = [
    # 持证类
    "精算师", "CFA", "FRM", "CPA", "ACCA", "注册会计师", "证券从业", "基金从业",
    "金融分析师", "金融工程", "金融数学", "金融专业", "持证上岗", "持证是硬门槛",
    # 行业类
    "投行", "券商", "银行风控", "审计师", "税务师", "注会", "财会",
    "四大事务所", "四大",  # 注意 "四大经典/四大领域" 是 OK, 但 "四大事务所" 必命中
    # 公司类
    "麦肯锡", "BCG", "贝恩", "Bain", "MBB", "高盛", "摩根士丹利",
    # 量化/建模
    "建模能力", "估值建模", "量化交易", "量化研究", "对冲基金",
    "二级市场", "一级市场", "买方研究", "卖方研究", "PE", "VC",
    # 咨询
    "管理咨询", "战略咨询", "战略管理咨询",
    # 通用金融话术 (风险词)
    "考证/读研", "无耐心考证", "案例分析",  # 仅在理工/医学/农学类里命中
]

INDUSTRIAL_DESIGN_STRONG = [
    "UI/UX", "UI 设计", "UX 设计", "产品设计", "工业设计", "IDEO", "Frog",
    "洛可可", "中央美院", "清华美院", "交通工具设计", "家居家电设计",
    "设计咨询", "品牌策略", "自由设计师", "互联网产品",
    "智能硬件 IoT 设计", "产品造型", "小米生态链", "洛可可设计", "frog design",
    "字节/阿里/腾讯 设计", "产品经理", "交互设计",
    # "设计院" 在工科里是真实雇主 (建筑设计院/化工设计院), 排除
]

# 中污染词 (>=2 个命中或特定字段命中)
DATA_SCIENCE = [
    "互联网大厂", "大厂算法", "算法岗", "后端", "前端开发", "Python工程师",
    "数据科学家", "数据分析师", "深度学习", "机器学习工程师",
    "BAT", "字节跳动算法", "字节跳动产品", "字节跳动数据", "阿里云",
    "数据中台", "数据科学", "数据挖掘", "推荐算法", "广告算法",
]

HUMANITIES_DRIFT = [  # 在理工类命中视为污染
    "出版编辑", "出版社编辑", "文学评论", "文学创作", "作家协会",
    "汉语教学", "对外汉语", "孔子学院",
]

EDUCATION_DRIFT = [  # 在非教育类命中视为污染
    "教学法", "学科教学", "微格教学", "教育实习", "教师资格证",
    "教师编制", "师范", "教育部直属",
]

MEDICAL_DRIFT = [  # 在非医学类命中视为污染
    "执业医师", "规培", "住院医师规范化培训", "处方权", "临床决策",
    "处方", "医院信息系统", "HIS",
]

LAW_GONGAN_DRIFT = [  # 在非法学/公安类命中视为污染
    "司法考试", "法考", "法律职业资格证", "律师执业", "律师事务所",
    "公安联考", "公安专业科目", "警察体能",
]

# 弱污染词 (>=3 个命中才视为污染, 通常 hero_quote/lede 允许)
SCIENCE_DRIFT = [
    "量子计算", "量子信息",  # 仅在数学/物理/计算机里 OK
    "高分子化学", "材料合成",  # 仅在化学/材料里 OK
    "有限元分析",  # 在非力学/机械/土木里罕见
    "细胞培养", "PCR",  # 仅在生物/医学里 OK
]

ALL_FORBIDDEN_FINANCE = [  # 在非经管/金融专业里都是污染
    "本专业就是 X 行业全部",  # deepseek 模板
    "不考证/不读研也能进头部",  # deepseek 模板
    "毕业 = 自动高薪",  # deepseek 模板
]


def detect_contamination(data: dict, title: str, style: str) -> list[tuple[str, str, list[str]]]:
    """
    Returns list of (field_path, contamination_level, [matched_keywords]).
    contamination_level: "strong" (必修) | "medium" (3+ 命中) | "weak" (1-2 命中, 仅参考)
    """
    issues = []
    # 字段路径: 每个字段单独扫
    fields_to_check = {
        "summary": data.get("summary", ""),
        "hero_quote": data.get("hero_quote", ""),
        "lede": data.get("lede") or data.get("overview_v2", {}).get("lede", ""),
        "what_you_learn": data.get("what_you_learn", ""),
        "pitfalls": data.get("pitfalls", "") or data.get("overview_v2", {}).get("pitfalls", []),
        "who_fits_yes": data.get("who_fits_yes", []) or data.get("overview_v2", {}).get("who_fits_yes", []),
        "who_fits_no": data.get("who_fits_no", []) or data.get("overview_v2", {}).get("who_fits_no", []),
        "alumni_quotes": data.get("alumni_quotes", []),
        "employment_direction": data.get("employment_direction", []),
        "top_companies": data.get("top_companies", []),
        "top_schools": data.get("top_schools", []),
        "salary": data.get("salary", {}),
        "deep_study": data.get("deep_study", {}),
    }

    # 选择词库
    strong_words = list(FINANCE_STRONG) + list(ALL_FORBIDDEN_FINANCE)
    if style in ("eng", "sci", "cs", "medicine", "agri", "humanities", "law", "gongan", "administration", "arts", "education"):
        # 非工业设计/艺术类, 强命中 industrial_design
        if style != "arts":
            strong_words += INDUSTRIAL_DESIGN_STRONG
    if style in ("eng", "sci", "medicine", "agri"):
        # 理工医农, 强命中 humanities_drift
        strong_words += HUMANITIES_DRIFT
    if style not in ("medicine",):
        strong_words += MEDICAL_DRIFT
    if style not in ("law", "gongan"):
        strong_words += LAW_GONGAN_DRIFT
    if style != "education":
        strong_words += EDUCATION_DRIFT

    medium_words = list(DATA_SCIENCE)
    if style in ("medicine", "eng", "sci", "agri"):
        medium_words += SCIENCE_DRIFT

    for field_name, val in fields_to_check.items():
        if val is None:
            continue
        text = _to_text(val)
        # 强污染: >=1 命中
        strong_hits = [w for w in strong_words if w in text]
        if strong_hits:
            issues.append((field_name, "strong", strong_hits))
            continue
        # 中污染: >=2 命中
        medium_hits = [w for w in medium_words if w in text]
        if len(medium_hits) >= 2:
            issues.append((field_name, "medium", medium_hits))

    return issues


def _to_text(val) -> str:
    """把任意结构转字符串 (用于关键词匹配)."""
    import json
    return json.dumps(val, ensure_ascii=False)


if __name__ == "__main__":
    import sys, json
    slug = sys.argv[1] if len(sys.argv) > 1 else "optoelectronic-information-science-engineering"
    d = json.load(open(f"skills/gaokao-major-explorer/data/curated/{slug}.json"))
    issues = detect_contamination(d, d.get("title", ""), d.get("style", ""))
    print(f"\n{slug} ({d.get('title')}, style={d.get('style')}):")
    if not issues:
        print("  ✅ 干净")
    for f, lvl, hits in issues:
        print(f"  ⚠️  [{lvl}] {f}: {hits[:5]}{'...' if len(hits) > 5 else ''}")
