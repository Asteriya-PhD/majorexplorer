"""
v4_styles/themes/administration.py — administration 主题 CSS + hero 渲染
"""

ADMINISTRATION_CSS = """
/* ── 招 #5: 国发文件红头 + 公文纸主体 ── */
.hero { padding: 0; background: transparent; position: relative; z-index: 2; overflow: hidden; }
.gov-red-header { background: #1E3A5F; border-bottom: 3px double #D4AF37; padding: 14px 40px; display: flex; justify-content: space-between; align-items: center; font-family: 'IBM Plex Mono', monospace; font-size: 0.6875rem; color: #FAFAF6; letter-spacing: 0.15em; text-transform: uppercase; position: relative; z-index: 2; }
.gov-red-header strong { font-family: 'IBM Plex Serif', serif; font-size: 0.875rem; font-weight: 700; color: #FAFAF6; letter-spacing: 0.2em; }
.gov-red-header .doc-num { color: #D4AF37; }
.gov-redline { height: 4px; background: linear-gradient(90deg, #C0392B 0%, #C0392B 40%, #D4AF37 40%, #D4AF37 60%, #C0392B 60%, #C0392B 100%); }
.gov-paper { position: relative; padding: 56px 64px 64px; background: #FAFAF6; max-width: 1080px; margin: 0 auto; box-shadow: 0 4px 24px rgba(30, 58, 95, 0.08); }
.gov-paper::before { content: ""; position: absolute; inset: 0; pointer-events: none; background-image: repeating-linear-gradient(0deg, rgba(26, 36, 56, 0.02) 0px, transparent 1px, transparent 3px); }
.gov-paper::after { content: ""; position: absolute; top: 16px; right: 16px; bottom: 16px; left: 16px; border: 1px solid rgba(30, 58, 95, 0.1); pointer-events: none; }
.gov-doc-title { font-family: 'Noto Serif SC', 'IBM Plex Serif', serif; font-size: clamp(1.875rem, 3.5vw, 2.5rem); font-weight: 900; color: #C0392B; text-align: center; letter-spacing: 0.4em; margin: 8px 0 8px; position: relative; }
.gov-doc-no { text-align: center; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #1E3A5F; letter-spacing: 0.2em; margin-bottom: 32px; position: relative; }
.gov-doc-no::before, .gov-doc-no::after { content: "〔"; color: #1E3A5F; }
.gov-doc-no::after { content: "〕"; }
.gov-doc-line { width: 60%; height: 1px; background: linear-gradient(90deg, transparent, #C0392B, transparent); margin: 12px auto; opacity: 0.6; position: relative; }
.gov-stamp { position: absolute; top: 32px; right: 32px; width: 96px; height: 96px; border: 2px solid #C0392B; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: 'Noto Serif SC', serif; font-size: 0.625rem; font-weight: 700; color: #C0392B; text-align: center; line-height: 1.3; transform: rotate(-8deg); opacity: 0.85; z-index: 3; }
.gov-stamp::before { content: "★"; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 1.25rem; color: #C0392B; opacity: 0.3; }
.gov-stamp-text { position: relative; z-index: 1; }
.gov-seal-strip { position: absolute; top: 50%; right: -8px; transform: translateY(-50%); background: #C0392B; color: #FAFAF6; padding: 6px 10px; font-family: 'Noto Serif SC', serif; font-size: 0.625rem; font-weight: 700; letter-spacing: 0.2em; writing-mode: vertical-rl; z-index: 3; }
.gov-h1 { font-family: 'Noto Serif SC', 'IBM Plex Serif', serif; font-size: clamp(2.25rem, 5vw, 3.5rem); font-weight: 900; color: #1A2438; text-align: center; line-height: 1.2; margin: 24px 0 16px; letter-spacing: 0.06em; position: relative; }
.gov-tagline { font-family: 'IBM Plex Serif', 'Noto Serif SC', serif; font-size: 1.0625rem; color: #1A2438; text-align: center; margin: 0 auto 32px; max-width: 720px; line-height: 1.7; position: relative; }
.gov-tagline::before { content: "— "; color: #C0392B; }
.gov-tagline::after { content: " —"; color: #C0392B; }
.gov-tags { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-bottom: 40px; position: relative; }
.gov-tag { padding: 6px 14px; background: transparent; border: 1px solid #1E3A5F; font-family: 'Noto Serif SC', serif; font-size: 0.875rem; color: #1E3A5F; letter-spacing: 0.05em; }
.gov-tag.primary { background: #1E3A5F; color: #FAFAF6; font-weight: 700; }
.gov-stats { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #1E3A5F; border-bottom: 1px solid #1E3A5F; max-width: 880px; margin: 0 auto; position: relative; }
.gov-stats .stat { padding: 20px 16px; border-right: 1px solid #C5C5B5; background: rgba(30, 58, 95, 0.02); position: relative; }
.gov-stats .stat:last-child { border-right: none; }
.gov-stats .stat::before { content: "〔" attr(data-num) "〕"; position: absolute; top: 6px; right: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 0.5625rem; color: #C0392B; }
.gov-stats .stat-label { font-family: 'IBM Plex Serif', serif; font-size: 0.6875rem; color: #5A6A7A; letter-spacing: 0.15em; text-transform: uppercase; font-weight: 500; }
.gov-stats .stat-value { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 700; color: #1A2438; margin-top: 4px; }
.gov-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 40px; padding-top: 16px; border-top: 1px dashed #C5C5B5; font-family: 'IBM Plex Mono', monospace; font-size: 0.6875rem; color: #5A6A7A; letter-spacing: 0.1em; }
section.tab { border-top: 1px solid #C5C5B5; border-bottom: 1px solid #C5C5B5; }
section.tab:first-of-type { border-top: none; }
section.tab:last-of-type { border-bottom: none; }
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.bento-item { padding: 28px 24px 24px; background: #FFFFFF; border: 1px solid #C5C5B5; position: relative; transition: border-color 250ms, transform 250ms; }
.bento-item::before { content: "■"; position: absolute; top: 20px; right: 20px; color: #1E3A5F; font-size: 0.75rem; opacity: 0.5; }
.bento-item:nth-child(3) { position: relative; }
.bento-item:nth-child(3)::before, .bento-item:nth-child(6)::before, .bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: #1E3A5F; z-index: 1; pointer-events: none; }
.bento-item:hover { border-color: #1E3A5F; transform: translateY(-2px); }
.bento-monogram { position: absolute; top: 20px; right: 50px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: #1E3A5F; color: #FAFAF6; font-family: 'IBM Plex Serif', serif; font-size: 1.0625rem; font-weight: 700; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #1E3A5F; border: 1px solid #1E3A5F; font-family: 'IBM Plex Serif', serif; font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.1em; margin-bottom: 12px; }
.bento-name { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 700; margin-bottom: 4px; color: #1A2438; padding-right: 80px; text-wrap: balance; line-height: 1.35; }
.bento-tag { font-family: 'IBM Plex Serif', serif; font-size: 0.8125rem; color: #5A6A7A; line-height: 1.5; }
.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 24px 22px 20px; background: #FFFFFF; border: 1px solid #C5C5B5; position: relative; transition: border-color 250ms, transform 250ms; }
.company:hover { border-color: #1E3A5F; transform: translateY(-2px); }
.company-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.company-monogram { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: #1E3A5F; color: #FAFAF6; font-family: 'IBM Plex Serif', serif; font-size: 1rem; font-weight: 700; }
.company-tier { padding: 2px 8px; border: 1px solid #1E3A5F; color: #1E3A5F; font-family: 'IBM Plex Serif', serif; font-size: 0.625rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }
.tier-S { background: #1E3A5F; color: #FAFAF6; }
.tier-A { background: transparent; }
.tier-B { background: transparent; color: #5A6A7A; border-color: #C5C5B5; }
.company-name { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 700; margin-bottom: 8px; color: #1A2438; }
.company-meta { font-family: 'IBM Plex Serif', serif; font-size: 0.8125rem; color: #5A6A7A; line-height: 1.5; margin-bottom: 8px; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 8px; border-top: 1px solid #E5E5DC; }
.sparkline-bar { flex: 1; background: #C5C5B5; min-height: 2px; transition: background 250ms; }
.company:hover .sparkline-bar { background: #1E3A5F; opacity: 0.8; }
.sparkline-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.625rem; color: #5A6A7A; letter-spacing: 0.1em; margin-top: 4px; }
.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: #FFFFFF; border: 1px solid #C5C5B5; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 18px 24px; text-align: left; border-bottom: 1px solid #E5E5DC; font-size: 0.875rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: rgba(30, 58, 95, 0.04); font-family: 'IBM Plex Serif', serif; font-weight: 700; font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.12em; color: #1E3A5F; }
.salary-stage { font-family: 'Noto Serif SC', serif; font-weight: 700; color: #1A2438; }
.salary-bar { display: inline-block; width: 80px; height: 6px; background: #E5E5DC; margin-left: 8px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #1E3A5F; }
.yoy { display: inline-block; font-family: 'IBM Plex Serif', serif; font-size: 0.75rem; font-weight: 600; margin-left: 12px; padding: 2px 6px; }
.yoy.up   { color: #1E3A5F; }
.yoy.down { color: #C0392B; }
.yoy.flat { color: #5A6A7A; }
.approx { font-family: 'IBM Plex Mono', monospace; color: #5A6A7A; margin-right: 4px; }
.direction-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 160px 1fr 60px; align-items: center; gap: 20px; padding: 14px 0; border-bottom: 1px solid #E5E5DC; }
.direction:last-child { border-bottom: none; }
.direction-name { font-family: 'Noto Serif SC', serif; font-weight: 600; font-size: 0.9375rem; color: #1A2438; }
.direction-bar { height: 8px; background: #E5E5DC; overflow: hidden; }
.direction-bar-fill { height: 100%; background: #1E3A5F; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); }
.direction-pct { font-family: 'IBM Plex Mono', monospace; font-weight: 700; text-align: right; font-size: 0.9375rem; color: #1A2438; }
.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: #FFFFFF; border: 1px solid #C5C5B5; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #1E3A5F; transform: translateY(-2px); }
.path-pct { font-family: 'Noto Serif SC', serif; font-size: 2.5rem; font-weight: 700; color: #1E3A5F; margin-bottom: 4px; letter-spacing: -0.02em; line-height: 1; }
.path-name { font-family: 'Noto Serif SC', serif; color: #5A6A7A; font-size: 0.8125rem; margin-top: 8px; }
.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 28px 32px 24px; background: #FFFFFF; border: 1px solid #C5C5B5; border-left: 3px solid #1E3A5F; margin-bottom: 16px; transition: border-left-width 250ms, transform 250ms; }
.quote:hover { border-left-width: 8px; transform: translateX(4px); }
.quote-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.quote-avatar { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: #1E3A5F; color: #FAFAF6; font-family: 'IBM Plex Serif', serif; font-size: 1rem; font-weight: 700; }
.quote-byline strong { display: block; font-family: 'Noto Serif SC', serif; font-weight: 700; color: #1A2438; font-size: 0.875rem; }
.quote-byline .quote-source { font-family: 'IBM Plex Serif', serif; color: #5A6A7A; font-size: 0.75rem; }
.quote-text { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; line-height: 1.7; color: #1A2438; }
.quote-text::before { content: "「"; color: #C0392B; }
.quote-text::after { content: "」"; color: #C0392B; }
.xuanke-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 200px 1fr 80px; align-items: center; gap: 20px; padding: 14px 0; border-bottom: 1px solid #E5E5DC; }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-family: 'Noto Serif SC', serif; font-weight: 600; font-size: 0.9375rem; color: #1A2438; }
.xuanke-bar { height: 8px; background: #E5E5DC; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #1E3A5F; }
.xuanke-pct { font-family: 'IBM Plex Mono', monospace; font-weight: 700; text-align: right; font-size: 0.9375rem; color: #1E3A5F; }
.curriculum-lede { color: #5A6A7A; font-size: 0.9375rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.curriculum-block { padding: 28px 24px; background: #FFFFFF; border: 1px solid #C5C5B5; transition: border-color 250ms, transform 250ms; }
.curriculum-block:hover { border-color: #1E3A5F; transform: translateY(-2px); }
.curriculum-title { font-family: 'Noto Serif SC', serif; font-size: 0.6875rem; color: #1E3A5F; text-transform: uppercase; letter-spacing: 0.15em; font-weight: 700; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #C5C5B5; }
.course { padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; font-size: 0.9375rem; }
.course-name { color: #1A2438; font-weight: 500; font-family: 'Noto Serif SC', serif; }
.course-credit { color: #5A6A7A; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; margin-left: 8px; }
.cta-block { margin-top: 32px; padding: 64px 48px; background: #FFFFFF; border: 1px solid #1E3A5F; text-align: center; position: relative; }
.cta-block::before { content: "〔 关联志愿 · 推荐填报 〕"; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #FAFAF6; padding: 0 16px; color: #1E3A5F; font-size: 0.75rem; letter-spacing: 0.2em; font-family: 'IBM Plex Serif', serif; }
.cta-block h3 { font-family: 'Noto Serif SC', serif; font-size: 1.75rem; margin-bottom: 12px; color: #1A2438; position: relative; z-index: 1; }
.cta-block p { color: #5A6A7A; margin: 0 auto 28px; max-width: 560px; position: relative; z-index: 1; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; position: relative; z-index: 1; }
.cta-input { padding: 14px 18px; background: #FAFAF6; border: 1px solid #C5C5B5; color: #1A2438; font-family: 'Noto Serif SC', serif; font-size: 1rem; width: 180px; outline: none; }
.cta-input:focus { border-color: #1E3A5F; }
.cta-button { padding: 14px 36px; background: #C0392B; color: #FAFAF6; font-family: 'Noto Serif SC', serif; font-size: 0.9375rem; font-weight: 700; letter-spacing: 0.1em; }
.cta-note { font-family: 'IBM Plex Serif', serif; font-size: 0.75rem; color: #5A6A7A; margin-top: 16px; position: relative; z-index: 1; }
.watermark { color: #1E3A5F; opacity: 0.04; }
.section-num { color: #C0392B; font-family: 'IBM Plex Serif', serif; }
section.tab h2 { font-family: 'Noto Serif SC', serif; color: #1A2438; }
section.tab p { color: #1A2438; }
section.tab p.lede { color: #5A6A7A; }
section.tab h3 { color: #1A2438; font-family: 'Noto Serif SC', serif; }
footer { background: #FAFAF6; border-top: 1px solid #C5C5B5; }
footer .label { color: #1E3A5F; font-family: 'IBM Plex Serif', serif; }
footer .data-source { color: #5A6A7A; }
.drop-cap::first-letter { font-family: 'Noto Serif SC', serif; font-size: 4em; font-weight: 900; line-height: 0.9; float: left; margin: 0.05em 0.12em 0 0; color: #C0392B; }
"""

