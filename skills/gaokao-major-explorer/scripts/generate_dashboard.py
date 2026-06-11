"""
scripts/generate_dashboard.py — Major Explorer v3 引擎 (Awwwards-grade v2)

v3 升级:
A. Hero 范式 — medicine 改手术仪表 (左 vital signs 滚动数字 + 右 hero), law 改法律卷宗 (顶部抬头+居中+底部 Filed)
B. 5 鼠标交互 — CS cursor 闪烁 / finance 数字闪金光 / medicine canvas 手术刀 trail / law 引文高亮 / education ❀ 漂浮
C. 5 真实感细节 — 学校/公司 monogram / quote 头像 / 数字 ≈ 标记 / 薪资 3 年变化 ↗ / 公司 sparkline 招聘趋势
"""
import argparse
import json
from pathlib import Path

# ──────────────────────────────────────────────────────────
# 5 套设计 tokens v3
# ──────────────────────────────────────────────────────────
STYLE_TOKENS = {
  "cs": {
    "name": "CS · 黑客终端",
    "fonts": {
      "heading": "'JetBrains Mono', 'SF Mono', Consolas, monospace",
      "body":    "'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', monospace",
      "cn":      "'PingFang SC', 'Microsoft YaHei', sans-serif",
      "num":     "'JetBrains Mono', 'SF Mono', monospace",
    },
    "colors": {
      "bg":          "#0B1120",
      "fg":          "#F8FAFC",
      "muted":       "#94A3B8",
      "primary":     "#22C55E",
      "primary_dim": "#16A34A",
      "primary_glow":"rgba(34, 197, 94, 0.20)",
      "surface":     "#111827",
      "surface_alt": "#1F2937",
      "border":      "#1F2937",
      "border_strong":"#334155",
      "accent":      "#22C55E",
      "accent_glow": "rgba(34, 197, 94, 0.20)",
      "monogram_bg": "#22C55E",
      "monogram_fg": "#0B1120",
      "shadow":      "0 1px 0 rgba(34, 197, 94, 0.08), 0 8px 32px rgba(0, 0, 0, 0.4)",
      "shadow_hover":"0 1px 0 rgba(34, 197, 94, 0.25), 0 12px 40px rgba(34, 197, 94, 0.15)",
    },
    "decor": "$ cat /major/{slug}.md",
    "label": "TERMINAL",
    "tagline": "编程是载体, 数学是底层",
    "hero_align": "left",
    "hero_decor_extra": "  # reading…",
    "hero_layout": "v2",
    "mouse_cursor": "text",
  },
  "humanities": {
    "name": "Humanities · 翻开的线装书",
    "fonts": {
      "heading": "'Noto Serif SC', 'Songti SC', 'Source Han Serif SC', serif",
      "body":    "'Noto Serif SC', 'Cormorant Garamond', 'PingFang SC', serif",
      "cn":      "'Noto Serif SC', 'Songti SC', 'PingFang SC', serif",
      "num":     "'Cormorant Garamond', 'Noto Serif SC', serif",
    },
    "colors": {
      "bg":          "#F2E8D5",
      "fg":          "#1F140A",
      "muted":       "#6B5D3F",
      "primary":     "#8B5A2B",
      "primary_dim": "#6B4226",
      "primary_glow":"rgba(184, 137, 58, 0.20)",
      "surface":     "#FBF6E9",
      "surface_alt": "#F2E8D5",
      "border":      "#C5B89A",
      "border_strong":"#8B5A2B",
      "accent":      "#9A2A2A",
      "accent_glow": "rgba(154, 42, 42, 0.20)",
      "monogram_bg": "#1F140A",
      "monogram_fg": "#F2E8D5",
      "shadow":      "0 1px 0 rgba(139, 90, 43, 0.04), 0 4px 12px rgba(31, 20, 10, 0.10)",
      "shadow_hover":"0 1px 0 rgba(139, 90, 43, 0.10), 0 8px 24px rgba(31, 20, 10, 0.15)",
    },
    "decor": "「{title}」",
    "label": "ARCHIVE",
    "tagline": "深棕墨 + 米白宣纸 + 古籍线装",
    "hero_align": "center",
    "hero_decor_extra": " · 嶽麓藏版",
    "hero_layout": "v2",
    "mouse_cursor": "default",
  },
  "administration": {
    "name": "Administration · 国发文件",
    "fonts": {
      "heading": "'Noto Serif SC', 'IBM Plex Serif', 'Songti SC', serif",
      "body":    "'IBM Plex Serif', 'Noto Serif SC', 'PingFang SC', serif",
      "cn":      "'Noto Serif SC', 'Songti SC', 'PingFang SC', serif",
      "num":     "'IBM Plex Mono', 'Noto Serif SC', monospace",
    },
    "colors": {
      "bg":          "#FAFAF6",
      "fg":          "#1A2438",
      "muted":       "#5A6A7A",
      "primary":     "#1E3A5F",
      "primary_dim": "#0F2540",
      "primary_glow":"rgba(30, 58, 95, 0.10)",
      "surface":     "#FFFFFF",
      "surface_alt": "#F2EDE0",
      "border":      "#C5C5B5",
      "border_strong":"#1E3A5F",
      "accent":      "#C0392B",
      "accent_glow": "rgba(192, 57, 43, 0.20)",
      "monogram_bg": "#1E3A5F",
      "monogram_fg": "#FAFAF6",
      "shadow":      "0 1px 0 rgba(30, 58, 95, 0.04), 0 4px 12px rgba(30, 58, 95, 0.06)",
      "shadow_hover":"0 1px 0 rgba(30, 58, 95, 0.10), 0 8px 24px rgba(30, 58, 95, 0.10)",
    },
    "decor": "〔{title}〕",
    "label": "DOSSIER",
    "tagline": "政府蓝 + 米白 + 国发文件 + 红头印章",
    "hero_align": "center",
    "hero_decor_extra": " · 教育部",
    "hero_layout": "v2",
    "mouse_cursor": "default",
  },
  "agri": {
    "name": "Agri · 林奈式植物图鉴",
    "fonts": {
      "heading": "'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif",
      "body":    "'Cormorant Garamond', 'Noto Serif SC', 'PingFang SC', serif",
      "cn":      "'Noto Serif SC', 'ZCOOL XiaoWei', 'PingFang SC', serif",
      "num":     "'Cormorant Garamond', 'Noto Serif SC', serif",
    },
    "colors": {
      "bg":          "#F5F9EC",
      "fg":          "#2E5A2E",
      "muted":       "#A0824D",
      "primary":     "#6B8E23",
      "primary_dim": "#2E5A2E",
      "primary_glow":"rgba(107, 142, 35, 0.15)",
      "surface":     "#F5F9EC",
      "surface_alt": "#E8EFDC",
      "border":      "#C5D9A8",
      "border_strong":"#6B8E23",
      "accent":      "#E6B422",
      "accent_glow": "rgba(230, 180, 34, 0.20)",
      "monogram_bg": "#2E5A2E",
      "monogram_fg": "#F5F9EC",
      "shadow":      "0 1px 0 rgba(107, 142, 35, 0.06), 0 4px 12px rgba(46, 90, 46, 0.10)",
      "shadow_hover":"0 1px 0 rgba(107, 142, 35, 0.12), 0 8px 24px rgba(46, 90, 46, 0.18)",
    },
    "decor": "「{title}」",
    "label": "AGRI-BOTANY",
    "tagline": "嫩芽白 + 橄榄叶绿 + 林奈式植物图鉴",
    "hero_align": "center",
    "hero_decor_extra": " · 華北農學會藏版",
    "hero_layout": "v2",
    "mouse_cursor": "default",
  },
  "arts": {
    "name": "Arts · 画室工作台",
    "fonts": {
      "heading": "'Cormorant Garamond', 'Noto Serif SC', serif",
      "body":    "'Noto Serif SC', 'Archivo', 'PingFang SC', sans-serif",
      "cn":      "'Noto Serif SC', 'Songti SC', 'PingFang SC', serif",
      "num":     "'Cormorant Garamond', 'Noto Serif SC', serif",
    },
    "colors": {
      "bg":          "#F5F0E8",
      "fg":          "#1A1A1A",
      "muted":       "#6B6B6B",
      "primary":     "#1A1A1A",
      "primary_dim": "#0A0A0A",
      "primary_glow":"rgba(26, 26, 26, 0.10)",
      "surface":     "#FAFAFA",
      "surface_alt": "#EBE3D4",
      "border":      "#1A1A1A",
      "border_strong":"#000000",
      "accent":      "#DC2626",
      "accent_glow": "rgba(220, 38, 38, 0.20)",
      "monogram_bg": "#1A1A1A",
      "monogram_fg": "#FAFAFA",
      "shadow":      "0 1px 0 rgba(0, 0, 0, 0.08), 0 8px 32px rgba(0, 0, 0, 0.40)",
      "shadow_hover":"0 1px 0 rgba(0, 0, 0, 0.15), 0 12px 40px rgba(220, 38, 38, 0.20)",
    },
    "decor": "「{title}」",
    "label": "STUDIO OF MAKING",
    "tagline": "炭黑 + 米白画布 + 调色板 + 包豪斯抽象画",
    "hero_align": "left",
    "hero_decor_extra": " · No. 042",
    "hero_layout": "v2",
    "mouse_cursor": "default",
  },
  "gongan": {
    "name": "Gongan · 国际司法范式 (盾+十字剑+橄榄枝)",
    "fonts": {
      "heading": "'Cinzel', 'Noto Serif SC', serif",
      "body":    "'Noto Serif SC', 'Inter', 'PingFang SC', sans-serif",
      "cn":      "'Noto Serif SC', 'Songti SC', 'PingFang SC', serif",
      "num":     "'Oswald', 'JetBrains Mono', monospace",
    },
    "colors": {
      "bg":          "#0A1420",
      "fg":          "#FAFAF6",
      "muted":       "#94A3B8",
      "primary":     "#D4AF37",
      "primary_dim": "#B8902A",
      "primary_glow":"rgba(212, 175, 55, 0.25)",
      "surface":     "#0F1F33",
      "surface_alt": "#1E3A5F",
      "border":      "rgba(212, 175, 55, 0.30)",
      "border_strong":"#D4AF37",
      "accent":      "#B91C1C",
      "accent_glow": "rgba(185, 28, 28, 0.30)",
      "monogram_bg": "#D4AF37",
      "monogram_fg": "#0F1F33",
      "shadow":      "0 1px 0 rgba(212, 175, 55, 0.10), 0 8px 32px rgba(0, 0, 0, 0.5)",
      "shadow_hover":"0 1px 0 rgba(212, 175, 55, 0.25), 0 12px 40px rgba(185, 28, 28, 0.20)",
    },
    "decor": "CASE No.{slug}",
    "label": "PUBLIC SECURITY",
    "tagline": "警蓝 + 国徽金 + 朱红 + 盾·十字剑·橄榄枝",
    "hero_align": "center",
    "hero_decor_extra": " · PSA-2026",
    "hero_layout": "v2",
    "mouse_cursor": "default",
  },
  "business": {
    "name": "Business · 椭圆董事局 (玫瑰金+胡桃木)",
    "fonts": {
      "heading": "'Bodoni Moda', 'Noto Serif SC', serif",
      "body":    "'Inter', 'Noto Serif SC', 'PingFang SC', sans-serif",
      "cn":      "'Noto Serif SC', 'Songti SC', 'PingFang SC', serif",
      "num":     "'JetBrains Mono', 'Bebas Neue', monospace",
    },
    "colors": {
      "bg":          "#FAFAF6",
      "fg":          "#1A1A1A",
      "muted":       "#5C6770",
      "primary":     "#C77B5C",
      "primary_dim": "#9C4A35",
      "primary_glow":"rgba(199, 123, 92, 0.20)",
      "surface":     "#FFFFFF",
      "surface_alt": "#F5F0E5",
      "border":      "#E5DCC8",
      "border_strong":"#C77B5C",
      "accent":      "#6B1F2A",
      "accent_glow": "rgba(107, 31, 42, 0.18)",
      "monogram_bg": "#1A1A1A",
      "monogram_fg": "#C77B5C",
      "shadow":      "0 1px 0 rgba(62, 42, 31, 0.06), 0 8px 24px rgba(62, 42, 31, 0.10)",
      "shadow_hover":"0 1px 0 rgba(199, 123, 92, 0.18), 0 12px 36px rgba(199, 123, 92, 0.18)",
    },
    "decor": "Boardroom No.{slug}",
    "label": "STRATEGIC BOARDROOM",
    "tagline": "玫瑰金 + 胡桃木 + 屏幕深蓝 + 8 椅董事局",
    "hero_align": "center",
    "hero_decor_extra": " · BUS-2026",
    "hero_layout": "v2",
    "mouse_cursor": "default",
  },
  "finance": {
    "name": "金融 · 高贵精致",
    "fonts": {
      "heading": "'Bodoni Moda', 'Source Han Serif SC', 'Songti SC', serif",
      "body":    "'Jost', 'PingFang SC', 'Microsoft YaHei', sans-serif",
      "cn":      "'PingFang SC', 'Microsoft YaHei', sans-serif",
      "num":     "'Bodoni Moda', 'Source Han Serif SC', serif",
    },
    "colors": {
      "bg":          "#FAFAF9",
      "fg":          "#0C0A09",
      "muted":       "#78716C",
      "primary":     "#1C1917",
      "primary_dim": "#44403C",
      "primary_glow":"rgba(161, 98, 7, 0.08)",
      "surface":     "#FFFFFF",
      "surface_alt": "#F5F5F4",
      "border":      "#E7E5E4",
      "border_strong":"#D6D3D1",
      "accent":      "#A16207",
      "accent_glow": "rgba(161, 98, 7, 0.10)",
      "monogram_bg": "#1C1917",
      "monogram_fg": "#FAFAF9",
      "shadow":      "0 1px 2px rgba(28, 25, 23, 0.04), 0 1px 0 rgba(28, 25, 23, 0.02)",
      "shadow_hover":"0 4px 12px rgba(28, 25, 23, 0.08), 0 1px 0 rgba(161, 98, 7, 0.10)",
    },
    "decor": "—— {title} ——",
    "label": "PRIVATE WEALTH",
    "tagline": "资金的时间价值 × 风险定价",
    "hero_align": "center",
    "hero_decor_extra": "",
    "hero_layout": "v2",
    "mouse_cursor": "default",
  },
  "medicine": {
    "name": "医学 · 手术室仪器",
    "fonts": {
      "heading": "'Inter', 'PingFang SC', sans-serif",
      "body":    "'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif",
      "cn":      "'PingFang SC', 'Microsoft YaHei', sans-serif",
      "num":     "'Inter', 'SF Mono', monospace",
    },
    "colors": {
      "bg":          "#F8FAFC",
      "fg":          "#0F172A",
      "muted":       "#475569",
      "primary":     "#0C4A6E",
      "primary_dim": "#0369A1",
      "primary_glow":"rgba(12, 74, 110, 0.08)",
      "surface":     "#FFFFFF",
      "surface_alt": "#F1F5F9",
      "border":      "#CBD5E1",
      "border_strong":"#94A3B8",
      "accent":      "#0C4A6E",
      "accent_red":  "#DC2626",
      "monogram_bg": "#0C4A6E",
      "monogram_fg": "#FFFFFF",
      "shadow":      "0 1px 0 rgba(15, 23, 42, 0.04), 0 1px 3px rgba(15, 23, 42, 0.04)",
      "shadow_hover":"0 2px 0 rgba(12, 74, 110, 0.08), 0 8px 24px rgba(12, 74, 110, 0.10)",
    },
    "decor": "▶ {title}",
    "label": "EVIDENCE-BASED",
    "tagline": "严谨 · 冷静 · 鸟瞰",
    "hero_align": "left",
    "hero_decor_extra": " · MAYO-CLINIC-STANDARD",
    "hero_layout": "vitals",   # ← NEW! 手术仪表
    "show_ecg": True,
    "mouse_cursor": "scalpel",  # ← NEW! canvas trail
    "vitals": [
      {"key": "HR",   "label": "心率",    "value": "72",   "unit": "bpm",  "range": "60-100"},
      {"key": "SpO2", "label": "血氧",    "value": "98",   "unit": "%",    "range": "95-100"},
      {"key": "Temp", "label": "体温",    "value": "36.6", "unit": "°C",   "range": "36.1-37.2"},
      {"key": "RR",   "label": "呼吸",    "value": "16",   "unit": "/min", "range": "12-20"},
    ],
  },
  "law": {
    "name": "法学 · 羊皮卷宗",
    "fonts": {
      "heading": "'EB Garamond', 'Source Han Serif SC', 'Songti SC', serif",
      "body":    "'Lato', 'PingFang SC', sans-serif",
      "cn":      "'PingFang SC', 'Microsoft YaHei', sans-serif",
      "num":     "'EB Garamond', 'Source Han Serif SC', serif",
    },
    "colors": {
      "bg":          "#FFFBEB",
      "fg":          "#1C1917",
      "muted":       "#57534E",
      "primary":     "#78350F",
      "primary_dim": "#92400E",
      "primary_glow":"rgba(120, 53, 15, 0.08)",
      "surface":     "#FFFFFF",
      "surface_alt": "#FEF3C7",
      "border":      "#E7E5E4",
      "border_strong":"#D6D3D1",
      "accent":      "#D97706",
      "accent_glow": "rgba(217, 119, 6, 0.12)",
      "monogram_bg": "#78350F",
      "monogram_fg": "#FFFBEB",
      "shadow":      "0 1px 2px rgba(120, 53, 15, 0.04)",
      "shadow_hover":"0 4px 16px rgba(120, 53, 15, 0.10)",
    },
    "decor": "§ {title} §",
    "label": "ARTICLE I",
    "tagline": "逻辑 · 表达 · 立场",
    "hero_align": "center",
    "hero_decor_extra": "",
    "hero_layout": "docket",  # ← NEW! 法律卷宗
    "mouse_cursor": "highlight",  # ← NEW! hover highlight
    "case_no": "CASE NO. 2026-HE-{n:03d}",
    "filed_at": "FILED: 2026-06-08 14:32 UTC+8",
  },
  "education": {
    "name": "教育 · 暖橙学术",
    "fonts": {
      "heading": "'Playfair Display', 'Source Han Serif SC', 'Songti SC', serif",
      "body":    "'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif",
      "cn":      "'PingFang SC', 'Microsoft YaHei', sans-serif",
      "num":     "'Inter', 'SF Mono', monospace",
    },
    "colors": {
      "bg":          "#FFFBEB",
      "fg":          "#1C1917",
      "muted":       "#78716C",
      "primary":     "#9A3412",
      "primary_dim": "#C2410C",
      "primary_glow":"rgba(154, 52, 18, 0.08)",
      "surface":     "#FFF7ED",
      "surface_alt": "#FED7AA",
      "border":      "#FDBA74",
      "border_strong":"#FB923C",
      "accent":      "#F59E0B",
      "accent_glow": "rgba(245, 158, 11, 0.12)",
      "monogram_bg": "#9A3412",
      "monogram_fg": "#FFFBEB",
      "shadow":      "0 1px 2px rgba(154, 52, 18, 0.04), 0 1px 0 rgba(245, 158, 11, 0.04)",
      "shadow_hover":"0 4px 12px rgba(154, 52, 18, 0.10), 0 1px 0 rgba(245, 158, 11, 0.10)",
    },
    "decor": "❀  {title}  ❀",
    "label": "EDUCATIO",
    "tagline": "研究'怎么学'的科学",
    "hero_align": "center",
    "hero_decor_extra": "",
    "hero_layout": "v2",
    "mouse_cursor": "flower",  # ← NEW! flower floating
  },
  "sci": {
    "name": "Sci · 米色学术 (Nature 风)",
    "fonts": {
      "heading": "'EB Garamond', 'Source Han Serif SC', 'Songti SC', serif",
      "body":    "'Lora', 'Source Han Serif SC', serif",
      "cn":      "'PingFang SC', 'Microsoft YaHei', serif",
      "num":     "'Crimson Pro', 'EB Garamond', serif",
    },
    "colors": {
      "bg":          "#EDE3CC",
      "fg":          "#1F1B12",
      "muted":       "#786A4F",
      "primary":     "#C73E1D",
      "primary_dim": "#A02E15",
      "primary_glow":"rgba(199, 62, 29, 0.06)",
      "surface":     "#F6EFD9",
      "surface_alt": "#E5D8B5",
      "border":      "rgba(31, 27, 18, 0.18)",
      "border_strong":"rgba(31, 27, 18, 0.45)",
      "accent":      "#2D5F4E",
      "accent_glow": "rgba(45, 95, 78, 0.10)",
      "monogram_bg": "#C73E1D",
      "monogram_fg": "#F6EFD9",
      "shadow":      "0 1px 0 rgba(199, 62, 29, 0.04), 0 4px 12px rgba(31, 27, 18, 0.06)",
      "shadow_hover":"0 2px 0 rgba(199, 62, 29, 0.10), 0 8px 24px rgba(199, 62, 29, 0.08)",
    },
    "decor": "VOL. 50 · NO. 03 · {title}",
    "label": "PEER-REVIEWED",
    "tagline": "白纸墨字红印章 — 学术期刊的庄重",
    "hero_align": "left",
    "hero_decor_extra": " · 2026 SPRING",
    "hero_layout": "v2",
    "mouse_cursor": "default",
  },
  "eng": {
    "name": "Eng · 浅米工程 (CAD 蓝图风)",
    "fonts": {
      "heading": "'Inter', 'PingFang SC', sans-serif",
      "body":    "'Source Sans 3', 'PingFang SC', sans-serif",
      "cn":      "'PingFang SC', 'Microsoft YaHei', sans-serif",
      "num":     "'Roboto Mono', 'JetBrains Mono', monospace",
    },
    "colors": {
      "bg":          "#F5F2EA",
      "fg":          "#1A1F2E",
      "muted":       "#5C6373",
      "primary":     "#1B3A5C",
      "primary_dim": "#0F2640",
      "primary_glow":"rgba(27, 58, 92, 0.08)",
      "surface":     "#FFFFFF",
      "surface_alt": "#EDE7DA",
      "border":      "rgba(27, 58, 92, 0.20)",
      "border_strong":"rgba(27, 58, 92, 0.50)",
      "accent":      "#FF6B35",
      "accent_glow": "rgba(255, 107, 53, 0.15)",
      "monogram_bg": "#1B3A5C",
      "monogram_fg": "#F5F2EA",
      "shadow":      "0 1px 0 rgba(27, 58, 92, 0.04), 0 4px 12px rgba(27, 58, 92, 0.06)",
      "shadow_hover":"0 2px 0 rgba(255, 107, 53, 0.10), 0 8px 24px rgba(27, 58, 92, 0.10)",
    },
    "decor": "DWG-{slug}-2026-003 · {title}",
    "label": "BLUEPRINT",
    "tagline": "蓝图蓝 + 安全橙 + 公差精度",
    "hero_align": "left",
    "hero_decor_extra": " · A4 LANDSCAPE",
    "hero_layout": "v2",
    "mouse_cursor": "default",
  },
}

