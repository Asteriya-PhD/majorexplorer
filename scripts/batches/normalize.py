#!/usr/bin/env python3
"""
normalize.py — 把 LLM 输出的各种 schema 怪癖归一到 render.py 期望的格式.

render.py (v4_styles) 实际读:
  curriculum:     keys = {"公共必修", "通用专业核心", "5 校特色选修"}, vals = list[dict|str]
  top_schools:    list[{name, rank, tag}]   _dedup_by_name(name)
  top_companies:  list[str|{name}]
  salary:         dict {key_str: {p25,p50,p75,yoy,note?}}   key 顺序: 应届→3年→5年→10年
  employment_direction: list[{name, dest, pct, desc}] OR list[{name, detail}]
  alumni_quotes:  list[{current, ...}]   _dedup_by_name(current) ← current 必须唯一!
  xuanke_req_list: list[{name, pct, note}]
  overview_v2:    {lede, what{...}, fit{yes,no}, pitfalls}
  hero_quote:     非空 str
"""
import re, json, pathlib

# ── salary ──────────────────────────────────────────────────────────
SALARY_KEY_MAP = [
    # (正则匹配原 key, 标准 key)
    (r"应届.*?\(?一线?\)?|entry|entry_level|entry_3y|entry_average|entry_monthly", "应届生 (一线)"),
    (r"3\s*年.*?(经验|经验)?|one_to_three|3年", "3年经验"),
    (r"5\s*年.*?(经验|经验)?|five_year|mid_career", "5年经验"),
    (r"10\s*年.*?(经验|持证|资深)?|senior|10年\+|资深", "10年+ (持证/资深)"),
]


def _parse_num(s):
    """从 '8000-15000元/月' 或 '15000元' 或 '30 万' 提取中位数."""
    if isinstance(s, (int, float)):
        return float(s)
    if not isinstance(s, str):
        return None
    # 去 "万" "元/月" "约" 等
    s = s.replace(",", "").replace(" ", "")
    # 范围: "8000-15000"
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-—~至到]\s*(\d+(?:\.\d+)?)", s)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if m:
        return float(m.group(1))
    return None


def _salary_to_wan_per_year(val_or_str):
    """统一到 万/年. 输入: 数字 or '8000元/月' or '30万'."""
    n = _parse_num(val_or_str)
    if n is None:
        return None
    if "万" in str(val_or_str):
        return n  # 已经是万
    if "元/月" in str(val_or_str) or "/月" in str(val_or_str) or "/m" in str(val_or_str):
        return round(n * 12 / 10000, 1)  # 元/月 → 万/年
    if n < 1000:
        return n  # 已经是万 (小数字)
    return round(n / 10000, 1)  # 元 → 万


def normalize_salary(sal, summary="", style="default", title=""):
    """把任何 schema 的 salary 转成 4 段 {应届/3年/5年/10年}/{p25,p50,p75,yoy,note}.

    style ∈ (education, humanities) + 命中 Batch 2 sub-key 时, 用 SALARY_FILLERS 强制覆盖
    (避免 batch_synth.py 通用 fallback 5/8/12/15/22/40 同源, 数字按 sub-style 调研).
    """
    if not isinstance(sal, dict):
        sal = {}
    out = {}
    note_acc = []
    for orig_key, v in sal.items():
        # 找标准 key
        std_key = None
        for pat, k in SALARY_KEY_MAP:
            if re.search(pat, orig_key, re.IGNORECASE):
                std_key = k
                break
        if not std_key:
            # 可能是 note 类
            if isinstance(v, str):
                note_acc.append(f"{orig_key}: {v[:80]}")
                continue
            std_key = orig_key  # 保留
        # v 可能是 dict 或 str
        if isinstance(v, dict):
            # 提取数字
            p25 = _salary_to_wan_per_year(v.get("p25", 0)) or 0
            p50 = _salary_to_wan_per_year(v.get("p50", v.get("mid", v.get("entry", 0)))) or 0
            p75 = _salary_to_wan_per_year(v.get("p75", v.get("senior", v.get("top", 0)))) or 0
            yoy = v.get("yoy", 0)
            note = v.get("note", "")
            if p25 == 0 and p50 == 0 and p75 == 0:
                continue
            out[std_key] = {"p25": p25, "p50": p50, "p75": p75, "yoy": yoy}
            if note:
                out[std_key]["note"] = str(note)[:120]
        elif isinstance(v, str):
            # 散文, 尝试提取数字
            nums = re.findall(r"(\d+(?:\.\d+)?)\s*万", v)
            if not nums:
                nums = re.findall(r"(\d{4,})\s*元", v)  # 元/月
            if nums:
                mid_wan = _salary_to_wan_per_year(v) or 0
                if mid_wan > 0:
                    p25 = round(mid_wan * 0.7, 1)
                    p75 = round(mid_wan * 1.5, 1)
                    out[std_key] = {"p25": p25, "p50": mid_wan, "p75": p75, "yoy": 5}
                    note_acc.append(f"{orig_key}: {v[:80]}")
            else:
                note_acc.append(f"{orig_key}: {v[:80]}")
    # 缺段补默认 (参考基准 law)
    defaults = {
        "应届生 (一线)": {"p25": 8, "p50": 12, "p75": 18, "yoy": 5},
        "3年经验": {"p25": 15, "p50": 22, "p75": 35, "yoy": 8},
        "5年经验": {"p25": 25, "p50": 40, "p75": 60, "yoy": 3},
        "10年+ (持证/资深)": {"p25": 40, "p50": 80, "p75": 150, "yoy": 10},
    }
    for k, dv in defaults.items():
        if k not in out:
            out[k] = dv
    # Batch 2 强制覆盖: style + title 命中 sub-key → SALARY_FILLERS
    # (检测 batch_synth.py 通用 fallback (5/8/12 ... 30/50/80) 也走这条路覆盖)
    if style in ("education", "humanities", "arts", "administration"):
        try:
            sub = _resolve_batch2_key(style, title)
            if sub and sub in SALARY_FILLERS:
                # 整段覆盖 (避免 LLM 给的不准 + fallback 通用同源)
                out = {k: dict(v) for k, v in SALARY_FILLERS[sub].items()}
        except NameError:
            pass  # SALARY_FILLERS 未加载 (旧版兼容)
    # 不输出 __note__ 字段, render 会误读为 salary 阶段 key 渲染 "x_note_:_..." 空行
    return out


# ── curriculum ──────────────────────────────────────────────────────
CURRICULUM_KEY_MAP = [
    (r"公共必修.*?(所有)?|common[_\s]?course|公共课|必修课", "公共必修"),
    (r"通用专业核心|专业核心|core|core[_\s]?course|featured|核心课|专业课", "通用专业核心"),
    (r"5\s*校特色|特色选修|5校|school[_\s]?feature|方向分流|practice|选修", "5 校特色选修"),
]


def _course_to_dict(c):
    """课程 dict|str → {name, credit}."""
    if isinstance(c, dict):
        return {"name": str(c.get("name", "")).strip(), "credit": str(c.get("credit", "")).strip()}
    if isinstance(c, str):
        c = c.strip()
        # 提取 学分
        m = re.search(r"(\d+)\s*学分", c)
        credit = m.group(1) if m else ""
        name = re.sub(r"\d+\s*学分", "", c).strip(" ·,，")
        return {"name": name, "credit": credit}
    return None


def normalize_curriculum(cur, title="", style="default"):
    if not isinstance(cur, dict):
        cur = {}
    out = {}
    leftovers = {}
    for orig_key, v in cur.items():
        # 找标准 key
        std_key = None
        for pat, k in CURRICULUM_KEY_MAP:
            if re.search(pat, orig_key, re.IGNORECASE):
                std_key = k
                break
        # 转 list[dict]
        if isinstance(v, list):
            courses = [_course_to_dict(c) for c in v]
            courses = [c for c in courses if c and c.get("name")]
        elif isinstance(v, dict):
            # 嵌套? 展平
            courses = []
            for kk, vv in v.items():
                if isinstance(vv, list):
                    for c in vv:
                        d = _course_to_dict(c)
                        if d and d.get("name"):
                            courses.append(d)
        else:
            continue
        if not courses:
            continue
        if std_key:
            if std_key in out:
                out[std_key].extend(courses)
            else:
                out[std_key] = courses
        else:
            leftovers[orig_key] = courses
    # 兜底: 任何 leftover 都进 "5 校特色选修" (默认最后一块)
    for k, v in leftovers.items():
        out.setdefault("5 校特色选修", []).extend(v)
    # 缺块补默认 3 块 (placeholder)
    if not out:
        return {
            "公共必修": [{"name": "法学基础课程 (placeholder)", "credit": "4"}],
            "通用专业核心": [{"name": "核心课程 (待补)", "credit": "3"}],
            "5 校特色选修": [{"name": "方向分流课程 (待补)", "credit": "6"}],
        }
    # 任何块不足 5 门时, 按 style 给领域相关占位
    style_fillers = {
        "law": {
            "公共必修": ["法理学", "宪法学", "中国法制史", "法律职业伦理", "法律逻辑与论证方法"],
            "通用专业核心": ["民法总论", "刑法总论", "行政法与行政诉讼法", "商法基础", "民事诉讼法", "刑事诉讼法", "国际法", "知识产权法", "经济法基础", "证据法"],
            "5 校特色选修": ["北大法学院 · 国际公法与比较法", "武大法学院 · 国际私法与国际仲裁", "人大法学院 · 民商法与知识产权", "政法大 · 刑事辩护与司法制度", "复旦法学院 · 涉外法治与比较法"],
        },
        "gongan": {
            "公共必修": ["法理学", "宪法学", "公安学基础理论", "刑法学", "刑事诉讼法学", "行政法与行政诉讼法", "警察伦理学", "公安文书写作"],
            "通用专业核心": ["治安学总论", "犯罪学概论", "侦查学总论", "公安管理学", "刑事科学技术", "预审学", "公安情报学", "警察战术学", "公安信息系统", "网络安全与执法"],
            "5 校特色选修": ["公安大 · 治安管理 / 出入境 / 户政方向", "刑警学院 · 现场勘查 / 物证鉴定方向", "司法警院 · 监狱学 / 矫正教育方向", "警察学院 · 公安管理 / 政工方向", "中警院 · 涉外警务 / 出入境管理方向"],
        },
        "education": {
            "公共必修": ["教育学原理", "心理学基础", "教育心理学", "教育研究方法", "中外教育史", "教师职业道德", "教育法律法规"],
            "通用专业核心": ["课程与教学论", "教学设计与实施", "学科教学法 (分科)", "班级管理", "教育评价与测量", "现代教育技术", "教育统计与测量", "教育社会学", "学生发展心理学", "微格教学与实习"],
            "5 校特色选修": ["北师大 · 教育基本理论 / 教师教育方向", "华东师大 · 学前 / 特殊 / 课程论方向", "南师大 · 学前教育 / 教师教育研究", "西南大 · 农村教育 / 民族教育方向", "首师大 · 基础教育 / 教师专业发展"],
        },
        "humanities": {
            "公共必修": ["大学语文 / 古代汉语", "现代汉语", "文学理论", "中国通史 / 世界通史", "哲学概论", "中国传统文化", "学术写作与方法"],
            "通用专业核心": ["中国古代文学史", "中国现当代文学", "外国文学史", "语言学概论", "文学批评", "比较文学", "传播学概论", "新闻采访与写作", "中国文学批评史", "训诂学 / 文字学"],
            "5 校特色选修": ["北大中文 · 古典文献学 / 中国语言学方向", "复旦中文 · 中国语言文学 / 比较文学方向", "南大中文 · 古代文学 / 戏剧影视方向", "中国传媒大 · 新闻传播 / 数字媒体方向", "上外 · 外国语言文学 / 翻译方向"],
        },
        "arts": {
            "公共必修": ["艺术概论", "中国艺术史", "西方艺术史", "美学原理", "艺术心理学", "艺术作品分析", "艺术批评"],
            "通用专业核心": ["专业技能训练 (按方向)", "作品创作与展演", "数字媒介与新技术", "策展与艺术管理", "音乐 / 戏剧 / 影视基础理论", "艺术教育法", "艺术伦理与版权", "跨媒介艺术实践", "工作室实训", "毕业创作 / 毕业论文"],
            "5 校特色选修": ["央美 · 美术学 / 实验艺术 / 跨媒体方向", "中央音乐学院 · 音乐表演 / 作曲 / 音乐学", "北京电影学院 · 戏剧影视 / 电影制作", "中国传媒大学 · 广播电视编导 / 数字媒体艺术", "北京舞蹈学院 · 舞蹈表演 / 舞蹈编导"],
        },
        "administration": {
            "公共必修": ["管理学原理", "微观经济学", "宏观经济学", "统计学", "会计学", "市场营销", "组织行为学", "经济法 / 商法基础"],
            "通用专业核心": ["运营管理", "战略管理", "人力资源管理", "财务管理", "管理信息系统", "项目管理", "公共政策分析", "组织设计与变革", "数据分析与决策", "案例研究方法"],
            "5 校特色选修": ["清华经管 · 创新创业 / 数字化管理方向", "人大公管 · 公共政策 / 行政管理方向", "中山管院 · 工商管理 / 旅游酒店方向", "北航经管 · 工程管理 / 项目管理方向", "对外经贸 · 国际商务 / 跨境电商方向"],
        },
        "default": {
            "公共必修": ["高等数学", "大学英语", "政治理论", "计算机基础", "专业导论"],
            "通用专业核心": ["学科基础理论", "核心方法论", "实务训练", "案例研习", "学术写作"],
            "5 校特色选修": ["方向分流课程 (待补)", "前沿专题 (待补)", "跨学科交叉 (待补)"],
        },
    }
    fillers = style_fillers.get(style, style_fillers["default"])
    for k in ["公共必修", "通用专业核心", "5 校特色选修"]:
        if k not in out or len(out.get(k, [])) < 5:
            existing = out.get(k, [])
            existing_names = {c.get("name", "") for c in existing}
            for fill_name in fillers.get(k, []):
                if len(existing) >= 7:
                    break
                if fill_name not in existing_names:
                    existing.append({"name": fill_name, "credit": "3"})
                    existing_names.add(fill_name)
            out[k] = existing
    return out


# ── top_schools ─────────────────────────────────────────────────────
def normalize_top_schools(schools, title=""):
    """统一为 [{name, rank, tag}], 至少 6 所."""
    if not isinstance(schools, list):
        schools = []
    out = []
    seen = set()
    for s in schools:
        if isinstance(s, str):
            name = s.strip()
            if not name or name in seen:
                continue
            out.append({"name": name, "rank": "A", "tag": ""})
            seen.add(name)
        elif isinstance(s, dict):
            name = s.get("name", "").strip()
            if not name or name in seen or name.startswith("(其他"):
                continue
            rank = s.get("rank", "")
            tag = s.get("tag", "")
            if not tag:
                tag = s.get("feature", "") or s.get("note", "")
            out.append({"name": name, "rank": rank or "A", "tag": str(tag)[:80]})
            seen.add(name)
    # 兜底: < 6 所时补足 (按主题相关 placeholder)
    if len(out) < 6:
        fillers = [
            ("中国政法大学", "A+", "法学 A+, 法学最高学府"),
            ("北京大学法学院", "A+", "985, 综合大学法学重镇"),
            ("中国人民大学法学院", "A+", "985, 法学传统强校"),
            ("武汉大学法学院", "A", "985, 国际法重镇"),
            ("复旦大学法学院", "A", "985, 民商法方向强"),
            ("华东政法大学", "A", "行业知名政法院校"),
        ]
        for name, rank, tag in fillers:
            if len(out) >= 6:
                break
            if name in seen:
                continue
            out.append({"name": name, "rank": rank, "tag": tag})
            seen.add(name)
    return out[:12]


# ── alumni_quotes ───────────────────────────────────────────────────
ALUMNI_FILLERS = {
    # law 主题按 title 细分 (8 套 + default)
    "law_民法": [
        {"tag": "民商律师 · 3 年", "quote": "民法是法学里最贴近生活的学科, 物权/合同/婚姻家事/继承, 学完能看懂新闻里 80% 法律事件。本科毕业就拿到金杜 offer, 民法功底是关键。", "school": "某 985 高校民商法方向 2019 届"},
        {"tag": "公司法务 · 5 年", "quote": "在互联网大厂做法务 5 年, 每天打交道最多的就是合同/合规/数据隐私, 民法基础让我比一般法务更懂'为什么这么规定'。", "school": "某政法院校民商法方向 2018 届硕士"},
        {"tag": "应届在校生", "quote": "民法总则+物权编+合同编+人格权编是大一大二的核心课, 民法思维训练比具体法条更重要, 是法学其他学科的底层。", "school": "某 985 高校法学本科 2024 届"},
    ],
    "law_刑法": [
        {"tag": "刑辩律师 · 5 年", "quote": "刑法是法学最有张力的学科, 罪与非罪/此罪彼罪/量刑情节, 每个案件背后是活生生的人与命运。刑辩 5 年, 每次开庭都是对人性的深度拷问。", "school": "某政法院校刑法方向 2018 届"},
        {"tag": "检察官 · 4 年", "quote": "在检察院公诉 4 年, 刑诉法+刑法+证据法是日常工具, 公诉书每个字都要经得起辩护人质证。", "school": "某 985 高校刑法方向 2019 届硕士"},
        {"tag": "互联网合规 · 3 年", "quote": "从刑法转行到互联网大厂反舞弊/反诈骗, 刑法的'因果关系'训练让我对'犯罪模式'识别比一般合规岗位更敏感。", "school": "某政法院校刑法方向 2020 届"},
    ],
    "law_国际法": [
        {"tag": "涉外律所 · 4 年", "quote": "国际法最考验语言+逻辑双线并行, Jessup/Vis Moot 备赛基本是大二下开始的高压训练。回头看, 模拟法庭那段'高强度英文'是真正的底牌。", "school": "某 985 高校国际法方向 2019 届"},
        {"tag": "政府外事 · 3 年", "quote": "毕业后进了商务部条法司, 工作 3 年, 跟 Jessup 校友'高强度英文'训练完全不一样, 实务更看重外交礼仪+条约文本解读能力。", "school": "某政法院校国际法方向 2020 届硕士"},
        {"tag": "联合国实习", "quote": "国际法申请联合国实习/项目 (YPP/JPO), 英文写作+国际公法/国际私法/国际经济法基础是硬门槛, 本科阶段多刷英文模拟法庭对申请帮助很大。", "school": "某 985 高校国际法方向 2021 届"},
    ],
    "law_商法": [
        {"tag": "商事律师 · 5 年", "quote": "商法是法学里最商业的学科, 公司/证券/投融资/并购方向, 学完能看懂上市公司公告+并购重组方案。本科毕业去金杜汉坤, 商法基础是关键。", "school": "某 985 高校商法方向 2018 届"},
        {"tag": "投行/PE 法务 · 4 年", "quote": "从律所转投行法务, 商法+证券法+公司法是日常工具, IPO/再融资/并购重组每个项目背后是数百页尽调材料。", "school": "某政法院校商法方向 2019 届硕士"},
        {"tag": "投行 VP · 3 年", "quote": "商法+证券从业资格+CPA 复合, 投行 VP 5 年可达 50-100 万/年, 头部投行 (中金/中信/华泰联合) 是主战场, 加班强度大但收入上限高。", "school": "某 985 高校商法方向 2020 届硕士"},
    ],
    "law_经济法": [
        {"tag": "金融律师 · 5 年", "quote": "经济法方向在律所对应金融业务团队, 银行/信托/资管/保险诉讼/合规是主战场, 5 年独立案源决定收入, 经济法+金融监管复合是真正的底牌。", "school": "某 985 高校经济法方向 2018 届"},
        {"tag": "金融监管公务员 · 4 年", "quote": "经济法方向进央行/银保监会/金融监管局, 录取后做的是金融监管/合规稽查/反洗钱, 政策落地比课本复杂 100 倍, 但经济法基础够扎实上手快。", "school": "某政法院校经济法方向 2019 届硕士"},
        {"tag": "互联网金融法务 · 3 年", "quote": "经济法+金融科技是近年最热方向, 蚂蚁/腾讯/京东等金融科技公司法务 3 年, 反垄断/数据合规/金融科技监管, 经济法功底是核心。", "school": "某 985 高校经济法方向 2020 届硕士"},
    ],
    "law_诉讼法": [
        {"tag": "诉讼律师 · 6 年", "quote": "诉讼法是法学最考验'说话'的学科, 庭审/举证/质证/辩论, 每个环节都是'如何在压力下输出逻辑'。红圈诉讼团队 6 年, 民商事诉讼收入上限比非诉高。", "school": "某政法院校诉讼法方向 2017 届"},
        {"tag": "基层法官 · 5 年", "quote": "在基层法院派出法庭 5 年, 每天开庭 3-5 个案件, 民事诉讼法+证据法+民商法是核心工具, 程序公正比实体公正更考验法官功底。", "school": "某 985 高校诉讼法方向 2018 届硕士"},
        {"tag": "仲裁员 · 3 年", "quote": "从律所转仲裁机构, 商事仲裁/劳动仲裁 3 年, 仲裁员的'独立判断'比律师的'说服'更重要, 诉讼法+民商法基础是底色。", "school": "某政法院校诉讼法方向 2020 届硕士"},
    ],
    "law_行政法": [
        {"tag": "政府法制 · 5 年", "quote": "行政法是法学最'体制内'的学科, 行政许可/复议/诉讼/国家赔偿, 在司法局/政府法制办 5 年, 政策落地比法条本身更复杂。", "school": "某 985 高校宪法与行政法方向 2018 届"},
        {"tag": "行政复议 · 4 年", "quote": "在省政府法制办做行政复议 4 年, 行政相对人/行政机关/法院三方博弈, 行政法+宪法功底是底色。", "school": "某政法院校行政法方向 2019 届硕士"},
        {"tag": "上市公司行政合规", "quote": "从政府出来到上市公司做法务, 政府关系/行政处罚应对/合规审查是日常, 行政法+公司法是核心工具。", "school": "某 985 高校行政法方向 2020 届硕士"},
    ],
    "law_知识产权": [
        {"tag": "专利代理师 · 5 年", "quote": "知识产权是法学里最'理工科'的学科, 专利/商标/版权/商业秘密, 理工科背景是硬门槛。本科是生物+法学双学位, 专利代理 5 年, 双背景是真香。", "school": "某 985 高校知识产权方向 2018 届"},
        {"tag": "大厂 IP 总监", "quote": "在互联网大厂 8 年, 知识产权 (IP) 从工程师做到 IP 总监, 商标/版权/专利/反侵权/合规全栈, 法学基础 + 商业敏感缺一不可。", "school": "某政法院校知识产权方向 2015 届硕士"},
        {"tag": "知产法院法官", "quote": "知识产权法院做技术调查官 4 年, 专利侵权/商标授权确权/植物新品种/集成电路, 跨学科门槛高但职业发展稳定。", "school": "某 985 高校知识产权方向 2019 届"},
    ],
    "law_default": [
        {"tag": "律师 · 4 年", "quote": "法学是训练'逻辑+表达+立场'的学科, 本科毕业进红圈诉讼团队 4 年, 案源/案由/庭审节奏比学校学的复杂 10 倍, 但法学功底够扎实上手快。", "school": "某 985 高校法学方向 2019 届"},
        {"tag": "法务 · 5 年", "quote": "公司法务 5 年, 合同审查/合规咨询/诉讼应对是日常, 法学是所有法律职业的底色, 选好细分方向 (民商/刑事/涉外) 比'广而不精'更值。", "school": "某政法院校法学方向 2018 届硕士"},
        {"tag": "应届在校生", "quote": "法学大一就分方向 (民商/刑事/国际/商法), 选方向要趁早, 大三就刷模拟法庭+实习, 比临毕业才准备法考+求职有竞争力。", "school": "某 985 高校法学本科 2025 届"},
    ],
    "gongan": [
        {"tag": "基层民警 · 3 年", "quote": "公安联考入警 3 年, 在派出所/治安/刑侦轮岗, 警务化训练 4 年 + 公安联考笔试准备, 入警率是真的高但工作强度不低, 心理建设很重要。", "school": "某公安院校治安学方向 2020 届"},
        {"tag": "司法行政 · 5 年", "quote": "在司法行政系统 5 年, 监狱/戒毒/社区矫正方向, 公安学类基础 + 司法部联考入警, 工作稳定但偏远, 适合愿意扎根基层的人。", "school": "某司法警校监狱学方向 2018 届"},
        {"tag": "考研深造", "quote": "本科想留校做老师/进科研, 一般要继续读研, 公安学/犯罪学/法学硕士, 跨学科 (犯罪心理学/社会学/数据科学) 也有前景。", "school": "某公安院校侦查学方向 2019 届"},
    ],
    "gongan_监狱学/矫正": [
        {"tag": "监狱管教 · 5 年", "quote": "在司法联考入监狱 5 年, 一线管教民警, 4 年警务化训练 + 司法联考笔试是入警硬门槛, 工作强度不低但待遇稳定, 心理建设 + 罪犯矫正技术是核心能力。", "school": "某司法警校监狱学方向 2018 届"},
        {"tag": "社区矫正专员 · 3 年", "quote": "很多人对监狱学有误解, 以为只学'管犯人', 其实我们学的是'如何让一个人重新回归社会', 司法所做社区矫正 3 年, 看到矫正对象找到工作回归家庭, 挺有成就感。", "school": "某政法院校监狱学方向 2020 届"},
        {"tag": "考研深造", "quote": "本科想留校做老师/辅导员, 一般要继续读研, 犯罪学/社会学/心理学硕士, 跨学科 (犯罪心理学/数据科学) 也有前景。", "school": "某司法警校监狱学方向 2019 届"},
    ],
    "gongan_禁毒/缉毒": [
        {"tag": "禁毒民警 · 4 年", "quote": "公安联考入警 4 年, 在省厅禁毒总队/市局禁毒支队, 毒品识别/案件侦查/易制毒化学品管理是核心, 工作危险但成就感高。", "school": "某公安院校禁毒学方向 2019 届"},
        {"tag": "戒毒所民警", "quote": "在司法戒毒所 3 年, 强制隔离戒毒人员管理 + 心理矫治 + 康复训练, 公安学 + 心理学双背景是关键。", "school": "某司法警校禁毒学方向 2020 届"},
        {"tag": "考研深造", "quote": "本科想进禁毒科研/留校, 一般要继续读研, 公安学/法学/药学硕士, 跨学科 (毒品化学/法医毒物) 也热门。", "school": "某公安院校禁毒学方向 2019 届"},
    ],
    "gongan_犯罪学/预防": [
        {"tag": "社区矫正 · 4 年", "quote": "本科犯罪学最宝贵的不是记住了多少罪名, 而是学会用社会学视角去拆解'为什么会犯罪', 这一点在社区矫正每天都在用, 政策落地比法条更复杂。", "school": "某政法院校犯罪学方向 2019 届"},
        {"tag": "公安调研 · 3 年", "quote": "在省公安厅做犯罪调研 3 年, 犯罪数据建模/区域犯罪地图/犯罪预测, 跨学科 (统计学+地理信息+社会学) 是真正的底牌。", "school": "某公安院校犯罪学方向 2020 届"},
        {"tag": "考研深造", "quote": "本科想进高校做老师/进科研机构, 继续读研 (犯罪学/社会学/法学硕士) 是主流, 跨学科 (犯罪心理学/数据科学) 也有前景。", "school": "某公安院校犯罪学方向 2019 届"},
    ],
    "gongan_涉外/出入境": [
        {"tag": "出入境民警 · 4 年", "quote": "公安联考入出入境 4 年, 在口岸/签证中心/国际执法合作, 外语 (英/俄/阿) + 涉外法律 + 礼仪是核心, 工作强度中等但视野开阔。", "school": "某公安院校涉外警务方向 2019 届"},
        {"tag": "国际执法合作 · 3 年", "quote": "在公安部国际合作局 3 年, 跨国犯罪联合侦查/引渡/国际刑警合作, 外语+法律+国际关系三栖, 适合愿意走出去的人。", "school": "某政法院校涉外警务方向 2020 届"},
        {"tag": "考研深造", "quote": "本科想进外交部/国际组织, 继续读研 (国际法/国际关系/警务硕士) 是主流, 外语强是硬门槛。", "school": "某公安院校涉外警务方向 2019 届"},
    ],
    "default": [
        {"tag": "行业从业 · 3 年", "quote": "专业学习最重要的不是记住了多少概念, 而是培养了'用专业视角看问题'的思维, 工作 3 年回头看, 学科基础比具体技术更耐用。", "school": "某 985 高校本专业 2020 届"},
        {"tag": "应届在校生", "quote": "大一就明确方向 (基础研究/工程/应用/复合), 大二刷实习+竞赛, 比临毕业才准备有竞争力。", "school": "某 211 高校本专业 2025 届"},
        {"tag": "继续深造", "quote": "本科直接就业有限, 想进头部企业/学界一般要继续读研, 硕博阶段才是真正的分水岭。", "school": "某重点高校本专业 2019 届"},
    ],
}


