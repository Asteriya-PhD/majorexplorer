"""
v4_styles/themes/sci.py — sci 主题 CSS + hero 渲染
"""

def render_hero_sci(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    return f'''
<header class="hero">
  <div style="border-bottom: 3px double #C73E1D; padding: 14px 40px; display: flex; justify-content: space-between; align-items: baseline; font-family: 'JetBrains Mono', monospace; font-size: 0.6875rem; letter-spacing: 0.15em; text-transform: uppercase; color: #786A4F; position: relative; z-index: 2;">
    <span><span style="color: #C73E1D;">VOL. 50 · NO. 03</span> · Major Explorer</span>
    <span>{title}专刊 · 2026 SPRING</span>
  </div>
  <div class="container" style="padding-top: 64px;">
    <div class="hero-decor" style="color: #C73E1D;">§ 01 · {title} · 基础学科</div>
    <h1 class="display" style="font-family: 'EB Garamond', serif; color: #1F1B12; font-weight: 500;">{title}</h1>
    <p class="hero-tagline" style="color: #786A4F; font-style: italic; max-width: 720px;">{summary[:140]}</p>
    <div class="hero-tags">
      {"".join(f'<span class="tag primary">{t}</span>' for t in tags[:3])}
      {"".join(f'<span class="tag">{t}</span>' for t in tags[3:])}
    </div>
    <div class="hero-stats">
      <div class="stat"><div class="stat-label">学科门类</div><div class="stat-value">{category}</div></div>
      <div class="stat"><div class="stat-label">学制 · 学位</div><div class="stat-value">{duration}Y · {degree}</div></div>
      <div class="stat"><div class="stat-label">难度</div><div class="stat-value">{difficulty}</div></div>
      <div class="stat"><div class="stat-label">数据更新</div><div class="stat-value">{updated_at}</div></div>
    </div>
  </div>
</header>'''