# 国内部署: 已将 Google Fonts 替换为 fonts.loli.net 镜像 (国内可访问)
# 海外部署可改回: https://fonts.googleapis.com
FONT_URLS = {
  "cs":        "@import url('https://fonts.loli.net/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');",
  "humanities":    "@import url('https://fonts.loli.net/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&family=Ma+Shan+Zheng&family=ZCOOL+XiaoWei&family=Long+Cang&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap');",
  "administration": "@import url('https://fonts.loli.net/css2?family=IBM+Plex+Serif:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@300;400;500&family=Noto+Serif+SC:wght@400;500;600;700;900&display=swap');",
  "finance":   "@import url('https://fonts.loli.net/css2?family=Bodoni+Moda:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Jost:wght@300;400;500;600;700&display=swap');",
  "medicine":  "@import url('https://fonts.loli.net/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');",
  "law":       "@import url('https://fonts.loli.net/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Lato:wght@300;400;700&display=swap');",
  "education": "@import url('https://fonts.loli.net/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap');",
  "agri":  "@import url('https://fonts.loli.net/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Noto+Serif+SC:wght@400;500;600;700;900&family=ZCOOL+XiaoWei&display=swap');",
  "arts":  "@import url('https://fonts.loli.net/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Noto+Serif+SC:wght@400;500;600;700;900&family=Archivo:wght@400;500;600;700;800;900&display=swap');",
  "gongan":  "@import url('https://fonts.loli.net/css2?family=Cinzel:wght@500;600;700;800&family=Cormorant+Unicase:wght@500;600;700&family=Noto+Serif+SC:wght@300;400;500;600;700;900&family=Oswald:wght@500;600;700&family=Inter:wght@300;400;500;600;700&family=Long+Cang&display=swap');",
  "business":"@import url('https://fonts.loli.net/css2?family=Bodoni+Moda:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Bebas+Neue&display=swap');",
}

