"""
scripts/v4_styles.py — 4 套极致 (cs/finance/law/education) 跟 medicine 同水准

8 招全上:
1. CSS noise 纹理 (SVG feTurbulence)
2. Stagger entrance (IntersectionObserver, 80ms × index)
3. 数字滚动 (data-count + easeOutExpo, 招 #3)
4. 巨型背景水印 (12vw 大, opacity 0.04)
5. 风格专属底层 (CS: 1px dot grid + scanlines / finance: 烫金纸 / law: 羊皮纹理 / education: 水彩)
6. 字体 (保 v3 选)
7. Drop cap
8. Asymmetric 卡片

每套专属 (极致方向):
- CS: CRT 扫描线 + 打字机 h1 + ASCII 边框 + 终端闪烁光标
- finance: 烫金水印 + editorial letterhead 抬头 + 中心烫金 rule line
- law: redacted ▓▓▓ 区块 + 律师签名 SVG + 边注 (margin notes) + small-caps + citation footnote
- education: 教科书扉页 (左书脊) + Caveat 手写 quote + ❀ 边框 + chapter §
"""
import re
from pathlib import Path

# 国内部署: 已将 Google Fonts 替换为 fonts.loli.net 镜像 (国内可访问)
FONT_URLS = {
  "cs":        "@import url('https://fonts.loli.net/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap');",
  "finance":   "@import url('https://fonts.loli.net/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap');",
  "finance":   "@import url('https://fonts.loli.net/css2?family=Bodoni+Moda:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Jost:wght@300;400;500;600;700&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap');",
  "law":       "@import url('https://fonts.loli.net/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Lato:wght@300;400;700&family=Cormorant+Unicase:wght@400;500;600;700&family=Caveat:wght@400;500;600&display=swap');",
  "education": "@import url('https://fonts.loli.net/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,400&family=Inter:wght@300;400;500;600;700&family=Caveat:wght@400;500;600;700&family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400&display=swap');",
  "humanities":    "@import url('https://fonts.loli.net/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&family=Ma+Shan+Zheng&family=ZCOOL+XiaoWei&family=Long+Cang&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap');",
  "administration": "@import url('https://fonts.loli.net/css2?family=IBM+Plex+Serif:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@300;400;500&family=Noto+Serif+SC:wght@400;500;600;700;900&display=swap');",
  "sci": "@import url('https://fonts.loli.net/css2?family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Crimson+Pro:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;1,400&family=EB+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');",
  "eng": "@import url('https://fonts.loli.net/css2?family=Inter:wght@300;400;500;600;700;800&family=Source+Sans+3:wght@400;500;600;700&family=Roboto+Mono:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');",
  "agri": "@import url('https://fonts.loli.net/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Noto+Serif+SC:wght@400;500;600;700;900&family=ZCOOL+XiaoWei&display=swap');",
  "arts": "@import url('https://fonts.loli.net/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Noto+Serif+SC:wght@400;500;600;700;900&family=Archivo:wght@400;500;600;700;800;900&display=swap');",
  "gongan":  "@import url('https://fonts.loli.net/css2?family=Cinzel:wght@500;600;700;800&family=Cormorant+Unicase:wght@500;600;700&family=Noto+Serif+SC:wght@300;400;500;600;700;900&family=Oswald:wght@500;600;700&family=Inter:wght@300;400;500;600;700&family=Long+Cang&display=swap');",
  "business":"@import url('https://fonts.loli.net/css2?family=Bodoni+Moda:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Bebas+Neue&display=swap');",
}


# ──────────────────────────────────────────────────────────
# 共享基础 (招 #1/5/6/7/8)
# ──────────────────────────────────────────────────────────
def get_base_css():
    return """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }
body { line-height: 1.65; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; font-feature-settings: 'kern' 1, 'liga' 1, 'tnum' 1; position: relative; overflow-x: hidden; }
img, svg { max-width: 100%; display: block; }
button { font: inherit; cursor: pointer; border: none; background: none; }
a { color: inherit; text-decoration: none; transition: opacity 200ms; }
a:hover { opacity: 0.65; }
h1, h2, h3, h4 { font-family: var(--font-heading); font-weight: 600; line-height: 1.2; letter-spacing: -0.02em; }
.num, .num * { font-family: var(--font-num); font-variant-numeric: tabular-nums; font-feature-settings: 'tnum' 1, 'lnum' 1; }
.caps { text-transform: uppercase; letter-spacing: 0.12em; font-weight: 500; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 40px; position: relative; z-index: 2; }
@media (max-width: 768px) { .container { padding: 0 20px; } }

.fade-up { opacity: 0; transform: translateY(24px); transition: opacity 700ms cubic-bezier(0.16, 1, 0.3, 1), transform 700ms cubic-bezier(0.16, 1, 0.3, 1); }
.fade-up.visible { opacity: 1; transform: translateY(0); }

section.tab { padding: 120px 0 96px; position: relative; z-index: 2; overflow: hidden; border-top: 1px solid #E2E8F0; }
section.tab:first-of-type { border-top: none; }
section.tab:last-of-type { border-bottom: none; }
.section-num { font-family: var(--font-num); font-size: 0.75rem; font-weight: 600; letter-spacing: 0.2em; margin-bottom: 12px; text-transform: uppercase; position: relative; z-index: 1; }
section.tab h2 { font-size: clamp(1.875rem, 3.5vw, 2.5rem); font-weight: 600; margin-bottom: 24px; position: relative; z-index: 1; }
section.tab h3 { font-size: 1.1875rem; font-weight: 600; margin: 40px 0 12px; }
section.tab p { margin-bottom: 16px; position: relative; z-index: 1; }
section.tab p.lede { font-size: 1.0625rem; line-height: 1.75; max-width: 720px; margin-bottom: 32px; position: relative; z-index: 1; }

.watermark { position: absolute; top: 40px; right: -20px; font-family: var(--font-heading); font-size: clamp(10rem, 18vw, 18rem); font-weight: 700; line-height: 0.85; letter-spacing: -0.05em; pointer-events: none; user-select: none; z-index: 0; }

footer { padding: 64px 0 48px; text-align: center; position: relative; z-index: 2; }
footer .container { display: flex; flex-direction: column; align-items: center; gap: 8px; }
footer .label { font-family: var(--font-num); font-size: 0.6875rem; letter-spacing: 0.15em; opacity: 0.7; }
footer .data-source { font-size: 0.75rem; opacity: 0.5; max-width: 600px; }

/* ──────────────────────────────────────────────────────────
   不必要的换行修复 — 短标签 / 徽章 / 单元统一 nowrap
   长文本 (lede / hero-tagline / quote) 用 text-wrap: pretty
   防止数字+单位、`/ · ` 周围、「」括号 等被切到下一行
   ────────────────────────────────────────────────────────── */
.section-num,
.stat-label, .stat-value,
.tag,
.bento-rank, .company-tier,
.yoy, .approx,
.sparkline-label,
.curriculum-title,
.path-name, .path-pct,
.direction-pct, .xuanke-pct,
.vital-label, .vital-value,
.docket-court, .docket-title, .docket-meta span,
.letterhead-meta, .letterhead-logo,
.chapter-marker,
.quote-byline strong, .quote-byline .quote-source,
.terminal-title, .terminal-status,
.salary-stage,
.hero-decor { white-space: nowrap; }

/* 长段落用 pretty wrap — 不在标点 / 数字 / 引号中间切 */
.lede, .hero-tagline, .quote-text,
.company-meta, .bento-tag,
section.tab p { text-wrap: pretty; word-break: keep-all; overflow-wrap: anywhere; line-break: strict; }

/* 数字+单位、`万/年/月` 单字单位不应单独成行 */
.num, .stat-value, .path-pct, .direction-pct, .xuanke-pct,
.salary-stage, .approx { word-break: keep-all; }


/* 院校/公司名: 允许在 <wbr> 软断点换行, 禁止在汉字字符间断 */
.bento-name, .company-name { word-break: keep-all; overflow-wrap: break-word; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse { 0%, 100% { opacity: 0.4; transform: scale(0.9); } 50% { opacity: 1; transform: scale(1.1); } }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
  .fade-up { opacity: 1; transform: none; }
}
"""


COUNT_UP_JS = """
<script>
(function() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  function easeOutExpo(t) { return t === 1 ? 1 : 1 - Math.pow(2, -10 * t); }
  function animateValue(el, start, end, duration) {
    const isFloat = el.dataset.float === '1';
    const startTime = performance.now();
    function step(now) {
      const t = Math.min(1, (now - startTime) / duration);
      const val = start + (end - start) * easeOutExpo(t);
      el.textContent = isFloat ? val.toFixed(1) : Math.round(val);
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  if ('IntersectionObserver' in window) {
    const countObs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting && !e.target.dataset.counted) {
          e.target.dataset.counted = '1';
          e.target.classList.add('count-up');
          animateValue(e.target, 0, parseFloat(e.target.dataset.count), 1500);
        }
      });
    }, { threshold: 0.3 });
    document.querySelectorAll('[data-count]').forEach(el => countObs.observe(el));
    const fadeObs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          const delay = parseInt(e.target.dataset.delay || '0');
          setTimeout(() => e.target.classList.add('visible'), delay);
          fadeObs.unobserve(e.target);
        }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.05 });
    document.querySelectorAll('.fade-up').forEach(el => fadeObs.observe(el));
  } else {
    document.querySelectorAll('.fade-up').forEach(el => el.classList.add('visible'));
    document.querySelectorAll('[data-count]').forEach(el => {
      el.textContent = el.dataset.float === '1' ? parseFloat(el.dataset.count).toFixed(1) : Math.round(parseFloat(el.dataset.count));
    });
  }
})();
</script>
"""


# 院校 / 公司名软换行 helper — 在「大学/学院/医学院/学部/学校/中心」后插 <wbr>
# 防止换行点落到「大」「学」之间, 同时不改变文本
def _dedup_by_name(items: list, key: str = "name") -> list:
    """Drop duplicate dicts (by item[key]) while preserving order — defensive against bad data."""
    seen, kept = set(), []
    for it in items or []:
        k = it.get(key) if isinstance(it, dict) else it
        if k in seen: continue
        seen.add(k); kept.append(it)
    return kept

_SOFT_BREAK_PAT = re.compile(r'(医学院|医学中心|大学|学院|学校|学部)(?=.)')
def soft_break_name(name: str) -> str:
    if not name:
        return ""
    return _SOFT_BREAK_PAT.sub(r'\1<wbr>', name)

def get_first_char(name: str) -> str:
    if not name:
        return "?"
    first = name.strip()[0]
    if first.isascii() and first.isalpha():
        return first.upper()
    return first


# ──────────────────────────────────────────────────────────
# 渲染通用 body (招 #1 noise + 招 #5 风格专属底层)
# ──────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────
# CS 极致: CRT 扫描线 + 打字机 h1 + ASCII 边框
# ──────────────────────────────────────────────────────────
CS_CSS = """
.hero { padding: 80px 0 96px; background: transparent; border-bottom: 1px solid #1F2937; position: relative; z-index: 2; overflow: hidden; }
.hero-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; }
@media (max-width: 900px) { .hero-grid { grid-template-columns: 1fr; gap: 32px; } }
.terminal-panel { padding: 28px 24px; background: rgba(17, 24, 39, 0.6); border: 1px solid #22C55E; border-radius: 4px; box-shadow: 0 0 0 1px rgba(34, 197, 94, 0.15), 0 0 40px rgba(34, 197, 94, 0.1), inset 0 0 60px rgba(34, 197, 94, 0.03); position: relative; }
.terminal-panel::before { content: "╔═══════════════════════════════════════════════════════════╗"; position: absolute; top: -14px; left: 0; right: 0; color: #22C55E; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; line-height: 1; white-space: pre; opacity: 0.4; }
.terminal-panel::after { content: "╚═══════════════════════════════════════════════════════════╝"; position: absolute; bottom: -14px; left: 0; right: 0; color: #22C55E; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; line-height: 1; white-space: pre; opacity: 0.4; }
.terminal-header { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #1F2937; }
.terminal-dot { width: 10px; height: 10px; border-radius: 50%; }
.terminal-dot.r { background: #EF4444; }
.terminal-dot.y { background: #F59E0B; }
.terminal-dot.g { background: #22C55E; }
.terminal-title { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #94A3B8; margin-left: 8px; letter-spacing: 0.05em; }
.terminal-status { margin-left: auto; display: flex; align-items: center; gap: 6px; font-family: 'JetBrains Mono', monospace; font-size: 0.6875rem; color: #22C55E; letter-spacing: 0.08em; }
.terminal-status::before { content: ""; width: 6px; height: 6px; background: #22C55E; border-radius: 50%; animation: pulse 1.2s infinite; }
.terminal-body { font-family: 'JetBrains Mono', monospace; font-size: 0.8125rem; line-height: 1.7; color: #94A3B8; }
.terminal-line { margin-bottom: 6px; }
.terminal-prompt { color: #22C55E; }
.terminal-cmd { color: #F8FAFC; }
.terminal-comment { color: #475569; }
.terminal-output { color: #94A3B8; }
.terminal-ascii { white-space: pre; color: #4ADE80; opacity: 1.0; line-height: 1.2; font-size: 0.75rem; margin: 12px 0; font-weight: 500; text-shadow: 0 0 6px rgba(34, 197, 94, 0.4); }

.hero-side { display: flex; flex-direction: column; }
.hero-decor { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #22C55E; letter-spacing: 0.15em; margin-bottom: 24px; display: flex; align-items: center; gap: 8px; text-transform: uppercase; }
.hero-decor::before { content: "$ "; }
.hero-decor::after { content: " █"; animation: pulse 1.2s infinite; }
.hero h1 { font-family: 'JetBrains Mono', monospace; font-size: clamp(2.75rem, 5.5vw, 4.5rem); font-weight: 600; letter-spacing: -0.02em; line-height: 1.1; color: #F8FAFC; margin-bottom: 24px; min-height: 1.2em; }
.hero h1 .typed-cursor { color: #22C55E; animation: pulse 1s infinite; }
.hero h1 .typed::after { content: "_"; color: #22C55E; animation: pulse 1s infinite; }
.hero-tagline { font-family: 'JetBrains Mono', monospace; font-size: 1.0625rem; color: #94A3B8; margin-bottom: 32px; line-height: 1.7; }
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 40px; }
.tag { padding: 5px 12px; background: rgba(34, 197, 94, 0.05); border: 1px solid #1F2937; border-radius: 2px; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #F8FAFC; letter-spacing: 0.05em; }
.tag.primary { background: rgba(34, 197, 94, 0.1); border-color: #22C55E; color: #22C55E; }

.hero-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; border-top: 1px solid #1F2937; border-bottom: 1px solid #1F2937; border-left: 1px solid #1F2937; border-right: 1px solid #1F2937; }
@media (max-width: 768px) { .hero-stats { grid-template-columns: repeat(2, 1fr); } }
.stat { padding: 20px 22px; border-right: 1px solid #1F2937; position: relative; }
.stat:last-child { border-right: none; }
@media (max-width: 768px) { .stat:nth-child(2) { border-right: none; } .stat:nth-child(1), .stat:nth-child(2) { border-bottom: 1px solid #1F2937; } }
.stat-label { font-family: 'JetBrains Mono', monospace; font-size: 0.625rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.15em; }
.stat-value { font-family: 'JetBrains Mono', monospace; font-size: 1.25rem; font-weight: 600; color: #22C55E; margin-top: 6px; letter-spacing: -0.01em; }

section.tab { border-top: 1px solid #475569; border-bottom: 2px solid #475569; }
section.tab:first-of-type { border-top: none; }
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1px; background: #1F2937; border: 1px solid #1F2937; border-radius: 4px; overflow: hidden; margin-top: 32px; position: relative; z-index: 1; }
.bento { position: relative; }

.bento-item:nth-child(3) { position: relative; }
.bento-item:nth-child(3)::before,
.bento-item:nth-child(6)::before,
.bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: rgba(34, 197, 94, 0.85); z-index: 1; pointer-events: none; }
.bento-item { padding: 28px 24px 24px; background: rgba(11, 17, 32, 0.6); position: relative; z-index: 0; transition: background 200ms; }
.bento-item:hover { background: rgba(17, 24, 39, 0.8); }
.bento-monogram { position: absolute; top: 20px; right: 20px; width: 36px; height: 36px; border-radius: 4px; display: flex; align-items: center; justify-content: center; background: #22C55E; color: #0B1120; font-family: 'JetBrains Mono', monospace; font-size: 0.9375rem; font-weight: 700; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #22C55E; border: 1px solid #22C55E; border-radius: 2px; font-family: 'JetBrains Mono', monospace; font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.08em; margin-bottom: 12px; }
.bento-name { font-family: 'JetBrains Mono', monospace; font-size: 1.0625rem; font-weight: 600; margin-bottom: 4px; color: #F8FAFC; padding-right: 44px; text-wrap: balance; line-height: 1.35; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 2.7em; }
.bento-tag { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #94A3B8; line-height: 1.5; }

.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 24px 22px 20px; background: rgba(11, 17, 32, 0.6); border: 1px solid #1F2937; border-radius: 4px; position: relative; transition: border-color 250ms, transform 250ms; }
.company:hover { border-color: #22C55E; transform: translateY(-2px); }
.company-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.company-monogram { width: 36px; height: 36px; border-radius: 4px; display: flex; align-items: center; justify-content: center; background: #22C55E; color: #0B1120; font-family: 'JetBrains Mono', monospace; font-size: 1rem; font-weight: 700; }
.company-tier { padding: 2px 8px; border-radius: 2px; font-family: 'JetBrains Mono', monospace; font-size: 0.625rem; font-weight: 700; letter-spacing: 0.08em; }
.tier-S { background: #22C55E; color: #0B1120; }
.tier-A { background: transparent; color: #22C55E; border: 1px solid #22C55E; }
.tier-B { background: rgba(34, 197, 94, 0.1); color: #94A3B8; }
.company-name { font-family: 'JetBrains Mono', monospace; font-size: 1.0625rem; font-weight: 600; margin-bottom: 8px; color: #F8FAFC; }
.company-meta { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #94A3B8; line-height: 1.5; margin-bottom: 12px; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 8px; border-top: 1px solid #1F2937; }
.sparkline-bar { flex: 1; background: #1F2937; min-height: 2px; transition: background 250ms; }
.company:hover .sparkline-bar { background: #22C55E; opacity: 0.6; }
.sparkline-label { font-family: 'JetBrains Mono', monospace; font-size: 0.625rem; color: #475569; letter-spacing: 0.1em; margin-top: 4px; }

.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: rgba(11, 17, 32, 0.6); border: 1px solid #1F2937; border-radius: 4px; overflow: hidden; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 18px 24px; text-align: left; border-bottom: 1px solid #1F2937; font-size: 0.875rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: rgba(17, 24, 39, 0.6); font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.12em; color: #94A3B8; }
.salary-stage { font-weight: 600; color: #F8FAFC; }
.salary-bar { display: inline-block; width: 80px; height: 6px; background: #1F2937; border-radius: 1px; margin-left: 8px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #22C55E; }
.yoy { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; font-weight: 600; margin-left: 12px; padding: 2px 6px; border-radius: 2px; }
.yoy.up   { color: #22C55E; background: rgba(34, 197, 94, 0.1); }
.yoy.down { color: #EF4444; background: rgba(239, 68, 68, 0.1); }
.yoy.flat { color: #94A3B8; background: rgba(31, 41, 55, 0.5); }
.approx { font-family: 'JetBrains Mono', monospace; color: #475569; margin-right: 4px; }

.direction-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 160px 1fr 60px; align-items: center; gap: 20px; padding: 14px 0; border-bottom: 1px solid #1F2937; }
.direction:last-child { border-bottom: none; }
.direction-name { font-family: 'JetBrains Mono', monospace; font-weight: 500; font-size: 0.875rem; color: #F8FAFC; }
.direction-bar { height: 10px; background: #1F2937; border-radius: 1px; overflow: hidden; }
.direction-bar-fill { height: 100%; background: #22C55E; transition: width 1.2s cubic-bezier(0.16, 1, 0.3, 1); }
.direction-pct { font-family: 'JetBrains Mono', monospace; font-weight: 600; text-align: right; font-size: 0.9375rem; color: #F8FAFC; }

.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: rgba(11, 17, 32, 0.6); border: 1px solid #1F2937; border-radius: 4px; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #22C55E; transform: translateY(-2px); }
.path-pct { font-family: 'JetBrains Mono', monospace; font-size: 2.5rem; font-weight: 700; color: #22C55E; margin-bottom: 4px; letter-spacing: -0.02em; line-height: 1; }
.path-name { font-family: 'JetBrains Mono', monospace; color: #94A3B8; font-size: 0.75rem; letter-spacing: 0.08em; margin-top: 8px; text-transform: uppercase; }

.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 28px 32px 24px; background: rgba(11, 17, 32, 0.6); border: 1px solid #1F2937; border-left: 2px solid #22C55E; border-radius: 0 4px 4px 0; margin-bottom: 16px; transition: border-left-width 250ms, transform 250ms; }
.quote:hover { border-left-width: 6px; transform: translateX(4px); }
.quote::before { content: "// "; color: #22C55E; font-family: 'JetBrains Mono', monospace; font-weight: 700; }
.quote-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.quote-avatar { width: 36px; height: 36px; border-radius: 4px; display: flex; align-items: center; justify-content: center; background: #22C55E; color: #0B1120; font-family: 'JetBrains Mono', monospace; font-size: 1rem; font-weight: 700; }
.quote-byline strong { display: block; font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #F8FAFC; font-size: 0.875rem; }
.quote-byline .quote-source { font-family: 'JetBrains Mono', monospace; color: #94A3B8; font-size: 0.75rem; }
.quote-text { font-family: 'JetBrains Mono', monospace; font-size: 1.0625rem; line-height: 1.7; color: #F8FAFC; font-style: normal; }
.quote-text::before { content: "“"; color: #22C55E; }
.quote-text::after { content: "”"; color: #22C55E; }

.xuanke-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 200px 1fr 80px; align-items: center; gap: 20px; padding: 14px 0; border-bottom: 1px solid #1F2937; }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-family: 'JetBrains Mono', monospace; font-weight: 500; font-size: 0.875rem; color: #F8FAFC; }
.xuanke-bar { height: 8px; background: #1F2937; border-radius: 1px; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #22C55E; }
.xuanke-pct { font-family: 'JetBrains Mono', monospace; font-weight: 600; text-align: right; font-size: 0.9375rem; color: #22C55E; }

.curriculum-lede { color: #94A3B8; font-size: 0.875rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.curriculum-block { padding: 28px 24px; background: rgba(11, 17, 32, 0.6); border: 1px solid #1F2937; border-radius: 4px; transition: border-color 250ms, transform 250ms; }
.curriculum-block:hover { border-color: #22C55E; transform: translateY(-2px); }
.curriculum-title { font-family: 'JetBrains Mono', monospace; font-size: 0.6875rem; color: #22C55E; text-transform: uppercase; letter-spacing: 0.15em; font-weight: 600; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #1F2937; }
.course { padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; font-size: 0.875rem; border-bottom: 1px dashed transparent; }
.course:hover { border-bottom-color: #1F2937; }
.course-name { color: #F8FAFC; }
.course-credit { color: #94A3B8; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; margin-left: 8px; }

.cta-block { margin-top: 32px; padding: 64px 48px; background: rgba(11, 17, 32, 0.8); border: 1px solid #22C55E; border-radius: 4px; text-align: center; position: relative; overflow: hidden; }
.cta-block::before { content: ""; position: absolute; inset: 0; background-image: repeating-linear-gradient(0deg, rgba(34, 197, 94, 0.05) 0px, transparent 1px); background-size: 100% 3px; pointer-events: none; }
.cta-block h3 { font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; margin-bottom: 12px; color: #F8FAFC; position: relative; z-index: 1; }
.cta-block p { color: #94A3B8; margin: 0 auto 28px; max-width: 560px; position: relative; z-index: 1; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; position: relative; z-index: 1; }
.cta-input { padding: 14px 18px; background: #0B1120; border: 1px solid #1F2937; border-radius: 2px; color: #F8FAFC; font-family: 'JetBrains Mono', monospace; font-size: 1rem; width: 180px; outline: none; }
.cta-input:focus { border-color: #22C55E; }
.cta-button { padding: 14px 36px; background: #22C55E; color: #0B1120; border-radius: 2px; font-family: 'JetBrains Mono', monospace; font-size: 0.9375rem; font-weight: 700; }
.cta-note { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #475569; margin-top: 16px; position: relative; z-index: 1; }

.watermark { color: #22C55E; opacity: 0.04; }
.section-num { color: #22C55E; }
section.tab h2 { color: #F8FAFC; }
section.tab p { color: #F8FAFC; }
section.tab p.lede { color: #94A3B8; line-break: strict; }
section.tab h3 { color: #F8FAFC; }
footer { background: rgba(11, 17, 32, 0.6); border-top: 1px solid #1F2937; }
footer .label { color: #22C55E; }
footer .data-source { color: #94A3B8; }

.drop-cap::first-letter { font-family: 'JetBrains Mono', monospace; font-size: 4em; font-weight: 700; line-height: 0.9; float: left; margin: 0.05em 0.12em 0 0; color: #22C55E; }

.lede { color: #94A3B8; line-break: strict; }

.terminal-prompt, .hero-decor { color: #22C55E; }
"""


