"""
render_og_cards.py v3.1 — 1080×1440 (3:4) 竖屏分享卡, 10 个热门专业 (5→10 扩充).

变化 (v3 → v3.1):
- 10 个热门: 临床医学/金融学/法学/公安学类/应用心理学 (原 5)
            + 计算机科学/工业设计/数字媒体艺术/工商管理/化学 (新增 5)
- 内容密度: lede + 5 基础课 chip + 3 方向 chip + 4 技能 chip + 1 亮点引文
- 每主题 hero 招牌元素直接搬:
  - medicine: 右上 vital sign cell (HR 72bpm 异常黄高亮 + ECG SVG 装饰)
  - finance: 顶部 letterhead (── Major Explorer ──) + 标题 drop cap + 烫金分隔
  - law: 右上 红圆 已立案 章 + 顶部 docket court header
  - gongan: 中央 P 警徽 (六边形 + Cinzel P) + 顶底烫金线
  - education: 暖橙底 + Playfair italic + 漂浮 ❀ 装饰
  - cs: 终端面板 + ASCII art + 打字机光标
  - eng: 工程图纸标题栏 (DWG-XXX) + datasheet spec card
  - arts: 美术馆 logo + 画框 + 朱红印章 + 金属铭牌
  - business: 椭圆董事局 + 玫瑰金 + 胡桃木
  - sci: 学术期刊刊头 (VOL.50 NO.03) + 双线分割 + 衬线 italic

用法:
    python3 scripts/render_og_cards.py                                # 10 热门
    python3 scripts/render_og_cards.py finance                        # 单个
    python3 scripts/render_og_cards.py --all                          # 全部 13
"""
from __future__ import annotations
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import json

ROOT = Path(__file__).resolve().parent.parent
CURATED = ROOT / "skills/gaokao-major-explorer/data/curated"
OUT = ROOT / ".tmp-hero/og"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / "skills/gaokao-major-explorer/scripts"))
from generate_dashboard import STYLE_TOKENS  # noqa: E402

# 10 热门 (配色全不撞) — 5→10 扩充
DEFAULT_REPS = {
    "medicine":  "clinical-medicine",   # 浅蓝 + 白 + ECG
    "finance":   "finance",              # 暖米 + 烫金 + Bodoni
    "law":       "law",                  # 米黄 + 棕红 + letterhead
    "gongan":    "public-security-demo", # 深蓝 + 烫金
    "education": "applied-psychology",   # 暖橙 + Playfair (心理学是 education 主题)
    "cs":        "computer-science",     # 终端深绿 + CRT 扫描线 + ASCII art
    "eng":       "industrial-design",    # 工程蓝 + 图纸 + datasheet
    "arts":      "digital-media-arts",   # 美术馆白盒 + 画框 + 朱红印章
    "business":  "business-administration-demo",  # 椭圆董事局 + 玫瑰金 + 胡桃木
    "sci":       "chemistry",            # 学术期刊 + 衬线 italic + 双线分割
}

ALL_REPS = {
    "cs":             "computer-science",
    "eng":            "industrial-design",
    "finance":        "finance",
    "medicine":       "clinical-medicine",
    "law":            "law",
    "education":      "applied-psychology",
    "sci":            "chemistry",
    "humanities":     "philosophy",
    "agri":           "horticulture",
    "arts":           "digital-media-arts",
    "administration": "library-science",
    "gongan":         "public-security-demo",
    "business":       "business-administration-demo",
}

FONT_IMPORT = """
@import url('https://fonts.loli.net/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&family=Cinzel:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&family=Playfair+Display:ital,wght@0,500;0,600;0,700;0,800;0,900;1,400;1,500&family=Inter:wght@400;500;600;700&family=Bodoni+Moda:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=EB+Garamond:ital,wght@0,500;0,600;0,700;1,400&family=Ma+Shan+Zheng&family=Long+Cang&family=Caveat:wght@400;500;600&display=swap');
"""

BASE_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1440px; overflow: hidden; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }

.card {
  width: 1080px; height: 1440px;
  display: flex; flex-direction: column;
  padding: 56px 56px; position: relative;
  background: var(--bg); color: var(--fg);
  overflow: hidden;
}

.brand-bar {
  display: flex; justify-content: space-between; align-items: center;
  font-family: var(--font-num); font-size: 22px; letter-spacing: 0.22em;
  text-transform: uppercase; color: var(--muted); opacity: 0.9;
  position: relative; z-index: 4;
}
.brand-bar .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--accent); margin-right: 13px; display: inline-block; vertical-align: middle; }

.category {
  margin-top: 24px;
  font-family: var(--font-num); font-size: 26px; letter-spacing: 0.16em;
  color: var(--accent); text-transform: uppercase; opacity: 0.95;
  position: relative; z-index: 4;
}
.title {
  margin-top: 6px;
  font-family: var(--font-heading);
  font-size: var(--title-size, 180px); line-height: 0.98; font-weight: 700;
  letter-spacing: -0.02em; color: var(--fg);
  position: relative; z-index: 4;
}
.subtitle-en {
  margin-top: 12px;
  font-family: var(--font-num);
  font-size: 32px; letter-spacing: 0.06em;
  color: var(--muted); font-style: italic;
  position: relative; z-index: 4;
}
.lede {
  margin-top: 14px;
  font-family: var(--font-body); font-size: 34px; line-height: 1.5;
  color: var(--fg); opacity: 0.95;
  position: relative; z-index: 4;
}
.lede::first-letter {
  font-family: var(--font-heading); font-size: 1.9em;
  font-weight: 700; float: left;
  margin: 0.04em 0.16em -0.1em 0;
  line-height: 0.9; color: var(--accent);
}

.section-divider {
  margin-top: 0px;
  display: flex; align-items: center; justify-content: center; gap: 20px;
  font-family: var(--font-num); font-size: 20px; letter-spacing: 0.24em;
  text-transform: uppercase; color: var(--muted); opacity: 0.9;
  position: relative; z-index: 4;
}
.section-divider .rule { flex: 1; max-width: 260px; height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent); opacity: 0.75; }
.section-divider .orn { color: var(--accent); font-size: 30px; opacity: 0.92; font-weight: 700; }

.chips-section {
  margin-top: 10px;
  position: relative; z-index: 4;
}
.chips-section + .chips-section { margin-top: 8px; }
.chips-label {
  font-family: var(--font-num); font-size: 18px;
  letter-spacing: 0.2em; text-transform: uppercase;
  color: var(--muted); opacity: 0.82; margin-bottom: 8px;
}
.chips {
  display: flex; flex-wrap: wrap; gap: 9px;
}
.chip {
  font-family: var(--font-body); font-size: 26px;
  padding: 9px 18px; border-radius: 3px;
  border: 1.5px solid var(--border); color: var(--fg);
  background: var(--surface);
  letter-spacing: 0.01em;
}

.quote {
  margin-top: 14px;
  font-family: var(--font-heading); font-style: italic;
  font-size: 28px; line-height: 1.45;
  color: var(--fg); opacity: 0.92;
  padding: 8px 0 8px 20px; border-left: 4px solid var(--accent);
  position: relative; z-index: 4;
}

.stats {
  margin-top: auto;
  display: grid; grid-template-columns: 1fr 1fr 1fr;
  gap: 0; border-top: 2px solid var(--border);
  padding-top: 18px; position: relative; z-index: 4;
}
.stat { padding: 0 22px; border-right: 1px solid var(--border); min-width: 0; }
.stat:first-child { padding-left: 0; }
.stat:last-child { border-right: none; padding-right: 0; }
.stat-label {
  font-family: var(--font-num); font-size: 19px;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--muted); opacity: 0.8;
}
.stat-value {
  margin-top: 6px;
  font-family: var(--font-heading); font-size: 38px;
  font-weight: 700; color: var(--fg); line-height: 1.15;
  letter-spacing: -0.005em;
}
.stat-value .small {
  display: block; font-size: 22px; font-weight: 500;
  color: var(--muted); margin-top: 4px; letter-spacing: 0.04em;
  line-height: 1.15;
}

