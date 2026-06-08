"""
scripts/generate_dashboard.py — Major Explorer 引擎

核心 1 函数: generate_dashboard(data, style, output_path=None)
- 5 套设计 (cs / finance / medicine / law / education), 共享 1 套 HTML 模板
- 精品 (data/curated/*.json) 和 长尾 (web_search 出的 dict) 视觉一致
- 单文件 HTML, 内嵌 CSS, 引用 Google Fonts, 不依赖 JS 框架

设计: 用 CSS 变量做主题切换. 5 套 :root 块, 1 套共享样式. 改 1 套 = 1 个 dict.

调用:
  python3 generate_dashboard.py --data <json> --style <cs|finance|medicine|law|education> --output <html>
"""
import argparse
import json
from pathlib import Path

# ──────────────────────────────────────────────────────────
# 5 套设计 tokens — 每个风格 1 个 :root 块 (CSS 变量)
# ──────────────────────────────────────────────────────────
STYLE_TOKENS = {
  "cs": {
    "font_heading": "'JetBrains Mono', 'SF Mono', Consolas, monospace",
    "font_body": "'JetBrains Mono', 'SF Mono', Consolas, monospace",
    "font_cn": "'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', monospace",
    "bg": "#0F172A", "fg": "#F8FAFC", "muted": "#94A3B8",
    "primary": "#22C55E", "primary_dim": "#16A34A", "primary_glow": "rgba(34, 197, 94, 0.25)",
    "surface": "#1E293B", "surface_alt": "#334155", "border": "#475569",
    "accent_red": "#EF4444", "accent_amber": "#F59E0B",
    "label": "TERMINAL",
    "tagline": "编程是载体, 数学是底层",
    "decor": "$ cat /major/{slug}.md",
  },
  "finance": {
    "font_heading": "'Bodoni Moda', 'Source Han Serif SC', 'Songti SC', serif",
    "font_body": "'Jost', 'PingFang SC', 'Microsoft YaHei', sans-serif",
    "font_cn": "'Jost', 'PingFang SC', 'Microsoft YaHei', sans-serif",
    "bg": "#FAFAF9", "fg": "#0C0A09", "muted": "#78716C",
    "primary": "#1C1917", "primary_dim": "#44403C", "primary_glow": "rgba(161, 98, 7, 0.15)",
    "surface": "#FFFFFF", "surface_alt": "#F5F5F4", "border": "#D6D3D1",
    "accent_red": "#DC2626", "accent_amber": "#A16207",
    "label": "PRIVATE WEALTH",
    "tagline": "资金的时间价值 × 风险定价",
    "decor": "——  {title}  ——",
  },
  "medicine": {
    "font_heading": "'Figtree', 'PingFang SC', sans-serif",
    "font_body": "'Noto Sans SC', 'PingFang SC', sans-serif",
    "font_cn": "'Noto Sans SC', 'PingFang SC', sans-serif",
    "bg": "#F0FDFA", "fg": "#134E4A", "muted": "#5EEAD4",
    "primary": "#0F766E", "primary_dim": "#14B8A6", "primary_glow": "rgba(15, 118, 110, 0.18)",
    "surface": "#FFFFFF", "surface_alt": "#CCFBF1", "border": "#99F6E4",
    "accent_red": "#DC2626", "accent_amber": "#0369A1",
    "label": "EVIDENCE-BASED",
    "tagline": "35 岁后越老越值钱",
    "decor": "+ {title} +",
  },
  "law": {
    "font_heading": "'EB Garamond', 'Source Han Serif SC', 'Songti SC', serif",
    "font_body": "'Lato', 'PingFang SC', sans-serif",
    "font_cn": "'Lato', 'PingFang SC', sans-serif",
    "bg": "#FFFBEB", "fg": "#0F172A", "muted": "#78716C",
    "primary": "#78716C", "primary_dim": "#92400E", "primary_glow": "rgba(217, 119, 6, 0.15)",
    "surface": "#FFFFFF", "surface_alt": "#FEF3C7", "border": "#E7E5E4",
    "accent_red": "#DC2626", "accent_amber": "#D97706",
    "label": "ARTICLE {n}",
    "tagline": "逻辑 + 表达 + 立场",
    "decor": "§ {title} §",
  },
  "education": {
    "font_heading": "'Playfair Display', 'Source Han Serif SC', 'Songti SC', serif",
    "font_body": "'Inter', 'PingFang SC', sans-serif",
    "font_cn": "'Inter', 'PingFang SC', sans-serif",
    "bg": "#FFFBEB", "fg": "#1C1917", "muted": "#78716C",
    "primary": "#9A3412", "primary_dim": "#C2410C", "primary_glow": "rgba(154, 52, 18, 0.18)",
    "surface": "#FFF7ED", "surface_alt": "#FED7AA", "border": "#FDBA74",
    "accent_red": "#DC2626", "accent_amber": "#F59E0B",
    "label": "EDU. {n}",
    "tagline": "研究'怎么学'的科学",
    "decor": "❀  {title}  ❀",
  },
}