# ──────────────────────────────────────────────────────────
# Finance 极致: 烫金水印 + editorial letterhead + drop cap
# ──────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────
# Law 极致: redacted ▓▓▓ + 律师签名 + 边注 + small-caps
# ──────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────
# Education 极致: 教科书扉页 + Caveat 手写 + ❀ 边框
# ──────────────────────────────────────────────────────────
EDUCATION_CSS = """
.hero { padding: 0; background: transparent; border-bottom: 1px solid #FDBA74; position: relative; z-index: 2; overflow: hidden; }
/* ── 教科书「打开的书」跨页布局 ── */
.book-frame {
  max-width: 1280px; margin: 0 auto; padding: 56px 32px 72px;
  display: grid;
  grid-template-columns: 52px 1fr 1fr;
  gap: 0;
  position: relative;
  min-height: 600px;
}
/* 中央装订线阴影 — 让两页有「向内凹」的立体感 */
.book-frame::before {
  content: ""; position: absolute; left: calc(50% + 26px); top: 56px; bottom: 72px;
  width: 36px; transform: translateX(-50%);
  background: linear-gradient(90deg,
    rgba(154, 52, 18, 0.10) 0%,
    rgba(154, 52, 18, 0.18) 50%,
    rgba(154, 52, 18, 0.10) 100%);
  pointer-events: none; z-index: 1;
}
/* 书脊 */
.book-spine {
  background: linear-gradient(90deg, #FB923C 0%, #FDBA74 60%, rgba(253, 186, 116, 0.4) 100%);
  display: flex; align-items: center; justify-content: center;
  position: relative; border-right: 1px solid #C2410C;
  box-shadow: 1px 0 0 rgba(154, 52, 18, 0.2), 2px 0 6px rgba(154, 52, 18, 0.12);
}
.book-spine-text {
  font-family: 'Playfair Display', serif; font-size: 0.9375rem; color: #FFFBEB;
  writing-mode: vertical-rl; letter-spacing: 0.28em; font-weight: 600;
  text-shadow: 0 1px 0 rgba(154, 52, 18, 0.6);
}
.book-spine-text span { display: block; margin: 12px 0; }
.book-spine-text .yr { font-family: 'Playfair Display', serif; font-style: italic; font-size: 0.75rem; opacity: 0.85; letter-spacing: 0.2em; }
/* 左页 verso —— 章节扉言 */
.book-verso {
  padding: 32px 56px 32px 64px;
  background: linear-gradient(90deg, #FEF3E2 0%, #FFFBEB 100%);
  border-right: 1px solid rgba(253, 186, 116, 0.5);
  position: relative;
  display: flex; flex-direction: column; justify-content: space-between;
}
.book-verso::after {  /* 内侧翻页阴影 */
  content: ""; position: absolute; right: 0; top: 0; bottom: 0; width: 40px;
  background: linear-gradient(90deg, transparent, rgba(154, 52, 18, 0.08));
  pointer-events: none;
}
.chapter-marker {
  display: inline-block; font-family: 'Cormorant Garamond', serif; font-style: italic;
  font-size: 0.875rem; color: #9A3412; letter-spacing: 0.18em;
  margin-bottom: 28px; padding-bottom: 8px; border-bottom: 1px solid #FDBA74;
}
.chapter-marker::before { content: "❀ "; }
.book-quote {
  font-family: 'Caveat', cursive; font-size: 1.5rem; color: #57534E;
  line-height: 1.55; margin: 24px 0; padding-left: 18px;
  border-left: 2px solid #F59E0B;
}
.book-quote::before { content: "「"; color: #F59E0B; margin-right: 4px; }
.book-quote::after  { content: "」"; color: #F59E0B; margin-left: 4px; }
.book-quote-sig {
  font-family: 'Cormorant Garamond', serif; font-style: italic;
  font-size: 0.875rem; color: #78716C; margin-top: 8px; padding-left: 18px;
}
.verso-footer {
  display: flex; align-items: flex-end; justify-content: space-between;
  padding-top: 24px; border-top: 1px dashed #FDBA74;
}
.book-publisher {
  font-family: 'Cormorant Garamond', serif; font-style: italic;
  font-size: 0.8125rem; color: #78716C; line-height: 1.6;
}
.book-publisher strong { color: #9A3412; font-style: normal;
  font-family: 'Playfair Display', serif; }
.book-page-num {
  font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.5rem;
  color: #C2410C; letter-spacing: 0.05em;
}
/* 右页 recto —— 主标题 + tagline + stats */
.book-recto {
  padding: 32px 56px 32px 64px;
  background: linear-gradient(-90deg, #FEF3E2 0%, #FFFBEB 100%);
  position: relative;
  display: flex; flex-direction: column;
}
.book-recto::before {  /* 内侧翻页阴影 */
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 40px;
  background: linear-gradient(-90deg, transparent, rgba(154, 52, 18, 0.08));
  pointer-events: none;
}
.recto-corner {
  font-family: 'Playfair Display', serif; font-style: italic; font-size: 0.75rem;
  color: #9A3412; letter-spacing: 0.18em; text-transform: uppercase;
  margin-bottom: 18px;
}
.hero h1 {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2.25rem, 4.2vw, 3.5rem);
  font-weight: 600; letter-spacing: -0.02em; line-height: 1.1;
  color: #1C1917; margin: 0 0 12px;
}
.hero h1::after { content: ""; display: block; width: 56px; height: 2px; background: #9A3412; margin: 18px 0; opacity: 0.6; }
.hero-tagline {
  font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 1.0625rem;
  color: #57534E; margin: 0 0 24px; line-height: 1.7;
}
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 32px; }
.tag { padding: 5px 14px; background: transparent; border: 1px solid #FDBA74;
  font-family: 'Cormorant Garamond', serif; font-size: 0.8125rem;
  color: #1C1917; letter-spacing: 0.04em; }
.tag.primary { background: rgba(154, 52, 18, 0.08); border-color: #9A3412; color: #9A3412; }
/* hero-stats —— 2×2 grid, 给长内容 (学制·学位 4Y · 教育学/文学/理学学士) 留足空间 */
.hero-stats {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.35fr);
  border: 1px solid #FDBA74; margin-top: auto;
}
.stat { padding: 18px 20px; border-right: 1px solid #FDBA74; border-bottom: 1px solid #FDBA74; min-width: 0; overflow: hidden; }
.stat:nth-child(2n) { border-right: none; }
.stat:nth-last-child(-n+2) { border-bottom: none; }
.stat-label { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.6875rem;
  color: #78716C; text-transform: uppercase; letter-spacing: 0.18em; font-weight: 500; }
/* 重要: 覆盖 base nowrap, 允许 stat-value 在 grid cell 内 wrap */
.book-recto .stat-value { font-family: 'Playfair Display', serif; font-size: 1.0625rem; font-weight: 600;
  color: #9A3412; margin-top: 4px; line-height: 1.4;
  white-space: normal !important; word-break: break-word; overflow-wrap: anywhere; }
/* 移动: 单列, 隐藏书脊 */
@media (max-width: 900px) {
  .book-frame { grid-template-columns: 1fr; gap: 16px; padding: 32px 20px 48px; min-height: 0; }
  .book-frame::before { display: none; }
  .book-spine { display: none; }
  .book-verso, .book-recto { padding: 24px 16px; border-right: none; background: #FFFBEB; }
  .book-verso::after, .book-recto::before { display: none; }
  .hero-stats { grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr); }
}

section.tab { border-top: 1px solid #F59E0B; border-bottom: 2px solid #F59E0B; }
section.tab:first-of-type { border-top: none; }
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1px; background: #F97316; border: 1px solid #F97316; margin-top: 32px; position: relative; z-index: 1; }
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
.bento-item::before { content: "❀"; position: absolute; top: 20px; right: 20px; color: #F59E0B; font-size: 0.875rem; opacity: 0.4; }
.bento-item:hover { background: #FFF7ED; }
.bento-monogram { position: absolute; top: 20px; right: 50px; width: 36px; height: 36px; border-radius: 4px; display: flex; align-items: center; justify-content: center; background: #9A3412; color: #FFFBEB; font-family: 'Playfair Display', serif; font-size: 1.0625rem; font-weight: 500; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #9A3412; border: 1px solid #9A3412; font-family: 'Cormorant Garamond', serif; font-variant: small-caps; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.12em; margin-bottom: 12px; }
.bento-name { font-family: 'Playfair Display', serif; font-size: 1.1875rem; font-weight: 500; margin-bottom: 4px; color: #1C1917; padding-right: 80px; text-wrap: balance; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 2.6em; }
.bento-tag { font-family: 'Inter', sans-serif; font-size: 0.8125rem; color: #57534E; line-height: 1.5; }

.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 28px 24px 22px; background: #FFFBEB; border: 1px solid #FDBA74; position: relative; transition: border-color 250ms, transform 250ms; }
.company:hover { border-color: #9A3412; transform: translateY(-2px); }
.company-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.company-monogram { width: 36px; height: 36px; border-radius: 4px; display: flex; align-items: center; justify-content: center; background: #9A3412; color: #FFFBEB; font-family: 'Playfair Display', serif; font-size: 1.0625rem; font-weight: 500; }
.company-tier { padding: 2px 8px; border: 1px solid #9A3412; color: #9A3412; font-family: 'Cormorant Garamond', serif; font-variant: small-caps; font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.12em; }
.tier-S { background: #9A3412; color: #FFFBEB; }
.tier-A { background: transparent; }
.tier-B { background: transparent; color: #78716C; border-color: #FDBA74; }
.company-name { font-family: 'Playfair Display', serif; font-size: 1.1875rem; font-weight: 500; margin-bottom: 10px; color: #1C1917; }
.company-meta { font-family: 'Inter', sans-serif; font-size: 0.8125rem; color: #57534E; line-height: 1.5; margin-bottom: 12px; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 10px; border-top: 1px solid #FDBA74; }
.sparkline-bar { flex: 1; background: #FDBA74; min-height: 2px; transition: background 250ms; }
.company:hover .sparkline-bar { background: #9A3412; opacity: 0.7; }
.sparkline-label { font-family: 'Inter', sans-serif; font-size: 0.6875rem; color: #78716C; letter-spacing: 0.05em; margin-top: 6px; }

.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: #FFFBEB; border: 1px solid #FDBA74; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 20px 24px; text-align: left; border-bottom: 1px solid #FDBA74; font-size: 0.9375rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: rgba(254, 215, 170, 0.3); font-family: 'Playfair Display', serif; font-weight: 500; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.15em; color: #57534E; }
.salary-stage { font-family: 'Playfair Display', serif; font-weight: 500; color: #1C1917; font-size: 1.0625rem; }
.salary-bar { display: inline-block; width: 80px; height: 4px; background: #FED7AA; margin-left: 12px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #9A3412; }
.yoy { display: inline-block; font-family: 'Playfair Display', serif; font-size: 0.8125rem; font-weight: 500; margin-left: 12px; padding: 2px 8px; }
.yoy.up   { color: #15803D; }
.yoy.down { color: #B91C1C; }
.yoy.flat { color: #78716C; }
.approx { font-family: 'Playfair Display', serif; color: #F59E0B; margin-right: 4px; }

.direction-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 160px 1fr 60px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #FDBA74; }
.direction:last-child { border-bottom: none; }
.direction-name { font-family: 'Playfair Display', serif; font-size: 1.0625rem; color: #1C1917; }
.direction-bar { height: 6px; background: #FED7AA; overflow: hidden; }
.direction-bar-fill { height: 100%; background: #9A3412; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); }
.direction-pct { font-family: 'Playfair Display', serif; font-weight: 500; text-align: right; font-size: 1.0625rem; color: #1C1917; }

.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: #FFFBEB; border: 1px solid #FDBA74; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #9A3412; transform: translateY(-2px); }
.path-pct { font-family: 'Playfair Display', serif; font-size: 2.75rem; font-weight: 500; color: #9A3412; margin-bottom: 4px; line-height: 1; }
.path-name { font-family: 'Inter', sans-serif; color: #57534E; font-size: 0.75rem; letter-spacing: 0.12em; margin-top: 8px; text-transform: uppercase; }

.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 32px 36px; background: #FFFBEB; border: 1px solid #FDBA74; border-left: 4px solid #F59E0B; margin-bottom: 20px; transition: border-left-width 250ms, transform 250ms, box-shadow 250ms; position: relative; }
.quote:hover { border-left-width: 12px; transform: translateX(4px); box-shadow: 0 8px 24px rgba(245, 158, 11, 0.15); }
.quote-head { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.quote-avatar { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #9A3412; color: #FFFBEB; font-family: 'Playfair Display', serif; font-size: 1.125rem; font-weight: 500; }
.quote-byline strong { display: block; font-family: 'Playfair Display', serif; font-weight: 500; color: #1C1917; font-size: 1rem; }
.quote-byline .quote-source { font-family: 'Inter', sans-serif; color: #78716C; font-size: 0.75rem; }
.quote-text { font-family: 'Caveat', cursive; font-size: 1.625rem; line-height: 1.55; color: #1C1917; font-weight: 500; }
.quote-text::before { content: "“"; color: #F59E0B; font-size: 1.4em; line-height: 0; vertical-align: -0.2em; margin-right: 4px; }
.quote-text::after { content: "”"; color: #F59E0B; font-size: 1.4em; line-height: 0; vertical-align: -0.2em; margin-left: 4px; }

.xuanke-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 220px 1fr 80px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #FDBA74; }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-family: 'Playfair Display', serif; font-size: 1.0625rem; color: #1C1917; }
.xuanke-bar { height: 6px; background: #FED7AA; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #9A3412; }
.xuanke-pct { font-family: 'Playfair Display', serif; font-weight: 500; text-align: right; font-size: 1.0625rem; color: #1C1917; }

.curriculum-lede { font-family: 'Playfair Display', serif; color: #57534E; font-size: 1.0625rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.curriculum-block { padding: 32px 28px; background: #FFFBEB; border: 1px solid #FDBA74; transition: border-color 250ms, transform 250ms; }
.curriculum-block:hover { border-color: #9A3412; transform: translateY(-2px); }
.curriculum-title { font-family: 'Playfair Display', serif; font-size: 1.0625rem; color: #9A3412; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #FDBA74; font-weight: 500; }
.course { padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; font-size: 0.9375rem; }
.course-name { font-family: 'Inter', sans-serif; color: #1C1917; }
.course-credit { font-family: 'Playfair Display', serif; color: #78716C; font-size: 0.8125rem; margin-left: 8px; }

.cta-block { margin-top: 32px; padding: 64px 48px; background: #FFFBEB; border: 2px solid #9A3412; text-align: center; position: relative; }
.cta-block::before { content: "❀  ❀  ❀"; position: absolute; top: -16px; left: 50%; transform: translateX(-50%); background: #FFFBEB; padding: 0 16px; color: #F59E0B; font-size: 1.25rem; letter-spacing: 0.5em; }
.cta-block::after { content: "❀  ❀  ❀"; position: absolute; bottom: -16px; left: 50%; transform: translateX(-50%); background: #FFFBEB; padding: 0 16px; color: #F59E0B; font-size: 1.25rem; letter-spacing: 0.5em; }
.cta-block h3 { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 500; margin-bottom: 16px; color: #1C1917; }
.cta-block p { font-family: 'Cormorant Garamond', serif; color: #57534E; margin: 0 auto 32px; max-width: 560px; font-size: 1.0625rem; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }
.cta-input { padding: 14px 18px; background: #FFFFFF; border: 1px solid #FDBA74; color: #1C1917; font-family: 'Inter', sans-serif; font-size: 1rem; width: 180px; outline: none; }
.cta-input:focus { border-color: #9A3412; }
.cta-button { padding: 14px 40px; background: #9A3412; color: #FFFBEB; font-family: 'Playfair Display', serif; font-size: 1rem; font-weight: 500; letter-spacing: 0.06em; transition: background 200ms; }
.cta-button:hover { background: #C2410C; }
.cta-note { font-family: 'Inter', sans-serif; color: #78716C; font-size: 0.75rem; margin-top: 20px; }

.watermark { color: #9A3412; opacity: 0.04; }
.section-num { font-family: 'Playfair Display', serif; color: #9A3412; }
section.tab h2 { font-family: 'Playfair Display', serif; }
section.tab p { color: #1C1917; }
section.tab p.lede { color: #57534E; }
section.tab h3 { color: #1C1917; }
footer { background: #FFFBEB; border-top: 1px solid #FDBA74; }
footer .label { color: #9A3412; }
footer .data-source { color: #78716C; }

.drop-cap::first-letter { font-family: 'Playfair Display', serif; font-size: 4.5em; font-weight: 500; line-height: 0.85; float: left; margin: 0.05em 0.12em 0 0; color: #9A3412; }
"""


# ──────────────────────────────────────────────────────────
# Tech 极致: 深紫 + 青绿 + 几何 — 给非终端的暗色调 (AI/DS/CS-soft)
# ──────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────
# 4 套共用的渲染逻辑 (招 #2/3/4/8 都内置)
# ──────────────────────────────────────────────────────────

HUMANITIES_CSS = """
/* ── 招 #5: 翻开的线装书 hero + 米白宣纸底层 ── */
.hero { padding: 80px 0 96px; background: transparent; border-bottom: 1px solid #C5B89A; position: relative; z-index: 2; overflow: hidden; }
.book-shell { position: relative; display: grid; grid-template-columns: 1fr 36px 1fr; gap: 0; max-width: 1080px; margin: 0 auto; transform: rotate(-1.2deg); }
.book-page { position: relative; aspect-ratio: 1.45/1; padding: 36px 32px; background: linear-gradient(135deg, #F2E8D5 0%, #EBDDC7 100%); border: 1px solid #C5B89A; box-shadow: inset 0 0 40px rgba(139, 90, 43, 0.08), 0 8px 32px rgba(31, 20, 10, 0.12); overflow: hidden; }
.book-page::before { content: ""; position: absolute; inset: 0; pointer-events: none; background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='3'/><feColorMatrix values='0 0 0 0 0.55 0 0 0 0 0.42 0 0 0 0 0.20 0 0 0 0.10 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.4'/></svg>"); mix-blend-mode: multiply; opacity: 0.6; }
.book-page::after { content: ""; position: absolute; inset: 8px; border: 1px dashed rgba(184, 137, 58, 0.45); pointer-events: none; }
.book-page.left { border-radius: 4px 0 0 4px; }
.book-page.right { border-radius: 0 4px 4px 0; }
.book-spine { background: linear-gradient(90deg, #8B5A2B 0%, #6B4226 50%, #8B5A2B 100%); position: relative; display: flex; flex-direction: column; align-items: center; justify-content: space-evenly; padding: 18px 0; box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.4); }
.book-spine::before { content: ""; position: absolute; top: 0; bottom: 0; left: 50%; width: 2px; background: rgba(255, 255, 255, 0.15); transform: translateX(-50%); }
.book-stitch { width: 6px; height: 6px; background: #F2E8D5; border-radius: 50%; box-shadow: 0 0 0 1px #6B4226; }
/* 顶部题首 */
.hu-topline { font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif; font-size: 0.75rem; color: #8B5A2B; letter-spacing: 0.4em; text-align: center; padding: 16px 0 8px; position: relative; z-index: 2; }
.hu-topline::after { content: ""; display: block; width: 80px; height: 1px; background: linear-gradient(90deg, transparent, #B8893A, transparent); margin: 8px auto 0; }
/* 左页扉页式: 朱砂引首章 + 巨型标题 + 引文 */
.hu-seal { position: absolute; top: 20px; right: 24px; width: 56px; height: 56px; background: #9A2A2A; display: flex; align-items: center; justify-content: center; font-family: 'Ma Shan Zheng', cursive; font-size: 1.5rem; color: #F2E8D5; transform: rotate(-3deg); box-shadow: 0 0 0 2px #F2E8D5 inset, 0 2px 4px rgba(0, 0, 0, 0.2); opacity: 0.9; }
.hu-seal::before { content: ""; position: absolute; inset: 4px; border: 1px solid rgba(242, 232, 213, 0.5); pointer-events: none; }
.hu-watermark { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-family: 'Noto Serif SC', serif; font-size: 14rem; font-weight: 900; color: #1F140A; opacity: 0.05; pointer-events: none; line-height: 1; user-select: none; }
.hu-title { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: clamp(3rem, 6vw, 5rem); color: #1F140A; line-height: 1.1; letter-spacing: 0.05em; position: relative; z-index: 2; }
.hu-subtitle { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 1rem; color: #8B5A2B; margin-top: 12px; letter-spacing: 0.05em; position: relative; z-index: 2; }
.hu-quote { position: relative; z-index: 2; margin-top: 32px; padding-left: 14px; border-left: 3px solid #9A2A2A; font-family: 'Noto Serif SC', serif; font-size: 0.875rem; color: #1F140A; line-height: 1.7; }
.hu-quote-sig { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.75rem; color: #6B5D3F; margin-top: 6px; }
/* 右页校勘式 stats */
.hu-folio { position: absolute; top: 16px; left: 24px; font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.6875rem; color: #8B5A2B; letter-spacing: 0.2em; z-index: 2; }
.hu-folio-right { position: absolute; top: 16px; right: 24px; font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.6875rem; color: #8B5A2B; letter-spacing: 0.2em; z-index: 2; }
.hero-stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 32px 0 24px; position: relative; z-index: 2; }
.hu-stat { padding: 14px 12px; background: rgba(255, 255, 255, 0.4); border: 1px dashed rgba(184, 137, 58, 0.6); position: relative; }
.hu-stat::after { content: ""; position: absolute; inset: 4px; border: 1px dashed rgba(184, 137, 58, 0.3); pointer-events: none; }
.hu-stat-seal { position: absolute; top: -8px; left: -8px; width: 24px; height: 24px; background: #9A2A2A; color: #F2E8D5; font-family: 'Ma Shan Zheng', cursive; font-size: 0.875rem; display: flex; align-items: center; justify-content: center; transform: rotate(-4deg); z-index: 3; }
.stat-label { font-family: 'Noto Serif SC', serif; font-size: 0.6875rem; color: #6B5D3F; text-transform: uppercase; letter-spacing: 0.15em; }
.stat-value { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 700; color: #1F140A; margin-top: 4px; }
/* 目录: 壹/貳/參/肆 */
.hu-toc { list-style: none; padding: 0; margin: 0; position: relative; z-index: 2; }
.hu-toc li { display: grid; grid-template-columns: 28px 1fr auto; align-items: baseline; gap: 10px; padding: 6px 0; border-bottom: 1px dotted rgba(184, 137, 58, 0.4); font-family: 'Noto Serif SC', serif; font-size: 0.875rem; color: #1F140A; }
.hu-toc li:last-child { border-bottom: none; }
.hu-toc-cnum { font-family: 'Ma Shan Zheng', cursive; color: #9A2A2A; font-size: 1.0625rem; }
.hu-toc-name { color: #1F140A; }
.hu-toc-pg { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #8B5A2B; font-size: 0.75rem; }
/* 底部版权条 */
.hu-foot { text-align: center; font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.6875rem; color: #6B5D3F; letter-spacing: 0.2em; padding-top: 16px; position: relative; z-index: 2; }
section.tab { border-top: 1px solid #C5B89A; border-bottom: 1px solid #C5B89A; }
section.tab:first-of-type { border-top: none; }
section.tab:last-of-type { border-bottom: none; }
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.bento-item { padding: 28px 24px 24px; background: #FBF6E9; border: 1px solid #C5B89A; border-radius: 4px; position: relative; transition: border-color 250ms, transform 250ms; box-shadow: 0 1px 0 rgba(92, 124, 90, 0.04); }
.bento-item::before { content: "○"; position: absolute; top: 20px; right: 20px; color: #8B5A2B; font-size: 0.875rem; opacity: 0.5; }
.bento-item:nth-child(3) { position: relative; }
.bento-item:nth-child(3)::before, .bento-item:nth-child(6)::before, .bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: #8B5A2B; z-index: 1; pointer-events: none; }
.bento-item:hover { border-color: #8B5A2B; transform: translateY(-2px); }
.bento-monogram { position: absolute; top: 20px; right: 50px; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #1F140A; color: #F2E8D5; font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 700; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #1F140A; border: 1px solid #1F140A; border-radius: 0; font-family: 'Noto Serif SC', serif; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; margin-bottom: 12px; }
.bento-name { font-family: 'Noto Serif SC', serif; font-size: 1.1875rem; font-weight: 700; margin-bottom: 4px; color: #1F140A; padding-right: 80px; text-wrap: balance; line-height: 1.3; }
.bento-tag { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.8125rem; color: #6B5D3F; line-height: 1.5; }
.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 28px 24px 22px; background: #FBF6E9; border: 1px solid #C5B89A; border-radius: 4px; position: relative; transition: border-color 250ms, transform 250ms; }
.company:hover { border-color: #8B5A2B; transform: translateY(-2px); }
.company-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.company-monogram { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #1F140A; color: #F2E8D5; font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 700; }
.company-tier { padding: 2px 8px; border: 1px solid #8B5A2B; color: #8B5A2B; font-family: 'Noto Serif SC', serif; font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.1em; }
.tier-S { background: #1F140A; color: #F2E8D5; border-color: #1F140A; }
.tier-A { background: transparent; }
.tier-B { background: transparent; color: #6B5D3F; border-color: #C5B89A; }
.company-name { font-family: 'Noto Serif SC', serif; font-size: 1.1875rem; font-weight: 700; margin-bottom: 8px; color: #1F140A; }
.company-meta { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.8125rem; color: #6B5D3F; line-height: 1.5; margin-bottom: 12px; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 10px; border-top: 1px solid #E8DFC8; }
.sparkline-bar { flex: 1; background: #C5B89A; min-height: 2px; transition: background 250ms; }
.company:hover .sparkline-bar { background: #8B5A2B; opacity: 0.7; }
.sparkline-label { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.6875rem; color: #6B5D3F; letter-spacing: 0.05em; margin-top: 6px; }
.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: #FBF6E9; border: 1px solid #C5B89A; border-radius: 4px; overflow: hidden; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 20px 24px; text-align: left; border-bottom: 1px solid #E8DFC8; font-size: 0.9375rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: #F2E8D5; font-family: 'Noto Serif SC', serif; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.12em; color: #6B5D3F; }
.salary-stage { font-family: 'Noto Serif SC', serif; font-weight: 700; color: #1F140A; font-size: 1.0625rem; }
.salary-bar { display: inline-block; width: 80px; height: 4px; background: #E8DFC8; margin-left: 12px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #8B5A2B; }
.yoy { display: inline-block; font-family: 'Noto Serif SC', serif; font-size: 0.8125rem; font-weight: 600; margin-left: 12px; padding: 2px 8px; }
.yoy.up   { color: #8B5A2B; }
.yoy.down { color: #9A2A2A; }
.yoy.flat { color: #6B5D3F; }
.approx { font-family: 'Noto Serif SC', serif; color: #8B5A2B; margin-right: 4px; }
.direction-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 160px 1fr 60px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #E8DFC8; }
.direction:last-child { border-bottom: none; }
.direction-name { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; color: #1F140A; }
.direction-bar { height: 6px; background: #E8DFC8; overflow: hidden; }
.direction-bar-fill { height: 100%; background: #8B5A2B; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); }
.direction-pct { font-family: 'Noto Serif SC', serif; font-weight: 700; text-align: right; font-size: 1.0625rem; color: #8B5A2B; }
.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: #FBF6E9; border: 1px solid #C5B89A; border-radius: 4px; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #8B5A2B; transform: translateY(-2px); }
.path-pct { font-family: 'Noto Serif SC', serif; font-size: 2.5rem; font-weight: 700; color: #1F140A; margin-bottom: 4px; line-height: 1; }
.path-name { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #6B5D3F; font-size: 0.875rem; margin-top: 8px; }
.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 28px 32px 24px; background: #FBF6E9; border: 1px solid #C5B89A; border-left: 4px solid #9A2A2A; border-radius: 0 4px 4px 0; margin-bottom: 16px; transition: border-left-width 250ms, transform 250ms; }
.quote:hover { border-left-width: 12px; transform: translateX(4px); }
.quote-head { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.quote-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #1F140A; color: #F2E8D5; font-family: 'Noto Serif SC', serif; font-size: 1rem; font-weight: 700; }
.quote-byline strong { display: block; font-family: 'Noto Serif SC', serif; font-weight: 700; color: #1F140A; font-size: 0.9375rem; }
.quote-byline .quote-source { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #6B5D3F; font-size: 0.75rem; }
.quote-text { font-family: 'Noto Serif SC', serif; font-style: italic; font-size: 1.1875rem; line-height: 1.65; color: #1F140A; }
.quote-text::before { content: "「"; color: #9A2A2A; }
.quote-text::after { content: "」"; color: #9A2A2A; }
.xuanke-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 200px 1fr 80px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #E8DFC8; }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; color: #1F140A; }
.xuanke-bar { height: 6px; background: #E8DFC8; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #8B5A2B; }
.xuanke-pct { font-family: 'Noto Serif SC', serif; font-weight: 700; text-align: right; font-size: 1.0625rem; color: #8B5A2B; }
.curriculum-lede { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #6B5D3F; font-size: 1.0625rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.curriculum-block { padding: 28px 24px; background: #FBF6E9; border: 1px solid #C5B89A; border-radius: 4px; transition: border-color 250ms, transform 250ms; }
.curriculum-block:hover { border-color: #8B5A2B; transform: translateY(-2px); }
.curriculum-title { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; color: #1F140A; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #C5B89A; font-weight: 700; }
.course { padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; font-size: 0.9375rem; }
.course-name { font-family: 'Noto Serif SC', serif; color: #1F140A; }
.course-credit { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #6B5D3F; font-size: 0.8125rem; margin-left: 8px; }
.cta-block { margin-top: 32px; padding: 64px 48px; background: #FBF6E9; border: 1px solid #1F140A; text-align: center; position: relative; }
.cta-block::before { content: "○  ○  ○"; position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: #F2E8D5; padding: 0 16px; color: #1F140A; font-size: 0.875rem; letter-spacing: 0.5em; }
.cta-block h3 { font-family: 'Noto Serif SC', serif; font-size: 1.75rem; margin-bottom: 12px; color: #1F140A; position: relative; z-index: 1; font-weight: 700; }
.cta-block p { color: #6B5D3F; margin: 0 auto 28px; max-width: 560px; position: relative; z-index: 1; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; position: relative; z-index: 1; }
.cta-input { padding: 14px 18px; background: #F2E8D5; border: 1px solid #C5B89A; color: #1F140A; font-family: 'Noto Serif SC', serif; font-size: 1rem; width: 180px; outline: none; }
.cta-input:focus { border-color: #8B5A2B; }
.cta-button { padding: 14px 36px; background: #1F140A; color: #F2E8D5; font-family: 'Noto Serif SC', serif; font-size: 1rem; font-weight: 700; letter-spacing: 0.05em; }
.cta-note { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.75rem; color: #6B5D3F; margin-top: 16px; position: relative; z-index: 1; }
.watermark { color: #8B5A2B; opacity: 0.04; }
.section-num { color: #8B5A2B; font-family: 'Noto Serif SC', serif; }
section.tab h2 { font-family: 'Noto Serif SC', serif; color: #1F140A; }
section.tab p { color: #1F140A; }
section.tab p.lede { color: #6B5D3F; font-style: italic; }
section.tab h3 { color: #1F140A; font-family: 'Noto Serif SC', serif; }
footer { background: #F2E8D5; border-top: 1px solid #C5B89A; }
footer .label { color: #1F140A; font-family: 'Noto Serif SC', serif; }
footer .data-source { color: #6B5D3F; }
.drop-cap::first-letter { font-family: 'Noto Serif SC', serif; font-size: 4.5em; font-weight: 900; line-height: 0.85; float: left; margin: 0.05em 0.12em 0 0; color: #9A2A2A; }
"""