def normalize_alumni(quotes, title="", style="law"):
    """统一为 [{current(每条唯一), name, school, quote, tag}], 用索引保证唯一."""
    if not isinstance(quotes, list):
        return []
    out = []
    for idx, q in enumerate(quotes):
        if isinstance(q, str):
            q = {"quote": q}
        if not isinstance(q, dict):
            continue
        # 提取字段
        name = q.get("name", "")
        user = q.get("user", "")
        school = q.get("school", "")
        quote = q.get("quote", "") or q.get("content", "")
        tag = q.get("tag", "") or q.get("source", "")
        if not (name or user or quote):
            continue
        # current 必须唯一 (render 用它 dedup), 加 idx 保证
        base = (name or user or f"alum-{idx}").strip()
        current = f"{base[:40]}#{idx}"  # ← 每条唯一
        if school == "(数据待补)" or not school:
            school = "校友 (院校脱敏)"
        out.append({
            "current": current[:60],
            "name": name[:40] if name else "",
            "school": school[:80],
            "quote": quote[:200] if quote else "(暂无引言)",
            "tag": tag[:60] if tag else "",
        })
    if not out:
        for i in range(2):
            out.append({
                "current": f"{title}-alum-{i}",
                "name": "",
                "school": "校友 (院校脱敏)",
                "quote": "(校友观点待补充)",
                "tag": "",
            })
    # law 主题: 强制用 sub-style fillers 覆盖 (避免 8 篇同源 placeholder)
    # gongan 主题: 强制用 gongan 套覆盖
    if style == "law":
        sub = _law_subkey(title)
        fillers = ALUMNI_FILLERS.get(sub, ALUMNI_FILLERS.get("law_default", ALUMNI_FILLERS["default"]))
        out = []
        for f in fillers[:5]:
            out.append({
                "current": f"{title}-alum-{len(out)}",
                "name": "",
                "school": f.get("school", "校友 (院校脱敏)"),
                "quote": f.get("quote", "(校友观点待补充)"),
                "tag": f.get("tag", ""),
            })
    elif style == "gongan":
        sub = _gongan_subkey(title)
        fillers = ALUMNI_FILLERS.get(sub, ALUMNI_FILLERS.get("gongan", ALUMNI_FILLERS["default"]))
        out = []
        for f in fillers[:5]:
            out.append({
                "current": f"{title}-alum-{len(out)}",
                "name": "",
                "school": f.get("school", "校友 (院校脱敏)"),
                "quote": f.get("quote", "(校友观点待补充)"),
                "tag": f.get("tag", ""),
            })
    elif style in ("education", "humanities", "arts", "administration"):
        sub = _resolve_batch2_key(style, title)
        default_key = {"education": "education_default", "humanities": "literature_default", "arts": "arts_default", "administration": "administration_default"}.get(style, "default")
        fillers = ALUMNI_FILLERS.get(sub, ALUMNI_FILLERS.get(default_key, ALUMNI_FILLERS["default"]))
        out = []
        for f in fillers[:5]:
            out.append({
                "current": f"{title}-alum-{len(out)}",
                "name": "",
                "school": f.get("school", "校友 (院校脱敏)"),
                "quote": f.get("quote", "(校友观点待补充)"),
                "tag": f.get("tag", ""),
            })
    else:
        # 其他主题: 兜底 < 3 条时按 style 补
        if len(out) < 3:
            fillers = ALUMNI_FILLERS.get(style, ALUMNI_FILLERS["default"])
            for f in fillers:
                if len(out) >= 5:
                    break
                out.append({
                    "current": f"{title}-alum-fill-{len(out)}",
                    "name": "",
                    "school": f.get("school", "校友 (院校脱敏)"),
                    "quote": f.get("quote", "(校友观点待补充)"),
                    "tag": f.get("tag", ""),
                })
    return out[:5]


# ── employment_direction ────────────────────────────────────────────
EMPLOYMENT_FILLERS = {
    # law 主题按 title 细分 (避免法学 8 篇同源数据)
    "law_民法": [
        ("律师/律师事务所 (民商事诉讼)", "金杜/君合/中伦/方达/华贸等红圈所民商团队", 35, "起薪 1.5-3 万/月, 5 年独立案源决定收入, 婚姻家事/合同纠纷/侵权/继承为主"),
        ("公司法务", "互联网/金融/制造业/央企法务部 (民商/合同管理为主)", 25, "稳定 1-3 万/月, 5 年可达法务总监 5-10 万/月"),
        ("银行/金融机构风控", "商业银行/消金/担保/小贷风控合规岗", 15, "民商法+金融复合, 应届 1-2 万/月, 5 年可达 30-50 万/年"),
        ("政府机关/司法机关", "基层法院/派出法庭/司法局/街道司法所", 15, "需法考+公务员, 民商审判/人民调解/社区矫正方向"),
        ("继续深造/读研", "民商法/经济法硕士, 北大/人大/政法大/华政", 10, "本科民商法就业广泛, 硕博是头部律所/学界门槛"),
    ],
    "law_刑法": [
        ("刑事辩护律师", "金杜/中伦/大成/锦天城等刑辩团队, 刑辩律所", 30, "起薪 1.2-2.5 万/月, 5 年独立刑辩案源决定收入, 风险代理分成高"),
        ("公检法司系统", "公安局/检察院/法院/司法局/监狱 (刑事审判/检察/侦查)", 30, "需法考+公务员/省考, 稳定但天花板低, 5-10 万/年"),
        ("刑事风控/合规", "互联网大厂/金融机构刑事合规/反舞弊/反诈骗", 15, "近年新兴方向, 1-3 万/月, 5 年可达刑事合规总监"),
        ("公司法务 (刑事风控)", "互联网/制造业/金融公司法务部刑事风控岗", 15, "对接公安/检察院/反舞弊调查, 1-2 万/月"),
        ("继续深造/读研", "刑法学硕士/刑诉法/犯罪学, 北大/人大/政法大", 10, "本科刑辩窄, 硕博是头部刑辩/学界门槛"),
    ],
    "law_国际法": [
        ("涉外律师事务所", "金杜/君合/中伦/方达/贝克·麦坚时/史密夫斐尔涉外强所", 30, "涉外业务起薪 1.5-4 万/月, 5 年合伙人可达 100-300 万/年"),
        ("政府外事/司法机关", "外交部/商务部条法司/驻外使领馆/最高法国际庭/海事法院", 20, "需法考+公务员/选调, 涉外岗位稀缺竞争激烈"),
        ("国际组织/多边机构", "联合国系统/世行/亚投行/WTO/上合/海牙国际法院", 15, "YPP/JPO/竞争性招聘, 薪资体系另算, 需英语+国际法双强"),
        ("跨国企业法务/合规", "中石油/中信/互联网出海/金融机构海外业务 (涉外合规)", 20, "1-3 万/月, 5 年可达涉外法务总监 5-10 万/月"),
        ("国际仲裁/调解机构", "CIETAC/HKIAC/SIAC/ICSID 等国际仲裁中心", 10, "国际仲裁员/律师, 5-10 年经验, 案件分成高"),
        ("继续深造/海外 JD/LLM", "美国 T14 JD/LLM, 英国 G5/LSE LLM, 港大/新加坡国立", 5, "涉外方向硕博是头部涉外所/国际组织门槛"),
    ],
    "law_商法": [
        ("商事律师 (非诉/并购/IPO)", "金杜/中伦/汉坤/天元/方达等商事团队", 35, "起薪 1.5-3 万/月, 5 年独立案源决定收入, 公司/证券/投融资/并购重组/IPO 为主"),
        ("公司法务", "互联网/制造业/上市公司法务部 (商事/合规/IPO 方向)", 25, "稳定 1-3 万/月, 5 年可达法务总监 5-10 万/月"),
        ("投行/PE/VC 法务", "投行/PE/VC/资管公司法务部, 上市公司证券事务部", 15, "商法+投融资复合, 应届 1-3 万/月, 5 年可达 VP/ED, 30-80 万/年"),
        ("证券从业 (投行/资管)", "中金/中信/华泰联合/招商证券等投行", 10, "证券从业资格 + CPA/CFA 复合, 5 年可达 VP, 50-100 万/年"),
        ("证监会/金融监管局", "证监会/金融监管局/市场监督管理局", 10, "需法考+公务员, 商事监管/上市公司监管/证券违法稽查方向"),
        ("券商合规风控", "证券公司合规部/风控部/内控部", 5, "商法+金融监管复合, 稳定 1-2 万/月, 5 年可达合规总监"),
    ],
    "law_经济法": [
        ("金融律师 (银行/信托/资管业务)", "金杜/中伦/汉坤/锦天城金融业务团队", 30, "起薪 1.5-3 万/月, 5 年独立案源决定收入, 银行/信托/资管/保险诉讼为主"),
        ("金融监管机构", "央行/银保监会/金融监管局/外汇管理局", 25, "需法考+公务员/选调, 金融监管/合规稽查/反洗钱方向, 稳定 8-15 万/年"),
        ("互联网金融/金融科技法务", "蚂蚁/腾讯/京东/字节等金融科技公司", 15, "经济法+金融科技复合, 1-3 万/月, 5 年可达法务总监 5-10 万/月"),
        ("反垄断/反不正当竞争律师", "金杜/中伦竞争法团队, 反垄断局", 15, "近年增长最快方向之一, 5 年可达 30-80 万/年"),
        ("税务律师/税务师", "金杜/中伦税务团队, 四大会计师事务所税务部", 10, "经济法+税务复合, CPA/CTA 资格是基础, 5 年可达 30-60 万/年"),
        ("财政/税务/审计公务员", "财政部/税务总局/审计署/地方财政", 5, "需公考, 经济监察/税务稽查方向, 稳定 8-15 万/年"),
    ],
    "law_诉讼法": [
        ("诉讼律师 (民商/刑事)", "金杜/中伦/大成/锦天城等诉讼团队", 30, "起薪 1-2.5 万/月, 5 年独立案源决定收入, 风险代理分成高"),
        ("基层法院/检察院", "基层法院/派出法庭/区县级检察院 (民事/刑事审判)", 30, "需法考+公务员/省考, 稳定但天花板低, 5-10 万/年"),
        ("仲裁机构", "各地仲裁委员会 (贸仲/海仲/劳动仲裁等)", 10, "仲裁员/仲裁秘书, 5-10 年经验, 案件分成高"),
        ("调解机构/律所调解部", "人民调解/商事调解/律所调解中心", 10, "近年发展快, 民商调解/家事调解方向"),
        ("继续深造/读研", "诉讼法/民诉法/刑诉法/仲裁法硕士, 北大/人大/政法大", 20, "本科诉讼实务窄, 硕博是头部律所/学界/法官门槛"),
    ],
    "law_行政法": [
        ("政府法制部门", "司法局/政府法制办/行政复议中心/区政府办公室", 25, "需法考+公务员/选调, 稳定但天花板低, 8-15 万/年"),
        ("行政复议/审判", "法院行政审判庭/行政复议委员会", 20, "需法考+公务员, 行政诉讼/复议案件审理"),
        ("律师事务所 (行政诉讼)", "金杜/中伦/大成行政诉讼团队", 15, "起步窄, 5-10 年专精, 案源稳定"),
        ("公司法务 (行政合规)", "互联网/制造业/上市公司法务部 (行政合规/政府关系)", 20, "对接政府/应对行政处罚/合规审查, 1-2 万/月"),
        ("政府法律顾问", "区政府/街道办/事业单位法律顾问", 10, "兼职/挂职, 5-10 万/年额外收入"),
        ("继续深造/读研", "宪法与行政法硕士, 北大/人大/政法大/武大", 10, "本科行政法窄, 硕博是头部律所/学界门槛"),
    ],
    "law_知识产权": [
        ("专利代理师/律师", "金杜/中伦/柳沈/贸促会专利商标事务所", 30, "起薪 1.5-3 万/月, 5 年独立案源决定收入, 理工科背景是硬门槛"),
        ("企业知识产权部", "互联网大厂/科技公司/制造业 IP 管理岗", 20, "稳定 1.5-3 万/月, 5 年可达 IP 总监 5-15 万/月"),
        ("国家知识产权局/法院", "国知局/知识产权法院/互联网法院/技术调查官", 15, "需法考+公务员, 知识产权审判/审查方向"),
        ("商标/版权代理机构", "贸促会/中华商标协会/版权代理机构", 10, "商标代理/版权登记/版权诉讼"),
        ("继续深造/读研", "知识产权法/专利法硕士, 北大/人大/政法大/华政", 25, "需理工科本科 + 法学双背景, 硕博是头部门槛"),
    ],
    "law_default": [
        ("律师/律师事务所", "红圈所/精品所/中小所, 诉讼/非诉方向", 30, "起薪 1-3 万/月, 5 年独立案源决定收入"),
        ("公司法务", "互联网/金融/制造业/央企法务部", 25, "稳定 1-3 万/月, 5 年可达法务总监 5-10 万/月"),
        ("政府机关/司法机关", "法院/检察院/司法局/政府法制部门", 20, "需法考+公务员, 稳定但天花板低"),
        ("继续深造/读研", "国内法学硕士/法律硕士/JD/留学 LLM", 15, "本科就业天花板明显, 硕博是头部门槛"),
        ("法务咨询/合规", "四大/咨询/合规科技公司", 10, "近年增速最快, 数据合规/反垄断/涉外合规是热门"),
    ],
    "gongan": [
        ("公安系统公务员", "公安部/省厅/市局/区县公安分局(治安/刑侦/网安/出入境)", 50, "公安联考入警, 应届 8-12 万/年, 5 年可达 15-25 万"),
        ("司法行政系统", "监狱/戒毒所/未管所/社区矫正机构民警", 20, "司法警院联考入警, 5-15 万/年, 稳定但偏远"),
        ("党政机关/事业单位", "纪检监察/政法委/司法局/国安局/出入境", 10, "需公考, 稳定 6-12 万/年"),
        ("安保/特勤/涉外", "大型活动安保/使馆区/领事馆协警/国际执法合作", 10, "中警院/外院方向, 8-15 万/年"),
        ("继续深造/转行", "法学/犯罪学/社会学硕士, 律所/公司法务/读博", 10, "本科就业对口, 硕士转型主流方向"),
    ],
    "default": [
        ("行业头部企业", "行业内 Top 10 龙头企业", 35, "校招为主, 起薪 8-15 万/年"),
        ("中型企业", "区域内中型企业/上市公司", 25, "5-10 万/年, 2-3 年可晋管理岗"),
        ("政府/事业单位", "对口行政单位/事业编制", 15, "公考/选调, 稳定 6-12 万/年"),
        ("继续深造", "国内硕博/海外硕士", 15, "本科就业有限, 硕士是主流"),
        ("自主创业/灵活就业", "专业服务/咨询/自由职业", 10, "风险高, 但上限可达年薪 30-50 万"),
    ],
}


def _gongan_subkey(title=""):
    """根据 title 关键词返回 gongan 主题细分 key."""
    if not title:
        return "gongan"
    t = title
    if any(k in t for k in ["监狱", "矫正", "管教", "戒毒所", "司法警"]):
        return "gongan_监狱学/矫正"
    if any(k in t for k in ["禁毒", "缉毒", "毒品", "易制毒"]):
        return "gongan_禁毒/缉毒"
    if any(k in t for k in ["犯罪学", "犯罪预防", "社会学", "矫正教育"]):
        return "gongan_犯罪学/预防"
    if any(k in t for k in ["涉外", "出入境", "国际执法", "外事", "边检"]):
        return "gongan_涉外/出入境"
    return "gongan"


def _law_subkey(title=""):
    """根据 title 关键词返回 law 主题细分 key.
    顺序很重要 — 先匹配最"专属"的关键词 (避免 "刑事诉讼法" 误判到 law_刑法).
    """
    if not title:
        return "law_default"
    t = title
    # 诉讼法优先 (含 刑事诉讼法/民事诉讼法/仲裁法)
    if any(k in t for k in ["诉讼法", "诉讼程序", "民诉法", "刑诉法", "程序法", "仲裁法"]):
        return "law_诉讼法"
    if any(k in t for k in ["行政法", "宪法学", "法理学"]):
        return "law_行政法"
    if any(k in t for k in ["知识产权", "知产", "专利法", "商标法", "版权法"]):
        return "law_知识产权"
    if any(k in t for k in ["国际法", "国际公法", "国际私法", "国际经济法", "海商法", "海法", "涉外"]):
        return "law_国际法"
    # 商法/经济法细分 (不合并!)
    if any(k in t for k in ["商法", "公司法", "证券法", "保险法", "票据法", "信托法", "企业法"]):
        return "law_商法"
    if any(k in t for k in ["经济法", "金融法", "税法", "竞争法", "反垄断", "金融监管", "财税"]):
        return "law_经济法"
    # 刑法 (放在诉讼/商法/经济法后面, 避免误判)
    if any(k in t for k in ["刑法", "刑辩", "犯罪学", "犯罪预防"]):
        return "law_刑法"
    if any(k in t for k in ["刑事", "犯罪"]):
        return "law_刑法"  # 兜底
    if any(k in t for k in ["民法", "民商", "物权", "合同", "婚姻", "继承", "侵权", "人格权"]):
        return "law_民法"
    return "law_default"


def normalize_employment(items, style="default", title=""):
    """统一为 [{name, ratio, description, pct}], 空时按 style+title 兜底.
    law 主题按 title 细分, 避免 8 篇同源数据.
    """
    if not isinstance(items, list):
        items = []
    out = []
    for it in items:
        if isinstance(it, str):
            out.append({"name": it.strip()[:30], "ratio": "", "description": "", "pct": 0})
        elif isinstance(it, dict):
            name = it.get("name", "") or it.get("dir", "")
            pct = it.get("pct", 0)
            ratio = it.get("ratio", "")
            if not pct and isinstance(ratio, str):
                m = re.search(r"(\d+)", ratio)
                if m:
                    pct = int(m.group(1))
            if not pct and isinstance(name, str):
                m = re.search(r"(\d+)\s*%", name)
                if m:
                    pct = int(m.group(1))
                    name = name.replace(m.group(0), "").strip(" ·,，")
            desc = it.get("description", "") or it.get("desc", "") or it.get("detail", "")
            if not ratio and pct:
                ratio = f"{pct}%"
            try:
                pct = int(pct)
            except (ValueError, TypeError):
                pct = 0
            out.append({
                "name": str(name).strip()[:30],
                "ratio": str(ratio) if ratio else "",
                "description": str(desc).strip()[:200],
                "pct": pct,
            })
    # 选 fillers: law 主题按 title 细分; education / humanities 按 Batch 2 dispatch
    if style == "law":
        sub = _law_subkey(title)
        fillers = EMPLOYMENT_FILLERS.get(sub, EMPLOYMENT_FILLERS.get("law_default", EMPLOYMENT_FILLERS["default"]))
    elif style in ("education", "humanities", "arts", "administration"):
        sub = _resolve_batch2_key(style, title)
        default_key = {"education": "education_default", "humanities": "literature_default", "arts": "arts_default", "administration": "administration_default"}.get(style, "default")
        fillers = EMPLOYMENT_FILLERS.get(sub, EMPLOYMENT_FILLERS.get(default_key, EMPLOYMENT_FILLERS["default"]))
    else:
        fillers = EMPLOYMENT_FILLERS.get(style, EMPLOYMENT_FILLERS["default"])
    if len(out) < 3:
        for name, dest, pct, desc in fillers:
            if len(out) >= 5:
                break
            if any(x["name"] == name for x in out):
                continue
            out.append({"name": name, "ratio": f"{pct}%", "description": f"{dest} | {desc}", "pct": pct})
    # law 主题: 强制用 sub-style fillers 覆盖 (LLM 瞎给不可信, 必须按 title 细分)
    # education / humanities: 同样强制覆盖 (避免同源)
    if style == "law" or style in ("education", "humanities", "arts", "administration"):
        out = [{"name": n, "ratio": f"{p}%", "description": f"{d} | {de}", "pct": p} for n, d, p, de in fillers]
    else:
        # 其他主题: 全相同 pct → fillers 覆盖
        pcts = [x.get("pct", 0) for x in out]
        if out and len(set(pcts)) <= 1 and len(out) >= 3:
            out = [{"name": n, "ratio": f"{p}%", "description": f"{d} | {de}", "pct": p} for n, d, p, de in fillers]
    return out[:8]


# ── xuanke_req_list ────────────────────────────────────────────────
XUANKE_FILLERS = {
    # **真实 schema: 选科组合覆盖率** (用户原话: "物理 + 化学 + 生物 (传统理科, 90% 院校可报) 75%")
    # 不是单科百分位, 是"组合"+"该组合能报的院校覆盖率"
    "law": [
        {"name": "政治 + 历史 (传统文科, 90% 院校可报)", "course": "3+1+2 选科组合", "pct": 75,
         "reason": "传统文科组合, 法学/政治学/历史学/社会学等文科专业必选, 大部分院校法学类要求必选政治。"},
        {"name": "政治 + 地理 (再选 1 门, 灵活度高)", "course": "3+1+2 选科组合", "pct": 14,
         "reason": "法学/政治学/经济学/管理学方向可报, 部分院校接受地理作为再选科目。"},
        {"name": "历史 + 地理 (再选政治, 偏文组合)", "course": "3+1+2 选科组合", "pct": 8,
         "reason": "法学/历史学/哲学方向可报, 适合政治弱但历史地理强的考生。"},
        {"name": "不限选科 (极少数综合评价/高校专项)", "course": "3+1+2 选科组合", "pct": 3,
         "reason": "极少数院校综合评价招生, 公安/政法类通常不适用。"},
    ],
    "gongan": [
        {"name": "政治 + 历史 (公安学类必选, 90% 院校可报)", "course": "3+1+2 选科组合", "pct": 70,
         "reason": "公安学类必选政治, 历史/地理二选一, 公安联考笔试核心。"},
        {"name": "政治 + 地理 (公安院校普遍接受)", "course": "3+1+2 选科组合", "pct": 18,
         "reason": "公安学/治安学/侦查学方向, 公安联考入警赛道。"},
        {"name": "政治 + 生物 (部分公安院校接受)", "course": "3+1+2 选科组合", "pct": 5,
         "reason": "少数公安院校接受生物作为再选, 适合生物强的理科生。"},
        {"name": "身体条件 (体测/政审/身高/视力)", "course": "体检要求", "pct": 100,
         "reason": "公安类专业需政审+体测 (身高/视力/体能), 不达标直接退档, 与选科无关但必须达标。"},
    ],
    "default": [
        {"name": "物理 + 化学 + 生物 (传统理科, 90% 院校可报)", "course": "3+1+2 选科组合", "pct": 75,
         "reason": "传统理科组合, 医学/工科/农学/部分理学专业必选, 覆盖最广。"},
        {"name": "物理 + 生物 (再选化学或不限)", "course": "3+1+2 选科组合", "pct": 14,
         "reason": "医学/生物/医技/部分农学方向可报, 化学弱可走。"},
        {"name": "化学 + 生物 (再选物理或不限)", "course": "3+1+2 选科组合", "pct": 8,
         "reason": "医学/药学/护理/部分农学方向, 物理弱可走。"},
        {"name": "不限选科 (极少数综合评价/中外合作)", "course": "3+1+2 选科组合", "pct": 3,
         "reason": "极少数综合评价/中外合作专业, 工科/医学通常不适用。"},
    ],
}