# ──────────────────────────────────────────────────────────
# 5 套设计 CSS (共享结构, 切换 tokens)
# ──────────────────────────────────────────────────────────
BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; scroll-behavior: smooth; }
body {
  font-family: var(--font-body);
  background: var(--bg);
  color: var(--fg);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
h1, h2, h3, h4 { font-family: var(--font-heading); font-weight: 600; line-height: 1.25; }
a { color: var(--primary); text-decoration: none; transition: opacity 150ms; }
a:hover { opacity: 0.75; }
button { font-family: inherit; cursor: pointer; border: none; }

/* layout */
.container { max-width: 1200px; margin: 0 auto; padding: 0 32px; }
@media (max-width: 768px) { .container { padding: 0 20px; } }

/* hero */
.hero {
  padding: 80px 0 60px;
  border-bottom: 1px solid var(--border);
  position: relative;
  overflow: hidden;
}
.hero-decor {
  font-family: var(--font-cn);
  font-size: 0.875rem;
  color: var(--muted);
  letter-spacing: 0.1em;
  margin-bottom: 24px;
  text-transform: uppercase;
}
.hero h1 {
  font-size: clamp(2.5rem, 5vw, 4.5rem);
  letter-spacing: -0.02em;
  margin-bottom: 16px;
}
.hero-tagline {
  font-size: 1.25rem;
  color: var(--muted);
  margin-bottom: 32px;
  max-width: 720px;
}
.hero-tags {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-bottom: 32px;
}
.tag {
  padding: 6px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  font-size: 0.875rem;
  color: var(--fg);
}
.tag.primary {
  background: var(--primary_glow);
  border-color: var(--primary);
  color: var(--primary);
  font-weight: 500;
}
.hero-stats {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-top: 32px;
}
.stat {
  padding: 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
}
.stat-label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }
.stat-value { font-family: var(--font-heading); font-size: 1.75rem; font-weight: 600; color: var(--fg); margin-top: 4px; }

/* sections */
section.tab {
  padding: 80px 0;
  border-bottom: 1px solid var(--border);
}
.section-num {
  font-family: var(--font-heading);
  font-size: 0.875rem;
  color: var(--primary);
  letter-spacing: 0.15em;
  margin-bottom: 12px;
}
section.tab h2 {
  font-size: clamp(1.75rem, 3vw, 2.5rem);
  margin-bottom: 32px;
}
section.tab h3 {
  font-size: 1.25rem;
  margin: 32px 0 12px;
}
section.tab p { margin-bottom: 16px; color: var(--fg); }
section.tab ul, section.tab ol { margin-left: 24px; margin-bottom: 16px; }

/* bento grid (院校) */
.bento {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
  margin-top: 24px;
}
.bento-item {
  padding: 24px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  transition: transform 200ms ease-out, box-shadow 200ms ease-out;
}
.bento-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px var(--primary_glow);
}
.bento-rank {
  display: inline-block;
  padding: 2px 8px;
  background: var(--primary_glow);
  color: var(--primary);
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 8px;
}
.bento-name { font-family: var(--font-heading); font-size: 1.125rem; font-weight: 600; margin-bottom: 4px; }
.bento-tag { font-size: 0.875rem; color: var(--muted); }

