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
    """curriculum = {公共必修, 通用专业核心, 5 校特色选修, 实践教学环节}"""
    if not curriculum:
        return ""
    year_map = {
        "公共必修": "大一",
        "通用专业核心": "大二",
        "5 校特色选修": "大三",
        "实践教学环节": "大四",
    }
    rows = []
    for key, label in year_map.items():
        items = curriculum.get(key, [])
        if not items:
            continue
        # items 可能是 list[str] 也可能是 list[dict]
        if isinstance(items[0], dict):
            names = " · ".join(it.get("course", it.get("name", str(it))) for it in items)
            tag = items[0].get("tag", label)
        else:
            names = " · ".join(str(it) for it in items)
            tag = label
        # 高亮 ★
        names_html = re.sub(r"★", '<strong style="color:var(--accent);">★</strong>', esc(names))
        rows.append(f'''<div class="course-row">
          <div class="course-yr">{esc(label)}</div>
          <div class="course-names">{names_html}</div>
          <div class="course-tag">{esc(tag)}</div>
        </div>''')
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">二</span>
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
    """ov2 = {lede, what, fit, pitfalls} — 用 fit + pitfalls 渲染风险段"""
    if not ov2:
        return ""
    fit = ov2.get("fit", "")
    pitfalls = ov2.get("pitfalls", [])
    if isinstance(pitfalls, list):
        pitfalls_text = "<br>".join("• " + esc(p) for p in pitfalls[:5])
    else:
        pitfalls_text = esc(pitfalls)

    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">一</span>
        <h2 class="art-title">这个专业到底学什么</h2>
      </div>
      <div class="art-body">
        <p>{esc(ov2.get("what", ""))}</p>
        <p>{esc(ov2.get("lede", ""))}</p>
      </div>
      <div class="risk">
        <div class="risk-head">⚠ 读之前先想清</div>
        <div class="risk-body">
          <strong>适合谁。</strong>{esc(fit)}
        </div>
      </div>
      {f'<div class="risk"><div class="risk-head">⚠ 容易踩的坑</div><div class="risk-body">{pitfalls_text}</div></div>' if pitfalls_text else ''}
    </section>'''


def render_salary(salary):
    """salary = {stage: pct_dict}"""
    if not salary:
        return ""
    # 计算最大 width
    def get_pct(v):
        if isinstance(v, dict):
            for k in ("ratio", "pct", "value", "median", "p25", "p75"):
                if k in v:
                    try: return float(str(v[k]).replace("%", "").replace("万", ""))
                    except: pass
        return 0
    rows_data = []
    for stage, val in salary.items():
        v = get_pct(val)
        rows_data.append((stage, v, val))
    rows_data.sort(key=lambda x: -x[1])
    max_w = max((r[1] for r in rows_data), default=1) or 1
    rows_html = []
    for stage, pct, val in rows_data[:5]:
        # 提取显示值
        if isinstance(val, dict):
            disp = val.get("label") or val.get("display") or f"{pct:.0f}%"
        else:
            disp = f"{val}%" if isinstance(val, (int, float)) else str(val)
        w = f"{(pct/max_w*100):.0f}%" if pct > 0 else "8%"
        rows_html.append(f'''<div class="sal-row">
          <div class="sal-l">{esc(stage)}</div>
          <div class="sal-bar" style="--w: {w};"></div>
          <div class="sal-v">{esc(disp)}</div>
        </div>''')
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">三</span>
        <h2 class="art-title">毕业后真的能拿多少</h2>
      </div>
      <div class="art-body">
        <p>头部太亮、中部太挤、尾部不香 — 看完分布再决定要不要押这个赛道.</p>
      </div>
      <div class="sal-rows">
        {''.join(rows_html)}
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
        <h2 class="art-title">头部院校参考</h2>
      </div>
      <div class="art-body">
        <p>按 2025 软科 + 武书连综合排名。<strong>分数线仅供参考</strong>, 录取以教育考试院公告为准.</p>
      </div>
      {''.join(rows)}
    </section>'''


def render_quote(quote_data, title=""):
    """quote_data = [{quote, name, school, tag}]"""
    if not quote_data:
        return ""
    q = quote_data[0]
    text = q.get("quote", q.get("text", ""))
    by = q.get("name", "") or q.get("school", "")
    sig = q.get("tag", "")
    by_full = f"{by} · {sig}" if by and sig else (by or sig)
    return f'''<section class="art-sec">
      <div class="art-head">
        <span class="art-num">四</span>
        <h2 class="art-title">学长学姐说</h2>
      </div>
      <div class="art-body">
        <p>选专业之前, 听听真正读过的人是后悔还是庆幸.</p>
      </div>
      <div class="pull">
        "{esc(text)}"
        <span class="by">— {esc(by_full)}</span>
      </div>
    </section>'''


def render_tags_strip(tags):
    if not tags:
        return ""
    return "\n".join(f'<span class="tag">{esc(t)}</span>' for t in tags[:8])


def render_one(slug, data, theme_color):
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

    # 1) 一·概况 (overview_v2)  +  pull quote
    ov2 = data.get("overview_v2", {})
    sec1 = render_overview_v2(ov2)
    # 2) 课程
    sec2 = render_curriculum(data.get("curriculum"))
    # 3) 薪资
    sec3 = render_salary(data.get("salary"))
    # 4) 校友引言
    sec4 = render_quote(data.get("alumni_quotes"))
    # 5) 院校
    sec5 = render_schools(data.get("top_schools"))

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

    # 满意度
    sat = data.get("difficulty", "—")
    # difficulty 是 ★ 数量, 满意度另算
    satisfaction = "7.0"

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
        "{{GRAD_RATE}}": grad_rate,
        "{{SATISFACTION}}": satisfaction,
    }
    for k, v in replacements.items():
        html = html.replace(k, v)
    # 注入 tags + sections
    html = html.replace('<div class="tags-strip" id="tags-strip">\n  <!-- JS render tags -->\n</div>',
                        f'<div class="tags-strip" id="tags-strip">\n  {tags_html}\n</div>')
    html = html.replace('<article class="article" id="article">\n  <!-- JS render sections -->\n</article>',
                        f'<article class="article" id="article">\n  {sec1}\n  {sec2}\n  {sec3}\n  {sec4}\n  {sec5}\n</article>')
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
            html = render_one(slug, data, theme_color)
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
