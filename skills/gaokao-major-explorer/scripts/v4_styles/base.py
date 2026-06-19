"""
v4_styles/base.py — 共享基础 (FONT_URLS, BASE_V4_CSS, get_base_css, COUNT_UP_JS, helpers)

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
:root {
  /* 响应式 token (Day 1 responsive overhaul 2026-06-19) */
  --bp-sm: 480px; --bp-md: 768px; --bp-lg: 1024px; --bp-xl: 1280px;
  --container-max: clamp(1024px, 92vw, 1280px);
  --container-px: clamp(20px, 4vw, 40px);
  --section-py: clamp(60px, 8vw, 120px);
  --section-py-bottom: clamp(48px, 6vw, 96px);
  --watermark-size: clamp(8rem, 12vw, 14rem);
  --hero-min-h: clamp(480px, 70vh, 720px);
}
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
.container { max-width: var(--container-max); margin: 0 auto; padding: 0 var(--container-px); position: relative; z-index: 2; }
/* 旧 max-width:1200px / padding:0 40px / 768px padding override 全部由 clamp 取代 */

.fade-up { opacity: 0; transform: translateY(24px); transition: opacity 700ms cubic-bezier(0.16, 1, 0.3, 1), transform 700ms cubic-bezier(0.16, 1, 0.3, 1); }
.fade-up.visible { opacity: 1; transform: translateY(0); }

section.tab { padding: var(--section-py) 0 var(--section-py-bottom); position: relative; z-index: 2; overflow: hidden; border-top: 1px solid #E2E8F0; }
section.tab:first-of-type { border-top: none; }
section.tab:last-of-type { border-bottom: none; }
.section-num { font-family: var(--font-num); font-size: 0.75rem; font-weight: 600; letter-spacing: 0.2em; margin-bottom: 12px; text-transform: uppercase; position: relative; z-index: 1; }
section.tab h2 { font-size: clamp(1.875rem, 3.5vw, 2.5rem); font-weight: 600; margin-bottom: 24px; position: relative; z-index: 1; }
section.tab h3 { font-size: 1.1875rem; font-weight: 600; margin: 40px 0 12px; }
section.tab p { margin-bottom: 16px; position: relative; z-index: 1; }
section.tab p.lede { font-size: 1.0625rem; line-height: 1.75; max-width: 720px; margin-bottom: 32px; position: relative; z-index: 1; }

.watermark { position: absolute; top: 40px; right: -20px; font-family: var(--font-heading); font-size: var(--watermark-size); font-weight: 700; line-height: 0.85; letter-spacing: -0.05em; pointer-events: none; user-select: none; z-index: 0; }

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

/* ============================================================
   Mobile patches (≤480px) — Day 1 responsive overhaul 2026-06-19
   留 overflow/tap-target/hero overflow 实用 fix,
   grid !important 由主题流体 auto-fit 取代, container padding 由 clamp 取代
   ============================================================ */
@media (max-width: 480px) {
  /* hero-stats: 2x2 cell 长内容 (学科 / 学制·学位 等) overflow 通病 */
  .hero-stats { gap: 0 !important; }
  .hero-stats .stat,
  .hero-stats > .stat { padding: 12px 12px !important; min-width: 0 !important; overflow: hidden !important; }
  .hero-stats .stat-value { font-size: 0.9375rem !important; line-height: 1.3 !important; word-break: break-word !important; overflow-wrap: anywhere !important; white-space: normal !important; }
  .hero-stats .stat-label { font-size: 0.5625rem !important; letter-spacing: 0.08em !important; }

  /* hero 大字: 各主题 clamp 在 390px 仍偏大, 强压 */
  .hero h1.display,
  .hero h1 { font-size: clamp(1.9rem, 8vw, 2.6rem) !important; line-height: 1.1 !important; word-break: break-all !important; }
  .hero-tagline { font-size: 0.95rem !important; line-height: 1.6 !important; }

  /* tag chip tap-target ≥ 32px (chip 太大会丑) */
  .tag { min-height: 32px; display: inline-flex; align-items: center; padding-top: 6px !important; padding-bottom: 6px !important; }

  /* CTA / link button tap-target ≥ 44px (WCAG AAA) */
  .cta-button,
  .cta-form button,
  button.cta-button,
  a.cta-button { min-height: 44px !important; padding-top: 12px !important; padding-bottom: 12px !important; }

  /* salary-table 列字号缩 */
  .salary-table { font-size: 0.8125rem !important; }
  .salary-table th, .salary-table td { padding: 8px 10px !important; }

  /* 装饰元素弱化 */
  .ecg-line { opacity: 0.3 !important; }
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
# BASE_V4_CSS: 8 招底层 (v4 渲染统一注入, 解决新主题 CSS 不继承问题)
# ──────────────────────────────────────────────────────────
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
/* 旧 .container { max-width: 1120px; padding: 0 32px } + 768px override 已由 get_base_css() 的 clamp 版本接管, 这里删除以避免 cascade 冲突 */
section.tab { padding: var(--section-py) 0 var(--section-py-bottom); position: relative; z-index: 2; overflow: hidden; border-top: 1px solid #E2E8F0; }
section.tab h2 { font-size: clamp(1.875rem, 3.5vw, 2.5rem); font-weight: 600; margin-bottom: 24px; }
section.tab h3 { font-size: 1.1875rem; font-weight: 600; margin: 40px 0 12px; }
section.tab p { margin-bottom: 16px; }
.fade-up { opacity: 0; transform: translateY(24px); transition: opacity 700ms cubic-bezier(0.16, 1, 0.3, 1), transform 700ms cubic-bezier(0.16, 1, 0.3, 1); }
.fade-up.visible { opacity: 1; transform: translateY(0); }
.watermark { position: absolute; font-family: var(--font-heading); font-size: var(--watermark-size); font-weight: 700; line-height: 0.85; letter-spacing: -0.05em; pointer-events: none; user-select: none; z-index: 0; opacity: 0.04; }
footer { padding: 64px 0 48px; text-align: center; position: relative; z-index: 2; }
footer .label { font-family: var(--font-num); font-size: 0.6875rem; letter-spacing: 0.15em; opacity: 0.7; }
footer .data-source { font-size: 0.75rem; opacity: 0.5; max-width: 600px; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
  .fade-up { opacity: 1; transform: none; }
}


"""
