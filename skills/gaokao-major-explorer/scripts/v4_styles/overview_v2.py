"""
v4_styles/overview_v2.py — 速览 v2: 3 张子卡片堆叠 (学什么 / 适合谁 / 避坑)
"""


# ──────────────────────────────────────────────────────────
# render_overview_v2: 3 张子卡片堆叠, 用于 data["overview_v2"]
# ──────────────────────────────────────────────────────────
def render_overview_v2(data: dict) -> str:
    """3 张子卡片 (学什么 / 适合谁 / 避坑), 主题色自动适配, 移动端 1 列堆叠"""
    ov = data.get("overview_v2", {})
    if not ov:
        return ""

    lede = ov.get("lede") or data.get("summary", "")
    what = ov.get("what", {})
    fit = ov.get("fit", {})
    pitfalls = ov.get("pitfalls", [])

    # ── lede 段 ──
    html = f'<p class="lede drop-cap ovv-lede">{lede}</p>'

    # ── 子卡 1: 这个专业学什么? (绿条) ──
    html += '<div class="ovv-card fade-up">'
    html += '<div class="ovv-card-head">'
    html += '<span class="ovv-card-num">01 / 03</span>'
    html += '<h3 class="ovv-card-title">这个专业学什么?</h3>'
    html += '<span class="ovv-card-tag">Foundations · Directions · Skills</span>'
    html += '</div>'

    foundations = what.get("foundations", [])
    if foundations:
        html += '<div class="ovv-foundations">'
        html += '<div class="ovv-foundations-label">前 2 年基础课</div>'
        html += '<div class="ovv-timeline">'
        for f in foundations:
            html += f'<div class="ovv-tl-step"><span>{f}</span></div>'
        html += '</div></div>'

    directions = what.get("directions", [])
    if directions:
        html += '<div class="ovv-directions-label">大三大四 · 5 大方向分流</div>'
        html += '<div class="ovv-directions">'
        for i, d in enumerate(directions, 1):
            if isinstance(d, dict):
                name = d.get("name", "")
                desc = d.get("desc", "")
            else:
                name = str(d)
                desc = ""
            html += f'<div class="ovv-dir"><div class="ovv-dir-num">F.0{i}</div><div class="ovv-dir-name">{name}</div><div class="ovv-dir-desc">{desc}</div></div>'
        html += '</div>'

    skills = what.get("skills", [])
    if skills:
        html += '<div class="ovv-skills">'
        for s in skills:
            html += f'<span class="ovv-skill">{s}</span>'
        html += '</div>'

    bonus = what.get("bonus", "")
    if bonus:
        html += f'<div class="ovv-bonus">{bonus}</div>'

    html += '</div>'

    # ── 子卡 2: 什么人适合? (蓝条) ──
    yes_list = fit.get("yes", [])
    no_list = fit.get("no", [])
    if yes_list or no_list:
        html += '<div class="ovv-card is-blue fade-up">'
        html += '<div class="ovv-card-head">'
        html += '<span class="ovv-card-num">02 / 03</span>'
        html += '<h3 class="ovv-card-title">什么人适合?</h3>'
        html += '<span class="ovv-card-tag">Fit Check</span>'
        html += '</div>'
        html += '<div class="ovv-fit-grid">'
        if yes_list:
            html += '<div class="ovv-fit-col is-yes"><div class="ovv-fit-label">✓ 适合</div><ul class="ovv-fit-list">'
            for item in yes_list:
                html += f'<li>{item}</li>'
            html += '</ul></div>'
        if no_list:
            html += '<div class="ovv-fit-col is-no"><div class="ovv-fit-label">✗ 不适合</div><ul class="ovv-fit-list">'
            for item in no_list:
                html += f'<li>{item}</li>'
            html += '</ul></div>'
        html += '</div></div>'

    # ── 子卡 3: 避坑指南 (橙红条) ──
    if pitfalls:
        html += '<div class="ovv-card is-orange fade-up">'
        html += '<div class="ovv-card-head">'
        html += '<span class="ovv-card-num">03 / 03</span>'
        html += '<h3 class="ovv-card-title">避坑指南</h3>'
        html += f'<span class="ovv-card-tag">{len(pitfalls)} 个常见误区</span>'
        html += '</div>'
        html += '<div class="ovv-pits">'
        for i, p in enumerate(pitfalls, 1):
            if isinstance(p, dict):
                myth = p.get("myth", "")
                reality = p.get("reality", "")
            else:
                myth = str(p)
                reality = ""
            html += f'<div class="ovv-pit"><div class="ovv-pit-num">误区 {i:02d}</div><div class="ovv-pit-myth">❌ {myth}</div><div class="ovv-pit-reality">{reality}</div></div>'
        html += '</div></div>'

    return html