.tags {
  margin-top: 14px;
  display: flex; flex-wrap: wrap; gap: 9px;
  position: relative; z-index: 4;
}
.tag {
  font-family: var(--font-num); font-size: 22px;
  padding: 8px 18px; border-radius: 3px;
  border: 1.5px solid var(--border); color: var(--fg);
  background: var(--surface);
  letter-spacing: 0.04em;
}
.tag.primary {
  background: var(--accent); color: var(--monogram-fg);
  border-color: var(--accent); font-weight: 600;
}

.footer {
  margin-top: 12px;
  display: flex; justify-content: space-between; align-items: baseline;
  font-family: var(--font-num); font-size: 18px;
  color: var(--muted); letter-spacing: 0.16em;
  text-transform: uppercase; opacity: 0.6;
  padding-top: 12px; border-top: 1px dashed var(--border);
  position: relative; z-index: 4;
}
"""

# 主题专属 CSS — 包含背景渐变 + 招牌元素 (letterhead/docket/vital/警徽/...)
THEME_CSS = {
    "medicine": """
.card { background: linear-gradient(180deg, #FFFFFF 0%, #F0F9FF 100%); }
.card::before {
  content: ""; position: absolute; inset: 32px; pointer-events: none;
  border: 1px solid #BAE6FD; border-radius: 8px;
}
/* ECG 作为流式分隔线 — 放在 subtitle 与 lede 之间, 不会盖字 */
.ecg-line { display: block; width: 100%; height: 26px; margin: 8px 0 4px; opacity: 0.55; }
.ecg-line path { stroke: #0C4A6E; stroke-width: 1.4; fill: none; }

/* 右上 vital 卡 */
.vital-card {
  position: absolute; right: 88px; top: 170px;
  width: 230px; padding: 16px 18px; border-radius: 8px;
  background: #FFFBEB; border-left: 6px solid #D97706;
  box-shadow: 0 6px 18px rgba(217,119,6,0.16);
  z-index: 3;
}
.lede {
  margin-top: 24px !important;
  margin-bottom: 28px !important;
}
.vital-label { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #92400E; letter-spacing: 0.12em; text-transform: uppercase; }
.vital-num { font-family: 'Inter', sans-serif; font-size: 56px; font-weight: 800; color: #1E293B; line-height: 1; letter-spacing: -0.02em; margin-top: 6px; }
.vital-unit { font-size: 18px; color: #475569; font-weight: 500; margin-left: 3px; }
.vital-ref { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #92400E; margin-top: 4px; opacity: 0.7; }
.vital-flag { font-size: 11px; color: #D97706; font-weight: 700; margin-top: 6px; letter-spacing: 0.15em; }
""",
    "finance": """
.card { background: linear-gradient(180deg, #FAFAF6 0%, #F2EDE0 100%); padding-top: 60px; }
/* 顶部 letterhead — 居中 logo + 双侧烫金分隔线 */
.letterhead {
  display: flex; align-items: center; justify-content: center; gap: 18px;
  padding-bottom: 14px; margin-bottom: 18px;
  border-bottom: 1px solid #C9A85A; position: relative; z-index: 4;
}
.letterhead-line { flex: 1; height: 1px;
  background: linear-gradient(90deg, transparent, #A16207, transparent); opacity: 0.65; }
.letterhead-logo { font-family: 'Bodoni Moda', serif; font-style: italic;
  font-size: 30px; font-weight: 600; color: #1C1917; letter-spacing: 0.06em; }
.letterhead-logo .me { color: #A16207; }
.letterhead-meta {
  display: flex; justify-content: space-between; max-width: 800px; margin: 0 auto 28px;
  font-family: 'Bodoni Moda', serif; font-style: italic; font-size: 18px;
  color: #57534E; letter-spacing: 0.08em; text-transform: uppercase;
  position: relative; z-index: 4;
}
.title { text-align: center; }
.subtitle-en { text-align: center; }
.lede { text-align: center; max-width: 760px; margin-left: auto; margin-right: auto; }
.chips-section { text-align: center; }
.chips { justify-content: center; }
/* drop-cap M·E background watermark */
.me-watermark {
  position: absolute; right: 60px; bottom: 180px; pointer-events: none;
  font-family: 'Bodoni Moda', serif; font-style: italic; font-weight: 700;
  font-size: 280px; color: #B8902A; opacity: 0.06; line-height: 0.85;
  letter-spacing: -0.06em; z-index: 1;
}
""",
    "law": """
.card { background: linear-gradient(180deg, #FAF7E8 0%, #F2EDDC 100%); padding-top: 60px; }
/* 顶部 docket court header */
.docket {
  text-align: center; margin-bottom: 16px;
  font-family: 'EB Garamond', serif;
  font-size: 18px; color: #57534E; letter-spacing: 0.14em;
  text-transform: uppercase; position: relative; z-index: 4;
}
.docket-rule {
  display: flex; align-items: center; justify-content: center; gap: 16px;
  margin: 8px 0; font-size: 15px;
}
.docket-rule .line { flex: 0 0 60px; height: 1px; background: #D97706; opacity: 0.6; }
/* 已立案 红圆章 */
.docket-stamp {
  position: absolute; right: 76px; top: 130px;
  width: 130px; height: 130px; border: 3px double #B91C1C; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #B91C1C; font-family: 'EB Garamond', serif;
  font-size: 16px; font-weight: 700; letter-spacing: 0.12em;
  text-align: center; line-height: 1.25; transform: rotate(11deg); opacity: 0.78;
  text-transform: uppercase; z-index: 3;
  background: rgba(185,28,28,0.04);
}
.docket-meta-strip {
  display: flex; justify-content: space-between; max-width: 880px; margin: 22px auto 0;
  font-family: 'EB Garamond', serif; font-size: 15px;
  color: #57534E; letter-spacing: 0.08em; text-transform: uppercase;
  border-top: 1px solid #D6C9A8; padding-top: 14px; position: relative; z-index: 4;
}
.title { text-align: center; }
.subtitle-en { text-align: center; }
""",
    "gongan": """
.card { background: linear-gradient(180deg, #0A1420 0%, #112338 55%, #0A1420 100%); padding-top: 72px; }
.card::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 6px;
  background: linear-gradient(90deg, transparent, #D4AF37 18%, #D4AF37 82%, transparent);
}
.card::after {
  content: ""; position: absolute; bottom: 0; left: 0; right: 0; height: 6px;
  background: linear-gradient(90deg, transparent, #D4AF37 18%, #D4AF37 82%, transparent);
}
.gold-line { position: absolute; left: 90px; right: 90px; height: 1px;
  background: linear-gradient(90deg, transparent, #D4AF37, transparent); opacity: 0.55; z-index: 2; }
.gold-line.top { top: 100px; }
.gold-line.bot { bottom: 100px; }
/* P 警徽: 移到右上角 (官方印章传统位置), 不挡 brand bar / category / title */
.warrant {
  position: absolute; right: 90px; top: 110px;
  width: 64px; height: 64px; z-index: 4;
}
.title { text-align: center; }
.category { text-align: center; }
.subtitle-en { text-align: center; }
.lede { text-align: center; max-width: 800px; margin-left: auto; margin-right: auto; }
.chips-section { text-align: center; }
.chips { justify-content: center; }
/* 修: 取消 stats 推底,引文 → stats 间不留大空 */
.quote { margin-bottom: 14px; }
.stats { margin-top: 16px !important; }
""",
    "education": """
.card { background: linear-gradient(180deg, #FFF7ED 0%, #FED7AA 100%); padding-top: 72px; }
.card::before {
  content: ""; position: absolute; inset: 32px; pointer-events: none;
  border: 1.5px solid #FDBA74; border-radius: 12px;
}
/* Playfair italic 大字标题 */
.title { font-style: italic; font-weight: 600; color: #9A3412; }
.subtitle-en { color: #C2410C; }
.category { color: #C2410C; }
/* 漂浮 ❀ 装饰 */
.flower { position: absolute; pointer-events: none; opacity: 0.45; color: #EA580C; z-index: 1; }
.flower.f1 { top: 200px; left: 76px; font-size: 36px; transform: rotate(-12deg); }
.flower.f2 { top: 480px; right: 110px; font-size: 28px; transform: rotate(18deg); }
.flower.f3 { bottom: 320px; left: 90px; font-size: 32px; transform: rotate(-25deg); }
/* 引文用 Caveat 手写 */
.quote { font-family: 'Caveat', cursive; font-style: normal; font-size: 30px; line-height: 1.35; color: #7C2D12; border-left-color: #EA580C; }
""",
}

# 每主题 inline DOM 装饰
THEME_DECOR = {
    "medicine": '''
<div class="vital-card">
  <div class="vital-label">HR · 心率</div>
  <div class="vital-num">72<span class="vital-unit">bpm</span></div>
  <div class="vital-ref">参考  60-100</div>
  <div class="vital-flag">● NORMAL</div>
</div>
''',
    "medicine_ecg_inline": '''
<svg class="ecg-line" viewBox="0 0 928 26" preserveAspectRatio="none">
  <path d="M 0 13 L 130 13 L 150 13 L 170 5 L 190 22 L 210 13 L 350 13 L 370 10 L 390 18 L 410 13 L 560 13 L 580 5 L 600 22 L 620 13 L 780 13 L 800 10 L 820 18 L 928 13"/>
</svg>
''',
    "finance": '''
<div class="letterhead">
  <div class="letterhead-line"></div>
  <div class="letterhead-logo"><span class="me">M·E</span> · MAJOR EXPLORER</div>
  <div class="letterhead-line"></div>
</div>
<div class="letterhead-meta">
  <span>VOL. 2026 · NO. III</span>
  <span>EDITORIAL · WEALTH</span>
  <span>EST. 2026</span>
</div>
<div class="me-watermark">M·E</div>
''',
    "law": '''
<div class="docket">
  IN THE COURT OF MAJOR STUDIES
  <div class="docket-rule"><div class="line"></div>专业全貌 · 第一章<div class="line"></div></div>
</div>
<div class="docket-stamp">已<br/>立案<br/>2026</div>
''',
    "gongan": '''
<div class="gold-line top"></div>
<div class="gold-line bot"></div>
<svg class="warrant" viewBox="0 0 100 100">
  <polygon points="50,6 92,28 92,72 50,94 8,72 8,28" fill="#0A1420" stroke="#D4AF37" stroke-width="2.5"/>
  <polygon points="50,16 84,33 84,67 50,84 16,67 16,33" fill="none" stroke="#D4AF37" stroke-width="0.8" opacity="0.6"/>
  <text x="50" y="64" text-anchor="middle" font-family="Cinzel, serif" font-size="36" fill="#D4AF37" font-weight="700">P</text>
</svg>
''',
    "education": '''
<div class="flower f1">❀</div>
<div class="flower f2">✿</div>
<div class="flower f3">❀</div>
''',
}

BRAND_LABELS = {
    "medicine":  "VITALS · CLINICAL",
    "finance":   "VOL. 2026 · NO. III",
    "law":       "DOCKET · 法 2026 LAW 001",
    "gongan":    "DOSSIER · 030600",
    "education": "STUDIO · 心理学类",
}

SUBTITLES = {
    "medicine":  "Clinical Medicine · 100201",
    "finance":   "Private Wealth · Risk & Reward",
    "law":       "Article I · Filed 2026",
    "gongan":    "Public Security & Law Studies · 030600",
    "education": "Applied Psychology · UX · HCI · IO",
}

# 主题专属 section ornament (lede 与 chips 间的分隔点缀)
SECTION_ORNAMENTS = {
    "medicine":  ("Rx · 主要课程", "▶"),
    "finance":   ("Editorial Brief", "§"),
    "law":       ("Exhibit A · 专业全貌", "❦"),
    "gongan":    ("六维档案 · DOSSIER", "❖"),
    "education": ("Lesson · 课程图", "❀"),
}


def title_size(title: str) -> int:
    n = len(title)
    if n <= 3:    return 210
    if n == 4:    return 180
    if n == 5:    return 148
    if n == 6:    return 124
    if n == 7:    return 110
    return 98


def fmt_degree(duration: int, degree: str) -> str:
    return f"{duration} 年<span class='small'>{degree}</span>"


def fmt_difficulty(difficulty: str) -> str:
    """难度 cell — 主行 ★★★★★ + 小行 5 / 5 形式 (凑 2 行)"""
    # ★ count
    full = difficulty.count("★")
    half = difficulty.count("☆")
    return f"{difficulty}<span class='small'>{full} / {full + half} 颗星 · 学术深度</span>"


def fmt_category(category: str) -> str:
    """学科门类 cell — 主行大字号 + 小行门类+专业码"""
    parts = [p.strip() for p in category.split("·")]
    main = parts[0] if parts else category
    sub = " · ".join(parts[1:]) if len(parts) > 1 else ""
    return f"{main}<span class='small'>{sub if sub else '专业门类 · 本科 4 年'}</span>"


def trunc(s: str, n: int) -> str:
    """截断到 n 字符: 句号/逗号处优先, 不加省略号 (避免 '万+...' 这种半截词)"""
    s = s.strip()
    if len(s) <= n:
        return s
    truncated = s[:n].rstrip("，,。.;；:： ")
    return truncated


def render_card(style: str, slug: str) -> str:
    data = json.loads((CURATED / f"{slug}.json").read_text(encoding="utf-8"))
    tok = STYLE_TOKENS[style]
    c = tok["colors"]
    f = tok["fonts"]
    v2 = data.get("overview_v2", {}) or {}
    what = v2.get("what", {}) or {}
    fit = v2.get("fit", {}) or {}
    pitfalls = v2.get("pitfalls", []) or []

    title = data["title"]
    category = data.get("category", "")
    lede = v2.get("lede") or data.get("summary", "")
    lede = trunc(lede, 180)  # 增大上限, 让 lede 完整显示 (不切词)
    duration = data.get("duration_years", 4)
    degree = data.get("degree", "")
    difficulty = data.get("difficulty", "")
    tags = data.get("tags", [])[:5]

    foundations = [trunc(x, 10) for x in (what.get("foundations") or [])[:5]]
    directions = [trunc(d.get("name", ""), 14) for d in (what.get("directions") or [])[:3] if d.get("name")]
    skills = [trunc(s, 18) for s in (what.get("skills") or [])[:4]]

    # quote: 优先 fit.yes[0], fallback pitfalls[0].myth
    quote_text = ""
    if fit.get("yes"):
        quote_text = "✓ " + trunc(fit["yes"][0], 60)
    elif pitfalls:
        m = pitfalls[0]
        quote_text = "✗ 误区: " + trunc(m.get("myth", "") + " — " + m.get("reality", ""), 70)

    en_subtitle = SUBTITLES.get(style, f"Major Explorer · {slug.upper()}")
    brand_right = BRAND_LABELS.get(style, "EDITION 2026")
    decor = THEME_DECOR.get(style, "")
    theme_css = THEME_CSS.get(style, "")

    css_vars = f"""
:root {{
  --bg: {c['bg']};
  --fg: {c['fg']};
  --muted: {c['muted']};
  --primary: {c['primary']};
  --accent: {c['accent']};
  --border: {c.get('border', c['muted'])};
  --surface: {c.get('surface', c['bg'])};
  --monogram-fg: {c.get('monogram_fg', c['bg'])};
  --font-heading: {f['heading']};
  --font-body: {f['body']};
  --font-num: {f['num']};
  --title-size: {title_size(title)}px;
}}
"""

    chips_html = ""
    if foundations:
        chips_html += f'<div class="chips-section"><div class="chips-label">基础课</div><div class="chips">{"".join(f"<span class=chip>{x}</span>" for x in foundations)}</div></div>'
    if directions:
        chips_html += f'<div class="chips-section"><div class="chips-label">主要方向</div><div class="chips">{"".join(f"<span class=chip>{x}</span>" for x in directions)}</div></div>'
    if skills:
        chips_html += f'<div class="chips-section"><div class="chips-label">核心技能</div><div class="chips">{"".join(f"<span class=chip>{x}</span>" for x in skills)}</div></div>'

    quote_html = f'<div class="quote">{quote_text}</div>' if quote_text else ""

    # 主题专属 section ornament (lede 与 chips 间)
    orn_label, orn_glyph = SECTION_ORNAMENTS.get(style, ("主要课程", "·"))
    divider_html = f'<div class="section-divider"><div class="rule"></div><span class="orn">{orn_glyph}</span><span>{orn_label}</span><span class="orn">{orn_glyph}</span><div class="rule"></div></div>'

    # medicine 主题: ECG 流式分隔线 (插在 subtitle 与 lede 之间)
    ecg_inline = THEME_DECOR.get("medicine_ecg_inline", "") if style == "medicine" else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<style>{FONT_IMPORT}{BASE_CSS}{theme_css}{css_vars}</style></head>
<body>
<div class="card">
  {decor}
  <div class="brand-bar">
    <span><span class="dot"></span>MAJOR EXPLORER · 2026 高考专业</span>
    <span>{brand_right}</span>
  </div>
  <div class="category">{category}</div>
  <h1 class="title">{title}</h1>
  <div class="subtitle-en">{en_subtitle}</div>
  {ecg_inline}
  <p class="lede">{lede}</p>
  {divider_html}
  {chips_html}
  {quote_html}
  <div class="stats">
    <div class="stat">
      <div class="stat-label">学制 · 学位</div>
      <div class="stat-value">{fmt_degree(duration, degree)}</div>
    </div>
    <div class="stat">
      <div class="stat-label">难度</div>
      <div class="stat-value">{fmt_difficulty(difficulty)}</div>
    </div>
    <div class="stat">
      <div class="stat-label">学科门类</div>
      <div class="stat-value">{fmt_category(category)}</div>
    </div>
  </div>
  <div class="tags">
    {''.join(f'<span class="tag {"primary" if i==0 else ""}">{t}</span>' for i, t in enumerate(tags))}
  </div>
  <div class="footer">
    <span>major-explorer · {slug}</span>
  </div>
</div>
</body></html>"""


def main():
    args = sys.argv[1:]
    if "--all" in args:
        reps = ALL_REPS
    elif args:
        reps = {s: ALL_REPS.get(s, DEFAULT_REPS.get(s, s)) for s in args}
    else:
        reps = DEFAULT_REPS

    with sync_playwright() as p:
        b = p.chromium.launch()
        for style, slug in reps.items():
            html = render_card(style, slug)
            tmp = OUT / f"_tmp_{style}.html"
            tmp.write_text(html, encoding="utf-8")
            ctx = b.new_context(viewport={"width": 1080, "height": 1440}, device_scale_factor=2)
            pg = ctx.new_page()
            try:
                pg.goto("file://" + str(tmp), wait_until="domcontentloaded", timeout=20000)
                # 主动等字体, 超时不阻塞 (loli.net 偶发慢)
                try:
                    pg.evaluate("() => Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 4500))])")
                except Exception:
                    pass
                pg.wait_for_timeout(800)
            except Exception as e:
                print(f"  ⚠️  goto error {style}: {e}")
            out_png = OUT / f"{style}__{slug}.png"
            # 关键: page.screenshot 自带 waits-for-fonts, 用 element.screenshot 绕过
            try:
                card = pg.locator(".card")
                card.screenshot(path=str(out_png), timeout=10000)
            except Exception as e:
                # 再 retry: 直接全屏截
                pg.screenshot(path=str(out_png), full_page=False, timeout=15000)
            ctx.close()
            tmp.unlink()
            print(f"✅ {style:11s} → {out_png.name}")
        b.close()


if __name__ == "__main__":
    main()
