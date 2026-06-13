"""
v4_styles/render.py — 通用 v4 渲染 orchestrator (cs/finance/law/education/sci/eng/humanities/administration/agri/arts/gongan/business)

替代原 891 行 if/elif hero 链, 调用 dispatch 表生成 hero + 主体 9 个 section.
"""
from pathlib import Path
from .base import FONT_URLS, get_base_css, COUNT_UP_JS, BASE_V4_CSS, _dedup_by_name, soft_break_name, get_first_char
from .body_bg import get_body_bg_css
from .overview_v2 import render_overview_v2, OVERVIEW_V2_CSS
from .overview_simple import render_overview_simple, OVERVIEW_SIMPLE_CSS, is_simple_format
from .themes import HERO_FN, THEME_CSS

# ── 心愿单注入 (chip / FAB / 12 主题卡) — 4 页 v1 一致 ──
try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from wishlist_inject import (
        WISHLIST_INJECT_STYLE as _WL_STYLE,
        WISHLIST_INJECT_HEAD_LINKS as _WL_HEAD,
        render_related_themes_section as _wl_related,
        build_wishlist_init_js as _wl_init,
    )
    _WL_MANIFEST = Path(__file__).resolve().parent.parent.parent / "data" / "curated" / "manifest.json"
except Exception:
    _WL_STYLE = ""; _WL_HEAD = ""; _wl_related = lambda *a, **k: ""; _wl_init = lambda *a, **k: ""; _WL_MANIFEST = None


# ── 国家战略 ⭐ 徽章 + mini-card 样式(纯展示层,不动算法) ──
STRATEGY_CSS = """
/* ⭐ 标题旁国家战略徽章 */
.strategy-badge {
  display: inline-block; margin-left: 14px;
  font-family: 'Songti SC', 'SimSun', '宋体', serif;
  font-size: 0.75rem; color: #B8323A;
  background: linear-gradient(90deg, rgba(184,50,58,0.08), rgba(217,119,6,0.08));
  border: 1px solid rgba(184,50,58,0.3);
  padding: 4px 12px; border-radius: 4px;
  letter-spacing: 0.08em; font-weight: 600;
  vertical-align: middle;
  white-space: nowrap;
}
/* 📋 国家战略契合度 mini-card(就业方向 section 上方) */
.strategy-fit-card {
  background: linear-gradient(135deg, rgba(184,50,58,0.04), rgba(217,119,6,0.04));
  border: 1px solid rgba(184,50,58,0.2);
  border-radius: 8px;
  padding: 18px 22px; margin: 0 0 24px 0;
}
.strategy-fit-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 14px;
  flex-wrap: wrap;
}
.strategy-fit-icon { font-size: 1.1rem; }
.strategy-fit-title {
  font-weight: 600; color: #B8323A;
  font-family: 'Songti SC', 'SimSun', serif;
  font-size: 1rem; letter-spacing: 0.05em;
}
.strategy-fit-source { color: #8B7355; font-size: 0.75rem; }
.strategy-fit-list {
  display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;
}
.strategy-link {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 7px 14px; background: white;
  border: 1px solid rgba(184,50,58,0.3);
  border-radius: 6px; text-decoration: none;
  color: #1A1A1A; font-size: 0.8125rem;
  transition: all 0.2s;
}
.strategy-link:hover {
  background: rgba(184,50,58,0.06);
  border-color: #B8323A; transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(184,50,58,0.12);
}
.strategy-link-name { font-weight: 500; }
.strategy-link-tier {
  color: #D97706; font-size: 0.6875rem; font-weight: 500;
  padding-left: 8px; border-left: 1px solid rgba(184,50,58,0.2);
}
.strategy-fit-tip {
  font-size: 0.75rem; color: #8B7355;
  margin-top: 4px; font-style: italic;
}
@media (max-width: 600px) {
  .strategy-badge { display: block; margin: 8px 0 0 0; width: fit-content; }
}
"""


