"""
v4_styles/themes/__init__.py — 12 主题 dispatch 表 (THEME_CSS + HERO_FN)
"""
from . import cs, finance, law, education, humanities, administration, agri, arts, gongan, business
from . import sci, eng  # sci/eng 复用 education CSS

# 主题 → CSS 字符串 (sci/eng 复用 education)
THEME_CSS = {
    "cs":             cs.CS_CSS,
    "finance":        finance.FINANCE_CSS,
    "law":            law.LAW_CSS,
    "education":      education.EDUCATION_CSS,
    "humanities":     humanities.HUMANITIES_CSS,
    "administration": administration.ADMINISTRATION_CSS,
    "agri":           agri.AGRI_CSS,
    "arts":           arts.ARTS_CSS,
    "gongan":         gongan.GONGAN_CSS,
    "business":       business.BUSINESS_CSS,
    "sci":            education.EDUCATION_CSS,   # 复用 (原 line 2805 别名)
    "eng":            education.EDUCATION_CSS,
}

# 主题 → hero 渲染函数
HERO_FN = {
    "cs":             cs.render_hero_cs,
    "finance":        finance.render_hero_finance,
    "law":            law.render_hero_law,
    "education":      education.render_hero_education,
    "humanities":     humanities.render_hero_humanities,
    "administration": administration.render_hero_administration,
    "agri":           agri.render_hero_agri,
    "arts":           arts.render_hero_arts,
    "gongan":         gongan.render_hero_gongan,
    "business":       business.render_hero_business,
    "sci":            sci.render_hero_sci,
    "eng":            eng.render_hero_eng,
}
