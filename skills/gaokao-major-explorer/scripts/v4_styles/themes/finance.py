"""
v4_styles/themes/finance.py — finance 主题 CSS + hero 渲染
"""

FINANCE_CSS = """
.hero { padding: 100px 0 80px; background: transparent; border-bottom: 1px solid #E7E5E4; text-align: center; position: relative; z-index: 2; }
.letterhead-top { display: flex; align-items: center; justify-content: center; gap: 16px; padding-bottom: 16px; margin-bottom: 32px; border-bottom: 1px solid #D6D3D1; max-width: 720px; margin-left: auto; margin-right: auto; }
.letterhead-logo { font-family: 'Cormorant Garamond', serif; font-size: 1.5rem; font-weight: 500; color: #1C1917; letter-spacing: 0.05em; }
.letterhead-divider { flex: 1; height: 1px; background: linear-gradient(90deg, transparent, #A16207, transparent); opacity: 0.5; }
.letterhead-meta { font-family: 'Jost', sans-serif; font-size: 0.6875rem; color: #78716C; letter-spacing: 0.15em; text-transform: uppercase; }
.letterhead-motto { font-family: 'Cormorant Garamond', serif; font-size: 0.9375rem; color: #A16207; text-align: center; letter-spacing: 0.04em; margin-bottom: 40px; }
.hero-decor { font-family: 'Cormorant Garamond', serif; font-size: 1rem; color: #78716C; letter-spacing: 0.05em; margin-bottom: 24px; }
.hero h1 { font-family: 'Bodoni Moda', serif; font-size: clamp(3.25rem, 6.5vw, 5.5rem); font-weight: 500; letter-spacing: -0.03em; line-height: 1.05; color: #0C0A09; margin-bottom: 24px; }
.hero h1::after { content: " ®"; font-size: 0.35em; vertical-align: super; color: #A16207; font-style: normal; font-weight: 400; }
.hero-tagline { font-family: 'Cormorant Garamond', serif; font-size: 1.25rem; color: #78716C; margin: 0 auto 40px; max-width: 600px; line-height: 1.7; }
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 56px; justify-content: center; }
.tag { padding: 6px 16px; background: transparent; border: 1px solid #D6D3D1; border-radius: 0; font-family: 'Cormorant Garamond', serif; font-size: 0.875rem; color: #1C1917; letter-spacing: 0.04em; }
.tag.primary { background: rgba(161, 98, 7, 0.08); border-color: #A16207; color: #A16207; }

.hero-stats { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #D6D3D1; border-bottom: 1px solid #D6D3D1; border-left: 1px solid #D6D3D1; border-right: 1px solid #D6D3D1; max-width: 800px; margin: 0 auto; }
@media (max-width: 768px) { .hero-stats { grid-template-columns: repeat(2, 1fr); } }
.stat { padding: 28px 20px; border-right: 1px solid #E7E5E4; }
.stat:last-child { border-right: none; }
@media (max-width: 768px) { .stat:nth-child(2) { border-right: none; } .stat:nth-child(1), .stat:nth-child(2) { border-bottom: 1px solid #E7E5E4; } }
.stat-label { font-family: 'Jost', sans-serif; font-size: 0.625rem; color: #78716C; text-transform: uppercase; letter-spacing: 0.18em; font-weight: 500; }
.stat-value { font-family: 'Bodoni Moda', serif; font-size: 1.5rem; font-weight: 500; color: #1C1917; margin-top: 6px; letter-spacing: -0.01em; }

.hero::after { content: ""; display: block; width: 240px; height: 1px; background: linear-gradient(90deg, transparent, #A16207, transparent); margin: 48px auto 0; opacity: 0.4; }

section.tab { border-top: 1px solid #A8A29E; border-bottom: 2px solid #A8A29E; }
section.tab:first-of-type { border-top: none; }
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1px; background: #A8A29E; border: 1px solid #A8A29E; border-radius: 0; overflow: hidden; margin-top: 32px; position: relative; z-index: 1; }
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
.bento-item { padding: 32px 24px 24px; background: #FFFFFF; position: relative; transition: background 250ms; }
.bento-item:hover { background: #FAFAF9; }
.bento-monogram { position: absolute; top: 20px; right: 20px; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #1C1917; color: #FAFAF9; font-family: 'Bodoni Moda', serif; font-size: 1.0625rem; font-weight: 500; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #A16207; border: 1px solid #A16207; border-radius: 0; font-family: 'Bodoni Moda', serif; font-size: 0.75rem; font-weight: 500; letter-spacing: 0.06em; margin-bottom: 12px; }
.bento-name { font-family: 'Bodoni Moda', serif; font-size: 1.1875rem; font-weight: 500; margin-bottom: 4px; color: #0C0A09; padding-right: 44px; text-wrap: balance; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 2.6em; }
.bento-tag { font-family: 'Jost', sans-serif; font-size: 0.8125rem; color: #57534E; line-height: 1.5; }

.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 32px 24px 22px; background: #FFFFFF; border: 1px solid #E7E5E4; border-radius: 0; position: relative; transition: border-color 250ms, transform 250ms; }
.company:hover { border-color: #A16207; transform: translateY(-2px); }
.company::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, #A16207, transparent); opacity: 0; transition: opacity 250ms; }
.company:hover::before { opacity: 0.6; }
.company-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.company-monogram { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #1C1917; color: #FAFAF9; font-family: 'Bodoni Moda', serif; font-size: 1.125rem; font-weight: 500; }
.company-tier { padding: 2px 8px; border: 1px solid #A16207; color: #A16207; font-family: 'Bodoni Moda', serif; font-size: 0.6875rem; font-weight: 500; letter-spacing: 0.08em; }
.tier-S { background: #A16207; color: #FAFAF9; border-color: #A16207; }
.tier-A { background: transparent; }
.tier-B { background: transparent; color: #78716C; border-color: #D6D3D1; }
.company-name { font-family: 'Bodoni Moda', serif; font-size: 1.1875rem; font-weight: 500; margin-bottom: 10px; color: #0C0A09; }
.company-meta { font-family: 'Jost', sans-serif; font-size: 0.8125rem; color: #57534E; line-height: 1.5; margin-bottom: 14px; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 12px; border-top: 1px solid #F5F5F4; }
.sparkline-bar { flex: 1; background: #E7E5E4; min-height: 2px; transition: background 250ms; }
.company:hover .sparkline-bar { background: #A16207; opacity: 0.7; }
.sparkline-label { font-family: 'Jost', sans-serif; font-size: 0.625rem; color: #A16207; letter-spacing: 0.15em; margin-top: 6px; text-transform: uppercase; }

.salary-table { width: 100%; border-collapse: collapse; margin: 32px auto 0; max-width: 880px; background: #FFFFFF; border: 1px solid #E7E5E4; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 22px 28px; text-align: left; border-bottom: 1px solid #E7E5E4; font-size: 0.9375rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: #FAFAF9; font-family: 'Bodoni Moda', serif; font-weight: 500; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.12em; color: #57534E; }
.salary-stage { font-family: 'Bodoni Moda', serif; font-weight: 500; color: #0C0A09; font-size: 1.0625rem; }
.salary-bar { display: inline-block; width: 80px; height: 4px; background: #F5F5F4; margin-left: 12px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #A16207; }
.yoy { display: inline-block; font-family: 'Bodoni Moda', serif; font-size: 0.8125rem; font-weight: 500; margin-left: 12px; padding: 2px 8px; }
.yoy.up   { color: #15803D; }
.yoy.down { color: #B91C1C; }
.yoy.flat { color: #78716C; }
.approx { font-family: 'Bodoni Moda', serif; color: #A16207; margin-right: 4px; }

.direction-list { margin: 32px auto 0; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 160px 1fr 60px; align-items: center; gap: 24px; padding: 16px 0; border-bottom: 1px solid #E7E5E4; }
.direction:last-child { border-bottom: none; }
.direction-name { font-family: 'Bodoni Moda', serif; font-size: 1.0625rem; color: #0C0A09; }
.direction-bar { height: 6px; background: #F5F5F4; overflow: hidden; }
.direction-bar-fill { height: 100%; background: #A16207; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); }
.direction-pct { font-family: 'Bodoni Moda', serif; font-weight: 500; text-align: right; font-size: 1.0625rem; color: #1C1917; }

.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 20px; margin: 32px auto 0; max-width: 800px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: #FFFFFF; border: 1px solid #E7E5E4; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #A16207; transform: translateY(-2px); }
.path-pct { font-family: 'Bodoni Moda', serif; font-size: 2.75rem; font-weight: 500; color: #1C1917; margin-bottom: 4px; line-height: 1; }
.path-name { font-family: 'Jost', sans-serif; color: #57534E; font-size: 0.75rem; letter-spacing: 0.12em; margin-top: 8px; text-transform: uppercase; }

.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 32px 36px; background: #FFFFFF; border: 1px solid #E7E5E4; border-left: 3px solid #A16207; margin-bottom: 20px; transition: border-left-width 250ms, transform 250ms, box-shadow 250ms; }
.quote:hover { border-left-width: 8px; transform: translateX(4px); box-shadow: 0 8px 24px rgba(161, 98, 7, 0.08); }
.quote-head { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.quote-avatar { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #1C1917; color: #FAFAF9; font-family: 'Bodoni Moda', serif; font-size: 1.125rem; font-weight: 500; }
.quote-byline strong { display: block; font-family: 'Bodoni Moda', serif; font-weight: 500; color: #0C0A09; font-size: 1rem; }
.quote-byline .quote-source { font-family: 'Jost', sans-serif; color: #78716C; font-size: 0.75rem; letter-spacing: 0.05em; }
.quote-text { font-family: 'Cormorant Garamond', serif; font-size: 1.375rem; line-height: 1.65; color: #0C0A09; }
.quote-text::before { content: "“"; color: #A16207; font-size: 1.4em; line-height: 0; vertical-align: -0.2em; margin-right: 4px; }
.quote-text::after { content: "”"; color: #A16207; font-size: 1.4em; line-height: 0; vertical-align: -0.2em; margin-left: 4px; }

.xuanke-list { margin: 32px auto 0; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 220px 1fr 80px; align-items: center; gap: 24px; padding: 16px 0; border-bottom: 1px solid #E7E5E4; }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-family: 'Bodoni Moda', serif; font-size: 1.0625rem; color: #0C0A09; }
.xuanke-bar { height: 6px; background: #F5F5F4; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #A16207; }
.xuanke-pct { font-family: 'Bodoni Moda', serif; font-weight: 500; text-align: right; font-size: 1.0625rem; color: #1C1917; }

.curriculum-lede { font-family: 'Cormorant Garamond', serif; color: #57534E; font-size: 1.0625rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 32px; position: relative; z-index: 1; }
.curriculum-block { padding: 32px 28px; background: #FFFFFF; border: 1px solid #E7E5E4; transition: border-color 250ms, transform 250ms; }
.curriculum-block:hover { border-color: #A16207; transform: translateY(-2px); }
.curriculum-title { font-family: 'Bodoni Moda', serif; font-size: 0.875rem; color: #A16207; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #E7E5E4; font-weight: 500; }
.course { padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; font-size: 0.9375rem; }
.course-name { font-family: 'Jost', sans-serif; color: #0C0A09; }
.course-credit { font-family: 'Bodoni Moda', serif; color: #78716C; font-size: 0.8125rem; margin-left: 8px; }

.cta-block { margin: 32px auto 0; max-width: 800px; padding: 64px 48px; background: #FFFFFF; border: 1px solid #1C1917; text-align: center; position: relative; }
.cta-block::before { content: ""; position: absolute; top: 8px; left: 8px; right: 8px; bottom: 8px; border: 1px solid #A16207; pointer-events: none; }
.cta-block h3 { font-family: 'Bodoni Moda', serif; font-size: 2rem; font-weight: 500; margin-bottom: 16px; color: #0C0A09; }
.cta-block p { font-family: 'Cormorant Garamond', serif; color: #57534E; margin: 0 auto 32px; max-width: 560px; font-size: 1.0625rem; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }
.cta-input { padding: 14px 18px; background: #FFFFFF; border: 1px solid #D6D3D1; color: #0C0A09; font-family: 'Bodoni Moda', serif; font-size: 1rem; width: 180px; outline: none; }
.cta-input:focus { border-color: #A16207; }
.cta-button { padding: 14px 40px; background: #1C1917; color: #FAFAF9; font-family: 'Bodoni Moda', serif; font-size: 1rem; font-weight: 500; letter-spacing: 0.06em; transition: background 200ms; }
.cta-button:hover { background: #A16207; }
.cta-note { font-family: 'Jost', sans-serif; color: #78716C; font-size: 0.75rem; margin-top: 20px; letter-spacing: 0.05em; }

.watermark { color: #A16207; opacity: 0.04; }
.section-num { font-family: 'Jost', sans-serif; color: #A16207; }
section.tab h2 { font-family: 'Bodoni Moda', serif; font-weight: 500; }
section.tab p { color: #0C0A09; }
section.tab p.lede { color: #57534E; }
section.tab h3 { color: #0C0A09; }
footer { background: transparent; border-top: 1px solid #D6D3D1; }
footer .label { color: #1C1917; }
footer .data-source { color: #78716C; }

.drop-cap::first-letter { font-family: 'Bodoni Moda', serif; font-size: 4.5em; font-weight: 500; line-height: 0.85; float: left; margin: 0.08em 0.12em 0 0; color: #A16207; }
"""