ADMINISTRATION_CSS = """
/* ── 招 #5: 国发文件红头 + 公文纸主体 ── */
.hero { padding: 0; background: transparent; position: relative; z-index: 2; overflow: hidden; }
.gov-red-header { background: #1E3A5F; border-bottom: 3px double #D4AF37; padding: 14px 40px; display: flex; justify-content: space-between; align-items: center; font-family: 'IBM Plex Mono', monospace; font-size: 0.6875rem; color: #FAFAF6; letter-spacing: 0.15em; text-transform: uppercase; position: relative; z-index: 2; }
.gov-red-header strong { font-family: 'IBM Plex Serif', serif; font-size: 0.875rem; font-weight: 700; color: #FAFAF6; letter-spacing: 0.2em; }
.gov-red-header .doc-num { color: #D4AF37; }
.gov-redline { height: 4px; background: linear-gradient(90deg, #C0392B 0%, #C0392B 40%, #D4AF37 40%, #D4AF37 60%, #C0392B 60%, #C0392B 100%); }
.gov-paper { position: relative; padding: 56px 64px 64px; background: #FAFAF6; max-width: 1080px; margin: 0 auto; box-shadow: 0 4px 24px rgba(30, 58, 95, 0.08); }
.gov-paper::before { content: ""; position: absolute; inset: 0; pointer-events: none; background-image: repeating-linear-gradient(0deg, rgba(26, 36, 56, 0.02) 0px, transparent 1px, transparent 3px); }
.gov-paper::after { content: ""; position: absolute; top: 16px; right: 16px; bottom: 16px; left: 16px; border: 1px solid rgba(30, 58, 95, 0.1); pointer-events: none; }
.gov-doc-title { font-family: 'Noto Serif SC', 'IBM Plex Serif', serif; font-size: clamp(1.875rem, 3.5vw, 2.5rem); font-weight: 900; color: #C0392B; text-align: center; letter-spacing: 0.4em; margin: 8px 0 8px; position: relative; }
.gov-doc-no { text-align: center; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #1E3A5F; letter-spacing: 0.2em; margin-bottom: 32px; position: relative; }
.gov-doc-no::before, .gov-doc-no::after { content: "〔"; color: #1E3A5F; }
.gov-doc-no::after { content: "〕"; }
.gov-doc-line { width: 60%; height: 1px; background: linear-gradient(90deg, transparent, #C0392B, transparent); margin: 12px auto; opacity: 0.6; position: relative; }
.gov-stamp { position: absolute; top: 32px; right: 32px; width: 96px; height: 96px; border: 2px solid #C0392B; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: 'Noto Serif SC', serif; font-size: 0.625rem; font-weight: 700; color: #C0392B; text-align: center; line-height: 1.3; transform: rotate(-8deg); opacity: 0.85; z-index: 3; }
.gov-stamp::before { content: "★"; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 1.25rem; color: #C0392B; opacity: 0.3; }
.gov-stamp-text { position: relative; z-index: 1; }
.gov-seal-strip { position: absolute; top: 50%; right: -8px; transform: translateY(-50%); background: #C0392B; color: #FAFAF6; padding: 6px 10px; font-family: 'Noto Serif SC', serif; font-size: 0.625rem; font-weight: 700; letter-spacing: 0.2em; writing-mode: vertical-rl; z-index: 3; }
.gov-h1 { font-family: 'Noto Serif SC', 'IBM Plex Serif', serif; font-size: clamp(2.25rem, 5vw, 3.5rem); font-weight: 900; color: #1A2438; text-align: center; line-height: 1.2; margin: 24px 0 16px; letter-spacing: 0.06em; position: relative; }
.gov-tagline { font-family: 'IBM Plex Serif', 'Noto Serif SC', serif; font-size: 1.0625rem; color: #1A2438; text-align: center; margin: 0 auto 32px; max-width: 720px; line-height: 1.7; position: relative; }
.gov-tagline::before { content: "— "; color: #C0392B; }
.gov-tagline::after { content: " —"; color: #C0392B; }
.gov-tags { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-bottom: 40px; position: relative; }
.gov-tag { padding: 6px 14px; background: transparent; border: 1px solid #1E3A5F; font-family: 'Noto Serif SC', serif; font-size: 0.875rem; color: #1E3A5F; letter-spacing: 0.05em; }
.gov-tag.primary { background: #1E3A5F; color: #FAFAF6; font-weight: 700; }
.gov-stats { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #1E3A5F; border-bottom: 1px solid #1E3A5F; max-width: 880px; margin: 0 auto; position: relative; }
.gov-stats .stat { padding: 20px 16px; border-right: 1px solid #C5C5B5; background: rgba(30, 58, 95, 0.02); position: relative; }
.gov-stats .stat:last-child { border-right: none; }
.gov-stats .stat::before { content: "〔" attr(data-num) "〕"; position: absolute; top: 6px; right: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 0.5625rem; color: #C0392B; }
.gov-stats .stat-label { font-family: 'IBM Plex Serif', serif; font-size: 0.6875rem; color: #5A6A7A; letter-spacing: 0.15em; text-transform: uppercase; font-weight: 500; }
.gov-stats .stat-value { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 700; color: #1A2438; margin-top: 4px; }
.gov-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 40px; padding-top: 16px; border-top: 1px dashed #C5C5B5; font-family: 'IBM Plex Mono', monospace; font-size: 0.6875rem; color: #5A6A7A; letter-spacing: 0.1em; }
section.tab { border-top: 1px solid #C5C5B5; border-bottom: 1px solid #C5C5B5; }
section.tab:first-of-type { border-top: none; }
section.tab:last-of-type { border-bottom: none; }
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.bento-item { padding: 28px 24px 24px; background: #FFFFFF; border: 1px solid #C5C5B5; position: relative; transition: border-color 250ms, transform 250ms; }
.bento-item::before { content: "■"; position: absolute; top: 20px; right: 20px; color: #1E3A5F; font-size: 0.75rem; opacity: 0.5; }
.bento-item:nth-child(3) { position: relative; }
.bento-item:nth-child(3)::before, .bento-item:nth-child(6)::before, .bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: #1E3A5F; z-index: 1; pointer-events: none; }
.bento-item:hover { border-color: #1E3A5F; transform: translateY(-2px); }
.bento-monogram { position: absolute; top: 20px; right: 50px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: #1E3A5F; color: #FAFAF6; font-family: 'IBM Plex Serif', serif; font-size: 1.0625rem; font-weight: 700; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #1E3A5F; border: 1px solid #1E3A5F; font-family: 'IBM Plex Serif', serif; font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.1em; margin-bottom: 12px; }
.bento-name { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 700; margin-bottom: 4px; color: #1A2438; padding-right: 80px; text-wrap: balance; line-height: 1.35; }
.bento-tag { font-family: 'IBM Plex Serif', serif; font-size: 0.8125rem; color: #5A6A7A; line-height: 1.5; }
.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 24px 22px 20px; background: #FFFFFF; border: 1px solid #C5C5B5; position: relative; transition: border-color 250ms, transform 250ms; }
.company:hover { border-color: #1E3A5F; transform: translateY(-2px); }
.company-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.company-monogram { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: #1E3A5F; color: #FAFAF6; font-family: 'IBM Plex Serif', serif; font-size: 1rem; font-weight: 700; }
.company-tier { padding: 2px 8px; border: 1px solid #1E3A5F; color: #1E3A5F; font-family: 'IBM Plex Serif', serif; font-size: 0.625rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }
.tier-S { background: #1E3A5F; color: #FAFAF6; }
.tier-A { background: transparent; }
.tier-B { background: transparent; color: #5A6A7A; border-color: #C5C5B5; }
.company-name { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 700; margin-bottom: 8px; color: #1A2438; }
.company-meta { font-family: 'IBM Plex Serif', serif; font-size: 0.8125rem; color: #5A6A7A; line-height: 1.5; margin-bottom: 8px; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 8px; border-top: 1px solid #E5E5DC; }
.sparkline-bar { flex: 1; background: #C5C5B5; min-height: 2px; transition: background 250ms; }
.company:hover .sparkline-bar { background: #1E3A5F; opacity: 0.8; }
.sparkline-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.625rem; color: #5A6A7A; letter-spacing: 0.1em; margin-top: 4px; }
.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: #FFFFFF; border: 1px solid #C5C5B5; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 18px 24px; text-align: left; border-bottom: 1px solid #E5E5DC; font-size: 0.875rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: rgba(30, 58, 95, 0.04); font-family: 'IBM Plex Serif', serif; font-weight: 700; font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.12em; color: #1E3A5F; }
.salary-stage { font-family: 'Noto Serif SC', serif; font-weight: 700; color: #1A2438; }
.salary-bar { display: inline-block; width: 80px; height: 6px; background: #E5E5DC; margin-left: 8px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #1E3A5F; }
.yoy { display: inline-block; font-family: 'IBM Plex Serif', serif; font-size: 0.75rem; font-weight: 600; margin-left: 12px; padding: 2px 6px; }
.yoy.up   { color: #1E3A5F; }
.yoy.down { color: #C0392B; }
.yoy.flat { color: #5A6A7A; }
.approx { font-family: 'IBM Plex Mono', monospace; color: #5A6A7A; margin-right: 4px; }
.direction-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 160px 1fr 60px; align-items: center; gap: 20px; padding: 14px 0; border-bottom: 1px solid #E5E5DC; }
.direction:last-child { border-bottom: none; }
.direction-name { font-family: 'Noto Serif SC', serif; font-weight: 600; font-size: 0.9375rem; color: #1A2438; }
.direction-bar { height: 8px; background: #E5E5DC; overflow: hidden; }
.direction-bar-fill { height: 100%; background: #1E3A5F; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); }
.direction-pct { font-family: 'IBM Plex Mono', monospace; font-weight: 700; text-align: right; font-size: 0.9375rem; color: #1A2438; }
.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: #FFFFFF; border: 1px solid #C5C5B5; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #1E3A5F; transform: translateY(-2px); }
.path-pct { font-family: 'Noto Serif SC', serif; font-size: 2.5rem; font-weight: 700; color: #1E3A5F; margin-bottom: 4px; letter-spacing: -0.02em; line-height: 1; }
.path-name { font-family: 'Noto Serif SC', serif; color: #5A6A7A; font-size: 0.8125rem; margin-top: 8px; }
.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 28px 32px 24px; background: #FFFFFF; border: 1px solid #C5C5B5; border-left: 3px solid #1E3A5F; margin-bottom: 16px; transition: border-left-width 250ms, transform 250ms; }
.quote:hover { border-left-width: 8px; transform: translateX(4px); }
.quote-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.quote-avatar { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: #1E3A5F; color: #FAFAF6; font-family: 'IBM Plex Serif', serif; font-size: 1rem; font-weight: 700; }
.quote-byline strong { display: block; font-family: 'Noto Serif SC', serif; font-weight: 700; color: #1A2438; font-size: 0.875rem; }
.quote-byline .quote-source { font-family: 'IBM Plex Serif', serif; color: #5A6A7A; font-size: 0.75rem; }
.quote-text { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; line-height: 1.7; color: #1A2438; }
.quote-text::before { content: "「"; color: #C0392B; }
.quote-text::after { content: "」"; color: #C0392B; }
.xuanke-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 200px 1fr 80px; align-items: center; gap: 20px; padding: 14px 0; border-bottom: 1px solid #E5E5DC; }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-family: 'Noto Serif SC', serif; font-weight: 600; font-size: 0.9375rem; color: #1A2438; }
.xuanke-bar { height: 8px; background: #E5E5DC; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #1E3A5F; }
.xuanke-pct { font-family: 'IBM Plex Mono', monospace; font-weight: 700; text-align: right; font-size: 0.9375rem; color: #1E3A5F; }
.curriculum-lede { color: #5A6A7A; font-size: 0.9375rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.curriculum-block { padding: 28px 24px; background: #FFFFFF; border: 1px solid #C5C5B5; transition: border-color 250ms, transform 250ms; }
.curriculum-block:hover { border-color: #1E3A5F; transform: translateY(-2px); }
.curriculum-title { font-family: 'Noto Serif SC', serif; font-size: 0.6875rem; color: #1E3A5F; text-transform: uppercase; letter-spacing: 0.15em; font-weight: 700; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #C5C5B5; }
.course { padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; font-size: 0.9375rem; }
.course-name { color: #1A2438; font-weight: 500; font-family: 'Noto Serif SC', serif; }
.course-credit { color: #5A6A7A; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; margin-left: 8px; }
.cta-block { margin-top: 32px; padding: 64px 48px; background: #FFFFFF; border: 1px solid #1E3A5F; text-align: center; position: relative; }
.cta-block::before { content: "〔 关联志愿 · 推荐填报 〕"; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #FAFAF6; padding: 0 16px; color: #1E3A5F; font-size: 0.75rem; letter-spacing: 0.2em; font-family: 'IBM Plex Serif', serif; }
.cta-block h3 { font-family: 'Noto Serif SC', serif; font-size: 1.75rem; margin-bottom: 12px; color: #1A2438; position: relative; z-index: 1; }
.cta-block p { color: #5A6A7A; margin: 0 auto 28px; max-width: 560px; position: relative; z-index: 1; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; position: relative; z-index: 1; }
.cta-input { padding: 14px 18px; background: #FAFAF6; border: 1px solid #C5C5B5; color: #1A2438; font-family: 'Noto Serif SC', serif; font-size: 1rem; width: 180px; outline: none; }
.cta-input:focus { border-color: #1E3A5F; }
.cta-button { padding: 14px 36px; background: #C0392B; color: #FAFAF6; font-family: 'Noto Serif SC', serif; font-size: 0.9375rem; font-weight: 700; letter-spacing: 0.1em; }
.cta-note { font-family: 'IBM Plex Serif', serif; font-size: 0.75rem; color: #5A6A7A; margin-top: 16px; position: relative; z-index: 1; }
.watermark { color: #1E3A5F; opacity: 0.04; }
.section-num { color: #C0392B; font-family: 'IBM Plex Serif', serif; }
section.tab h2 { font-family: 'Noto Serif SC', serif; color: #1A2438; }
section.tab p { color: #1A2438; }
section.tab p.lede { color: #5A6A7A; }
section.tab h3 { color: #1A2438; font-family: 'Noto Serif SC', serif; }
footer { background: #FAFAF6; border-top: 1px solid #C5C5B5; }
footer .label { color: #1E3A5F; font-family: 'IBM Plex Serif', serif; }
footer .data-source { color: #5A6A7A; }
.drop-cap::first-letter { font-family: 'Noto Serif SC', serif; font-size: 4em; font-weight: 900; line-height: 0.9; float: left; margin: 0.05em 0.12em 0 0; color: #C0392B; }
"""

# ──────────────────────────────────────────────────────────
# AGRI (农林) — 林奈式植物图鉴 + 标本夹 + 朱砂印
# ──────────────────────────────────────────────────────────
AGRI_CSS = """
/* 招 #6 字体 */
.hero, .hero * { --font-heading: 'Noto Serif SC', 'Cormorant Garamond', serif; --font-num: 'Cormorant Garamond', serif; }
section.tab h1, section.tab h2, section.tab h3, section.tab h4 { font-family: var(--font-heading); }
section.tab p, section.tab li { font-family: 'Noto Serif SC', 'Source Han Serif SC', serif; }
.num, .num * { font-family: 'Cormorant Garamond', 'Source Han Serif SC', serif; font-variant-numeric: oldstyle-nums; font-feature-settings: 'onum' 1; }

.hero { padding: 0; background: transparent; border-bottom: 1px solid #B8CC98; position: relative; z-index: 2; overflow: hidden; min-height: 720px; }
.hero .container { position: relative; z-index: 3; }

/* ── 木桌 (含线纹) ── */
.desk {
  position: absolute; inset: 0; z-index: 1;
  background:
    repeating-linear-gradient(90deg,
      rgba(107,142,35,0.0) 0px, rgba(107,142,35,0.0) 120px,
      rgba(107,142,35,0.08) 121px, rgba(107,142,35,0.0) 122px,
      rgba(107,142,35,0.0) 260px, rgba(107,142,35,0.10) 261px, rgba(107,142,35,0.0) 262px),
    linear-gradient(180deg, #F0F5E2 0%, #E0E8C8 100%);
}
.sunbeam {
  position: absolute; top: -180px; left: 30%;
  transform: rotate(20deg);
  width: 700px; height: 1100px;
  background: linear-gradient(180deg, rgba(255,250,200,0.25) 0%, rgba(255,250,200,0.10) 30%, transparent 70%);
  z-index: 2; pointer-events: none; filter: blur(20px);
}

/* ── 角标 ── */
.corner-mark { position: absolute; width: 22px; height: 22px; z-index: 4; }
.corner-mark::before, .corner-mark::after { content: ""; position: absolute; background: #2E5A2E; }
.corner-mark::before { width: 22px; height: 1.5px; }
.corner-mark::after { width: 1.5px; height: 22px; }
.cm-tl { top: 24px; left: 24px; }
.cm-tr { top: 24px; right: 24px; }
.cm-tr::before { right: 0; }
.cm-tr::after { right: 0; }
.cm-bl { bottom: 24px; left: 24px; }
.cm-bl::before { bottom: 0; }
.cm-bl::after { bottom: 0; }
.cm-br { bottom: 24px; right: 24px; }
.cm-br::before { right: 0; bottom: 0; }
.cm-br::after { right: 0; bottom: 0; }

/* ── 顶部题首 ── */
.top-mark {
  position: absolute; top: 36px; left: 50%; transform: translateX(-50%);
  font-family: 'Cormorant Garamond', serif; font-style: italic;
  font-size: 0.75rem; letter-spacing: 0.3em; text-transform: uppercase;
  color: #6B8E23; z-index: 4; white-space: nowrap;
}
.top-mark::before, .top-mark::after { content: "·"; margin: 0 12px; color: #B8CC98; }

/* ── 标本夹 ── */
.herbarium-stage {
  position: relative;
  margin: 0 auto;
  max-width: 1080px;
  padding: 22px 12px;
  z-index: 5;
}
.press-cover {
  position: relative;
  background: linear-gradient(135deg, #A8C088 0%, #B8CC98 25%, #98B078 50%, #A8C088 75%, #88A868 100%);
  border-radius: 3px;
  padding: 22px 12px;
  box-shadow:
    inset 0 0 50px rgba(46,90,46,0.20),
    inset 0 0 0 1.5px rgba(230,180,34,0.30),
    0 24px 48px rgba(46,90,46,0.30);
}
.press-cover::before {
  content: ""; position: absolute; inset: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='l'><feTurbulence type='fractalNoise' baseFrequency='2.2' numOctaves='2'/></filter><rect width='100%25' height='100%25' filter='url(%23l)'/></svg>");
  opacity: 0.30; mix-blend-mode: overlay; border-radius: 3px; pointer-events: none;
}
.press-cover::after {
  content: ""; position: absolute; inset: 18px;
  background:
    radial-gradient(circle 3.5px at 0% 0%, var(--paper) 100%, transparent),
    radial-gradient(circle 3.5px at 100% 0%, var(--paper) 100%, transparent),
    radial-gradient(circle 3.5px at 0% 100%, var(--paper) 100%, transparent),
    radial-gradient(circle 3.5px at 100% 100%, var(--paper) 100%, transparent);
  pointer-events: none;
}

.specimen-page {
  position: relative;
  min-height: 540px;
  background: linear-gradient(180deg, #F5F9EC 0%, #E8EFDC 50%, #F5F9EC 100%);
  box-shadow: inset 0 0 60px rgba(107,142,35,0.10), inset 0 0 0 1px rgba(107,142,35,0.20);
  overflow: hidden;
  padding: 48px 56px;
}
.specimen-page::before {
  content: ""; position: absolute; inset: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='320' height='320'><filter id='p'><feTurbulence type='fractalNoise' baseFrequency='1.6' numOctaves='2'/></filter><rect width='100%25' height='100%25' filter='url(%23p)'/></svg>");
  opacity: 0.4; mix-blend-mode: multiply; pointer-events: none;
}
.page-left { border-radius: 2px 10px 10px 2px; box-shadow: inset -10px 0 18px -6px rgba(60,80,40,0.22); }
.page-right { border-radius: 10px 2px 2px 10px; box-shadow: inset 10px 0 18px -6px rgba(60,80,40,0.22); }
.page-content { position: relative; z-index: 2; }
.chapter-mark {
  font-family: 'Cormorant Garamond', serif; font-style: italic; font-weight: 500;
  font-size: 0.75rem; letter-spacing: 0.3em; text-transform: uppercase;
  color: #6B8E23; margin-bottom: 16px;
}
.chapter-mark::before { content: "§ "; color: #B8902A; }

.hero-title {
  font-family: 'Noto Serif SC', 'Source Han Serif SC', serif; font-weight: 900;
  font-size: clamp(2.4rem, 5vw, 3.6rem); line-height: 1.05; letter-spacing: -0.02em;
  color: #2E5A2E; margin: 8px 0 12px;
}
.title-cn { display: block; }
.title-en {
  display: block; font-family: 'Cormorant Garamond', serif; font-style: italic;
  font-weight: 500; font-size: 0.55em; color: #6B8E23; margin-top: 6px; letter-spacing: 0.04em;
}
.ampersand { font-style: italic; color: #B8902A; font-weight: 400; padding: 0 0.05em; }
.lat-name { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #6B8E23; font-size: 0.95rem; }
.pull-quote {
  font-family: 'Noto Serif SC', serif; font-weight: 500;
  font-size: 0.92rem; line-height: 1.7; color: #2E5A2E;
  border-left: 2px solid #B8902A; padding: 4px 0 4px 14px; margin: 18px 0 6px;
}
.attribution { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.78rem; color: #6B8E23; }

/* ── 朱砂印 ── */
.seal {
  display: inline-block; background: #B83A2A; color: #FFE8B0;
  font-family: 'Noto Serif SC', serif; font-weight: 900;
  font-size: 0.7rem; line-height: 1; letter-spacing: 0.1em;
  padding: 4px 6px; margin: 4px;
  border: 1.5px solid #B83A2A; border-radius: 2px;
  box-shadow: 0 0 0 1px #FFE8B0 inset, 1px 1px 0 rgba(0,0,0,0.10);
  transform: rotate(-3deg);
}
.seal-vertical { writing-mode: vertical-rl; padding: 6px 4px; }
.hu-stat-seal { display: flex; gap: 4px; margin-top: 14px; }

/* ── 校勘式 stat (右页) ── */
.hu-stat {
  display: flex; align-items: baseline; gap: 12px;
  padding: 8px 0; border-bottom: 1px dashed rgba(107,142,35,0.25);
  font-family: 'Noto Serif SC', serif;
}
.hu-stat:last-child { border-bottom: none; }
.hu-stat-label { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.8rem; color: #6B8E23; min-width: 60px; letter-spacing: 0.05em; }
.hu-stat-value { font-family: 'Cormorant Garamond', serif; font-size: 1.05rem; font-weight: 600; color: #2E5A2E; }

/* ── 书签 ── */
.bookmark {
  position: absolute; top: 0; right: 56px;
  width: 28px; height: 96px; background: #B8902A;
  box-shadow: inset -2px 0 0 rgba(0,0,0,0.15);
  z-index: 6;
}
.bookmark::after { content: ""; position: absolute; bottom: 0; left: 0; right: 0; height: 16px; background: linear-gradient(135deg, transparent 50%, #B8902A 50%) 0 0/14px 16px no-repeat, linear-gradient(225deg, transparent 50%, #B8902A 50%) 14px 0/14px 16px no-repeat; }

/* ── 装饰: 麦穗 + 叶脉 + 光合色素 ── */
.wheat { position: absolute; top: 60px; left: 12px; width: 56px; height: 200px; opacity: 0.85; z-index: 3; }
.leaf-vein { position: absolute; bottom: 60px; left: 12px; width: 56px; height: 200px; opacity: 0.7; z-index: 3; }
.chloro-panel {
  position: absolute; right: 12px; top: 60px;
  width: 200px; padding: 14px 16px;
  background: rgba(245,249,236,0.85);
  border: 1px solid rgba(107,142,35,0.25);
  border-radius: 2px;
  font-family: 'Cormorant Garamond', 'Noto Serif SC', serif;
  z-index: 3;
}
.cp-title { font-family: 'Cormorant Garamond', serif; font-style: italic; font-weight: 600; font-size: 0.85rem; color: #2E5A2E; letter-spacing: 0.1em; text-transform: uppercase; border-bottom: 1px solid #B8CC98; padding-bottom: 6px; margin-bottom: 8px; }
.chloro-line { display: grid; grid-template-columns: 90px 1fr auto; gap: 8px; font-size: 0.78rem; padding: 3px 0; color: #2E5A2E; align-items: baseline; }
.chloro-line .num { font-style: italic; color: #B8902A; }
.chloro-line .ch { font-family: 'Noto Serif SC', serif; }
.chloro-line .note { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #6B8E23; font-size: 0.7rem; }

/* 招 #7 数字滚动/招 #4 巨型水印 */
section.tab h2 { color: #2E5A2E; font-size: clamp(1.375rem, 2.2vw, 1.625rem); font-weight: 600; }
section.tab h3 { color: #2E5A2E; font-family: 'Noto Serif SC', serif; }
section.tab p.lede { color: #4A5A3A; }
.watermark { font-family: 'Cormorant Garamond', serif; color: #B8CC98; }
footer { background: #F0F5E2; border-top: 1px solid #B8CC98; }
footer .label { color: #2E5A2E; font-family: 'Noto Serif SC', serif; }
footer .data-source { color: #6B8E23; }
.drop-cap::first-letter { font-family: 'Noto Serif SC', serif; color: #B8902A; }

/* ── Agri body section 框架 (仿 HUMANITIES 极简浅色 + 绿色主题) ── */
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.bento-item { padding: 28px 24px 24px; background: #FAFCF3; border: 1px solid #B8CC98; border-radius: 4px; position: relative; transition: border-color 250ms, transform 250ms; box-shadow: 0 1px 0 rgba(46, 90, 46, 0.04); }
.bento-item::before { content: "❀"; position: absolute; top: 20px; right: 20px; color: #6B8E23; font-size: 0.875rem; opacity: 0.4; }
.bento-item:nth-child(3)::before, .bento-item:nth-child(6)::before, .bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: #6B8E23; z-index: 1; pointer-events: none; }
.bento-item:hover { border-color: #6B8E23; transform: translateY(-2px); }
.bento-monogram { position: absolute; top: 20px; right: 50px; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #2E5A2E; color: #F0F5E2; font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 700; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #2E5A2E; border: 1px solid #2E5A2E; border-radius: 0; font-family: 'Noto Serif SC', serif; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; margin-bottom: 12px; }
.bento-name { font-family: 'Noto Serif SC', serif; font-size: 1.1875rem; font-weight: 700; margin-bottom: 4px; color: #2E5A2E; padding-right: 80px; text-wrap: balance; line-height: 1.3; }
.bento-tag { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.8125rem; color: #6B8E23; line-height: 1.5; }
.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 28px 24px 22px; background: #FAFCF3; border: 1px solid #B8CC98; border-radius: 4px; position: relative; transition: border-color 250ms, transform 250ms; }
.company:hover { border-color: #6B8E23; transform: translateY(-2px); }
.company-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.company-monogram { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #2E5A2E; color: #F0F5E2; font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 700; }
.company-tier { padding: 2px 8px; border: 1px solid #6B8E23; color: #6B8E23; font-family: 'Noto Serif SC', serif; font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.1em; }
.tier-S { background: #2E5A2E; color: #F0F5E2; border-color: #2E5A2E; }
.tier-A { background: transparent; }
.tier-B { background: transparent; color: #6B8E23; border-color: #B8CC98; }
.company-name { font-family: 'Noto Serif SC', serif; font-size: 1.1875rem; font-weight: 700; margin-bottom: 8px; color: #2E5A2E; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 10px; border-top: 1px solid #DCE8C5; }
.sparkline-bar { flex: 1; background: #B8CC98; min-height: 2px; transition: background 250ms; }
.company:hover .sparkline-bar { background: #6B8E23; opacity: 0.7; }
.sparkline-label { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.6875rem; color: #6B8E23; letter-spacing: 0.05em; margin-top: 6px; }
.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: #FAFCF3; border: 1px solid #B8CC98; border-radius: 4px; overflow: hidden; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 20px 24px; text-align: left; border-bottom: 1px solid #DCE8C5; font-size: 0.9375rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: #F0F5E2; font-family: 'Noto Serif SC', serif; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.12em; color: #6B8E23; }
.direction-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 200px 1fr 70px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #DCE8C5; }
.direction:last-child { border-bottom: none; }
.direction-name { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 600; color: #2E5A2E; }
.direction-bar { height: 8px; background: rgba(107, 142, 35, 0.12); overflow: hidden; border-radius: 2px; }
.direction-bar-fill { height: 100%; background: #6B8E23; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); border-radius: 2px; }
.direction-pct { font-family: 'Cormorant Garamond', serif; font-weight: 700; text-align: right; font-size: 1.0625rem; color: #6B8E23; }
.path-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: #FAFCF3; border: 1px solid #B8CC98; border-radius: 4px; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #6B8E23; transform: translateY(-2px); }
.path-pct { font-family: 'Noto Serif SC', serif; font-size: 2.5rem; font-weight: 700; color: #2E5A2E; margin-bottom: 4px; line-height: 1; }
.path-name { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #6B8E23; font-size: 0.875rem; margin-top: 8px; }
.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 28px 32px 24px; background: #FAFCF3; border: 1px solid #B8CC98; border-left: 4px solid #B8902A; border-radius: 0 4px 4px 0; margin-bottom: 16px; transition: border-left-width 250ms, transform 250ms; }
.quote:hover { border-left-width: 12px; transform: translateX(4px); }
.quote-head { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.quote-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #2E5A2E; color: #F0F5E2; font-family: 'Noto Serif SC', serif; font-size: 1rem; font-weight: 700; }
.quote-byline strong { display: block; font-family: 'Noto Serif SC', serif; font-weight: 700; color: #2E5A2E; font-size: 0.9375rem; }
.quote-byline .quote-source { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #6B8E23; font-size: 0.75rem; }
.quote-text { font-family: 'Noto Serif SC', serif; font-style: italic; font-size: 1.1875rem; line-height: 1.65; color: #2E5A2E; }
.quote-text::before { content: "「"; color: #B8902A; }
.quote-text::after { content: "」"; color: #B8902A; }
.xuanke-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 200px 1fr 80px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #DCE8C5; }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; color: #2E5A2E; }
.xuanke-bar { height: 6px; background: #DCE8C5; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #6B8E23; }
.xuanke-pct { font-family: 'Noto Serif SC', serif; font-weight: 700; text-align: right; font-size: 1.0625rem; color: #6B8E23; }
.curriculum-lede { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #6B8E23; font-size: 1.0625rem; margin: 0 0 32px; max-width: 720px; }
.cta-block { margin-top: 32px; padding: 64px 48px; background: #FAFCF3; border: 1px solid #2E5A2E; text-align: center; position: relative; }
.cta-block::before { content: "❀  ❀  ❀"; position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: #F0F5E2; padding: 0 16px; color: #2E5A2E; font-size: 0.875rem; letter-spacing: 0.5em; }
.cta-block h3 { font-family: 'Noto Serif SC', serif; font-size: 1.75rem; margin-bottom: 12px; color: #2E5A2E; position: relative; z-index: 1; font-weight: 700; }
.cta-block p { color: #4A5A3A; margin: 0 auto 28px; max-width: 560px; position: relative; z-index: 1; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; position: relative; z-index: 1; }
.cta-input { padding: 14px 18px; background: #F0F5E2; border: 1px solid #B8CC98; color: #2E5A2E; font-family: 'Noto Serif SC', serif; font-size: 1rem; width: 180px; outline: none; }
.cta-input:focus { border-color: #6B8E23; }
.cta-button { padding: 14px 36px; background: #2E5A2E; color: #F0F5E2; font-family: 'Noto Serif SC', serif; font-size: 1rem; font-weight: 700; letter-spacing: 0.05em; }
.cta-note { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.75rem; color: #6B8E23; margin-top: 16px; position: relative; z-index: 1; }
.tag { display: inline-block; padding: 4px 12px; border: 1px solid #2E5A2E; color: #2E5A2E; font-family: 'Noto Serif SC', serif; font-size: 0.75rem; letter-spacing: 0.05em; }
.tag.primary { background: #2E5A2E; color: #F0F5E2; }

/* ── Agri body section 配色 (浅绿底, 保持与 BASE_CSS 默认对比) ── */
section.tab { border-top: 1px solid #C5D9A8; }
.section-num { color: #6B8E23; }
.watermark { color: #6B8E23; opacity: 0.04; }
.salary-stage { color: #2E5A2E; }
.salary-bar { display: inline-block; width: 80px; height: 4px; background: rgba(107, 142, 35, 0.15); margin-left: 12px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #6B8E23; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); }
.salary-bar { background: rgba(107, 142, 35, 0.15); }
.salary-bar-fill { background: #6B8E23; }
.yoy { display: inline-block; font-family: 'Noto Serif SC', serif; font-size: 0.8125rem; font-weight: 600; margin-left: 12px; padding: 2px 8px; }
.yoy.up { color: #2E5A2E; background: rgba(46, 90, 46, 0.08); }
.yoy.down { color: #DC2626; background: rgba(220, 38, 38, 0.08); }
.yoy.flat { color: #999; }
.direction-bar { background: rgba(107, 142, 35, 0.12); }
.direction-bar-fill { background: #6B8E23; }
.direction-name { color: #2E5A2E; }
.curriculum-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.direction-pct { color: #2E5A2E; }
.path-name { color: #2E5A2E; }
.quote-byline strong { color: #2E5A2E; }
.quote-source { color: #A0824D; }
.quote-text { color: #2E5A2E; }
.quote-text::before, .quote-text::after { color: #6B8E23; }
.xuanke-bar { background: rgba(107, 142, 35, 0.12); }
.xuanke-bar-fill { background: #6B8E23; }
.xuanke-name { color: #2E5A2E; }
.xuanke-pct { color: #2E5A2E; }
.course { color: #2E5A2E; border-bottom: 1px dashed rgba(107, 142, 35, 0.2); padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; gap: 12px; font-size: 0.9375rem; transition: background 200ms, padding-left 200ms; }
.course:hover { background: rgba(107, 142, 35, 0.04); padding-left: 8px; }
.course-name { color: #2E5A2E; }
.course-credit { color: #6B8E23; font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.8125rem; flex-shrink: 0; font-weight: 600; }
.curriculum-block { padding: 22px 26px; background: rgba(245, 249, 236, 0.55); border: 1px solid #B8CC98; border-radius: 3px; margin-bottom: 18px; transition: border-color 250ms; }
.curriculum-block:last-child { margin-bottom: 0; }
.curriculum-block:hover { border-color: #6B8E23; }
.curriculum-title { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; color: #2E5A2E; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid rgba(107,142,35,0.3); font-weight: 700; }
.bento-tag { color: #6B8E23; }
.bento-rank { color: #6B8E23; border: 1px solid #6B8E23; }
.bento-name { color: #2E5A2E; }
.company-meta { color: #A0824D; }
.cta-block p { color: #4A5A3A; }
.cta-input { background: #FAFAFA; border: 1px solid #C5D9A8; color: #2E5A2E; }
.cta-button:hover { background: #FAFAFA; color: #6B8E23; }
.cta-note { color: #A0824D; }

/* ── Hero 主内容区 (agri 居中布局, 装饰作 frame) ── */
.hero-content { max-width: 880px; margin: 0 auto; padding: 60px 0 40px; position: relative; z-index: 5; text-align: center; }
.hero-chapter { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 0.85rem; letter-spacing: 0.3em; color: #6B8E23; margin-bottom: 14px; text-transform: uppercase; }
.hero-title { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: clamp(3rem, 7vw, 5rem); line-height: 1; letter-spacing: -0.01em; color: #2E5A2E; margin: 0 0 10px; }
.title-cn { display: block; }
.title-en { display: block; font-family: 'Cormorant Garamond', serif; font-style: italic; font-weight: 500; font-size: 1.5rem; color: #6B8E23; margin-top: 12px; letter-spacing: 0.04em; }
.ampersand { color: #E6B422; font-style: italic; }
.hero-tagline { font-family: 'Noto Serif SC', serif; font-size: 1rem; line-height: 1.7; color: #4A5A3A; max-width: 720px; margin: 18px auto 0; }
.hu-stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin: 28px auto 0; max-width: 880px; padding: 20px 0; border-top: 1px solid rgba(107,142,35,0.4); border-bottom: 1px solid rgba(107,142,35,0.4); }
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 22px; }
.hu-tag { font-family: 'Noto Serif SC', serif; font-size: 0.8rem; padding: 4px 12px; border: 1px solid #6B8E23; color: #2E5A2E; border-radius: 2px; background: rgba(245,249,236,0.6); }
"""