# ──────────────────────────────────────────────────────────
# 共享 BASE CSS v3
# ──────────────────────────────────────────────────────────
BASE_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }
body {
  font-family: var(--font-body);
  background: var(--bg);
  color: var(--fg);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-feature-settings: 'kern' 1, 'liga' 1;
}
img, svg { max-width: 100%; display: block; }
button { font: inherit; cursor: pointer; border: none; background: none; }
a { color: inherit; text-decoration: none; transition: opacity 200ms; }
a:hover { opacity: 0.65; }

.display { font-size: clamp(3.25rem, 7vw, 5.5rem); font-weight: 600; letter-spacing: -0.03em; line-height: 1.05; }
.h1      { font-size: clamp(2.25rem, 5vw, 3.5rem); font-weight: 600; letter-spacing: -0.02em; line-height: 1.15; }
.h2      { font-size: clamp(1.75rem, 3vw, 2.25rem); font-weight: 600; letter-spacing: -0.01em; line-height: 1.25; }
.h3      { font-size: 1.25rem; font-weight: 600; line-height: 1.4; }
.body    { font-size: 1rem; line-height: 1.65; }
.body-sm { font-size: 0.9375rem; line-height: 1.6; }
.caption { font-size: 0.8125rem; line-height: 1.5; }
.label   { font-size: 0.6875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.15em; }
h1, h2, h3, h4 { font-family: var(--font-heading); }

.num, .num * { font-variant-numeric: tabular-nums; font-feature-settings: 'tnum' 1, 'lnum' 1; font-family: var(--font-num); }

.container { max-width: 1120px; margin: 0 auto; padding: 0 32px; }
@media (max-width: 768px) { .container { padding: 0 20px; } }

/* ── v2 hero (CS/finance/education) ── */
.hero { padding: 128px 0 96px; position: relative; border-bottom: 1px solid var(--border); overflow: hidden; }
.hero.center { text-align: center; }
.hero.left   { text-align: left; }
.hero-decor {
  font-family: var(--font-body);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  margin-bottom: 32px;
  display: flex; align-items: center; gap: 8px;
}
.hero.center .hero-decor { justify-content: center; }
.hero-decor::before { content: ""; display: inline-block; width: 32px; height: 1px; background: var(--accent); opacity: 0.4; }
.hero h1.display { margin-bottom: 24px; }
.hero-tagline { font-size: 1.125rem; color: var(--muted); margin-bottom: 40px; max-width: 640px; line-height: 1.7; }
.hero.center .hero-tagline { margin-left: auto; margin-right: auto; }
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 48px; }
.hero.center .hero-tags { justify-content: center; }
.tag {
  padding: 5px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--fg);
  letter-spacing: 0.02em;
}
.tag.primary { background: transparent; border-color: var(--accent); color: var(--accent); }

