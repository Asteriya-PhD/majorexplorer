"""
overview_simple.py — 简化版速览渲染 (TEMPLATE 锁定的 4 段, 不分 cards)

跟 overview_v2.py 的区别:
  - v2: 3 子卡 (学什么/适合谁/避坑), 复杂 timeline + 5 方向 grid + skills chip
  - simple: 4 段平面 (lede/what_you_learn/who_fits/pitfalls), LLM 不需要拆 what.foundations/skills

TEMPLATE 字段:
  overview_v2.lede              → 1 段总览
  overview_v2.what_you_learn    → 1 长串 (含 4 年 + 5 方向 + 核心能力)
  overview_v2.who_fits_yes      → [3-5 短要点]
  overview_v2.who_fits_no       → [2-3 短要点]
  overview_v2.pitfalls          → [{myth, reality} × 4-6]

新增场景: 现场/批量合成的内容走这里, 格式稳定, 走样空间 0.
保留 v2: 70 篇精品继续走 v2 cards.
"""
from __future__ import annotations
from typing import Any


OVERVIEW_SIMPLE_CSS = r"""
/* === 简化速览 (TEMPLATE 锁版, 不分 cards) === */
.ovv-simple { max-width: 880px; margin: 0 auto; }
.ovv-simple-section { margin-bottom: 56px; }
.ovv-simple-lede {
  font-family: var(--font-heading);
  font-size: 1.1875rem; line-height: 1.85; color: var(--ink, #1A1A1A);
  margin-bottom: 48px; max-width: 760px; padding-left: 0;
  font-weight: 400;
}
.ovv-simple-lede::first-letter {
  font-family: var(--font-heading);
  font-size: 3.25rem; font-weight: 700; line-height: 1;
  color: var(--accent, #DC2626); margin-right: 8px; float: left;
  padding-top: 4px;
}
.ovv-simple-h {
  font-family: var(--font-heading);
  font-size: 1.375rem; font-weight: 700; color: var(--ink, #1A1A1A);
  margin: 0 0 20px; padding-bottom: 12px;
  border-bottom: 1px solid var(--rule, #E5E5E0);
  letter-spacing: -0.01em;
}
.ovv-simple-h .ovv-num {
  font-family: var(--font-num);
  font-size: 0.75rem; font-weight: 600;
  color: var(--muted, #6B6B6B); letter-spacing: 0.2em;
  margin-right: 12px;
}
.ovv-simple-body {
  font-family: var(--font-body);
  font-size: 1rem; line-height: 1.85; color: var(--ink, #1A1A1A);
}
.ovv-simple-fit {
  display: grid; grid-template-columns: 1fr 1fr; gap: 32px;
  margin-top: 16px;
}
.ovv-simple-fit-col { padding: 20px 0; }
.ovv-simple-fit-col.is-yes { border-left: 3px solid #2E7D32; padding-left: 20px; background: rgba(46, 125, 50, 0.03); }
.ovv-simple-fit-col.is-no  { border-left: 3px solid #B8323A; padding-left: 20px; background: rgba(184, 50, 58, 0.03); }
.ovv-simple-fit-list li { color: #1A1A1A !important; } /* 修复 2026-06-22: defensive 防止任何 theme 下看不清 */
.ovv-simple-fit-label {
  font-family: var(--font-heading);
  font-size: 0.8125rem; font-weight: 700;
  letter-spacing: 0.15em; text-transform: uppercase;
  margin-bottom: 12px;
}
.ovv-simple-fit-col.is-yes .ovv-simple-fit-label { color: #2E7D32; }
.ovv-simple-fit-col.is-no  .ovv-simple-fit-label { color: #B8323A; }
.ovv-simple-fit-list {
  list-style: none; padding: 0; margin: 0;
}
.ovv-simple-fit-list li {
  font-family: var(--font-body);
  font-size: 0.9375rem; line-height: 1.7;
  color: var(--ink, #1A1A1A);
  padding: 6px 0;
  border-bottom: 1px dashed rgba(0,0,0,0.06);
}
.ovv-simple-fit-list li:last-child { border-bottom: none; }
.ovv-simple-pitfalls {
  list-style: none; padding: 0; margin: 0;
}
.ovv-simple-pitfalls li {
  padding: 16px 0;
  border-bottom: 1px solid var(--rule, #E5E5E0);
  display: grid; grid-template-columns: 1fr; gap: 6px;
}
.ovv-simple-pitfalls li:last-child { border-bottom: none; }
.ovv-simple-pit-myth {
  font-family: var(--font-heading);
  font-size: 0.9375rem; color: #B8323A; font-weight: 600;
}
.ovv-simple-pit-myth::before { content: "❌ "; }
.ovv-simple-pit-reality {
  font-family: var(--font-body);
  font-size: 0.9375rem; color: var(--ink, #1A1A1A);
  line-height: 1.7;
}
.ovv-simple-pit-reality::before { content: "✓ "; color: #2E7D32; font-weight: 700; }
@media (max-width: 768px) {
  .ovv-simple-fit { grid-template-columns: 1fr; gap: 16px; }
}
"""