# ──────────────────────────────────────────────────────────
# ARTS (美术) — 美术馆白盒 + 画框 + 展签 + 朱砂印章 + 金属铭牌
# 配色: 珍珠白 #F8F6F2 底, 朱砂红 #B83A2A 印章, 暖金 #B8902A 铭牌
# 字体: Noto Serif SC (中文) + EB Garamond (英文展签/拉丁) + Cormorant (衬线小字)
# ──────────────────────────────────────────────────────────
ARTS_CSS = """
/* === 美术馆白盒 (白墙 + 灯光锥 + 大理石地面) === */
.museum-wall { position: absolute; inset: 0; z-index: 1;
  background: radial-gradient(ellipse 80% 50% at 50% 0%, rgba(255, 248, 220, 0.30) 0%, transparent 60%),
              radial-gradient(ellipse 60% 40% at 50% 100%, rgba(184, 144, 42, 0.08) 0%, transparent 60%),
              linear-gradient(180deg, #F8F6F2 0%, #FBF9F4 50%, #F2EFE8 100%);
}
.museum-wall::before { content: ""; position: absolute; inset: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='280' height='280'><filter id='p'><feTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.55 0 0 0 0 0.45 0 0 0 0 0.32 0 0 0 0.04 0'/></filter><rect width='100%25' height='100%25' filter='url(%23p)'/></svg>");
  opacity: 0.6; mix-blend-mode: multiply; pointer-events: none;
}
.museum-floor { position: absolute; left: 0; right: 0; bottom: 0; height: 80px; z-index: 1;
  background: linear-gradient(180deg, transparent 0%, rgba(184, 144, 42, 0.05) 50%, rgba(184, 144, 42, 0.12) 100%),
              repeating-linear-gradient(90deg, #F0EDE5 0px, #EBE7DE 30px, #F0EDE5 60px, #EDE8DF 90px);
}
.museum-floor::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(184, 144, 42, 0.4) 20%, rgba(184, 144, 42, 0.4) 80%, transparent);
}
.museum-light { position: absolute; top: -40px; left: 50%; transform: translateX(-50%); width: 600px; height: 200px; z-index: 2; pointer-events: none;
  background: radial-gradient(ellipse 50% 100% at 50% 0%, rgba(255, 248, 220, 0.5) 0%, transparent 70%);
}

/* === 美术馆 logo === */
.museum-logo { position: absolute; top: 28px; left: 50%; transform: translateX(-50%); z-index: 5; text-align: center; pointer-events: none; }
.museum-logo-text { font-family: 'EB Garamond', serif; font-weight: 700; font-size: 0.95rem; letter-spacing: 0.4em; color: #1A1A1A; text-transform: uppercase; border-bottom: 1px solid #1A1A1A; padding-bottom: 4px; }
.museum-logo-sub { font-family: 'EB Garamond', serif; font-style: italic; font-size: 0.7rem; color: #6B5D43; letter-spacing: 0.1em; margin-top: 4px; }

/* === 朱砂印章 === */
.cinnabar-seal { position: absolute; top: 90px; right: 80px; z-index: 6; width: 70px; height: 70px; background: #B83A2A;
  display: flex; align-items: center; justify-content: center; font-family: 'Noto Serif SC', serif; font-weight: 900; color: #FFE8B0; font-size: 0.78rem; line-height: 1.1; text-align: center;
  box-shadow: 0 2px 8px rgba(184, 58, 42, 0.3), inset 0 0 0 2px #FFE8B0, inset 0 0 0 3px #B83A2A; transform: rotate(-6deg); }
.cinnabar-seal::before { content: ""; position: absolute; inset: 4px; border: 1px solid #FFE8B0; opacity: 0.5; }

/* === 金属铭牌 === */
.brass-plate { position: absolute; top: 88px; left: 80px; z-index: 6; padding: 8px 18px;
  background: linear-gradient(135deg, #C8A26E 0%, #B8902A 50%, #8B6914 100%); border: 1px solid #6B5D43;
  font-family: 'EB Garamond', serif; font-weight: 700; font-size: 0.7rem; letter-spacing: 0.3em; text-transform: uppercase; color: #2A1A0A;
  box-shadow: 0 2px 6px rgba(107, 93, 67, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2); }

/* === 装饰色卡 === */
.color-swatches { position: absolute; left: 36px; top: 220px; z-index: 5; width: 96px; height: 168px; padding: 12px 8px; background: linear-gradient(180deg, #FFFFFF 0%, #F5F0E5 100%); border: 1.5px solid #B8902A; border-radius: 2px; box-shadow: 0 6px 16px rgba(0,0,0,0.12), inset 0 0 0 1px #FFFFFF; z-index: 5; }
.color-swatches::before { content: "PALETTE"; position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: #B8902A; color: #FFFFFF; font-family: 'EB Garamond', serif; font-size: 0.5rem; letter-spacing: 0.3em; padding: 2px 8px; font-weight: 700; }
.color-swatch { position: absolute; left: 50%; display: block; height: 12px; border-radius: 2px 8px 2px 2px; box-shadow: 0 2px 4px rgba(0,0,0,0.2), inset 0 -1px 0 rgba(0,0,0,0.15); }
.swatch-1 { top: 28px; width: 78px; transform: translateX(-50%) rotate(-4deg); background: linear-gradient(90deg, #C8A26E 0%, #B8902A 50%, #8B6914 100%); }
.swatch-2 { top: 48px; width: 64px; transform: translateX(-50%) rotate(7deg); background: linear-gradient(90deg, #DC2626 0%, #991B1B 100%); }
.swatch-3 { top: 68px; width: 82px; transform: translateX(-50%) rotate(-2deg); background: linear-gradient(90deg, #1E40AF 0%, #1E3A8A 100%); }
.swatch-4 { top: 88px; width: 70px; transform: translateX(-50%) rotate(5deg); background: linear-gradient(90deg, #4A5D3A 0%, #2A3A1A 100%); }
.swatch-5 { top: 108px; width: 60px; transform: translateX(-50%) rotate(-3deg); background: linear-gradient(90deg, #6B3410 0%, #4A2A0A 100%); }
.color-swatch-label { display: none; }

/* === 画框 (双线 + 暖金内沿) === */
.gallery-frame-wrap { position: relative; margin: 60px 24px 0; z-index: 4; padding: 18px; background: #F8F6F2;
  box-shadow: 0 0 0 1px #1A1A1A, 0 0 0 5px #F8F6F2, 0 0 0 6px #1A1A1A, 0 24px 48px rgba(0, 0, 0, 0.10), inset 0 0 0 1px #B8902A; }
.gallery-frame-wrap::before, .gallery-frame-wrap::after { content: ""; position: absolute; width: 24px; height: 24px; border: 1.5px solid #B8902A; pointer-events: none; }
.gallery-frame-wrap::before { top: -2px; left: -2px; border-right: none; border-bottom: none; }
.gallery-frame-wrap::after { top: -2px; right: -2px; border-left: none; border-bottom: none; }
.frame-corner-bl, .frame-corner-br { position: absolute; width: 24px; height: 24px; border: 1.5px solid #B8902A; pointer-events: none; }
.frame-corner-bl { bottom: -2px; left: -2px; border-right: none; border-top: none; }
.frame-corner-br { bottom: -2px; right: -2px; border-left: none; border-top: none; }
.gallery-frame-inner { background: #FFFFFF; padding: 40px 36px 28px; position: relative; }

/* === 展签 (bottom gallery label) === */
.gallery-label { position: relative; margin: 32px auto 0; z-index: 6; padding: 12px 28px; background: #FFFFFF; border: 1px solid #1A1A1A; box-shadow: 0 4px 12px rgba(0,0,0,0.12); text-align: center; max-width: 720px; }
.gallery-label::before { content: ""; position: absolute; top: -1px; left: 16px; right: 16px; height: 1px; background: linear-gradient(90deg, transparent, #B8902A 20%, #B8902A 80%, transparent); }
.label-eyebrow { font-family: 'EB Garamond', serif; font-weight: 600; font-size: 0.65rem; letter-spacing: 0.3em; text-transform: uppercase; color: #B8902A; }
.label-title { font-family: 'Noto Serif SC', serif; font-size: 0.95rem; font-weight: 700; color: #1A1A1A; margin-top: 4px; }
.label-meta { font-family: 'EB Garamond', serif; font-style: italic; font-size: 0.7rem; color: #6B5D43; margin-top: 4px; letter-spacing: 0.05em; }

/* === Hero 白盒主内容 === */
.hero { padding: 0; background: transparent; border-bottom: 1px solid #B8902A; position: relative; z-index: 2; overflow: hidden; min-height: 720px; color: #1A1A1A; }
.hero, .hero * { --font-heading: 'Noto Serif SC', 'EB Garamond', serif; --font-num: 'EB Garamond', serif; }
.hero .container { position: relative; z-index: 3; }
section.tab h1, section.tab h2, section.tab h3, section.tab h4 { font-family: var(--font-heading); }
section.tab p, section.tab li { font-family: 'Noto Serif SC', 'Source Han Serif SC', serif; }
.num, .num * { font-family: 'EB Garamond', serif; font-variant-numeric: lining-nums; }

.hero-content { max-width: 880px; margin: 0 auto; padding: 60px 0 40px; position: relative; z-index: 5; text-align: center; }
.hero-chapter { font-family: 'EB Garamond', serif; font-style: italic; font-size: 0.85rem; letter-spacing: 0.4em; color: #B8902A; margin-bottom: 14px; text-transform: uppercase; display: inline-block; padding-bottom: 4px; border-bottom: 1px solid #B8902A; }
.hero-title { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: clamp(2.5rem, 6vw, 4.5rem); line-height: 1.05; letter-spacing: -0.02em; color: #1A1A1A; margin: 0 0 6px; }
.title-cn { display: block; }
.title-en-small { display: block; font-family: 'EB Garamond', serif; font-style: italic; font-weight: 400; font-size: 0.45em; color: #6B5D43; letter-spacing: 0.25em; margin-bottom: 8px; text-transform: uppercase; }
.title-en { display: block; font-family: 'EB Garamond', serif; font-style: italic; font-size: 0.75rem; color: #6B5D43; letter-spacing: 0.3em; margin-top: 14px; text-transform: uppercase; }
.hero-tagline { font-family: 'Noto Serif SC', serif; font-size: 1rem; line-height: 1.7; color: #4A5A3A; max-width: 720px; margin: 20px auto 0; }
.hu-stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 24px auto 0; max-width: 100%; padding: 16px 0; border-top: 1px solid rgba(184, 144, 42, 0.3); border-bottom: 1px solid rgba(184, 144, 42, 0.3); }
.hu-stat { text-align: center; padding: 6px 4px; position: relative; }
.hu-stat:not(:last-child)::after { content: ""; position: absolute; right: -6px; top: 22%; bottom: 22%; width: 1px; background: rgba(184, 144, 42, 0.2); }
.hu-stat-label { font-family: 'Noto Serif SC', serif; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.25em; color: #B8902A; margin-bottom: 6px; }
.hu-stat-value { font-family: 'Noto Serif SC', serif; font-size: 1rem; font-weight: 700; color: #1A1A1A; line-height: 1.3; }
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 24px; }
.hu-tag { font-family: 'EB Garamond', serif; font-style: italic; font-size: 0.78rem; letter-spacing: 0.05em; padding: 4px 14px; border: 1px solid #1A1A1A; color: #1A1A1A; background: rgba(248, 246, 242, 0.6); }

/* === Body section 配色 (白盒浅色) === */
section.tab { border-top: 1px solid #D6D2C5; }
section.tab h2 { color: #1A1A1A; font-family: 'Noto Serif SC', serif; font-weight: 700; font-size: clamp(1.375rem, 2.2vw, 1.625rem); }
section.tab h3 { color: #1A1A1A; font-family: 'Noto Serif SC', serif; }
section.tab p { color: #2A2520; }
section.tab p.lede { color: #4A5A3A; }
.watermark { font-family: 'EB Garamond', serif; color: #D6D2C5; }
footer { background: #2A2520; color: #FAFAF6; border-top: 1px solid #B8902A; }
footer .label { color: #FAFAF6; font-family: 'EB Garamond', serif; }
footer .data-source { color: #999; }
.drop-cap::first-letter { font-family: 'Noto Serif SC', serif; color: #B83A2A; font-weight: 900; }

/* === 速览 v2 (白盒 default) === */
.ovv-card { background: #FFFFFF; border: 1px solid #E5E5E0; }
.ovv-card-title { color: #1A1A1A; }
.ovv-card-tag { color: #6B5D43; }
.ovv-foundations-label, .ovv-dir-name, .ovv-skill { color: #1A1A1A; }
.ovv-dir { background: #FBF9F4; border-color: #D6D2C5; }
.ovv-dir:hover { border-color: #B83A2A; background: #FAFAF6; }
.ovv-dir-desc { color: #4A5A3A; }
.ovv-skill { background: #FBF9F4; color: #1A1A1A; border-color: #1A1A1A; }
.ovv-bonus { color: #2A2520; background: rgba(184, 144, 42, 0.06); border-left: 3px solid #B8902A; }
.ovv-pit { background: #FBF9F4; border-color: #D6D2C5; border-left: 3px solid #B83A2A; }
.ovv-pit-reality { color: #2A2520; }
.ovv-fit-col { background: #FBF9F4; border-color: #D6D2C5; }
.ovv-fit-col.is-yes { background: rgba(46, 125, 50, 0.05); border-color: #2E7D32; }
.ovv-fit-col.is-no { background: rgba(185, 28, 28, 0.05); border-color: #B83A2A; }
.ovv-fit-list li { color: #1A1A1A; border-color: #D6D2C5; }
.ovv-card-head { border-color: #D6D2C5; }
.ovv-pits .ovv-pit:last-child:nth-child(odd) { grid-column: 1 / -1; max-width: 50%; margin: 0 auto; }

/* === 院校 === */
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.bento-item { padding: 28px 24px 24px; background: #FFFFFF; border: 1px solid #D6D2C5; border-radius: 3px; position: relative; transition: border-color 250ms, transform 250ms, box-shadow 250ms; }
.bento-item::before { content: "✦"; position: absolute; top: 20px; right: 20px; color: #B8902A; font-size: 0.875rem; opacity: 0.5; }
.bento-item:nth-child(3)::before, .bento-item:nth-child(6)::before, .bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: #B83A2A; }
.bento-item:hover { border-color: #B83A2A; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(184, 58, 42, 0.08); }
.bento-monogram { position: absolute; top: 20px; right: 50px; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #1A1A1A; color: #FAFAF6; font-family: 'EB Garamond', serif; font-size: 1.0625rem; font-weight: 700; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #B83A2A; border: 1px solid #B83A2A; border-radius: 0; font-family: 'EB Garamond', serif; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; margin-bottom: 12px; }
.bento-name { font-family: 'Noto Serif SC', serif; font-size: 1.1875rem; font-weight: 700; margin-bottom: 4px; padding-right: 80px; text-wrap: balance; line-height: 1.3; }
.bento-tag { font-family: 'EB Garamond', serif; font-style: italic; font-size: 0.8125rem; color: #6B5D43; line-height: 1.5; }

/* === 公司 === */
.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 28px 24px 22px; background: #FFFFFF; border: 1px solid #D6D2C5; border-radius: 3px; transition: border-color 250ms, transform 250ms, box-shadow 250ms; }
.company:hover { border-color: #B83A2A; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(184, 58, 42, 0.08); }
.company-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.company-monogram { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #1A1A1A; color: #FAFAF6; font-family: 'EB Garamond', serif; font-size: 1.0625rem; font-weight: 700; }
.company-tier { padding: 2px 8px; border: 1px solid #B8902A; color: #B8902A; font-family: 'EB Garamond', serif; font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.1em; }
.tier-S { background: #B8902A; color: #FFFFFF; border-color: #B8902A; }
.tier-A { background: transparent; }
.tier-B { background: transparent; color: #6B5D43; border-color: #D6D2C5; }
.company-name { font-family: 'Noto Serif SC', serif; font-size: 1.1875rem; font-weight: 700; margin-bottom: 8px; color: #1A1A1A; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 10px; border-top: 1px solid #D6D2C5; }
.sparkline-bar { flex: 1; background: #D6D2C5; min-height: 2px; transition: background 250ms; }
.company:hover .sparkline-bar { background: #B8902A; }
.sparkline-label { font-family: 'EB Garamond', serif; font-style: italic; font-size: 0.6875rem; color: #6B5D43; letter-spacing: 0.05em; margin-top: 6px; }

/* === 薪资表 === */
.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: #FFFFFF; border: 1px solid #D6D2C5; border-radius: 3px; overflow: hidden; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 20px 24px; text-align: left; border-bottom: 1px solid #D6D2C5; font-size: 0.9375rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: #F8F6F2; font-family: 'EB Garamond', serif; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.12em; color: #B8902A; }
.salary-stage { font-family: 'Noto Serif SC', serif; font-weight: 700; color: #1A1A1A; font-size: 1.0625rem; }
.salary-bar { display: inline-block; width: 80px; height: 4px; background: rgba(184, 144, 42, 0.12); margin-left: 12px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #B8902A; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); }
.yoy { display: inline-block; font-family: 'EB Garamond', serif; font-size: 0.8125rem; font-weight: 600; margin-left: 12px; padding: 2px 8px; }
.yoy.up { color: #2E7D32; background: rgba(46, 125, 50, 0.08); }
.yoy.down { color: #B83A2A; background: rgba(184, 58, 42, 0.08); }
.yoy.flat { color: #6B5D43; background: rgba(107, 93, 67, 0.06); }

/* === 就业方向 === */
.direction-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 200px 1fr 70px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #D6D2C5; }
.direction:last-child { border-bottom: none; }
.direction-name { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; font-weight: 600; color: #1A1A1A; }
.direction-bar { height: 8px; background: rgba(184, 144, 42, 0.12); overflow: hidden; border-radius: 2px; }
.direction-bar-fill { height: 100%; background: #B8902A; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); border-radius: 2px; }
.direction-pct { font-family: 'EB Garamond', serif; font-weight: 700; text-align: right; font-size: 1.0625rem; color: #B8902A; }

/* === 深造路径 === */
.path-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: #FFFFFF; border: 1px solid #D6D2C5; border-radius: 3px; text-align: center; transition: border-color 250ms, transform 250ms, box-shadow 250ms; }
.path-card:hover { border-color: #B83A2A; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(184, 58, 42, 0.08); }
.path-pct { font-family: 'EB Garamond', serif; font-size: 2.5rem; font-weight: 700; color: #1A1A1A; margin-bottom: 4px; line-height: 1; }
.path-name { font-family: 'EB Garamond', serif; font-style: italic; font-size: 0.875rem; color: #6B5D43; margin-top: 8px; }

/* === 学长学姐说 === */
.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 28px 32px 24px; background: #FFFFFF; border: 1px solid #D6D2C5; border-left: 4px solid #B83A2A; border-radius: 0 3px 3px 0; margin-bottom: 16px; transition: border-left-width 250ms, transform 250ms; }
.quote:hover { border-left-width: 12px; transform: translateX(4px); }
.quote-head { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.quote-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #1A1A1A; color: #FAFAF6; font-family: 'EB Garamond', serif; font-size: 1rem; font-weight: 700; }
.quote-byline strong { display: block; font-family: 'Noto Serif SC', serif; font-weight: 700; color: #1A1A1A; font-size: 0.9375rem; }
.quote-byline .quote-source { font-family: 'EB Garamond', serif; font-style: italic; font-size: 0.75rem; color: #6B5D43; }
.quote-text { font-family: 'Noto Serif SC', serif; font-style: italic; font-size: 1.1875rem; line-height: 1.65; color: #1A1A1A; }
.quote-text::before { content: "「"; color: #B83A2A; }
.quote-text::after { content: "」"; color: #B83A2A; }

/* === 选科 === */
.xuanke-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 200px 1fr 80px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #D6D2C5; }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-family: 'Noto Serif SC', serif; font-size: 1.0625rem; color: #1A1A1A; }
.xuanke-bar { height: 6px; background: #D6D2C5; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #B8902A; }
.xuanke-pct { font-family: 'EB Garamond', serif; font-weight: 700; text-align: right; font-size: 1.0625rem; color: #B8902A; }

/* === 课程 === */
.curriculum-lede { font-family: 'EB Garamond', serif; font-style: italic; color: #4A5A3A; font-size: 1.0625rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.curriculum-block { padding: 32px 28px; background: #FFFFFF; border: 1px solid #D6D2C5; border-radius: 3px; transition: border-color 250ms, transform 250ms, box-shadow 250ms; }
.curriculum-block:hover { border-color: #B83A2A; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(184, 58, 42, 0.08); }
.curriculum-title { font-family: 'Noto Serif SC', serif; font-size: 1.1875rem; color: #1A1A1A; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid #D6D2C5; font-weight: 700; }
.course { color: #1A1A1A; border-bottom: 1px dashed #D6D2C5; padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; gap: 12px; font-size: 0.9375rem; transition: background 200ms, padding-left 200ms; }
.course:hover { background: rgba(184, 144, 42, 0.05); padding-left: 8px; }
.course-name { color: #1A1A1A; }
.course-credit { color: #B8902A; font-family: 'EB Garamond', serif; font-style: italic; font-size: 0.8125rem; flex-shrink: 0; font-weight: 600; }

/* === CTA === */
.cta-block { margin-top: 32px; padding: 64px 48px; background: #FFFFFF; border: 1px solid #1A1A1A; text-align: center; position: relative; }
.cta-block::before { content: "MAJOR · MUSEUM · 2026"; position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: #F8F6F2; padding: 0 16px; color: #B8902A; font-family: 'EB Garamond', serif; font-size: 0.7rem; letter-spacing: 0.5em; }
.cta-block h3 { font-family: 'Noto Serif SC', serif; font-size: 1.75rem; margin-bottom: 12px; color: #1A1A1A; position: relative; z-index: 1; font-weight: 700; }
.cta-block p { color: #4A5A3A; margin: 0 auto 28px; max-width: 560px; position: relative; z-index: 1; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; position: relative; z-index: 1; }
.cta-input { padding: 14px 18px; background: #F8F6F2; border: 1px solid #D6D2C5; color: #1A1A1A; font-family: 'Noto Serif SC', serif; font-size: 1rem; width: 180px; outline: none; }
.cta-input:focus { border-color: #B83A2A; }
.cta-button { padding: 14px 36px; background: #1A1A1A; color: #FAFAF6; font-family: 'Noto Serif SC', serif; font-size: 1rem; font-weight: 700; letter-spacing: 0.05em; }
.cta-button:hover { background: #B83A2A; }
.cta-note { font-family: 'EB Garamond', serif; font-style: italic; font-size: 0.75rem; color: #6B5D43; margin-top: 16px; position: relative; z-index: 1; }
.tag { display: inline-block; padding: 4px 12px; border: 1px solid #1A1A1A; color: #1A1A1A; font-family: 'EB Garamond', serif; font-size: 0.75rem; letter-spacing: 0.05em; }
.tag.primary { background: #1A1A1A; color: #FAFAF6; }

/* === 响应式 === */
@media (max-width: 1023px) {
  .gallery-frame-wrap { max-width: 92%; margin: 60px auto 0; }
  .gallery-frame-inner { padding: 40px 32px 32px; }
  .cinnabar-seal { right: 40px; top: 70px; width: 56px; height: 56px; font-size: 0.65rem; }
  .brass-plate { left: 40px; top: 68px; padding: 6px 14px; font-size: 0.6rem; }
  .color-swatches { left: 16px; bottom: 16px; }
  .gallery-label { bottom: 8px; min-width: 260px; padding: 8px 18px; }
  .museum-logo-text { font-size: 0.8rem; }
  .museum-logo-sub { font-size: 0.6rem; }
}
@media (max-width: 767px) {
  .gallery-frame-wrap { padding: 12px; }
  .gallery-frame-inner { padding: 30px 20px 24px; }
  .cinnabar-seal, .brass-plate { display: none; }
  .color-swatches { display: none; }
  .gallery-label { position: static; transform: none; margin: 24px auto 0; max-width: 90%; }
  .museum-logo { top: 16px; }
  .museum-logo-text { font-size: 0.7rem; letter-spacing: 0.25em; }
  .museum-logo-sub { font-size: 0.55rem; }
"""