.hero-stats {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.hero.center .hero-stats { border-left: 1px solid var(--border); border-right: 1px solid var(--border); }
@media (max-width: 768px) { .hero-stats { grid-template-columns: repeat(2, 1fr); } }
.stat { padding: 24px 28px; border-right: 1px solid var(--border); position: relative; }
.stat:last-child { border-right: none; }
@media (max-width: 768px) { .stat:nth-child(2) { border-right: none; } .stat:nth-child(1), .stat:nth-child(2) { border-bottom: 1px solid var(--border); } }
.stat-label { font-size: 0.6875rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.12em; font-weight: 500; }
.stat-value { font-family: var(--font-heading); font-size: 1.5rem; font-weight: 600; color: var(--fg); margin-top: 6px; letter-spacing: -0.01em; }

/* ── v3 hero: vitals (medicine) ── */
.hero.vitals { padding: 96px 0 80px; }
.hero.vitals .container {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 64px;
  align-items: center;
}
@media (max-width: 900px) { .hero.vitals .container { grid-template-columns: 1fr; gap: 32px; } }
.vitals-panel {
  padding: 32px 28px;
  background: var(--surface);
  border: 1px solid var(--border_strong);
  border-radius: 16px;
  box-shadow: 0 4px 32px rgba(12, 74, 110, 0.10);
  position: relative;
}
.vitals-panel::before {
  content: "VITAL SIGNS · PATIENT-MONITOR";
  position: absolute; top: -10px; left: 16px;
  background: var(--bg);
  padding: 0 8px;
  font-family: var(--font-num);
  font-size: 0.625rem;
  color: var(--accent);
  letter-spacing: 0.15em;
  font-weight: 600;
}
.vitals-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.vitals-time { font-family: var(--font-num); font-size: 0.75rem; color: var(--muted); letter-spacing: 0.1em; }
.vitals-status { display: flex; align-items: center; gap: 6px; font-family: var(--font-num); font-size: 0.75rem; color: var(--accent); font-weight: 600; letter-spacing: 0.08em; }
.vitals-status::before { content: ""; width: 8px; height: 8px; background: var(--accent); border-radius: 50%; animation: pulse 1.5s infinite; }
.vitals-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.vital {
  padding: 16px 14px;
  background: var(--surface_alt);
  border-radius: 10px;
  position: relative;
}
.vital-label { font-family: var(--font-num); font-size: 0.6875rem; color: var(--muted); letter-spacing: 0.15em; font-weight: 600; }
.vital-value { font-family: var(--font-num); font-size: 2.25rem; font-weight: 700; color: var(--fg); line-height: 1; margin-top: 4px; letter-spacing: -0.02em; }
.vital-unit  { font-family: var(--font-num); font-size: 0.75rem; color: var(--muted); margin-left: 4px; font-weight: 500; }
.vital-range { font-family: var(--font-num); font-size: 0.625rem; color: var(--muted); margin-top: 4px; letter-spacing: 0.05em; }
.vital.heart .vital-value { color: var(--accent_red); }
.vital-body .vital-content { display: flex; align-items: baseline; }
.hero-vitals-side { display: flex; flex-direction: column; }

/* ── v3 hero: docket (law) ── */
.hero.docket { padding: 80px 0 64px; }
.docket-header {
  text-align: center;
  margin-bottom: 48px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--border);
}
.docket-court {
  font-family: var(--font-num);
  font-size: 0.75rem;
  color: var(--muted);
  letter-spacing: 0.25em;
  text-transform: uppercase;
  font-weight: 500;
  margin-bottom: 12px;
}
.docket-title-wrap { display: flex; align-items: center; justify-content: center; gap: 24px; margin-bottom: 16px; }
.docket-line { flex: 0 0 80px; height: 1px; background: var(--accent); opacity: 0.4; }
.docket-title { font-family: var(--font-heading); font-size: 0.875rem; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; }
.hero.docket h1.display { text-align: center; font-style: italic; }
.docket-meta {
  display: flex; justify-content: space-between;
  margin-top: 32px;
  font-family: var(--font-num);
  font-size: 0.6875rem;
  color: var(--muted);
  letter-spacing: 0.15em;
  text-transform: uppercase;
}
@media (max-width: 768px) { .docket-meta { flex-direction: column; gap: 8px; align-items: center; } }
.docket-stamp {
  position: absolute; top: 32px; right: 32px;
  width: 80px; height: 80px;
  border: 2px solid var(--accent_red);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: var(--accent_red);
  font-family: var(--font-num);
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-align: center;
  line-height: 1.2;
  transform: rotate(12deg);
  opacity: 0.7;
  text-transform: uppercase;
}

/* ── sections ── */
section.tab { padding: 96px 0; border-bottom: 1px solid var(--border); opacity: 0; transform: translateY(20px); transition: opacity 800ms cubic-bezier(0.16, 1, 0.3, 1), transform 800ms cubic-bezier(0.16, 1, 0.3, 1); }
section.tab.visible { opacity: 1; transform: translateY(0); }
section.tab:last-of-type { border-bottom: none; }
.section-num { font-family: var(--font-num); font-size: 0.75rem; font-weight: 500; color: var(--accent); letter-spacing: 0.2em; margin-bottom: 16px; text-transform: uppercase; }
section.tab h2.h2 { margin-bottom: 24px; }
section.tab h3.h3 { margin: 40px 0 12px; }
section.tab p { margin-bottom: 16px; color: var(--fg); }
section.tab p.lede { color: var(--muted); font-size: 1rem; line-height: 1.7; max-width: 720px; margin-bottom: 32px; }

/* ── bento grid (院校) ── */
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1px; margin-top: 32px; background: var(--border); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; }
.bento-item { padding: 28px 24px 24px; background: var(--surface); position: relative; transition: background 200ms ease-out; }
.bento-item:hover { background: var(--surface_alt); }
.bento-monogram { position: absolute; top: 20px; right: 20px; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-family: var(--font-heading); font-size: 1rem; font-weight: 700; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: var(--accent); border: 1px solid var(--accent); border-radius: 4px; font-family: var(--font-num); font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.08em; margin-bottom: 12px; }
.bento-name { font-family: var(--font-heading); font-size: 1.0625rem; font-weight: 600; margin-bottom: 4px; letter-spacing: -0.01em; padding-right: 44px; }
.bento-tag { font-size: 0.8125rem; color: var(--muted); line-height: 1.5; }

/* ── company cards (头部公司) ── */
.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 32px; }
.company { padding: 24px 22px 18px; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; position: relative; transition: box-shadow 250ms, transform 250ms, border-color 250ms; }
.company:hover { box-shadow: var(--shadow_hover); transform: translateY(-2px); border-color: var(--border_strong); }
.company-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.company-monogram { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-family: var(--font-heading); font-size: 1.125rem; font-weight: 700; flex-shrink: 0; }
.company-tier { padding: 2px 8px; border-radius: 4px; font-family: var(--font-num); font-size: 0.625rem; font-weight: 700; letter-spacing: 0.08em; }
.tier-S { background: var(--accent); color: var(--bg); }
.tier-A { background: transparent; color: var(--accent); border: 1px solid var(--accent); }
.tier-B { background: var(--surface_alt); color: var(--muted); }
.company-name { font-family: var(--font-heading); font-size: 1.0625rem; font-weight: 600; margin-bottom: 8px; }
.company-meta { font-size: 0.8125rem; color: var(--muted); line-height: 1.5; margin-bottom: 12px; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border); }
.sparkline-bar { flex: 1; background: var(--border); border-radius: 1px; transition: background 250ms; min-height: 2px; }
.company:hover .sparkline-bar { background: var(--accent); opacity: 0.6; }
.sparkline-label { font-family: var(--font-num); font-size: 0.625rem; color: var(--muted); letter-spacing: 0.1em; margin-top: 4px; }

/* ── salary table ── */
.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.salary-table th, .salary-table td { padding: 18px 24px; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.9375rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: var(--surface_alt); font-family: var(--font-body); font-weight: 500; font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); }
.salary-table td { font-family: var(--font-num); }
.salary-stage { font-weight: 600; color: var(--fg); }
.salary-bar { display: inline-block; width: 80px; height: 6px; background: var(--surface_alt); border-radius: 3px; margin-left: 8px; vertical-align: middle; position: relative; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: var(--accent); border-radius: 3px; }
.yoy { display: inline-block; font-family: var(--font-num); font-size: 0.75rem; font-weight: 600; margin-left: 12px; padding: 2px 6px; border-radius: 4px; }
.yoy.up   { color: #15803D; background: rgba(21, 128, 61, 0.08); }
.yoy.down { color: #B91C1C; background: rgba(185, 28, 28, 0.08); }
.yoy.flat { color: var(--muted); background: var(--surface_alt); }
.approx { font-family: var(--font-num); color: var(--muted); margin-right: 4px; }

/* ── direction bars ── */
.direction-list { margin-top: 32px; max-width: 720px; }
.direction { display: grid; grid-template-columns: 160px 1fr 60px; align-items: center; gap: 20px; padding: 14px 0; border-bottom: 1px solid var(--border); }
.direction:last-child { border-bottom: none; }
.direction-name { font-weight: 500; font-size: 0.9375rem; }
.direction-bar { height: 10px; background: var(--surface_alt); border-radius: 5px; overflow: hidden; position: relative; }
.direction-bar-fill { height: 100%; background: var(--accent); border-radius: 5px; transition: width 1s cubic-bezier(0.16, 1, 0.3, 1); }
.direction-pct { font-family: var(--font-num); font-weight: 600; text-align: right; font-size: 0.9375rem; color: var(--fg); }

/* ── deep study cards ── */
.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-top: 32px; }
.path-card { padding: 32px 24px; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; text-align: center; transition: box-shadow 250ms, transform 250ms, border-color 250ms; }
.path-card:hover { box-shadow: var(--shadow_hover); transform: translateY(-2px); border-color: var(--border_strong); }
.path-pct { font-family: var(--font-num); font-size: 2.5rem; font-weight: 600; color: var(--accent); margin-bottom: 4px; letter-spacing: -0.02em; line-height: 1; }
.path-name { color: var(--muted); font-size: 0.8125rem; letter-spacing: 0.02em; margin-top: 8px; }

/* ── quotes (with avatar) ── */
.quotes { margin-top: 32px; }
.quote { padding: 28px 32px 24px; background: var(--surface); border: 1px solid var(--border); border-left: 2px solid var(--accent); border-radius: 0 12px 12px 0; margin-bottom: 16px; position: relative; transition: border-left-width 200ms, background 200ms, transform 200ms; }
.quote-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.quote-avatar { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: var(--font-heading); font-size: 1rem; font-weight: 600; flex-shrink: 0; }
.quote-byline { font-size: 0.875rem; }
.quote-byline strong { font-weight: 500; color: var(--fg); display: block; }
.quote-byline .quote-source { color: var(--muted); font-size: 0.75rem; font-family: var(--font-num); }
.quote-text { font-family: var(--font-heading); font-size: 1.1875rem; line-height: 1.7; font-style: italic; margin: 0; color: var(--fg); font-weight: 400; }
.quote-text::before { content: "\\201C"; color: var(--accent); font-size: 1.4em; line-height: 0; vertical-align: -0.2em; margin-right: 4px; }
.quote-text::after { content: "\\201D"; color: var(--accent); font-size: 1.4em; line-height: 0; vertical-align: -0.2em; margin-left: 4px; }

/* ── xuanke ── */
.xuanke-list { margin-top: 32px; max-width: 720px; }
.xuanke { display: grid; grid-template-columns: 200px 1fr 80px; align-items: center; gap: 20px; padding: 14px 0; border-bottom: 1px solid var(--border); }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-weight: 500; font-size: 0.9375rem; }
.xuanke-bar { height: 8px; background: var(--surface_alt); border-radius: 4px; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: var(--accent); border-radius: 4px; }
.xuanke-pct { font-family: var(--font-num); font-weight: 600; text-align: right; font-size: 0.9375rem; }

