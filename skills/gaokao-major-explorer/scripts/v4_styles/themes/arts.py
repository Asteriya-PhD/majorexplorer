"""
v4_styles/themes/arts.py — arts 主题 CSS + hero 渲染
"""

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
}
"""

def render_hero_arts(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    return f'''
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
