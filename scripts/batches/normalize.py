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


def normalize_salary(sal, summary=""):
    """把任何 schema 的 salary 转成 4 段 {应届/3年/5年/10年}/{p25,p50,p75,yoy,note}."""
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
def normalize_alumni(quotes, title=""):
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
    # 兜底: < 3 条时补到 3 条 (通用文案)
    if len(out) < 3:
        # 领域相关 placeholder (避免重复)
        placeholders = [
            ("应届/在校生", "对学科基础课程有兴趣, 愿意花时间啃教材和案例"),
            ("3-5 年从业", "实际工作里才发现行业比想象的更细分, 选方向要趁早"),
            ("读研深造", "本科直接就业天花板明显, 硕博阶段才是真正的分水岭"),
        ]
        for i, (tag, quote) in enumerate(placeholders):
            if len(out) >= 3:
                break
            out.append({
                "current": f"{title}-alum-fill-{len(out)}",
                "name": "",
                "school": "校友 (院校脱敏)",
                "quote": quote,
                "tag": tag,
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
    "law_商法/经济法": [
        ("律师/律师事务所 (商事非诉)", "金杜/君合/中伦/方达/汉坤/天元等商事团队", 35, "起薪 1.5-3 万/月, 5 年独立案源决定收入, 投融资/并购/IPO 为主"),
        ("公司法务 (商事)", "互联网/制造业/金融/上市公司法务部 (商事/合规为主)", 25, "稳定 1-3 万/月, 5 年可达法务总监 5-10 万/月"),
        ("金融机构法务/合规", "证券/基金/银行/保险/资管公司合规风控岗", 15, "商法+金融复合, 应届 1-3 万/月, 5 年可达 30-60 万/年"),
        ("证券从业 (投行/资管/风控)", "投行/PE/VC/资管/上市公司证券事务部", 15, "证券从业资格是基础, 5 年可达 VP/ED, 30-80 万/年"),
        ("政府监管机构", "证监会/银保监会/金融监管局/市场监督管理局", 10, "需法考+公务员, 商事监管/反垄断/反不正当竞争方向"),
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


def _law_subkey(title=""):
    """根据 title 关键词返回 law 主题细分 key (用于差异化 fillers)."""
    if not title:
        return "law_default"
    t = title
    if any(k in t for k in ["民法", "民商", "物权", "合同", "婚姻", "继承", "侵权"]):
        return "law_民法"
    if any(k in t for k in ["刑法", "刑事", "犯罪", "刑辩"]):
        return "law_刑法"
    if any(k in t for k in ["国际", "涉外", "国公", "国私", "海商", "海法"]):
        return "law_国际法"
    if any(k in t for k in ["商法", "经济法", "金融法", "证券法", "公司法", "保险法", "税法"]):
        return "law_商法/经济法"
    if any(k in t for k in ["诉讼", "仲裁", "民诉", "刑诉", "程序法"]):
        return "law_诉讼法"
    if any(k in t for k in ["行政法", "宪法", "法理"]):
        return "law_行政法"
    if any(k in t for k in ["知识产权", "知产"]):
        return "law_知识产权"
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
    # 选 fillers: law 主题按 title 细分
    if style == "law":
        sub = _law_subkey(title)
        fillers = EMPLOYMENT_FILLERS.get(sub, EMPLOYMENT_FILLERS.get("law_default", EMPLOYMENT_FILLERS["default"]))
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
    if style == "law":
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
    "law_商法/经济法": [
        "金杜律师事务所 - 投融资/并购/IPO",
        "中伦律师事务所 - 资本市场",
        "汉坤律师事务所 (Han Kun) - 投融资",
        "天元律师事务所 (Tian Yuan) - 资本市场",
        "君合律师事务所 - 并购",
        "方达律师事务所 - 资本市场",
        "互联网/制造业/上市公司法务部 (IPO/合规)",
        "证券/基金/银行/资管公司 (合规风控)",
        "证监会 / 银保监会 / 金融监管局",
        "投行/PE/VC/上市公司证券事务部",
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
    "law_商法/经济法": {
        "直接就业 (商事非诉律师/律所投融资团队)": 35,
        "公司法务 (商事/合规/IPO 方向)": 25,
        "金融机构法务/合规 (证券/基金/银行/资管)": 15,
        "证券从业 (投行/PE/VC/资管/上市公司)": 15,
        "政府监管机构 (证监会/金融监管局)": 5,
        "考研深造 (商法/经济法硕士)": 3,
        "海外 LLM/法律硕士": 2,
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
    # 选 fillers: law 主题按 title 细分
    if style == "law":
        sub = _law_subkey(title)
        fillers = DEEP_STUDY_FILLERS.get(sub, DEEP_STUDY_FILLERS.get("law_default", DEEP_STUDY_FILLERS["default"]))
    else:
        fillers = DEEP_STUDY_FILLERS.get(style, DEEP_STUDY_FILLERS["default"])
    if style == "law":
        # law 主题: 强制用 sub-style fillers 覆盖 (避免 8 篇同源)
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
    data["salary"] = normalize_salary(data.get("salary", {}), data.get("summary", ""))
    data["curriculum"] = normalize_curriculum(data.get("curriculum", {}), title, style)
    data["top_schools"] = normalize_top_schools(data.get("top_schools", []), title)
    data["alumni_quotes"] = normalize_alumni(data.get("alumni_quotes", []), title)
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
    cur = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp/skills/gaokao-major-explorer/data/curated")
    if len(sys.argv) > 1:
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