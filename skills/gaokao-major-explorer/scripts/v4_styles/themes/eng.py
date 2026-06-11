"""
v4_styles/themes/eng.py — eng 主题 CSS + hero 渲染
"""

def render_hero_eng(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    slug = data.get("slug", "ME")
    return f'''
<header class="hero">
  <div style="border-bottom: 2px solid #1B3A5C; display: grid; grid-template-columns: auto 1fr auto; align-items: center; padding: 12px 24px; font-family: 'Roboto Mono', monospace; font-size: 0.6875rem; letter-spacing: 0.12em; text-transform: uppercase; color: #1B3A5C; position: relative; z-index: 2;">
    <span style="border-right: 1px solid rgba(27,58,92,0.4); padding-right: 16px;">DWG-{slug.upper()}-2026-003</span>
    <span style="text-align: center; font-weight: 600; padding: 0 16px;">{title} · 课程总览</span>
    <span style="border-left: 1px solid rgba(27,58,92,0.4); padding-left: 16px;"><span style="color: #FF6B35;">SCALE 1:1 · </span>A4 LANDSCAPE</span>
  </div>
  <div class="container" style="padding-top: 64px;">
    <div class="hero-decor" style="color: #FF6B35;">▶ {title} · 制造业基础</div>
    <h1 class="display" style="font-family: 'Inter', sans-serif; color: #1A1F2E; font-weight: 800; letter-spacing: -0.03em;">{title}</h1>
    <p class="hero-tagline" style="color: #5C6373; max-width: 720px;">{summary[:140]}</p>
    <div class="hero-tags">
      {"".join(f'<span class="tag primary">{t}</span>' for t in tags[:3])}
      {"".join(f'<span class="tag">{t}</span>' for t in tags[3:])}
    </div>
    <div class="hero-stats">
      <div class="stat"><div class="stat-label">学科</div><div class="stat-value">{category}</div></div>
      <div class="stat"><div class="stat-label">学制 · 学位</div><div class="stat-value">{duration}Y · {degree}</div></div>
      <div class="stat"><div class="stat-label">难度</div><div class="stat-value">{difficulty}</div></div>
      <div class="stat"><div class="stat-label">数据更新</div><div class="stat-value">{updated_at}</div></div>
    </div>
  </div>
</header>'''