# ── 📚 学科门类 breadcrumb(纯展示层,不动算法) ──
DISCIPLINE_CSS = """
/* 📚 学科定位 breadcrumb(hero 标题下方) */
.discipline-breadcrumb {
  max-width: 880px; margin: -16px auto 24px; padding: 0 24px;
  font-size: 0.875rem; color: var(--c-muted, #6B7280);
  display: flex; align-items: center; flex-wrap: wrap; gap: 4px;
}
.discipline-breadcrumb a {
  color: #2A6F4F; text-decoration: none;
  border-bottom: 1px dotted rgba(42,111,79,0.4);
  transition: all 0.2s;
}
.discipline-breadcrumb a:hover {
  background: rgba(42,111,79,0.06);
  border-bottom-color: #2A6F4F;
}
.bc-sep { margin: 0 8px; color: #ccc; }
.bc-current { color: var(--c-ink, #1A1A1A); font-weight: 500; }
@media (max-width: 600px) {
  .discipline-breadcrumb { padding: 0 16px; font-size: 0.8125rem; }
}
"""


def apply_strategy_tags(html: str, data: dict) -> str:
    """注入 ⭐ 徽章(标题旁) + 战略契合度 mini-card(就业方向 section 上方)。

    - 任意主题(12 套 v4 + medicine)HTML 都可调
    - 找不到 anchor(<h1> 或就业方向 section)时静默跳过
    - data 缺 national_strategy_tags 字段时静默跳过
    """
    import re
    tags = data.get("national_strategy_tags", [])
    if not tags:
        return html

    # 1) 徽章: 注入到第一个 </h1> 后
    badge = (
        '<span class="strategy-badge" '
        f'title="{" · ".join(tags)}">'
        '⭐ 国家战略</span>'
    )
    html, n = re.subn(r'(</h1>)', r'\1' + badge, html, count=1)
    if n == 0:
        # 兜底: 注入到 hero-tags 之前(medicine 主题的结构)
        html, n2 = re.subn(
            r'(<div class="hero-tags">)',
            badge + r'\1',
            html, count=1
        )
        if n2 == 0:
            print(f"[strategy] WARN: no anchor for badge in {data.get('slug', '?')}")

    # 2) mini-card: 注入到 <div class="direction-list"> 之前
    industry_links = []
    for tag in tags:
        if "-" in tag:
            tier, industry_name = tag.split("-", 1)
        else:
            tier, industry_name = "", tag
        industry_links.append(
            f'<a href="/strategy.html#{industry_name}" class="strategy-link">'
            f'<span class="strategy-link-name">⭐ {industry_name}</span>'
            f'<span class="strategy-link-tier">{tier}</span>'
            f'</a>'
        )
    fit_html = f'''
    <div class="strategy-fit-card">
      <div class="strategy-fit-header">
        <span class="strategy-fit-icon">⭐</span>
        <span class="strategy-fit-title">国家战略契合度</span>
        <span class="strategy-fit-source">· 4+6 产业格局</span>
      </div>
      <div class="strategy-fit-list">
        {"".join(industry_links)}
      </div>
      <div class="strategy-fit-tip">⚠️ 战略契合 ≠ 个人兴趣,请结合自身情况判断</div>
    </div>'''
    html, n = re.subn(r'(<div class="direction-list">)', fit_html + r'\1', html, count=1)
    if n == 0:
        print(f"[strategy] WARN: no direction-list anchor in {data.get('slug', '?')}")

    return html


def get_strategy_css() -> str:
    """返回 strategy CSS 字符串,供 v4_medicine 注入用。"""
    return STRATEGY_CSS


# ── 📚 学科门类 lookup + breadcrumb 注入 ──
_HIERARCHY_CACHE = None

def _load_hierarchy():
    """读 discipline_hierarchy.json,返回 (disc_name_map, sub_name_map)。带缓存。"""
    global _HIERARCHY_CACHE
    if _HIERARCHY_CACHE is not None:
        return _HIERARCHY_CACHE
    try:
        from pathlib import Path
        hier_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "public" / "data" / "discipline_hierarchy.json"
        import json as _json
        data = _json.load(open(hier_path, encoding="utf-8"))
        disc_map = {}  # code → name
        sub_map = {}   # code → name
        for code, disc in data.get("门类", {}).items():
            disc_map[code] = disc["name"]
            for sub_code, sub in disc.get("sub_classes", {}).items():
                sub_map[sub_code] = sub["name"]
        _HIERARCHY_CACHE = (disc_map, sub_map)
        return _HIERARCHY_CACHE
    except Exception as e:
        print(f"[discipline] WARN: hierarchy load failed: {e}")
        _HIERARCHY_CACHE = ({}, {})
        return _HIERARCHY_CACHE