def render_hero_finance(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    return f'''
<header class="hero">
  <div class="container">
    <div class="letterhead-top">
      <div class="letterhead-meta">VOL. {updated_at.split("-")[0] or "2026"} · NO. {tags[0] if tags else "01"}</div>
      <div class="letterhead-logo">M·E</div>
      <div class="letterhead-meta">MAJOR EXPLORER · 内部传阅</div>
    </div>
    <div class="letterhead-motto">— Private wealth · Risk and reward · Compound interest of knowledge —</div>
    <h1>{title}</h1>
    <p class="hero-tagline">— {summary[:120]} —</p>
    <div class="hero-tags">
      {''.join(f'<span class="tag primary">{t}</span>' for t in tags[:3])}
      {''.join(f'<span class="tag">{t}</span>' for t in tags[3:])}
    </div>
    <div class="hero-stats">
      <div class="stat"><div class="stat-label">学科</div><div class="stat-value">{category}</div></div>
      <div class="stat"><div class="stat-label">学制 · 学位</div><div class="stat-value">{duration}Y · {degree}</div></div>
      <div class="stat"><div class="stat-label">难度</div><div class="stat-value">{difficulty}</div></div>
      <div class="stat"><div class="stat-label">更新</div><div class="stat-value">{updated_at}</div></div>
    </div>
  </div>
</header>'''