# ──────────────────────────────────────────────────────────
# 速览 v2 共享 CSS — 3 张子卡片堆叠 (林奈式 + 朱砂印 + 标本签)
# 设计原则: 全局零 layout 改动, 只在 #overview 内部; 颜色用主题变量
# 3 个子卡: 学什么 (绿条) / 适合谁 (蓝条) / 避坑 (橙红条)
# ──────────────────────────────────────────────────────────
OVERVIEW_V2_CSS = """
/* === 速览 v2 — 3 子卡堆叠 === */
.ovv-lede { max-width: 720px; margin: 0 0 48px; }
.ovv-card {
  position: relative; padding: 36px 40px 40px; margin-bottom: 32px;
  background: var(--paper, #FAFAF6); border: 1px solid var(--rule, #E5E5E0);
  border-radius: 4px; overflow: hidden;
  transition: border-color 250ms, transform 250ms, box-shadow 250ms;
}
.ovv-card:hover { border-color: var(--moss, #6B8E23); transform: translateY(-2px); box-shadow: 0 12px 32px rgba(0,0,0,0.06); }
.ovv-card::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
  background: var(--moss, #6B8E23);
}
.ovv-card.is-blue::before { background: #1E3A5F; }
.ovv-card.is-orange::before { background: #B91C1C; }
.ovv-card-head { display: flex; align-items: baseline; gap: 18px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--rule, #E5E5E0); }
.ovv-card-num {
  font-family: 'Cormorant Garamond', serif; font-size: 0.875rem;
  letter-spacing: 0.3em; text-transform: uppercase; font-weight: 600;
  color: var(--moss, #6B8E23);
}
.ovv-card.is-blue .ovv-card-num { color: #1E3A5F; }
.ovv-card.is-orange .ovv-card-num { color: #B91C1C; }
.ovv-card-title {
  font-family: 'Noto Serif SC', serif; font-size: 1.5rem; font-weight: 700;
  color: var(--ink, #1A1A1A); margin: 0; flex: 1;
}
.ovv-card-tag {
  font-family: 'Cormorant Garamond', serif; font-style: italic;
  font-size: 0.8125rem; color: var(--muted, #666);
}

/* === 学什么 — 时间轴 + 5 方向 grid + 3 技能 chip === */
.ovv-foundations { margin-bottom: 28px; }
.ovv-foundations-label {
  font-family: 'Noto Serif SC', serif; font-size: 0.875rem; color: var(--muted, #666);
  margin-bottom: 12px; letter-spacing: 0.05em;
}
.ovv-timeline {
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px;
  position: relative; padding-top: 18px;
}
.ovv-timeline::before {
  content: ""; position: absolute; left: 0; right: 0; top: 6px; height: 1px;
  background: linear-gradient(90deg, transparent, var(--moss, #6B8E23) 20%, var(--moss, #6B8E23) 80%, transparent);
}
.ovv-tl-step { position: relative; text-align: center; }
.ovv-tl-step::before {
  content: ""; position: absolute; left: 50%; top: -16px; transform: translateX(-50%);
  width: 9px; height: 9px; border-radius: 50%; background: var(--paper, #FAFAF6);
  border: 1.5px solid var(--moss, #6B8E23);
}
.ovv-tl-step span {
  display: block; font-family: 'Noto Serif SC', serif; font-size: 0.8125rem;
  color: var(--ink, #1A1A1A); padding-top: 14px;
}
.ovv-directions-label {
  font-family: 'Noto Serif SC', serif; font-size: 0.875rem; color: var(--muted, #666);
  margin: 24px 0 12px; letter-spacing: 0.05em;
}
.ovv-directions { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.ovv-dir {
  padding: 18px 16px; border: 1px solid var(--rule, #E5E5E0); border-radius: 3px;
  background: rgba(255,255,255,0.4);
  transition: border-color 200ms, background 200ms, transform 200ms;
  min-height: 110px;
}
.ovv-dir:hover { border-color: var(--moss, #6B8E23); background: var(--paper, #FAFAF6); transform: translateY(-2px); }
.ovv-dir-num {
  font-family: 'Cormorant Garamond', serif; font-style: italic;
  font-size: 0.75rem; color: var(--moss, #6B8E23); margin-bottom: 4px;
  letter-spacing: 0.1em;
}
.ovv-dir-name {
  font-family: 'Noto Serif SC', serif; font-size: 0.9375rem; font-weight: 700;
  color: var(--ink, #1A1A1A); margin-bottom: 6px; line-height: 1.3;
}
.ovv-dir-desc {
  font-family: 'Noto Serif SC', serif; font-size: 0.75rem; color: var(--muted, #666);
  line-height: 1.5;
}
.ovv-skills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 24px; }
.ovv-skill {
  font-family: 'Noto Serif SC', serif; font-size: 0.8125rem;
  padding: 6px 14px; border: 1px solid var(--moss, #6B8E23);
  color: var(--moss, #6B8E23); border-radius: 2px; background: rgba(255,255,255,0.4);
}
.ovv-bonus {
  margin-top: 24px; padding: 16px 20px;
  border-left: 3px solid var(--gold, #B8902A); background: rgba(184, 144, 42, 0.04);
  font-family: 'Noto Serif SC', serif; font-size: 0.9375rem; font-style: italic;
  color: var(--ink, #1A1A1A); line-height: 1.7;
}

/* === 适合谁 — ✓ / ✗ 双列 === */
.ovv-fit-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.ovv-fit-col { padding: 20px 24px; border: 1px solid var(--rule, #E5E5E0); border-radius: 3px; }
.ovv-fit-col.is-yes { border-left: 3px solid #2E7D32; background: rgba(46, 125, 50, 0.03); }
.ovv-fit-col.is-no { border-left: 3px solid #B91C1C; background: rgba(185, 28, 28, 0.03); }
.ovv-fit-label {
  font-family: 'Noto Serif SC', serif; font-weight: 700; font-size: 0.9375rem;
  margin-bottom: 12px; letter-spacing: 0.05em;
}
.ovv-fit-col.is-yes .ovv-fit-label { color: #2E7D32; }
.ovv-fit-col.is-no .ovv-fit-label { color: #B91C1C; }
.ovv-fit-list { list-style: none; padding: 0; margin: 0; }
.ovv-fit-list li {
  font-family: 'Noto Serif SC', serif; font-size: 0.875rem; line-height: 1.7;
  color: var(--ink, #1A1A1A); padding: 6px 0; border-bottom: 1px dashed var(--rule, #E5E5E0);
  position: relative; padding-left: 20px;
}
.ovv-fit-list li:last-child { border-bottom: none; }
.ovv-fit-col.is-yes .ovv-fit-list li::before {
  content: "✓"; position: absolute; left: 0; top: 6px; color: #2E7D32; font-weight: 700;
}
.ovv-fit-col.is-no .ovv-fit-list li::before {
  content: "✗"; position: absolute; left: 0; top: 6px; color: #B91C1C; font-weight: 700;
}

/* === 避坑 — 6 误区 + 真相 === */
.ovv-pits { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.ovv-pit {
  padding: 20px 22px; border: 1px solid var(--rule, #E5E5E0); border-left: 3px solid #B91C1C;
  border-radius: 3px; background: rgba(185, 28, 28, 0.02);
  transition: border-color 200ms, transform 200ms, background 200ms;
}
.ovv-pit:hover { border-color: #B91C1C; background: rgba(185, 28, 28, 0.06); transform: translateX(4px); }
.ovv-pit-num {
  font-family: 'Cormorant Garamond', serif; font-size: 0.75rem;
  color: #B91C1C; letter-spacing: 0.15em; margin-bottom: 4px;
}
.ovv-pit-myth {
  font-family: 'Noto Serif SC', serif; font-size: 0.9375rem; font-weight: 700;
  color: #B91C1C; margin-bottom: 8px; line-height: 1.4;
}
.ovv-pit-reality {
  font-family: 'Noto Serif SC', serif; font-size: 0.8125rem; color: var(--ink, #1A1A1A);
  line-height: 1.7;
}

/* === 移动端 === */
@media (max-width: 1023px) {
  .ovv-card { padding: 28px 28px 32px; }
  .ovv-timeline { grid-template-columns: repeat(4, 1fr); }
  .ovv-timeline > .ovv-tl-step:nth-child(n+5) { display: none; }
  .ovv-directions { grid-template-columns: repeat(3, 1fr); }
  .ovv-fit-grid { grid-template-columns: 1fr; }
  .ovv-pits { grid-template-columns: 1fr; }
}
@media (max-width: 767px) {
  .ovv-card { padding: 24px 22px 28px; }
  .ovv-card-head { flex-wrap: wrap; gap: 8px; }
  .ovv-card-title { font-size: 1.25rem; }
  .ovv-timeline { grid-template-columns: repeat(3, 1fr); }
  .ovv-timeline > .ovv-tl-step:nth-child(n+4) { display: none; }
  .ovv-directions { grid-template-columns: repeat(2, 1fr); }
  .ovv-skills { gap: 6px; }
  .ovv-skill { font-size: 0.75rem; padding: 4px 10px; }
}
@media (max-width: 480px) {
  .ovv-directions { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .ovv-card, .ovv-dir, .ovv-pit { transition: none; }
  .ovv-card:hover, .ovv-dir:hover, .ovv-pit:hover { transform: none; }
}
"""