def apply_discipline_breadcrumb(html: str, data: dict) -> str:
    """注入 📚 学科定位 breadcrumb (hero h1 下方一行)。

    - 任意主题(12 套 v4 + medicine)HTML 都可调
    - data 缺 discipline + sub_discipline 时静默跳过
    """
    import re
    disc = data.get("discipline")
    sub = data.get("sub_discipline")
    title = data.get("title", "")
    if not disc or not sub:
        return html

    disc_map, sub_map = _load_hierarchy()
    disc_name = disc_map.get(disc, disc)
    sub_name = sub_map.get(sub, sub)

    bc_html = (
        f'\n<div class="discipline-breadcrumb">'
        f'<a href="/?discipline={disc}#majors">{disc_name}</a>'
        f'<span class="bc-sep">›</span>'
        f'<a href="/?discipline={disc}&sub={sub}#majors">{sub_name}</a>'
        f'<span class="bc-sep">›</span>'
        f'<span class="bc-current">{title}</span>'
        f'</div>'
    )

    # 注入到 </h1> 后(跟 strategy badge 同行,div 强制换行)
    html, n = re.subn(r'(</h1>)', r'\1' + bc_html, html, count=1)
    if n == 0:
        # 兜底: 注入到 <body> 第一个 </section> 后
        html, n2 = re.subn(r'(</section>)', r'\1' + bc_html, html, count=1)
        if n2 == 0:
            print(f"[discipline] WARN: no anchor for breadcrumb in {data.get('slug', '?')}")
    return html


def get_discipline_css() -> str:
    """返回 discipline CSS 字符串,供 v4_medicine 注入用。"""
    return DISCIPLINE_CSS


