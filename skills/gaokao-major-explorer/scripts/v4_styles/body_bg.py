"""
v4_styles/body_bg.py — 渲染通用 body 底层纹理 (招 #1 noise + 招 #5 风格专属底层)
"""


def get_body_bg_css(style: str) -> str:
    """招 #1 + 招 #5: 风格专属底层纹理"""
    if style == "cs":
        return """
body { background: #0B1120; color: #F8FAFC; font-family: 'JetBrains Mono', 'PingFang SC', monospace; }
/* 招 #5: 1px dot grid */
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0; background-image: radial-gradient(circle at 1px 1px, #1F2937 1px, transparent 0); background-size: 24px 24px; }
/* 招 #1: noise + 招 #5 强化: CRT scanlines */
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1;
  background:
    repeating-linear-gradient(0deg, rgba(34, 197, 94, 0.025) 0px, rgba(34, 197, 94, 0.025) 1px, transparent 1px, transparent 3px),
    url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/><feColorMatrix values='0 0 0 0 0.13 0 0 0 0 0.77 0 0 0 0 0.37 0 0 0 0.4 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>");
  opacity: 0.5;
}
/* 招 #6: 终端光标 */
body { cursor: text; }
"""
    if style == "humanities":
        return """
body { background: #F2E8D5; color: #1F140A; font-family: 'Noto Serif SC', 'Cormorant Garamond', serif; }
/* 招 #5: 米白宣纸 + 顶部台灯辐射光斑 */
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 800px 500px at 50% 0%, rgba(184, 137, 58, 0.12) 0%, transparent 60%),
    radial-gradient(ellipse 600px 400px at 15% 100%, rgba(154, 42, 42, 0.04) 0%, transparent 60%),
    radial-gradient(ellipse 600px 400px at 85% 100%, rgba(139, 90, 43, 0.04) 0%, transparent 60%);
}
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1; background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3'/><feColorMatrix values='0 0 0 0 0.55 0 0 0 0 0.42 0 0 0 0 0.20 0 0 0 0.10 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>"); opacity: 0.18; mix-blend-mode: multiply; }
"""
    if style == "administration":
        return """
body { background: #FAFAF6; color: #1A2438; font-family: 'IBM Plex Serif', 'Noto Serif SC', serif; }
/* 招 #5: 公文纸底纹 + 政府蓝 radial 暗示红头 */
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 700px 400px at 50% 0%, rgba(30, 58, 95, 0.06) 0%, transparent 60%),
    radial-gradient(ellipse 500px 300px at 80% 100%, rgba(192, 57, 43, 0.04) 0%, transparent 60%);
}
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1;
  background:
    repeating-linear-gradient(0deg, rgba(26, 36, 56, 0.012) 0px, transparent 1px, transparent 3px),
    url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/><feColorMatrix values='0 0 0 0 0.42 0 0 0 0 0.30 0 0 0 0 0.18 0 0 0 0.06 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>");
  opacity: 0.5;
}
"""
    if style == "finance":
        return """
body { background: #FAFAF9; color: #0C0A09; font-family: 'Jost', 'PingFang SC', sans-serif; }
/* 招 #5: 烫金纸纹理 (subtle gold dust) */
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 800px 400px at 20% 0%, rgba(161, 98, 7, 0.04) 0%, transparent 60%),
    radial-gradient(ellipse 600px 300px at 80% 100%, rgba(161, 98, 7, 0.03) 0%, transparent 60%);
}
/* 招 #1: noise */
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1; background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/><feColorMatrix values='0 0 0 0 0.63 0 0 0 0 0.39 0 0 0 0 0.03 0 0 0 0.3 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>"); opacity: 0.08; mix-blend-mode: multiply; }
"""
    if style == "law":
        return """
body { background: #FFFBEB; color: #1C1917; font-family: 'Lato', 'PingFang SC', sans-serif; }
/* 招 #5: 羊皮纹理 */
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 1000px 600px at 50% 0%, rgba(120, 53, 15, 0.04) 0%, transparent 70%),
    radial-gradient(ellipse 800px 400px at 50% 100%, rgba(217, 119, 6, 0.03) 0%, transparent 70%);
}
/* 招 #1: noise */
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1; background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='3'/><feColorMatrix values='0 0 0 0 0.47 0 0 0 0 0.21 0 0 0 0 0.06 0 0 0 0.4 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>"); opacity: 0.07; mix-blend-mode: multiply; }
"""
    if style == "education":
        return """
body { background: #FFFBEB; color: #1C1917; font-family: 'Inter', 'PingFang SC', sans-serif; }
/* 招 #5: 暖橙 + 银杏叶 */
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 600px 400px at 30% 10%, rgba(154, 52, 18, 0.04) 0%, transparent 60%),
    radial-gradient(ellipse 500px 300px at 70% 90%, rgba(245, 158, 11, 0.05) 0%, transparent 60%);
}
/* 招 #1: noise */
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1; background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3'/><feColorMatrix values='0 0 0 0 0.6 0 0 0 0 0.2 0 0 0 0 0.05 0 0 0 0.3 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>"); opacity: 0.08; mix-blend-mode: multiply; }
"""
    if style == "sci":
        return """
body { background: #EDE3CC; color: #1F1B12; font-family: 'Lora', 'Source Han Serif SC', serif; }
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 700px 400px at 20% 0%, rgba(199, 62, 29, 0.05) 0%, transparent 60%),
    radial-gradient(ellipse 600px 300px at 80% 100%, rgba(45, 95, 78, 0.04) 0%, transparent 60%);
}
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1; background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/><feColorMatrix values='0 0 0 0 0.55 0 0 0 0 0.42 0 0 0 0 0.20 0 0 0 0.10 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>"); opacity: 0.6; mix-blend-mode: multiply; }
"""
    if style == "eng":
        return """
body { background: #F5F2EA; color: #1A1F2E; font-family: 'Source Sans 3', 'PingFang SC', sans-serif; }
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    linear-gradient(rgba(27, 58, 92, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(27, 58, 92, 0.06) 1px, transparent 1px);
  background-size: 64px 64px, 64px 64px;
}
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1; background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.95' numOctaves='2'/><feColorMatrix values='0 0 0 0 0.1 0 0 0 0 0.22 0 0 0 0 0.36 0 0 0 0.5 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>"); opacity: 0.04; }
"""
    if style == "agri":
        return """
body { background: linear-gradient(165deg, #F5F9EC 0%, #E8EFDC 45%, #F5F9EC 100%); color: #2E5A2E; font-family: 'Noto Serif SC', 'Cormorant Garamond', serif; }
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 700px 400px at 18% 25%, rgba(230, 180, 34, 0.08), transparent 60%),
    radial-gradient(ellipse 600px 400px at 82% 75%, rgba(107, 142, 35, 0.12), transparent 60%);
}
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1; background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/><feColorMatrix values='0 0 0 0 0.42 0 0 0 0 0.52 0 0 0 0 0.28 0 0 0 0.10 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>"); opacity: 0.30; mix-blend-mode: multiply; }
"""
    if style == "arts":
        return """
body { background: #F8F6F2; color: #1A1A1A; font-family: 'Noto Serif SC', 'EB Garamond', serif; }
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 800px 500px at 50% 0%, rgba(255, 248, 220, 0.30), transparent 60%),
    radial-gradient(ellipse 600px 400px at 50% 100%, rgba(184, 144, 42, 0.08), transparent 60%);
}
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1; background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.55 0 0 0 0 0.45 0 0 0 0 0.32 0 0 0 0.04 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>"); opacity: 0.30; mix-blend-mode: multiply; }
section.tab { background: transparent; }
"""
    if style == "gongan":
        return """
body { background: #0A1420; color: #FAFAF6; font-family: 'Noto Serif SC', 'Cinzel', serif; }
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 800px 500px at 20% 15%, rgba(212, 175, 55, 0.10), transparent 60%),
    radial-gradient(ellipse 700px 500px at 85% 80%, rgba(127, 29, 29, 0.10), transparent 60%);
}
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1; background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/><feColorMatrix values='0 0 0 0 0.83 0 0 0 0 0.69 0 0 0 0 0.22 0 0 0 0.06 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>"); opacity: 0.5; mix-blend-mode: overlay; }
"""
    if style == "business":
        return """
body { background: #FAFAF6; color: #1A1A1A; font-family: 'Inter', 'Noto Serif SC', sans-serif; }
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 800px 500px at 80% 20%, rgba(199, 123, 92, 0.10), transparent 60%),
    radial-gradient(ellipse 700px 500px at 15% 80%, rgba(62, 42, 31, 0.08), transparent 60%);
}
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 1; background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.95' numOctaves='2'/><feColorMatrix values='0 0 0 0 0.42 0 0 0 0 0.30 0 0 0 0 0.22 0 0 0 0.04 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/></svg>"); opacity: 0.30; }
"""
    return ""