/* ── curriculum ── */
.curriculum-lede { color: var(--muted); font-size: 0.9375rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-top: 32px; }
.curriculum-block { padding: 28px 24px; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; }
.curriculum-title { font-family: var(--font-body); font-size: 0.6875rem; color: var(--accent); text-transform: uppercase; letter-spacing: 0.15em; font-weight: 600; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.course { padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; font-size: 0.9375rem; border-bottom: 1px dashed transparent; transition: border-color 200ms; position: relative; }
.course:hover { border-bottom-color: var(--border); }
.course-name { color: var(--fg); }
.course-credit { color: var(--muted); font-family: var(--font-num); font-size: 0.75rem; margin-left: 8px; }

/* ── timeline ── */
.timeline { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0; margin-top: 32px; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.tl-item { padding: 32px 24px; background: var(--surface); border-right: 1px solid var(--border); position: relative; }
.tl-item:last-child { border-right: none; }
.tl-year { font-family: var(--font-num); font-size: 1.5rem; font-weight: 600; color: var(--accent); margin-bottom: 8px; letter-spacing: -0.01em; }
.tl-stage { font-family: var(--font-heading); font-size: 1.0625rem; font-weight: 600; margin-bottom: 8px; }
.tl-income { font-size: 0.8125rem; color: var(--muted); line-height: 1.5; }

/* ── cta ── */
.cta-block { margin-top: 32px; padding: 56px 48px; background: var(--surface); border: 1px solid var(--border); border-radius: 16px; text-align: center; }
.cta-block h3.h3 { font-family: var(--font-heading); font-size: 1.5rem; margin-bottom: 12px; color: var(--fg); }
.cta-block p { color: var(--muted); margin-bottom: 28px; max-width: 560px; margin-left: auto; margin-right: auto; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin-bottom: 16px; }
.cta-input { padding: 14px 18px; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; color: var(--fg); font-family: var(--font-num); font-size: 1rem; width: 180px; outline: none; transition: border-color 200ms; }
.cta-input:focus { border-color: var(--accent); }
.cta-input::placeholder { color: var(--muted); }
.cta-button { padding: 14px 36px; background: var(--accent); color: var(--bg); border-radius: 8px; font-family: var(--font-heading); font-size: 0.9375rem; font-weight: 600; letter-spacing: 0.02em; transition: transform 200ms, box-shadow 200ms; }
.cta-button:hover { transform: translateY(-1px); box-shadow: 0 8px 24px var(--accent_glow, var(--primary_glow)); }
.cta-note { font-size: 0.75rem; color: var(--muted); margin-top: 16px; }

footer { padding: 64px 0 48px; text-align: center; border-top: 1px solid var(--border); }
footer .container { display: flex; flex-direction: column; align-items: center; gap: 8px; }
footer .label { color: var(--muted); }
footer .data-source { font-size: 0.75rem; color: var(--muted); opacity: 0.7; max-width: 600px; }

/* ── ECG (medicine) ── */
.ecg-line { display: block; width: 100%; height: 40px; margin: 0; }
.ecg-line path { stroke: var(--primary); stroke-width: 1.5; fill: none; stroke-dasharray: 1000; animation: ecg 3s linear infinite; }

/* ── canvas trail (medicine) ── */
.scalpel-canvas { position: fixed; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 9999; }

/* ── animations ── */
@keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes ecg { 0% { stroke-dashoffset: 1000; } 100% { stroke-dashoffset: 0; } }
@keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
@keyframes flowerFloat {
  0%   { transform: translate(0, 0) rotate(0deg); opacity: 0; }
  20%  { opacity: 1; }
  100% { transform: translate(20px, -60px) rotate(180deg); opacity: 0; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
  section.tab { opacity: 1; transform: none; }
}
"""

STYLE_OVERRIDES = {
  "cs": """
.hero { background: var(--bg); }
.hero h1.display { color: var(--fg); }
.hero h1.display::before { content: "> "; color: var(--primary); }
.hero-decor::before { background: var(--primary); opacity: 0.8; }
.hero-decor::after { content: " █"; color: var(--primary); animation: pulse 1.2s infinite; }
.bento-rank { font-family: var(--font-num); }
.quote { border-left: 2px solid var(--primary); }
.quote-text { font-family: var(--font-body); font-style: normal; }
.quote-text::before, .quote-text::after { color: var(--primary); font-family: var(--font-num); }
.cta-button { font-family: var(--font-num); }
section.tab { background-image: radial-gradient(circle at 1px 1px, var(--border) 1px, transparent 0); background-size: 24px 24px; background-position: -1px -1px; }
body { cursor: text; }
""",
  "finance": """
.hero { background: var(--bg); }
.hero h1.display { font-style: italic; font-weight: 500; letter-spacing: -0.02em; }
.hero h1.display::after { content: " ®"; font-size: 0.35em; vertical-align: super; color: var(--accent); font-style: normal; font-weight: 400; }
.hero-decor { font-family: var(--font-heading); font-style: italic; font-size: 0.9375rem; letter-spacing: 0.1em; text-transform: none; }
.hero-decor::before { width: 64px; background: var(--accent); opacity: 0.4; }
.hero-tags .tag { font-family: var(--font-heading); letter-spacing: 0.06em; }
.tag.primary { font-style: italic; }
.bento-rank { font-family: var(--font-num); font-style: italic; }
.bento-name { font-style: italic; font-weight: 500; }
.quote { border-left: 2px solid var(--accent); }
.quote-text { font-size: 1.3125rem; line-height: 1.6; }
.quote-text::before, .quote-text::after { color: var(--accent); }
.cta-button { font-family: var(--font-heading); font-style: italic; letter-spacing: 0.08em; }
.salary-table th { font-family: var(--font-heading); font-style: italic; font-weight: 500; }
.stat-value { font-family: var(--font-num); font-style: italic; }
.hero::after { content: ""; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 80%; max-width: 600px; height: 1px; background: linear-gradient(90deg, transparent, var(--accent), transparent); opacity: 0.3; }

/* v3: 数字 hover 闪金光 */
.num:hover { color: var(--accent); text-shadow: 0 0 12px var(--accent_glow); transition: color 200ms, text-shadow 200ms; }
""",
  "medicine": """
.hero { background: var(--bg); }
.hero h1.display { font-weight: 700; letter-spacing: -0.04em; }
.hero h1.display::before { content: "NO."; display: block; font-family: var(--font-num); font-size: 0.75rem; font-weight: 500; color: var(--muted); letter-spacing: 0.2em; margin-bottom: 16px; }
.hero-decor { font-family: var(--font-num); }
.bento-rank { font-family: var(--font-num); font-weight: 700; background: var(--primary); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; padding: 0; display: inline-flex; align-items: center; justify-content: center; }
.bento-name { font-family: var(--font-num); font-weight: 600; letter-spacing: 0.02em; }
.quote { border-left: 2px solid var(--primary); background: linear-gradient(90deg, var(--primary_glow) 0%, var(--surface) 30%); }
.quote-text { font-family: var(--font-num); font-style: normal; font-size: 1.0625rem; line-height: 1.7; }
.quote-text::before, .quote-text::after { color: var(--primary); font-family: var(--font-num); }
.cta-button { font-family: var(--font-num); letter-spacing: 0.1em; }
.section-num { font-family: var(--font-num); font-weight: 600; }
.stat { position: relative; }
.stat::after { content: ""; position: absolute; top: 12px; right: 12px; width: 6px; height: 6px; background: var(--primary); border-radius: 50%; opacity: 0.5; }
.vital.heart { border-left: 3px solid var(--accent_red); }
""",
  "law": """
.hero { background: var(--bg); padding-top: 96px; padding-bottom: 96px; }
.hero h1.display { font-style: italic; text-align: center; font-weight: 500; }
.hero-decor { font-family: var(--font-heading); font-style: italic; font-size: 1.125rem; text-transform: none; letter-spacing: 0.08em; }
.hero-decor::before { background: var(--accent); opacity: 0.5; }
.hero-tagline { text-align: center; max-width: 600px; }
.tag.primary { font-family: var(--font-heading); font-style: italic; letter-spacing: 0.06em; }
.bento-item { background: var(--bg); }
.bento-item:hover { background: var(--surface_alt); }
.bento-item::before { content: "§"; position: absolute; top: 24px; right: 24px; color: var(--accent); font-family: var(--font-heading); font-size: 1.5rem; font-weight: 700; opacity: 0.3; }
.bento-name { font-style: italic; font-weight: 500; }
.quote { border-left: 4px double var(--accent); background: var(--bg); }
.quote-text { font-family: var(--font-heading); font-size: 1.25rem; line-height: 1.65; font-style: italic; }
.quote-text::before, .quote-text::after { color: var(--accent); font-family: var(--font-heading); }
.cta-button { font-family: var(--font-heading); font-style: italic; letter-spacing: 0.06em; }
.salary-table th { font-family: var(--font-heading); font-style: italic; font-weight: 500; }
.hero::before, .hero::after { content: ""; display: block; width: 64px; height: 1px; background: var(--accent); margin: 24px auto; opacity: 0.4; }
.hero::before { margin-bottom: 32px; }
.hero::after { margin-top: 32px; margin-bottom: 0; }

/* v3: 引文 hover 整行高亮 */
.quote { transition: border-left-width 200ms, background 200ms, transform 200ms, box-shadow 200ms; }
.quote:hover { border-left-width: 8px; background: linear-gradient(90deg, var(--accent_glow) 0%, var(--bg) 50%); transform: translateX(4px); box-shadow: 0 4px 16px rgba(120, 53, 15, 0.08); }
""",
  "education": """
.hero { background: var(--bg); }
.hero h1.display { font-style: italic; font-weight: 500; letter-spacing: -0.02em; }
.hero h1.display::before { content: "❀"; display: inline-block; color: var(--accent); margin-right: 16px; font-style: normal; }
.hero-decor { font-family: var(--font-heading); font-style: italic; font-size: 0.9375rem; text-transform: none; letter-spacing: 0.1em; }
.hero-decor::before { background: var(--accent); }
.bento-item { background: var(--bg); }
.bento-item::before { content: "❀"; position: absolute; top: 20px; right: 20px; color: var(--accent); font-size: 0.875rem; opacity: 0.5; }
.bento-name { font-style: italic; }
.quote { border-left: 2px solid var(--accent); background: var(--bg); }
.quote-text { font-family: var(--font-heading); font-style: italic; font-size: 1.1875rem; line-height: 1.65; }
.quote-text::before { content: "\\201C"; color: var(--accent); }
.quote-text::after { content: "\\201D"; color: var(--accent); }
.cta-button { font-family: var(--font-heading); font-style: italic; letter-spacing: 0.06em; }
.stat-value { font-family: var(--font-num); font-weight: 600; color: var(--accent); }
.tag { font-family: var(--font-heading); font-style: italic; letter-spacing: 0.04em; }

/* v3: hover 课程 ❀ 漂浮 */
.course { position: relative; }
.course::after { content: "❀"; position: absolute; right: -4px; top: 50%; transform: translateY(-50%); opacity: 0; transition: opacity 300ms; font-size: 0.875rem; color: var(--accent); pointer-events: none; }
.course:hover::after { opacity: 1; animation: flowerFloat 1.5s ease-out forwards; }
""",
}


def build_style_css(style: str) -> str:
    tok = STYLE_TOKENS[style]
    c = tok["colors"]
    f = tok["fonts"]
    font_url = FONT_URLS[style]
    css = f""":root {{
  --font-heading: {f['heading']};
  --font-body: {f['body']};
  --font-cn: {f['cn']};
  --font-num: {f['num']};
  --bg: {c['bg']};
  --fg: {c['fg']};
  --muted: {c['muted']};
  --primary: {c['primary']};
  --primary_dim: {c.get('primary_dim', c['primary'])};
  --primary_glow: {c.get('primary_glow', 'rgba(0,0,0,0.08)')};
  --surface: {c['surface']};
  --surface_alt: {c['surface_alt']};
  --border: {c['border']};
  --border_strong: {c.get('border_strong', c['border'])};
  --accent: {c.get('accent', c['primary'])};
  --accent_glow: {c.get('accent_glow', c.get('primary_glow', 'rgba(0,0,0,0.08)'))};
  --shadow: {c.get('shadow', '0 1px 2px rgba(0,0,0,0.04)')};
  --shadow_hover: {c.get('shadow_hover', c.get('shadow', '0 4px 12px rgba(0,0,0,0.08)'))};
}}
{font_url}
{BASE_CSS}
{STYLE_OVERRIDES.get(style, "")}
"""
    return css


ECG_SVG = """<svg class="ecg-line" viewBox="0 0 1200 40" preserveAspectRatio="none" aria-hidden="true"><path d="M 0 20 L 200 20 L 220 20 L 240 20 L 260 8 L 280 32 L 300 20 L 320 20 L 340 20 L 360 20 L 380 20 L 400 20 L 420 20 L 440 14 L 460 26 L 480 20 L 500 20 L 520 20 L 540 20 L 560 20 L 580 20 L 600 20 L 620 20 L 640 8 L 660 32 L 680 20 L 700 20 L 720 20 L 740 20 L 760 20 L 780 20 L 800 20 L 820 14 L 840 26 L 860 20 L 880 20 L 900 20 L 920 20 L 940 20 L 960 20 L 980 20 L 1000 8 L 1020 32 L 1040 20 L 1060 20 L 1080 20 L 1100 20 L 1120 20 L 1140 20 L 1160 20 L 1180 20 L 1200 20" /></svg>"""


def get_first_char(name: str) -> str:
    """取 name 第一个字符. 英文取首字母, 中文取首字."""
    if not name:
        return "?"
    first = name.strip()[0]
    if first.isascii() and first.isalpha():
        return first.upper()
    return first


# ──────────────────────────────────────────────────────────
# v3 模板 (5 套 hero 范式分支)
# ──────────────────────────────────────────────────────────
def render_html(data: dict, style: str) -> str:
    tok = STYLE_TOKENS[style]
    c = tok["colors"]
    title = data.get("title", "未命名专业")
    slug = data.get("slug", "unknown")
    summary = data.get("summary", "")
    category = data.get("category", "")
    degree = data.get("degree", "")
    duration = data.get("duration_years", 4)
    tags = data.get("tags", [])
    difficulty = data.get("difficulty", "★★★☆☆")
    is_5_year = duration == 5
    show_ecg = tok.get("show_ecg", False)
    hero_layout = tok.get("hero_layout", "v2")

    curriculum = data.get("curriculum", {})
    top_schools = data.get("top_schools", [])
    top_companies = data.get("top_companies", [])
    salary = data.get("salary", {})
    directions = data.get("employment_direction", [])
    deep_study = data.get("deep_study", {})
    quotes = data.get("alumni_quotes", [])
    xuanke = data.get("xuanke_req_list", [])
    data_source = data.get("data_source", "实时整合")
    updated_at = data.get("updated_at", "2026-06")

    decor = tok["decor"].format(slug=slug, title=title, n=1) + tok.get("hero_decor_extra", "")

    # ── 渲染课程 ──
    def render_courses(block_name: str, courses: list) -> str:
        if not courses:
            return ""
        items = "\n".join(
            f'          <div class="course"><span class="course-name">{c.get("name", "")}</span><span class="course-credit">{c.get("credit", "")} 学分</span></div>'
            for c in courses
        )
        return f'        <div class="curriculum-block"><div class="curriculum-title">{block_name}</div>\n{items}\n        </div>'

    course_sections = []
    if "公共必修" in curriculum:
        course_sections.append(("公共必修 (所有院校都开)", curriculum["公共必修"]))
    if "通用专业核心" in curriculum:
        course_sections.append(("通用专业核心 (≈ 80% 院校覆盖)", curriculum["通用专业核心"]))
    if "5 校特色选修" in curriculum:
        course_sections.append(("5 校特色选修 (按方向分流)", curriculum["5 校特色选修"]))
    for k, v in curriculum.items():
        if k not in ("公共必修", "通用专业核心", "5 校特色选修"):
            course_sections.append((k, v))
    curriculum_html = "\n".join([render_courses(name, courses) for name, courses in course_sections]) if course_sections else '<p style="color:var(--muted)">课程数据待补充</p>'

    # ── 院校 (bento + monogram) ──
    schools_html = "\n".join(
        f'''        <div class="bento-item">
          <div class="bento-monogram" style="background:{c.get('monogram_bg', c['accent'])}; color:{c.get('monogram_fg', c['bg'])}">{get_first_char(s.get("name", ""))}</div>
          <span class="bento-rank">{s.get("rank", "")}</span>
          <div class="bento-name">{s.get("name", "")}</div>
          <div class="bento-tag">{s.get("tag", "")}</div>
        </div>'''
        for s in top_schools
    ) if top_schools else '<div style="grid-column: 1/-1; padding: 24px; color:var(--muted)">院校数据待补充</div>'

    # ── 公司 (monogram + sparkline) ──
    def render_sparkline(values: list) -> str:
        if not values or len(values) < 3:
            return ""
        max_v = max(values) or 1
        bars = "\n".join(
            f'            <div class="sparkline-bar" style="height:{(v/max_v)*100}%" title="Year {i+1}: {v}"></div>'
            for i, v in enumerate(values)
        )
        return f'          <div class="sparkline">\n{bars}\n          </div>\n          <div class="sparkline-label">近 5 年招聘量趋势</div>'

    monogram_bg = c.get("monogram_bg", c.get("accent", c.get("primary")))
    monogram_fg = c.get("monogram_fg", c.get("bg"))
    companies_html = "\n".join(
        f'''        <div class="company">
          <div class="company-head">
            <div class="company-monogram" style="background:{monogram_bg}; color:{monogram_fg}">{get_first_char(co.get("name", ""))}</div>
            <span class="company-tier tier-{co.get("tier", "B")}">{co.get("tier", "B")}</span>
          </div>
          <div class="company-name">{co.get("name", "")}</div>
          <div class="company-meta">{co.get("headcount", "")} · 校招 {co.get("salary", "")}</div>
{render_sparkline(co.get("sparkline", []))}
        </div>'''
        for co in top_companies
    ) if top_companies else '<p style="color:var(--muted)">公司数据待补充</p>'

    # ── 薪资 (≈ + yoy 箭头) ──
    salary_rows = []
    for stage, vals in salary.items():
        p25, p50, p75 = vals.get("p25", 0), vals.get("p50", 0), vals.get("p75", 0)
        yoy = vals.get("yoy", 0)  # int % (e.g. +12 / -3 / 0)
        max_v = max(p25, p50, p75, 1)
        if yoy > 0:
            yoy_html = f'<span class="yoy up">↗ +{yoy}%</span>'
        elif yoy < 0:
            yoy_html = f'<span class="yoy down">↘ {yoy}%</span>'
        else:
            yoy_html = f'<span class="yoy flat">→ 0%</span>'
        salary_rows.append(
            f'''        <tr>
          <td class="salary-stage">{stage}</td>
          <td class="num"><span class="approx">≈</span>P25 {p25} 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p25/max_v*100}%"></span></span>{yoy_html}</td>
          <td class="num"><span class="approx">≈</span>P50 {p50} 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p50/max_v*100}%"></span></span></td>
          <td class="num"><span class="approx">≈</span>P75 {p75} 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p75/max_v*100}%"></span></span></td>
        </tr>'''
        )
    salary_html = "\n".join(salary_rows) if salary_rows else '<tr><td colspan="4" style="color:var(--muted)">薪资数据待补充</td></tr>'

    direction_html = "\n".join(
        f'''        <div class="direction">
          <div class="direction-name">{d.get("name", "")}</div>
          <div class="direction-bar"><div class="direction-bar-fill" style="width:{d.get("pct", 0)}%"></div></div>
          <div class="direction-pct num">{d.get("pct", 0)}%</div>
        </div>'''
        for d in directions
    ) if directions else '<p style="color:var(--muted)">就业方向待补充</p>'

    path_html = "\n".join(
        f'''        <div class="path-card">
          <div class="path-pct num">{v}%</div>
          <div class="path-name">{k}</div>
        </div>'''
        for k, v in deep_study.items()
    ) if deep_study else '<p style="color:var(--muted)">深造数据待补充</p>'

    # ── quote (avatar) ──
    quotes_html = "\n".join(
        f'''        <div class="quote">
          <div class="quote-head">
            <div class="quote-avatar" style="background:{c.get('monogram_bg', c['accent'])}; color:{c.get('monogram_fg', c['bg'])}">{get_first_char(q.get("current", "?"))}</div>
            <div class="quote-byline">
              <strong>{q.get("current", "")}</strong>
              <span class="quote-source">{q.get("year", "")} · {q.get("source", "")}</span>
            </div>
          </div>
          <p class="quote-text">{q.get("quote", "")}</p>
        </div>'''
        for q in quotes
    ) if quotes else '<p style="color:var(--muted)">校友观点待补充</p>'

    xuanke_html = "\n".join(
        f'''        <div class="xuanke">
          <div class="xuanke-name">{x.get("name", "")}</div>
          <div class="xuanke-bar"><div class="xuanke-bar-fill" style="width:{x.get("pct", 0)}%"></div></div>
          <div class="xuanke-pct num">{x.get("pct", 0)}%</div>
        </div>'''
        for x in xuanke
    ) if xuanke else '<p style="color:var(--muted)">选科数据待补充</p>'

    timeline_html = ""
    if is_5_year and data.get("timeline"):
        tl = data["timeline"]
        timeline_html = f'''
<section class="tab" id="timeline">
  <div class="container">
    <div class="section-num">05+ · TIME-LINE</div>
    <h2 class="h2">学制时间轴</h2>
    <p class="lede">临床医学 5 年起步, 3+X 才是真正的开始。家里能撑住 10 年低收入吗?</p>
    <div class="timeline">
{chr(10).join(f'      <div class="tl-item"><div class="tl-year">{t.get("year")}</div><div class="tl-stage">{t.get("stage")}</div><div class="tl-income">{t.get("income", "")}</div></div>' for t in tl)}
    </div>
  </div>
</section>'''

    company_section_extra = ""
    if style == "cs" and data.get("github_metric"):
        gm = data["github_metric"]
        company_section_extra = f'''
<section class="tab" id="github">
  <div class="container">
    <div class="section-num">05+ · $ stat /students/quality</div>
    <h2 class="h2">这个专业的人, GitHub 上都干啥?</h2>
    <p class="lede">{gm.get("desc", "")}</p>
    <div class="path-grid">
      <div class="path-card"><div class="path-pct num">{gm.get("p1000_star", "12%")}</div><div class="path-name">1000+ star 项目</div></div>
      <div class="path-card"><div class="path-pct num">{gm.get("acm_award", "8%")}</div><div class="path-name">ACM 区域赛获奖</div></div>
      <div class="path-card"><div class="path-pct num">{gm.get("oss_contrib", "30%")}</div><div class="path-name">知名开源贡献</div></div>
    </div>
  </div>
</section>'''

    ecg_block = ECG_SVG if show_ecg else ""
    css = build_style_css(style)

    curriculum_note = data.get("curriculum_note", "全国 4 年制通用框架, 不同高校在大三/大四有不同方向分流。")

    # ──────────────────────────────────────────────────────────
    # 5 套 Hero layout
    # ──────────────────────────────────────────────────────────
    if hero_layout == "vitals":
        # medicine: 左侧 vital signs 仪表 + 右侧 hero 文字
        vitals = tok.get("vitals", [])
        vital_html = "\n".join(
            f'''            <div class="vital {v.get("key", "").lower()}">
              <div class="vital-label">{v.get("key", "")} · {v.get("label", "")}</div>
              <div class="vital-body"><span class="vital-value">{v.get("value", "")}</span><span class="vital-unit">{v.get("unit", "")}</span></div>
              <div class="vital-range">参考 {v.get("range", "")}</div>
            </div>'''
            for v in vitals
        )
        hero_html = f'''
<header class="hero vitals">
  {ecg_block}
  <div class="container">
    <div class="vitals-panel">
      <div class="vitals-header">
        <span class="vitals-time">14:32:08 UTC+8</span>
        <span class="vitals-status">NORMAL · 正常</span>
      </div>
      <div class="vitals-grid">
{vital_html}
      </div>
    </div>
    <div class="hero-vitals-side">
      <div class="hero-decor">{decor}</div>
      <h1 class="display">{title}</h1>
      <p class="hero-tagline">{tok['tagline']} — {summary[:100]}</p>
      <div class="hero-tags">
        {''.join(f'<span class="tag primary">{t}</span>' for t in tags[:3])}
        {''.join(f'<span class="tag">{t}</span>' for t in tags[3:])}
      </div>
      <div class="hero-stats">
        <div class="stat"><div class="stat-label">学科门类</div><div class="stat-value">{category}</div></div>
        <div class="stat"><div class="stat-label">学制 · 学位</div><div class="stat-value num">{duration}年 · {degree}</div></div>
        <div class="stat"><div class="stat-label">难度自评</div><div class="stat-value">{difficulty}</div></div>
        <div class="stat"><div class="stat-label">数据更新</div><div class="stat-value num">{updated_at}</div></div>
      </div>
    </div>
  </div>
</header>'''
    elif hero_layout == "docket":
        # law: 法律卷宗首页
        case_no = tok.get("case_no", "CASE NO. 2026-HE-001").format(n=1)
        filed_at = tok.get("filed_at", "FILED: 2026-06-08 14:32 UTC+8")
        hero_html = f'''
<header class="hero docket">
  <div class="docket-stamp">CASE<br/>FILED</div>
  <div class="container">
    <div class="docket-header">
      <div class="docket-court">IN THE COURT OF PUBLIC OPINION · BEFORE THE HIGH-SCHOOL APPLICANT</div>
      <div class="docket-title-wrap">
        <div class="docket-line"></div>
        <div class="docket-title">{tok['label']}</div>
        <div class="docket-line"></div>
      </div>
    </div>
    <h1 class="display">{title}</h1>
    <p class="hero-tagline">{tok['tagline']} — {summary[:100]}</p>
    <div class="hero-tags">
      {''.join(f'<span class="tag primary">{t}</span>' for t in tags[:3])}
      {''.join(f'<span class="tag">{t}</span>' for t in tags[3:])}
    </div>
    <div class="docket-meta">
      <span>{case_no}</span>
      <span>{filed_at}</span>
      <span>PETITIONER: HIGH-SCHOOL CLASS OF 2026</span>
    </div>
  </div>
</header>'''
    else:
        # v2 hero (CS/finance/education)
        hero_html = f'''
<header class="hero {tok.get('hero_align', 'left')}">
  {ecg_block}
  <div class="container">
    <div class="hero-decor">{decor}</div>
    <h1 class="display">{title}</h1>
    <p class="hero-tagline">{tok['tagline']} — {summary[:100]}</p>
    <div class="hero-tags">
      {''.join(f'<span class="tag primary">{t}</span>' for t in tags[:3])}
      {''.join(f'<span class="tag">{t}</span>' for t in tags[3:])}
    </div>
    <div class="hero-stats">
      <div class="stat"><div class="stat-label">学科门类</div><div class="stat-value">{category}</div></div>
      <div class="stat"><div class="stat-label">学制 · 学位</div><div class="stat-value num">{duration}年 · {degree}</div></div>
      <div class="stat"><div class="stat-label">难度自评</div><div class="stat-value">{difficulty}</div></div>
      <div class="stat"><div class="stat-label">数据更新</div><div class="stat-value num">{updated_at}</div></div>
    </div>
  </div>
</header>'''

    # 5 鼠标交互 — canvas (medicine) + scroll observer
    scalpel_canvas = '<canvas class="scalpel-canvas"></canvas>' if style == "medicine" else ""

    interactions_js = ""
    if style == "medicine":
        interactions_js = """
<script>
(function() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const c = document.querySelector('.scalpel-canvas');
  if (!c) return;
  const ctx = c.getContext('2d');
  let dpr = window.devicePixelRatio || 1;
  function resize() { c.width = innerWidth * dpr; c.height = innerHeight * dpr; c.style.width = innerWidth + 'px'; c.style.height = innerHeight + 'px'; }
  resize(); window.addEventListener('resize', resize);
  const points = [];
  const PRIMARY = getComputedStyle(document.documentElement).getPropertyValue('--primary').trim() || '#0C4A6E';
  document.addEventListener('mousemove', e => {
    points.push({ x: e.clientX * dpr, y: e.clientY * dpr, t: Date.now() });
    if (points.length > 30) points.shift();
  });
  function draw() {
    ctx.clearRect(0, 0, c.width, c.height);
    const now = Date.now();
    for (let i = 0; i < points.length - 1; i++) {
      const p = points[i], q = points[i+1];
      const age = now - p.t;
      if (age > 800) continue;
      const alpha = (1 - age / 800) * 0.4;
      ctx.strokeStyle = PRIMARY;
      ctx.globalAlpha = alpha;
      ctx.lineWidth = 1.5 * dpr;
      ctx.beginPath();
      ctx.moveTo(p.x, p.y);
      ctx.lineTo(q.x, q.y);
      ctx.stroke();
    }
    points = points.filter(p => now - p.t < 800);
    requestAnimationFrame(draw);
  }
  draw();
})();
</script>
"""
    scroll_observer_js = """
<script>
(function() {
  if (!('IntersectionObserver' in window)) {
    document.querySelectorAll('section.tab').forEach(s => s.classList.add('visible'));
    return;
  }
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        obs.unobserve(e.target);
      }
    });
  }, { rootMargin: '0px 0px -10% 0px', threshold: 0.05 });
  document.querySelectorAll('section.tab').forEach(s => obs.observe(s));
})();
</script>
"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}专业介绍 2026 高考 | Major Explorer</title>
<meta name="description" content="{tok['tagline']}。{summary[:80]}">
<style>
{css}
</style>
</head>
<body>
{hero_html}