def render_v4(data: dict, style: str) -> str:
    """通用 12 套极致渲染"""
    if style not in HERO_FN:
        raise ValueError(f"Unknown v4 style: {style}")

    title = data.get("title", "未命名")
    slug = data.get("slug", "")
    summary = data.get("summary", "")
    category = data.get("category", "")
    degree = data.get("degree", "")
    duration = data.get("duration_years", 4)
    tags = data.get("tags", [])
    difficulty = data.get("difficulty", "★★★☆☆")
    data_source = data.get("data_source", "人工精编")
    updated_at = data.get("updated_at", "2026-06")
    # hero 扉页金句 (默认是教育学版的「研究怎么学, 而非教什么」)
    # 其他非师范专业在 JSON 里覆盖 hero_quote 即可换成领域金句
    hero_quote = data.get("hero_quote", "研究「怎么学」, 而非「教什么」")
    hero_quote_sig = data.get("hero_quote_sig", "—— Major Explorer 编辑寄言")
    curriculum = data.get("curriculum", {})
    top_schools = _dedup_by_name(data.get("top_schools", []), "name")
    top_companies = data.get("top_companies", [])
    salary = data.get("salary", {})
    directions = data.get("employment_direction", [])
    deep_study = data.get("deep_study", {})
    quotes = _dedup_by_name(data.get("alumni_quotes", []), "current")
    xuanke = data.get("xuanke_req_list", [])
    national_strategy_tags = data.get("national_strategy_tags", [])

    # ── 课程 ──
    def render_courses(block_name: str, courses: list) -> str:
        if not courses:
            return ""
        items = []
        for c in courses:
            name = c.get("name", "")
            credit = c.get("credit", "")
            items.append(f'          <div class="course"><span class="course-name">{name}</span><span class="course-credit">{credit} 学分</span></div>')
        return f'        <div class="curriculum-block fade-up"><div class="curriculum-title">{block_name}</div>\n' + "\n".join(items) + "\n        </div>"

    course_sections = []
    if "公共必修" in curriculum:
        course_sections.append(("公共必修 (所有院校都开)", curriculum["公共必修"]))
    if "通用专业核心" in curriculum:
        course_sections.append(("通用专业核心 (≈ 80% 院校覆盖)", curriculum["通用专业核心"]))
    if "5 校特色选修" in curriculum:
        course_sections.append(("5 校特色选修 (按方向分流)", curriculum["5 校特色选修"]))
    for k, v in curriculum.items():
        if k not in ("公共必修", "通用专业核心", "5 校特色选修"):
            course_sections.append((k, v))
    curriculum_html = "\n".join([render_courses(name, courses) for name, courses in course_sections]) if course_sections else '<p style="color:#94A3B8">课程数据待补充</p>'

    # ── 院校 (招 #8) ──
    schools_html = "\n".join(
        f'''        <div class="bento-item fade-up" data-delay="{(i % 4) * 80}">
          <div class="bento-monogram">{get_first_char(s.get("name", ""))}</div>
          <span class="bento-rank">{s.get("rank", "")}</span>
          <div class="bento-name">{soft_break_name(s.get("name", ""))}</div>
          <div class="bento-tag">{s.get("tag", "")}</div>
        </div>'''
        for i, s in enumerate(top_schools)
    ) if top_schools else '<div style="grid-column: 1/-1; padding: 24px;">院校数据待补充</div>'

    # ── 公司 ──
    def render_sparkline(values: list) -> str:
        if not values or len(values) < 3:
            return ""
        max_v = max(values) or 1
        bars = "\n".join(
            f'            <div class="sparkline-bar" style="height:{(v/max_v)*100}%"></div>'
            for v in values
        )
        return f'          <div class="sparkline">\n{bars}\n          </div>\n          <div class="sparkline-label">近 5 年招聘量趋势</div>'

    companies_html = "\n".join(
        f'''        <div class="company fade-up" data-delay="{(i % 4) * 80}">
          <div class="company-head">
            <div class="company-monogram">{get_first_char(co.get("name", ""))}</div>
            <span class="company-tier tier-{co.get("tier", "B")}">{co.get("tier", "B")}</span>
          </div>
          <div class="company-name">{soft_break_name(co.get("name", ""))}</div>
          <div class="company-meta">{co.get("headcount", "")} · 校招 {co.get("salary", "")}</div>
{render_sparkline(co.get("sparkline", []))}
        </div>'''
        for i, co in enumerate(top_companies)
    ) if top_companies else '<p>公司数据待补充</p>'

    # ── 薪资 (招 #3 数字滚动) ──
    salary_rows = []
    for stage, vals in salary.items():
        p25, p50, p75 = vals.get("p25", 0), vals.get("p50", 0), vals.get("p75", 0)
        yoy = vals.get("yoy", 0)
        max_v = max(p25, p50, p75, 1)
        if yoy > 0:
            yoy_html = f'<span class="yoy up">↗ +{yoy}%</span>'
        elif yoy < 0:
            yoy_html = f'<span class="yoy down">↘ {yoy}%</span>'
        else:
            yoy_html = f'<span class="yoy flat">→ 0%</span>'
        salary_rows.append(
            f'''        <tr>
          <td class="salary-stage">{stage}</td>
          <td class="num"><span class="approx">≈</span><span data-count="{p25}">0</span> 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p25/max_v*100}%"></span></span>{yoy_html}</td>
          <td class="num"><span class="approx">≈</span><span data-count="{p50}">0</span> 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p50/max_v*100}%"></span></span></td>
          <td class="num"><span class="approx">≈</span><span data-count="{p75}">0</span> 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p75/max_v*100}%"></span></span></td>
        </tr>'''
        )
    salary_html = "\n".join(salary_rows) if salary_rows else '<tr><td colspan="4">薪资数据待补充</td></tr>'

    direction_html = "\n".join(
        f'''        <div class="direction">
          <div class="direction-name">{d.get("name", "")}</div>
          <div class="direction-bar"><div class="direction-bar-fill" style="width:{d.get("pct", 0)}%"></div></div>
          <div class="direction-pct">{d.get("pct", 0)}%</div>
        </div>'''
        for d in directions
    ) if directions else '<p>就业方向待补充</p>'

    path_html = "\n".join(
        f'''        <div class="path-card fade-up" data-delay="{(i % 4) * 80}">
          <div class="path-pct">{v if isinstance(v, (int, float)) else len(v) if isinstance(v, list) else "推荐"}<span class="path-unit">{"%" if isinstance(v, (int, float)) else "项"}</span></div>
          <div class="path-name">{k}</div>
          {f'<ul class="path-bullets">{"".join(f"<li>{item[:80]}</li>" for item in v[:5])}</ul>' if isinstance(v, list) else f'<div class="path-detail">{v}</div>' if isinstance(v, str) else ""}
        </div>'''
        for i, (k, v) in enumerate(deep_study.items())
    ) if deep_study else '<p>深造数据待补充</p>'

    quotes_html = "\n".join(
        f'''        <div class="quote fade-up" data-delay="{(i % 4) * 80}" {"data-cite=" + repr(q.get("citation", "")) if q.get("citation") else ""}>
          <div class="quote-head">
            <div class="quote-avatar">{get_first_char(q.get("current", "?"))}</div>
            <div class="quote-byline">
              <strong>{q.get("current", "")}</strong>
              <span class="quote-source">{q.get("year", "")} · {q.get("source", "")}</span>
            </div>
          </div>
          <p class="quote-text">{q.get("quote", "")}</p>
        </div>'''
        for i, q in enumerate(quotes)
    ) if quotes else '<p>校友观点待补充</p>'

    xuanke_html = "\n".join(
        f'''        <div class="xuanke">
          <div class="xuanke-name">{x.get("name", "")}</div>
          <div class="xuanke-bar"><div class="xuanke-bar-fill" style="width:{x.get("pct", 0)}%"></div></div>
          <div class="xuanke-pct">{x.get("pct", 0)}%</div>
        </div>'''
        for x in xuanke
    ) if xuanke else '<p>选科数据待补充</p>'

    # ── HERO (dispatch) ──
    hero_html = HERO_FN[style](
        data,
        title=title, summary=summary, category=category, degree=degree,
        duration=duration, tags=tags, difficulty=difficulty, updated_at=updated_at,
        hero_quote=hero_quote, hero_quote_sig=hero_quote_sig,
    )

    # ── 国家战略 ⭐ 徽章: 中心化注入在完整 HTML 末尾(不动 12 个 theme 文件) ──

    body_bg = get_body_bg_css(style)

    _html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- Lighthouse perf: 字体源提前预连接 (DNS + TCP + TLS), 减 FCP/LCP 100-400ms -->