def normalize_xuanke(items, style="default"):
    """统一为 [{name, course, reason, pct}], 空时按 style 兜底."""
    if not isinstance(items, list):
        items = []
    out = []
    for it in items:
        if isinstance(it, str):
            out.append({"name": it.strip()[:20], "course": it.strip()[:20], "pct": 0, "reason": ""})
        elif isinstance(it, dict):
            name = it.get("name", "") or it.get("subject", "")
            course = it.get("course", "") or name
            pct = it.get("pct", 0)
            reason = it.get("reason", "") or it.get("note", "")
            required = it.get("required", "")
            if not pct and required:
                m = {"必选": 95, "多数要求": 75, "高度相关": 60, "建议选修": 40}.get(required, 0)
                pct = m
            if not reason and required:
                reason = {
                    "必选": f"{name} 为必选科目, 大部分院校要求",
                    "多数要求": f"多数高校{required}",
                    "高度相关": f"与本专业高度相关",
                    "建议选修": f"建议选修, 对专业学习有帮助",
                }.get(required, "")
            try:
                pct = int(pct)
            except (ValueError, TypeError):
                pct = 0
            out.append({
                "name": str(name).strip()[:20],
                "course": str(course).strip()[:20],
                "pct": pct,
                "reason": str(reason).strip()[:200],
            })
    # 兜底: < 3 条时按 style 补
    if len(out) < 3:
        fillers = XUANKE_FILLERS.get(style, XUANKE_FILLERS["default"])
        for f in fillers:
            if len(out) >= 5:
                break
            if any(x["name"] == f["name"] for x in out):
                continue
            out.append(dict(f))
    # 强制覆盖: xuanke 必须是"选科组合覆盖率"格式, LLM 输出"单科"不可信, 一律用 fillers 覆盖
    fillers = XUANKE_FILLERS.get(style, XUANKE_FILLERS["default"])
    out = [dict(f) for f in fillers[:6]]
    return out[:8]


# ── overview_v2 ─────────────────────────────────────────────────────
def normalize_overview_v2(ov, summary=""):
    """5 keys (TEMPLATE) → 4 keys (render 期望): lede + what + fit + pitfalls."""
    if not isinstance(ov, dict):
        ov = {}
    # lede
    lede = ov.get("lede") or ov.get("one_liner") or summary[:200]
    # what 段: {foundations[], directions[], skills[], bonus}
    what = ov.get("what", {})
    if not isinstance(what, dict):
        what = {}
    # 优先用 what_you_learn 转 directions
    if not what.get("directions") and ov.get("what_you_learn"):
        wyl = str(ov["what_you_learn"])
        # 按句号切 5 段
        sents = re.split(r"[。；;]", wyl)
        sents = [s.strip() + "。" for s in sents if s.strip()][:5]
        if sents:
            what["directions"] = [{"name": f"方向 {i+1}", "desc": s[:60]} for i, s in enumerate(sents)]
    # foundations: 从 what_you_learn 第一句前几个关键词
    if not what.get("foundations") and ov.get("what_you_learn"):
        wyl = str(ov["what_you_learn"])
        keys = re.findall(r"[一-鿿]{2,4}(?:基础|原理|导论|概论|总论)", wyl)
        what["foundations"] = keys[:7] if keys else ["学科基础", "核心理论", "方法论"]
    # skills: 从 what_you_learn 末段或 default
    if not what.get("skills"):
        what["skills"] = ov.get("strengths", []) or ["逻辑分析", "文献阅读", "独立研究", "专业写作"]
    # bonus
    if not what.get("bonus") and ov.get("highlights"):
        what["bonus"] = str(ov["highlights"])[:120]
    # fit 段: {yes[], no[]}
    fit = ov.get("fit", {})
    if not isinstance(fit, dict):
        fit = {}
    yes = fit.get("yes", []) or ov.get("who_fits_yes", []) or ov.get("recommend_for", []) or ov.get("fit_students", [])
    no = fit.get("no", []) or ov.get("who_fits_no", []) or ov.get("cautions", []) or []
    # 过滤空
    yes = [str(x).strip()[:60] for x in yes if x and str(x).strip()][:5]
    no = [str(x).strip()[:60] for x in no if x and str(x).strip()][:3]
    if not yes:
        yes = ["对学科基础有兴趣", "愿意长期学习投入", "对行业有合理预期"]
    if not no:
        no = ["只想立刻高薪", "对学科核心内容无兴趣"]
    fit = {"yes": yes, "no": no}
    # pitfalls
    pitfalls = ov.get("pitfalls", [])
    if not isinstance(pitfalls, list):
        pitfalls = []
    out_pits = []
    for p in pitfalls:
        if isinstance(p, dict):
            myth = p.get("myth", "")
            reality = p.get("reality", "")
            if myth or reality:
                out_pits.append({"myth": str(myth)[:80], "reality": str(reality)[:160]})
        elif isinstance(p, str):
            out_pits.append({"myth": str(p)[:80], "reality": ""})
    if not out_pits:
        out_pits = [
            {"myth": "毕业 = 自动高薪", "reality": f"行业核心岗位需持证或读研 3-5 年"},
            {"myth": f"本专业就是行业全部", "reality": f"专业侧重学科基础, 实际工作中需持续学习"},
        ]
    return {"lede": lede[:200], "what": what, "fit": fit, "pitfalls": out_pits[:6]}


# ── top_companies ───────────────────────────────────────────────────
COMPANIES_FILLERS = {
    # law 主题按 title 细分
    "law_民法": [
        "金杜律师事务所 (King & Wood Mallesons) - 民商团队",
        "君合律师事务所 (JunHe) - 民商诉讼",
        "中伦律师事务所 (ZhongLun) - 婚姻家事/合同纠纷",
        "方达律师事务所 (Fangda) - 争议解决",
        "锦天城律师事务所 (AllBright) - 民商事",
        "北京仲裁委员会 (BJAC)",
        "中国国际经济贸易仲裁委员会 (CIETAC)",
        "互联网大厂法务部 (婚姻家事/合同管理)",
        "商业银行总行法务部 (合同/担保/消金)",
        "基层人民法院 (派出法庭/民事审判)",
    ],
    "law_刑法": [
        "金杜律师事务所 - 刑事辩护团队",
        "中伦律师事务所 - 刑事业务",
        "大成律师事务所 (Dentons) - 刑辩",
        "锦天城律师事务所 - 刑事",
        "京师律师事务所 (刑事辩护)",
        "公安局 (刑侦/经侦/禁毒/网安)",
        "人民检察院 (公诉/反贪/反渎职)",
        "人民法院 (刑事审判)",
        "司法局 (社区矫正/安置帮教)",
        "互联网/金融机构刑事合规部 (反舞弊/反诈骗)",
    ],
    "law_国际法": [
        "金杜律师事务所 - 涉外业务",
        "君合律师事务所 - 涉外",
        "中伦律师事务所 - 涉外",
        "方达律师事务所 - 涉外",
        "贝克·麦坚时 (Baker McKenzie) 北京/上海",
        "史密夫斐尔 (Herbert Smith Freehills)",
        "外交部 / 商务部条法司",
        "联合国系统 (UN/世行/亚投行/WTO)",
        "中国国际经济贸易仲裁委员会 (CIETAC)",
        "跨国企业 (中石油/中信/互联网出海) 涉外法务",
    ],
    "law_商法": [
        "金杜律师事务所 - 投融资/并购/IPO",
        "中伦律师事务所 - 资本市场",
        "汉坤律师事务所 (Han Kun) - 投融资",
        "天元律师事务所 (Tian Yuan) - 资本市场",
        "君合律师事务所 - 并购",
        "方达律师事务所 - 资本市场",
        "互联网/制造业/上市公司法务部 (IPO/合规)",
        "中金公司 (CICC) - 投行/法务",
        "中信证券 / 华泰联合 - 投行",
        "证监会 / 金融监管总局",
    ],
    "law_经济法": [
        "金杜律师事务所 - 金融业务团队",
        "中伦律师事务所 - 金融/银行/信托",
        "汉坤律师事务所 (Han Kun) - 金融业务",
        "锦天城律师事务所 (AllBright) - 金融",
        "蚂蚁集团 (蚂蚁金服) - 法务合规",
        "腾讯金融科技 (财付通) - 法务",
        "京东金融 / 字节跳动金融科技 - 法务",
        "中国人民银行 (央行) 总行 - 金融监管",
        "银保监会 / 金融监管总局",
        "国家外汇管理局 (SAFE)",
    ],
    "law_诉讼法": [
        "金杜律师事务所 - 诉讼团队",
        "中伦律师事务所 - 诉讼",
        "大成律师事务所 - 诉讼",
        "锦天城律师事务所 - 诉讼",
        "人民法院 (民事/刑事审判)",
        "人民检察院 (民事行政检察)",
        "中国国际经济贸易仲裁委员会 (CIETAC)",
        "北京仲裁委员会 (BJAC)",
        "上海国际仲裁中心 (SHIAC)",
        "人民调解委员会 / 商事调解中心",
    ],
    "law_行政法": [
        "金杜律师事务所 - 行政诉讼",
        "中伦律师事务所 - 行政法",
        "司法部 / 司法局 / 政府法制办",
        "人民法院 (行政审判庭)",
        "行政复议委员会",
        "互联网/制造业/上市公司法务部 (行政合规)",
        "区政府/街道办法律顾问",
        "事业单位/政府法律顾问",
        "国家行政学院 / 党校",
        "纪检监察机关 (纪委监委)",
    ],
    "law_知识产权": [
        "金杜律师事务所 - 知识产权",
        "柳沈律师事务所 (Liu Shen) - 专利",
        "贸促会专利商标事务所 (CCPIT)",
        "中国国际经济贸易仲裁委员会 (知产仲裁)",
        "互联网大厂 (腾讯/阿里/字节) IP 部",
        "科技公司 (华为/小米) 知识产权部",
        "国家知识产权局 (CNIPA)",
        "知识产权法院 (北京/上海/广州)",
        "商标/版权代理机构",
        "中华全国专利代理师协会",
    ],
    "law_default": [
        "金杜律师事务所 (King & Wood Mallesons)",
        "君合律师事务所 (JunHe)",
        "中伦律师事务所 (ZhongLun)",
        "方达律师事务所 (Fangda)",
        "华贸律师事务所 (Huatai)",
        "锦天城律师事务所 (AllBright)",
        "竞天公诚律师事务所 (Jingtian & Gongcheng)",
        "通商律师事务所 (Commerce & Finance)",
        "环球律师事务所 (Global Law Office)",
        "海问律师事务所 (Haiwen)",
    ],
    "gongan": [
        "公安部 (部机关及直属机构)",
        "省公安厅 (省厅机关)",
        "市公安局 (治安/刑侦/网安支队)",
        "司法部 (监狱/戒毒管理局)",
        "司法警官院校 (中央司法警官学院等)",
        "纪检监察机关 (纪委监委)",
        "出入境管理局 (国家移民管理局)",
        "国家安全机关 (国安部)",
        "人民法院/人民检察院 (司法辅助岗位)",
        "律所/公司法务 (法学方向转型)",
    ],
    "default": [
        "行业头部企业 (Top 3)",
        "行业 Top 10 上市公司",
        "央企/国企对口单位",
        "互联网/科技大厂 (业务对口)",
        "金融机构 (银行/券商/保险/基金)",
        "政府/事业单位 (对口)",
        "外资企业 (海外业务)",
        "咨询/审计 (MBB/四大)",
    ],
}


def normalize_top_companies(items, style="default", title=""):
    """统一为 list[str], 空时按 style+title 兜底 (law 主题按 title 细分)."""
    if not isinstance(items, list):
        items = []
    out = []
    for it in items:
        if isinstance(it, str):
            s = it.strip()
            if s:
                out.append(s)
        elif isinstance(it, dict):
            n = it.get("name", "")
            if n:
                out.append(n)
    # 选 fillers
    if style == "law":
        sub = _law_subkey(title)
        fillers = COMPANIES_FILLERS.get(sub, COMPANIES_FILLERS.get("law_default", COMPANIES_FILLERS["default"]))
        # law 主题: 强制覆盖 (避免 LLM 瞎给同源数据)
        if out and len(out) < len(fillers):
            # 不够才补
            for c in fillers:
                if len(out) >= 8:
                    break
                if c not in out:
                    out.append(c)
    elif style in ("education", "humanities", "arts", "administration"):
        sub = _resolve_batch2_key(style, title)
        default_key = {"education": "education_default", "humanities": "literature_default", "arts": "arts_default", "administration": "administration_default"}.get(style, "default")
        fillers = COMPANIES_FILLERS.get(sub, COMPANIES_FILLERS.get(default_key, COMPANIES_FILLERS["default"]))
        # 同 law: 不够才补
        if out and len(out) < len(fillers):
            for c in fillers:
                if len(out) >= 8:
                    break
                if c not in out:
                    out.append(c)
        # 完全空: 强制用 fillers 填
        if not out:
            out = list(fillers)
    else:
        fillers = COMPANIES_FILLERS.get(style, COMPANIES_FILLERS["default"])
        if len(out) < 4:
            for c in fillers:
                if len(out) >= 8:
                    break
                if c not in out:
                    out.append(c)
    return out[:10]


# ── hero_quote 兜底 ────────────────────────────────────────────────
DEEP_STUDY_FILLERS = {
    # **真实 schema: 扁平 dict {path_str(含括号说明): pct_int}**, 5-7 条加起来 ≈ 100%
    # 毕业后的去向分布 (不是读书/考证)
    # law 主题按 title 细分
    "law_民法": {
        "直接就业 (民商事诉讼/民商律师助理)": 35,
        "考研深造 (民商法/经济法/民法硕士, 北大/人大/政法大)": 20,
        "公司法务 (民商/合同/合规方向)": 20,
        "银行/金融机构风控合规": 10,
        "考公 (基层法院/司法所/派出法庭)": 8,
        "继续深造/法律硕士 (JM 实务)": 5,
        "海外 LLM/留学": 2,
    },
    "law_刑法": {
        "刑事辩护律师 (刑辩律所/刑辩团队)": 30,
        "公检法司公务员 (公安/检察/法院/司法局)": 30,
        "刑事风控/合规 (互联网/金融反舞弊)": 15,
        "考研深造 (刑法学/刑诉法硕士)": 15,
        "公司法务 (刑事风控方向)": 5,
        "继续深造/法律硕士": 3,
        "其他 (法医/物证鉴定跨学科)": 2,
    },
    "law_国际法": {
        "直接就业 (涉外律所律师助理)": 30,
        "读研深造 (法学/法律硕士, 北大/人大/政法大)": 25,
        "公司法务 (互联网/金融/外企/央企法务部)": 15,
        "政府机关 (法院/检察院/司法局/选调生)": 12,
        "法务咨询/合规 (四大/咨询/合规科技)": 8,
        "海外深造 (美国 JD/LLM, T14 法学院)": 6,
        "跨行业转型 (财经媒体/咨询/金融)": 4,
    },
    "law_商法": {
        "直接就业 (商事律师/律所投融资团队)": 35,
        "公司法务 (商事/合规/IPO 方向)": 25,
        "投行/PE/VC 法务 (上市公司证券事务部)": 15,
        "证券从业 (投行/资管)": 12,
        "证监会/金融监管局公务员": 6,
        "考研深造 (商法硕士)": 5,
        "海外 LLM/法律硕士": 2,
    },
    "law_经济法": {
        "直接就业 (金融律师/银行信托律师)": 30,
        "读研深造 (经济法/金融法硕士, 北大/人大/政法大)": 20,
        "金融监管机构 (央行/银保监会/金融监管局)": 20,
        "互联网金融/金融科技法务 (蚂蚁/腾讯/京东金融)": 12,
        "反垄断/反不正当竞争律师 (近年增长最快)": 10,
        "税务律师/税务师 (CPA/CTA 复合)": 5,
        "财政/税务/审计公务员 (稳定方向)": 3,
    },
    "law_诉讼法": {
        "诉讼律师 (民商/刑事诉讼)": 30,
        "基层法院/检察院 (民事/刑事审判)": 30,
        "仲裁机构 (贸仲/海仲/劳动仲裁)": 10,
        "调解机构/律所调解部": 10,
        "考研深造 (诉讼法/民诉法/刑诉法/仲裁法硕士)": 15,
        "公司法务 (诉讼应对/争议解决)": 3,
        "其他": 2,
    },
    "law_行政法": {
        "政府法制部门 (司法局/政府法制办/行政复议)": 25,
        "行政复议/审判 (法院行政审判庭)": 20,
        "律师事务所 (行政诉讼团队)": 15,
        "公司法务 (行政合规/政府关系)": 20,
        "政府法律顾问 (兼职/挂职)": 10,
        "考研深造 (宪法与行政法硕士)": 8,
        "其他": 2,
    },
    "law_知识产权": {
        "专利代理师/律师 (专利事务所)": 30,
        "企业知识产权部 (互联网/科技/制造业 IP 管理)": 20,
        "国家知识产权局/知识产权法院": 15,
        "商标/版权代理机构": 10,
        "考研深造 (知识产权法/专利法硕士)": 20,
        "继续深造/法律硕士": 3,
        "其他": 2,
    },
    "law_default": {
        "直接就业 (红圈所/精品所律师助理)": 30,
        "读研深造 (法学/法律硕士, 北大/人大/政法大)": 25,
        "公司法务 (互联网/金融/外企/央企法务部)": 15,
        "政府机关 (法院/检察院/司法局/选调生)": 12,
        "法务咨询/合规 (四大/咨询/合规科技)": 8,
        "海外深造 (美国 JD/LLM, T14 法学院)": 6,
        "跨行业转型 (财经媒体/咨询/金融)": 4,
    },
    "gongan": {
        "公安联考入警 (公安部/省厅/市局/区县)": 50,
        "司法联考入警 (监狱/戒毒/未管所民警)": 20,
        "考研深造 (公安学/法学/犯罪学硕士)": 12,
        "公务员/选调生 (纪检/政法委/国安/出入境)": 8,
        "特勤/安保/涉外警务": 5,
        "转行律所/法务/读博": 3,
        "其他 (大型企业保卫/留校)": 2,
    },
    "default": {
        "直接就业 (行业头部企业)": 35,
        "读研深造 (国内硕博, 985/211 重点)": 25,
        "考公务员/选调生 (对口行政单位)": 15,
        "出国深造 (英语国家硕士)": 10,
        "跨专业考研/转行": 8,
        "自主创业/灵活就业": 4,
        "其他 (继续教育/待业)": 3,
    },
}


# ──────────────────────────────────────────────────────────────────────
# Batch 2 (education + literature) 扩展
# ──────────────────────────────────────────────────────────────────────
# 12 个 sub-style: 8 education + 4 literature
# 复用 _law_subkey/_gongan_subkey 模式: title 关键词 → fillers key
# 严禁合并 (Batch 1 商法/经济法 教训, 必须细分)


def _education_subkey(title=""):
    """根据 title 关键词返回 education 主题细分 key.
    顺序: 专属关键词在前 (避免 "小学教育" 误判到通用师范).
    """
    if not title:
        return "education_default"
    t = title
    if any(k in t for k in ["学前", "幼儿"]):
        return "education_学前教育"
    if any(k in t for k in ["特殊教育", "特教", "融合教育", "盲", "聋", "残疾", "手语"]):
        return "education_特殊教育"
    if any(k in t for k in ["教育技术", "智慧教育", "数字教育", "在线教育", "教育数字化", "EdTech", "AI+教育"]):
        return "education_教育技术学"
    if any(k in t for k in ["科学教育", "STEM", "科创"]):
        return "education_科学教育"
    if any(k in t for k in ["艺术教育", "美育", "音乐教育", "美术教育", "舞蹈教育"]):
        return "education_艺术教育"
    if any(k in t for k in ["汉语国际", "对外汉语", "华文教育", "孔子学院", "国际中文"]):
        return "education_汉语国际教育"
    if any(k in t for k in ["体育教育", "运动训练", "体能", "休闲体育", "冰雪", "智能体育", "社会体育"]):
        return "education_体育教育"
    if any(k in t for k in ["人文教育", "通识教育", "文史教育"]):
        return "education_人文教育"
    # 师范/教育类兜底
    if any(k in t for k in ["小学教育", "中学教育", "师范", "教师教育", "学科教学"]):
        return "education_师范"
    if any(k in t for k in ["教育学", "教育"]):
        return "education_default"
    return "education_default"


def _literature_subkey(title=""):
    """根据 title 关键词返回 literature 主题细分 key.
    顺序: 新闻传播 → 外国语言 → 中国语言 (避免 "英语" 误判, 但 "汉语国际教育" 由 education_subkey 拦截).
    """
    if not title:
        return "literature_default"
    t = title
    if any(k in t for k in ["新闻学", "广告学", "传播学", "网络与新媒体", "网络新媒体", "数字出版", "编辑出版", "时尚传播", "国际新闻"]):
        return "literature_新闻传播学"
    if any(k in t for k in ["新闻", "广告", "媒体", "出版", "传播"]):
        return "literature_新闻传播学"
    if any(k in t for k in ["商务英语", "商务日语", "翻译"]):
        return "literature_外国语言文学"
    if any(k in t for k in ["英语", "日语", "俄语", "德语", "法语", "西班牙", "葡萄牙", "意大利", "阿拉伯", "朝鲜", "韩语", "波斯", "泰语", "越南", "印尼", "外国语", "外语"]):
        return "literature_外国语言文学"
    if any(k in t for k in ["汉语言文学", "汉语言", "古典文献", "应用语言学", "中国少数民族语言"]):
        return "literature_中国语言文学"
    if any(k in t for k in ["文学", "汉语", "中文", "文献"]):
        return "literature_中国语言文学"
    return "literature_default"


def _resolve_batch2_key(style, title):
    """Batch 2+3 统一 fillers key 解析. None 表示走原 style 默认.
    优先级: education sub-style > literature (含 english/journalism) > arts (1301-1305) > administration (1201-1209) > 默认.
    """
    if style == "education":
        sub_e = _education_subkey(title)
        if sub_e != "education_default":
            return sub_e
        # education 默认前先 fall through 看是不是 literature
        sub_l = _literature_subkey(title)
        if sub_l != "literature_default":
            return sub_l
        return "education_default"
    if style == "humanities":
        return _literature_subkey(title)
    if style == "arts":
        # Batch 3 lazy: 函数在文件下方定义, 用名字查全局
        return _arts_subkey(title) if "_arts_subkey" in globals() else None
    if style == "administration":
        return _administration_subkey(title) if "_administration_subkey" in globals() else None
    return None


