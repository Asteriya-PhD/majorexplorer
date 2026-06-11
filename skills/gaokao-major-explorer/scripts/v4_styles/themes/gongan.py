"""
v4_styles/themes/gongan.py — gongan 主题 CSS + hero 渲染
"""

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

def render_hero_gongan(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    return f'''
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
