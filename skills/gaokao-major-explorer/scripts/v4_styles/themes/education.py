"""
v4_styles/themes/education.py — education 主题 CSS + hero 渲染
"""

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

/* ── eng (工程图纸) mobile patch — 顶部 DWG 三列 docket 在 390px 严重拥挤 ──
   inline style 用 grid-template-columns: auto 1fr auto; 通过属性选择器降到单列堆叠 */
@media (max-width: 480px) {
  header.hero > div[style*="grid-template-columns: auto 1fr auto"] {
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 6px !important;
    padding: 10px 14px !important;
  }
  header.hero > div[style*="grid-template-columns: auto 1fr auto"] > span {
    border: none !important;
    padding: 0 !important;
    font-size: 0.65rem !important;
    text-align: left !important;
  }
  /* sci 同主题 docket meta (顶部 4-cell 杂志页眉) — 在 480px 已经堆叠为 2-row, 字体保持 */
}
"""

def render_hero_education(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    return f'''
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