def render_hero_administration(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    return f'''
<header class="hero">
  <div class="gov-red-header">
    <span class="doc-num">MAJOR · 〔2026〕第 {tags[0] if tags else "001"} 号</span>
    <strong>Major Explorer 编辑部</strong>
    <span class="doc-num">专题资料 · 编辑部内阅</span>
  </div>
  <div class="gov-redline"></div>
  <div class="container" style="padding: 0;">
    <div class="gov-paper">
      <div class="gov-stamp">
        <span class="gov-stamp-text">升学<br/>研究组</span>
      </div>
      <div class="gov-seal-strip">归档 · 内部资料</div>
      <div class="gov-doc-title">专业介绍</div>
      <div class="gov-doc-no">专题号 ME〔2026〕第 {tags[0] if tags else "001"} 号</div>
      <div class="gov-doc-line"></div>
      <h1 class="gov-h1">{title}</h1>
      <p class="gov-tagline">{summary[:120]}</p>
      <div class="gov-tags">
        {"".join(f'<span class="gov-tag primary">{t}</span>' for t in tags[:3])}
        {"".join(f'<span class="gov-tag">{t}</span>' for t in tags[3:])}
      </div>
      <div class="gov-stats">
        <div class="stat" data-num="01"><div class="stat-label">学 科 门 类</div><div class="stat-value">{category}</div></div>
        <div class="stat" data-num="02"><div class="stat-label">学 制 · 学 位</div><div class="stat-value">{duration}Y · {degree}</div></div>
        <div class="stat" data-num="03"><div class="stat-label">难 度 评 定</div><div class="stat-value">{difficulty}</div></div>
        <div class="stat" data-num="04"><div class="stat-label">编 纂 修 订</div><div class="stat-value">{updated_at}</div></div>
      </div>
      <div class="gov-foot">
        <span>编纂: Major Explorer 编辑部 · 升学研究组</span>
        <span>成文日期: {updated_at}</span>
        <span>份号: 0026-ME-{data.get("slug", "doc")[:6].upper()}</span>
      </div>
    </div>
  </div>
</header>'''
