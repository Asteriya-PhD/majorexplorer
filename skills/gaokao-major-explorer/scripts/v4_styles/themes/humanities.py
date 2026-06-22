"""
v4_styles/themes/humanities.py — humanities 主题 CSS + hero 渲染
"""

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
.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: #FBF6E9; border: 1px solid #C5B89A; border-radius: 4px; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #8B5A2B; transform: translateY(-2px); }
.path-pct { font-family: 'Noto Serif SC', serif; font-size: 2.5rem; font-weight: 700; color: #1F140A; margin-bottom: 4px; line-height: 1; }
.path-name { font-family: 'Cormorant Garamond', serif; font-style: italic; color: #6B5D3F; font-size: 0.875rem; margin-top: 8px; }
.path-name { word-break: break-word; line-height: 1.4; hyphens: auto; }
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

/* ── humanities (线装书) mobile patch — book-shell 1fr-36px-1fr + rotate 在 390px 严重溢出 ──
   策略: 关闭翻开效果, 单页显示, 隐藏 spine + left page, 取消 rotate */
@media (max-width: 480px) {
  .book-shell { grid-template-columns: 1fr !important; transform: none !important; }
  .book-page { aspect-ratio: auto !important; padding: 28px 22px !important; }
  .book-page.left { display: none !important; }
  .book-spine { display: none !important; }
  .book-page.right { border-radius: 4px !important; }
  /* 大背景 01 数字 与 01/10·速览 label 重叠 — 弱化背景数字 */
  .book-page-num { opacity: 0.15 !important; font-size: 6rem !important; }
}
"""

def render_hero_humanities(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    return f'''
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