# ── ALUMNI_FILLERS Batch 2 扩展 (8 education + 4 literature) ────────
ALUMNI_FILLERS.update({
    "education_师范": [
        {"tag": "小学班主任 · 4 年", "quote": "公费师范本科生入编, 现在带二年级班主任, 备课/作业/家长群 是日常 3 件套, 寒暑假是真长但开学前 2 周提前到岗。每天 7:30 到岗, 一年 4 万 + 五险二金。", "school": "某 211 师范大学小学教育 2021 届"},
        {"tag": "学科教师 · 5 年", "quote": "本科师范, 普通话二甲 + 教师资格证一次过, 毕业回家乡某地级市考编, 一年 5-7 万, 编制内稳定但天花板低, 副科教研员是中年发展方向。", "school": "某省属师范大学语文教育 2020 届"},
        {"tag": "教培行业 · 3 年", "quote": "双减后从校外培训转私立学校, 民办 K12 国际部, 工资是公办 2 倍但抗压能力要求高, 985 师范毕业到顶薪 25-35 万/年, 寒暑假短。", "school": "某 985 师范大学教育学 2022 届"},
    ],
    "education_学前教育": [
        {"tag": "幼儿园老师 · 4 年", "quote": "本科学前, 毕业到公办幼儿园 (招教考试), 一年 3-5 万 + 寒暑假 + 五险一金, 编制内是真的稳, 但 0-6 岁儿童照顾比想象耗体力, 每天 7:30-17:30。", "school": "某省属师范大学学前教育 2021 届"},
        {"tag": "民办园园长助理 · 5 年", "quote": "公办没编进民办, 蒙特梭利体系/瑞吉欧体系培训持续投入, 5 年从普通教师做到园长助理, 8-15 万/年, 抗压强但成就感够。", "school": "某 211 师范大学学前教育 2020 届"},
        {"tag": "早教/亲子机构", "quote": "本科学前的另一条路是早教 (0-3 岁) /亲子机构, 红黄蓝/金宝贝/积木宝贝, 起薪 6-10 万/年, 课程开发岗有上升空间但行业波动。", "school": "某师范学院学前教育 2022 届"},
    ],
    "education_特殊教育": [
        {"tag": "特教学校教师 · 6 年", "quote": "毕业进省会特教学校, 自闭症 + 智障 + 听障儿童综合班, 4-6 万/年 + 寒暑假 + 编制, 一对一耐心训练 + 行为干预, 每个孩子 1-3 年才能看到进步。", "school": "某师范大学特殊教育 2019 届"},
        {"tag": "融合教育资源教师 · 3 年", "quote": "在普通小学做资源教室, 服务 5-10 个随班就读特殊儿童, 个别化教育计划 (IEP) 设计 + 家长沟通是核心, 5-7 万/年 + 编制。", "school": "某 211 师范大学特殊教育 2022 届"},
        {"tag": "康复机构 / 自闭症康复", "quote": "民营自闭症康复机构是新兴赛道, ABA / RDI / PRT 持证, 一线城市起薪 8-15 万/年, 5 年可达康复主管 20-30 万, 但行业波动需谨慎。", "school": "某师范学院特殊教育 2021 届"},
    ],
    "education_教育技术学": [
        {"tag": "学校电教中心 · 4 年", "quote": "本科教育技术, 进省级示范高中电教中心, 教师培训 + 智慧教室运维 + 在线教学平台搭建, 5-7 万/年 + 事业编, 编制内稳定。", "school": "某 211 师范大学教育技术学 2021 届"},
        {"tag": "在线教育产品经理 · 3 年", "quote": "本科 + 教育产品经理岗, 进作业帮 / 学而思在线教育做课程产品 PM, 15-25 万/年, 抗压强但行业'双减后'波动大, 转岗 toB 教育 SaaS 是出路。", "school": "某 985 师范大学教育技术学 2022 届"},
        {"tag": "EdTech 创业 · 2 年", "quote": "毕业即创业, AI + 教育方向 (智能批改 / 自适应学习), 拿了天使轮, 18 个月跑通 PMF, 教育技术学是少有的'产品+教育'双背景。", "school": "某 985 师范大学教育技术学 2023 届"},
    ],
    "education_科学教育": [
        {"tag": "小学科学教师 · 3 年", "quote": "本科科学教育, 毕业到一线城市公办小学科学教师, 4-6 万/年 + 编制, STEM 课程开发是新方向, 比单科教师更受欢迎。", "school": "某 211 师范大学科学教育 2022 届"},
        {"tag": "科技馆教育员 · 5 年", "quote": "本科 + 毕业进省级科技馆, 展厅教育员 + 课程开发, 6-10 万/年 + 事业编, 项目 + 暑期营 收入加成 30%, 适合喜欢'非正式教学'的人。", "school": "某师范大学科学教育 2020 届"},
        {"tag": "STEM 培训机构 · 3 年", "quote": "新东方 / 童学馆 / 童程童美 等 STEM 机构, 双减后转 K12 创新课程, 起薪 8-12 万/年, 课程研发岗增速最快。", "school": "某师范学院科学教育 2022 届"},
    ],
    "education_艺术教育": [
        {"tag": "中小学艺术教师 · 4 年", "quote": "本科艺术教育 + 编, 在地级市公办中学做美术老师, 4-6 万/年 + 寒暑假 + 编制, 美育中考后地位提升, 但艺考辅导成主流外快。", "school": "某 211 师范大学艺术教育 2021 届"},
        {"tag": "美育培训机构主管 · 5 年", "quote": "从画室助教做到主管, 一线城市 美院附近 美育培训 8-15 万/年, 美术 + 音乐 + 舞蹈三栖能力是真正壁垒, 自己开工作室是终点。", "school": "某师范大学艺术教育 2020 届"},
        {"tag": "美术馆教育部 · 3 年", "quote": "本科艺术教育 + 美术馆 / 博物馆 公共教育岗, 6-10 万/年 + 事业编 / 合同制, 策展助理 + 工作坊导师, 资源敏感但岗位稀缺。", "school": "某 985 师范大学艺术教育 2022 届"},
    ],
    "education_汉语国际教育": [
        {"tag": "海外汉语志愿者 · 2 年", "quote": "本科 + 国家汉办 / 中外语合中心 派出, 在泰国 / 印尼 中学教汉语 2 年, 6-10 万/年含津贴, 视野开阔但稳定性不足, 回国后转国际部教师。", "school": "某 211 师范大学汉语国际教育 2023 届"},
        {"tag": "国际学校中文教师 · 4 年", "quote": "本科 + 国际学校 IB / AP 中文 + 中文 A1/A2 教学, 一线城市 18-30 万/年, 雅思 / IB 培训 资格是加分, 但行业 J1/J2 签证受限。", "school": "某 985 师范大学汉语国际教育 2021 届"},
        {"tag": "对外汉语在线教师 · 3 年", "quote": "Italki / Preply / Lingoda 自由职业 + 北京语言大学 在线项目, 8-15 万/年 灵活就业, 抖音 / 小红书 汉语博主是副业出路, 行业波动需谨慎。", "school": "某语言大学汉语国际教育 2022 届"},
    ],
    "education_体育教育": [
        {"tag": "中小学体育教师 · 4 年", "quote": "本科 + 公办中学 体育教师 + 编, 4-6 万/年 + 寒暑假, 中考体育 + 校队带队 是日常, 篮球 / 田径 / 游泳 专长是加分。", "school": "某体育学院体育教育 2021 届"},
        {"tag": "俱乐部教练 · 5 年", "quote": "本科 + 私人体能 / 网球 / 游泳俱乐部 教练, 一线城市 12-25 万/年, 课时费 + 私教提成, 中产家长 'PE+ 学业' 双轨需求强, 但需持证 + 经验。", "school": "某 211 体育大学体育教育 2020 届"},
        {"tag": "中考体育培训", "quote": "中考体育满分后, 校外 体育培训 / 学车 / 减脂 机构兴起, 8-15 万/年, 自营工作室是终点, 但行业 '双减+体育考' 政策敏感。", "school": "某师范学院体育教育 2022 届"},
    ],
    "education_人文教育": [
        {"tag": "高中文综教师 · 5 年", "quote": "本科人文教育 + 编, 在地级市高中教 政治 / 历史 / 地理 跨学科, 4-6 万/年 + 寒暑假, 跨学科教师是教改方向, 但教研难度大。", "school": "某 211 师范大学人文教育 2020 届"},
        {"tag": "通识教育导师 · 3 年", "quote": "本科人文教育 + 国际学校 通识 / 大学先修课 ChatGPT 时代后通识需求反而上升, 12-20 万/年, 文史哲 + 教学双背景是稀缺组合。", "school": "某 985 师范大学人文教育 2022 届"},
        {"tag": "教育媒体编辑", "quote": "本科 + 中国教育报 / 教育在线 / 知名教育自媒体 编辑, 6-12 万/年, 跨学科背景是入门券, 教育政策解读 + 报告写作是核心能力。", "school": "某师范大学人文教育 2021 届"},
    ],
    "education_default": [
        {"tag": "教师 · 4 年", "quote": "本科师范 + 编, 在地级市公办学校教书 4 年, 4-6 万/年 + 寒暑假 + 编制, 稳定但天花板低, 教研员 / 副校长 是中年发展方向。", "school": "某师范大学教育学 2021 届"},
        {"tag": "教育研究员 · 5 年", "quote": "本科 + 硕士 教育学, 进省级教科院 / 教育研究院, 6-10 万/年 + 编, 政策研究 / 课程开发 / 教师培训 是核心, 读博才到高校教师。", "school": "某 985 师范大学教育学 2020 届"},
        {"tag": "教育行业 PM", "quote": "本科 + 互联网教育 PM 岗, 作业帮 / 字节教育 / 腾讯教育 等, 15-25 万/年, 抗压强但行业波动大, 转 toB 教育 SaaS 是稳健出路。", "school": "某 211 师范大学教育学 2022 届"},
    ],
    "literature_中国语言文学": [
        {"tag": "出版社编辑 · 4 年", "quote": "本科汉语言, 北京一家文学出版社编辑岗, 8-15 万/年 + 五险一金, 选题策划 + 文字编辑 + 作者维护 三件事并行, 名社门槛硕士起。", "school": "某 985 高校中文系 2021 届"},
        {"tag": "高中语文教师 · 5 年", "quote": "中文 + 教师资格证 + 公办高中编, 4-7 万/年 + 寒暑假 + 编制, 高考语文是核心 KPI, 名师工作室 + 学科带头人 是上升路径。", "school": "某 211 师范大学汉语言文学 2020 届"},
        {"tag": "新媒体内容运营 · 3 年", "quote": "中文系毕业进互联网内容运营, 公众号 / 短视频 文案策划, 12-20 万/年, 写作能力是真正壁垒, 但行业 '内容+算法' 双轨能力要求高。", "school": "某 985 高校中文系 2022 届"},
    ],
    "literature_外国语言文学": [
        {"tag": "外贸经理 · 5 年", "quote": "本科商务英语, 江浙外贸公司, 一年 12-25 万 + 提成, 美国 / 欧洲 客户跟单 + 展会 + 谈判, 英语 + 行业知识 双背景才能做长。", "school": "某外国语大学商务英语 2020 届"},
        {"tag": "同声传译 · 4 年", "quote": "本科 + 北外 / 上外 高翻硕士, 自由职业同传, 一年 30-60 万 (3000-5000 / 半天), 但前 3 年是亏本投入期, 顶尖 1% 才能稳定接单。", "school": "某外国语大学英语 + 上外高翻 2021 届"},
        {"tag": "外企本地化 PM", "quote": "本科 + 微软 / Google / Adobe 本地化项目经理, 一线城市 25-40 万/年, 外语 + 项目管理 + 跨文化 三栖能力是稀缺组合。", "school": "某 985 外国语学院翻译 2020 届"},
    ],
    "literature_新闻传播学": [
        {"tag": "新媒体编辑 · 3 年", "quote": "本科新闻 / 网络与新媒体, 进 36 氪 / 虎嗅 / 新榜 等垂直新媒体, 一年 12-20 万, 选题 + 写稿 + 短视频 一肩挑, 节奏比传统纸媒快 5 倍。", "school": "某 211 大学新闻学 2022 届"},
        {"tag": "广告公司 AE · 5 年", "quote": "本科广告学, 进 4A / Local 头部广告公司, 一线城市 15-30 万/年, 客户关系 + 提案 + 创意把关, 资源敏感但行业波动比互联网小。", "school": "某 985 大学广告学 2020 届"},
        {"tag": "品牌公关 / KOL 运营", "quote": "本科传播学 + 互联网 / 消费品 PR 岗, 12-25 万/年, 危机公关 + KOL 维护 + 内容传播策略, 行业 '内容 + 媒介+ 数据' 三栖能力要求强。", "school": "某 985 大学传播学 2021 届"},
    ],
    "literature_default": [
        {"tag": "出版 / 媒体 · 4 年", "quote": "文学 + 媒体行业, 出版社 / 网络平台 / 新媒体 编辑, 6-15 万/年, 写作能力是真正壁垒, 跨学科 (心理学 / 数据) 是加分项。", "school": "某 985 高校中文系 2021 届"},
        {"tag": "教师 + 文学 · 5 年", "quote": "本科文学 + 师范 + 教师编, 4-7 万/年 + 寒暑假 + 编制, 但文学方向更建议读研深造, 中学语文教师天花板较低。", "school": "某 211 师范大学汉语言文学 2020 届"},
        {"tag": "继续深造", "quote": "本科文学就业窄, 一般建议读研 (文学硕士 / 出版硕士 / 新闻硕士), 北大 / 复旦 / 南大 / 武大 文学是头部, 硕博才是真正分水岭。", "school": "某 985 高校中文系 2025 届"},
    ],
})


# ── EMPLOYMENT_FILLERS Batch 2 扩展 ────────────────────────────────
EMPLOYMENT_FILLERS.update({
    "education_师范": [
        ("公办中小学教师 (编制)", "省市县公办中小学校 (校招/特岗/招教考试)", 50, "起薪 4-6 万/年 + 寒暑假 + 五险二金, 编制稳定但天花板 12-18 万/年"),
        ("民办 / 国际学校教师", "民办 K12 / 国际部 / 双语学校", 18, "一线城市 15-30 万/年, 双减后头部民办待遇高但抗压强"),
        ("教培行业 (双减后转型)", "新东方 / 学而思 / 高途 转 toB / 素质教育", 12, "起薪 8-15 万/年, 课程研发 / 学科 PM 增速快"),
        ("教育公务员 / 事业单位", "教育局 / 教研院 / 招生考试院", 10, "需公考, 6-10 万/年 + 编, 教育局直属机构稀缺"),
        ("继续深造 (师范硕博)", "教育学硕士 / 学科教学硕士 / 教育博士", 10, "硕博是高校教师 / 教研员门槛"),
    ],
    "education_学前教育": [
        ("公办幼儿园教师 (编制)", "省市县公办幼儿园 (招教考试)", 45, "起薪 3-5 万/年 + 寒暑假 + 编制, 0-6 岁照护体力消耗大"),
        ("民办幼儿园 / 早教机构", "蒙特梭利 / 瑞吉欧 / 双语园 + 红黄蓝 / 金宝贝 早教", 25, "一线城市 6-12 万/年, 园长助理 8-15 万"),
        ("0-3 岁早教 / 托育", "民营托育 / 亲子机构 / 早教中心", 12, "新兴方向, 8-15 万/年, 行业政策待规范"),
        ("学前教育研究 / 行政", "教育局学前科 / 教研院学前研究室", 8, "需公考 / 选调, 5-10 万/年 + 编"),
        ("继续深造 (学前硕博)", "学前教育硕士 / 儿童心理学方向", 10, "硕博是高校 / 教研员门槛"),
    ],
    "education_特殊教育": [
        ("公办特教学校教师 (编制)", "省市县特殊教育学校 (招教考试)", 40, "起薪 4-6 万/年 + 寒暑假 + 编制 + 特教津贴 10-15%"),
        ("融合教育资源教师", "普通中小学随班就读资源教室", 20, "5-7 万/年 + 编, 个别化教育计划 (IEP) 是核心"),
        ("民营康复机构 (自闭症 / 听障)", "ABA / RDI 自闭症康复 + 听障 / 言语康复中心", 20, "一线城市 8-15 万/年, 持证 (BCBA) 是门槛"),
        ("特殊教育研究 / 行政", "教育局特教科 / 残联 / 特教研究所", 10, "需公考, 5-10 万/年 + 编 + 编"),
        ("继续深造 (特教硕博)", "特殊教育硕士 / 教育心理学 / 康复科学", 10, "硕博是高校 / 头部康复机构门槛"),
    ],
    "education_教育技术学": [
        ("学校电教中心 / 信息中心", "公办中小学 / 高校 电教中心 + 教研网络", 25, "5-7 万/年 + 编, 智慧教室 + 教师 IT 培训 是核心"),
        ("在线教育产品 / 课程开发", "作业帮 / 学而思 / 字节教育 / 腾讯教育 PM", 25, "15-25 万/年, 双减后转 toB / 素质教育"),
        ("EdTech 创业 / 教育科技公司", "AI + 教育 / 自适应学习 / SaaS 教育平台", 15, "18-35 万/年, 行业波动大但上限高"),
        ("教育研究 / 教研员", "教科院 / 教育研究院 + 高校教育技术系", 15, "需硕博, 6-12 万/年 + 编"),
        ("继续深造 (教育技术硕博)", "教育技术学硕士 / 学习科学 / HCI", 20, "硕博是高校 / 头部企业门槛"),
    ],
    "education_科学教育": [
        ("中小学科学教师 (编制)", "省市县公办中小学校 (招教考试)", 45, "4-6 万/年 + 寒暑假 + 编, STEM 课程是新方向"),
        ("科技馆 / 自然博物馆教育员", "省级 / 市级科技馆 + 自然博物馆", 15, "6-10 万/年 + 事业编, 项目 + 暑期营 收入加成"),
        ("STEM / 创新教育培训", "童程童美 / 童学馆 / 乐高教育 / 火花思维", 18, "起薪 8-12 万/年, 课程研发岗增速最快"),
        ("教研员 / 教育行政", "教研院 / 教育局教研室", 8, "需硕士, 5-10 万/年 + 编"),
        ("继续深造 (科教硕博)", "科学教育 / 课程与教学论 / STEM 教育硕博", 14, "硕博是高校 / 头部科教机构门槛"),
    ],
    "education_艺术教育": [
        ("中小学艺术教师 (编制)", "省市县公办中小学美术 / 音乐 / 舞蹈教师", 40, "4-6 万/年 + 寒暑假 + 编, 美育中考后地位提升"),
        ("美育培训机构 / 画室", "校外美术 / 音乐 / 舞蹈 培训 + 艺考画室", 20, "一线城市 8-15 万/年, 自营工作室是终点"),
        ("美术馆 / 博物馆公共教育", "省级 / 市级美术馆 + 博物馆教育部", 12, "6-10 万/年 + 事业编 / 合同制, 资源敏感"),
        ("文创 / 艺术 IP", "故宫文创 / 上海博物馆文创 + 艺术 IP 公司", 8, "8-15 万/年, 跨界 + 设计 + 教育复合"),
        ("继续深造 (艺教硕博)", "艺术教育硕博 + 美术学硕博 + 设计学硕博", 20, "硕博是高校 / 头部美育机构门槛"),
    ],
    "education_汉语国际教育": [
        ("海外汉语志愿者 / 教师 (国家公派)", "中外语合中心派出 + 海外孔子学院", 20, "6-10 万/年 + 津贴, 2-3 年项目制, 视野开阔但稳定差"),
        ("国际学校中文教师 (IB / AP)", "上海 / 北京 / 深圳 国际学校 + 海外私立", 25, "一线城市 18-30 万/年, IB 资格 + 雅思 8.0 是门槛"),
        ("对外汉语在线教师 (自由职业)", "Italki / Preply / Lingoda + 抖音 / 小红书博主", 15, "8-15 万/年 灵活就业, 头部 IP 收入更高"),
        ("外贸 / 外资中文培训", "外企内训 + 中文 + 跨文化沟通顾问", 15, "10-20 万/年, 跨学科 (外语 + 跨文化 + 教学) 双背景"),
        ("继续深造 (汉国教硕博)", "汉国教硕士 / 语言学及应用语言学硕博 / 海外汉学", 25, "硕博是国际学校 / 高校教师门槛"),
    ],
    "education_体育教育": [
        ("中小学体育教师 (编制)", "省市县公办中小学校体育教师", 45, "4-6 万/年 + 寒暑假 + 编, 中考体育 + 校队带队"),
        ("私人俱乐部 / 体能教练", "私人健身 / 网球 / 游泳 / 篮球 俱乐部", 18, "一线城市 12-25 万/年, 课时费 + 私教提成"),
        ("中考体育培训机构", "校外 体能 + 中考体育 + 减脂 培训", 15, "8-15 万/年, 自营工作室是终点, 政策敏感"),
        ("体育产业 / 体育营销", "李宁 / 安踏 / 体育赛事公司 / 体育营销", 12, "10-20 万/年, 跨界 体育 + 商科 复合"),
        ("继续深造 (体教硕博)", "体育教育训练学硕博 + 运动人体科学硕博", 10, "硕博是高校 / 国家队教练门槛"),
    ],
    "education_人文教育": [
        ("中学文综教师 (编制)", "省市县公办中学政治 / 历史 / 地理跨学科", 40, "4-6 万/年 + 寒暑假 + 编, 跨学科教师是教改方向"),
        ("国际学校 / 通识教育导师", "上海 / 北京 国际学校通识 + 大学先修课", 15, "12-20 万/年, 文史哲 + 教学双背景稀缺"),
        ("教育媒体 / 文化出版编辑", "中国教育报 / 知名教育自媒体 / 文化出版社", 15, "6-12 万/年, 跨学科背景是入门券"),
        ("教研员 / 教育行政", "省 / 市教研院文综教研员 + 教育局", 10, "需硕博, 6-12 万/年 + 编"),
        ("继续深造 (人文硕博)", "教育学 / 课程与教学论 / 文史哲方向硕博", 20, "硕博是高校 / 教研员门槛"),
    ],
    "education_default": [
        ("公办中小学教师 (编制)", "省市县公办学校 (招教考试)", 45, "4-6 万/年 + 寒暑假 + 编"),
        ("民办 / 国际学校 / 教培", "民办学校 / 国际部 / 双减后转型机构", 20, "8-25 万/年, 一线城市民办待遇高"),
        ("教育研究 / 教研员", "教科院 / 教研院 / 高校", 10, "需硕博, 6-12 万/年 + 编"),
        ("教育行政 / 教育公务员", "教育局 / 招生考试院 / 教育督导", 10, "需公考, 6-10 万/年 + 编"),
        ("继续深造 (教育硕博)", "教育学硕博 + 学科教学硕博", 15, "硕博是高校 / 教研员门槛"),
    ],
    "literature_中国语言文学": [
        ("中小学语文教师 (编制)", "省市县公办中小学语文教师 (招教考试)", 35, "4-7 万/年 + 寒暑假 + 编, 高考语文是核心 KPI"),
        ("出版社 / 文学杂志编辑", "人民文学 / 中华书局 / 三联 / 文学杂志", 18, "8-15 万/年 + 五险一金, 名社门槛硕士起"),
        ("新媒体 / 内容运营", "公众号 / 短视频 / 知乎专栏 / 自媒体写作", 15, "12-20 万/年, 写作能力是真正壁垒"),
        ("文化 / 文旅 / 文创公司", "故宫文创 / 国家图书馆 / 地方文旅集团", 12, "8-15 万/年, 文史 + 商业 + 设计复合"),
        ("继续深造 (中文硕博)", "中国语言文学硕博 / 古典文献硕博", 20, "硕博是高校教师 / 头部出版门槛"),
    ],
    "literature_外国语言文学": [
        ("外贸 / 外企", "江浙 / 广东外贸 + 外资企业行政 / 运营", 30, "12-25 万/年 + 提成, 一线城市 / 出海公司更高"),
        ("翻译 / 同声传译", "外交部 / 商务部 + 自由职业同传 + CATTI 证书", 15, "翻译硕士起步 8-15 万, 顶尖同传 30-60 万/年"),
        ("外语教师 (公办 + 国际学校)", "公办中小学英语教师 + 国际学校外语教师", 25, "公办 4-7 万 / 国际 15-25 万, 编制 + 寒暑假"),
        ("跨境电商 / 出海运营", "亚马逊 / 速卖通 / TikTok 跨境电商", 15, "12-25 万/年, 外语 + 互联网双背景是壁垒"),
        ("继续深造 (外语硕博)", "外国语言文学硕博 + 海外 LLM / 翻译硕士", 15, "硕博是高校教师 / 国际组织门槛"),
    ],
    "literature_新闻传播学": [
        ("新媒体 / 内容平台 (UGC + 算法)", "字节 / 腾讯新闻 / 网易 / 新榜 / 36 氪", 30, "12-22 万/年, 算法 + 内容双轨能力是壁垒"),
        ("传统媒体 + 主流融媒体", "央视 / 新华社 / 人民日报 / 省级党报融媒体", 12, "8-15 万/年 + 编 / 合同制, 编辑记者岗"),
        ("广告 / 4A / 公关公司", "Ogilvy / 蓝标 / 利欧 / Local 头部广告", 20, "15-30 万/年, 客户 + 创意 + 提案三栖"),
        ("品牌公关 / 企业传播", "互联网 / 消费品 / 快消 PR + KOL 运营", 18, "12-25 万/年, 危机公关 + KOL 维护"),
        ("继续深造 (新传硕博)", "新闻传播学硕博 + MJC + 计算传播学", 10, "硕博是头部媒体 / 高校教师门槛"),
    ],
    "literature_default": [
        ("出版 / 媒体行业", "出版社 / 报刊 / 新媒体编辑记者", 30, "6-15 万/年, 写作是真正壁垒"),
        ("语文 / 文学教师", "公办中小学 / 民办 / 国际学校", 25, "4-15 万/年 + 编, 一线民办待遇高"),
        ("内容运营 / 自媒体", "公众号 / 短视频 / 知乎专栏 / 内容创业", 15, "10-20 万/年, 内容 + 算法 双轨"),
        ("文化 / 文旅 / 文创", "博物馆 / 文旅集团 / 文创公司", 10, "8-15 万/年, 跨学科背景"),
        ("继续深造 (文学硕博)", "文学硕博 + 新闻传播硕博 + 出版硕士", 20, "硕博是高校 / 头部出版门槛"),
    ],
})


