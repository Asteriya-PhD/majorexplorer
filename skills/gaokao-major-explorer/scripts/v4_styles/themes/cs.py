"""
v4_styles/themes/cs.py — cs 主题 CSS + hero 渲染
"""

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

.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: rgba(11, 17, 32, 0.6); border: 1px solid #1F2937; border-radius: 4px; text-align: center; transition: border-color 250ms, transform 250ms; }
.path-card:hover { border-color: #22C55E; transform: translateY(-2px); }
.path-pct { font-family: 'JetBrains Mono', monospace; font-size: 2.5rem; font-weight: 700; color: #22C55E; margin-bottom: 4px; letter-spacing: -0.02em; line-height: 1; }
.path-name { font-family: 'JetBrains Mono', monospace; color: #94A3B8; font-size: 0.75rem; letter-spacing: 0.08em; margin-top: 8px; text-transform: uppercase; }

.path-name { word-break: break-word; line-height: 1.4; hyphens: auto; }

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
/* 修复 2026-06-22: cs 主题深色背景, 默认 var(--ink, #1A1A1A) 不可见, 覆盖 12 处 var(--ink) 文字类 */
:root { --ink: #F8FAFC; --rule: #1F2937; }
/* a1b9ebc6 的 !important #1A1A1A 硬编码需要 theme override */
section.tab .ovv-simple-fit-list li { color: #F8FAFC !important; }
section.tab .ovv-pit { background: rgba(34, 197, 94, 0.04); border-color: #1F2937; }
footer { background: rgba(11, 17, 32, 0.6); border-top: 1px solid #1F2937; }
footer .label { color: #22C55E; }
footer .data-source { color: #94A3B8; }

.drop-cap::first-letter { font-family: 'JetBrains Mono', monospace; font-size: 4em; font-weight: 700; line-height: 0.9; float: left; margin: 0.05em 0.12em 0 0; color: #22C55E; }

.lede { color: #94A3B8; line-break: strict; }

.terminal-prompt, .hero-decor { color: #22C55E; }

/* ── CS mobile patch (≤480px) — hide 终端 ASCII 3D 大字, 因为下方有干净标题重复显示 ── */
@media (max-width: 480px) {
  .terminal-panel { display: none !important; }
  .hero-grid { display: block !important; }
  .hero { padding-top: 40px !important; padding-bottom: 32px !important; }
}
"""

def render_hero_cs(data, *, title, summary, category, degree, duration, tags, difficulty, updated_at, hero_quote, hero_quote_sig):
    return f'''
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
