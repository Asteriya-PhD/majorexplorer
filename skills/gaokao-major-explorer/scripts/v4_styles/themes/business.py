"""
v4_styles/themes/business.py — business 主题 CSS + hero 渲染
"""

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
/* BUSINESS font: preconnect 在 head, @import 在 FONT_URLS['business'] (此处冗余已移除) */
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
.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: #FFFFFF; border: 1px solid #E5DCC8; border-radius: 4px; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #5C6770; transform: translateY(-2px); }
.path-pct { font-family: var(--font-heading); font-size: 2.5rem; font-weight: 700; color: #3E2A1F; margin-bottom: 4px; line-height: 1; }
.path-name { font-family: var(--font-heading); color: #5C6770; font-size: 0.875rem; margin-top: 8px; }
.path-name { word-break: break-word; line-height: 1.4; hyphens: auto; }
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
.curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
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
.biz-hero + section.tab .path-grid, .biz-hero ~ section.tab .path-grid { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
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

def render_hero_business(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    return f'''
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
