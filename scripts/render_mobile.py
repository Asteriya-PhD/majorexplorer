#!/usr/bin/env python3
"""
render_mobile.py — 批量渲染 126 个 mobile 详情页
数据源: skills/gaokao-major-explorer/data/curated/{slug}.json (结构化 raw)
模板:  public/m/majors/_template.html
输出:  public/m/majors/{slug}.html (126 个)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "public/m/majors/_template.html"
CURATED_DIR = ROOT / "skills/gaokao-major-explorer/data/curated"
OUT_DIR = ROOT / "public/m/majors"
MANIFEST = ROOT / "public/data/manifest.json"
CHSI_MAJORS = ROOT / "public/data/chsi_majors.json"

# 13 theme → 4 色调色板 (主/深/浅/金) — 跟 mock mobile 主题色保持协调
THEMES = {
    "finance":        ("#4A4564", "#2E2945", "#ECEAF2", "#B5934A"),
    "business":       ("#5A4632", "#3D2E20", "#F0E8DA", "#B5934A"),
    "law":            ("#3A3A3A", "#1F1F1F", "#E8E6E1", "#A88A3E"),
    "gongan":         ("#1E3A5F", "#0F1F33", "#E0E8F0", "#B5934A"),
    "administration": ("#5C5C8A", "#3A3A5C", "#E8E8F0", "#B5934A"),
    "education":      ("#5C7C4A", "#3D5530", "#E8F0E0", "#B5934A"),
    "humanities":     ("#6B4F35", "#3D2E1F", "#F0E8DC", "#B5934A"),
    "arts":           ("#8B3A62", "#5C2642", "#F0DCE8", "#B5934A"),
    "sci":            ("#1E5E72", "#0F3D4D", "#DCE8F0", "#B5934A"),
    "eng":            ("#5B5B47", "#3D3D2E", "#ECECE0", "#B5934A"),
    "cs":             ("#1E5E72", "#0F3D4D", "#DCE8F0", "#B5934A"),
    "medicine":       ("#8B2424", "#5C1818", "#F0DCDE", "#B5934A"),
    "agri":           ("#6B7A3F", "#3F4D22", "#ECEFCC", "#B5934A"),
}

# 数字 + 汉字 编码安全转换
def esc(s):
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# 章节渲染器
def render_curriculum(curriculum):
    """curriculum = {公共必修, 通用专业核心, 5 校特色选修, 实践教学环节}.
    自动给硬课关键词加 ★ 标记"""
    if not curriculum:
        return ""
    year_map = {
        "公共必修": "大一",
        "通用专业核心": "大二",
        "5 校特色选修": "大三",
        "实践教学环节": "大四",
    }
    star_keywords = ["硬课", "必修", "考证", "实务", "实习", "竞赛", "法考", "司法考试",
                     "数学", "统计", "概率", "线性代数", "微积分", "编程", "算法", "英语",
                     "毕业", "论文", "实战", "前沿", "导论", "基础", "总论", "训练",
                     "实训", "诊所", "模拟", "检索", "写作", "谈判", "辩论"]
    def render_name(name):
        if "★" in name:
            return re.sub(r"★", '<strong style="color:var(--accent);">★</strong>', esc(name))
        if any(kw in name for kw in star_keywords):
            return '<strong style="color:var(--accent);">★</strong> ' + esc(name)
        return esc(name)

    rows = []
    for key, label in year_map.items():
        items = curriculum.get(key, [])
        if not items:
            continue
        if isinstance(items[0], dict):
            names_list = [it.get("course", it.get("name", str(it))) for it in items]
            tag = items[0].get("tag", label)
        else:
            names_list = [str(it) for it in items]
            tag = label
        names_html = " · ".join(render_name(n) for n in names_list)
        rows.append(f'''<div class="course-row">
          <div class="course-yr">{esc(label)}</div>
          <div class="course-names">{names_html}</div>
          <div class="course-tag">{esc(tag)}</div>
        </div>''')
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">四</span>
        <h2 class="art-title">本科 4 年学的课</h2>
      </div>
      <div class="art-body">
        <p>下面按年级排列。打 <span style="color: var(--accent); font-weight: 700;">★</span> 的是对找工作有直接影响的硬课.</p>
      </div>
      <div class="course-list">
        {''.join(rows)}
      </div>
    </section>'''


def render_overview_v2(ov2):
    """ov2 = {lede, what} — fit/pitfalls 已拆独立段, what 渲染为方向卡 + 标签云"""
    if not ov2:
        return ""
    what = ov2.get("what")
    parts = []
    if isinstance(what, dict):
        dirs = what.get("directions") or []
        if dirs:
            cards = []
            for i, d in enumerate(dirs[:6], 1):
                if not isinstance(d, dict):
                    continue
                name = d.get("name", "") or d.get("title", "")
                desc = d.get("desc", "") or d.get("description", "")
                cards.append(
                    f'<div class="dir-card">'
                    f'<div class="dir-num">{i:02d}</div>'
                    f'<div class="dir-body">'
                    f'<div class="dir-name">{esc(name)}</div>'
                    f'<div class="dir-desc">{esc(desc)}</div>'
                    f'</div>'
                    f'</div>'
                )
            if cards:
                parts.append(f'<div class="dir-list">{"".join(cards)}</div>')
        foundations = what.get("foundations") or []
        skills = what.get("skills") or []
        # 兼容: skills 可能是 dict{item: [...]} 异常 schema
        if isinstance(skills, dict):
            skills = skills.get("item") or skills.get("items") or []
        tag_blocks = []
        if foundations:
            tags = "".join(f'<span class="tag-mini">{esc(t)}</span>' for t in foundations[:8])
            tag_blocks.append(f'<div class="what-tags-block"><div class="what-tags-label">学什么底子</div><div class="what-tags">{tags}</div></div>')
        if skills:
            tags = "".join(f'<span class="tag-mini">{esc(t)}</span>' for t in skills[:8])
            tag_blocks.append(f'<div class="what-tags-block"><div class="what-tags-label">练什么能力</div><div class="what-tags">{tags}</div></div>')
        if tag_blocks:
            parts.append(f'<div class="what-tags-stack">{"".join(tag_blocks)}</div>')
    lede = ov2.get("lede", "")

    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">一</span>
        <h2 class="art-title">这个专业学什么</h2>
      </div>
      <div class="art-body">
        {f'<p class="lede">{esc(lede)}</p>' if lede else ''}
        {"".join(parts)}
      </div>
    </section>'''


def render_fit(fit):
    """fit = {'yes': [str], 'no': [str]} → 杂志风双段"""
    if not isinstance(fit, dict):
        return ""
    yes = fit.get("yes") or []
    no = fit.get("no") or []
    if not yes and not no:
        return ""

    def _list(items):
        if not items:
            return ""
        lis = "".join(f"<li>{esc(it)}</li>" for it in items if it)
        return f'<ul class="fit-list">{lis}</ul>'

    yes_html = ""
    if yes:
        yes_html = (
            f'<div class="fit-col fit-yes">'
            f'<div class="fit-num">Y · YES</div>'
            f'<div class="fit-title">🌱 适合来读</div>'
            f'{_list(yes)}'
            f'</div>'
        )
    no_html = ""
    if no:
        no_html = (
            f'<div class="fit-col fit-no">'
            f'<div class="fit-num">N · NO</div>'
            f'<div class="fit-title">⛔ 慎入</div>'
            f'{_list(no)}'
            f'</div>'
        )
    return f'<div class="fit-pair">{yes_html}{no_html}</div>'


def render_pitfalls(pitfalls):
    """pitfalls = [{myth, reality}, ...] → 杂志风列表"""
    if not pitfalls:
        return ""
    rows = []
    for i, p in enumerate(pitfalls[:5], 1):
        if isinstance(p, dict):
            myth = p.get("myth", "")
            reality = p.get("reality", "")
        else:
            myth, reality = "", str(p)
        if not (myth or reality):
            continue
        rows.append(
            f'<div class="pit-row">'
            f'<div class="pit-myth-side">'
            f'<div class="pit-label">误区 0{i}</div>'
            f'<div class="pit-myth-text">{esc(myth)}</div>'
            f'</div>'
            f'<div class="pit-reality-side">'
            f'<div class="pit-label">真相</div>'
            f'<div class="pit-reality-text">{esc(reality)}</div>'
            f'</div>'
            f'</div>'
        )
    if not rows:
        return ""
    return f'<div class="pit-grid">{"".join(rows)}</div>'


def _render_fit_section(fit):
    """整段 fit 包装"""
    body = render_fit(fit)
    if not body:
        return ""
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">二</span>
        <h2 class="art-title">什么人适合</h2>
      </div>
      <div class="art-body">
        <p>在决定之前, 先想清楚自己是哪种人.</p>
      </div>
      {body}
    </section>'''


def _render_pitfalls_section(pitfalls):
    """整段 pitfalls 包装"""
    body = render_pitfalls(pitfalls)
    if not body:
        return ""
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">三</span>
        <h2 class="art-title">避坑指南</h2>
      </div>
      <div class="art-body">
        <p>关于这个专业最常见的几个误区, 看完再决定要不要押.</p>
      </div>
      {body}
    </section>'''


def render_salary(salary):
    """salary = {stage: {p25, p50, p75, yoy}} → P25/P50/P75 三列表格 + 估算符号 + yoy 箭头"""
    if not salary:
        return ""
    # 按工作年限自然顺序 (应届 → 3年 → 5年 → 10年+), 数字从小到大
    rows_data = []
    for stage, val in salary.items():
        if isinstance(val, dict):
            p25 = float(val.get("p25", 0)) if val.get("p25") else 0
            p50 = float(val.get("p50", 0)) if val.get("p50") else 0
            p75 = float(val.get("p75", 0)) if val.get("p75") else 0
            yoy = val.get("yoy", 0)
            rows_data.append((stage, p25, p50, p75, yoy))
        elif isinstance(val, (int, float)):
            rows_data.append((stage, 0, float(val), 0, 0))
        else:
            rows_data.append((stage, 0, 0, 0, 0))
    # 按 P50 中位升序 (应届 → 资深)
    rows_data.sort(key=lambda x: x[2])
    if not rows_data:
        return ""
    # 计算每列最大宽度
    max_p25 = max((r[1] for r in rows_data), default=1) or 1
    max_p50 = max((r[2] for r in rows_data), default=1) or 1
    max_p75 = max((r[3] for r in rows_data), default=1) or 1

    def cell_html(value, mx, approx=True):
        if value is None or value == 0:
            return '<span class="sal-cell-empty">—</span>'
        prefix = '<span class="approx">≈</span>' if approx else ''
        yoy_html = ""
        w = f"{(value/mx*100):.0f}%" if mx else "8%"
        bar = f'<span class="sal-cell-bar"><span class="sal-cell-fill" style="width:{w};"></span></span>'
        return f'{prefix}<span class="sal-cell-num">{value:.1f}</span><span class="sal-cell-unit">万</span>{bar}'

    rows_html = []
    for stage, p25, p50, p75, yoy in rows_data[:5]:
        yoy_html = ""
        if isinstance(yoy, (int, float)) and yoy != 0:
            arrow = "↗" if yoy > 0 else "↘"
            cls = "up" if yoy > 0 else "down"
            yoy_html = f'<span class="sal-yoy {cls}">{arrow} {abs(yoy):g}%</span>'
        rows_html.append(f'''<div class="sal-tr">
          <div class="sal-stage">{esc(stage)}{yoy_html}</div>
          <div class="sal-cell">{cell_html(p25, max_p25)}</div>
          <div class="sal-cell is-p50">{cell_html(p50, max_p50)}</div>
          <div class="sal-cell">{cell_html(p75, max_p75)}</div>
        </div>''')

    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">七</span>
        <h2 class="art-title">毕业后真的能拿多少</h2>
      </div>
      <div class="art-body">
        <p>P25/P50/P75 = 25/50/75 百分位. ≈ 表示估算值. ↗/↘ = 3 年变化.</p>
      </div>
      <div class="sal-table">
        <div class="sal-th">
          <div class="sal-th-stage">阶段</div>
          <div class="sal-th-cell">P25</div>
          <div class="sal-th-cell is-p50">P50 中位</div>
          <div class="sal-th-cell">P75 高位</div>
        </div>
        {"".join(rows_html)}
      </div>
    </section>'''


def render_schools(schools, hubei_only=False):
    """schools = [{name, rank, tag, score?}]"""
    if not schools:
        return ""
    # 湖北优先, 但目前 mock 全是湖北的 + 跨省, 先全列
    items = schools[:8]
    rows = []
    for i, s in enumerate(items, 1):
        rank = s.get("rank", "")
        # 把 ★ 渲染成徽章
        rank_html = re.sub(r"★", "★", esc(rank))
        # tag → 短 badge
        tag = s.get("tag", "")
        # 如果 tag 含 A+ / A / A- / B+ → 取第一个
        badge = ""
        m = re.search(r"评估?\s*([A+\-]+[ABCDF]?)", tag)
        if m:
            badge = m.group(1)
        # score (没数据时省)
        score = s.get("score") or s.get("hubei_2024_score") or s.get("min_2024")
        score_html = f'<div class="uni-score">{esc(score)}</div>' if score else '<div class="uni-score">—</div>'
        rows.append(f'''<div class="uni-row">
          <div class="uni-rank">{i:02d}</div>
          <div class="uni-name">{esc(s.get("name", ""))}{f'<span class="badge">{esc(badge)}</span>' if badge else ''}</div>
          {score_html}
        </div>''')
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">五</span>
        <h2 class="art-title">院校分布</h2>
      </div>
      <div class="art-body">
        <p>按 2025 软科 + 武书连综合排名。<strong>分数线仅供参考</strong>, 录取以教育考试院公告为准.</p>
      </div>
      {''.join(rows)}
    </section>'''


def render_quote(quote_data, title=""):
    """quote_data = [{quote, name, school, tag}] → 取前 3 个卡片堆叠"""
    if not quote_data:
        return ""
    items = []
    for q in quote_data[:3]:
        if not isinstance(q, dict):
            continue
        text = q.get("quote", q.get("text", ""))
        by = q.get("name", "") or q.get("school", "")
        sig = q.get("tag", "")
        if not text:
            continue
        by_full = f"{by} · {sig}" if by and sig else (by or sig)
        items.append(
            f'<div class="pull">'
            f'"{esc(text)}"'
            f'<span class="by">— {esc(by_full)}</span>'
            f'</div>'
        )
    if not items:
        return ""
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">十</span>
        <h2 class="art-title">学长学姐说</h2>
      </div>
      <div class="art-body">
        <p>选专业之前, 听听真正读过的人是后悔还是庆幸. (前 3 条)</p>
      </div>
      <div class="pull-list">
        {"".join(items)}
      </div>
    </section>'''


def render_companies(companies):
    """top_companies = [{name, sparkline, headcount, salary, tier}] → 头部雇主 (tier=S/A/B top 12)"""
    if not companies:
        return ""
    tier_order = {"S": 0, "A": 1, "B": 2, "C": 3}
    sorted_co = sorted(
        [c for c in companies if isinstance(c, dict)],
        key=lambda c: tier_order.get(c.get("tier", "C"), 4)
    )
    rows = []
    for c in sorted_co[:12]:
        name = c.get("name", "")
        headcount = c.get("headcount", "")
        salary = c.get("salary", "")
        tier = c.get("tier", "")
        spark = c.get("sparkline", [])
        spark_html = ""
        if isinstance(spark, list) and len(spark) >= 2:
            mx, mn = max(spark), min(spark)
            rng = mx - mn or 1
            points = []
            W, H = 50, 14
            for i, v in enumerate(spark):
                x = (i / (len(spark) - 1)) * W
                y = H - ((v - mn) / rng) * H
                points.append(f"{x:.1f},{y:.1f}")
            spark_html = f'<svg class="co-spark" viewBox="0 0 {W} {H}" preserveAspectRatio="none"><polyline points="{" ".join(points)}" /></svg>'
        rows.append(
            f'<div class="co-row">'
            f'<div class="co-info">'
            f'<div class="co-name">{esc(name)}<span class="co-tier co-tier-{tier.lower()}">{tier}</span></div>'
            f'<div class="co-meta">{esc(headcount)}<span class="dot">·</span>{esc(salary)}</div>'
            f'</div>'
            f'<div class="co-spark-wrap">{spark_html}</div>'
            f'</div>'
        )
    if not rows:
        return ""
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">六</span>
        <h2 class="art-title">头部雇主参考</h2>
      </div>
      <div class="art-body">
        <p>按招聘规模 + 校招起薪排序 (top 12). 5 年趋势线看公司扩张节奏.</p>
      </div>
      <div class="co-list">
        {''.join(rows)}
      </div>
    </section>'''


def render_xuanke(xuanke_list):
    """xuanke_req_list = [{name, course, pct, reason}] → 选科要求"""
    if not xuanke_list:
        return ""
    rows = []
    for i, x in enumerate(xuanke_list[:6], 1):
        if not isinstance(x, dict):
            continue
        name = x.get("name", "")
        pct = x.get("pct", 0)
        reason = x.get("reason", "")
        rows.append(
            f'<div class="xk-row">'
            f'<div class="xk-head">'
            f'<span class="xk-num">0{i}</span>'
            f'<div class="xk-info">'
            f'<div class="xk-name">{esc(name)}</div>'
            f'<div class="xk-bar"><div class="xk-fill" style="--w:{pct}%;"></div><span class="xk-pct">{pct}%</span></div>'
            f'</div>'
            f'</div>'
            f'<div class="xk-reason">{esc(reason)}</div>'
            f'</div>'
        )
    if not rows:
        return ""
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">十一</span>
        <h2 class="art-title">高考选科要求</h2>
      </div>
      <div class="art-body">
        <p>新高考 3+1+2 模式下, 不同选科组合可报院校比例.</p>
      </div>
      <div class="xk-list">
        {''.join(rows)}
      </div>
    </section>'''


def render_deep_study(ds):
    """deep_study = {方向: 百分比} → 深造路径"""
    if not isinstance(ds, dict) or not ds:
        return ""
    items = sorted(ds.items(), key=lambda x: -float(x[1]) if isinstance(x[1], (int, float)) else 0)
    max_pct = max((float(v) for _, v in items if isinstance(v, (int, float))), default=1) or 1
    rows = []
    for name, pct in items[:7]:
        try:
            pct_num = float(pct)
        except (TypeError, ValueError):
            continue
        is_study = any(kw in name for kw in ["读研", "考研", "深造", "保研", "学硕", "专硕", "博士", "硕博", "研究生"])
        rows.append(
            f'<div class="ds-row{" ds-study" if is_study else ""}">'
            f'<div class="ds-name">{esc(name)}</div>'
            f'<div class="ds-bar"><div class="ds-fill" style="--w:{(pct_num/max_pct*100):.0f}%;"></div></div>'
            f'<div class="ds-pct">{pct_num:.0f}%</div>'
            f'</div>'
        )
    if not rows:
        return ""
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">九</span>
        <h2 class="art-title">深造与就业路径分布</h2>
      </div>
      <div class="art-body">
        <p>毕业生 7 大主流方向占比. 标注的为继续深造路径.</p>
      </div>
      <div class="ds-list">
        {''.join(rows)}
      </div>
    </section>'''


def render_employment(emp_list):
    """employment_direction = [{name, ratio, description, pct}] → 就业方向"""
    if not emp_list:
        return ""
    rows = []
    for i, e in enumerate(emp_list[:8], 1):
        if not isinstance(e, dict):
            continue
        name = e.get("name", "")
        ratio = e.get("ratio", "") or f"{e.get('pct', 0)}%"
        desc = e.get("description", "")
        pct = e.get("pct", 0)
        try:
            pct_num = float(pct)
        except (TypeError, ValueError):
            pct_num = 0
        rows.append(
            f'<div class="emp-row">'
            f'<div class="emp-head">'
            f'<span class="emp-num">0{i}</span>'
            f'<div class="emp-name">{esc(name)}</div>'
            f'<div class="emp-ratio">{esc(ratio)}</div>'
            f'</div>'
            f'<div class="emp-bar"><div class="emp-fill" style="--w:{pct_num}%;"></div></div>'
            f'<div class="emp-desc">{esc(desc)}</div>'
            f'</div>'
        )
    if not rows:
        return ""
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">八</span>
        <h2 class="art-title">主流就业方向</h2>
      </div>
      <div class="art-body">
        <p>8 大就业方向及占比.</p>
      </div>
      <div class="emp-list">
        {''.join(rows)}
      </div>
    </section>'''


def render_tags_strip(tags):
    if not tags:
        return ""
    return "\n".join(f'<span class="tag">{esc(t)}</span>' for t in tags[:8])


def render_one(slug, data, theme_color, chsi_sat=None):
    chsi_sat = chsi_sat or {}
    theme, theme_deep, theme_soft, theme_gold = theme_color
    title = data.get("title", slug)
    category = data.get("category", "")
    degree = data.get("degree", "")
    years = data.get("duration_years", 4)
    moe = f"{data.get('discipline', '')}{data.get('sub_discipline', '')}"
    ghost = title[0] if title else "?"
    summary = data.get("summary", "")
    hero_quote = data.get("hero_quote", "")
    hero_sig = data.get("hero_quote_sig", "")

    # 一·概况 (overview_v2) — fit/pitfalls 已拆独立段, 按 PC 端顺序
    ov2 = data.get("overview_v2", {})
    sec1 = render_overview_v2(ov2)
    # 二·什么人适合 (fit) — 杂志风
    sec2 = _render_fit_section(ov2.get("fit"))
    # 三·避坑指南 (pitfalls) — 杂志风
    sec3 = _render_pitfalls_section(ov2.get("pitfalls"))
    # 四·主要课程
    sec4 = render_curriculum(data.get("curriculum"))
    # 五·院校分布
    sec5 = render_schools(data.get("top_schools"))
    # 六·头部雇主 (tier=S/A top 12)
    sec6 = render_companies(data.get("top_companies"))
    # 七·薪资分布 (按工作年限正序, P25/P50/P75 表格)
    sec7 = render_salary(data.get("salary"))
    # 八·就业方向
    sec8 = render_employment(data.get("employment_direction"))
    # 九·深造路径
    sec9 = render_deep_study(data.get("deep_study"))
    # 十·学长学姐说 (top 3)
    sec10 = render_quote(data.get("alumni_quotes"))
    # 十一·选科要求
    sec11 = render_xuanke(data.get("xuanke_req_list"))

    # stats 数字
    salary_val = ""
    if data.get("salary"):
        first_stage = list(data["salary"].keys())[0]
        v = data["salary"][first_stage]
        if isinstance(v, dict):
            for k in ("median", "value", "p25", "ratio"):
                if k in v:
                    salary_val = str(v[k]).replace("万", "").replace("%", "").split(".")[0]
                    break
        else:
            salary_val = str(v).replace("万", "").replace("%", "").split(".")[0]
    if not salary_val:
        salary_val = "—"

    grad_rate = "—"
    ds = data.get("deep_study", {})
    if isinstance(ds, dict):
        for k, v in ds.items():
            if "读研" in k or "考研" in k or "深造" in k:
                if isinstance(v, dict) and "ratio" in v:
                    grad_rate = str(v["ratio"]).replace("%", "").split(".")[0]
                break
    if grad_rate == "—":
        # fallback 关键词搜索
        for k, v in ds.items() if isinstance(ds, dict) else []:
            if isinstance(v, str) and "%" in v:
                grad_rate = v.replace("%", "").split(".")[0]
                break

    # 读研率档位 (高/中/低) + 具体百分比
    grad_tier = "—"
    grad_keywords = ["读研", "考研", "深造", "保研", "学硕", "专硕", "博士", "硕博", "研究生", "MPA", "MBA"]
    deep_pct = 0
    if isinstance(ds, dict):
        for k, v in ds.items():
            if isinstance(k, str) and any(kw in k for kw in grad_keywords):
                if isinstance(v, (int, float)):
                    deep_pct += v
                elif isinstance(v, str):
                    try:
                        deep_pct += float(v.replace("%", ""))
                    except ValueError:
                        pass
    elif isinstance(ds, list):
        hits = sum(1 for s in ds if isinstance(s, str) and any(kw in s for kw in grad_keywords))
        deep_pct = min(hits * 15, 50)
    if deep_pct >= 30:
        grad_tier = f"高 {deep_pct:.0f}%"
    elif deep_pct >= 10:
        grad_tier = f"中 {deep_pct:.0f}%"
    elif deep_pct > 0:
        grad_tier = f"低 {deep_pct:.0f}%"

    # 满意度 (阳光高考 5 分制, 从 chsi_majors.json 按 sub_discipline + title 查)
    sub4 = (data.get("sub_discipline") or "")[:4]  # manifest 存的 4 位 (部分缺省)
    bucket = chsi_sat.get(sub4, {})
    sat_val = bucket.get(title, 0)
    if sat_val and sat_val > 0:
        satisfaction = f"{sat_val:.1f}"
    else:
        satisfaction = "—"

    # tagline
    tagline = hero_quote or ov2.get("lede", "")

    # tags
    tags_html = render_tags_strip(data.get("tags", []))

    template = TEMPLATE.read_text(encoding="utf-8")
    html = template
    replacements = {
        "{{SLUG}}": slug,
        "{{TITLE}}": title,
        "{{THEME}}": theme,
        "{{THEME_DEEP}}": theme_deep,
        "{{THEME_SOFT}}": theme_soft,
        "{{THEME_GOLD}}": theme_gold,
        "{{CATEGORY}}": category,
        "{{MOE_CODE}}": moe,
        "{{GHOST}}": ghost,
        "{{DEGREE}}": degree,
        "{{YEARS}}": str(years),
        "{{ADMISSION}}": "普通批本科",
        "{{TAGLINE}}": tagline,
        "{{SALARY}}": salary_val,
        "{{GRAD_RATE}}": grad_tier,
        "{{SATISFACTION}}": satisfaction,
    }
    for k, v in replacements.items():
        html = html.replace(k, v)
    # 注入 tags + sections
    html = html.replace('<div class="tags-strip" id="tags-strip">\n  <!-- JS render tags -->\n</div>',
                        f'<div class="tags-strip" id="tags-strip">\n  {tags_html}\n</div>')
    html = html.replace('<article class="article" id="article">\n  <!-- JS render sections -->\n</article>',
                        f'<article class="article" id="article">\n  {sec1}\n  {sec2}\n  {sec3}\n  {sec4}\n  {sec5}\n  {sec6}\n  {sec7}\n  {sec8}\n  {sec9}\n  {sec10}\n  {sec11}\n</article>')
    return html


def main():
    if not TEMPLATE.exists():
        print(f"❌ 模板不存在: {TEMPLATE}", file=sys.stderr)
        sys.exit(1)
    if not CURATED_DIR.exists():
        print(f"❌ 数据目录不存在: {CURATED_DIR}", file=sys.stderr)
        sys.exit(1)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    slugs = [m["slug"] for m in manifest["majors"]]
    styles = {m["slug"]: m.get("style", "cs") for m in manifest["majors"]}

    # 满意度字典: sub_discipline (4 位 menjia+subclass) → {name: satisfaction}
    # chsi 的 moe_code 是 6 位 (menjia 2 + subclass 2 + major 2), manifest 只存前 4 位
    # 故按 sub_discipline(4位) 桶分组, 桶内按 name 精确匹配
    chsi_sat = {}  # {sub_discipline: {name: satisfaction}}
    if CHSI_MAJORS.exists():
        chsi_data = json.loads(CHSI_MAJORS.read_text(encoding="utf-8"))
        for item in chsi_data:
            moe = item.get("moe_code", "")
            if len(moe) < 4:
                continue
            sub4 = moe[:4]  # e.g. "0901" for 农学
            chsi_sat.setdefault(sub4, {})[item["name"]] = item.get("satisfaction", 0)

    ok = 0
    skip = 0
    err = 0
    errs = []
    for slug in slugs:
        json_path = CURATED_DIR / f"{slug}.json"
        out_path = OUT_DIR / f"{slug}.html"
        if not json_path.exists():
            print(f"  ⚠ {slug}: 缺 curated json")
            skip += 1
            continue
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ✗ {slug}: json parse err {e}")
            err += 1
            errs.append(slug)
            continue
        style = styles.get(slug, data.get("style", "cs"))
        theme_color = THEMES.get(style, THEMES["cs"])
        try:
            html = render_one(slug, data, theme_color, chsi_sat)
            out_path.write_text(html, encoding="utf-8")
            ok += 1
        except Exception as e:
            print(f"  ✗ {slug}: render err {e}")
            err += 1
            errs.append(slug)

    print(f"\n✅ {ok} rendered, {skip} skipped, {err} errors")
    if errs:
        print("errs:", errs[:10])


if __name__ == "__main__":
    main()
