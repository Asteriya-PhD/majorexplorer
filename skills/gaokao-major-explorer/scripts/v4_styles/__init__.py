"""
v4_styles — 12 主题极致渲染 package (拆分自原 v4_styles.py)

公开 API (保持与原模块一致, 0 调用方改动):
- render_v4(data, style) → HTML str
- FONT_URLS: dict, 主题 → @import url
- COUNT_UP_JS: str, 数字滚动 JS
- BASE_V4_CSS: str, 8 招底层 CSS
- OVERVIEW_V2_CSS: str, 速览 v2 子卡 CSS
- get_base_css() → str
- get_body_bg_css(style) → str
- render_overview_v2(data) → str
"""
from .base import FONT_URLS, COUNT_UP_JS, BASE_V4_CSS, get_base_css
from .body_bg import get_body_bg_css
from .overview_v2 import render_overview_v2, OVERVIEW_V2_CSS
from .render import render_v4

__all__ = [
    "render_v4",
    "FONT_URLS",
    "COUNT_UP_JS",
    "BASE_V4_CSS",
    "OVERVIEW_V2_CSS",
    "get_base_css",
    "get_body_bg_css",
    "render_overview_v2",
]