# ──────────────────────────────────────────────────────────
# GONGAN_CSS · 公安学类 (国际司法范式: 盾+十字剑+橄榄枝, 警蓝+国徽金+朱红)
# ──────────────────────────────────────────────────────────
GONGAN_CSS = """
:root {
  /* 主题色 */
  --gg-red: #B91C1C;        --gg-red-dk: #7F1D1D;    --gg-red-soft: #DC2626;
  --gg-blue: #1E3A5F;       --gg-blue-dk: #0F1F33;   --gg-blue-2: #2A4A75;
  --gg-gold: #D4AF37;       --gg-gold-dk: #B8902A;   --gg-gold-soft: #E5C158;
  --gg-silver: #94A3B8;     --gg-silver-soft: #CBD5E1;
  --gg-paper: #FAFAF6;      --gg-ink: #1A0A0A;
  --gg-glow: rgba(212, 175, 55, 0.35);
  /* 字体 (修复 v4_styles 未注入 base CSS 的问题) */
  --font-heading: "Cinzel", "Noto Serif SC", serif;
  --font-body:    "Noto Serif SC", "Inter", "PingFang SC", "Songti SC", serif;
  --font-cn:      "Noto Serif SC", "Songti SC", "PingFang SC", serif;
  --font-num:     "Oswald", "JetBrains Mono", monospace;
}
@import url('https://fonts.loli.net/css2?family=Cinzel:wght@500;600;700;800&family=Cormorant+Unicase:wght@500;600;700&family=Noto+Serif+SC:wght@300;400;500;600;700;900&family=Oswald:wght@500;600;700&family=Inter:wght@300;400;500;600;700&family=Long+Cang&display=swap');
/* ── Hero 主体 ── */
.gg-hero { position: relative; width: 100%; min-height: 720px; padding: 96px 0 110px; overflow: hidden; z-index: 2; isolation: isolate;
  background: radial-gradient(ellipse 30% 35% at 50% 22%, rgba(212,175,55,0.18) 0%, transparent 60%),
              radial-gradient(ellipse 30% 50% at 88% 70%, rgba(148,163,184,0.12) 0%, transparent 60%),
              linear-gradient(155deg, #0F1F33 0%, #1E3A5F 35%, #3A1424 70%, #0F1F33 100%);
  border-bottom: 1px solid #1F1408; color: var(--gg-paper);
  font-family: var(--font-body); }
.gg-bg-noise { position: absolute; inset: 0; opacity: 0.5; mix-blend-mode: overlay; pointer-events: none; z-index: 1;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.83 0 0 0 0 0.69 0 0 0 0 0.22 0 0 0 0.06 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>"); }
.gg-gold-band { position: absolute; top: 0; left: 0; right: 0; height: 56px; z-index: 4; pointer-events: none;
  background: linear-gradient(180deg, #D4AF37 0%, #B8902A 50%, #8B6F1F 100%);
  clip-path: polygon(0 0, 100% 0, 100% 70%, 96% 78%, 100% 88%, 100% 100%, 0 100%, 0 88%, 4% 78%, 0 70%);
  box-shadow: 0 4px 16px rgba(0,0,0,0.5); }
/* ── 主徽 (盾+十字剑+橄榄枝) ── */
.gg-main-emblem { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 320px; height: 320px; z-index: 2; opacity: 0.18; pointer-events: none; filter: drop-shadow(0 0 60px var(--gg-glow)); animation: ggGlow 6s ease-in-out infinite; }
.gg-main-emblem svg { width: 100%; height: 100%; }
@keyframes ggGlow { 0%,100% { opacity: 0.18; } 50% { opacity: 0.28; } }
/* ── 6 大专业 hu-tag (顶部装饰) ── */
.gg-hu-tags { position: relative; z-index: 10; display: flex; gap: 6px; justify-content: center; flex-wrap: wrap; max-width: 1100px; margin: 0 auto 32px; padding: 0 24px; }
.gg-hu-tag { padding: 7px 16px 7px 14px; background: rgba(15,31,51,0.78); border: 1px solid var(--gg-gold);
  font-family: var(--font-body); font-size: 12px; font-weight: 600; color: var(--gg-gold-soft);
  letter-spacing: 0.12em; clip-path: polygon(0 0, 100% 0, calc(100% - 8px) 100%, 0 100%); }
.gg-hu-tag::before { content: "▪"; color: var(--gg-red-soft); margin-right: 6px; font-size: 10px; }
/* ── 标题区 ── */
.gg-title-zone { position: relative; z-index: 10; text-align: center; max-width: 1100px; margin: 0 auto 36px; padding: 0 24px; }
.gg-discipline { font-family: var(--font-heading); font-size: 11px; font-weight: 600; letter-spacing: 0.55em; color: var(--gg-gold); margin-bottom: 12px; text-transform: uppercase; }
.gg-hero-title { font-family: var(--font-body); font-weight: 900; font-size: clamp(2.5rem, 5.5vw, 4.25rem); line-height: 1; color: var(--gg-paper); letter-spacing: 0.08em;
  text-shadow: 0 0 30px rgba(212,175,55,0.4), 0 4px 14px rgba(0,0,0,0.7); margin: 0 0 8px; }
.gg-hero-title .accent { color: var(--gg-gold); }
.gg-title-en { font-family: var(--font-heading); font-weight: 500; font-size: clamp(15px, 1.4vw, 20px); color: var(--gg-gold-soft); letter-spacing: 0.18em; text-transform: uppercase; margin-top: 4px; }
.gg-subtitle { margin-top: 18px; display: inline-block; padding: 8px 22px; background: rgba(15,31,51,0.6); border-left: 3px solid var(--gg-red); border-right: 3px solid var(--gg-red);
  font-family: var(--font-body); font-size: 14px; color: rgba(250,250,246,0.85); letter-spacing: 0.18em; }
/* ── 4 stats 关键数据 ── */
.gg-stats-row { position: relative; z-index: 10; display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; max-width: 1100px; margin: 0 auto 40px; padding: 0 24px; }
.gg-stat { position: relative; padding: 18px 22px 16px; background: linear-gradient(180deg, rgba(15,31,51,0.85) 0%, rgba(30,58,95,0.65) 100%);
  border-top: 2px solid var(--gg-gold); border-bottom: 1px solid rgba(212,175,55,0.4); text-align: center; }
.gg-stat + .gg-stat { border-left: 1px solid rgba(212,175,55,0.2); }
.gg-stat-label { font-family: var(--font-heading); font-size: 10px; font-weight: 600; letter-spacing: 0.35em; color: var(--gg-gold-soft); text-transform: uppercase; margin-bottom: 4px; }
.gg-stat-label-cn { font-family: var(--font-body); font-size: 11px; color: rgba(250,250,246,0.55); letter-spacing: 0.25em; margin-bottom: 8px; }
.gg-stat-value { font-family: var(--font-num); font-weight: 700; font-size: clamp(28px, 3vw, 40px); line-height: 1; color: var(--gg-paper); letter-spacing: 0.02em; }
.gg-stat-value .unit { font-size: 14px; font-weight: 500; color: var(--gg-gold-soft); margin-left: 4px; letter-spacing: 0.1em; }
.gg-stat.featured { background: linear-gradient(180deg, rgba(127,29,29,0.8) 0%, rgba(185,28,28,0.55) 100%); }
/* ── 引言 ── */
.gg-quote { position: relative; z-index: 10; text-align: center; margin: 0 auto; max-width: 900px; padding: 0 24px; }
.gg-quote-text { font-family: var(--font-body); font-weight: 700; font-size: clamp(15px, 1.5vw, 22px); color: var(--gg-gold-soft); letter-spacing: 0.4em;
  text-shadow: 0 0 24px var(--gg-glow), 0 2px 8px rgba(0,0,0,0.6); margin-bottom: 10px; }
.gg-quote-text .sep { color: var(--gg-red-soft); margin: 0 10px; font-weight: 400; }
.gg-quote-sig { font-family: var(--font-heading); font-style: italic; font-size: 11px; letter-spacing: 0.4em; color: rgba(250,250,246,0.55); text-transform: uppercase; }
.gg-quote-sig::before, .gg-quote-sig::after { content: "——"; margin: 0 12px; color: var(--gg-gold); }
/* ── 4 角金线角标 (装饰) ── */
.gg-corner-mark { position: absolute; width: 26px; height: 26px; border: 1px solid var(--gg-gold); z-index: 50; opacity: 0.55; }
.gg-corner-mark::before { content: ""; position: absolute; inset: 4px; border: 1px solid var(--gg-gold); }
.gg-cm-tl { top: 70px; left: 24px; border-right: none; border-bottom: none; }
.gg-cm-tr { top: 70px; right: 24px; border-left: none; border-bottom: none; }
.gg-cm-bl { bottom: 24px; left: 24px; border-right: none; border-top: none; }
.gg-cm-br { bottom: 24px; right: 24px; border-left: none; border-top: none; }
/* ── Section tab 主题色 (下方内容区) ── */
body.gg-body { background: #0A1420; color: var(--gg-paper); font-family: var(--font-body); }
.gg-hero h1, .gg-hero h2, .gg-hero h3 { font-family: var(--font-heading); }
.gg-hero .num, .gg-hero .num * { font-family: var(--font-num); }
.gg-hero + section.tab, .gg-hero ~ section.tab { background: #0A1420; color: var(--gg-paper); border-top: 1px solid #1F1408; }
.gg-hero + section.tab h2, .gg-hero + section.tab h3,
.gg-hero ~ section.tab h2, .gg-hero ~ section.tab h3 { color: var(--gg-paper); }
.gg-hero + section.tab p, .gg-hero + section.tab .lede,
.gg-hero ~ section.tab p, .gg-hero ~ section.tab .lede { color: rgba(250,250,246,0.78); }
.gg-hero + section.tab .bento-card, .gg-hero + section.tab .company-card, .gg-hero + section.tab .curriculum-block,
.gg-hero ~ section.tab .bento-card, .gg-hero ~ section.tab .company-card, .gg-hero ~ section.tab .curriculum-block { background: rgba(15,31,51,0.55); border: 1px solid rgba(212,175,55,0.25); color: var(--gg-paper); }
.gg-hero + section.tab .bento-card:hover, .gg-hero + section.tab .company-card:hover, .gg-hero + section.tab .curriculum-block:hover,
.gg-hero ~ section.tab .bento-card:hover, .gg-hero ~ section.tab .company-card:hover, .gg-hero ~ section.tab .curriculum-block:hover { border-color: var(--gg-gold); }
.gg-hero + section.tab .quote, .gg-hero ~ section.tab .quote { background: rgba(15,31,51,0.55); border: 1px solid rgba(212,175,55,0.25); border-left: 4px solid var(--gg-gold); }
.gg-hero + section.tab .quote-text, .gg-hero ~ section.tab .quote-text { color: var(--gg-gold-soft); }
.gg-hero + section.tab .course-name, .gg-hero ~ section.tab .course-name { color: var(--gg-paper); }
.gg-hero + section.tab .course-credit, .gg-hero ~ section.tab .course-credit { color: var(--gg-gold); }
.gg-hero ~ footer { color: rgba(250,250,246,0.5); }
/* ── 响应式 ── */
@media (max-width: 1280px) {
  .gg-hero { min-height: 660px; padding: 80px 0 90px; }
  .gg-stats-row { grid-template-columns: repeat(2, 1fr); }
  .gg-main-emblem { width: 240px; height: 240px; }
  .gg-hu-tag { font-size: 11px; padding: 6px 14px 6px 12px; }
}
@media (max-width: 768px) {
  .gg-hero { min-height: auto; padding: 72px 0 60px; }
  .gg-stats-row { grid-template-columns: 1fr 1fr; }
  .gg-main-emblem { width: 180px; height: 180px; opacity: 0.12; }
  .gg-hero-title { font-size: clamp(1.875rem, 8vw, 2.5rem); }
  .gg-quote-text { letter-spacing: 0.25em; }
  .gg-corner-mark { width: 20px; height: 20px; }
  .gg-cm-tl, .gg-cm-tr { top: 64px; }
}
/* ── 主体 section tab 样式 (复刻 agri 范式 + 主题色) ── */
section.tab { border-top: 1px solid rgba(212, 175, 55, 0.25); }
section.tab h2 { color: #0F1F33; font-size: clamp(1.375rem, 2.2vw, 1.625rem); font-weight: 600; }
section.tab h3 { color: #0F1F33; font-family: var(--font-heading); }
section.tab p, section.tab li { font-family: var(--font-body); }
section.tab p.lede { color: rgba(250, 250, 246, 0.55); }
.watermark { font-family: var(--font-heading); color: #0F1F33; opacity: 0.04; }
footer { background: #FAFAF6; border-top: 1px solid rgba(212, 175, 55, 0.25); }
footer .label { color: #0F1F33; font-family: var(--font-body); }
footer .data-source { color: #2A4A75; }
.drop-cap::first-letter { font-family: var(--font-heading); color: #D4AF37; }
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.bento-item { padding: 28px 24px 24px; background: rgba(250, 250, 246, 0.55); border: 1px solid rgba(212, 175, 55, 0.25); border-radius: 4px; position: relative; transition: border-color 250ms, transform 250ms; box-shadow: 0 1px 0 rgba(212, 175, 55, 0.08); }
.bento-item::before { content: "◆"; position: absolute; top: 20px; right: 20px; color: #2A4A75; font-size: 0.875rem; opacity: 0.4; }
.bento-item:nth-child(3)::before, .bento-item:nth-child(6)::before, .bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: #2A4A75; z-index: 1; pointer-events: none; }
.bento-item:hover { border-color: #2A4A75; transform: translateY(-2px); }
.bento-monogram { position: absolute; top: 20px; right: 50px; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #0F1F33; color: #FAFAF6; font-family: var(--font-heading); font-size: 1.0625rem; font-weight: 700; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #0F1F33; border: 1px solid #0F1F33; border-radius: 0; font-family: var(--font-heading); font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; margin-bottom: 12px; }
.bento-name { font-family: var(--font-heading); font-size: 1.1875rem; font-weight: 700; margin-bottom: 4px; color: #0F1F33; padding-right: 80px; text-wrap: balance; line-height: 1.3; }
.bento-tag { font-family: var(--font-heading); font-size: 0.8125rem; color: #2A4A75; line-height: 1.5; }
.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 28px 24px 22px; background: rgba(250, 250, 246, 0.55); border: 1px solid rgba(212, 175, 55, 0.25); border-radius: 4px; position: relative; transition: border-color 250ms, transform 250ms; }
.company:hover { border-color: #2A4A75; transform: translateY(-2px); }
.company-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.company-monogram { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #0F1F33; color: #FAFAF6; font-family: var(--font-heading); font-size: 1.0625rem; font-weight: 700; }
.company-tier { padding: 2px 8px; border: 1px solid #2A4A75; color: #2A4A75; font-family: var(--font-heading); font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.1em; }
.tier-S { background: #0F1F33; color: #FAFAF6; border-color: #0F1F33; }
.tier-A { background: transparent; }
.tier-B { background: transparent; color: #2A4A75; border-color: rgba(212, 175, 55, 0.25); }
.company-name { font-family: var(--font-heading); font-size: 1.1875rem; font-weight: 700; margin-bottom: 8px; color: #0F1F33; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 10px; border-top: 1px solid rgba(212, 175, 55, 0.25); }
.sparkline-bar { flex: 1; background: rgba(212, 175, 55, 0.25); min-height: 2px; transition: background 250ms; }
.company:hover .sparkline-bar { background: #2A4A75; opacity: 0.7; }
.sparkline-label { font-family: var(--font-heading); font-size: 0.6875rem; color: #2A4A75; letter-spacing: 0.05em; margin-top: 6px; }
.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: rgba(250, 250, 246, 0.55); border: 1px solid rgba(212, 175, 55, 0.25); border-radius: 4px; overflow: hidden; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 20px 24px; text-align: left; border-bottom: 1px solid rgba(212, 175, 55, 0.25); font-size: 0.9375rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: #FAFAF6; font-family: var(--font-heading); font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.12em; color: #2A4A75; }
.salary-stage { color: #0F1F33; }
.salary-bar { display: inline-block; width: 80px; height: 4px; background: rgba(212, 175, 55, 0.12); margin-left: 12px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #2A4A75; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); }
.yoy { display: inline-block; font-family: var(--font-heading); font-size: 0.8125rem; font-weight: 600; margin-left: 12px; padding: 2px 8px; }
.yoy.up { color: #0F1F33; background: rgba(212, 175, 55, 0.10); }
.yoy.down { color: #DC2626; background: rgba(220, 38, 38, 0.10); }
.yoy.flat { color: rgba(250, 250, 246, 0.55); }
.direction-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 200px 1fr 70px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid rgba(212, 175, 55, 0.25); }
.direction:last-child { border-bottom: none; }
.direction-name { font-family: var(--font-heading); font-size: 1.0625rem; font-weight: 600; color: #0F1F33; }
.direction-bar { height: 8px; background: rgba(212, 175, 55, 0.12); overflow: hidden; border-radius: 2px; }
.direction-bar-fill { height: 100%; background: #2A4A75; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); border-radius: 2px; }
.direction-pct { font-family: var(--font-heading); font-weight: 700; text-align: right; font-size: 1.0625rem; color: #0F1F33; }
.path-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: rgba(250, 250, 246, 0.55); border: 1px solid rgba(212, 175, 55, 0.25); border-radius: 4px; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #2A4A75; transform: translateY(-2px); }
.path-pct { font-family: var(--font-heading); font-size: 2.5rem; font-weight: 700; color: #0F1F33; margin-bottom: 4px; line-height: 1; }
.path-name { font-family: var(--font-heading); color: #2A4A75; font-size: 0.875rem; margin-top: 8px; }
.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 28px 32px 24px; background: rgba(250, 250, 246, 0.55); border: 1px solid rgba(212, 175, 55, 0.25); border-left: 4px solid #D4AF37; border-radius: 0 4px 4px 0; margin-bottom: 16px; transition: border-left-width 250ms, transform 250ms; }
.quote:hover { border-left-width: 12px; transform: translateX(4px); }
.quote-head { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.quote-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #0F1F33; color: #FAFAF6; font-family: var(--font-heading); font-size: 1rem; font-weight: 700; }
.quote-byline strong { display: block; font-family: var(--font-heading); font-weight: 700; color: #0F1F33; font-size: 0.9375rem; }
.quote-byline .quote-source { font-family: var(--font-heading); color: rgba(250, 250, 246, 0.55); font-size: 0.75rem; }
.quote-text { font-family: var(--font-heading); font-style: italic; font-size: 1.1875rem; line-height: 1.65; color: #0F1F33; }
.quote-text::before { content: "「"; color: #D4AF37; }
.quote-text::after { content: "」"; color: #D4AF37; }
.xuanke-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 200px 1fr 80px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid rgba(212, 175, 55, 0.25); }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-family: var(--font-heading); font-size: 1.0625rem; color: #0F1F33; }
.xuanke-bar { height: 6px; background: rgba(212, 175, 55, 0.25); overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #2A4A75; }
.xuanke-pct { font-family: var(--font-heading); font-weight: 700; text-align: right; font-size: 1.0625rem; color: #0F1F33; }
.curriculum-lede { font-family: var(--font-heading); color: #2A4A75; font-size: 1.0625rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.curriculum-block { padding: 22px 26px; background: rgba(250, 250, 246, 0.55); border: 1px solid rgba(212, 175, 55, 0.25); border-radius: 3px; margin-bottom: 18px; transition: border-color 250ms; }
.curriculum-block:last-child { margin-bottom: 0; }
.curriculum-block:hover { border-color: #2A4A75; }
.curriculum-title { font-family: var(--font-heading); font-size: 1.0625rem; color: #0F1F33; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid rgba(212, 175, 55, 0.30); font-weight: 700; }
.course { color: #0F1F33; border-bottom: 1px dashed rgba(212, 175, 55, 0.20); padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; gap: 12px; font-size: 0.9375rem; transition: background 200ms, padding-left 200ms; }
.course:hover { background: rgba(212, 175, 55, 0.04); padding-left: 8px; }
.course-name { color: #0F1F33; }
.course-credit { color: #2A4A75; font-family: var(--font-heading); font-style: italic; font-size: 0.8125rem; flex-shrink: 0; font-weight: 600; }
.cta-block { margin-top: 32px; padding: 64px 48px; background: rgba(250, 250, 246, 0.55); border: 1px solid #0F1F33; text-align: center; position: relative; }
.cta-block::before { content: "◆  ◆  ◆"; position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: #FAFAF6; padding: 0 16px; color: #0F1F33; font-size: 0.875rem; letter-spacing: 0.5em; }
.cta-block h3 { font-family: var(--font-heading); font-size: 1.75rem; margin-bottom: 12px; color: #0F1F33; position: relative; z-index: 1; font-weight: 700; }
.cta-block p { color: rgba(250, 250, 246, 0.55); margin: 0 auto 28px; max-width: 560px; position: relative; z-index: 1; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; position: relative; z-index: 1; }
.cta-input { padding: 14px 18px; background: #FAFAF6; border: 1px solid rgba(212, 175, 55, 0.25); color: #0F1F33; font-family: var(--font-heading); font-size: 1rem; width: 180px; outline: none; }
.cta-input:focus { border-color: #2A4A75; }
.cta-button { padding: 14px 36px; background: #0F1F33; color: #FAFAF6; font-family: var(--font-heading); font-size: 1rem; font-weight: 700; letter-spacing: 0.05em; }
.cta-button:hover { background: #FAFAF6; color: #2A4A75; }
.cta-note { font-family: var(--font-heading); font-size: 0.75rem; color: rgba(250, 250, 246, 0.55); margin-top: 16px; position: relative; z-index: 1; }
.tag { display: inline-block; padding: 4px 12px; border: 1px solid #0F1F33; color: #0F1F33; font-family: var(--font-heading); font-size: 0.75rem; letter-spacing: 0.05em; }
.tag.primary { background: #0F1F33; color: #FAFAF6; }

/* ── GONGAN 深色主题 section 文字色反转 (警蓝底, 文字必须亮色) ── */
.gg-hero + section.tab, .gg-hero ~ section.tab,
/* (原通配 * { color: inherit } 删除 — 会让 ovv-card 内部文字透明) */
/* 标题 (h2/h3) — 金色突出 */
.gg-hero + section.tab h2, .gg-hero + section.tab h3,
.gg-hero ~ section.tab h2, .gg-hero ~ section.tab h3 { color: var(--gg-gold-soft); }
/* 章节小字 (06/10 · 院校) */
.gg-hero + section.tab .section-num, .gg-hero ~ section.tab .section-num { color: var(--gg-gold); }
/* lede 段 */
.gg-hero + section.tab p.lede, .gg-hero ~ section.tab p.lede { color: rgba(250, 250, 246, 0.85); }
.gg-hero + section.tab p, .gg-hero ~ section.tab p,
.gg-hero + section.tab li, .gg-hero ~ section.tab li { color: rgba(250, 250, 246, 0.78); }
/* bento (院校) */
.gg-hero + section.tab .bento-item, .gg-hero ~ section.tab .bento-item { background: rgba(15, 31, 51, 0.65); border-color: rgba(212, 175, 55, 0.30); }
.gg-hero + section.tab .bento-monogram, .gg-hero ~ section.tab .bento-monogram { background: var(--gg-gold); color: var(--gg-blue-dk); }
.gg-hero + section.tab .bento-rank, .gg-hero ~ section.tab .bento-rank { color: var(--gg-gold-soft); border-color: var(--gg-gold); }
.gg-hero + section.tab .bento-name, .gg-hero ~ section.tab .bento-name { color: var(--gg-paper); }
.gg-hero + section.tab .bento-tag, .gg-hero ~ section.tab .bento-tag { color: rgba(212, 175, 55, 0.7); }
/* company (头部公司) */
.gg-hero + section.tab .company, .gg-hero ~ section.tab .company { background: rgba(15, 31, 51, 0.65); border-color: rgba(212, 175, 55, 0.30); }
.gg-hero + section.tab .company-monogram, .gg-hero ~ section.tab .company-monogram { background: var(--gg-gold); color: var(--gg-blue-dk); }
.gg-hero + section.tab .company-name, .gg-hero ~ section.tab .company-name { color: var(--gg-paper); }
.gg-hero + section.tab .company-tier, .gg-hero ~ section.tab .company-tier { color: var(--gg-gold-soft); border-color: var(--gg-gold); }
.gg-hero + section.tab .tier-S, .gg-hero ~ section.tab .tier-S { background: var(--gg-gold); color: var(--gg-blue-dk); border-color: var(--gg-gold); }
.gg-hero + section.tab .tier-B, .gg-hero ~ section.tab .tier-B { color: rgba(212, 175, 55, 0.6); border-color: rgba(212, 175, 55, 0.3); }
.gg-hero + section.tab .sparkline, .gg-hero ~ section.tab .sparkline { border-top-color: rgba(212, 175, 55, 0.20); }
.gg-hero + section.tab .sparkline-bar, .gg-hero ~ section.tab .sparkline-bar { background: rgba(212, 175, 55, 0.4); }
.gg-hero + section.tab .company:hover .sparkline-bar, .gg-hero ~ section.tab .company:hover .sparkline-bar { background: var(--gg-gold); }
.gg-hero + section.tab .sparkline-label, .gg-hero ~ section.tab .sparkline-label { color: rgba(212, 175, 55, 0.6); }
/* salary */
.gg-hero + section.tab .salary-table, .gg-hero ~ section.tab .salary-table { background: rgba(15, 31, 51, 0.65); border-color: rgba(212, 175, 55, 0.30); color: var(--gg-paper); }
.gg-hero + section.tab .salary-table th, .gg-hero ~ section.tab .salary-table th { background: rgba(15, 31, 51, 0.85); color: var(--gg-gold-soft); }
.gg-hero + section.tab .salary-table td, .gg-hero ~ section.tab .salary-table td { color: var(--gg-paper); border-bottom-color: rgba(212, 175, 55, 0.20); }
.gg-hero + section.tab .salary-stage, .gg-hero ~ section.tab .salary-stage { color: var(--gg-paper); }
.gg-hero + section.tab .salary-bar, .gg-hero ~ section.tab .salary-bar { background: rgba(212, 175, 55, 0.20); }
.gg-hero + section.tab .salary-bar-fill, .gg-hero ~ section.tab .salary-bar-fill { background: var(--gg-gold); }
.gg-hero + section.tab .yoy.up, .gg-hero ~ section.tab .yoy.up { color: #22C55E; background: rgba(34, 197, 94, 0.12); }
.gg-hero + section.tab .yoy.down, .gg-hero ~ section.tab .yoy.down { color: #FCA5A5; background: rgba(220, 38, 38, 0.12); }
/* direction (就业方向) — 关键修复: 文字必须亮色 */
.gg-hero + section.tab .direction-name, .gg-hero ~ section.tab .direction-name { color: var(--gg-paper); }
.gg-hero + section.tab .direction-bar, .gg-hero ~ section.tab .direction-bar { background: rgba(212, 175, 55, 0.20); }
.gg-hero + section.tab .direction-bar-fill, .gg-hero ~ section.tab .direction-bar-fill { background: var(--gg-gold); }
.gg-hero + section.tab .direction-pct, .gg-hero ~ section.tab .direction-pct { color: var(--gg-gold-soft); }
.gg-hero + section.tab .direction, .gg-hero ~ section.tab .direction { border-bottom-color: rgba(212, 175, 55, 0.20); }
/* path */
.gg-hero + section.tab .path-card, .gg-hero ~ section.tab .path-card { background: rgba(15, 31, 51, 0.65); border-color: rgba(212, 175, 55, 0.30); }
.gg-hero + section.tab .path-pct, .gg-hero ~ section.tab .path-pct { color: var(--gg-gold-soft); }
.gg-hero + section.tab .path-name, .gg-hero ~ section.tab .path-name { color: rgba(212, 175, 55, 0.7); }
/* quote (校友引言) — 关键修复 */
.gg-hero + section.tab .quote, .gg-hero ~ section.tab .quote { background: rgba(15, 31, 51, 0.65); border-color: rgba(212, 175, 55, 0.30); border-left: 4px solid var(--gg-gold); }
.gg-hero + section.tab .quote-avatar, .gg-hero ~ section.tab .quote-avatar { background: var(--gg-gold); color: var(--gg-blue-dk); }
.gg-hero + section.tab .quote-byline strong, .gg-hero ~ section.tab .quote-byline strong { color: var(--gg-paper); }
.gg-hero + section.tab .quote-byline .quote-source, .gg-hero ~ section.tab .quote-byline .quote-source { color: rgba(212, 175, 55, 0.7); }
.gg-hero + section.tab .quote-text, .gg-hero ~ section.tab .quote-text { color: var(--gg-paper); }
.gg-hero + section.tab .quote-text::before, .gg-hero ~ section.tab .quote-text::before,
.gg-hero + section.tab .quote-text::after, .gg-hero ~ section.tab .quote-text::after { color: var(--gg-gold); }
/* xuanke (选科要求) — 关键修复 */
.gg-hero + section.tab .xuanke-name, .gg-hero ~ section.tab .xuanke-name { color: var(--gg-paper); }
.gg-hero + section.tab .xuanke-bar, .gg-hero ~ section.tab .xuanke-bar { background: rgba(212, 175, 55, 0.20); }
.gg-hero + section.tab .xuanke-bar-fill, .gg-hero ~ section.tab .xuanke-bar-fill { background: var(--gg-gold); }
.gg-hero + section.tab .xuanke-pct, .gg-hero ~ section.tab .xuanke-pct { color: var(--gg-gold-soft); }
.gg-hero + section.tab .xuanke, .gg-hero ~ section.tab .xuanke { border-bottom-color: rgba(212, 175, 55, 0.20); }
/* curriculum */
.gg-hero + section.tab .curriculum-block, .gg-hero ~ section.tab .curriculum-block { background: rgba(15, 31, 51, 0.65); border-color: rgba(212, 175, 55, 0.30); }
.gg-hero + section.tab .curriculum-title, .gg-hero ~ section.tab .curriculum-title { color: var(--gg-gold-soft); border-bottom-color: rgba(212, 175, 55, 0.30); }
.gg-hero + section.tab .course, .gg-hero ~ section.tab .course { color: var(--gg-paper); border-bottom-color: rgba(212, 175, 55, 0.20); }
.gg-hero + section.tab .course:hover, .gg-hero ~ section.tab .course:hover { background: rgba(212, 175, 55, 0.05); }
.gg-hero + section.tab .course-name, .gg-hero ~ section.tab .course-name { color: var(--gg-paper); }
.gg-hero + section.tab .course-credit, .gg-hero ~ section.tab .course-credit { color: var(--gg-gold-soft); }
.gg-hero + section.tab .curriculum-lede, .gg-hero ~ section.tab .curriculum-lede { color: var(--gg-gold-soft); }
/* cta */
.gg-hero + section.tab .cta-block, .gg-hero ~ section.tab .cta-block { background: rgba(15, 31, 51, 0.7); border-color: var(--gg-gold); }
.gg-hero + section.tab .cta-block::before, .gg-hero ~ section.tab .cta-block::before { background: var(--gg-blue-dk); color: var(--gg-gold); }
.gg-hero + section.tab .cta-block h3, .gg-hero ~ section.tab .cta-block h3 { color: var(--gg-gold-soft); }
.gg-hero + section.tab .cta-block p, .gg-hero ~ section.tab .cta-block p { color: rgba(250, 250, 246, 0.78); }
.gg-hero + section.tab .cta-input, .gg-hero ~ section.tab .cta-input { background: rgba(15, 31, 51, 0.8); border-color: rgba(212, 175, 55, 0.4); color: var(--gg-paper); }
.gg-hero + section.tab .cta-input:focus, .gg-hero ~ section.tab .cta-input:focus { border-color: var(--gg-gold); }
.gg-hero + section.tab .cta-button, .gg-hero ~ section.tab .cta-button { background: var(--gg-gold); color: var(--gg-blue-dk); }
.gg-hero + section.tab .cta-button:hover, .gg-hero ~ section.tab .cta-button:hover { background: var(--gg-paper); color: var(--gg-blue-dk); }
.gg-hero + section.tab .cta-note, .gg-hero ~ section.tab .cta-note { color: rgba(212, 175, 55, 0.6); }
.gg-hero + section.tab .tag, .gg-hero ~ section.tab .tag { color: var(--gg-gold-soft); border-color: var(--gg-gold); }
.gg-hero + section.tab .tag.primary, .gg-hero ~ section.tab .tag.primary { background: var(--gg-gold); color: var(--gg-blue-dk); }
.gg-hero + section.tab .drop-cap::first-letter, .gg-hero ~ section.tab .drop-cap::first-letter { color: var(--gg-gold); }
.gg-hero + section.tab .watermark, .gg-hero ~ section.tab .watermark { color: var(--gg-gold); opacity: 0.03; }
.gg-hero + section.tab footer, .gg-hero ~ section.tab footer { background: rgba(15, 31, 51, 0.85); color: rgba(250, 250, 246, 0.5); }
.gg-hero + section.tab footer .label, .gg-hero ~ section.tab footer .label { color: var(--gg-gold-soft); }
.gg-hero + section.tab footer .data-source, .gg-hero ~ section.tab footer .data-source { color: rgba(212, 175, 55, 0.6); }

/* ── GONGAN ovv-card (速览 3 子卡) 深色覆写 ── */
.gg-hero + section.tab .ovv-card, .gg-hero ~ section.tab .ovv-card { background: rgba(15, 31, 51, 0.7); border-color: rgba(212, 175, 55, 0.3); color: var(--gg-paper); }
.gg-hero + section.tab .ovv-lede, .gg-hero ~ section.tab .ovv-lede { color: var(--gg-paper); }
.gg-hero + section.tab .ovv-lede::first-letter, .gg-hero ~ section.tab .ovv-lede::first-letter { color: var(--gg-gold); }
.gg-hero + section.tab .ovv-card-title, .gg-hero ~ section.tab .ovv-card-title { color: var(--gg-gold-soft); }
.gg-hero + section.tab .ovv-card-num, .gg-hero ~ section.tab .ovv-card-num { color: var(--gg-gold); }
.gg-hero + section.tab .ovv-card-tag, .gg-hero ~ section.tab .ovv-card-tag { color: rgba(212, 175, 55, 0.7); border-color: rgba(212, 175, 55, 0.4); }
.gg-hero + section.tab .ovv-foundations-label, .gg-hero ~ section.tab .ovv-foundations-label { color: var(--gg-gold-soft); }
.gg-hero + section.tab .ovv-tl-step, .gg-hero ~ section.tab .ovv-tl-step { background: rgba(212, 175, 55, 0.10); color: var(--gg-paper); border-color: rgba(212, 175, 55, 0.3); }
.gg-hero + section.tab .ovv-directions-label, .gg-hero ~ section.tab .ovv-directions-label { color: var(--gg-gold-soft); }
.gg-hero + section.tab .ovv-dir, .gg-hero ~ section.tab .ovv-dir { background: rgba(15, 31, 51, 0.6); border-color: rgba(212, 175, 55, 0.3); }
.gg-hero + section.tab .ovv-dir-num, .gg-hero ~ section.tab .ovv-dir-num { color: var(--gg-gold); }
.gg-hero + section.tab .ovv-dir-name, .gg-hero ~ section.tab .ovv-dir-name { color: var(--gg-paper); }
.gg-hero + section.tab .ovv-dir-desc, .gg-hero ~ section.tab .ovv-dir-desc { color: rgba(212, 175, 55, 0.7); }
.gg-hero + section.tab .ovv-skills, .gg-hero ~ section.tab .ovv-skills { color: var(--gg-paper); }
.gg-hero + section.tab .ovv-skill, .gg-hero ~ section.tab .ovv-skill { background: rgba(212, 175, 55, 0.10); color: var(--gg-paper); border-color: rgba(212, 175, 55, 0.3); }
.gg-hero + section.tab .ovv-bonus, .gg-hero ~ section.tab .ovv-bonus { color: var(--gg-gold-soft); background: rgba(212, 175, 55, 0.08); border-left: 4px solid var(--gg-gold); }
.gg-hero + section.tab .ovv-fit-col.is-yes, .gg-hero ~ section.tab .ovv-fit-col.is-yes { color: #22C55E; }
.gg-hero + section.tab .ovv-fit-col.is-no, .gg-hero ~ section.tab .ovv-fit-col.is-no { color: #FCA5A5; }
.gg-hero + section.tab .ovv-fit-label, .gg-hero ~ section.tab .ovv-fit-label { color: var(--gg-gold); }
.gg-hero + section.tab .ovv-fit-list li, .gg-hero ~ section.tab .ovv-fit-list li { color: var(--gg-paper); }
.gg-hero + section.tab .ovv-pit, .gg-hero ~ section.tab .ovv-pit { background: rgba(15, 31, 51, 0.6); border-color: rgba(212, 175, 55, 0.3); }
.gg-hero + section.tab .ovv-pit-num, .gg-hero ~ section.tab .ovv-pit-num { color: var(--gg-gold); }
.gg-hero + section.tab .ovv-pit-myth, .gg-hero ~ section.tab .ovv-pit-myth { color: #FCA5A5; }
.gg-hero + section.tab .ovv-pit-reality, .gg-hero ~ section.tab .ovv-pit-reality { color: var(--gg-paper); }

/* ── GONGAN ovv-card (速览 3 子卡) 文字加亮 + 边框加深 ── */
.gg-hero + section.tab .ovv-card, .gg-hero ~ section.tab .ovv-card { background: rgba(15, 31, 51, 0.85); border: 1.5px solid rgba(212, 175, 55, 0.45); box-shadow: 0 2px 12px rgba(0,0,0,0.4); }
.gg-hero + section.tab .ovv-card.is-blue, .gg-hero ~ section.tab .ovv-card.is-blue { border-color: rgba(96, 165, 250, 0.6); }
.gg-hero + section.tab .ovv-card.is-orange, .gg-hero ~ section.tab .ovv-card.is-orange { border-color: rgba(251, 146, 60, 0.7); }
.gg-hero + section.tab .ovv-lede, .gg-hero ~ section.tab .ovv-lede { color: var(--gg-paper); line-height: 1.85; }
.gg-hero + section.tab .ovv-lede::first-letter, .gg-hero ~ section.tab .ovv-lede::first-letter { color: var(--gg-gold); font-size: 3em; }
.gg-hero + section.tab .ovv-card-head, .gg-hero ~ section.tab .ovv-card-head { border-bottom: 1px solid rgba(212, 175, 55, 0.3); }
.gg-hero + section.tab .ovv-card-title, .gg-hero ~ section.tab .ovv-card-title { color: var(--gg-gold-soft); font-weight: 700; }
.gg-hero + section.tab .ovv-card-num, .gg-hero ~ section.tab .ovv-card-num { color: var(--gg-gold); font-weight: 700; }
.gg-hero + section.tab .ovv-card-tag, .gg-hero ~ section.tab .ovv-card-tag { color: var(--gg-paper); background: rgba(212, 175, 55, 0.18); border: 1px solid rgba(212, 175, 55, 0.5); padding: 3px 10px; }
.gg-hero + section.tab .ovv-foundations-label, .gg-hero ~ section.tab .ovv-foundations-label { color: var(--gg-gold-soft); font-weight: 600; letter-spacing: 0.1em; }
.gg-hero + section.tab .ovv-timeline, .gg-hero ~ section.tab .ovv-timeline { border-top: 1px solid rgba(212, 175, 55, 0.2); border-bottom: 1px solid rgba(212, 175, 55, 0.2); }
.gg-hero + section.tab .ovv-tl-step span, .gg-hero ~ section.tab .ovv-tl-step span { color: var(--gg-paper); font-weight: 600; font-size: 0.95rem; }
.gg-hero + section.tab .ovv-tl-step, .gg-hero ~ section.tab .ovv-tl-step { background: rgba(212, 175, 55, 0.15); border: 1.5px solid rgba(212, 175, 55, 0.5); padding: 12px 16px; }
.gg-hero + section.tab .ovv-tl-step::before, .gg-hero ~ section.tab .ovv-tl-step::before { background: var(--gg-gold); border-color: var(--gg-gold); width: 12px; height: 12px; box-shadow: 0 0 8px var(--gg-glow); }
.gg-hero + section.tab .ovv-directions-label, .gg-hero ~ section.tab .ovv-directions-label { color: var(--gg-gold-soft); font-weight: 600; letter-spacing: 0.1em; }
.gg-hero + section.tab .ovv-dir, .gg-hero ~ section.tab .ovv-dir { background: rgba(15, 31, 51, 0.7); border: 1.5px solid rgba(212, 175, 55, 0.4); }
.gg-hero + section.tab .ovv-dir-num, .gg-hero ~ section.tab .ovv-dir-num { color: var(--gg-gold); font-weight: 700; }
.gg-hero + section.tab .ovv-dir-name, .gg-hero ~ section.tab .ovv-dir-name { color: var(--gg-paper); font-weight: 700; font-size: 1.0625rem; }
.gg-hero + section.tab .ovv-dir-desc, .gg-hero ~ section.tab .ovv-dir-desc { color: rgba(212, 175, 55, 0.85); font-size: 0.85rem; }
.gg-hero + section.tab .ovv-skills-label, .gg-hero ~ section.tab .ovv-skills-label { color: var(--gg-gold-soft); }
.gg-hero + section.tab .ovv-skill, .gg-hero ~ section.tab .ovv-skill { background: rgba(212, 175, 55, 0.18); color: var(--gg-paper); border: 1.5px solid rgba(212, 175, 55, 0.5); font-weight: 500; }
.gg-hero + section.tab .ovv-bonus, .gg-hero ~ section.tab .ovv-bonus { color: var(--gg-paper); background: rgba(212, 175, 55, 0.10); border-left: 4px solid var(--gg-gold); padding: 16px 20px; line-height: 1.75; }
.gg-hero + section.tab .ovv-fit-col.is-yes, .gg-hero ~ section.tab .ovv-fit-col.is-yes { color: #22C55E; font-weight: 600; }
.gg-hero + section.tab .ovv-fit-col.is-no, .gg-hero ~ section.tab .ovv-fit-col.is-no { color: #FCA5A5; font-weight: 600; }
.gg-hero + section.tab .ovv-fit-label, .gg-hero ~ section.tab .ovv-fit-label { color: var(--gg-gold); font-weight: 700; }
.gg-hero + section.tab .ovv-fit-list li, .gg-hero ~ section.tab .ovv-fit-list li { color: var(--gg-paper); line-height: 1.7; padding: 4px 0; }
.gg-hero + section.tab .ovv-fit-list li::before, .gg-hero ~ section.tab .ovv-fit-list li::before { color: var(--gg-gold); }
.gg-hero + section.tab .ovv-pit, .gg-hero ~ section.tab .ovv-pit { background: rgba(15, 31, 51, 0.7); border: 1.5px solid rgba(212, 175, 55, 0.4); }
.gg-hero + section.tab .ovv-pit-num, .gg-hero ~ section.tab .ovv-pit-num { color: var(--gg-gold); font-weight: 700; }
.gg-hero + section.tab .ovv-pit-myth, .gg-hero ~ section.tab .ovv-pit-myth { color: #FCA5A5; font-weight: 600; }
.gg-hero + section.tab .ovv-pit-reality, .gg-hero ~ section.tab .ovv-pit-reality { color: var(--gg-paper); line-height: 1.65; }
/* ── 强制 .path-grid 5 列一行 (高 specificity) ── */
body.gg-body .gg-hero + section.tab .path-grid, body.gg-body .gg-hero ~ section.tab .path-grid,
body.biz-body .biz-hero + section.tab .path-grid, body.biz-body .biz-hero ~ section.tab .path-grid { grid-template-columns: repeat(5, 1fr) !important; gap: 10px !important; }
body.gg-body .gg-hero + section.tab .path-card, body.gg-body .gg-hero ~ section.tab .path-card,
body.biz-body .biz-hero + section.tab .path-card, body.biz-body .biz-hero ~ section.tab .path-card { padding: 24px 8px 20px !important; }
body.gg-body .gg-hero + section.tab .path-pct, body.gg-body .gg-hero ~ section.tab .path-pct,
body.biz-body .biz-hero + section.tab .path-pct, body.biz-body .biz-hero ~ section.tab .path-pct { font-size: clamp(1.5rem, 2.2vw, 2rem) !important; }
body.gg-body .gg-hero + section.tab .path-name, body.gg-body .gg-hero ~ section.tab .path-name,
body.biz-body .biz-hero + section.tab .path-name, body.biz-body .biz-hero ~ section.tab .path-name { font-size: 0.7rem !important; line-height: 1.4 !important; padding: 0 4px !important; word-break: break-all !important; }

/* ── ovv-tl-step 一行 + ovv-fit-list 列表 marker 修复 (所有 ovv 主题) ── */
.gg-hero + section.tab .ovv-timeline, .gg-hero ~ section.tab .ovv-timeline,
.biz-hero + section.tab .ovv-timeline, .biz-hero ~ section.tab .ovv-timeline { display: flex; flex-wrap: nowrap; overflow-x: auto; gap: 10px; padding-bottom: 8px; }
.gg-hero + section.tab .ovv-tl-step, .gg-hero ~ section.tab .ovv-tl-step,
.biz-hero + section.tab .ovv-tl-step, .biz-hero ~ section.tab .ovv-tl-step { flex: 0 0 auto; min-width: 100px; text-align: center; }
.gg-hero + section.tab .ovv-fit-list, .gg-hero ~ section.tab .ovv-fit-list,
.biz-hero + section.tab .ovv-fit-list, .biz-hero ~ section.tab .ovv-fit-list { list-style: none; padding-left: 0; margin: 0; }
.gg-hero + section.tab .ovv-fit-list li, .gg-hero ~ section.tab .ovv-fit-list li,
.biz-hero + section.tab .ovv-fit-list li, .biz-hero ~ section.tab .ovv-fit-list li { padding-left: 0; }
.gg-hero + section.tab .ovv-fit-list li::before, .gg-hero ~ section.tab .ovv-fit-list li::before,
.biz-hero + section.tab .ovv-fit-list li::before, .biz-hero ~ section.tab .ovv-fit-list li::before { content: none; }

"""