def render_overview_simple(data: dict) -> str:
    """渲染简化速览. 期望 data['overview_v2'] 有 {lede, what_you_learn, who_fits_yes, who_fits_no, pitfalls}."""
    ov = data.get("overview_v2", {})
    if not ov:
        return ""

    lede = ov.get("lede") or data.get("summary", "")
    what = ov.get("what_you_learn", "").strip()
    yes_list = ov.get("who_fits_yes", []) or []
    no_list = ov.get("who_fits_no", []) or []
    pitfalls = ov.get("pitfalls", []) or []

    if not lede and not what and not yes_list and not no_list and not pitfalls:
        return ""

    html = '<div class="ovv-simple">'

    # 1. lede (大段)
    if lede:
        html += f'<p class="ovv-simple-lede">{lede}</p>'

    # 2. what_you_learn (单段长文本)
    if what:
        html += '<div class="ovv-simple-section">'
        html += '<h3 class="ovv-simple-h"><span class="ovv-num">01</span>这个专业学什么?</h3>'
        html += f'<p class="ovv-simple-body">{what}</p>'
        html += '</div>'

    # 3. 适合谁 (✓/✗)
    if yes_list or no_list:
        html += '<div class="ovv-simple-section">'
        html += '<h3 class="ovv-simple-h"><span class="ovv-num">02</span>什么人适合?</h3>'
        html += '<div class="ovv-simple-fit">'
        if yes_list:
            html += '<div class="ovv-simple-fit-col is-yes">'
            html += '<div class="ovv-simple-fit-label">✓ 适合</div>'
            html += '<ul class="ovv-simple-fit-list">'
            for item in yes_list:
                html += f'<li>{item}</li>'
            html += '</ul></div>'
        if no_list:
            html += '<div class="ovv-simple-fit-col is-no">'
            html += '<div class="ovv-simple-fit-label">✗ 不适合</div>'
            html += '<ul class="ovv-simple-fit-list">'
            for item in no_list:
                html += f'<li>{item}</li>'
            html += '</ul></div>'
        html += '</div></div>'

    # 注: pitfalls 已分离为独立 page-level section (render_pitfalls_v2).
    # 修复 2026-06-22: simple format 之前在速览 inline 渲染 pitfalls, 加上 render_pitfalls_v2
    # 再渲染一次 → 同 7 条 pit 显示 2 次 (43 篇 PC HTML 中招). 改为只在独立避坑 section 渲染一次.

    html += '</div>'
    return html


def is_simple_format(data: dict) -> bool:
    """判断是否用 simple 格式 (有 what_you_learn 字段就用 simple)."""
    ov = data.get("overview_v2", {})
    if not ov:
        return False
    return bool(ov.get("what_you_learn")) or isinstance(ov.get("who_fits_yes"), list)