<link rel="preconnect" href="https://fonts.loli.net" crossorigin>
<link rel="dns-prefetch" href="https://fonts.loli.net">
<!-- inline favicon: 防止 file:// / http 访问时控制台 404 favicon.ico -->
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 16%22><text y=%2214%22 font-size=%2214%22>📘</text></svg>">
{_WL_HEAD}
<title>{title}专业介绍 2026 高考 | Major Explorer</title>
<meta name="description" content="{summary[:100]}">
<style>
{FONT_URLS[style]}
{get_base_css()}
{BASE_V4_CSS}
{body_bg}
{OVERVIEW_V2_CSS}
{OVERVIEW_SIMPLE_CSS}
{THEME_CSS[style]}
{_WL_STYLE}
{STRATEGY_CSS}
</style>
</head>
<body>
{hero_html}

<section class="tab" id="overview">
  <div class="watermark">01</div>
  <div class="container">
    <div class="section-num">01 / 10 · 速览</div>
    <h2>速览</h2>
    {render_overview_simple(data) if is_simple_format(data) else (render_overview_v2(data) if data.get("overview_v2") else (f"<p class=lede drop-cap>{summary}</p>"
    + (f"<h3>这个专业学什么?</h3><p>{data.get("what_you_learn", "")}</p>" if data.get("what_you_learn") else "")
    + (f"<h3>什么人适合?</h3><p>{data.get("who_fits", "")}</p>" if data.get("who_fits") else "")
    + (f"<h3>避坑指南</h3><p>{data.get("pitfalls", "")}</p>" if data.get("pitfalls") else "")))}
  </div>