<section class="tab" id="overview">
  <div class="container">
    <div class="section-num">01 / 10 · OVERVIEW</div>
    <h2 class="h2">速览</h2>
    <p class="lede">{summary}</p>
    {f'<h3 class="h3">这个专业学什么?</h3><p>{data.get("what_you_learn", "")}</p>' if data.get("what_you_learn") else ''}
    {f'<h3 class="h3">什么人适合?</h3><p>{data.get("who_fits", "")}</p>' if data.get("who_fits") else ''}
    {f'<h3 class="h3">避坑指南</h3><p>{data.get("pitfalls", "")}</p>' if data.get("pitfalls") else ''}
  </div>
</section>

<section class="tab" id="curriculum">
  <div class="container">
    <div class="section-num">02 / 10 · CURRICULUM</div>
    <h2 class="h2">主要课程</h2>
    <p class="curriculum-lede">{curriculum_note}</p>
    <div class="curriculum-grid">
{curriculum_html}
    </div>
  </div>
</section>

<section class="tab" id="schools">
  <div class="container">
    <div class="section-num">03 / 10 · SCHOOLS</div>
    <h2 class="h2">院校分布</h2>
    <p class="lede">教育部学科评估第四轮 (2017, 第五轮 2022 部分公开)。A+ = 前 2% 或前 2 所, A = 前 2-10%, A- = 前 10-20%。</p>
    <div class="bento">
{schools_html}
    </div>
  </div>