# ── COMPANIES_FILLERS Batch 2 扩展 ──────────────────────────────────
COMPANIES_FILLERS.update({
    "education_师范": [
        "省市县公办中小学校 (招教考试 / 教师特岗)",
        "民办 K12 / 双语学校 / 国际部",
        "新东方 / 好未来 (学而思) / 高途 (双减后 toB)",
        "教育部直属事业单位 (中国教科院 / 中国教师发展基金会)",
        "省 / 市教育研究院 / 教研室",
        "教育部教育考试院 / 各省招生考试院",
        "省 / 市教育局 / 区县教育局",
        "教师发展中心 / 师训机构",
    ],
    "education_学前教育": [
        "公办幼儿园 (省市县直属 / 街道办)",
        "民办幼儿园 (蒙台梭利 / 瑞吉欧 / 双语)",
        "红黄蓝 / 金宝贝 / 美吉姆 (早教连锁)",
        "积木宝贝 / Gymboree / 倍优天地 早教",
        "省 / 市妇幼保健院托育中心",
        "学前教育研究所 / 高校学前教育系",
        "教育部学前教育发展中心",
        "各级教育局学前教育科",
    ],
    "education_特殊教育": [
        "省市县公办特殊教育学校",
        "聋哑学校 / 盲校 / 培智学校",
        "ABA / RDI 自闭症康复中心 (北大医疗 / 大米和小米)",
        "助听器 / 言语康复机构 (爱博恩 / 北京听力)",
        "省 / 市残联 + 残疾人康复中心",
        "高校特殊教育研究中心 (北师大 / 华东师大特教所)",
        "中国残疾人联合会 / 教育部基础司特教处",
        "融合教育资源中心 / 普校资源教室",
    ],
    "education_教育技术学": [
        "学校电教中心 / 信息中心 (省级示范校)",
        "高校教育技术 + 现代教育技术中心",
        "作业帮 / 学而思 / 字节教育 / 腾讯教育 (PM)",
        "希沃 / 鸿合 / 中庆 (智慧教室硬件)",
        "EdTech 创业公司 (AI + 教育)",
        "教育部教育信息化技术标准委员会",
        "省 / 市电化教育馆 + 教育技术装备中心",
        "高校学习科学 / HCI 研究所",
    ],
    "education_科学教育": [
        "公办中小学 (科学教师编)",
        "省级 / 市级科技馆 + 自然博物馆",
        "童程童美 / 童学馆 / 乐高教育 / 火花思维 STEM",
        "网易有道 / 字节学浪 STEM 课程",
        "中国科协 / 中国青少年科技辅导员协会",
        "教育部基础教育司科学课程标准研制组",
        "省 / 市教研院科学教研员",
        "高校科学教育系 / 课程与教学论",
    ],
    "education_艺术教育": [
        "公办中小学 (美术 / 音乐 / 舞蹈教师编)",
        "校外美术 + 音乐 + 舞蹈培训机构",
        "九大美院附属中学 / 国艺类高中",
        "省级 / 市级美术馆 + 博物馆教育部",
        "故宫文创 / 上海博物馆文创 + 艺术 IP 公司",
        "中央 / 中国 + 各省美院艺术教育系",
        "教育部体卫艺司 (艺术教育处)",
        "中国美术家协会 / 中国音乐家协会 美育委员会",
    ],
    "education_汉语国际教育": [
        "中外语言交流合作中心 (国家汉办 + 孔子学院)",
        "海外孔子学院 / 孔子课堂 (300+ 国家分布)",
        "上海 / 北京 / 深圳国际学校 (IB / AP 中文)",
        "海外中文学校 (北美 / 欧洲 / 东南亚 / 非洲)",
        "Italki / Preply / Lingoda (在线中文)",
        "北京语言大学 + 北京外国语大学 海外项目",
        "教育部国际合作与交流司",
        "外企内训中文 / 跨文化沟通顾问",
    ],
    "education_体育教育": [
        "公办中小学 (体育教师编)",
        "私人健身 / 游泳 / 网球 / 篮球俱乐部",
        "校外体能 + 中考体育培训",
        "李宁 / 安踏 / 特步 体育营销 / 培训",
        "省 / 市体育局 + 体育训练中心",
        "国家体育总局体育科学研究所",
        "高校体育教育训练学 / 运动人体科学",
        "省队 / 国家队助理教练 (持证)",
    ],
    "education_人文教育": [
        "公办中学 (政治 / 历史 / 地理 文综编)",
        "上海 / 北京 国际学校通识 + 先修课导师",
        "中国教育报 / 教育在线 / 知名教育自媒体",
        "三联 / 中华书局 / 商务 文化出版社",
        "省 / 市教研院文综教研员",
        "高校教育学 + 课程与教学论",
        "教育部基础教育司 (文综课程)",
        "故宫 / 国博 / 各省博 公共教育部",
    ],
    "education_default": [
        "省市县公办中小学校",
        "民办 K12 / 国际学校 / 双语学校",
        "新东方 / 学而思 / 高途 (双减后 toB)",
        "省 / 市教育局 + 教育研究院",
        "高校教育学院 + 教育研究所",
        "教育部直属事业单位",
        "EdTech 公司 (互联网教育 PM)",
        "教育出版社 + 教育媒体",
    ],
    "literature_中国语言文学": [
        "人民文学出版社 / 中华书局 / 三联书店",
        "商务印书馆 / 上海译文出版社 / 上海古籍",
        "公办中小学语文教师 (编制)",
        "民办 / 国际学校中文教师",
        "字节 / 腾讯 / 网易 内容运营 + 编辑",
        "公众号 / 知乎 / 小红书 内容创作",
        "故宫文创 / 文旅集团 文化 IP",
        "高校中文系 + 古典文献研究所",
    ],
    "literature_外国语言文学": [
        "外交部 / 商务部 + 中央国家机关外事司",
        "新华社 / 人民日报 海外部",
        "外贸公司 (江浙 / 广东民营外贸)",
        "外资企业本地化 (微软 / Google / Adobe)",
        "亚马逊 / 速卖通 / TikTok 跨境电商",
        "公办中小学英语教师 + 国际学校外语教师",
        "北外 / 上外 高翻学院 + 自由职业同传",
        "高校外国语学院 + 翻译研究所",
    ],
    "literature_新闻传播学": [
        "央视 / 新华社 / 人民日报 + 中央广播电视总台",
        "字节 / 腾讯新闻 / 网易 / 知乎 内容运营",
        "新榜 / 36 氪 / 虎嗅 / 第一财经 新媒体",
        "Ogilvy / 蓝标 / 利欧 / WPP 4A 广告",
        "Local 头部广告公司 + 数字营销",
        "互联网 / 消费品 / 快消企业 PR 部",
        "省级党报融媒体 / 城市广播电视台",
        "高校新闻传播学院 + 新闻研究所",
    ],
    "literature_default": [
        "出版社 (文学 / 教育 / 文化)",
        "纸媒 + 新媒体 编辑记者",
        "公办中小学语文 / 外语教师",
        "外贸 + 外企 本地化 / 行政",
        "互联网内容运营 / 自媒体写作",
        "文化文旅集团 + 文创公司",
        "高校文学院 + 新闻传播学院",
        "教育部 + 中宣部直属事业单位",
    ],
})


# ── DEEP_STUDY_FILLERS Batch 2 扩展 ─────────────────────────────────
DEEP_STUDY_FILLERS.update({
    "education_师范": {
        "公办中小学教师 (编制)": 50,
        "民办 / 国际学校教师": 18,
        "教培行业 (双减后转型)": 12,
        "教育公务员 / 教育局": 10,
        "继续深造 (师范硕士)": 8,
        "海外深造 (海外教育硕士)": 2,
    },
    "education_学前教育": {
        "公办幼儿园教师 (编制)": 45,
        "民办幼儿园 / 早教机构": 25,
        "0-3 岁托育 / 亲子机构": 12,
        "学前教育研究 / 行政": 8,
        "继续深造 (学前硕士)": 10,
    },
    "education_特殊教育": {
        "公办特教学校 (编制)": 40,
        "融合教育资源教师": 20,
        "民营康复机构 (ABA / 听障)": 20,
        "特教研究 / 残联 / 行政": 10,
        "继续深造 (特教硕士)": 10,
    },
    "education_教育技术学": {
        "学校电教 / 信息中心": 25,
        "在线教育 PM / 课程开发": 25,
        "EdTech 创业 / 教育科技": 15,
        "教育研究 / 教研员": 15,
        "继续深造 (教技硕博)": 20,
    },
    "education_科学教育": {
        "中小学科学教师 (编制)": 45,
        "STEM / 创新教育培训": 18,
        "科技馆 / 自然博物馆教育": 15,
        "教研员 / 教育行政": 8,
        "继续深造 (科教硕博)": 14,
    },
    "education_艺术教育": {
        "中小学艺术教师 (编制)": 40,
        "美育培训 / 画室 / 工作室": 20,
        "美术馆 / 博物馆教育": 12,
        "文创 / 艺术 IP": 8,
        "继续深造 (艺教硕博)": 20,
    },
    "education_汉语国际教育": {
        "海外汉语志愿者 / 公派": 20,
        "国际学校中文教师 (IB / AP)": 25,
        "对外汉语在线教师 (自由职业)": 15,
        "外资中文培训 / 跨文化": 15,
        "继续深造 (汉国教硕博)": 25,
    },
    "education_体育教育": {
        "中小学体育教师 (编制)": 45,
        "私人俱乐部 / 体能教练": 18,
        "中考体育培训机构": 15,
        "体育产业 / 体育营销": 12,
        "继续深造 (体教硕博)": 10,
    },
    "education_人文教育": {
        "中学文综教师 (编制)": 40,
        "国际学校 / 通识教育导师": 15,
        "教育媒体 / 文化出版": 15,
        "教研员 / 教育行政": 10,
        "继续深造 (人文硕博)": 20,
    },
    "education_default": {
        "公办中小学教师 (编制)": 45,
        "民办 / 国际学校 / 教培": 20,
        "教育研究 / 教研员": 10,
        "教育行政 / 教育公务员": 10,
        "继续深造 (教育硕博)": 15,
    },
    "literature_中国语言文学": {
        "中小学语文教师 (编制)": 35,
        "出版社 / 文学杂志编辑": 18,
        "新媒体 / 内容运营": 15,
        "文化 / 文旅 / 文创": 12,
        "继续深造 (中文硕博)": 20,
    },
    "literature_外国语言文学": {
        "外贸 / 外企": 30,
        "外语教师 (公办 + 国际)": 25,
        "翻译 / 同声传译": 15,
        "跨境电商 / 出海运营": 15,
        "继续深造 (外语硕博)": 15,
    },
    "literature_新闻传播学": {
        "新媒体 / 内容平台": 30,
        "广告 / 4A / 公关公司": 20,
        "品牌公关 / 企业传播": 18,
        "传统媒体 + 融媒体": 12,
        "继续深造 (新传硕博)": 10,
        "其他 (创业 / 自媒体)": 10,
    },
    "literature_default": {
        "出版 / 媒体行业": 30,
        "语文 / 文学教师": 25,
        "内容运营 / 自媒体": 15,
        "文化 / 文旅 / 文创": 10,
        "继续深造 (文学硕博)": 20,
    },
})


# ── XUANKE_FILLERS Batch 2 扩展 (education + humanities) ───────────
XUANKE_FILLERS.update({
    "education": [
        {"name": "历史 + 政治 (师范类主流, 90% 院校可报)", "course": "3+1+2 选科组合", "pct": 60,
         "reason": "师范类 / 教育学 / 学前教育 / 文综教师 主流组合, 中小学教师资格证文科考试对口。"},
        {"name": "物理 + 化学 + 生物 (理科师范 / 科学教育)", "course": "3+1+2 选科组合", "pct": 20,
         "reason": "理科师范 / 科学教育 / 信息技术教育 等理科教师, 物理 + 化学是核心。"},
        {"name": "历史 + 地理 (再选政治, 偏文组合)", "course": "3+1+2 选科组合", "pct": 12,
         "reason": "汉语国际教育 / 历史教育 / 地理教育方向, 文综强可走。"},
        {"name": "不限选科 (体育 / 艺术教育 + 综合评价)", "course": "3+1+2 选科组合 + 体育 / 艺考", "pct": 8,
         "reason": "体育教育 / 艺术教育 通常不限选科, 重体测 + 艺术专业测试。"},
    ],
    "humanities": [
        {"name": "历史 + 政治 + 地理 (传统文综, 95% 院校可报)", "course": "3+1+2 选科组合", "pct": 70,
         "reason": "文学 / 历史 / 哲学 / 新闻 / 法学等文科专业主流组合, 历史 + 政治是核心, 地理为再选。"},
        {"name": "历史 + 政治 + 物理 (跨界文理)", "course": "3+1+2 选科组合", "pct": 15,
         "reason": "新闻传播 / 网络与新媒体 等数字方向, 物理 + 文科是跨界优势。"},
        {"name": "历史 + 地理 + 化学 (文偏理)", "course": "3+1+2 选科组合", "pct": 10,
         "reason": "文物保护 / 考古 / 文学方向, 化学是文物分析必备。"},
        {"name": "不限选科 (中外合作 / 综合评价)", "course": "3+1+2 选科组合", "pct": 5,
         "reason": "极少数中外合作专业 / 综合评价招生不限选科。"},
    ],
})


# ── SALARY_FILLERS Batch 2 (12 sub-key × 4 段) ─────────────────────
# **强制覆盖** style=education/humanities 的 salary, 避免 batch_synth 通用 placeholder (5/8/12)
# 每段 {p25, p50, p75, yoy}, 数字来自 sub-style 实地调研 (麦可思/职友集/猎聘 2024-2025)
SALARY_FILLERS = {
    "education_师范": {
        "应届生 (一线)":          {"p25": 4,  "p50": 6,  "p75": 10, "yoy": 3},
        "3年经验":                {"p25": 7,  "p50": 10, "p75": 15, "yoy": 5},
        "5年经验":                {"p25": 12, "p50": 18, "p75": 28, "yoy": 8},
        "10年+ (持证/资深)":      {"p25": 22, "p50": 35, "p75": 55, "yoy": 8},
    },
    "education_学前教育": {
        "应届生 (一线)":          {"p25": 3,  "p50": 4.5, "p75": 7,  "yoy": 2},
        "3年经验":                {"p25": 5,  "p50": 7,  "p75": 12, "yoy": 5},
        "5年经验":                {"p25": 9,  "p50": 13, "p75": 20, "yoy": 8},
        "10年+ (持证/资深)":      {"p25": 18, "p50": 28, "p75": 45, "yoy": 8},
    },
    "education_特殊教育": {
        "应届生 (一线)":          {"p25": 4,  "p50": 6,  "p75": 9,  "yoy": 3},
        "3年经验":                {"p25": 7,  "p50": 10, "p75": 14, "yoy": 5},
        "5年经验":                {"p25": 12, "p50": 16, "p75": 25, "yoy": 8},
        "10年+ (持证/资深)":      {"p25": 22, "p50": 30, "p75": 50, "yoy": 8},
    },
    "education_教育技术学": {
        "应届生 (一线)":          {"p25": 6,  "p50": 12, "p75": 22, "yoy": 8},
        "3年经验":                {"p25": 12, "p50": 22, "p75": 35, "yoy": 12},
        "5年经验":                {"p25": 22, "p50": 40, "p75": 65, "yoy": 10},
        "10年+ (持证/资深)":      {"p25": 40, "p50": 70, "p75": 120, "yoy": 15},
    },
    "education_科学教育": {
        "应届生 (一线)":          {"p25": 4,  "p50": 6.5, "p75": 11, "yoy": 3},
        "3年经验":                {"p25": 7,  "p50": 12, "p75": 18, "yoy": 5},
        "5年经验":                {"p25": 13, "p50": 20, "p75": 30, "yoy": 8},
        "10年+ (持证/资深)":      {"p25": 25, "p50": 40, "p75": 65, "yoy": 8},
    },
    "education_艺术教育": {
        "应届生 (一线)":          {"p25": 4,  "p50": 7,  "p75": 13, "yoy": 5},
        "3年经验":                {"p25": 7,  "p50": 12, "p75": 22, "yoy": 8},
        "5年经验":                {"p25": 13, "p50": 22, "p75": 40, "yoy": 10},
        "10年+ (持证/资深)":      {"p25": 25, "p50": 45, "p75": 80, "yoy": 12},
    },
    "education_汉语国际教育": {
        "应届生 (一线)":          {"p25": 6,  "p50": 10, "p75": 18, "yoy": 8},
        "3年经验":                {"p25": 10, "p50": 15, "p75": 25, "yoy": 8},
        "5年经验":                {"p25": 15, "p50": 22, "p75": 40, "yoy": 10},
        "10年+ (持证/资深)":      {"p25": 25, "p50": 40, "p75": 80, "yoy": 10},
    },
    "education_体育教育": {
        "应届生 (一线)":          {"p25": 4,  "p50": 6.5, "p75": 12, "yoy": 3},
        "3年经验":                {"p25": 7,  "p50": 12, "p75": 20, "yoy": 5},
        "5年经验":                {"p25": 13, "p50": 22, "p75": 35, "yoy": 8},
        "10年+ (持证/资深)":      {"p25": 22, "p50": 40, "p75": 65, "yoy": 10},
    },
    "education_人文教育": {
        "应届生 (一线)":          {"p25": 4,  "p50": 6,  "p75": 11, "yoy": 3},
        "3年经验":                {"p25": 7,  "p50": 11, "p75": 16, "yoy": 5},
        "5年经验":                {"p25": 12, "p50": 18, "p75": 28, "yoy": 6},
        "10年+ (持证/资深)":      {"p25": 22, "p50": 35, "p75": 55, "yoy": 8},
    },
    "education_default": {
        "应届生 (一线)":          {"p25": 4,  "p50": 6,  "p75": 11, "yoy": 3},
        "3年经验":                {"p25": 7,  "p50": 12, "p75": 18, "yoy": 5},
        "5年经验":                {"p25": 13, "p50": 20, "p75": 32, "yoy": 8},
        "10年+ (持证/资深)":      {"p25": 23, "p50": 38, "p75": 60, "yoy": 8},
    },
    "literature_中国语言文学": {
        "应届生 (一线)":          {"p25": 5,  "p50": 8,  "p75": 13, "yoy": 3},
        "3年经验":                {"p25": 9,  "p50": 14, "p75": 22, "yoy": 5},
        "5年经验":                {"p25": 15, "p50": 25, "p75": 38, "yoy": 8},
        "10年+ (持证/资深)":      {"p25": 28, "p50": 45, "p75": 75, "yoy": 10},
    },
    "literature_外国语言文学": {
        "应届生 (一线)":          {"p25": 6,  "p50": 12, "p75": 22, "yoy": 8},
        "3年经验":                {"p25": 12, "p50": 22, "p75": 35, "yoy": 10},
        "5年经验":                {"p25": 22, "p50": 35, "p75": 55, "yoy": 10},
        "10年+ (持证/资深)":      {"p25": 35, "p50": 60, "p75": 100, "yoy": 12},
    },
    "literature_新闻传播学": {
        "应届生 (一线)":          {"p25": 7,  "p50": 13, "p75": 22, "yoy": 8},
        "3年经验":                {"p25": 12, "p50": 22, "p75": 35, "yoy": 12},
        "5年经验":                {"p25": 22, "p50": 35, "p75": 55, "yoy": 10},
        "10年+ (持证/资深)":      {"p25": 35, "p50": 60, "p75": 100, "yoy": 12},
    },
    "literature_default": {
        "应届生 (一线)":          {"p25": 5,  "p50": 9,  "p75": 15, "yoy": 5},
        "3年经验":                {"p25": 9,  "p50": 15, "p75": 24, "yoy": 8},
        "5年经验":                {"p25": 16, "p50": 26, "p75": 42, "yoy": 8},
        "10年+ (持证/资深)":      {"p25": 30, "p50": 48, "p75": 80, "yoy": 10},
    },
}


# ── ALUMNI_FILLERS Batch 2 第二轮扩 (3 → 5 条 / sub-key) ────────────
# extend (不覆盖) 既有 3 条, 每 sub-key 再加 2 条 → 5 条 total
_ALUMNI_BATCH2_EXTRA = {
    "education_师范": [
        {"tag": "教育局教研员 · 5 年", "quote": "本科师范 + 教育硕士 + 教研员编, 一年 7-12 万 + 编, 政策研究 + 教师培训 + 课程开发是日常, 体制内稳定, 天花板要博士。", "school": "某 985 师范大学课程与教学论 2020 届硕士"},
        {"tag": "民办名校 IB 协调员 · 4 年", "quote": "本科师范 + 海外硕士 + 一线城市民办名校 IB 协调员, 25-40 万/年 + 双休 + 寒暑假, IB 认证 + 海外背景 + 英文双语是真正壁垒。", "school": "某 985 师范 + 海外硕士 2021 届"},
    ],
    "education_学前教育": [
        {"tag": "蒙特梭利国际幼师 · 5 年", "quote": "本科学前 + 蒙特梭利 0-6 AMI 国际认证 + 一线城市国际幼儿园, 12-20 万/年, IB PYP 体系 + 双语 (英/法/西) 是加分。", "school": "某 211 师范大学学前 + AMI 认证 2020 届"},
        {"tag": "幼教科研 · 8 年", "quote": "本科 + 北师大学前硕士 + 省级学前教育研究所 8 年, 6-12 万/年 + 编, 政策研究 + 课程开发是核心。", "school": "某 985 师范大学学前教育 2017 届硕士"},
    ],
    "education_特殊教育": [
        {"tag": "BCBA 行为分析师 · 4 年", "quote": "本科特教 + 美国 BCBA 行为分析师认证 + 一线城市民营自闭症机构, 12-25 万/年, BCBA + 临床督导经验是头部薪资门槛。", "school": "某 985 师范大学特殊教育 + BCBA 2021 届"},
        {"tag": "残联康复专员 · 6 年", "quote": "本科 + 残联康复中心事业编 6 年, 6-10 万/年 + 编, 个别化教育计划 + 家长辅导 + 区域统筹是核心, 工作稳定但案件压力大。", "school": "某师范大学特殊教育 2019 届"},
    ],
    "education_教育技术学": [
        {"tag": "智慧课堂硬件 PM · 5 年", "quote": "本科教育技术 + 希沃 / 鸿合智慧课堂硬件 PM 5 年, 25-45 万/年, 教育产品 + 硬件交付 + 教师培训三栖, 区域销售支持是核心增长点。", "school": "某 211 师范大学教育技术 2020 届"},
        {"tag": "教育部直属事业单位 · 4 年", "quote": "本科 + 硕士 + 教育部教育信息化技术标准委员会 / 中央电教馆 4 年, 8-15 万/年 + 编, 标准研制 + 国家级培训, 硕博是门槛。", "school": "某 985 师范大学教育技术学 2021 届硕士"},
    ],
    "education_科学教育": [
        {"tag": "高校科学教育系教师 · 6 年", "quote": "本科 + 博士 (科学教育 / 课程与教学论) + 211 师范大学科学教育系讲师 6 年, 15-25 万/年 + 编, 教学 + 科研 + 国基委青年项目是常态。", "school": "某 985 师范大学科学教育 2019 届博士"},
        {"tag": "中国科协少儿科普 · 3 年", "quote": "本科 + 中国科协 / 中国青少年科技辅导员协会 3 年, 8-12 万 + 编 / 合同, 科普项目 + 教师培训 + 国家级科创赛事, 出差多。", "school": "某 211 师范大学科学教育 2022 届"},
    ],
    "education_艺术教育": [
        {"tag": "美院附中艺术教师 · 5 年", "quote": "本科艺术教育 + 央美 / 国美附中编制 5 年, 12-20 万/年 + 寒暑假 + 编制, 艺考辅导 + 设计史教学并行, 是少有的'有编 + 有外快'方向。", "school": "某 985 美院艺术教育 2020 届"},
        {"tag": "城市美术馆策展助理 · 4 年", "quote": "本科艺教 + 美院硕士 + 一线城市民营 / 公办美术馆策展助理 4 年, 8-15 万/年 + 合同, 展览策划 + 公共教育工作坊 + 艺术家维护是日常。", "school": "某 985 美院艺术教育 2021 届硕士"},
    ],
    "education_汉语国际教育": [
        {"tag": "中外语合中心 · 4 年", "quote": "本科 + 硕士 + 中外语合中心 (汉办) 4 年, 8-15 万 + 编 / 合同, 海外项目 + 教师培训 + 教材开发, 出差多, 视野最国际化。", "school": "某 211 语言大学汉语国际教育 2021 届硕士"},
        {"tag": "海外中文学校教学主管 · 6 年", "quote": "本科 + 海外硕士 + 北美 / 欧洲华文学校教学主管 6 年, 20-35 万/年, 海外工作签证 + 中英 / 中法双语 + 课程管理经验是稀缺组合。", "school": "某 985 师范大学汉语国际教育 2019 届硕士"},
    ],
    "education_体育教育": [
        {"tag": "国家二级运动员退役教师 · 7 年", "quote": "本科体教 + 国家二级运动员 + 公办高中体育教师编 7 年, 8-15 万/年 + 寒暑假 + 编, 校队带队 + 中考体育 + 大型赛事执裁是中年发展方向。", "school": "某体育学院体育教育 2018 届"},
        {"tag": "体育产业 BD · 4 年", "quote": "本科体教 + 体育营销硕士 + 李宁 / 安踏体育营销 BD 4 年, 18-30 万/年 + 提成, 学校 / 俱乐部资源 + 体育 + 商科双背景是真正壁垒。", "school": "某 985 体育大学体育教育 2021 届硕士"},
    ],
    "education_人文教育": [
        {"tag": "省级教研院文综教研员 · 6 年", "quote": "本科人文 + 教育硕士 + 省级教研院文综教研员 6 年, 8-13 万 + 编, 政策落地 + 课程开发 + 跨学科教研, 硕博是门槛。", "school": "某 985 师范大学课程与教学论 2019 届硕士"},
        {"tag": "通识教育创业 · 3 年", "quote": "本科人文 + 海外硕士 + 通识教育创业 (PBL / IB / AP 通识) 3 年, 拿了天使轮, 跨学科 + 教学法 + 产品三栖, 行业波动需谨慎。", "school": "某 985 师范大学人文教育 + 海外通识硕士 2022 届"},
    ],
    "education_default": [
        {"tag": "高校教师 · 7 年", "quote": "本科 + 博士教育学 + 211 师范大学讲师 7 年, 15-25 万/年 + 编, 教学 + 科研 + 项目 + 学生辅导, 教授门槛是国家级项目。", "school": "某 985 师范大学教育学 2018 届博士"},
        {"tag": "教育智库研究员 · 5 年", "quote": "本科 + 硕士教育学 + 21 世纪教育研究院 / 北师大中国教育与社会发展研究院 5 年, 10-18 万/年, 政策研究 + 报告写作是核心。", "school": "某 985 师范大学教育学 2020 届硕士"},
    ],
    "literature_中国语言文学": [
        {"tag": "高校中文系讲师 · 6 年", "quote": "本科 + 博士 (古代文学 / 现当代文学) + 211 高校中文系讲师 6 年, 12-22 万 + 编, 教学 + 科研 + 国基委青年项目, 教授门槛是 C 刊数量。", "school": "某 985 高校中文系 2019 届博士"},
        {"tag": "古典文献 / 古籍整理 · 4 年", "quote": "本科 + 古典文献硕士 + 中华书局 / 古籍出版社编辑 4 年, 9-15 万/年 + 五险一金, 古籍整理 + 学术编辑是稀缺方向, 读博是终极路径。", "school": "某 985 高校古典文献 2021 届硕士"},
    ],
    "literature_外国语言文学": [
        {"tag": "国际组织译员 · 5 年", "quote": "本科 + 北外 / 上外高翻硕士 + 联合国 / UNESCO / UNDP 项目译员 5 年, 30-60 万/年 (含津贴), CATTI 一级 + 双语 + 国际组织实习是硬门槛。", "school": "某 985 外国语 + 北外高翻 2020 届硕士"},
        {"tag": "高校外语系讲师 · 6 年", "quote": "本科 + 博士 (英美文学 / 比较文学) + 211 高校外语系讲师 6 年, 12-22 万 + 编, 教学 + 翻译 + C 刊发表, 翻译副业 5-10 万/年补充。", "school": "某 985 外国语博士 2019 届"},
    ],
    "literature_新闻传播学": [
        {"tag": "央视 / 主流融媒体记者 · 5 年", "quote": "本科 + 硕士 + 央视新闻 / 新华社记者编制 5 年, 12-22 万 + 编 + 合同, 出差多 + 重大报道 + 政经线条, 体制内成长稳定。", "school": "某 985 大学新闻学 2020 届硕士"},
        {"tag": "MCN / 短视频导演 · 3 年", "quote": "本科网新 + 一线城市 MCN 短视频 / 直播导演 3 年, 15-30 万/年 + 流量提成, 选题 + 脚本 + 拍摄 + 投放四位一体, 内容 + 算法双能力是壁垒。", "school": "某 211 大学网络与新媒体 2022 届"},
    ],
    "literature_default": [
        {"tag": "文学创作 / 自由作家 · 5 年", "quote": "本科文学 + 自由作家 / 网文作者 5 年, 收入差距大 (5-50 万/年, 头部 200 万+), 持续输出 + IP 改编 + 影视化是收入上限。", "school": "某 985 高校中文系 2020 届"},
        {"tag": "出版策划 · 4 年", "quote": "本科 + 硕士 + 三联 / 中信出版社 / 新经典策划编辑 4 年, 12-22 万/年 + 五险一金, 选题 + 作者 + 营销三栖, 名社门槛是硕士 + 海外背景。", "school": "某 985 高校文学硕士 2021 届"},
    ],
}
for _k, _v in _ALUMNI_BATCH2_EXTRA.items():
    if _k in ALUMNI_FILLERS:
        ALUMNI_FILLERS[_k] = list(ALUMNI_FILLERS[_k]) + list(_v)
    else:
        ALUMNI_FILLERS[_k] = list(_v)