/* company cards (头部公司) */
.company-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-top: 24px;
}
.company {
  padding: 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  position: relative;
}
.company-tier {
  position: absolute; top: 12px; right: 12px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
}
.tier-S { background: var(--accent_amber); color: var(--bg); }
.tier-A { background: var(--primary); color: var(--bg); }
.tier-B { background: var(--surface_alt); color: var(--fg); }
.company-name { font-family: var(--font-heading); font-size: 1.125rem; font-weight: 600; margin-bottom: 8px; }
.company-meta { font-size: 0.8125rem; color: var(--muted); }

/* salary box (薪资箱型) */
.salary-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 24px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.salary-table th, .salary-table td {
  padding: 16px 20px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
.salary-table th {
  background: var(--surface_alt);
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}
.salary-bar {
  display: inline-block;
  height: 8px;
  background: var(--primary_glow);
  border-radius: 4px;
  margin-left: 8px;
  vertical-align: middle;
}
.salary-bar-fill { display: block; height: 100%; background: var(--primary); border-radius: 4px; }

/* employment pie (用横向 bar 替代饼图, 更好读) */
.direction-list { margin-top: 24px; }
.direction {
  display: grid;
  grid-template-columns: 140px 1fr 60px;
  align-items: center;
  gap: 16px;
  padding: 10px 0;
}
.direction-name { font-weight: 500; }
.direction-bar {
  height: 20px;
  background: var(--surface_alt);
  border-radius: 4px;
  overflow: hidden;
}
.direction-bar-fill { height: 100%; background: var(--primary); }
.direction-pct { font-family: var(--font-heading); font-weight: 600; text-align: right; }

/* deep study (深造) */
.path-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-top: 24px;
}
.path-card {
  padding: 24px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  text-align: center;
}
.path-pct {
  font-family: var(--font-heading);
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 4px;
}
.path-name { color: var(--muted); font-size: 0.875rem; }

/* quotes (学长学姐) */
.quotes { margin-top: 24px; }
.quote {
  padding: 24px 28px;
  background: var(--surface);
  border-left: 4px solid var(--primary);
  border-radius: 0 12px 12px 0;
  margin-bottom: 16px;
  position: relative;
}
.quote-text {
  font-size: 1.0625rem;
  font-style: italic;
  margin-bottom: 12px;
  line-height: 1.7;
}
.quote-meta {
  font-size: 0.875rem;
  color: var(--muted);
  display: flex; gap: 12px;
}
.quote-meta strong { color: var(--fg); font-weight: 500; }

/* xuanke (选科) */
.xuanke-list { margin-top: 24px; }
.xuanke {
  display: grid;
  grid-template-columns: 180px 1fr 80px;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-weight: 500; }
.xuanke-bar {
  height: 12px;
  background: var(--surface_alt);
  border-radius: 6px;
  overflow: hidden;
}
.xuanke-bar-fill { height: 100%; background: var(--primary); }
.xuanke-pct { font-family: var(--font-heading); font-weight: 600; text-align: right; }

/* curriculum (主要课程) */
.curriculum-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-top: 24px;
}
.curriculum-block {
  padding: 24px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
}
.curriculum-title {
  font-family: var(--font-heading);
  font-size: 0.875rem;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 16px;
}
.course {
  padding: 8px 0;
  border-bottom: 1px dashed var(--border);
  display: flex; justify-content: space-between;
  font-size: 0.9375rem;
}
.course:last-child { border-bottom: none; }
.course-credit { color: var(--muted); font-size: 0.8125rem; }

/* CTA (关联志愿) */
.cta {
  padding: 48px;
  background: var(--primary_glow);
  border: 1px solid var(--primary);
  border-radius: 16px;
  margin-top: 24px;
  text-align: center;
}
.cta h3 {
  font-size: 1.5rem;
  margin-bottom: 12px;
  color: var(--fg);
}
.cta p { color: var(--muted); margin-bottom: 24px; }
.cta-form {
  display: flex; flex-wrap: wrap;
  gap: 12px; justify-content: center;
  margin-bottom: 16px;
}
.cta-input {
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--fg);
  font-family: var(--font-heading);
  font-size: 1rem;
  width: 160px;
}
.cta-button {
  padding: 12px 32px;
  background: var(--primary);
  color: var(--bg);
  border-radius: 8px;
  font-family: var(--font-heading);
  font-size: 1rem;
  font-weight: 600;
  transition: transform 150ms;
}
.cta-button:hover { transform: translateY(-1px); }