</section>

<section class="tab" id="companies">
  <div class="container">
    <div class="section-num">04 / 10 · EMPLOYERS</div>
    <h2 class="h2">头部公司</h2>
    <p class="lede">S = 顶级 (顶级薪资+大量校招), A = 知名 (稳定校招), B = 大量招 (中等门槛)。校招薪资为 2024 秋招主流 offer 中位数。底部 bar = 近 5 年招聘量趋势。</p>
    <div class="company-grid">
{companies_html}
    </div>
  </div>
</section>

{timeline_html}

{company_section_extra}

<section class="tab" id="salary">
  <div class="container">
    <div class="section-num">{('06' if timeline_html or company_section_extra else '05')} / 10 · SALARY</div>
    <h2 class="h2">薪资分布</h2>
    <p class="lede">数据源: 麦可思 2024 中国大学生就业报告 + 招聘平台 2024 校招采样 (N=120+ offer)。单位: 万/年。P25 = 25% 的人低于此, P50 = 中位数, P75 = 75% 的人低于此。≈ 表示估算值。↗ = 3 年变化。</p>
    <table class="salary-table">
      <thead>
        <tr><th>阶段</th><th>P25</th><th>P50 中位</th><th>P75 高位</th></tr>
      </thead>
      <tbody>
{salary_html}
      </tbody>
    </table>
  </div>