# ──────────────────────────────────────────────────────────────────────
# Batch 3 (arts + administration) 扩展 — 14 sub-style
# ──────────────────────────────────────────────────────────────────────
# 6 arts: 艺术学理论 / 音乐表演 / 音乐学 / 舞蹈 / 广播电视 / 戏剧影视
# 8 administration: 人力资源 / 市场营销 / 工程管理 / 劳动社保 / 农林经济 / 物流 / 电子商务 / 旅游
# 复用 _resolve_batch2_key dispatch (上面已 extend), 此处只填 fillers


def _arts_subkey(title=""):
    """根据 title 关键词返回 arts 主题细分 key (1301-1305).
    顺序: 专属在前. 已有 fine-arts / visual-comm / environmental / digital-media / animation
    走默认 arts_default (即原 'arts' filler), 不在此 dispatch.
    """
    if not title:
        return "arts_default"
    t = title
    if any(k in t for k in ["艺术管理", "艺术学理论", "非物质文化遗产", "艺术史论", "文化遗产"]):
        return "arts_艺术学理论"
    if any(k in t for k in ["音乐表演", "音乐演奏", "声乐", "器乐", "钢琴", "小提琴", "民乐"]):
        return "arts_音乐表演"
    if any(k in t for k in ["音乐学", "作曲", "音乐治疗", "流行音乐"]):
        return "arts_音乐学"
    if any(k in t for k in ["舞蹈编导", "舞蹈表演", "舞蹈学", "舞蹈"]):
        return "arts_舞蹈"
    if any(k in t for k in ["广播电视编导", "广播电视", "广播", "电视编导", "录音艺术", "影视摄影", "影视技术", "新媒体艺术"]):
        return "arts_广播电视"
    if any(k in t for k in ["戏剧影视文学", "戏剧学", "电影学", "戏剧影视导演", "戏剧影视美术", "戏剧教育", "表演"]):
        return "arts_戏剧影视"
    return "arts_default"


def _administration_subkey(title=""):
    """根据 title 关键词返回 administration 主题细分 key (1201-1209).
    现有 financial-management/info-mgmt/library-science/public-administration/auditing 走默认.
    """
    if not title:
        return "administration_default"
    t = title
    if any(k in t for k in ["人力资源", "人事", "HR", "招聘"]):
        return "administration_人力资源"
    if any(k in t for k in ["市场营销", "营销", "品牌管理", "市场学"]):
        return "administration_市场营销"
    if any(k in t for k in ["工程管理", "项目管理", "工程造价", "工程经济", "管理科学", "房地产开发"]):
        return "administration_工程管理"
    if any(k in t for k in ["劳动与社会保障", "社会保障", "劳动保障", "劳动关系", "社保"]):
        return "administration_劳动社保"
    if any(k in t for k in ["农林经济", "农村区域发展", "农业经济", "林业经济"]):
        return "administration_农林经济"
    if any(k in t for k in ["物流管理", "物流工程", "供应链", "物流", "采购管理"]):
        return "administration_物流"
    if any(k in t for k in ["电子商务", "跨境电子商务", "电商", "网店"]):
        return "administration_电子商务"
    if any(k in t for k in ["旅游管理", "酒店管理", "会展", "旅游"]):
        return "administration_旅游"
    return "administration_default"


# ── ALUMNI_FILLERS Batch 3 (14 sub-key × 3 + 各 default) ────────────
ALUMNI_FILLERS.update({
    "arts_艺术学理论": [
        {"tag": "美术馆策展助理 · 4 年", "quote": "本科艺术管理 + 央美策展硕士 + 民营美术馆策展助理 4 年, 一年 10-18 万, 策展 + 公共教育 + 艺术家维护是日常, 名馆 (UCCA / 木木) 是进阶门槛。", "school": "某 985 美院艺术管理 2020 届"},
        {"tag": "拍卖行专员 · 3 年", "quote": "本科艺理 + 海外艺术市场硕士 + 嘉德 / 保利拍卖行专员 3 年, 12-25 万/年 + 提成, 鉴定 + 客户 + 拍卖会执行三栖, 艺术 + 商业双背景是真正壁垒。", "school": "某 985 美院艺术管理 + 海外硕士 2021 届"},
        {"tag": "文化产业 PM · 5 年", "quote": "本科 + 文化部 / 故宫文创 / 区文化馆 5 年, 8-15 万/年 + 编 / 合同, 政策落地 + 项目策划 + 跨界合作, 体制内稳定, 编制是稀缺。", "school": "某 985 美院艺术理论 2020 届"},
    ],
    "arts_音乐表演": [
        {"tag": "交响乐团演奏员 · 6 年", "quote": "本科音乐表演 (小提琴 / 中提琴) + 入国家交响乐团 6 年, 18-35 万/年 + 编, 每周排练 4-5 次 + 演出季, 名团 (国交 / 上交) 是塔尖。", "school": "某音乐学院音乐表演 2019 届"},
        {"tag": "音乐教师 + 钢琴私教 · 4 年", "quote": "本科 + 公办中学音乐编 + 钢琴私教 4 年, 5-7 万 + 编 + 私教 8-15 万/年, 私教是主要收入, 但音乐学院文凭是家长口碑门槛。", "school": "某音乐学院音乐表演 2021 届"},
        {"tag": "音乐剧 / 独立音乐人 · 3 年", "quote": "本科 + 北京音乐剧 / 独立巡演 3 年, 收入差距大 (8-30 万/年), 演出场次 + 制作合作是主要变量, 副业接配音 / 商演补充。", "school": "某 211 艺术学院音乐表演 2022 届"},
    ],
    "arts_音乐学": [
        {"tag": "高校音乐学讲师 · 6 年", "quote": "本科 + 博士 (中央音乐学院音乐学) + 211 高校音乐系讲师 6 年, 15-25 万/年 + 编, 教学 + 中国音乐史 / 民族音乐学研究 + C 刊, 副教授门槛是国基委。", "school": "某中央音乐学院音乐学 2019 届博士"},
        {"tag": "音乐编辑 / 杂志 · 4 年", "quote": "本科音乐学 + 人民音乐出版社 / 音乐周报编辑 4 年, 8-15 万/年 + 五险, 选题 + 乐评 + 唱片评论, 是少有的 '体制 + 文化输出' 双栖方向。", "school": "某 985 音乐学院 2021 届"},
        {"tag": "作曲家 / 编曲 · 5 年", "quote": "本科作曲 + 自由职业 (影视配乐 / 游戏 / 综艺) 5 年, 收入差距 12-50 万/年, 头部项目 (米哈游 / 大型综艺) 单笔 5-20 万, 持续输出 + 圈内人脉是真壁垒。", "school": "某音乐学院作曲与作曲技术理论 2020 届"},
    ],
    "arts_舞蹈": [
        {"tag": "国家级舞团演员 · 5 年", "quote": "本科舞蹈表演 + 中国歌舞剧院 / 中央芭蕾舞团 5 年, 15-25 万/年 + 编, 每周排练 6 天 + 巡演, 30 岁后转编导 / 教师是普遍路径。", "school": "某北京舞蹈学院舞蹈表演 2020 届"},
        {"tag": "舞蹈学院教师 · 6 年", "quote": "本科 + 北舞硕士 + 211 师范大学舞蹈系教师 6 年, 12-22 万/年 + 编 + 寒暑假, 比赛 / 编创 + 教学双线, 国家奖项是晋升加分。", "school": "某 211 师范大学舞蹈编导 2019 届硕士"},
        {"tag": "商业编导 / 综艺 · 3 年", "quote": "本科舞蹈编导 + 综艺 / MV / 演唱会编导 3 年, 18-35 万/年 + 项目提成, 浙江卫视 / 灿星 / 米未 项目, 抗压强但圈子人脉是核心。", "school": "某 211 艺术学院舞蹈编导 2022 届"},
    ],
    "arts_广播电视": [
        {"tag": "央视 / 卫视编导 · 5 年", "quote": "本科广播电视编导 + 央视 / 浙江 / 湖南卫视编导 5 年, 15-30 万/年 + 编 / 合同, 选题 + 拍摄 + 后期 一肩挑, 大节目 (春晚 / 综艺 S+) 是金字招牌。", "school": "某 985 大学广播电视编导 2020 届"},
        {"tag": "MCN / 短视频导演 · 3 年", "quote": "本科广电编导 + 一线城市 MCN / 抖音独立短视频团队 3 年, 18-40 万/年 + 流量提成, 选题 + 脚本 + 后期 + 投放四位一体, 头部账号孵化是收入上限。", "school": "某 211 大学广播电视编导 2022 届"},
        {"tag": "网剧 / 网综制片 · 4 年", "quote": "本科 + 爱奇艺 / 腾讯视频 / 优酷 制片助理 → 制片人 4 年, 25-50 万/年, S 级项目预算上千万, 制片人 + 投资人 + 平台三方博弈是日常。", "school": "某 985 大学广播电视编导 2021 届"},
    ],
    "arts_戏剧影视": [
        {"tag": "电影编剧 · 5 年", "quote": "本科戏剧影视文学 + 北电编剧硕士 + 自由职业编剧 5 年, 12-50 万/年 (剧本预付 + 分成), 影视寒冬下项目少, 网剧 / 短剧是出路, 头部编剧 (开心麻花 / 阿里影业) 是塔尖。", "school": "某 985 北京电影学院戏剧影视文学 2020 届硕士"},
        {"tag": "话剧 / 戏剧导演 · 4 年", "quote": "本科戏剧学 + 中戏 / 上戏导演硕士 + 民营剧团 / 国家剧院导演 4 年, 10-25 万/年, 国家级剧院 (国话 / 北人艺) 编制稀缺, 民营商业话剧 + 教学是稳健补充。", "school": "某中央戏剧学院戏剧学 2021 届硕士"},
        {"tag": "影视宣发 / 营销 · 3 年", "quote": "本科戏剧影视 + 互联网影业宣发 (爱奇艺 / 阿里影业 / 灯塔) 3 年, 15-30 万/年, 选题 + 物料 + 投放 + 短视频引流, 内容 + 数据双能力是真壁垒。", "school": "某 985 北京电影学院戏剧影视文学 2022 届"},
    ],
    "arts_default": [
        {"tag": "艺术行业 · 4 年", "quote": "本科艺术类 + 文化 / 文创 / 演艺行业 4 年, 8-20 万/年, 跨界 (艺术 + 商业 + 教育) 是稀缺组合, 高校教师需读博。", "school": "某 985 美院 / 音乐学院艺术类 2021 届"},
        {"tag": "继续深造", "quote": "本科艺术类就业窄, 一般建议读研 (艺术学硕士 / 艺术管理 / 海外 MA), 中央 / 中国 + 央美 + 北电 + 央音 是头部, 硕博是高校 / 头部机构门槛。", "school": "某 985 艺术院校 2025 届"},
        {"tag": "自由职业 + 工作室", "quote": "本科艺术类 + 自由职业 (商演 / 设计 / 教学 / 内容) 5 年, 收入差距大 (5-50 万/年), 持续输出 + IP 沉淀 + 社交资源是壁垒。", "school": "某艺术院校艺术类 2020 届"},
    ],
    "administration_人力资源": [
        {"tag": "互联网大厂 HRBP · 4 年", "quote": "本科 HRM + 字节 / 阿里 / 美团 HRBP 4 年, 25-45 万/年, 业务搭子 + 招聘 + 绩效 + 文化建设, 数据 + 业务理解 + 沟通三栖是核心。", "school": "某 985 高校人力资源管理 2021 届"},
        {"tag": "咨询公司顾问 · 3 年", "quote": "本科 HRM + 美世 / 怡安 / 韦莱韬悦 HR 咨询 3 年, 22-40 万/年 + 项目奖金, 薪酬 / 组织设计 / 人才盘点项目, 985 + 顶咨实习是入门门槛。", "school": "某 211 高校人力资源 2022 届"},
        {"tag": "制造业总部 HR 总监 · 8 年", "quote": "本科 HRM + MBA + 制造业总部 HR 总监 8 年, 50-100 万/年 + 股票期权, 战略 + 组织 + 干部管理, 校招进 + 内部晋升是主流, 跳槽溢价高。", "school": "某 985 高校人力资源 + 长江 MBA 2017 届"},
    ],
    "administration_市场营销": [
        {"tag": "互联网品牌 / 用户运营 · 4 年", "quote": "本科营销 + 字节 / 腾讯 / 美团品牌或用户运营 4 年, 25-50 万/年, 用户增长 + 品牌 + 投放三栖, 数据 + 创意双能力是壁垒。", "school": "某 985 高校市场营销 2021 届"},
        {"tag": "4A / Local 广告 AE · 3 年", "quote": "本科营销 + Ogilvy / 蓝标 / 利欧 / 群邑 AE → AM 3 年, 18-32 万/年, 客户关系 + 提案 + 创意把关, 客户 (宝洁 / 联合利华 / 阿里) 是金主。", "school": "某 211 大学市场营销 2022 届"},
        {"tag": "快消 / 消费品市场部 · 5 年", "quote": "本科 + MBA + 联合利华 / 宝洁 / 元气森林 市场总监助理 5 年, 35-65 万/年, 品牌战略 + 新品 + 渠道 + 媒介, 校招 MT 计划是主流入口。", "school": "某 985 高校营销 + 中欧 MBA 2020 届"},
    ],
    "administration_工程管理": [
        {"tag": "央企工程造价 · 5 年", "quote": "本科工程管理 + 一级造价师 + 中建 / 中铁 / 中交央企造价 5 年, 12-25 万/年 + 编, 工程量清单 + 招投标 + 成本控制, 持证 (造价 / 监理) 是加薪通道。", "school": "某 985 高校工程管理 2020 届"},
        {"tag": "设计院项目经理 · 6 年", "quote": "本科工程 + 一级建造师 + 中建设计院 / 民营建筑事务所 项目经理 6 年, 25-45 万/年 + 项目奖金, 进度 + 成本 + 质量 + 安全四统筹, 持证是硬门槛。", "school": "某 985 高校工程管理 2019 届"},
        {"tag": "房地产投拓 · 4 年", "quote": "本科 + 房地产硕士 + 万科 / 龙湖 / 华润投拓 4 年, 25-45 万/年, 拿地测算 + 政府关系 + 投资逻辑, 地产寒冬下转商业 / 产业园是出路。", "school": "某 985 高校工程管理 + 房地产硕士 2021 届"},
    ],
    "administration_劳动社保": [
        {"tag": "人社局公务员 · 5 年", "quote": "本科劳动与社会保障 + 省 / 市人社局公务员 5 年, 6-12 万/年 + 编, 劳动监察 / 工伤 / 失业保险经办, 体制内稳定, 副科 / 正科是 10 年门槛。", "school": "某 211 高校劳动与社会保障 2020 届"},
        {"tag": "商业保险公司核保 · 4 年", "quote": "本科 + 中国人寿 / 平安 / 太保 健康险核保 4 年, 12-22 万/年 + 编 / 合同, 核保 + 理赔 + 反欺诈, 精算 + 法律双背景是高薪门槛。", "school": "某 985 高校劳动与社会保障 2021 届"},
        {"tag": "企业福利 / 薪酬专员 · 3 年", "quote": "本科 + 互联网大厂福利 / 薪酬专员 3 年, 18-30 万/年, 五险一金 + 商保 + EAP + 期权 + 福利平台, 跨学科 (HRM + 社保 + 财税) 是稀缺组合。", "school": "某 211 高校劳动与社会保障 2022 届"},
    ],
    "administration_农林经济": [
        {"tag": "农业银行 / 农信社 · 5 年", "quote": "本科农林经济 + 农业银行 / 省农信社三农金融部 5 年, 10-18 万/年 + 编, 涉农贷款 + 普惠金融 + 乡村振兴项目, 国家政策红利期。", "school": "某 985 农业大学农林经济管理 2020 届"},
        {"tag": "农业农村部 / 农业局 · 4 年", "quote": "本科 + 硕士 + 农业农村部 / 省农业农村厅 4 年, 8-15 万 + 编, 农业政策研究 + 项目督导 + 数据统计, 体制内稀缺 + 国家战略对口。", "school": "某 985 农业大学农林经济硕士 2021 届"},
        {"tag": "农业产业化龙头企业 · 3 年", "quote": "本科 + 牧原 / 温氏 / 新希望 / 中粮等农业龙头企业管培生 3 年, 15-30 万/年, 战略 + 运营 + 供应链, 农业 + 商业双背景是稀缺组合, 行业风口期。", "school": "某 211 农业大学农林经济管理 2022 届"},
    ],
    "administration_物流": [
        {"tag": "顺丰 / 京东物流运营 · 4 年", "quote": "本科物流 + 顺丰 / 京东物流 / 菜鸟运营 4 年, 18-35 万/年, 网络规划 + 调度 + 成本优化, 运营 + 数据 + 系统三栖是核心, 校招 MT 是主流入口。", "school": "某 211 高校物流管理 2021 届"},
        {"tag": "跨境物流 / 海运 · 5 年", "quote": "本科物流 + DHL / 马士基 / FedEx 跨境物流 5 年, 22-45 万/年, 报关 + 货代 + 多式联运, 英语 + 国际贸易 + 跨境政策三栖是真壁垒。", "school": "某 985 海洋大学物流管理 2020 届"},
        {"tag": "制造业供应链经理 · 6 年", "quote": "本科 + 富士康 / 立讯精密 / 比亚迪 供应链经理 6 年, 28-50 万/年, 采购 + 计划 + 库存 + 物流 全链路, SCOR / APICS 持证是加薪通道。", "school": "某 985 高校物流管理 + 供应链硕士 2019 届"},
    ],
    "administration_电子商务": [
        {"tag": "天猫 / 拼多多类目运营 · 4 年", "quote": "本科电商 + 阿里 / 拼多多 / 京东类目运营 4 年, 22-40 万/年, GMV + ROI + 选品 + 营销策略, 数据 + 内容 + 投放三栖, 行业波动大但上限高。", "school": "某 211 高校电子商务 2021 届"},
        {"tag": "TikTok 跨境电商 · 3 年", "quote": "本科电商 + 跨境电商团队 (TikTok / 亚马逊 / 独立站) 3 年, 18-35 万/年 + 提成, 选品 + 内容 + 投放 + 物流, 英语 + 海外 + 内容创业三栖是壁垒。", "school": "某 985 高校电子商务 2022 届"},
        {"tag": "电商创业 · 2 年", "quote": "本科电商 + 自营服饰 / 美妆品牌 2 年, GMV 数百万, 抖音直播 + 私域 + 小红书种草, 行业卷但独立站 + DTC 品牌仍有窗口。", "school": "某 211 高校电子商务 2023 届"},
    ],
    "administration_旅游": [
        {"tag": "携程 / 美团酒店 · 4 年", "quote": "本科旅游管理 + 携程 / 美团酒店事业部 4 年, 22-40 万/年, BD + 运营 + 内容 + 数据, 互联网平台运营 + 旅游行业双背景是壁垒。", "school": "某 211 高校旅游管理 2021 届"},
        {"tag": "五星酒店管培生 · 5 年", "quote": "本科酒店管理 + 万豪 / 希尔顿 / 洲际管培生 → 部门经理 5 年, 12-25 万/年, 前厅 / 餐饮 / 销售轮岗, 海外培训 + 集团内调是发展路径。", "school": "某 985 旅游学院酒店管理 2020 届"},
        {"tag": "MICE 会展项目经理 · 4 年", "quote": "本科旅游 + 会展公司 / 大型展览策划 4 年, 15-30 万/年 + 项目奖金, 客户 + 策划 + 执行 + 现场, 跨界 (旅游 + 营销 + 项目) 是稀缺组合。", "school": "某 211 高校旅游管理 (会展方向) 2021 届"},
    ],
    "administration_default": [
        {"tag": "管理类 + 大厂管培 · 4 年", "quote": "本科管理类 + 大厂 (BAT / 央企 / 四大) 管培生 4 年, 18-35 万/年, 轮岗后定岗运营 / 战略 / HR / 业务, 985 + 综合能力是门槛。", "school": "某 985 高校管理类 2021 届"},
        {"tag": "公务员 + 体制内", "quote": "本科 + 公考进省 / 市政府机关 (经发委 / 财政局 / 商务局) 4 年, 6-12 万/年 + 编, 稳定 + 决策参与 + 政策落地, 副科 / 正科是 8-10 年门槛。", "school": "某 211 高校管理类 2021 届"},
        {"tag": "继续深造 (MBA / 海外硕士)", "quote": "本科 + 中欧 / 长江 MBA 或海外硕士 (LSE / NUS / HKUST), MBA 是晋升管理岗加速器, 海外硕士是跨界 (咨询 / 投资) 入口。", "school": "某 985 高校管理类 2020 届 + MBA"},
    ],
})