# ──────────────────────────────────────────────────────────
# BUSINESS · 工商管理 (椭圆董事局 + 玫瑰金 + 胡桃木 + 屏幕深蓝)
# ──────────────────────────────────────────────────────────
BUSINESS_CSS = """
:root {
  /* 主题色 */
  --biz-walnut-dk: #3E2A1F;  --biz-walnut-soft: #6B4A3A; --biz-walnut-xd: #1F1208;
  --biz-rose-gold: #C77B5C;   --biz-rose-gold-dk: #9C4A35; --biz-rose-gold-soft: #DDA28A;
  --biz-screen-blue: #0B1120; --biz-screen-blue-2: #1E293B;
  --biz-ivory: #F5F0E5;       --biz-bg: #FAFAF6;
  --biz-leather: #1A1A1A;     --biz-burgundy: #6B1F2A; --biz-steel: #5C6770;
  --biz-pos: #22C55E;         --biz-neg: #DC2626; --biz-warn: #F59E0B;
  /* 字体 (修复 v4_styles 未注入 base CSS 的问题) */
  --font-heading: "Bodoni Moda", "Noto Serif SC", serif;
  --font-body:    "Inter", "Noto Serif SC", "PingFang SC", sans-serif;
  --font-cn:      "Noto Serif SC", "Songti SC", "PingFang SC", serif;
  --font-num:     "JetBrains Mono", "Bebas Neue", monospace;
}
@import url('https://fonts.loli.net/css2?family=Bodoni+Moda:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Bebas+Neue&display=swap');
/* ── Hero 主体 ── */
.biz-hero { position: relative; width: 100%; min-height: 720px; padding: 96px 0 110px; overflow: hidden; z-index: 2; isolation: isolate;
  background: radial-gradient(ellipse 60% 40% at 50% 0%, rgba(199,123,92,0.10) 0%, transparent 60%),
              linear-gradient(180deg, #FAFAF6 0%, #F5F0E5 50%, #EFE7D5 100%);
  color: var(--biz-leather); font-family: var(--font-body); border-bottom: 1px solid #E5DCC8; }
.biz-marble { position: absolute; inset: 0; z-index: 1; opacity: 0.4; pointer-events: none;
  background-image: linear-gradient(rgba(62,42,31,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(62,42,31,0.03) 1px, transparent 1px);
  background-size: 32px 32px; }
.biz-ceiling-light { position: absolute; top: 0; left: 0; right: 0; height: 300px; z-index: 2; pointer-events: none;
  background: radial-gradient(ellipse 800px 200px at 50% 0%, rgba(255,235,200,0.4) 0%, transparent 70%); }
.biz-grain { position: absolute; inset: 0; z-index: 1; opacity: 0.18; pointer-events: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>"); mix-blend-mode: multiply; }
/* ── 3 屏数据墙 (顶部装饰背景) ── */
/* ── 椭圆董事桌 (中央) ── */
/* ── 8 椅环 (环绕椭圆桌) ── */
/* ── 8 个座位名牌 ── */
/* ── 6 hu-tag 专业列表 ── */
.biz-hu-tag-row { position: relative; z-index: 10; display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; max-width: 1100px; margin: 0 auto 32px; padding: 0 24px; }
.biz-hu-tag { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px 6px 10px; background: rgba(255,255,255,0.7); border-left: 3px solid var(--biz-rose-gold);
  font-family: var(--font-body); font-size: 12px; color: var(--biz-walnut-dk); letter-spacing: 0.1em; }
.biz-hu-tag-num { font-family: "Bebas Neue", sans-serif; font-size: 13px; color: var(--biz-rose-gold); }
.biz-hu-tag-en { font-family: "Bodoni Moda", serif; font-style: italic; font-size: 9px; color: var(--biz-rose-gold-dk); letter-spacing: 0.2em; }
/* ── 标题区 ── */
.biz-title-zone { position: relative; z-index: 10; text-align: center; max-width: 1100px; margin: 0 auto 28px; padding: 0 24px; }
.biz-top-tag { display: inline-flex; align-items: baseline; gap: 10px; margin-bottom: 10px; }
.biz-top-tag-text { font-family: "Bebas Neue", sans-serif; font-size: 12px; letter-spacing: 0.3em; color: var(--biz-walnut-dk); }
.biz-top-tag-num { font-family: "Bodoni Moda", serif; font-weight: 700; font-size: 18px; color: var(--biz-rose-gold); }
.biz-discipline { font-family: "Bodoni Moda", serif; font-style: italic; font-size: 11px; letter-spacing: 0.5em; color: var(--biz-rose-gold); margin-bottom: 6px; text-transform: uppercase; }
.biz-discipline-cn { font-family: var(--font-body); font-size: 12px; color: var(--biz-walnut-dk); letter-spacing: 0.4em; margin-bottom: 18px; }
.biz-title-main { font-family: var(--font-heading); font-weight: 700; font-size: clamp(2.25rem, 5vw, 3.75rem); line-height: 1.05; color: var(--biz-leather); letter-spacing: -0.01em; margin: 0 0 4px; }
.biz-title-main-cn { font-family: var(--font-body); font-weight: 600; font-size: 20px; color: var(--biz-walnut-dk); letter-spacing: 0.18em; margin: 0 0 14px; }
.biz-title-cn-accent { color: var(--biz-rose-gold); position: relative; }
.biz-title-cn-accent::after { content: ""; display: block; height: 2px; background: linear-gradient(90deg, var(--biz-rose-gold), var(--biz-rose-gold-dk)); margin-top: 6px; width: 80px; margin-left: auto; margin-right: auto; }
.biz-subtitle { font-family: "Bodoni Moda", serif; font-style: italic; font-size: 11px; color: var(--biz-rose-gold-dk); letter-spacing: 0.35em; text-transform: uppercase; }
.biz-subtitle-line { width: 80px; height: 1px; background: var(--biz-rose-gold); margin: 14px auto 16px; }
.biz-lede { font-family: var(--font-body); font-size: 15px; line-height: 1.8; color: var(--biz-walnut-dk); max-width: 720px; margin: 0 auto 18px; }
.biz-lede em { font-style: normal; color: var(--biz-leather); border-bottom: 1.5px solid var(--biz-rose-gold); padding-bottom: 1px; font-weight: 600; }
.biz-hero-quote { font-family: "Bodoni Moda", serif; font-style: italic; font-size: 16px; color: var(--biz-walnut-dk); border-left: 2px solid var(--biz-rose-gold); padding: 8px 0 8px 16px; max-width: 640px; margin: 0 auto; }
.biz-hero-quote-sig { display: block; font-family: "Bebas Neue", sans-serif; font-style: normal; font-size: 11px; color: var(--biz-rose-gold); margin-top: 6px; letter-spacing: 0.25em; }
/* ── 4 stats 底部条 ── */
.biz-stats-strip { position: relative; z-index: 10; display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; max-width: 1100px; margin: 32px auto 0; padding: 0 24px; }
.biz-stat-block { padding: 18px 22px 16px; background: var(--biz-leather); border: 1px solid var(--biz-rose-gold); text-align: center; }
.biz-stat-block + .biz-stat-block { border-left: none; }
.biz-stat-label { font-family: "Bebas Neue", sans-serif; font-size: 11px; letter-spacing: 0.25em; color: var(--biz-rose-gold); margin-bottom: 6px; text-transform: uppercase; }
.biz-stat-num { font-family: var(--font-heading); font-weight: 700; font-size: clamp(28px, 3vw, 36px); line-height: 1; color: var(--biz-rose-gold); }
.biz-stat-num-sub { font-size: 13px; font-weight: 500; color: var(--biz-rose-gold-soft); margin-left: 2px; }
.biz-stat-label-cn { font-family: var(--font-body); font-size: 10px; color: rgba(245,240,229,0.55); margin-top: 6px; letter-spacing: 0.15em; }
/* ── Section tab 主题色 (下方内容区) ── */
body.biz-body { background: var(--biz-bg); color: var(--biz-leather); font-family: var(--font-body); }
.biz-hero h1, .biz-hero h2, .biz-hero h3 { font-family: var(--font-heading); }
.biz-hero .num, .biz-hero .num * { font-family: var(--font-num); }
.biz-hero + section.tab, .biz-hero ~ section.tab { background: var(--biz-bg); color: var(--biz-leather); border-top: 1px solid #E5DCC8; }
.biz-hero + section.tab h2, .biz-hero + section.tab h3,
.biz-hero ~ section.tab h2, .biz-hero ~ section.tab h3 { color: var(--biz-leather); }
.biz-hero + section.tab p, .biz-hero + section.tab .lede,
.biz-hero ~ section.tab p, .biz-hero ~ section.tab .lede { color: var(--biz-walnut-dk); }
.biz-hero + section.tab .bento-card, .biz-hero + section.tab .company-card, .biz-hero + section.tab .curriculum-block,
.biz-hero ~ section.tab .bento-card, .biz-hero ~ section.tab .company-card, .biz-hero ~ section.tab .curriculum-block { background: #FFFFFF; border: 1px solid #E5DCC8; color: var(--biz-leather); }
.biz-hero + section.tab .bento-card:hover, .biz-hero + section.tab .company-card:hover, .biz-hero + section.tab .curriculum-block:hover,
.biz-hero ~ section.tab .bento-card:hover, .biz-hero ~ section.tab .company-card:hover, .biz-hero ~ section.tab .curriculum-block:hover { border-color: var(--biz-rose-gold); }
.biz-hero + section.tab .quote, .biz-hero ~ section.tab .quote { background: #FFFFFF; border: 1px solid #E5DCC8; border-left: 4px solid var(--biz-rose-gold); }
.biz-hero + section.tab .quote-text, .biz-hero ~ section.tab .quote-text { color: var(--biz-walnut-dk); }
.biz-hero + section.tab .course-name, .biz-hero ~ section.tab .course-name { color: var(--biz-leather); }
.biz-hero + section.tab .course-credit, .biz-hero ~ section.tab .course-credit { color: var(--biz-rose-gold); }
.biz-hero + section.tab .path-card, .biz-hero ~ section.tab .path-card { background: #FFFFFF; border: 1px solid #E5DCC8; }
.biz-hero + section.tab .path-card:hover, .biz-hero ~ section.tab .path-card:hover { border-color: var(--biz-rose-gold); }
.biz-hero + section.tab .cta-block, .biz-hero ~ section.tab .cta-block { background: var(--biz-leather); color: #FAFAF6; border: 1px solid var(--biz-rose-gold); }
.biz-hero + section.tab .cta-block h3, .biz-hero + section.tab .cta-block p,
.biz-hero ~ section.tab .cta-block h3, .biz-hero ~ section.tab .cta-block p { color: #FAFAF6; }
.biz-hero ~ footer { color: var(--biz-walnut-dk); }
/* ── 响应式 ── */
@media (max-width: 1280px) {
  .biz-hero { min-height: 660px; padding: 80px 0 90px; }
  .biz-stats-strip { grid-template-columns: repeat(2, 1fr); }
  .biz-stat-block + .biz-stat-block { border-left: 1px solid var(--biz-rose-gold); border-top: none; }
}
@media (max-width: 768px) {
  .biz-hero { min-height: auto; padding: 72px 0 60px; }
  .biz-stats-strip { grid-template-columns: 1fr 1fr; }
  .biz-title-main { font-size: clamp(1.875rem, 7vw, 2.5rem); }
}
/* ── 主体 section tab 样式 (复刻 agri 范式 + 主题色) ── */
section.tab { border-top: 1px solid #E5DCC8; }
section.tab h2 { color: #3E2A1F; font-size: clamp(1.375rem, 2.2vw, 1.625rem); font-weight: 600; }
section.tab h3 { color: #3E2A1F; font-family: var(--font-heading); }
section.tab p, section.tab li { font-family: var(--font-body); }
section.tab p.lede { color: #5C6770; }
.watermark { font-family: var(--font-heading); color: #3E2A1F; opacity: 0.04; }
footer { background: #F5F0E5; border-top: 1px solid #E5DCC8; }
footer .label { color: #3E2A1F; font-family: var(--font-body); }
footer .data-source { color: #5C6770; }
.drop-cap::first-letter { font-family: var(--font-heading); color: #C77B5C; }
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.bento-item { padding: 28px 24px 24px; background: #FFFFFF; border: 1px solid #E5DCC8; border-radius: 4px; position: relative; transition: border-color 250ms, transform 250ms; box-shadow: 0 1px 0 rgba(199, 123, 92, 0.06); }
.bento-item::before { content: "◆"; position: absolute; top: 20px; right: 20px; color: #5C6770; font-size: 0.875rem; opacity: 0.4; }
.bento-item:nth-child(3)::before, .bento-item:nth-child(6)::before, .bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: #5C6770; z-index: 1; pointer-events: none; }
.bento-item:hover { border-color: #5C6770; transform: translateY(-2px); }
.bento-monogram { position: absolute; top: 20px; right: 50px; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #3E2A1F; color: #F5F0E5; font-family: var(--font-heading); font-size: 1.0625rem; font-weight: 700; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #3E2A1F; border: 1px solid #3E2A1F; border-radius: 0; font-family: var(--font-heading); font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; margin-bottom: 12px; }
.bento-name { font-family: var(--font-heading); font-size: 1.1875rem; font-weight: 700; margin-bottom: 4px; color: #3E2A1F; padding-right: 80px; text-wrap: balance; line-height: 1.3; }
.bento-tag { font-family: var(--font-heading); font-size: 0.8125rem; color: #5C6770; line-height: 1.5; }
.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 28px 24px 22px; background: #FFFFFF; border: 1px solid #E5DCC8; border-radius: 4px; position: relative; transition: border-color 250ms, transform 250ms; }
.company:hover { border-color: #5C6770; transform: translateY(-2px); }
.company-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.company-monogram { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #3E2A1F; color: #F5F0E5; font-family: var(--font-heading); font-size: 1.0625rem; font-weight: 700; }
.company-tier { padding: 2px 8px; border: 1px solid #5C6770; color: #5C6770; font-family: var(--font-heading); font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.1em; }
.tier-S { background: #3E2A1F; color: #F5F0E5; border-color: #3E2A1F; }
.tier-A { background: transparent; }
.tier-B { background: transparent; color: #5C6770; border-color: #E5DCC8; }
.company-name { font-family: var(--font-heading); font-size: 1.1875rem; font-weight: 700; margin-bottom: 8px; color: #3E2A1F; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 10px; border-top: 1px solid #E5DCC8; }
.sparkline-bar { flex: 1; background: #E5DCC8; min-height: 2px; transition: background 250ms; }
.company:hover .sparkline-bar { background: #5C6770; opacity: 0.7; }
.sparkline-label { font-family: var(--font-heading); font-size: 0.6875rem; color: #5C6770; letter-spacing: 0.05em; margin-top: 6px; }
.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: #FFFFFF; border: 1px solid #E5DCC8; border-radius: 4px; overflow: hidden; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 20px 24px; text-align: left; border-bottom: 1px solid #E5DCC8; font-size: 0.9375rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: #F5F0E5; font-family: var(--font-heading); font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.12em; color: #5C6770; }
.salary-stage { color: #3E2A1F; }
.salary-bar { display: inline-block; width: 80px; height: 4px; background: rgba(199, 123, 92, 0.12); margin-left: 12px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #5C6770; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); }
.yoy { display: inline-block; font-family: var(--font-heading); font-size: 0.8125rem; font-weight: 600; margin-left: 12px; padding: 2px 8px; }
.yoy.up { color: #3E2A1F; background: rgba(62, 42, 31, 0.08); }
.yoy.down { color: #DC2626; background: rgba(220, 38, 38, 0.08); }
.yoy.flat { color: #5C6770; }
.direction-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 200px 1fr 70px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #E5DCC8; }
.direction:last-child { border-bottom: none; }
.direction-name { font-family: var(--font-heading); font-size: 1.0625rem; font-weight: 600; color: #3E2A1F; }
.direction-bar { height: 8px; background: rgba(199, 123, 92, 0.12); overflow: hidden; border-radius: 2px; }
.direction-bar-fill { height: 100%; background: #5C6770; transition: width 1.5s cubic-bezier(0.16, 1, 0.3, 1); border-radius: 2px; }
.direction-pct { font-family: var(--font-heading); font-weight: 700; text-align: right; font-size: 1.0625rem; color: #3E2A1F; }
.path-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: #FFFFFF; border: 1px solid #E5DCC8; border-radius: 4px; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #5C6770; transform: translateY(-2px); }
.path-pct { font-family: var(--font-heading); font-size: 2.5rem; font-weight: 700; color: #3E2A1F; margin-bottom: 4px; line-height: 1; }
.path-name { font-family: var(--font-heading); color: #5C6770; font-size: 0.875rem; margin-top: 8px; }
.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 28px 32px 24px; background: #FFFFFF; border: 1px solid #E5DCC8; border-left: 4px solid #C77B5C; border-radius: 0 4px 4px 0; margin-bottom: 16px; transition: border-left-width 250ms, transform 250ms; }
.quote:hover { border-left-width: 12px; transform: translateX(4px); }
.quote-head { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.quote-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #3E2A1F; color: #F5F0E5; font-family: var(--font-heading); font-size: 1rem; font-weight: 700; }
.quote-byline strong { display: block; font-family: var(--font-heading); font-weight: 700; color: #3E2A1F; font-size: 0.9375rem; }
.quote-byline .quote-source { font-family: var(--font-heading); color: #5C6770; font-size: 0.75rem; }
.quote-text { font-family: var(--font-heading); font-style: italic; font-size: 1.1875rem; line-height: 1.65; color: #3E2A1F; }
.quote-text::before { content: "「"; color: #C77B5C; }
.quote-text::after { content: "」"; color: #C77B5C; }
.xuanke-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 200px 1fr 80px; align-items: center; gap: 24px; padding: 14px 0; border-bottom: 1px solid #E5DCC8; }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-family: var(--font-heading); font-size: 1.0625rem; color: #3E2A1F; }
.xuanke-bar { height: 6px; background: #E5DCC8; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #5C6770; }
.xuanke-pct { font-family: var(--font-heading); font-weight: 700; text-align: right; font-size: 1.0625rem; color: #3E2A1F; }
.curriculum-lede { font-family: var(--font-heading); color: #5C6770; font-size: 1.0625rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.curriculum-block { padding: 22px 26px; background: #FFFFFF; border: 1px solid #E5DCC8; border-radius: 3px; margin-bottom: 18px; transition: border-color 250ms; }
.curriculum-block:last-child { margin-bottom: 0; }
.curriculum-block:hover { border-color: #5C6770; }
.curriculum-title { font-family: var(--font-heading); font-size: 1.0625rem; color: #3E2A1F; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid rgba(199, 123, 92, 0.30); font-weight: 700; }
.course { color: #3E2A1F; border-bottom: 1px dashed rgba(199, 123, 92, 0.20); padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; gap: 12px; font-size: 0.9375rem; transition: background 200ms, padding-left 200ms; }
.course:hover { background: rgba(199, 123, 92, 0.04); padding-left: 8px; }
.course-name { color: #3E2A1F; }
.course-credit { color: #5C6770; font-family: var(--font-heading); font-style: italic; font-size: 0.8125rem; flex-shrink: 0; font-weight: 600; }
.cta-block { margin-top: 32px; padding: 64px 48px; background: #FFFFFF; border: 1px solid #3E2A1F; text-align: center; position: relative; }
.cta-block::before { content: "◆  ◆  ◆"; position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: #F5F0E5; padding: 0 16px; color: #3E2A1F; font-size: 0.875rem; letter-spacing: 0.5em; }
.cta-block h3 { font-family: var(--font-heading); font-size: 1.75rem; margin-bottom: 12px; color: #3E2A1F; position: relative; z-index: 1; font-weight: 700; }
.cta-block p { color: #5C6770; margin: 0 auto 28px; max-width: 560px; position: relative; z-index: 1; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; position: relative; z-index: 1; }
.cta-input { padding: 14px 18px; background: #F5F0E5; border: 1px solid #E5DCC8; color: #3E2A1F; font-family: var(--font-heading); font-size: 1rem; width: 180px; outline: none; }
.cta-input:focus { border-color: #5C6770; }
.cta-button { padding: 14px 36px; background: #3E2A1F; color: #F5F0E5; font-family: var(--font-heading); font-size: 1rem; font-weight: 700; letter-spacing: 0.05em; }
.cta-button:hover { background: #F5F0E5; color: #5C6770; }
.cta-note { font-family: var(--font-heading); font-size: 0.75rem; color: #5C6770; margin-top: 16px; position: relative; z-index: 1; }
.tag { display: inline-block; padding: 4px 12px; border: 1px solid #3E2A1F; color: #3E2A1F; font-family: var(--font-heading); font-size: 0.75rem; letter-spacing: 0.05em; }
.tag.primary { background: #3E2A1F; color: #F5F0E5; }

/* ── 5 列一行 (GONGAN / BUSINESS 都有 5 个深造路径) ── */
.gg-hero + section.tab .path-grid, .gg-hero ~ section.tab .path-grid,
.biz-hero + section.tab .path-grid, .biz-hero ~ section.tab .path-grid { grid-template-columns: repeat(5, 1fr); }
.gg-hero + section.tab .path-card, .gg-hero ~ section.tab .path-card,
.biz-hero + section.tab .path-card, .biz-hero ~ section.tab .path-card { padding: 28px 12px 24px; }
.gg-hero + section.tab .path-pct, .gg-hero ~ section.tab .path-pct,
.biz-hero + section.tab .path-pct, .biz-hero ~ section.tab .path-pct { font-size: clamp(1.75rem, 2.5vw, 2.25rem); }

/* ── ovv-tl-step 一行 + ovv-fit-list 列表 marker 修复 (所有 ovv 主题) ── */
.gg-hero + section.tab .ovv-timeline, .gg-hero ~ section.tab .ovv-timeline,
.biz-hero + section.tab .ovv-timeline, .biz-hero ~ section.tab .ovv-timeline { display: flex; flex-wrap: nowrap; overflow-x: auto; gap: 10px; padding-bottom: 8px; }
.gg-hero + section.tab .ovv-tl-step, .gg-hero ~ section.tab .ovv-tl-step,
.biz-hero + section.tab .ovv-tl-step, .biz-hero ~ section.tab .ovv-tl-step { flex: 0 0 auto; min-width: 100px; text-align: center; }
.gg-hero + section.tab .ovv-fit-list, .gg-hero ~ section.tab .ovv-fit-list,
.biz-hero + section.tab .ovv-fit-list, .biz-hero ~ section.tab .ovv-fit-list { list-style: none; padding-left: 0; margin: 0; }
.gg-hero + section.tab .ovv-fit-list li, .gg-hero ~ section.tab .ovv-fit-list li,
.biz-hero + section.tab .ovv-fit-list li, .biz-hero ~ section.tab .ovv-fit-list li { padding-left: 0; }
.gg-hero + section.tab .ovv-fit-list li::before, .gg-hero ~ section.tab .ovv-fit-list li::before,
.biz-hero + section.tab .ovv-fit-list li::before, .biz-hero ~ section.tab .ovv-fit-list li::before { content: none; }

"""