/* footer */
footer {
  padding: 60px 0 40px;
  text-align: center;
  color: var(--muted);
  font-size: 0.875rem;
  border-top: 1px solid var(--border);
}
.data-source {
  margin-top: 12px;
  font-size: 0.8125rem;
  opacity: 0.7;
}
"""

STYLE_OVERRIDES = {
  "cs": """
.hero { background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%); }
.hero-decor::before { content: "$ "; color: var(--primary); }
.hero-decor::after { content: "  # reading..."; color: var(--muted); animation: blink 1.2s infinite; }
@keyframes blink { 50% { opacity: 0; } }
.hero h1 { color: var(--fg); position: relative; }
.hero h1::before { content: "> "; color: var(--primary); }
.tag { font-family: var(--font-cn); }
.bento-item::before {
  content: "[+]";
  position: absolute; top: 16px; right: 16px;
  font-family: var(--font-cn);
  color: var(--primary);
  font-size: 0.875rem;
  font-weight: 700;
}
.bento-item { position: relative; }
.quote::before { content: "//"; color: var(--primary); font-family: var(--font-cn); margin-right: 8px; }
.quote-text { font-family: var(--font-cn); font-style: normal; }
.cta { background: #0F172A; }
.cta h3::before { content: "$ "; color: var(--primary); }
""",
  "finance": """
.hero { background: linear-gradient(135deg, #FAFAF9 0%, #FEF3C7 100%); }
.hero-decor { font-family: var(--font-heading); font-style: italic; font-size: 1rem; letter-spacing: 0.05em; }
.hero h1 { font-style: italic; font-weight: 500; }
.hero h1::after { content: " ®"; font-size: 0.4em; vertical-align: super; color: var(--primary); }
.tag { font-family: var(--font-heading); letter-spacing: 0.04em; }
.bento-item::after { content: "★"; position: absolute; top: 20px; right: 20px; color: var(--accent_amber); font-size: 1.125rem; }
.bento-item { position: relative; }
.quote { border-left-color: var(--accent_amber); }
.quote-text { font-family: var(--font-heading); font-size: 1.25rem; font-style: italic; }
.cta { background: linear-gradient(135deg, #FFFFFF 0%, #FEF3C7 100%); border-color: var(--accent_amber); }
.cta-button { background: var(--accent_amber); }
.salary-table th { background: var(--accent_amber); color: #FFFFFF; }
""",
  "medicine": """
.hero { background: linear-gradient(180deg, #F0FDFA 0%, #CCFBF1 100%); }
.hero-decor { color: var(--primary); font-weight: 500; }
.tag.primary { background: var(--primary); color: white; }
.quote { border-left-color: var(--primary); }
.quote::before { content: "▶ "; color: var(--primary); }
.cta { background: var(--primary); }
.cta h3, .cta p { color: white; }
.cta-button { background: white; color: var(--primary); }
.section-num { color: var(--primary); }
""",
  "law": """
.hero { background: linear-gradient(180deg, #FFFBEB 0%, #FEF3C7 100%); border-bottom: 2px solid var(--accent_amber); }
.hero h1 { font-style: italic; text-align: center; }
.hero-decor { text-align: center; font-family: var(--font-heading); font-style: italic; font-size: 1.125rem; }
.hero-stats { border-top: 1px solid var(--border); padding-top: 32px; }
.bento-item { background: linear-gradient(135deg, #FFFFFF 0%, #FFFBEB 100%); }
.bento-item::before { content: "§"; position: absolute; top: 8px; right: 16px; color: var(--accent_amber); font-family: var(--font-heading); font-size: 1.5rem; font-weight: 700; }
.bento-item { position: relative; }
.quote { border-left: 4px double var(--accent_amber); }
.quote-text { font-family: var(--font-heading); font-size: 1.125rem; }
.cta { background: var(--primary); color: white; }
.cta h3, .cta p { color: white; }
.cta-input { background: white; color: var(--fg); }
.cta-button { background: var(--accent_amber); }
""",
  "education": """
.hero { background: linear-gradient(135deg, #FFF7ED 0%, #FED7AA 100%); }
.hero h1 { font-style: italic; }
.hero-decor { color: var(--primary); font-weight: 500; letter-spacing: 0.1em; }
.tag.primary { background: var(--primary); color: white; border-color: var(--primary); }
.bento-item { background: linear-gradient(180deg, #FFFFFF 0%, #FFF7ED 100%); border-color: var(--accent_amber); }
.bento-item::before { content: "❀"; position: absolute; top: 12px; right: 16px; color: var(--accent_amber); font-size: 1rem; }
.bento-item { position: relative; }
.quote { border-left-color: var(--accent_amber); background: linear-gradient(90deg, #FFF7ED 0%, #FFFFFF 100%); }
.quote-text { font-family: var(--font-heading); font-style: italic; }
.cta { background: linear-gradient(135deg, var(--primary) 0%, var(--accent_amber) 100%); color: white; border: none; }
.cta h3, .cta p { color: white; }
.cta-button { background: white; color: var(--primary); }
""",
}


def build_style_css(style: str) -> str:
    """Build complete <style> block for given style."""
    tok = STYLE_TOKENS[style]
    root_vars = "\n".join(f"  --{k}: {v};" for k, v in tok.items() if k not in ("label", "tagline", "decor"))
    font_url = ""
    if style == "cs":
        font_url = "@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');"
    elif style == "finance":
        font_url = "@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Jost:wght@300;400;500;600;700&display=swap');"
    elif style == "medicine":
        font_url = "@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');"
    elif style == "law":
        font_url = "@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Lato:wght@300;400;700&display=swap');"
    elif style == "education":
        font_url = "@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap');"

    css = f""":root {{
{root_vars}
}}
{font_url}
{BASE_CSS}
{STYLE_OVERRIDES.get(style, "")}
"""
    return css


# ──────────────────────────────────────────────────────────
# HTML 模板 (1 套, 风格由 CSS 变量决定)
# ──────────────────────────────────────────────────────────
def render_html(data: dict, style: str) -> str:
    tok = STYLE_TOKENS[style]
    title = data.get("title", "未命名专业")
    slug = data.get("slug", "unknown")
    summary = data.get("summary", "")
    category = data.get("category", "")
    degree = data.get("degree", "")
    duration = data.get("duration_years", 4)
    tags = data.get("tags", [])
    difficulty = data.get("difficulty", "★★★☆☆")
    is_5_year = duration == 5

    curriculum = data.get("curriculum", {})
    top_schools = data.get("top_schools", [])
    top_companies = data.get("top_companies", [])
    salary = data.get("salary", {})
    directions = data.get("employment_direction", [])
    deep_study = data.get("deep_study", {})
    quotes = data.get("alumni_quotes", [])
    xuanke = data.get("xuanke_req_list", [])
    data_source = data.get("data_source", "实时整合")
    updated_at = data.get("updated_at", "2026-06")

    decor = tok["decor"].format(slug=slug, title=title, n=1)

    # 渲染课程
    def render_courses(block_name: str, courses: list) -> str:
        if not courses:
            return ""
        items = "\n".join(
            f'      <div class="course"><span>{c.get("name", "")}</span><span class="course-credit">{c.get("credit", "")} 学分</span></div>'
            for c in courses
        )
        return f'    <div class="curriculum-block"><div class="curriculum-title">{block_name}</div>\n{items}\n    </div>'

    curriculum_html = "\n".join([
        render_courses(name, courses) for name, courses in curriculum.items()
    ]) if curriculum else '<p style="color:var(--muted)">课程数据待补充</p>'

    # 渲染院校 (bento)
    schools_html = "\n".join(
        f'''      <div class="bento-item">
        <span class="bento-rank">{s.get("rank", "")}</span>
        <div class="bento-name">{s.get("name", "")}</div>
        <div class="bento-tag">{s.get("tag", "")}</div>
      </div>'''
        for s in top_schools
    ) if top_schools else '<p style="color:var(--muted)">院校数据待补充</p>'

    # 渲染头部公司
    companies_html = "\n".join(
        f'''      <div class="company">
        <span class="company-tier tier-{c.get("tier", "B")}">{c.get("tier", "B")}</span>
        <div class="company-name">{c.get("name", "")}</div>
        <div class="company-meta">{c.get("headcount", "")} · 校招 {c.get("salary", "")}</div>
      </div>'''
        for c in top_companies
    ) if top_companies else '<p style="color:var(--muted)">公司数据待补充</p>'

    # 渲染薪资
    salary_rows = []
    for stage, vals in salary.items():
        p25, p50, p75 = vals.get("p25", 0), vals.get("p50", 0), vals.get("p75", 0)
        max_v = max(p25, p50, p75, 1)
        salary_rows.append(
            f'''      <tr>
        <td><strong>{stage}</strong></td>
        <td>
          P25 {p25} 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p25/max_v*100}%"></span></span>
        </td>
        <td>
          P50 {p50} 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p50/max_v*100}%"></span></span>
        </td>
        <td>
          P75 {p75} 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p75/max_v*100}%"></span></span>
        </td>
      </tr>'''
        )
    salary_html = "\n".join(salary_rows) if salary_rows else '<tr><td colspan="4" style="color:var(--muted)">薪资数据待补充</td></tr>'

    # 渲染就业方向
    direction_html = "\n".join(
        f'''      <div class="direction">
        <div class="direction-name">{d.get("name", "")}</div>
        <div class="direction-bar"><div class="direction-bar-fill" style="width:{d.get("pct", 0)}%"></div></div>
        <div class="direction-pct">{d.get("pct", 0)}%</div>
      </div>'''
        for d in directions
    ) if directions else '<p style="color:var(--muted)">就业方向待补充</p>'

    # 渲染深造
    path_html = "\n".join(
        f'''      <div class="path-card">
        <div class="path-pct">{v}%</div>
        <div class="path-name">{k}</div>
      </div>'''
        for k, v in deep_study.items()
    ) if deep_study else '<p style="color:var(--muted)">深造数据待补充</p>'

    # 渲染 quote
    quotes_html = "\n".join(
        f'''      <div class="quote">
        <div class="quote-text">"{q.get("quote", "")}"</div>
        <div class="quote-meta">
          <strong>{q.get("current", "")}</strong>
          <span>· {q.get("year", "")} 届 ·</span>
          <span>{q.get("source", "")}</span>
        </div>
      </div>'''
        for q in quotes
    ) if quotes else '<p style="color:var(--muted)">校友观点待补充</p>'

    # 渲染选科
    xuanke_html = "\n".join(
        f'''      <div class="xuanke">
        <div class="xuanke-name">{x.get("name", "")}</div>
        <div class="xuanke-bar"><div class="xuanke-bar-fill" style="width:{x.get("pct", 0)}%"></div></div>
        <div class="xuanke-pct">{x.get("pct", 0)}%</div>
      </div>'''
        for x in xuanke
    ) if xuanke else '<p style="color:var(--muted)">选科数据待补充</p>'

    # 5+3+X 时间轴 (仅医学)
    timeline_html = ""
    if style == "medicine" and is_5_year and data.get("timeline"):
        tl = data["timeline"]
        timeline_html = f'''
  <section class="tab" id="timeline">
    <div class="container">
      <div class="section-num">05+</div>
      <h2>学制时间轴</h2>
      <p style="color:var(--muted); margin-bottom: 32px;">临床医学 5 年起步, 3+X 才是真正的开始。家里能撑住 10 年低收入吗?</p>
      <div class="timeline">
        {''.join(f'<div class="tl-item"><div class="tl-year">{t.get("year")}</div><div class="tl-stage">{t.get("stage")}</div><div class="tl-income">{t.get("income", "")}</div></div>' for t in tl)}
      </div>
    </div>
  </section>'''

    # 头部公司 (CS 特别版: 加 GitHub link)
    company_section_extra = ""
    if style == "cs" and data.get("github_metric"):
        gm = data["github_metric"]
        company_section_extra = f'''
  <section class="tab" id="github">
    <div class="container">
      <div class="section-num">$ stat /students/quality</div>
      <h2>这个专业的人, GitHub 上都干啥?</h2>
      <p style="color:var(--muted)">{gm.get("desc", "")}</p>
      <div class="github-grid">
        <div class="gh-stat"><div class="gh-pct">{gm.get("p1000_star", "12%")}</div><div class="gh-label">有 1000+ star 项目的同学比例</div></div>
        <div class="gh-stat"><div class="gh-pct">{gm.get("acm_award", "8%")}</div><div class="gh-label">ACM 区域赛获奖比例</div></div>
        <div class="gh-stat"><div class="gh-pct">{gm.get("oss_contrib", "30%")}</div><div class="gh-label">为知名开源项目贡献过</div></div>
      </div>
    </div>
  </section>'''

    css = build_style_css(style)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}专业介绍 2026 高考 | Major Explorer</title>
<meta name="description" content="{tok['tagline']}。{summary[:80]}">
<style>
{css}
.timeline {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-top: 24px;
}}
.tl-item {{
  padding: 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--primary);
  border-radius: 0 12px 12px 0;
}}
.tl-year {{ font-family: var(--font-heading); font-size: 1.5rem; font-weight: 700; color: var(--primary); }}
.tl-stage {{ font-size: 1rem; margin: 4px 0 8px; font-weight: 500; }}
.tl-income {{ font-size: 0.8125rem; color: var(--muted); }}
.github-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-top: 24px;
}}
.gh-stat {{
  padding: 32px 24px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  text-align: center;
}}
.gh-pct {{ font-family: var(--font-heading); font-size: 2.5rem; font-weight: 700; color: var(--primary); }}
.gh-label {{ font-size: 0.875rem; color: var(--muted); margin-top: 8px; }}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="hero-decor">{decor}</div>
    <h1>{title}</h1>
    <p class="hero-tagline">{tok['tagline']} — {summary[:100]}</p>
    <div class="hero-tags">
      {''.join(f'<span class="tag primary">{t}</span>' for t in tags[:3])}
      {''.join(f'<span class="tag">{t}</span>' for t in tags[3:])}
    </div>
    <div class="hero-stats">
      <div class="stat">
        <div class="stat-label">学科门类</div>
        <div class="stat-value">{category}</div>
      </div>
      <div class="stat">
        <div class="stat-label">学制 / 学位</div>
        <div class="stat-value">{duration} 年 · {degree}</div>
      </div>
      <div class="stat">
        <div class="stat-label">难度自评</div>
        <div class="stat-value">{difficulty}</div>
      </div>
      <div class="stat">
        <div class="stat-label">数据更新</div>
        <div class="stat-value">{updated_at}</div>
      </div>
    </div>
  </div>
</header>

<section class="tab" id="overview">
  <div class="container">
    <div class="section-num">01 / 10</div>
    <h2>速览</h2>
    <p>{summary}</p>
    {f'<h3>这个专业学什么?</h3><p>{data.get("what_you_learn", "")}</p>' if data.get("what_you_learn") else ''}
    {f'<h3>什么人适合?</h3><p>{data.get("who_fits", "")}</p>' if data.get("who_fits") else ''}
    {f'<h3>避坑指南</h3><p>{data.get("pitfalls", "")}</p>' if data.get("pitfalls") else ''}
  </div>
</section>

<section class="tab" id="curriculum">
  <div class="container">
    <div class="section-num">02 / 10</div>
    <h2>主要课程</h2>
    <p style="color:var(--muted); margin-bottom: 24px;">{data.get("curriculum_note", "以清华大学培养方案为参考, 实际各校有差异。")}</p>
    <div class="curriculum-grid">
{curriculum_html}
    </div>
  </div>
</section>

<section class="tab" id="schools">
  <div class="container">
    <div class="section-num">03 / 10</div>
    <h2>院校分布</h2>
    <p style="color:var(--muted); margin-bottom: 8px;">教育部学科评估第四轮 (2017, 第五轮 2022 部分公开)。A+ = 前 2% 或前 2 所, A = 前 2-10%, A- = 前 10-20%。</p>
    <div class="bento">
{schools_html}
    </div>
  </div>
</section>

<section class="tab" id="companies">
  <div class="container">
    <div class="section-num">04 / 10</div>
    <h2>头部公司</h2>
    <p style="color:var(--muted); margin-bottom: 8px;">S = 顶级 (顶级薪资+大量校招), A = 知名 (稳定校招), B = 大量招 (中等门槛)。校招薪资为 2024 秋招主流 offer 中位数。</p>
    <div class="company-grid">
{companies_html}
    </div>
  </div>
</section>

{timeline_html}

{company_section_extra}

<section class="tab" id="salary">
  <div class="container">
    <div class="section-num">{('06' if timeline_html or company_section_extra else '05')} / 10</div>
    <h2>薪资分布</h2>
    <p style="color:var(--muted); margin-bottom: 8px;">数据源: 麦可思 2024 中国大学生就业报告 + 招聘平台 2024 校招采样 (N=120+ offer)。单位: 万/年。P25 = 25% 的人低于此, P50 = 中位数, P75 = 75% 的人低于此。</p>
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
  <div class="container">
    <div class="section-num">{('07' if timeline_html or company_section_extra else '06')} / 10</div>
    <h2>就业方向</h2>
    <p style="color:var(--muted); margin-bottom: 8px;">毕业 1-3 年的去向分布, 占比合计 100%。</p>
    <div class="direction-list">
{direction_html}
    </div>
  </div>
</section>

<section class="tab" id="deep-study">
  <div class="container">
    <div class="section-num">{('08' if timeline_html or company_section_extra else '07')} / 10</div>
    <h2>深造路径</h2>
    <div class="path-grid">
{path_html}
    </div>
  </div>
</section>

<section class="tab" id="quotes">
  <div class="container">
    <div class="section-num">{('09' if timeline_html or company_section_extra else '08')} / 10</div>
    <h2>学长学姐说</h2>
    <p style="color:var(--muted); margin-bottom: 8px;">真实在校生/毕业生观点, 有夸有劝退, 自己判断。</p>
    <div class="quotes">
{quotes_html}
    </div>
  </div>
</section>

<section class="tab" id="xuanke">
  <div class="container">
    <div class="section-num">{('10' if timeline_html or company_section_extra else '09')} / 10</div>
    <h2>选科要求 (新高考 3+1+2)</h2>
    <p style="color:var(--muted); margin-bottom: 8px;">基于 2024 年全国开设此专业院校的招生选科要求统计。覆盖率越高, 你的选科组合能报的院校越多。</p>
    <div class="xuanke-list">
{xuanke_html}
    </div>
  </div>
</section>

<section class="tab" id="cta">
  <div class="container">
    <div class="section-num">{('11' if timeline_html or company_section_extra else '10')} / 10</div>
    <h2>关联志愿</h2>
    <div class="cta">
      <h3>基于你的位次, 推荐这些校 + 组</h3>
      <p>上面院校列表已内置, 输入位次和分数, 立刻出志愿表 (冲 / 稳 / 保 比例 25/50/25)。</p>
      <form class="cta-form" onsubmit="event.preventDefault(); alert('功能开发中, 请关注后续更新');">
        <input type="number" class="cta-input" placeholder="位次 (如 1234)" required>
        <input type="number" class="cta-input" placeholder="分数 (如 620)" required>
        <button type="submit" class="cta-button">推荐志愿 →</button>
      </form>
      <p style="font-size:0.8125rem; margin-top:16px; opacity:0.8;">⚠️ 本页所有数据截至 {updated_at}, 仅供高考志愿参考, 不构成最终决策建议。</p>
    </div>
  </div>
</section>

<footer>
  <div class="container">
    <div>{tok['label']} · Major Explorer · 2026 高考</div>
    <div class="data-source">数据源: {data_source}</div>
  </div>
</footer>
</body>
</html>"""


def generate_dashboard(data: dict, style: str, output_path: str | None = None) -> str:
    """主入口: 渲染 dashboard HTML. style 必选, output_path 选填 (写文件)."""
    if style not in STYLE_TOKENS:
        raise ValueError(f"Unknown style: {style}. Choose from {list(STYLE_TOKENS.keys())}")
    html = render_html(data, style)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(html, encoding="utf-8")
    return html


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Major Explorer dashboard")
    parser.add_argument("--data", required=True, help="Path to JSON data file")
    parser.add_argument("--style", required=True, choices=list(STYLE_TOKENS.keys()))
    parser.add_argument("--output", default=None, help="Output HTML path")
    args = parser.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    out = generate_dashboard(data, args.style, args.output)
    if args.output:
        print(f"✅ Generated: {args.output} ({len(out):,} bytes)")
    else:
        print(out)