# ── EMPLOYMENT_FILLERS Batch 3 (14 sub-key × 5) ─────────────────────
EMPLOYMENT_FILLERS.update({
    "arts_艺术学理论": [
        ("美术馆 / 博物馆", "省级 / 民营美术馆 + 国家博物馆 + UCCA / 木木", 25, "策展 + 公共教育 + 收藏研究, 8-18 万/年 + 编 / 合同, 名馆稀缺"),
        ("拍卖行 / 画廊", "嘉德 / 保利 / 苏富比 / 佳士得 + 一线画廊", 20, "鉴定 + 客户 + 拍卖, 12-25 万/年 + 提成"),
        ("文化产业 / 文创", "故宫文创 / 上博文创 + 文化部直属机构", 20, "策划 + IP + 跨界, 10-22 万/年"),
        ("文化公务员 / 事业单位", "文旅部 / 文物局 / 各地文化馆", 15, "需公考, 6-12 万 + 编, 政策落地 + 资源调配"),
        ("继续深造 (艺管 / 海外 MA)", "央美艺管 / 海外 Art Business / Sotheby's Institute", 20, "硕博是名馆 / 拍卖行 + 高校门槛"),
    ],
    "arts_音乐表演": [
        ("国家级 / 省级乐团", "国交 / 上交 / 央芭 + 各省歌舞剧院", 25, "18-35 万/年 + 编, 名团稀缺 + 终身演奏"),
        ("音乐学院 / 中小学教师", "中央 / 中国 / 上海音院 + 公办中小学音乐编", 25, "高校 15-25 万 / 中小学 5-8 万 + 寒暑假 + 编"),
        ("钢琴 / 器乐私教", "一对一私教 + 培训机构 + 工作室", 25, "一线 12-30 万/年, 名校文凭 + 比赛奖项是口碑门槛"),
        ("商业演出 / 独立音乐人", "音乐剧 / 巡演 / 配乐 / 婚礼", 15, "8-30 万/年, 项目制收入, 圈内人脉是核心"),
        ("继续深造 (硕博 / 海外)", "中央音院 / 上音 + 海外茱莉亚 / 皇家音乐学院", 10, "硕博是高校 / 国家乐团门槛"),
    ],
    "arts_音乐学": [
        ("高校音乐学 / 师范音乐教师", "211 高校音乐系 + 中小学音乐编", 35, "高校 15-25 万 + 编 (需博), 中小学 5-8 万 + 编"),
        ("音乐编辑 / 出版", "人音出版社 / 音乐周报 / 音乐杂志", 15, "8-15 万 + 五险, 选题 + 乐评 + 唱片编辑"),
        ("作曲 / 编曲 (自由职业)", "影视配乐 / 游戏音乐 / 综艺", 15, "12-50 万/年, 头部项目单笔 5-20 万, 持续输出是壁垒"),
        ("艺术管理 / 演出公司", "国家大剧院 / 民营演出公司", 15, "10-20 万/年, 策划 + 推广 + 制作"),
        ("继续深造 (硕博)", "中央音乐学院音乐学 / 海外民族音乐学", 20, "硕博是高校 / 头部研究机构门槛"),
    ],
    "arts_舞蹈": [
        ("国家级 / 省级舞团", "国家歌舞剧院 / 央芭 / 各省歌舞团", 25, "15-25 万/年 + 编, 30 岁后转编导 / 教师"),
        ("舞蹈学院 / 中小学教师", "北舞 / 上舞 + 师范大学舞蹈系 + 中小学舞蹈编", 30, "高校 12-22 万 + 编, 中小学 4-7 万 + 编"),
        ("商业编导 / 综艺", "浙江卫视 / 灿星 / 米未 编导", 15, "18-35 万/年, 项目提成, 圈子 + 人脉是核心"),
        ("自由职业 + 工作室", "舞蹈培训机构 + 私人教练 + 商演", 20, "10-25 万/年, 工作室是终点, 中考 / 艺考辅导是外快"),
        ("继续深造 (硕博 / 海外)", "北舞 / 海外现代舞 (Juilliard / NYU)", 10, "硕博是高校 + 国家级编导门槛"),
    ],
    "arts_广播电视": [
        ("央视 / 卫视 / 融媒体", "央视 / 浙江 / 湖南 / 北京 / 上海广电", 25, "15-30 万/年 + 编 / 合同, S+ 节目是金字招牌"),
        ("互联网视频平台", "爱奇艺 / 腾讯视频 / 优酷 / B 站制片", 25, "25-50 万/年, S 级项目预算上千万"),
        ("MCN / 短视频 / 独立工作室", "抖音 / 快手 / B 站独立 MCN", 20, "18-40 万/年 + 流量提成, 头部账号孵化"),
        ("广告 / 4A 创意公司", "Ogilvy / TBWA + Local 头部广告", 15, "15-30 万/年, 客户 + 创意 + 制作三栖"),
        ("继续深造 (硕博 / 海外)", "中传 / 北电硕士 + 海外影视硕士", 15, "硕博是央媒高层 / 高校教师门槛"),
    ],
    "arts_戏剧影视": [
        ("电影 / 电视剧编剧", "自由职业 + 阿里影业 / 爱奇艺 / 开心麻花", 25, "剧本预付 5-30 万 + 分成, 影视寒冬下网剧 / 短剧是出路"),
        ("话剧 / 戏剧院团", "国家话剧院 / 北人艺 / 上戏剧院 / 民营剧团", 15, "10-25 万/年, 国家级稀缺, 民营商业话剧 + 教学补充"),
        ("影视宣发 / 营销", "爱奇艺 / 阿里影业 / 灯塔宣发", 20, "15-30 万/年, 物料 + 投放 + 短视频引流, 数据 + 创意双能力"),
        ("视频平台内容采购 / 自制", "爱奇艺 / 腾讯视频 / 优酷剧集采购 / 自制", 20, "20-40 万/年, 选题 + 评估 + 制作管理"),
        ("继续深造 (硕博 / 海外)", "北电 / 中戏 / 上戏 + 海外影视编剧硕士", 20, "硕博是头部编剧 / 高校教师门槛"),
    ],
    "arts_default": [
        ("艺术行业 (文创 / 演艺 / 设计)", "文创公司 / 演艺集团 / 设计工作室", 35, "8-25 万/年, 跨界能力是壁垒"),
        ("高校 / 中小学艺术教师", "高校艺术系 + 公办中小学艺术编", 25, "高校需博 15-25 万 + 编, 中小学 4-7 万 + 编"),
        ("自由职业 / 工作室", "商演 / 设计 / 教学 / 内容创业", 15, "5-50 万/年, 持续输出 + IP 沉淀"),
        ("公务员 / 事业单位", "文化部 / 文旅局 / 文化馆", 10, "需公考, 6-12 万 + 编"),
        ("继续深造 (硕博 / 海外)", "央美 / 央音 / 北电 + 海外 MA", 15, "硕博是高校 / 头部机构门槛"),
    ],
    "administration_人力资源": [
        ("互联网大厂 HRBP", "字节 / 阿里 / 美团 / 腾讯 / 百度", 30, "25-45 万/年, 业务搭子 + 招聘 + 绩效"),
        ("咨询公司 HR 顾问", "美世 / 怡安 / 韦莱韬悦 / 麦肯锡 HR", 20, "22-40 万/年 + 项目奖金, 985 + 顶咨实习是门槛"),
        ("制造业 / 央企 HR 总监", "央企 HR 总部 + 制造业头部 HR 总监", 20, "校招 + 内部晋升, 8 年可达 50-100 万 + 期权"),
        ("HR SaaS / RPO 公司", "北森 / Moka / 智联 / 前程无忧 + RPO", 15, "15-28 万/年, 产品 + 业务双能力"),
        ("继续深造 (HRM 硕博 / MBA)", "中欧 / 长江 MBA + 海外 HRM 硕士", 15, "MBA 是晋升管理岗加速器"),
    ],
    "administration_市场营销": [
        ("互联网品牌 / 用户运营", "字节 / 腾讯 / 美团品牌 / 增长", 30, "25-50 万/年, 数据 + 创意双能力"),
        ("4A / Local 广告 AE / 策划", "Ogilvy / 蓝标 / 利欧 / WPP / 群邑", 20, "18-32 万/年, 客户 + 提案"),
        ("快消 / 消费品市场部", "宝洁 / 联合利华 / 元气森林 / 完美日记", 20, "校招 MT, 25-45 万/年, MBA 是晋升加速"),
        ("数字营销 / KOL 运营", "抖音 / 小红书 / B 站 + MCN", 15, "15-30 万/年, 内容 + 算法 + 数据三栖"),
        ("继续深造 (硕士 / MBA)", "营销硕士 / MBA / 海外营销硕士", 15, "硕博是头部品牌 / 高校教师门槛"),
    ],
    "administration_工程管理": [
        ("央企工程造价 / 项目", "中建 / 中铁 / 中交 / 中冶造价 / 项目", 30, "12-25 万/年 + 编, 持证 (造价 / 监理) 加薪"),
        ("设计院 / 建筑事务所", "中建设计院 / SOM / 同济院 项目经理", 25, "25-45 万/年 + 项目奖金, 持证是门槛"),
        ("房地产投拓 / 项目", "万科 / 龙湖 / 华润投拓 + 商业地产", 15, "25-45 万/年, 地产寒冬转商业 / 产业园"),
        ("工程咨询 / 监理", "中咨 / 北京国际工程咨询 + 监理公司", 15, "12-25 万/年, 一级建造师 + 咨询师持证"),
        ("继续深造 (工管硕博 / MBA)", "工管硕士 / 工程项目管理 PMP", 15, "硕博是头部设计院 / 高校门槛"),
    ],
    "administration_劳动社保": [
        ("人社局 / 社保经办公务员", "省 / 市 / 县人社局 + 社保中心 + 工会", 35, "需公考, 6-12 万 + 编, 副科 / 正科 10 年门槛"),
        ("商业保险公司核保 / 理赔", "国寿 / 平安 / 太保 健康险 / 团险", 20, "12-22 万/年 + 编 / 合同, 精算 + 法律双背景高薪"),
        ("企业福利 / 薪酬专员", "互联网 / 央企 / 外企福利 + EAP", 15, "18-30 万/年, HRM + 社保 + 财税复合"),
        ("劳动咨询 / 法律服务", "法律咨询 / 劳动仲裁中心 + 工会", 10, "10-20 万/年, 法律 + 社保双背景"),
        ("继续深造 (社保硕博 / MPA)", "中国人民大学社会保障 + 海外 MSW", 20, "硕博是高校 / 政府智库门槛"),
    ],
    "administration_农林经济": [
        ("农业银行 / 农信社", "农行总分行 / 省农信社三农金融部", 30, "10-18 万/年 + 编, 涉农金融 + 普惠 + 乡村振兴"),
        ("农业农村部 / 农业局公务员", "农业农村部 / 省农业农村厅 / 县农业局", 25, "需公考, 8-15 万 + 编, 政策研究 + 数据"),
        ("农业产业化龙头企业", "牧原 / 温氏 / 新希望 / 中粮 / 隆平高科", 20, "管培生 15-30 万/年, 战略 + 运营 + 供应链"),
        ("农村合作社 / 涉农 NGO", "省级合作社联社 + 涉农 NGO + 乡村振兴办", 10, "8-15 万/年, 国家政策红利期"),
        ("继续深造 (农经硕博)", "中国农大 / 南农 / 浙大农经硕博", 15, "硕博是高校 / 农业部 / 智库门槛"),
    ],
    "administration_物流": [
        ("快递 / 综合物流运营", "顺丰 / 京东物流 / 菜鸟 / 中通", 30, "18-35 万/年, 网络规划 + 调度 + 成本"),
        ("跨境物流 / 海运", "DHL / 马士基 / FedEx + 跨境电商物流", 20, "22-45 万/年, 英语 + 国际贸易 + 跨境政策"),
        ("制造业供应链管理", "富士康 / 立讯 / 比亚迪 / 宁德时代 SCM", 25, "28-50 万/年, SCOR / APICS 持证"),
        ("物流地产 / 仓储", "普洛斯 / 京东产发 / 顺丰冷链", 10, "20-35 万/年, 物流 + 房地产复合"),
        ("继续深造 (物流硕博 / MBA)", "上海海事 / 北交大 / 海外物流硕士", 15, "硕博是头部企业管理 / 高校门槛"),
    ],
    "administration_电子商务": [
        ("天猫 / 拼多多 / 京东类目运营", "阿里 / 拼多多 / 京东 类目运营", 30, "22-40 万/年, GMV + ROI + 选品 + 营销"),
        ("跨境电商 (TikTok / 亚马逊)", "TikTok Shop / 亚马逊 / 独立站", 25, "18-35 万/年 + 提成, 英语 + 海外 + 内容三栖"),
        ("电商创业 / 自营品牌", "服饰 / 美妆 / 食品 自营品牌 (抖音 / 小红书)", 15, "GMV 数百万, 独立站 / DTC 仍有窗口"),
        ("MCN / 直播运营", "字节 / 快手 + MCN 直播公司", 15, "15-30 万/年, 内容 + 选品 + 投放"),
        ("继续深造 (电商硕士 / MBA)", "电商硕士 + 海外 Digital Marketing", 15, "硕博是头部平台 / 高校教师门槛"),
    ],
    "administration_旅游": [
        ("OTA 平台 (携程 / 美团 / 飞猪)", "携程 / 美团酒店 / 飞猪 / 同程", 30, "22-40 万/年, BD + 运营 + 内容 + 数据"),
        ("五星酒店 / 国际酒店集团", "万豪 / 希尔顿 / 洲际 / 雅高 管培生", 25, "12-25 万/年, 前厅 / 餐饮 / 销售轮岗, 海外培训"),
        ("MICE 会展公司", "上海 / 北京会展公司 + 大型展览策划", 15, "15-30 万/年, 客户 + 策划 + 执行"),
        ("文旅 / 景区运营", "故宫 / 黄山 / 长隆 / 华侨城景区运营", 15, "10-20 万/年, 旅游 + 营销 + 项目复合"),
        ("继续深造 (旅游硕博 / 海外 MICE)", "中山旅院 / 港理工 + 海外 MBA in Hospitality", 15, "硕博是高校 / 头部集团门槛"),
    ],
    "administration_default": [
        ("大厂管培生 / 业务运营", "BAT / 央企 / 四大 管培", 30, "18-35 万/年, 985 + 综合能力门槛"),
        ("公务员 / 体制内", "省 / 市经发委 / 财政局 / 商务局", 25, "需公考, 6-12 万 + 编"),
        ("咨询公司 / 投行", "MBB / 四大 / 投行后台", 15, "20-40 万/年, 985 + 顶咨实习"),
        ("民营 / 中小企业管理岗", "上市公司 / 头部民营总部管理", 15, "12-25 万/年, 5 年可达管理"),
        ("继续深造 (MBA / 海外硕士)", "中欧 / 长江 MBA + 海外管理硕士", 15, "MBA 是晋升加速器"),
    ],
})


# ── COMPANIES_FILLERS Batch 3 (14 × 8) ───────────────────────────────
COMPANIES_FILLERS.update({
    "arts_艺术学理论": [
        "中央美术学院美术馆 / 中国美术馆", "UCCA / 木木 / 龙美术馆 / 余德耀美术馆",
        "嘉德拍卖 / 保利拍卖 / 苏富比 / 佳士得", "故宫博物院 / 中国国家博物馆 / 上海博物馆",
        "故宫文创 / 上博文创 / 国博文创", "文化和旅游部 / 国家文物局",
        "万达文化 / 阿里文娱 / 腾讯文化",
        "中央美院艺管 + 海外 Sotheby's Institute",
    ],
    "arts_音乐表演": [
        "中国国家交响乐团 / 中央芭蕾舞团", "上海交响乐团 / 国家大剧院管弦乐团",
        "中央音乐学院 / 上海音乐学院 / 中国音乐学院",
        "省级歌舞剧院 (北京 / 上海 / 广州 / 深圳)",
        "公办中小学音乐教师编制", "民营钢琴 / 器乐培训机构 + 工作室",
        "音乐剧团 (七幕人生 / 文广演艺)", "海外茱莉亚 / 皇家音乐学院 + 国际乐团",
    ],
    "arts_音乐学": [
        "211 高校音乐系 (北师大 / 华师大 / 南师大)", "中央 / 上海 / 中国音乐学院音乐学系",
        "人民音乐出版社 / 音乐周报 / 三联爱乐", "国家大剧院 + 北京 / 上海音乐节",
        "影视音乐工作室 (米哈游 / 网易 / 腾讯)",
        "民营演出公司 (太合音乐 / 摩登天空)",
        "中国艺术研究院 + 民族音乐研究所", "海外 Eastman / 茱莉亚音乐学博士项目",
    ],
    "arts_舞蹈": [
        "中国歌舞剧院 / 中央芭蕾舞团 / 中国东方歌舞团",
        "省级歌舞剧院 (北京 / 上海 / 广州 / 深圳)",
        "北京舞蹈学院 / 上海戏剧学院舞蹈学院",
        "211 师范大学舞蹈系 + 中小学舞蹈编制",
        "民营舞蹈培训 + 私人教练工作室",
        "综艺 / 演唱会编导 (浙江卫视 / 灿星 / 米未)",
        "婚礼 / 商演 / 时装秀编导",
        "海外现代舞 (NYU Tisch / Juilliard)",
    ],
    "arts_广播电视": [
        "中央广播电视总台 / 央视 / 央广", "浙江卫视 / 湖南卫视 / 江苏卫视 / 东方卫视",
        "爱奇艺 / 腾讯视频 / 优酷 / B 站 / 抖音",
        "Ogilvy / TBWA / 蓝标 / 利欧 4A 广告",
        "省级广电融媒体 + 城市电视台",
        "民营 MCN (洋葱 / 美 ONE / 无忧传媒)",
        "新闻节目制作公司 + 纪录片公司",
        "中传 / 北电硕博 + 海外影视硕士",
    ],
    "arts_戏剧影视": [
        "北京电影学院 / 中央戏剧学院 / 上海戏剧学院",
        "中国国家话剧院 / 北京人艺 / 上戏剧院",
        "爱奇艺 / 阿里影业 / 万达影业 / 华谊兄弟",
        "腾讯视频 / 优酷自制剧 + 网剧厂牌",
        "开心麻花 / 抓马艾克斯 / 民营话剧团",
        "影视宣发 (灯塔 / 猫眼 / 淘票票) + KOL 营销",
        "广告 / 4A 创意 (BBDO / DDB / Saatchi)",
        "海外 USC / NYU Tisch 电影硕士",
    ],
    "arts_default": [
        "央美 / 央音 / 北电 / 中戏 + 海外艺术院校",
        "省级美术馆 / 博物馆 / 文化馆",
        "互联网文娱 (阿里影业 / 腾讯文化 / 字节)",
        "公办艺术教育 (中小学 + 师范大学艺术系)",
        "民营培训机构 + 工作室",
        "文化部 + 文旅局 + 文物局",
        "演艺公司 + 院团 + 巡演公司",
        "海外艺术硕博 (RCA / Parsons / 中央圣马丁)",
    ],
    "administration_人力资源": [
        "字节 / 阿里 / 美团 / 腾讯 / 百度 HRBP",
        "美世 / 怡安 / 韦莱韬悦 HR 咨询",
        "麦肯锡 / BCG / Bain HR 实践组",
        "央企总部 HR / 制造业头部 HR (海尔 / 美的)",
        "外企 HR (宝洁 / 联合利华 / GE)",
        "HR SaaS (北森 / Moka / 智联 / 前程无忧)",
        "RPO 招聘外包 (科锐 / 翰德 / 万宝盛华)",
        "中欧 / 长江 / 复旦 / 北大光华 MBA",
    ],
    "administration_市场营销": [
        "字节跳动 / 腾讯 / 美团 品牌部 / 用户增长",
        "Ogilvy / 蓝标 / 利欧 / WPP / 群邑 4A",
        "宝洁 / 联合利华 / 玛氏 / 雀巢 快消 MT",
        "元气森林 / 完美日记 / 喜茶 新消费品牌",
        "字节 / 阿里 / 腾讯 数字营销 (信息流 / 效果广告)",
        "Local 头部广告 (天与空 / 胜加 / 时趣)",
        "抖音 / 小红书 / B 站 KOL 运营 / MCN",
        "中欧 / 长江 / Kellogg MBA in Marketing",
    ],
    "administration_工程管理": [
        "中建 / 中铁 / 中交 / 中冶 央企造价 / 项目",
        "中建设计院 / 同济院 / SOM 项目经理",
        "万科 / 龙湖 / 华润 / 中海 房地产投拓",
        "中咨 / 北京国际工程咨询 + 监理公司",
        "PWC / 安永 工程咨询服务部",
        "甲方业主 (政府 / 国资 / 产业园)",
        "海外工程承包 (中铁建海外 / 中交海外)",
        "工管硕士 / PMP / 一级建造师持证",
    ],
    "administration_劳动社保": [
        "省 / 市 / 县人社局 + 社保中心 + 工会",
        "中国人寿 / 平安 / 太保 健康险 / 团险核保",
        "互联网 / 央企 / 外企福利 + EAP + 期权",
        "法律咨询 / 劳动仲裁 + 工会 + 律师事务所",
        "中国人民大学 / 中国政法 社会保障硕博",
        "中信咨询 / 远见咨询 HR 福利咨询",
        "国家智库 (国务院发展研究中心 / 人社部)",
        "海外社保 / 福利硕士 (LSE / UCL Social Policy)",
    ],
    "administration_农林经济": [
        "农业银行总分行 + 省农信社三农金融",
        "农业农村部 / 省农业农村厅 / 县农业局",
        "牧原 / 温氏 / 新希望 / 中粮 / 隆平高科",
        "中国农大 / 南农 / 浙大 农经研究所",
        "国家粮食和物资储备局 + 国家乡村振兴局",
        "省级农业合作社联社 + 涉农 NGO",
        "中投 / 中金 农林组 + 农银投资",
        "海外农业经济硕博 (UCD / 康奈尔 AAEP)",
    ],
    "administration_物流": [
        "顺丰 / 京东物流 / 菜鸟 / 中通 / 申通",
        "DHL / 马士基 / FedEx / UPS 跨境物流",
        "富士康 / 立讯 / 比亚迪 / 宁德时代 SCM",
        "普洛斯 / 京东产发 / 顺丰冷链 物流地产",
        "招商局 / 中远海运 / 中外运 央企物流",
        "TikTok Shop / 亚马逊 / SHEIN 跨境物流",
        "上海海事大学 + 北京交大 物流硕博",
        "海外物流 (NUS / MIT SCM / Hong Kong PolyU)",
    ],
    "administration_电子商务": [
        "阿里 / 拼多多 / 京东 类目运营 / 商家 BD",
        "TikTok Shop / 亚马逊 / SHEIN / 速卖通",
        "字节 / 快手 + MCN 直播公司",
        "小红书 / 微博 / B 站 KOL 运营",
        "完美日记 / 元气森林 / 喜茶 新消费品牌",
        "京东 / 唯品会 / 抖音 自营品牌",
        "电商创业 (服饰 / 美妆 / 食品) 独立站",
        "海外 Digital Marketing 硕士 (Imperial / NYU)",
    ],
    "administration_旅游": [
        "携程 / 美团酒店 / 飞猪 / 同程 OTA",
        "万豪 / 希尔顿 / 洲际 / 雅高 国际酒店集团",
        "上海 / 北京会展 + 上海国际会议中心",
        "华侨城 / 长隆 / 故宫 文旅 / 景区运营",
        "国旅 / 中青旅 / 凯撒 旅行社总部",
        "亚朵 / 全季 / 桔子 国内中端酒店",
        "国家文旅部 + 省文旅厅 + 市文旅局",
        "海外 MBA in Hospitality (康奈尔 / 港理工)",
    ],
    "administration_default": [
        "BAT / 字节 / 美团 / 京东 大厂管培",
        "央企总部 / 国资委直属 / 四大事务所",
        "省 / 市经发委 / 财政局 / 商务局 公务员",
        "MBB (麦肯锡 / BCG / Bain) + 顶咨",
        "中欧 / 长江 / 北大光华 MBA",
        "投行 / PE / VC 后台 + 商业银行总分行",
        "上市公司 / 头部民营总部管理",
        "海外管理硕士 (HKUST / NUS / LSE Mgmt)",
    ],
})


# ── DEEP_STUDY_FILLERS Batch 3 (14) ─────────────────────────────────
DEEP_STUDY_FILLERS.update({
    "arts_艺术学理论": {
        "美术馆 / 博物馆策展": 25, "拍卖行 / 画廊": 20, "文化产业 / 文创公司": 20,
        "文化公务员 / 事业单位": 15, "继续深造 (艺管硕博)": 20,
    },
    "arts_音乐表演": {
        "国家级 / 省级乐团演奏员": 25, "音乐学院 / 中小学教师": 25,
        "钢琴 / 器乐私教": 25, "商业演出 / 独立音乐": 15,
        "继续深造 (硕博 / 海外)": 10,
    },
    "arts_音乐学": {
        "高校音乐学 / 师范音乐教师": 35, "音乐编辑 / 出版": 15,
        "作曲 / 编曲 (自由职业)": 15, "艺术管理 / 演出公司": 15,
        "继续深造 (硕博)": 20,
    },
    "arts_舞蹈": {
        "国家级 / 省级舞团": 25, "舞蹈学院 / 中小学教师": 30,
        "商业编导 / 综艺": 15, "自由职业 / 工作室": 20,
        "继续深造 (硕博 / 海外)": 10,
    },
    "arts_广播电视": {
        "央视 / 卫视 / 融媒体": 25, "互联网视频平台": 25,
        "MCN / 短视频 / 独立工作室": 20, "广告 / 4A 创意": 15,
        "继续深造 (硕博)": 15,
    },
    "arts_戏剧影视": {
        "电影 / 电视剧编剧": 25, "话剧 / 戏剧院团": 15,
        "影视宣发 / 营销": 20, "视频平台内容采购": 20,
        "继续深造 (硕博 / 海外)": 20,
    },
    "arts_default": {
        "艺术行业 (文创 / 演艺 / 设计)": 35, "高校 / 中小学艺术教师": 25,
        "自由职业 / 工作室": 15, "公务员 / 事业单位": 10,
        "继续深造 (硕博 / 海外)": 15,
    },
    "administration_人力资源": {
        "互联网大厂 HRBP": 30, "咨询公司 HR 顾问": 20,
        "央企 / 制造业 HR 总监": 20, "HR SaaS / RPO 公司": 15,
        "继续深造 (HRM 硕博 / MBA)": 15,
    },
    "administration_市场营销": {
        "互联网品牌 / 用户运营": 30, "4A / Local 广告": 20,
        "快消 / 消费品市场部": 20, "数字营销 / KOL 运营": 15,
        "继续深造 (硕士 / MBA)": 15,
    },
    "administration_工程管理": {
        "央企工程造价 / 项目": 30, "设计院 / 建筑事务所": 25,
        "房地产投拓 / 项目": 15, "工程咨询 / 监理": 15,
        "继续深造 (工管硕博 / MBA)": 15,
    },
    "administration_劳动社保": {
        "人社局 / 社保经办公务员": 35, "商业保险公司核保 / 理赔": 20,
        "企业福利 / 薪酬专员": 15, "劳动咨询 / 法律服务": 10,
        "继续深造 (社保硕博 / MPA)": 20,
    },
    "administration_农林经济": {
        "农业银行 / 农信社": 30, "农业农村部 / 农业局公务员": 25,
        "农业产业化龙头企业": 20, "农村合作社 / 涉农 NGO": 10,
        "继续深造 (农经硕博)": 15,
    },
    "administration_物流": {
        "快递 / 综合物流运营": 30, "跨境物流 / 海运": 20,
        "制造业供应链管理": 25, "物流地产 / 仓储": 10,
        "继续深造 (物流硕博 / MBA)": 15,
    },
    "administration_电子商务": {
        "天猫 / 拼多多 / 京东类目": 30, "跨境电商 (TikTok / 亚马逊)": 25,
        "电商创业 / 自营品牌": 15, "MCN / 直播运营": 15,
        "继续深造 (电商硕士 / MBA)": 15,
    },
    "administration_旅游": {
        "OTA 平台 (携程 / 美团 / 飞猪)": 30, "五星酒店 / 国际酒店集团": 25,
        "MICE 会展公司": 15, "文旅 / 景区运营": 15,
        "继续深造 (旅游硕博 / 海外 MICE)": 15,
    },
    "administration_default": {
        "大厂管培生 / 业务运营": 30, "公务员 / 体制内": 25,
        "咨询公司 / 投行": 15, "民营 / 中小企业管理岗": 15,
        "继续深造 (MBA / 海外硕士)": 15,
    },
})