</section>

<section class="tab" id="curriculum">
  <div class="watermark">02</div>
  <div class="container">
    <div class="section-num">02 / 10 · 课程</div>
    <h2>主要课程</h2>
    <p class="curriculum-lede">{data.get("curriculum_note", "全国通用 4 年制框架, 不同高校在大三/大四有不同方向分流。")}</p>
    <div class="curriculum-grid">
{curriculum_html}
    </div>
  </div>
</section>

<section class="tab" id="schools">
  <div class="watermark">03</div>
  <div class="container">
    <div class="section-num">03 / 10 · 院校</div>
    <h2>院校分布</h2>
    <p class="lede">教育部学科评估第四轮 (2017, 第五轮 2022 部分公开)。A+ = 前 2% 或前 2 所, A = 前 2-10%, A- = 前 10-20%。</p>
    <div class="bento">
{schools_html}
    </div>
  </div>
</section>

<section class="tab" id="companies">
  <div class="watermark">04</div>
  <div class="container">
    <div class="section-num">04 / 10 · 头部雇主</div>
    <h2>头部雇主</h2>
    <p class="lede">S = 顶级, A = 知名, B = 大量招。校招薪资为 2024 秋招主流 offer 中位数。底部 bar = 近 5 年招聘量趋势。</p>
    <div class="company-grid">
{companies_html}
    </div>
  </div>
</section>

<section class="tab" id="salary">
  <div class="watermark">05</div>
  <div class="container">
    <div class="section-num">05 / 10 · 薪资</div>
    <h2>薪资分布</h2>
    <p class="lede">数据源: 麦可思 2024 + 招聘平台 2024 校招采样。单位: 万/年。P25/P50/P75 = 25/50/75 百分位。≈ 表示估算值。↗ = 3 年变化。进入视口时数字滚动。</p>
    <table class="salary-table">
      <thead>
        <tr><th>阶段</th><th>P25</th><th>P50 中位</th><th>P75 高位</th></tr>
      </thead>
      <tbody>
{salary_html}
      </tbody>
    </table>
  </div>
</section>

<section class="tab" id="directions">
  <div class="watermark">06</div>
  <div class="container">
    <div class="section-num">06 / 10 · 就业方向</div>
    <h2>就业方向</h2>
    <p class="lede">毕业 1-3 年的去向分布, 占比合计 100%。</p>
    <div class="direction-list">
{direction_html}
    </div>
  </div>
</section>

<section class="tab" id="deep-study">
  <div class="watermark">07</div>
  <div class="container">
    <div class="section-num">07 / 10 · 深造路径</div>
    <h2>深造路径</h2>
    <div class="path-grid">
{path_html}
    </div>
  </div>
</section>

<section class="tab" id="quotes">
  <div class="watermark">08</div>
  <div class="container">
    <div class="section-num">08 / 10 · 学长学姐说</div>
    <h2>学长学姐说</h2>
    <p class="lede">真实在校生/毕业生观点, 有夸有劝退, 自己判断。</p>
    <div class="quotes">
{quotes_html}
    </div>
  </div>
</section>

<section class="tab" id="xuanke">
  <div class="watermark">09</div>
  <div class="container">
    <div class="section-num">09 / 10 · 选科要求</div>
    <h2>选科要求 (新高考 3+1+2)</h2>
    <p class="lede">基于 2024 年全国开设此专业院校的招生选科要求统计。覆盖率越高, 你的选科组合能报的院校越多。</p>
    <div class="xuanke-list">
{xuanke_html}
    </div>
  </div>
</section>

{_wl_related(slug, _WL_MANIFEST) if _WL_MANIFEST else ""}
<footer>
  <div class="container">
    <div class="label">Major Explorer · 2026 高考专业指南</div>
    <div class="data-source">数据源: {data_source}</div>
  </div>
</footer>

{COUNT_UP_JS}
{_wl_init(slug, title, style, category)}
</body>
</html>"""

    # ── 在完整 HTML 上注入 ⭐ 徽章 + mini-card + 📚 breadcrumb(对 12 theme 都生效) ──
    return apply_discipline_breadcrumb(apply_strategy_tags(_html, data), data)