</section>

<section class="tab" id="directions">
  <div class="container">
    <div class="section-num">{('07' if timeline_html or company_section_extra else '06')} / 10 · DIRECTIONS</div>
    <h2 class="h2">就业方向</h2>
    <p class="lede">毕业 1-3 年的去向分布, 占比合计 100%。</p>
    <div class="direction-list">
{direction_html}
    </div>
  </div>
</section>

<section class="tab" id="deep-study">
  <div class="container">
    <div class="section-num">{('08' if timeline_html or company_section_extra else '07')} / 10 · DEEP-STUDY</div>
    <h2 class="h2">深造路径</h2>
    <div class="path-grid">
{path_html}
    </div>
  </div>
</section>

<section class="tab" id="quotes">
  <div class="container">
    <div class="section-num">{('09' if timeline_html or company_section_extra else '08')} / 10 · VOICES</div>
    <h2 class="h2">学长学姐说</h2>
    <p class="lede">真实在校生/毕业生观点, 有夸有劝退, 自己判断。</p>
    <div class="quotes">
{quotes_html}
    </div>
  </div>
</section>

<section class="tab" id="xuanke">
  <div class="container">
    <div class="section-num">{('10' if timeline_html or company_section_extra else '09')} / 10 · SUBJECTS</div>
    <h2 class="h2">选科要求 (新高考 3+1+2)</h2>
    <p class="lede">基于 2024 年全国开设此专业院校的招生选科要求统计。覆盖率越高, 你的选科组合能报的院校越多。</p>
    <div class="xuanke-list">
{xuanke_html}
    </div>
  </div>
</section>

<section class="tab" id="cta">
  <div class="container">
    <div class="section-num">{('11' if timeline_html or company_section_extra else '10')} / 10 · NEXT</div>
    <h2 class="h2">关联志愿</h2>
    <div class="cta-block">
      <h3 class="h3">基于你的位次, 推荐这些校 + 组</h3>
      <p>上面院校列表已内置, 输入位次和分数, 立刻出志愿表 (冲 / 稳 / 保 比例 25/50/25)。</p>
      <form class="cta-form" onsubmit="event.preventDefault(); alert('功能开发中, 请关注后续更新');">
        <input type="number" class="cta-input" placeholder="位次 (如 1234)" required>
        <input type="number" class="cta-input" placeholder="分数 (如 620)" required>
        <button type="submit" class="cta-button">推荐志愿 →</button>
      </form>
      <p class="cta-note">⚠️ 本页所有数据截至 {updated_at}, 仅供高考志愿参考, 不构成最终决策建议。</p>
    </div>
  </div>
</section>

<footer>
  <div class="container">
    <div class="label">{tok['label']} · Major Explorer · 2026 高考</div>
    <div class="data-source">数据源: {data_source}</div>
  </div>
</footer>

{scalpel_canvas}
{interactions_js}
{scroll_observer_js}
</body>
</html>"""


def generate_dashboard(data: dict, style: str, output_path: str | None = None) -> str:
    if style not in STYLE_TOKENS:
        raise ValueError(f"Unknown style: {style}. Choose from {list(STYLE_TOKENS.keys())}")
    # v4 分流:
    #   - medicine → v4_medicine (Mayo Clinic 级, 之前已建)
    #   - cs/finance/law/education → v4_styles (本轮 4 套极致)
    if style == "medicine":
        from v4_medicine import render_v4_medicine
        html = render_v4_medicine(data)
    elif style in ("cs", "humanities", "administration", "finance", "law", "education", "sci", "eng", "agri", "arts", "gongan", "business"):
        from v4_styles import render_v4
        html = render_v4(data, style)
    else:
        html = render_html(data, style)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(html, encoding="utf-8")
    return html


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Major Explorer dashboard v3")
    parser.add_argument("--data", required=True)
    parser.add_argument("--style", required=True, choices=list(STYLE_TOKENS.keys()))
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    out = generate_dashboard(data, args.style, args.output)
    if args.output:
        print(f"✅ Generated: {args.output} ({len(out):,} bytes)")
    else:
        print(out)