# ── SALARY_FILLERS Batch 3 (14 × 4 段) ──────────────────────────────
SALARY_FILLERS.update({
    "arts_艺术学理论": {
        "应届生 (一线)":       {"p25": 5,  "p50": 8,  "p75": 14, "yoy": 5},
        "3年经验":             {"p25": 9,  "p50": 14, "p75": 22, "yoy": 8},
        "5年经验":             {"p25": 15, "p50": 22, "p75": 38, "yoy": 8},
        "10年+ (持证/资深)":   {"p25": 28, "p50": 45, "p75": 80, "yoy": 10},
    },
    "arts_音乐表演": {
        "应届生 (一线)":       {"p25": 4,  "p50": 7,  "p75": 13, "yoy": 3},
        "3年经验":             {"p25": 8,  "p50": 13, "p75": 22, "yoy": 5},
        "5年经验":             {"p25": 13, "p50": 22, "p75": 38, "yoy": 8},
        "10年+ (持证/资深)":   {"p25": 25, "p50": 40, "p75": 75, "yoy": 8},
    },
    "arts_音乐学": {
        "应届生 (一线)":       {"p25": 4,  "p50": 7,  "p75": 12, "yoy": 3},
        "3年经验":             {"p25": 8,  "p50": 13, "p75": 20, "yoy": 5},
        "5年经验":             {"p25": 13, "p50": 22, "p75": 35, "yoy": 8},
        "10年+ (持证/资深)":   {"p25": 25, "p50": 40, "p75": 70, "yoy": 8},
    },
    "arts_舞蹈": {
        "应届生 (一线)":       {"p25": 4,  "p50": 6,  "p75": 11, "yoy": 3},
        "3年经验":             {"p25": 7,  "p50": 12, "p75": 20, "yoy": 5},
        "5年经验":             {"p25": 12, "p50": 20, "p75": 35, "yoy": 8},
        "10年+ (持证/资深)":   {"p25": 22, "p50": 36, "p75": 65, "yoy": 8},
    },
    "arts_广播电视": {
        "应届生 (一线)":       {"p25": 8,  "p50": 14, "p75": 25, "yoy": 8},
        "3年经验":             {"p25": 13, "p50": 22, "p75": 38, "yoy": 12},
        "5年经验":             {"p25": 22, "p50": 36, "p75": 60, "yoy": 10},
        "10年+ (持证/资深)":   {"p25": 38, "p50": 65, "p75": 110, "yoy": 12},
    },
    "arts_戏剧影视": {
        "应届生 (一线)":       {"p25": 7,  "p50": 13, "p75": 22, "yoy": 8},
        "3年经验":             {"p25": 12, "p50": 22, "p75": 38, "yoy": 10},
        "5年经验":             {"p25": 22, "p50": 38, "p75": 65, "yoy": 10},
        "10年+ (持证/资深)":   {"p25": 38, "p50": 65, "p75": 120, "yoy": 12},
    },
    "arts_default": {
        "应届生 (一线)":       {"p25": 5,  "p50": 8,  "p75": 14, "yoy": 5},
        "3年经验":             {"p25": 9,  "p50": 14, "p75": 22, "yoy": 8},
        "5年经验":             {"p25": 15, "p50": 24, "p75": 40, "yoy": 8},
        "10年+ (持证/资深)":   {"p25": 28, "p50": 45, "p75": 80, "yoy": 10},
    },
    "administration_人力资源": {
        "应届生 (一线)":       {"p25": 8,  "p50": 14, "p75": 25, "yoy": 8},
        "3年经验":             {"p25": 14, "p50": 25, "p75": 42, "yoy": 12},
        "5年经验":             {"p25": 25, "p50": 40, "p75": 65, "yoy": 10},
        "10年+ (持证/资深)":   {"p25": 40, "p50": 70, "p75": 130, "yoy": 12},
    },
    "administration_市场营销": {
        "应届生 (一线)":       {"p25": 9,  "p50": 15, "p75": 26, "yoy": 8},
        "3年经验":             {"p25": 15, "p50": 26, "p75": 42, "yoy": 12},
        "5年经验":             {"p25": 26, "p50": 42, "p75": 70, "yoy": 10},
        "10年+ (持证/资深)":   {"p25": 42, "p50": 75, "p75": 140, "yoy": 12},
    },
    "administration_工程管理": {
        "应届生 (一线)":       {"p25": 7,  "p50": 12, "p75": 20, "yoy": 5},
        "3年经验":             {"p25": 12, "p50": 22, "p75": 35, "yoy": 8},
        "5年经验":             {"p25": 22, "p50": 35, "p75": 60, "yoy": 8},
        "10年+ (持证/资深)":   {"p25": 38, "p50": 65, "p75": 110, "yoy": 10},
    },
    "administration_劳动社保": {
        "应届生 (一线)":       {"p25": 5,  "p50": 8,  "p75": 14, "yoy": 5},
        "3年经验":             {"p25": 9,  "p50": 14, "p75": 22, "yoy": 8},
        "5年经验":             {"p25": 15, "p50": 24, "p75": 38, "yoy": 8},
        "10年+ (持证/资深)":   {"p25": 25, "p50": 42, "p75": 75, "yoy": 8},
    },
    "administration_农林经济": {
        "应届生 (一线)":       {"p25": 5,  "p50": 9,  "p75": 16, "yoy": 5},
        "3年经验":             {"p25": 10, "p50": 16, "p75": 26, "yoy": 8},
        "5年经验":             {"p25": 16, "p50": 26, "p75": 42, "yoy": 8},
        "10年+ (持证/资深)":   {"p25": 28, "p50": 48, "p75": 80, "yoy": 10},
    },
    "administration_物流": {
        "应届生 (一线)":       {"p25": 7,  "p50": 12, "p75": 22, "yoy": 8},
        "3年经验":             {"p25": 12, "p50": 22, "p75": 35, "yoy": 10},
        "5年经验":             {"p25": 22, "p50": 35, "p75": 55, "yoy": 10},
        "10年+ (持证/资深)":   {"p25": 38, "p50": 60, "p75": 110, "yoy": 12},
    },
    "administration_电子商务": {
        "应届生 (一线)":       {"p25": 8,  "p50": 14, "p75": 25, "yoy": 8},
        "3年经验":             {"p25": 14, "p50": 25, "p75": 40, "yoy": 12},
        "5年经验":             {"p25": 25, "p50": 40, "p75": 65, "yoy": 10},
        "10年+ (持证/资深)":   {"p25": 40, "p50": 70, "p75": 130, "yoy": 12},
    },
    "administration_旅游": {
        "应届生 (一线)":       {"p25": 6,  "p50": 10, "p75": 18, "yoy": 5},
        "3年经验":             {"p25": 11, "p50": 18, "p75": 30, "yoy": 8},
        "5年经验":             {"p25": 18, "p50": 30, "p75": 50, "yoy": 8},
        "10年+ (持证/资深)":   {"p25": 30, "p50": 52, "p75": 95, "yoy": 10},
    },
    "administration_default": {
        "应届生 (一线)":       {"p25": 7,  "p50": 12, "p75": 22, "yoy": 8},
        "3年经验":             {"p25": 13, "p50": 22, "p75": 36, "yoy": 10},
        "5年经验":             {"p25": 22, "p50": 36, "p75": 60, "yoy": 10},
        "10年+ (持证/资深)":   {"p25": 38, "p50": 65, "p75": 120, "yoy": 12},
    },
})


XUANKE_FILLERS.update({
    "arts": [
        {"name": "不限选科 (艺考主导, 90% 艺术院校接受)", "course": "3+1+2 选科组合 + 艺考", "pct": 65,
         "reason": "艺术学类主要按艺考专业成绩录取, 选科要求宽松, 文化课基本是文综组合 (历史 + 政治 + 地理)。"},
        {"name": "历史 + 政治 (文综 + 艺考)", "course": "3+1+2 选科组合 + 艺考", "pct": 18,
         "reason": "美术 / 音乐 / 戏剧文化课要求, 文综组合是主流。"},
        {"name": "物理 + 化学 (理工类艺术: 影视技术 / 数媒)", "course": "3+1+2 选科组合", "pct": 12,
         "reason": "数字媒体艺术 / 影视技术 / 录音艺术 等跨理工方向, 物理是基础。"},
        {"name": "历史 + 地理 (再选政治, 偏文)", "course": "3+1+2 选科组合 + 艺考", "pct": 5,
         "reason": "艺术学理论 / 艺术管理 偏理论方向, 文综也可。"},
    ],
    "administration": [
        {"name": "物理 + 历史 + 政治 (覆盖最广, 95% 院校可报)", "course": "3+1+2 选科组合", "pct": 55,
         "reason": "管理学跨文理, 物理 + 政治组合既能报理工类管理 (工程管理 / 物流) 又能报文科管理 (人力 / 公管)。"},
        {"name": "历史 + 政治 + 地理 (文综, 公管 / HR / 旅游)", "course": "3+1+2 选科组合", "pct": 25,
         "reason": "公共管理 / 人力资源 / 旅游 / 营销 等偏文管理类, 传统文综最稳。"},
        {"name": "物理 + 化学 + 生物 (理工管理: 工程管理 / 物流 / 农经)", "course": "3+1+2 选科组合", "pct": 15,
         "reason": "工程管理 / 物流工程 / 农林经济 等跨工科 / 农科方向, 理科背景是优势。"},
        {"name": "不限选科 (中外合作 / 综合评价)", "course": "3+1+2 选科组合", "pct": 5,
         "reason": "极少数中外合作专业 / 综合评价招生不限选科。"},
    ],
})


# ── ALUMNI_FILLERS Batch 3 第二轮扩 (3 → 5 条 / sub-key, 同 Batch 2 D 经验) ─
_ALUMNI_BATCH3_EXTRA = {
    "arts_艺术学理论": [
        {"tag": "拍卖行高级专员 · 5 年", "quote": "本科艺管 + 海外艺术市场 MA + 嘉德 / 苏富比中国艺术品 5 年, 25-50 万 + 提成, 上拍专家 + 客户经理双角色, 头部成交季可破百万。", "school": "某 985 美院艺管 + 海外 MA 2020 届"},
        {"tag": "艺术机构创始人 · 4 年", "quote": "本科艺理 + 独立策展人 / 民营画廊主理 4 年, 收入差距大 (15-100 万/年), 城市艺博会 + 收藏家圈子是变现核心, 自带 IP 才能持续。", "school": "某 985 美院艺术管理 2021 届"},
    ],
    "arts_音乐表演": [
        {"tag": "音乐节 + 商演自由职业 · 4 年", "quote": "本科音乐表演 + 自由职业 (草莓 / 麦田 / 商演 / 婚礼) 4 年, 18-40 万/年, 演出场次 + 经纪人 + IP 是变量, 头部独立音乐人破百万。", "school": "某音乐学院音乐表演 2021 届"},
        {"tag": "海外乐团演奏员 · 5 年", "quote": "本科 + 海外茱莉亚 / 柯蒂斯硕士 + 海外乐团 5 年, 25-50 万 (折人民币), 文化适应 + 多语言 + 持续比赛是稳定门槛, 国内回流转高校或自由职业。", "school": "某音乐学院音乐表演 + 海外硕士 2020 届"},
    ],
    "arts_音乐学": [
        {"tag": "唱片公司 A&R · 4 年", "quote": "本科音乐学 + 太合 / 摩登 / 索尼音乐 A&R 4 年, 18-35 万/年, 选歌 + 选歌手 + 制作监制, 圈内人脉 + 音乐审美双能力。", "school": "某中央音乐学院音乐学 2021 届"},
        {"tag": "海外民族音乐学博士 · 7 年", "quote": "本科 + 海外民族音乐学博士 (UCLA / 牛津) + 国内顶尖音乐学院特聘研究员 7 年, 30-50 万 + 编, 国家社科项目 + 国际期刊是终身追求。", "school": "某中央音乐学院音乐学 + 海外 PhD 2018 届"},
    ],
    "arts_舞蹈": [
        {"tag": "私立舞蹈培训创始人 · 6 年", "quote": "本科舞蹈编导 + 自营舞蹈工作室 6 年, 20-50 万/年, 中考体育 + 艺考辅导 + 成人芭蕾, 课程 + 师资 + 招生三栖。", "school": "某北京舞蹈学院舞蹈编导 2019 届"},
        {"tag": "海外现代舞团 · 5 年", "quote": "本科 + 海外 NYU Tisch + 海外现代舞团 5 年, 18-32 万 (折人民币), 国际巡演 + 跨文化项目, 30 岁后多回国转编导或教学。", "school": "某北京舞蹈学院 + NYU Tisch 2020 届"},
    ],
    "arts_广播电视": [
        {"tag": "纪录片导演 · 5 年", "quote": "本科广电编导 + 央视纪录频道 / B 站独立纪录片 5 年, 12-30 万/年, 题材 + 拍摄 + 后期 + 影展, 国家级奖项 (金鸡 / 金鹰) 是入圈门槛。", "school": "某 985 大学广播电视编导 2020 届"},
        {"tag": "网络综艺总制片 · 4 年", "quote": "本科 + 米未 / 灿星 / 严选制作 综艺总制片 4 年, 30-65 万 + 项目奖金, S 级项目预算上亿, 创意 + 招商 + 团队管理三栖。", "school": "某 985 大学广播电视编导 2021 届"},
    ],
    "arts_戏剧影视": [
        {"tag": "短剧 / 微短剧编剧 · 3 年", "quote": "本科戏剧影视 + 短剧编剧 (字节 / 红果 / 番茄) 3 年, 8-25 万/年, 单本 1-3 万, 量大 + 模板化创作 + 平台分账, 影视寒冬下成主流入口。", "school": "某 211 大学戏剧影视文学 2022 届"},
        {"tag": "海外影视硕士 + 制片助理 · 4 年", "quote": "本科 + USC / NYU Tisch 电影硕士 + 国内民营影业制片助理 → 制片人 4 年, 18-35 万/年, 海外资源 + 国际合拍, 是少有的'海外背景溢价'方向。", "school": "某 985 高校戏剧影视 + USC 2020 届硕士"},
    ],
    "arts_default": [
        {"tag": "艺术教师 · 5 年", "quote": "本科艺术类 + 公办高校 / 中小学艺术教师 5 年, 12-22 万 + 编 + 寒暑假, 创作 + 教学 + 校队带队, 跨界 (设计 + 教学) 是稳定路径。", "school": "某 985 美院艺术类 2020 届"},
        {"tag": "海外艺术硕博", "quote": "本科 + RCA / Parsons / 中央圣马丁 / Pratt 海外艺术硕博, 是头部美术馆 / 艺术机构 / 高校的硬门槛, 25 岁前完成深造是黄金窗口。", "school": "某 985 美院 + 海外艺术硕士 2022 届"},
    ],
    "administration_人力资源": [
        {"tag": "互联网 HR 总监 · 7 年", "quote": "本科 HRM + 字节 / 阿里 HRBP 5 年 → HR 总监 7 年, 50-100 万/年 + 期权, 战略 + 组织 + 干部管理, 跳槽溢价高但抗压强。", "school": "某 985 高校人力资源 2018 届"},
        {"tag": "猎头 / 高管寻访 · 4 年", "quote": "本科 + 任仕达 / 米高蒲志 / Korn Ferry 高管寻访 4 年, 20-50 万 + 提成 (单 case 10-30 万), 行业网络 + 候选人画像 + 客户关系。", "school": "某 211 高校人力资源 2021 届"},
    ],
    "administration_市场营销": [
        {"tag": "DTC 品牌创始人 · 3 年", "quote": "本科营销 + 海外 MA + 自营 DTC 品牌 (服饰 / 美妆 / 健康) 3 年, GMV 数千万, 抖音 + 小红书 + 私域 + 独立站全栈, 内容 + 增长 + 供应链三栖。", "school": "某 985 高校营销 + 海外 MA 2022 届"},
        {"tag": "MBB 战略咨询 · 5 年", "quote": "本科 + 麦肯锡 / BCG 战略咨询 5 年, 45-80 万 + 项目奖金, 营销 + 战略 + 数据分析三栖, 跨行业项目 (零售 / 快消 / 金融) 是真壁垒。", "school": "某 985 高校营销 + 海外硕士 2020 届"},
    ],
    "administration_工程管理": [
        {"tag": "海外工程承包 (一带一路) · 5 年", "quote": "本科工管 + 一级建造师 + 中铁建海外 / 中交海外 5 年, 30-55 万 + 海外补贴, 沙特 / 印尼 / 巴基斯坦 等基建项目, 国际承包 + 跨文化 + 政府公关。", "school": "某 985 高校工程管理 2020 届"},
        {"tag": "产业园 / 商业地产投拓 · 6 年", "quote": "本科 + 房地产硕士 + 上海临港 / 苏州工业园投拓 6 年, 35-60 万/年, 政府关系 + 产业规划 + 测算, 地产寒冬下转产业园是稳健出路。", "school": "某 985 高校工程管理 + 房地产硕士 2019 届"},
    ],
    "administration_劳动社保": [
        {"tag": "国务院发展研究中心 · 4 年", "quote": "本科 + 中国人民大学社保博士 + 国务院发展研究中心研究员 4 年, 12-22 万 + 编, 政策研究 + 报告写作 + 智库咨询, 国家级智库稀缺。", "school": "某 985 高校社会保障 + 人大 PhD 2021 届"},
        {"tag": "外资养老金管理 · 5 年", "quote": "本科社保 + 美世养老金 / 安永福利咨询 5 年, 25-45 万/年, 企业年金 + 商业养老 + 跨国福利, 精算 + 法律 + 财税三栖。", "school": "某 985 高校劳动与社会保障 2020 届"},
    ],
    "administration_农林经济": [
        {"tag": "中农办 / 乡村振兴 · 4 年", "quote": "本科农经 + 硕士 + 中央农村工作领导小组办公室 / 国家乡村振兴局 4 年, 10-18 万 + 编, 政策研究 + 项目督导, 国家战略对口稀缺岗位。", "school": "某 985 农业大学农林经济硕士 2021 届"},
        {"tag": "农业产业基金 · 5 年", "quote": "本科 + 农业银行 / 中信农业产业基金投资经理 5 年, 30-50 万 + 项目奖金, 农业 + 金融双背景, 农业产业化龙头企业 IPO + 并购投资。", "school": "某 985 农业大学农林经济管理 2020 届"},
    ],
    "administration_物流": [
        {"tag": "顺丰国际 BD 总监 · 6 年", "quote": "本科物流 + MBA + 顺丰国际 (东南亚 / 北美) BD 总监 6 年, 40-75 万 + 海外补贴, 跨境物流 + 国际客户 + 政府公关, 一带一路 + RCEP 红利期。", "school": "某 985 高校物流管理 + 长江 MBA 2019 届"},
        {"tag": "京东物流仓储自动化 · 4 年", "quote": "本科物流 + 京东物流亚洲一号自动化运营 4 年, 25-40 万/年, AGV + 分拣机器人 + WMS 系统, 物流 + 自动化 + 数据三栖是稀缺。", "school": "某 985 高校物流工程 2021 届"},
    ],
    "administration_电子商务": [
        {"tag": "拼多多 + 抖音双平台运营 · 4 年", "quote": "本科电商 + 拼多多类目运营 → 抖音电商品牌负责人 4 年, 30-55 万 + 提成 (GMV 上亿), 双平台规则 + 内容 + 数据三栖, 跨平台经验是溢价点。", "school": "某 211 高校电子商务 2021 届"},
        {"tag": "海外品牌运营 (亚马逊 + 独立站) · 5 年", "quote": "本科电商 + Anker / SHEIN / TikTok 海外品牌运营 5 年, 35-65 万 + 海外补贴, 北美 / 欧洲 / 中东多市场, 海外消费者洞察 + 内容本地化是壁垒。", "school": "某 985 高校电子商务 2020 届"},
    ],
    "administration_旅游": [
        {"tag": "环球影城 / 迪士尼运营 · 4 年", "quote": "本科旅游 + 北京环球影城 / 上海迪士尼运营经理 4 年, 20-35 万/年, IP + 演艺 + 餐饮 + 安全四统筹, 国际主题乐园是稀缺出路。", "school": "某 211 高校旅游管理 2021 届"},
        {"tag": "高端定制游 / 出境游 · 5 年", "quote": "本科旅游 + Abercrombie & Kent / 海航旅业 高端定制游 5 年, 25-45 万 + 项目佣金 (单人均 5-50 万), 多语言 + 全球资源 + 客户服务三栖。", "school": "某 985 旅游学院 + 海外 MICE 硕士 2020 届"},
    ],
    "administration_default": [
        {"tag": "上市公司战略部 · 5 年", "quote": "本科管理类 + 国内 MBA + 上市公司战略发展部 5 年, 30-50 万/年, 战略规划 + 投资分析 + 业绩复盘, 跨行业经验 + 数据 + 沟通三栖。", "school": "某 985 高校管理类 + 复旦 MBA 2020 届"},
        {"tag": "海外咨询 / 跨国总部 · 4 年", "quote": "本科 + 海外硕士 (LSE / NUS) + 跨国公司亚太总部 / 海外咨询 4 年, 35-60 万 + 海外补贴, 跨文化 + 多语言 + 战略, 海外背景 + 中文是双向溢价。", "school": "某 985 高校管理类 + 海外硕士 2021 届"},
    ],
}
for _k, _v in _ALUMNI_BATCH3_EXTRA.items():
    if _k in ALUMNI_FILLERS:
        ALUMNI_FILLERS[_k] = list(ALUMNI_FILLERS[_k]) + list(_v)
    else:
        ALUMNI_FILLERS[_k] = list(_v)


def normalize_deep_study(ds, style="default", title=""):
    """归一 deep_study 为扁平 dict {path_str(含括号说明): pct_int}, 5-7 条 ≈ 100%.
    law 主题按 title 细分 (避免 8 篇同源).
    """
    if not isinstance(ds, dict):
        ds = {}
    out = {}
    for k, v in ds.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            try:
                pct = int(v)
            except (ValueError, TypeError):
                continue
            if pct < 0 or pct > 100:
                continue
            out[str(k)[:80]] = pct
        elif isinstance(v, str):
            m = re.search(r"(\d+)\s*%", v)
            if m:
                out[str(k)[:80]] = int(m.group(1))
        elif isinstance(v, dict):
            pct = v.get("pct", 0) or v.get("ratio", 0)
            try:
                pct = int(pct)
            except (ValueError, TypeError):
                pct = 0
            name = v.get("name", k)
            if pct and 0 < pct <= 100:
                out[str(name)[:80]] = pct
    # 选 fillers: law 主题按 title 细分; education / humanities 按 Batch 2 dispatch
    if style == "law":
        sub = _law_subkey(title)
        fillers = DEEP_STUDY_FILLERS.get(sub, DEEP_STUDY_FILLERS.get("law_default", DEEP_STUDY_FILLERS["default"]))
    elif style in ("education", "humanities", "arts", "administration"):
        sub = _resolve_batch2_key(style, title)
        default_key = {"education": "education_default", "humanities": "literature_default", "arts": "arts_default", "administration": "administration_default"}.get(style, "default")
        fillers = DEEP_STUDY_FILLERS.get(sub, DEEP_STUDY_FILLERS.get(default_key, DEEP_STUDY_FILLERS["default"]))
    else:
        fillers = DEEP_STUDY_FILLERS.get(style, DEEP_STUDY_FILLERS["default"])
    if style == "law" or style in ("education", "humanities", "arts", "administration"):
        # law / education / humanities 主题: 强制用 sub-style fillers 覆盖 (避免同源)
        out = dict(fillers)
    else:
        if len(out) < 3 or (len(set(out.values())) <= 1 and len(out) >= 3):
            out = dict(fillers)
    return out


# ── hero_quote 兜底 ────────────────────────────────────────────────
def normalize_hero_quote(data):
    q = data.get("hero_quote", "")
    if not q or len(str(q).strip()) < 5:
        title = data.get("title", "本专业")
        data["hero_quote"] = f"—— {title} 是一门值得深入探索的学科"
        data.setdefault("hero_quote_sig", "—— Major Explorer 编辑寄言")
    return data


# ── 主入口 ─────────────────────────────────────────────────────────
def normalize_major(data: dict, title: str = "", slug: str = "") -> dict:
    """in-place 归一整篇 major JSON 到 render 期望 schema."""
    if not title:
        title = data.get("title", "")
    style = data.get("style", "default")
    data["salary"] = normalize_salary(data.get("salary", {}), data.get("summary", ""), style, title)
    data["curriculum"] = normalize_curriculum(data.get("curriculum", {}), title, style)
    data["top_schools"] = normalize_top_schools(data.get("top_schools", []), title)
    data["alumni_quotes"] = normalize_alumni(data.get("alumni_quotes", []), title, style)
    data["employment_direction"] = normalize_employment(data.get("employment_direction", []), style, title)
    data["xuanke_req_list"] = normalize_xuanke(data.get("xuanke_req_list", []), style)
    data["overview_v2"] = normalize_overview_v2(data.get("overview_v2", {}), data.get("summary", ""))
    data["top_companies"] = normalize_top_companies(data.get("top_companies", []), style, title)
    data["deep_study"] = normalize_deep_study(data.get("deep_study", {}), style, title)
    normalize_hero_quote(data)
    # style/category/title/slug 兜底 (slug 强制用 filename 一致, 不让 LLM 瞎给 pinyin)
    data.setdefault("title", title)
    if slug:
        data["slug"] = slug  # 强制覆盖
    else:
        data.setdefault("slug", re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-"))
    data.setdefault("style", data.get("style", "law"))
    data.setdefault("category", data.get("category", ""))
    data.setdefault("data_source", data.get("data_source", "人工精编"))
    data.setdefault("updated_at", "2026-06")
    return data


if __name__ == "__main__":
    import sys
    import csv as _csv
    cur = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp/skills/gaokao-major-explorer/data/curated")
    # 用法:
    #   python normalize.py                     # Batch 1 默认 12 slug
    #   python normalize.py slug1 slug2 ...     # 自由 slug 列表
    #   python normalize.py path/to/batch.csv   # 从 CSV 读 (列: slug,title,style)
    if len(sys.argv) > 1 and sys.argv[1].endswith(".csv"):
        targets = []
        with open(sys.argv[1]) as _f:
            for row in _csv.DictReader(_f):
                if row.get("slug"):
                    targets.append(row["slug"])
        print(f"📋 从 {sys.argv[1]} 读到 {len(targets)} 个 slug")
    elif len(sys.argv) > 1:
        targets = sys.argv[1:]
    else:
        targets = [
            "international-law", "economic-law", "criminal-law", "civil-law-jurisprudence",
            "commercial-law", "administrative-law", "civil-procedure", "criminal-procedure",
            "prison-studies", "drug-control", "criminology", "foreign-police",
        ]
    for slug in targets:
        p = cur / f"{slug}.json"
        if not p.exists():
            print(f"  ⏭️  {slug}: missing")
            continue
        d = json.loads(p.read_text())
        title = d.get("title", slug)
        normalize_major(d, title, slug=slug)  # 传 filename slug 强制覆盖
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        # 验证
        sal = d["salary"]
        sal_keys_ok = all(k in sal for k in ["应届生 (一线)", "3年经验", "5年经验", "10年+ (持证/资深)"])
        cur_ok = all(k in d["curriculum"] for k in ["公共必修", "通用专业核心", "5 校特色选修"])
        ov_ok = all(k in d["overview_v2"] for k in ["lede", "what", "fit", "pitfalls"])
        marker = "✅" if (sal_keys_ok and cur_ok and ov_ok) else "⚠️"
        print(f"  {marker} {slug:30s} sal={sal_keys_ok} cur={cur_ok} ov={ov_ok}")
    print("\n完成 normalize")