BASE_V4_CSS = """
/* ──────────────────────────────────────────────────────────
   BASE_V4_CSS: 8 招底层 (v4 渲染统一注入, 解决新主题 CSS 不继承问题)
   ────────────────────────────────────────────────────────── */
:root {
  /* 字体 (8 主题共用, 主题专属 CSS 可覆盖) */
  --font-heading: "Noto Serif SC", "Cormorant Garamond", "Bodoni Moda", "Cinzel", "Songti SC", serif;
  --font-body:    "Noto Serif SC", "Inter", "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-cn:      "Noto Serif SC", "Songti SC", "PingFang SC", serif;
  --font-num:     "JetBrains Mono", "Bebas Neue", "Oswald", monospace;
  /* 主题色默认 (各主题可覆盖) */
  --bg: #FAFAF6; --fg: #1A1A1A; --muted: #6B6B6B;
  --primary: #1A1A1A; --primary_dim: #0A0A0A;
  --surface: #FFFFFF; --surface_alt: #F5F5F4;
  --border: #E5E5E5; --border_strong: #1A1A1A;
  --accent: #DC2626;
  --shadow: 0 1px 0 rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.08);
  --shadow_hover: 0 2px 0 rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.12);
}
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
h1, h2, h3, h4 { font-family: var(--font-heading); font-weight: 600; line-height: 1.2; letter-spacing: -0.02em; }
.num, .num * { font-family: var(--font-num); font-variant-numeric: tabular-nums; }
.container { max-width: 1120px; margin: 0 auto; padding: 0 32px; }
@media (max-width: 768px) { .container { padding: 0 20px; } }
section.tab { padding: 120px 0 96px; position: relative; z-index: 2; overflow: hidden; border-top: 1px solid #E2E8F0; }
section.tab h2 { font-size: clamp(1.875rem, 3.5vw, 2.5rem); font-weight: 600; margin-bottom: 24px; }
section.tab h3 { font-size: 1.1875rem; font-weight: 600; margin: 40px 0 12px; }
section.tab p { margin-bottom: 16px; }
.fade-up { opacity: 0; transform: translateY(24px); transition: opacity 700ms cubic-bezier(0.16, 1, 0.3, 1), transform 700ms cubic-bezier(0.16, 1, 0.3, 1); }
.fade-up.visible { opacity: 1; transform: translateY(0); }
.watermark { position: absolute; font-family: var(--font-heading); font-size: clamp(10rem, 18vw, 18rem); font-weight: 700; line-height: 0.85; letter-spacing: -0.05em; pointer-events: none; user-select: none; z-index: 0; opacity: 0.04; }
footer { padding: 64px 0 48px; text-align: center; position: relative; z-index: 2; }
footer .label { font-family: var(--font-num); font-size: 0.6875rem; letter-spacing: 0.15em; opacity: 0.7; }
footer .data-source { font-size: 0.75rem; opacity: 0.5; max-width: 600px; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
  .fade-up { opacity: 1; transform: none; }
}


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


def render_v4(data: dict, style: str) -> str:
    """通用 8 套极致渲染 (cs/eng/medicine/law/education/sci/humanities/administration)"""
    if style == "cs":
        css_extra = CS_CSS
    elif style == "humanities":
        css_extra = HUMANITIES_CSS
    elif style == "administration":
        css_extra = ADMINISTRATION_CSS
    elif style == "finance":
        css_extra = FINANCE_CSS
    elif style == "law":
        css_extra = LAW_CSS
    elif style == "education":
        css_extra = EDUCATION_CSS
    elif style in ("sci", "eng"):
        # sci/eng 复用 education 框架 (共享 layout) + 自定义 body bg + hero
        css_extra = EDUCATION_CSS
    elif style == "agri":
        css_extra = AGRI_CSS
    elif style == "arts":
        css_extra = ARTS_CSS
    elif style == "gongan":
        css_extra = GONGAN_CSS
    elif style == "business":
        css_extra = BUSINESS_CSS
    else:
        raise ValueError(f"Unknown v4 style: {style}")

    title = data.get("title", "未命名")
    summary = data.get("summary", "")
    category = data.get("category", "")
    degree = data.get("degree", "")
    duration = data.get("duration_years", 4)
    tags = data.get("tags", [])
    difficulty = data.get("difficulty", "★★★☆☆")
    data_source = data.get("data_source", "人工精编")
    updated_at = data.get("updated_at", "2026-06")
    # hero 扉页金句 (默认是教育学版的「研究怎么学, 而非教什么」)
    # 其他非师范专业在 JSON 里覆盖 hero_quote 即可换成领域金句
    hero_quote = data.get("hero_quote", "研究「怎么学」, 而非「教什么」")
    hero_quote_sig = data.get("hero_quote_sig", "—— Major Explorer 编辑寄言")
    curriculum = data.get("curriculum", {})
    top_schools = _dedup_by_name(data.get("top_schools", []), "name")
    top_companies = data.get("top_companies", [])
    salary = data.get("salary", {})
    directions = data.get("employment_direction", [])
    deep_study = data.get("deep_study", {})
    quotes = _dedup_by_name(data.get("alumni_quotes", []), "current")
    xuanke = data.get("xuanke_req_list", [])

    # ── 课程 ──
    def render_courses(block_name: str, courses: list) -> str:
        if not courses:
            return ""
        items = []
        for c in courses:
            name = c.get("name", "")
            credit = c.get("credit", "")
            items.append(f'          <div class="course"><span class="course-name">{name}</span><span class="course-credit">{credit} 学分</span></div>')
        return f'        <div class="curriculum-block fade-up"><div class="curriculum-title">{block_name}</div>\n' + "\n".join(items) + "\n        </div>"

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
    curriculum_html = "\n".join([render_courses(name, courses) for name, courses in course_sections]) if course_sections else '<p style="color:#94A3B8">课程数据待补充</p>'

    # ── 院校 (招 #8) ──
    schools_html = "\n".join(
        f'''        <div class="bento-item fade-up" data-delay="{(i % 4) * 80}">
          <div class="bento-monogram">{get_first_char(s.get("name", ""))}</div>
          <span class="bento-rank">{s.get("rank", "")}</span>
          <div class="bento-name">{soft_break_name(s.get("name", ""))}</div>
          <div class="bento-tag">{s.get("tag", "")}</div>
        </div>'''
        for i, s in enumerate(top_schools)
    ) if top_schools else '<div style="grid-column: 1/-1; padding: 24px;">院校数据待补充</div>'

    # ── 公司 ──
    def render_sparkline(values: list) -> str:
        if not values or len(values) < 3:
            return ""
        max_v = max(values) or 1
        bars = "\n".join(
            f'            <div class="sparkline-bar" style="height:{(v/max_v)*100}%"></div>'
            for v in values
        )
        return f'          <div class="sparkline">\n{bars}\n          </div>\n          <div class="sparkline-label">近 5 年招聘量趋势</div>'

    companies_html = "\n".join(
        f'''        <div class="company fade-up" data-delay="{(i % 4) * 80}">
          <div class="company-head">
            <div class="company-monogram">{get_first_char(co.get("name", ""))}</div>
            <span class="company-tier tier-{co.get("tier", "B")}">{co.get("tier", "B")}</span>
          </div>
          <div class="company-name">{soft_break_name(co.get("name", ""))}</div>
          <div class="company-meta">{co.get("headcount", "")} · 校招 {co.get("salary", "")}</div>
{render_sparkline(co.get("sparkline", []))}
        </div>'''
        for i, co in enumerate(top_companies)
    ) if top_companies else '<p>公司数据待补充</p>'

    # ── 薪资 (招 #3 数字滚动) ──
    salary_rows = []
    for stage, vals in salary.items():
        p25, p50, p75 = vals.get("p25", 0), vals.get("p50", 0), vals.get("p75", 0)
        yoy = vals.get("yoy", 0)
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
          <td class="num"><span class="approx">≈</span><span data-count="{p25}">0</span> 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p25/max_v*100}%"></span></span>{yoy_html}</td>
          <td class="num"><span class="approx">≈</span><span data-count="{p50}">0</span> 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p50/max_v*100}%"></span></span></td>
          <td class="num"><span class="approx">≈</span><span data-count="{p75}">0</span> 万<span class="salary-bar"><span class="salary-bar-fill" style="width:{p75/max_v*100}%"></span></span></td>
        </tr>'''
        )
    salary_html = "\n".join(salary_rows) if salary_rows else '<tr><td colspan="4">薪资数据待补充</td></tr>'

    direction_html = "\n".join(
        f'''        <div class="direction">
          <div class="direction-name">{d.get("name", "")}</div>
          <div class="direction-bar"><div class="direction-bar-fill" style="width:{d.get("pct", 0)}%"></div></div>
          <div class="direction-pct">{d.get("pct", 0)}%</div>
        </div>'''
        for d in directions
    ) if directions else '<p>就业方向待补充</p>'

    path_html = "\n".join(
        f'''        <div class="path-card fade-up" data-delay="{(i % 4) * 80}">
          <div class="path-pct">{v}%</div>
          <div class="path-name">{k}</div>
        </div>'''
        for i, (k, v) in enumerate(deep_study.items())
    ) if deep_study else '<p>深造数据待补充</p>'

    quotes_html = "\n".join(
        f'''        <div class="quote fade-up" data-delay="{(i % 4) * 80}" {"data-cite=" + repr(q.get("citation", "")) if q.get("citation") else ""}>
          <div class="quote-head">
            <div class="quote-avatar">{get_first_char(q.get("current", "?"))}</div>
            <div class="quote-byline">
              <strong>{q.get("current", "")}</strong>
              <span class="quote-source">{q.get("year", "")} · {q.get("source", "")}</span>
            </div>
          </div>
          <p class="quote-text">{q.get("quote", "")}</p>
        </div>'''
        for i, q in enumerate(quotes)
    ) if quotes else '<p>校友观点待补充</p>'

    xuanke_html = "\n".join(
        f'''        <div class="xuanke">
          <div class="xuanke-name">{x.get("name", "")}</div>
          <div class="xuanke-bar"><div class="xuanke-bar-fill" style="width:{x.get("pct", 0)}%"></div></div>
          <div class="xuanke-pct">{x.get("pct", 0)}%</div>
        </div>'''
        for x in xuanke
    ) if xuanke else '<p>选科数据待补充</p>'

    # ── HERO 各套专属 ──
    if style == "cs":
        # 终端面板 + ASCII art
        hero_html = f'''
<header class="hero">
  <div class="container">
    <div class="hero-grid">
      <div class="terminal-panel">
        <div class="terminal-header">
          <span class="terminal-dot r"></span>
          <span class="terminal-dot y"></span>
          <span class="terminal-dot g"></span>
          <span class="terminal-title">~/major/computer-science.md</span>
          <span class="terminal-status">在线</span>
        </div>
        <div class="terminal-body">
          <div class="terminal-line"><span class="terminal-prompt">$</span> <span class="terminal-cmd">cat /major/{data.get("slug", "computer-science")}.md</span></div>
          <pre class="terminal-ascii">   _____                  _       ____                       _
  / ____|                | |     / ____|                     | |
 | |     _ __ ___  _ __ | | __ | (___  _ __   ___ _ __   ___| |__
 | |    | '__/ _ \| '_ \| |/ /  \___ \| '_ \ / _ \ '_ \ / __| '_ \\
 | |____| | | (_) | | | |   <   ____) | |_) |  __/ | | | (__| | | |
  \_____|_|  \___/|_| |_|_|\_\ |_____/| .__/ \___|_| |_|\___|_| |_|
                                       |_|
</pre>
          <div class="terminal-line"><span class="terminal-comment"># {summary[:120]}</span></div>
          <div class="terminal-line"><span class="terminal-prompt">$</span> <span class="terminal-cmd">echo "{tags[0] if tags else '热门'} · 4 年制 · {degree}"</span></div>
          <div class="terminal-line terminal-output">{tags[0] if tags else ''} · 4 年 · {degree} · 按 Tab 浏览</div>
          <div class="terminal-line"><span class="terminal-prompt">$</span> <span class="terminal-cmd">_</span><span class="typed-cursor">█</span></div>
        </div>
      </div>
      <div class="hero-side">
        <div class="hero-decor">cat /major/{data.get("slug", "computer-science")}.md</div>
        <h1>{title}<span class="typed">_</span></h1>
        <p class="hero-tagline">// {summary[:100]}</p>
        <div class="hero-tags">
          {''.join(f'<span class="tag primary">[{t}]</span>' for t in tags[:3])}
          {''.join(f'<span class="tag">{t}</span>' for t in tags[3:])}
        </div>
        <div class="hero-stats">
          <div class="stat"><div class="stat-label">类型</div><div class="stat-value">{category}</div></div>
          <div class="stat"><div class="stat-label">学制</div><div class="stat-value">{duration}Y · {degree}</div></div>
          <div class="stat"><div class="stat-label">难度</div><div class="stat-value">{difficulty}</div></div>
          <div class="stat"><div class="stat-label">更新</div><div class="stat-value">{updated_at}</div></div>
        </div>
      </div>
    </div>
  </div>
</header>'''
    elif style == "finance":
        # editorial letterhead
        hero_html = f'''
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
    elif style == "law":
        # 法律卷宗
        hero_html = f'''
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
    elif style == "humanities":
        # 翻开的线装书 — 左页扉页式 + 右页校勘式
        hero_html = f'''
<header class="hero">
  <div class="hu-topline">高 考 选 专 业 · 精 品 卷 · 第 四 册</div>
  <div class="container">
    <div class="book-shell">
      <div class="book-page left">
        <div class="hu-seal">印</div>
        <div class="hu-folio">folio ii</div>
        <div class="hu-watermark">{title[:1] if title else "学"}</div>
        <h1 class="hu-title">{title}</h1>
        <div class="hu-subtitle">History &amp; Humanities · 2026</div>
        <div class="hu-quote">
          「一時代之學術, 必有其新材料與新問題。<br/>
          取用此材料以研求問題, 則為此時代學術之新潮流。」
          <div class="hu-quote-sig">— 陳寅恪 · 1930</div>
        </div>
      </div>
      <div class="book-spine">
        <span class="book-stitch"></span><span class="book-stitch"></span><span class="book-stitch"></span>
        <span class="book-stitch"></span><span class="book-stitch"></span><span class="book-stitch"></span>
        <span class="book-stitch"></span><span class="book-stitch"></span><span class="book-stitch"></span>
      </div>
      <div class="book-page right">
        <div class="hu-folio-right">folio iii</div>
        <div class="hero-stats">
          <div class="hu-stat"><span class="hu-stat-seal">正</span><div class="stat-label">学 科 门 类</div><div class="stat-value">{category}</div></div>
          <div class="hu-stat"><div class="stat-label">学 制 · 学 位</div><div class="stat-value">{duration}Y · {degree}</div></div>
          <div class="hu-stat"><div class="stat-label">难 度 评 定</div><div class="stat-value">{difficulty}</div></div>
          <div class="hu-stat"><div class="stat-label">版 本 修 订</div><div class="stat-value">{updated_at}</div></div>
        </div>
        <ul class="hu-toc">
          <li><span class="hu-toc-cnum">壹</span><span class="hu-toc-name">速览 · 专业全貌</span><span class="hu-toc-pg">p. 02</span></li>
          <li><span class="hu-toc-cnum">貳</span><span class="hu-toc-name">课程 · 核心知识</span><span class="hu-toc-pg">p. 14</span></li>
          <li><span class="hu-toc-cnum">參</span><span class="hu-toc-name">院校 · 学科评估</span><span class="hu-toc-pg">p. 28</span></li>
          <li><span class="hu-toc-cnum">肆</span><span class="hu-toc-name">就业 · 前辈去向</span><span class="hu-toc-pg">p. 42</span></li>
        </ul>
        <div class="hu-foot">2026 EDITION · SERIES IV / VOL. 01 · 嶽麓書院 藏版</div>
      </div>
    </div>
  </div>
</header>'''

    elif style == "administration":
        # 公文式抬头 (中性 / 非官方 — Major Explorer 编辑部出品, 避免模仿真实政府公文)
        hero_html = f'''
<header class="hero">
  <div class="gov-red-header">
    <span class="doc-num">MAJOR · 〔2026〕第 {tags[0] if tags else "001"} 号</span>
    <strong>Major Explorer 编辑部</strong>
    <span class="doc-num">专题资料 · 编辑部内阅</span>
  </div>
  <div class="gov-redline"></div>
  <div class="container" style="padding: 0;">
    <div class="gov-paper">
      <div class="gov-stamp">
        <span class="gov-stamp-text">升学<br/>研究组</span>
      </div>
      <div class="gov-seal-strip">归档 · 内部资料</div>
      <div class="gov-doc-title">专业介绍</div>
      <div class="gov-doc-no">专题号 ME〔2026〕第 {tags[0] if tags else "001"} 号</div>
      <div class="gov-doc-line"></div>
      <h1 class="gov-h1">{title}</h1>
      <p class="gov-tagline">{summary[:120]}</p>
      <div class="gov-tags">
        {"".join(f'<span class="gov-tag primary">{t}</span>' for t in tags[:3])}
        {"".join(f'<span class="gov-tag">{t}</span>' for t in tags[3:])}
      </div>
      <div class="gov-stats">
        <div class="stat" data-num="01"><div class="stat-label">学 科 门 类</div><div class="stat-value">{category}</div></div>
        <div class="stat" data-num="02"><div class="stat-label">学 制 · 学 位</div><div class="stat-value">{duration}Y · {degree}</div></div>
        <div class="stat" data-num="03"><div class="stat-label">难 度 评 定</div><div class="stat-value">{difficulty}</div></div>
        <div class="stat" data-num="04"><div class="stat-label">编 纂 修 订</div><div class="stat-value">{updated_at}</div></div>
      </div>
      <div class="gov-foot">
        <span>编纂: Major Explorer 编辑部 · 升学研究组</span>
        <span>成文日期: {updated_at}</span>
        <span>份号: 0026-ME-{data.get("slug", "doc")[:6].upper()}</span>
      </div>
    </div>
  </div>
</header>'''
    elif style == "education":
        # 教科书扉页
        hero_html = f'''
<header class="hero">
  <div class="book-frame">
    <div class="book-spine">
      <div class="book-spine-text">
        <span>{title}</span>
        <span class="yr">MMXXVI</span>
      </div>
    </div>
    <!-- 左页 verso: 章节寄言 -->
    <div class="book-verso">
      <div>
        <div class="chapter-marker">第一章 · 专业全貌</div>
        <p class="book-quote">{hero_quote}</p>
        <div class="book-quote-sig">{hero_quote_sig}</div>
      </div>
      <div class="verso-footer">
        <div class="book-publisher">
          <strong>Major Explorer</strong><br/>
          高考志愿出版社 · 2026 卷<br/>
          数据更新于 {updated_at}
        </div>
        <div class="book-page-num">i</div>
      </div>
    </div>
    <!-- 右页 recto: 标题 + 元信息 -->
    <div class="book-recto">
      <div class="recto-corner">CHAPTER I · 专业全貌</div>
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
        <div class="stat"><div class="stat-label">版本</div><div class="stat-value">{updated_at}</div></div>
      </div>
    </div>
  </div>
</header>'''
    elif style == "sci":
        # 学术期刊 hero — 顶部刊头 + 大字标题 + 摘要框
        hero_html = f'''
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
    elif style == "eng":
        # 工程图纸 hero — 顶部标题栏 + 零件图 spec card + datasheet
        slug = data.get("slug", "ME")
        hero_html = f'''
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
    elif style == "agri":
        # 林奈式植物图鉴 + 标本夹作 frame + 内容居中
        hero_html = f'''
<header class="hero">
  <!-- 装饰层 (absolute, 不影响内容布局) -->
  <div class="desk"></div>
  <div class="sunbeam"></div>
  <div class="corner-mark cm-tl"></div>
  <div class="corner-mark cm-tr"></div>
  <div class="corner-mark cm-bl"></div>
  <div class="corner-mark cm-br"></div>
  <div class="top-mark">高考选专业 · 精品卷 第五册 · 華北農學會藏版</div>
  <div class="wheat">
    <svg viewBox="0 0 50 160" xmlns="http://www.w3.org/2000/svg">
      <path d="M 25 160 Q 26 110 25 60" stroke="#C8A26E" stroke-width="1" fill="none"/>
      <g fill="#E6B422" stroke="#B8902A" stroke-width="0.3">
        <ellipse cx="20" cy="75" rx="3.5" ry="8" transform="rotate(-15 20 75)"/>
        <ellipse cx="30" cy="88" rx="3.5" ry="8" transform="rotate(15 30 88)"/>
        <ellipse cx="19" cy="105" rx="4" ry="9" transform="rotate(-15 19 105)"/>
        <ellipse cx="31" cy="118" rx="4" ry="9" transform="rotate(15 31 118)"/>
        <ellipse cx="18" cy="135" rx="4.5" ry="10" transform="rotate(-15 18 135)"/>
      </g>
      <g stroke="#B8902A" stroke-width="0.4" fill="none" opacity="0.8">
        <line x1="25" y1="60" x2="20" y2="22"/><line x1="25" y1="60" x2="25" y2="14"/>
        <line x1="25" y1="60" x2="30" y2="22"/><line x1="25" y1="60" x2="22" y2="28"/>
        <line x1="25" y1="60" x2="28" y2="28"/>
      </g>
    </svg>
  </div>
  <div class="leaf-vein">
    <svg viewBox="0 0 50 160" xmlns="http://www.w3.org/2000/svg">
      <path d="M 25 10 L 25 150" stroke="#6B8E23" stroke-width="0.7" fill="none" opacity="0.6"/>
      <g stroke="#9CB87A" stroke-width="0.4" fill="none" opacity="0.6">
        <path d="M 25 28 Q 16 32 10 40"/><path d="M 25 28 Q 34 32 40 40"/>
        <path d="M 25 55 Q 14 62 8 75"/><path d="M 25 55 Q 36 62 42 75"/>
        <path d="M 25 85 Q 14 95 8 110"/><path d="M 25 85 Q 36 95 42 110"/>
        <path d="M 25 115 Q 16 125 12 140"/><path d="M 25 115 Q 34 125 38 140"/>
      </g>
    </svg>
  </div>
  <div class="chloro-panel">
    <div class="cp-title">光合色素</div>
    <div class="chloro-line"><span class="ch">叶绿素 a</span><span class="note">蓝绿</span></div>
    <div class="chloro-line"><span class="ch">叶绿素 b</span><span class="note">黄绿</span></div>
    <div class="chloro-line"><span class="ch">胡萝卜素</span><span class="note">橙</span></div>
    <div class="chloro-line"><span class="ch">叶黄素</span><span class="note">黄</span></div>
    <div class="chloro-line"><span class="ch">花青素</span><span class="note">红紫</span></div>
  </div>
  <!-- 朱砂方印 -->
  <div class="hu-stat-seal"><span class="seal">农</span></div>
  <div class="bookmark"></div>
  <!-- 主内容 (居中, viewport 1440×900 可见) -->
  <div class="hero-content">
    <div class="hero-chapter">{category} · 第一章</div>
    <h1 class="hero-title">
      <span class="title-cn">{title}</span>
      <span class="title-en">Agri-Botany <span class="ampersand">&amp;</span> 林奈式分类</span>
    </h1>
    <p class="hero-tagline">{summary[:160]}</p>
    <div class="hu-stats-grid">
      <div class="hu-stat"><span class="hu-stat-label">学科</span><span class="hu-stat-value">{category}</span></div>
      <div class="hu-stat"><span class="hu-stat-label">学制</span><span class="hu-stat-value">{duration} 年 · {degree}</span></div>
      <div class="hu-stat"><span class="hu-stat-label">难度</span><span class="hu-stat-value">{difficulty}</span></div>
      <div class="hu-stat"><span class="hu-stat-label">更新</span><span class="hu-stat-value">{updated_at}</span></div>
    </div>
    <div class="hero-tags">
      {"".join(f'<span class="hu-tag">{t}</span>' for t in tags[:6])}
    </div>
  </div>
</header>'''
    elif style == "arts":
        # 美术馆白盒 + 画框 + 展签 + 朱红印章 + 金属铭牌
        hero_html = f'''
<header class="hero">
  <div class="museum-wall"></div>
  <div class="museum-floor"></div>
  <div class="museum-light"></div>
  <!-- 顶部 美术馆 logo -->
  <div class="museum-logo">
    <div class="museum-logo-text">MUSEUM OF MAJOR</div>
    <div class="museum-logo-sub">Major Explorer Collection · Est. 2026</div>
  </div>
  <!-- 朱红印章 (右) -->
  <div class="cinnabar-seal">MAJOR<br/>EXPLORER</div>
  <!-- 金属铭牌 (左) -->
  <div class="brass-plate">Section I · Studies</div>
  <!-- 装饰色卡 (左下, 替代颜料管) -->
  <div class="color-swatches">
    <div class="color-swatch swatch-1"><span class="color-swatch-label">黄</span></div>
    <div class="color-swatch swatch-2"><span class="color-swatch-label">朱</span></div>
    <div class="color-swatch swatch-3"><span class="color-swatch-label">青</span></div>
    <div class="color-swatch swatch-4"><span class="color-swatch-label">墨</span></div>
    <div class="color-swatch swatch-5"><span class="color-swatch-label">赭</span></div>
  </div>
  <!-- 画框 + 主内容 -->
  <div class="gallery-frame-wrap">
    <div class="frame-corner-bl"></div>
    <div class="frame-corner-br"></div>
    <div class="gallery-frame-inner">
      <div class="hero-content">
        <div class="hero-chapter">Museum of Studies</div>
        <h1 class="hero-title">
          <span class="title-en-small">Museum of</span>
          <span class="title-cn">{title}</span>
          <span class="title-en">HISTORY · THEORY · CURATORSHIP</span>
        </h1>
        <p class="hero-tagline">{summary[:160]}</p>
        <div class="hu-stats-grid">
          <div class="hu-stat"><span class="hu-stat-label">学科</span><span class="hu-stat-value">{category}</span></div>
          <div class="hu-stat"><span class="hu-stat-label">学制</span><span class="hu-stat-value">{duration} 年 · {degree}</span></div>
          <div class="hu-stat"><span class="hu-stat-label">难度</span><span class="hu-stat-value">{difficulty}</span></div>
          <div class="hu-stat"><span class="hu-stat-label">更新</span><span class="hu-stat-value">{updated_at}</span></div>
        </div>
        <div class="hero-tags">
          {"".join(f'<span class="hu-tag">{t}</span>' for t in tags[:5])}
        </div>
      </div>
    </div>
  </div>
  <!-- 展签 (底部) -->
  <div class="gallery-label">
    <div class="label-eyebrow">Collection · F.001</div>
    <div class="label-title">{title}</div>
    <div class="label-meta">Major Explorer Editorial · 2026 春季</div>
  </div>
</header>'''
    elif style == "gongan":
        # 公安学类 · 国际司法范式: 盾+十字剑+橄榄枝, 警蓝+国徽金+朱红
        # 6 核心元素: 金线带 / 主徽 / hu-tag / 标题+stats / 引言 / 角标
        hero_html = f'''
<header class="hero gg-hero">
  <div class="gg-bg-noise"></div>
  <div class="gg-gold-band"></div>
  <!-- 中央主徽: 盾+十字剑+橄榄枝 (背景氛围, 半透明) -->
  <div class="gg-main-emblem" aria-hidden="true">
    <svg viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="ggGoldG" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#E5C158"/><stop offset="50%" stop-color="#D4AF37"/><stop offset="100%" stop-color="#B8902A"/>
        </linearGradient>
        <linearGradient id="ggShieldG" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#1E3A5F"/><stop offset="100%" stop-color="#0F1F33"/>
        </linearGradient>
      </defs>
      <path d="M 120 24 L 200 44 L 200 120 Q 200 168 120 210 Q 40 168 40 120 L 40 44 Z" fill="url(#ggShieldG)" stroke="url(#ggGoldG)" stroke-width="2.5"/>
      <circle cx="120" cy="64" r="10" fill="none" stroke="url(#ggGoldG)" stroke-width="1.5"/>
      <circle cx="120" cy="64" r="5" fill="url(#ggGoldG)"/>
      <g fill="url(#ggGoldG)">
        <rect x="117" y="74" width="6" height="14"/>
        <rect x="98" y="88" width="44" height="5"/>
        <rect x="96" y="86" width="4" height="9"/>
        <rect x="140" y="86" width="4" height="9"/>
        <polygon points="116,93 124,93 122,170 118,170"/>
        <polygon points="118,170 122,170 120,182"/>
      </g>
      <g stroke="url(#ggGoldG)" stroke-width="0.8" fill="url(#ggGoldG)">
        <path d="M 60 130 Q 80 154 110 170" fill="none"/>
        <ellipse cx="68" cy="138" rx="2.5" ry="5" transform="rotate(-30 68 138)"/>
        <ellipse cx="78" cy="146" rx="2.5" ry="5" transform="rotate(-20 78 146)"/>
        <ellipse cx="88" cy="156" rx="2.5" ry="5" transform="rotate(-10 88 156)"/>
        <ellipse cx="98" cy="164" rx="2.5" ry="5" transform="rotate(-5 98 164)"/>
        <ellipse cx="64" cy="148" rx="2.5" ry="5" transform="rotate(30 64 148)"/>
        <ellipse cx="74" cy="158" rx="2.5" ry="5" transform="rotate(20 74 158)"/>
      </g>
      <g stroke="url(#ggGoldG)" stroke-width="0.8" fill="url(#ggGoldG)">
        <path d="M 180 130 Q 160 154 130 170" fill="none"/>
        <ellipse cx="172" cy="138" rx="2.5" ry="5" transform="rotate(30 172 138)"/>
        <ellipse cx="162" cy="146" rx="2.5" ry="5" transform="rotate(20 162 146)"/>
        <ellipse cx="152" cy="156" rx="2.5" ry="5" transform="rotate(10 152 156)"/>
        <ellipse cx="142" cy="164" rx="2.5" ry="5" transform="rotate(5 142 164)"/>
        <ellipse cx="176" cy="148" rx="2.5" ry="5" transform="rotate(-30 176 148)"/>
        <ellipse cx="166" cy="158" rx="2.5" ry="5" transform="rotate(-20 166 158)"/>
      </g>
    </svg>
  </div>
  <!-- 4 角金线角标 -->
  <div class="gg-corner-mark gg-cm-tl"></div>
  <div class="gg-corner-mark gg-cm-tr"></div>
  <div class="gg-corner-mark gg-cm-bl"></div>
  <div class="gg-corner-mark gg-cm-br"></div>
  <!-- 6 大专业 hu-tag -->
  <div class="gg-hu-tags">
    <div class="gg-hu-tag">公 安 学</div>
    <div class="gg-hu-tag">治 安 学</div>
    <div class="gg-hu-tag">侦 查 学</div>
    <div class="gg-hu-tag">刑事科学技术</div>
    <div class="gg-hu-tag">禁 毒 学</div>
    <div class="gg-hu-tag">公安管理学</div>
  </div>
  <!-- 标题区 -->
  <div class="gg-title-zone">
    <div class="gg-discipline">PUBLIC SECURITY &amp; LAW STUDIES · 030600</div>
    <h1 class="gg-hero-title">公 安 <span class="accent">学</span> 类</h1>
    <div class="gg-title-en">Public Security &amp; Law Studies</div>
    <div class="gg-subtitle">从 部 委 直 属 高 校 到 省 属 警 院 — 公 正 的 守 护 者 通 道</div>
  </div>
  <!-- 4 stats -->
  <div class="gg-stats-row">
    <div class="gg-stat featured">
      <div class="gg-stat-label">Police Acad.</div>
      <div class="gg-stat-label-cn">公 安 院 校</div>
      <div class="gg-stat-value">No.52<span class="unit">所</span></div>
    </div>
    <div class="gg-stat">
      <div class="gg-stat-label">Enrollment</div>
      <div class="gg-stat-label-cn">年 招 生 规 模</div>
      <div class="gg-stat-value">6.8<span class="unit">万</span></div>
    </div>
    <div class="gg-stat">
      <div class="gg-stat-label">Posts</div>
      <div class="gg-stat-label-cn">警 种 岗 位</div>
      <div class="gg-stat-value">200<span class="unit">+</span></div>
    </div>
    <div class="gg-stat">
      <div class="gg-stat-label">Employment</div>
      <div class="gg-stat-label-cn">入 警 率</div>
      <div class="gg-stat-value">98.2<span class="unit">%</span></div>
    </div>
  </div>
  <!-- 引言 -->
  <div class="gg-quote">
    <div class="gg-quote-text">对 党 忠 诚<span class="sep">·</span>服 务 人 民<span class="sep">·</span>执 法 公 正<span class="sep">·</span>纪 律 严 明</div>
    <div class="gg-quote-sig">入 警 誓 词 · OATH OF OFFICE</div>
  </div>
</header>'''
    elif style == "business":
        # 工商管理 · 椭圆董事局 + 玫瑰金 + 胡桃木 + 屏幕深蓝
        # 6 核心元素: 3 屏数据墙 / 椭圆桌 / 8 椅 / 8 名牌 / 标题+引言 / 6 hu-tag + 4 stats
        hero_html = f'''
<header class="hero biz-hero">
  <div class="biz-marble"></div>
  <div class="biz-ceiling-light"></div>
  <div class="biz-grain"></div>
  
  <div class="biz-title-zone">
  <h1 class="biz-title-main">Strategic Management</h1>
    <h2 class="biz-title-main-cn"><span class="biz-title-cn-accent">战略管理</span> · 决策科学</h2>
  <div class="biz-hero-quote">
      "If you don't know where you're going, you might not get there."
      <span class="biz-hero-quote-sig">— Yogi Berra</span>
    </div>
  </div>
  <!-- 6 hu-tag 专业列表 -->
  <div class="biz-hu-tag-row">
    <div class="biz-hu-tag"><span class="biz-hu-tag-num">01</span><span>战略管理</span><span class="biz-hu-tag-en">Strategy</span></div>
    <div class="biz-hu-tag"><span class="biz-hu-tag-num">02</span><span>组织行为</span><span class="biz-hu-tag-en">OB</span></div>
    <div class="biz-hu-tag"><span class="biz-hu-tag-num">03</span><span>人力资源</span><span class="biz-hu-tag-en">HRM</span></div>
    <div class="biz-hu-tag"><span class="biz-hu-tag-num">04</span><span>运营管理</span><span class="biz-hu-tag-en">OPS</span></div>
    <div class="biz-hu-tag"><span class="biz-hu-tag-num">05</span><span>供应链</span><span class="biz-hu-tag-en">SCM</span></div>
    <div class="biz-hu-tag"><span class="biz-hu-tag-num">06</span><span>国际商务</span><span class="biz-hu-tag-en">IB</span></div>
  </div>
  <!-- 4 stats 底部条 -->
  <div class="biz-stats-strip">
    <div class="biz-stat-block">
      <div class="biz-stat-label">Strategy Tools</div>
      <div class="biz-stat-num">42<span class="biz-stat-num-sub">+</span></div>
      <div class="biz-stat-label-cn">主流战略工具 (BCG / Porter / 蓝海)</div>
    </div>
    <div class="biz-stat-block">
      <div class="biz-stat-label">Consulting</div>
      <div class="biz-stat-num">3<span class="biz-stat-num-sub">Tier-1</span></div>
      <div class="biz-stat-label-cn">MBB · 麦肯锡 / BCG / 贝恩</div>
    </div>
    <div class="biz-stat-block">
      <div class="biz-stat-label">F500 Employers</div>
      <div class="biz-stat-num">128<span class="biz-stat-num-sub">家</span></div>
      <div class="biz-stat-label-cn">财富 500 强中国总部招聘</div>
    </div>
    <div class="biz-stat-block">
      <div class="biz-stat-label">Avg. Promotion</div>
      <div class="biz-stat-num">4.2<span class="biz-stat-num-sub">年</span></div>
      <div class="biz-stat-label-cn">管培生 → 中层管理 平均年限</div>
    </div>
  </div>
</header>'''

    body_bg = get_body_bg_css(style)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- inline favicon: 防止 file:// / http 访问时控制台 404 favicon.ico -->
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 16%22><text y=%2214%22 font-size=%2214%22>📘</text></svg>">
<title>{title}专业介绍 2026 高考 | Major Explorer</title>
<meta name="description" content="{summary[:100]}">
<style>
{FONT_URLS[style]}
{get_base_css()}
{BASE_V4_CSS}
{body_bg}
{OVERVIEW_V2_CSS}
{css_extra}
</style>
</head>
<body>
{hero_html}

<section class="tab" id="overview">
  <div class="watermark">01</div>
  <div class="container">
    <div class="section-num">01 / 10 · 速览</div>
    <h2>速览</h2>
    {render_overview_v2(data) if data.get("overview_v2") else f'''<p class="lede drop-cap">{summary}</p>
    {f'<h3>这个专业学什么?</h3><p>{data.get("what_you_learn", "")}</p>' if data.get("what_you_learn") else ''}
    {f'<h3>什么人适合?</h3><p>{data.get("who_fits", "")}</p>' if data.get("who_fits") else ''}
    {f'<h3>避坑指南</h3><p>{data.get("pitfalls", "")}</p>' if data.get("pitfalls") else ''}'''}
  </div>
</section>

<section class="tab" id="curriculum">
  <div class="watermark">02</div>
  <div class="container">
    <div class="section-num">02 / 10 · 课程</div>
    <h2>主要课程</h2>
    <p class="curriculum-lede">{data.get("curriculum_note", "全国通用 4 年制框架, 不同高校在大三/大四有不同方向分流。")}</p>
    <div class="curriculum-grid">
{curriculum_html}
    </div>
  </div>
</section>

<section class="tab" id="schools">
  <div class="watermark">03</div>
  <div class="container">
    <div class="section-num">03 / 10 · 院校</div>
    <h2>院校分布</h2>
    <p class="lede">教育部学科评估第四轮 (2017, 第五轮 2022 部分公开)。A+ = 前 2% 或前 2 所, A = 前 2-10%, A- = 前 10-20%。</p>
    <div class="bento">
{schools_html}
    </div>
  </div>
</section>

<section class="tab" id="companies">
  <div class="watermark">04</div>
  <div class="container">
    <div class="section-num">04 / 10 · 头部雇主</div>
    <h2>头部雇主</h2>
    <p class="lede">S = 顶级, A = 知名, B = 大量招。校招薪资为 2024 秋招主流 offer 中位数。底部 bar = 近 5 年招聘量趋势。</p>
    <div class="company-grid">
{companies_html}
    </div>
  </div>
</section>

<section class="tab" id="salary">
  <div class="watermark">05</div>
  <div class="container">
    <div class="section-num">05 / 10 · 薪资</div>
    <h2>薪资分布</h2>
    <p class="lede">数据源: 麦可思 2024 + 招聘平台 2024 校招采样。单位: 万/年。P25/P50/P75 = 25/50/75 百分位。≈ 表示估算值。↗ = 3 年变化。进入视口时数字滚动。</p>
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
  <div class="watermark">06</div>
  <div class="container">
    <div class="section-num">06 / 10 · 就业方向</div>
    <h2>就业方向</h2>
    <p class="lede">毕业 1-3 年的去向分布, 占比合计 100%。</p>
    <div class="direction-list">
{direction_html}
    </div>
  </div>
</section>

<section class="tab" id="deep-study">
  <div class="watermark">07</div>
  <div class="container">
    <div class="section-num">07 / 10 · 深造路径</div>
    <h2>深造路径</h2>
    <div class="path-grid">
{path_html}
    </div>
  </div>
</section>

<section class="tab" id="quotes">
  <div class="watermark">08</div>
  <div class="container">
    <div class="section-num">08 / 10 · 学长学姐说</div>
    <h2>学长学姐说</h2>
    <p class="lede">真实在校生/毕业生观点, 有夸有劝退, 自己判断。</p>
    <div class="quotes">
{quotes_html}
    </div>
  </div>
</section>

<section class="tab" id="xuanke">
  <div class="watermark">09</div>
  <div class="container">
    <div class="section-num">09 / 10 · 选科要求</div>
    <h2>选科要求 (新高考 3+1+2)</h2>
    <p class="lede">基于 2024 年全国开设此专业院校的招生选科要求统计。覆盖率越高, 你的选科组合能报的院校越多。</p>
    <div class="xuanke-list">
{xuanke_html}
    </div>
  </div>
</section>

<section class="tab" id="cta">
  <div class="watermark">10</div>
  <div class="container">
    <div class="section-num">10 / 10 · 关联志愿</div>
    <h2>关联志愿</h2>
    <div class="cta-block">
      <h3>基于你的位次, 推荐这些校 + 组</h3>
      <p>上面院校列表已内置, 输入位次和分数, 立刻出志愿表 (冲 / 稳 / 保 比例 25/50/25)。</p>
      <form class="cta-form" onsubmit="event.preventDefault(); alert('功能开发中, 请关注后续更新');">
        <input type="number" class="cta-input" placeholder="位次 (如 1234)" required>
        <input type="number" class="cta-input" placeholder="分数 (如 620)" required>
        <button type="submit" class="cta-button">推荐志愿 →</button>
      </form>
      <p class="cta-note">⚠ 本页所有数据截至 {updated_at}, 仅供高考志愿参考, 不构成最终决策建议。</p>
    </div>
  </div>
</section>

<footer>
  <div class="container">
    <div class="label">Major Explorer · 2026 高考专业指南</div>
    <div class="data-source">数据源: {data_source}</div>
  </div>
</footer>

{COUNT_UP_JS}
</body>
</html>"""


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

