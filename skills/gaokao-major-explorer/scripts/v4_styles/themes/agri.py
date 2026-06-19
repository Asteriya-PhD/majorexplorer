"""
v4_styles/themes/agri.py — agri 主题 CSS + hero 渲染
"""

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
.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
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
.curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
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

/* ── agri (林奈植物图鉴) mobile patch — chloro-panel/wheat/top-mark 重叠 园艺 大字 ──
   策略: 隐藏装饰元素, 让 hero 主体 (标题+stats+tags) 干净显示 */
@media (max-width: 480px) {
  .chloro-panel { display: none !important; }
  .wheat { display: none !important; }
  .top-mark { font-size: 0.55rem !important; padding: 4px 8px !important; }
  .corner-mark { width: 14px !important; height: 14px !important; }
  .hu-stats-grid { grid-template-columns: repeat(2, 1fr) !important; gap: 12px !important; padding: 14px 0 !important; }
  /* 标题区上下间距收紧 */
  .title-en { font-size: 1.1rem !important; margin-top: 6px !important; }
}
"""

def render_hero_agri(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    return f'''
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
