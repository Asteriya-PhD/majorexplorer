"""
v4_styles/themes/law.py — law 主题 CSS + hero 渲染
"""

LAW_CSS = """
.hero { padding: 80px 0 80px; background: transparent; border-bottom: 2px solid #78350F; text-align: center; position: relative; z-index: 2; }
.hero::before { content: ""; display: block; width: 80px; height: 1px; background: #A16207; margin: 0 auto 32px; opacity: 0.4; }
.hero::after { content: ""; display: block; width: 80px; height: 1px; background: #A16207; margin: 32px auto 0; opacity: 0.4; }
.docket-header { margin-bottom: 24px; }
.docket-court { font-family: 'EB Garamond', serif; font-size: 0.875rem; color: #57534E; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 12px; }
.docket-title-wrap { display: flex; align-items: center; justify-content: center; gap: 24px; margin-bottom: 16px; }
.docket-line { flex: 0 0 80px; height: 1px; background: #D97706; opacity: 0.5; }
.docket-title { font-family: 'EB Garamond', serif; font-size: 0.875rem; color: #57534E; letter-spacing: 0.15em; text-transform: uppercase; font-variant: small-caps; }
.hero h1 { font-family: 'EB Garamond', serif; font-size: clamp(3rem, 6vw, 5rem); font-weight: 500; letter-spacing: -0.02em; line-height: 1.05; color: #1C1917; margin-bottom: 24px; }
.hero-tagline { font-family: 'EB Garamond', serif; font-size: 1.25rem; color: #57534E; margin: 0 auto 32px; max-width: 580px; line-height: 1.7; }
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 40px; justify-content: center; }
.tag { padding: 5px 14px; background: transparent; border: 1px solid #D6D3D1; font-family: 'EB Garamond', serif; font-size: 0.875rem; color: #1C1917; letter-spacing: 0.04em; }
.tag.primary { background: rgba(120, 53, 15, 0.08); border-color: #78350F; color: #78350F; font-variant: small-caps; letter-spacing: 0.15em; font-size: 0.75rem; font-weight: 600; }

.hero-stats { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #D6D3D1; border-bottom: 1px solid #D6D3D1; border-left: 1px solid #D6D3D1; border-right: 1px solid #D6D3D1; max-width: 800px; margin: 0 auto; }
@media (max-width: 768px) { .hero-stats { grid-template-columns: repeat(2, 1fr); } }
.stat { padding: 24px 20px; border-right: 1px solid #E7E5E4; }
.stat:last-child { border-right: none; }
@media (max-width: 768px) { .stat:nth-child(2) { border-right: none; } .stat:nth-child(1), .stat:nth-child(2) { border-bottom: 1px solid #E7E5E4; } }
.stat-label { font-family: 'EB Garamond', serif; font-size: 0.6875rem; color: #57534E; text-transform: uppercase; letter-spacing: 0.18em; font-weight: 500; }
.stat-value { font-family: 'EB Garamond', serif; font-size: 1.5rem; font-weight: 500; color: #1C1917; margin-top: 6px; }

.docket-stamp { position: absolute; top: 32px; right: 32px; width: 90px; height: 90px; border: 2px solid #B91C1C; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #B91C1C; font-family: 'EB Garamond', serif; font-size: 0.625rem; font-weight: 700; letter-spacing: 0.1em; text-align: center; line-height: 1.2; transform: rotate(12deg); opacity: 0.65; text-transform: uppercase; }
.docket-meta { display: flex; justify-content: space-between; max-width: 800px; margin: 24px auto 0; font-family: 'EB Garamond', serif; font-size: 0.75rem; color: #57534E; letter-spacing: 0.08em; text-transform: uppercase; }
@media (max-width: 768px) { .docket-meta { flex-direction: column; gap: 8px; align-items: center; } }

section.tab { border-top: 1px solid #A8A29E; border-bottom: 2px solid #A8A29E; }
section.tab:first-of-type { border-top: none; }
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1px; background: #78716C; border: 1px solid #78716C; margin-top: 32px; position: relative; z-index: 1; }
.bento { position: relative; }
.bento { position: relative; }

.bento-item:nth-child(3) { position: relative; }
.bento-item:nth-child(3)::before,
.bento-item:nth-child(6)::before,
.bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: rgba(34, 197, 94, 0.85); z-index: 1; pointer-events: none; }
.bento-item:nth-child(3) { position: relative; }
.bento-item:nth-child(3)::before,
.bento-item:nth-child(6)::before,
.bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: rgba(161, 98, 7, 0.85); z-index: 1; pointer-events: none; }
.bento-item:nth-child(3) { position: relative; }
.bento-item:nth-child(3)::before,
.bento-item:nth-child(6)::before,
.bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: rgba(120, 53, 15, 0.85); z-index: 1; pointer-events: none; }
.bento-item:nth-child(3) { position: relative; }
.bento-item:nth-child(3)::before,
.bento-item:nth-child(6)::before,
.bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: rgba(249, 115, 22, 0.85); z-index: 1; pointer-events: none; }
.bento-item { padding: 32px 24px 24px; background: #FFFBEB; position: relative; transition: background 250ms; }
.bento-item::before { content: "§"; position: absolute; top: 24px; right: 24px; color: #D97706; font-family: 'EB Garamond', serif; font-size: 1.5rem; font-weight: 500; opacity: 0.3; }
.bento-item:hover { background: #FEF3C7; }
.bento-monogram { position: absolute; top: 20px; right: 50px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: #78350F; color: #FFFBEB; font-family: 'EB Garamond', serif; font-size: 1.0625rem; font-weight: 500; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #78350F; border: 1px solid #78350F; font-family: 'EB Garamond', serif; font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.12em; margin-bottom: 12px; text-transform: uppercase; }
.bento-name { font-family: 'EB Garamond', serif; font-size: 1.1875rem; font-weight: 500; margin-bottom: 4px; color: #1C1917; padding-right: 80px; text-wrap: balance; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 2.6em; }
.bento-tag { font-family: 'EB Garamond', serif; font-size: 0.875rem; color: #57534E; line-height: 1.5; }

.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 28px 24px 20px; background: #FFFBEB; border: 1px solid #D6D3D1; position: relative; transition: border-color 250ms, transform 250ms; }
.company:hover { border-color: #78350F; transform: translateY(-2px); }
.company-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.company-monogram { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: #78350F; color: #FFFBEB; font-family: 'EB Garamond', serif; font-size: 1.0625rem; font-weight: 500; }
.company-tier { padding: 2px 8px; border: 1px solid #78350F; color: #78350F; font-family: 'EB Garamond', serif; font-size: 0.625rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; }
.tier-S { background: #78350F; color: #FFFBEB; }
.tier-A { background: transparent; }
.tier-B { background: transparent; color: #78716C; border-color: #D6D3D1; }
.company-name { font-family: 'EB Garamond', serif; font-size: 1.1875rem; font-weight: 500; margin-bottom: 10px; color: #1C1917; }
.company-meta { font-family: 'EB Garamond', serif; font-size: 0.8125rem; color: #57534E; line-height: 1.5; margin-bottom: 12px; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 10px; border-top: 1px solid #E7E5E4; }
.sparkline-bar { flex: 1; background: #D6D3D1; min-height: 2px; transition: background 250ms; }
.company:hover .sparkline-bar { background: #78350F; opacity: 0.7; }
.sparkline-label { font-family: 'EB Garamond', serif; font-size: 0.6875rem; color: #78716C; letter-spacing: 0.1em; margin-top: 6px; }

.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: #FFFBEB; border: 1px solid #D6D3D1; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 20px 24px; text-align: left; border-bottom: 1px solid #E7E5E4; font-size: 0.9375rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: rgba(254, 243, 199, 0.4); font-family: 'EB Garamond', serif; font-weight: 500; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.15em; color: #57534E; }
.salary-stage { font-family: 'EB Garamond', serif; font-weight: 500; color: #1C1917; font-size: 1.0625rem; }
.salary-bar { display: inline-block; width: 80px; height: 4px; background: #E7E5E4; margin-left: 12px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #78350F; }
.yoy { display: inline-block; font-family: 'EB Garamond', serif; font-size: 0.8125rem; font-weight: 500; margin-left: 12px; padding: 2px 8px; }
.yoy.up   { color: #15803D; }
.yoy.down { color: #B91C1C; }
.yoy.flat { color: #78716C; }
.approx { font-family: 'EB Garamond', serif; color: #A16207; margin-right: 4px; }

.direction-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 160px 1fr 60px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #E7E5E4; }
.direction:last-child { border-bottom: none; }
.direction-name { font-family: 'EB Garamond', serif; font-size: 1.0625rem; color: #1C1917; }
.direction-bar { height: 6px; background: #E7E5E4; overflow: hidden; }
.direction-bar-fill { height: 100%; background: #78350F; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); }
.direction-pct { font-family: 'EB Garamond', serif; font-weight: 500; text-align: right; font-size: 1.0625rem; color: #1C1917; }

.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: #FFFBEB; border: 1px solid #D6D3D1; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #78350F; transform: translateY(-2px); }
.path-pct { font-family: 'EB Garamond', serif; font-size: 2.75rem; font-weight: 500; color: #1C1917; margin-bottom: 4px; line-height: 1; }
.path-name { font-family: 'EB Garamond', serif; color: #57534E; font-size: 0.875rem; letter-spacing: 0.04em; margin-top: 8px; }

.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 36px 40px 32px; background: #FFFBEB; border: 1px solid #D6D3D1; border-left: 4px double #D97706; margin-bottom: 20px; transition: border-left-width 250ms, transform 250ms, box-shadow 250ms; position: relative; }
.quote:hover { border-left-width: 12px; transform: translateX(4px); box-shadow: 0 8px 24px rgba(120, 53, 15, 0.10); }
.quote::after { content: "— see " attr(data-cite) ", supra."; display: block; font-family: 'EB Garamond', serif; font-size: 0.75rem; color: #78716C; margin-top: 16px; padding-top: 12px; border-top: 1px solid #E7E5E4; }
.quote-head { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.quote-avatar { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #78350F; color: #FFFBEB; font-family: 'EB Garamond', serif; font-size: 1.125rem; font-weight: 500; }
.quote-byline strong { display: block; font-family: 'EB Garamond', serif; font-weight: 500; color: #1C1917; font-size: 1.0625rem; }
.quote-byline .quote-source { font-family: 'EB Garamond', serif; color: #78716C; font-size: 0.75rem; letter-spacing: 0.05em; }
.quote-text { font-family: 'EB Garamond', serif; font-size: 1.375rem; line-height: 1.7; color: #1C1917; }
.quote-text::before { content: "“"; color: #D97706; font-size: 1.4em; line-height: 0; vertical-align: -0.2em; margin-right: 4px; }
.quote-text::after { content: "”"; color: #D97706; font-size: 1.4em; line-height: 0; vertical-align: -0.2em; margin-left: 4px; }

.xuanke-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 220px 1fr 80px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #E7E5E4; }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-family: 'EB Garamond', serif; font-size: 1.0625rem; color: #1C1917; }
.xuanke-bar { height: 6px; background: #E7E5E4; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #78350F; }
.xuanke-pct { font-family: 'EB Garamond', serif; font-weight: 500; text-align: right; font-size: 1.0625rem; color: #1C1917; }

.curriculum-lede { font-family: 'EB Garamond', serif; color: #57534E; font-size: 1.0625rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.curriculum-block { padding: 32px 28px; background: #FFFBEB; border: 1px solid #D6D3D1; transition: border-color 250ms, transform 250ms; }
.curriculum-block:hover { border-color: #78350F; transform: translateY(-2px); }
.curriculum-title { font-family: 'EB Garamond', serif; font-variant: small-caps; font-size: 0.875rem; color: #78350F; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #D6D3D1; font-weight: 600; letter-spacing: 0.12em; }
.course { padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; font-size: 0.9375rem; }
.course-name { font-family: 'EB Garamond', serif; color: #1C1917; }
.course-credit { font-family: 'EB Garamond', serif; color: #78716C; font-size: 0.8125rem; margin-left: 8px; }

.cta-block { margin-top: 32px; padding: 64px 48px; background: #FFFBEB; border: 2px solid #1C1917; text-align: center; position: relative; }
.cta-block::before { content: ""; position: absolute; top: 8px; left: 8px; right: 8px; bottom: 8px; border: 1px solid #A16207; pointer-events: none; }
.cta-block h3 { font-family: 'EB Garamond', serif; font-size: 2rem; font-weight: 500; margin-bottom: 16px; color: #1C1917; }
.cta-block p { font-family: 'EB Garamond', serif; color: #57534E; margin: 0 auto 32px; max-width: 560px; font-size: 1.0625rem; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }
.cta-input { padding: 14px 18px; background: #FFFFFF; border: 1px solid #D6D3D1; color: #1C1917; font-family: 'EB Garamond', serif; font-size: 1rem; width: 180px; outline: none; }
.cta-input:focus { border-color: #78350F; }
.cta-button { padding: 14px 40px; background: #1C1917; color: #FFFBEB; font-family: 'EB Garamond', serif; font-size: 1rem; font-weight: 500; letter-spacing: 0.06em; transition: background 200ms; }
.cta-button:hover { background: #78350F; }
.cta-note { font-family: 'EB Garamond', serif; color: #78716C; font-size: 0.75rem; margin-top: 20px; }

.watermark { color: #78350F; opacity: 0.04; }
.section-num { font-family: 'EB Garamond', serif; color: #78350F; }
section.tab h2 { font-family: 'EB Garamond', serif; }
section.tab p { color: #1C1917; }
section.tab p.lede { color: #57534E; }
section.tab h3 { color: #1C1917; }
footer { background: rgba(254, 243, 199, 0.3); border-top: 1px solid #D6D3D1; }
footer .label { color: #1C1917; font-variant: small-caps; }
footer .data-source { color: #78716C; }

.drop-cap::first-letter { font-family: 'EB Garamond', serif; font-size: 4.5em; font-weight: 500; line-height: 0.85; float: left; margin: 0.05em 0.12em 0 0; color: #78350F; }

.redacted-block { display: inline-block; background: #1C1917; color: #1C1917; padding: 2px 8px; user-select: none; border-radius: 1px; margin: 0 2px; }
.redacted-block::before { content: "█████████"; }
"""

def render_hero_law(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    return f'''
<header class="hero">
  <div class="container">
    <div class="docket-stamp">已<br/>立案<br/>2026</div>
    <div class="docket-header">
      <div class="docket-court">在 2026 高考选专业的判断中</div>
      <div class="docket-title-wrap">
        <div class="docket-line"></div>
        <div class="docket-title">第一章 · 专业全貌</div>
        <div class="docket-line"></div>
      </div>
    </div>
    <h1>{title}</h1>
    <p class="hero-tagline">— {summary[:120]} —</p>
    <div class="hero-tags">
      {''.join(f'<span class="tag primary">{t}</span>' for t in tags[:3])}
      {''.join(f'<span class="tag">{t}</span>' for t in tags[3:])}
    </div>
    <div class="docket-meta">
      <span>案号 2026-HE-LAW-001</span>
      <span>立案: {updated_at} 14:32 UTC+8</span>
      <span>申请人: 2026 届考生</span>
    </div>
  </div>
</header>'''
