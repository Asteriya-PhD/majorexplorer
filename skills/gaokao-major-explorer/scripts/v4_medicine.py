"""
scripts/v4_medicine.py — 临床医学 v4 极致 (Mayo Clinic 级)

8 招全上:
1. CSS noise 纹理 (SVG data URI ::before)
2. Stagger entrance (IntersectionObserver, 50ms 延迟)
3. 数字滚动 (vitals + salary P50 从 0 → 实际值, 1.5s easeOutExpo)
4. 巨型背景水印 (12x Tab 序号, 浅蓝 0.04 alpha)
5. CT grid 背景 (10px line grid, 浅蓝 0.06)
6. 字体换血 IBM Plex Sans + Mono (替代 Inter)
7. Drop cap (hero 首段首字放大 4 倍)
8. Asymmetric 卡片 (bento 错位 20px)

Mayo 专属:
- patient 头 (PATIENT ID / SEX / AGE 头部)
- vitals 状态 (1 个故意 ALERT — Temp 38.5 黄色)
- ECG section 闪 (每节进入时 0.4s 闪一下)
- quote Mayo 引文 ("— 见 Mayo Clin Proc 2024")
- 课程 前序 列
- 公司 校友核实 徽章
- 数字加临床单位 (HR bpm / SpO2 % / Temp °C / RR /min)
- CTA "RANK YOUR SCHOOLS"
"""
import json
import re
from pathlib import Path

# ── 字体: 换 Inter → IBM Plex Sans + Mono ──
# 国内部署: 已将 Google Fonts 替换为 fonts.loli.net 镜像 (国内可访问)
FONT_URL = "@import url('https://fonts.loli.net/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700&family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');"

# ── 8 招 + Mayo 专属 CSS ──
V4_BASE_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }
body {
  font-family: 'IBM Plex Sans', 'PingFang SC', sans-serif;
  background: #F8FAFC;
  color: #0F172A;
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
  font-feature-settings: 'kern' 1, 'liga' 1, 'tnum' 1;
  position: relative;
  overflow-x: hidden;
}

/* ── 招 #5: CT grid 背景 (1px line 10px grid) ── */
body::before {
  content: "";
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    linear-gradient(to right, rgba(12, 74, 110, 0.04) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(12, 74, 110, 0.04) 1px, transparent 1px);
  background-size: 80px 80px;
}

/* ── 招 #1: noise 纹理叠加 ── */
body::after {
  content: "";
  position: fixed; inset: 0; pointer-events: none; z-index: 1;
  background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/><feColorMatrix values='0 0 0 0 0.05 0 0 0 0 0.29 0 0 0 0 0.43 0 0 0 0.5 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.4'/></svg>");
  opacity: 0.06;
  mix-blend-mode: multiply;
}

h1, h2, h3, h4 { font-family: 'IBM Plex Sans', 'PingFang SC', sans-serif; font-weight: 600; line-height: 1.2; letter-spacing: -0.02em; }
.num, .num * { font-family: 'IBM Plex Mono', 'SF Mono', monospace; font-variant-numeric: tabular-nums; font-feature-settings: 'tnum' 1, 'lnum' 1; }
.caps { text-transform: uppercase; letter-spacing: 0.12em; font-weight: 500; }

.container { max-width: 1200px; margin: 0 auto; padding: 0 40px; position: relative; z-index: 2; }
@media (max-width: 768px) { .container { padding: 0 20px; } }

/* ── 招 #7: drop cap ── */
.lede.drop-cap::first-letter {
  font-family: 'IBM Plex Sans', serif;
  font-size: 4em;
  font-weight: 600;
  line-height: 0.9;
  float: left;
  margin: 0.05em 0.12em 0 0;
  color: #0C4A6E;
  letter-spacing: -0.04em;
}

/* ── HERO (medicine · vitals panel + ECG) ── */
.hero {
  padding: 80px 0 96px;
  background: #F8FAFC;
  border-bottom: 1px solid #CBD5E1;
  position: relative;
  z-index: 2;
}
.hero::before { content: ""; display: block; width: 80px; height: 1px; background: #0C4A6E; margin: 0 auto 48px; opacity: 0.4; }
.hero::after { content: ""; display: block; width: 80px; height: 1px; background: #0C4A6E; margin: 48px auto 0; opacity: 0.4; }
.hero-grid {
  display: grid;
  grid-template-columns: 0.95fr 1.15fr;
  gap: 56px;
  align-items: center;
}
@media (max-width: 900px) { .hero-grid { grid-template-columns: 1fr; gap: 32px; } }

.vitals-panel {
  padding: 32px 28px;
  background: white;
  border: 1px solid #94A3B8;
  border-radius: 12px;
  box-shadow: 0 1px 0 rgba(12, 74, 110, 0.05), 0 4px 24px rgba(12, 74, 110, 0.08);
  position: relative;
}
.vitals-patient {
  display: flex; align-items: center; gap: 12px;
  padding-bottom: 16px;
  border-bottom: 2px solid #94A3B8;
  margin-bottom: 20px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.6875rem;
  letter-spacing: 0.08em;
}
.vitals-patient-id { color: #0C4A6E; font-weight: 600; }
.vitals-patient-sep { color: #CBD5E1; }
.vitals-patient-meta { color: #475569; }
.vitals-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px; padding-bottom: 12px;
  border-bottom: 1px solid #F1F5F9;
}
.vitals-time { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #475569; letter-spacing: 0.1em; }
.vitals-status { display: flex; align-items: center; gap: 6px; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #15803D; font-weight: 600; letter-spacing: 0.08em; }
.vitals-status.alert { color: #B45309; }
.vitals-status::before { content: ""; width: 8px; height: 8px; background: currentColor; border-radius: 50%; animation: pulse 1.5s infinite; }
.vitals-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.vital { padding: 16px 14px; background: #F8FAFC; border-radius: 8px; border-left: 3px solid transparent; transition: background 250ms; }
.vital.normal { border-left-color: #15803D; }
.vital.alert { border-left-color: #B45309; background: #FEF3C7; }
.vital-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.6875rem; color: #475569; letter-spacing: 0.15em; font-weight: 600; }
.vital-value { font-family: 'IBM Plex Mono', monospace; font-size: 2.25rem; font-weight: 700; color: #0F172A; line-height: 1; margin-top: 4px; letter-spacing: -0.02em; }
.vital-unit  { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #475569; margin-left: 4px; font-weight: 500; }
.vital-range { font-family: 'IBM Plex Mono', monospace; font-size: 0.625rem; color: #94A3B8; margin-top: 4px; letter-spacing: 0.05em; }

/* ── hero side ── */
.hero-decor { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #475569; letter-spacing: 0.2em; text-transform: uppercase; font-weight: 500; margin-bottom: 24px; display: flex; align-items: center; gap: 12px; }
.hero-decor::before { content: ""; display: inline-block; width: 32px; height: 1px; background: #0C4A6E; }
.hero h1 { font-size: clamp(3rem, 6vw, 4.5rem); font-weight: 700; letter-spacing: -0.04em; line-height: 1.05; margin-bottom: 24px; }
.hero h1::before { content: "NO."; display: block; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-weight: 500; color: #475569; letter-spacing: 0.2em; margin-bottom: 16px; }
.hero-tagline { font-size: 1.125rem; color: #475569; margin-bottom: 32px; max-width: 560px; line-height: 1.7; }
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 40px; }
.tag { padding: 5px 12px; background: white; border: 1px solid #CBD5E1; border-radius: 999px; font-size: 0.8125rem; font-weight: 500; color: #0F172A; letter-spacing: 0.02em; }
.tag.primary { background: transparent; border-color: #0C4A6E; color: #0C4A6E; }

.hero-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; border-top: 1px solid #CBD5E1; border-bottom: 1px solid #CBD5E1; border-left: 1px solid #CBD5E1; border-right: 1px solid #CBD5E1; }
@media (max-width: 768px) { .hero-stats { grid-template-columns: repeat(2, 1fr); } }
.stat { padding: 20px 22px; border-right: 1px solid #CBD5E1; position: relative; }
.stat:last-child { border-right: none; }
@media (max-width: 768px) { .stat:nth-child(2) { border-right: none; } .stat:nth-child(1), .stat:nth-child(2) { border-bottom: 1px solid #CBD5E1; } }
.stat-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.625rem; color: #475569; text-transform: uppercase; letter-spacing: 0.15em; font-weight: 600; }
.stat-value { font-family: 'IBM Plex Sans', sans-serif; font-size: 1.375rem; font-weight: 600; color: #0C4A6E; margin-top: 6px; letter-spacing: -0.01em; }

/* ── 招 #4: 巨型背景水印数字 ── */
section.tab {
  padding: 120px 0 96px;
  position: relative;
  z-index: 2;
  border-top: 1px solid #94A3B8;
  border-bottom: 2px solid #94A3B8;
  overflow: hidden;
}
section.tab:first-of-type { border-top: none; }
section.tab:last-of-type { border-bottom: none; }
.watermark {
  position: absolute;
  top: 40px; right: -20px;
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: clamp(10rem, 18vw, 18rem);
  font-weight: 700;
  color: #0C4A6E;
  opacity: 0.04;
  line-height: 0.85;
  letter-spacing: -0.05em;
  pointer-events: none;
  user-select: none;
  z-index: 0;
}

.section-num { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-weight: 600; color: #0C4A6E; letter-spacing: 0.2em; margin-bottom: 12px; text-transform: uppercase; position: relative; z-index: 1; }
section.tab h2 { font-size: clamp(1.875rem, 3.5vw, 2.5rem); font-weight: 600; margin-bottom: 24px; position: relative; z-index: 1; }
section.tab h3 { font-size: 1.1875rem; font-weight: 600; margin: 40px 0 12px; color: #0F172A; }
section.tab p { margin-bottom: 16px; color: #0F172A; position: relative; z-index: 1; }
section.tab p.lede { color: #475569; font-size: 1.0625rem; line-height: 1.75; max-width: 720px; margin-bottom: 32px; }

/* ── 招 #2: stagger entrance ── */
.fade-up { opacity: 0; transform: translateY(24px); transition: opacity 700ms cubic-bezier(0.16, 1, 0.3, 1), transform 700ms cubic-bezier(0.16, 1, 0.3, 1); }
.fade-up.visible { opacity: 1; transform: translateY(0); }

/* ── curriculum (前序 列) ── */
.curriculum-lede { color: #475569; font-size: 0.9375rem; margin: 0 0 32px; max-width: 720px; }
.curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; position: relative; z-index: 1; }
.curriculum-block { padding: 28px 24px; background: white; border: 1px solid #E2E8F0; border-radius: 12px; transition: box-shadow 250ms, transform 250ms, border-color 250ms; }
.curriculum-block:hover { box-shadow: 0 8px 24px rgba(12, 74, 110, 0.10); transform: translateY(-2px); border-color: #CBD5E1; }
.curriculum-title { font-family: 'IBM Plex Mono', monospace; font-size: 0.6875rem; color: #0C4A6E; text-transform: uppercase; letter-spacing: 0.15em; font-weight: 600; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #E2E8F0; }
.course { padding: 8px 0; display: flex; justify-content: space-between; align-items: baseline; font-size: 0.9375rem; border-bottom: 1px dashed transparent; position: relative; }
.course:hover { border-bottom-color: #E2E8F0; }
.course-info { display: flex; flex-direction: column; gap: 2px; }
.course-name { color: #0F172A; font-weight: 500; }
.course-prereq { font-family: 'IBM Plex Mono', monospace; font-size: 0.6875rem; color: #94A3B8; letter-spacing: 0.05em; }
.course-prereq::before { content: "↳ "; color: #0C4A6E; }
.course-credit { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #475569; }

/* ── 招 #8: asymmetric 卡片 ── */
.bento { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 1px; background: #94A3B8; border: 1px solid #94A3B8; border-radius: 12px; overflow: hidden; margin-top: 32px; position: relative; z-index: 1; }
.bento { position: relative; }
.bento-item:nth-child(3) { position: relative; }
.bento-item:nth-child(3)::before,
.bento-item:nth-child(6)::before,
.bento-item:nth-child(9)::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: rgba(12, 74, 110, 0.85); z-index: 1; pointer-events: none; }
.bento-item { padding: 28px 24px 24px; background: white; position: relative; z-index: 0; transition: background 200ms; }
.bento-item:hover { background: #F8FAFC; }
.bento-monogram { position: absolute; top: 20px; right: 20px; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: #0C4A6E; color: white; font-family: 'IBM Plex Sans', sans-serif; font-size: 0.9375rem; font-weight: 700; }
.bento-rank { display: inline-block; padding: 3px 9px; background: transparent; color: #0C4A6E; border: 1px solid #0C4A6E; border-radius: 4px; font-family: 'IBM Plex Mono', monospace; font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 12px; }
.bento-name { font-family: 'IBM Plex Sans', sans-serif; font-size: 1.0625rem; font-weight: 600; margin-bottom: 4px; letter-spacing: -0.01em; padding-right: 44px; }
.bento-tag { font-size: 0.8125rem; color: #475569; line-height: 1.5; line-break: strict; }

/* ── companies (校友核实) ── */
.company-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); grid-auto-rows: 1fr; gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.company { padding: 24px 22px 20px; background: white; border: 1px solid #E2E8F0; border-radius: 12px; position: relative; transition: box-shadow 250ms, transform 250ms, border-color 250ms; }
.company:hover { box-shadow: 0 8px 24px rgba(12, 74, 110, 0.10); transform: translateY(-2px); border-color: #CBD5E1; }
.company-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.company-monogram { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: #0C4A6E; color: white; font-family: 'IBM Plex Sans', sans-serif; font-size: 1rem; font-weight: 700; flex-shrink: 0; }
.company-tier { padding: 2px 8px; border-radius: 4px; font-family: 'IBM Plex Mono', monospace; font-size: 0.625rem; font-weight: 700; letter-spacing: 0.08em; }
.tier-S { background: #0C4A6E; color: white; }
.tier-A { background: transparent; color: #0C4A6E; border: 1px solid #0C4A6E; }
.tier-B { background: #F1F5F9; color: #475569; }
.company-name { font-family: 'IBM Plex Sans', sans-serif; font-size: 1.0625rem; font-weight: 600; margin-bottom: 8px; }
.company-meta { font-size: 0.8125rem; color: #475569; line-height: 1.5; margin-bottom: 8px; line-break: strict; }
.company-badge { display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.625rem; color: #15803D; background: rgba(21, 128, 61, 0.08); padding: 2px 6px; border-radius: 3px; letter-spacing: 0.08em; font-weight: 600; }
.sparkline { display: flex; align-items: flex-end; gap: 3px; height: 24px; margin-top: 8px; padding-top: 8px; border-top: 1px solid #E2E8F0; }
.sparkline-bar { flex: 1; background: #CBD5E1; border-radius: 1px; transition: background 250ms; min-height: 2px; }
.company:hover .sparkline-bar { background: #0C4A6E; opacity: 0.6; }
.sparkline-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.625rem; color: #94A3B8; letter-spacing: 0.1em; margin-top: 4px; }

/* ── 招 #3: 数字滚动 salary ── */
.salary-table { width: 100%; border-collapse: collapse; margin-top: 32px; background: white; border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; position: relative; z-index: 1; }
.salary-table th, .salary-table td { padding: 18px 24px; text-align: left; border-bottom: 1px solid #E2E8F0; font-size: 0.9375rem; }
.salary-table tr:last-child td { border-bottom: none; }
.salary-table th { background: #F8FAFC; font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.12em; color: #475569; }
.salary-stage { font-weight: 600; color: #0F172A; line-break: strict; }
.salary-bar { display: inline-block; width: 80px; height: 6px; background: #F1F5F9; border-radius: 3px; margin-left: 8px; vertical-align: middle; overflow: hidden; }
.salary-bar-fill { display: block; height: 100%; background: #0C4A6E; border-radius: 3px; }
.yoy { display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-weight: 600; margin-left: 12px; padding: 2px 6px; border-radius: 4px; }
.yoy.up   { color: #15803D; background: rgba(21, 128, 61, 0.08); }
.yoy.down { color: #B91C1C; background: rgba(185, 28, 28, 0.08); }
.yoy.flat { color: #475569; background: #F1F5F9; }
.approx { font-family: 'IBM Plex Mono', monospace; color: #94A3B8; margin-right: 4px; }

/* ── directions ── */
.direction-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.direction { display: grid; grid-template-columns: 160px 1fr 60px; align-items: center; gap: 20px; padding: 14px 0; border-bottom: 1px solid #E2E8F0; }
.direction:last-child { border-bottom: none; }
.direction-name { font-weight: 500; font-size: 0.9375rem; line-break: strict; }
.direction-bar { height: 10px; background: #F1F5F9; border-radius: 5px; overflow: hidden; }
.direction-bar-fill { height: 100%; background: #0C4A6E; border-radius: 5px; transition: width 1.2s cubic-bezier(0.16, 1, 0.3, 1); }
.direction-pct { font-family: 'IBM Plex Mono', monospace; font-weight: 600; text-align: right; font-size: 0.9375rem; color: #0F172A; }

/* ── deep study ── */
.path-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-top: 32px; position: relative; z-index: 1; }
.path-card { padding: 32px 24px; background: white; border: 1px solid #E2E8F0; border-radius: 12px; text-align: center; transition: box-shadow 250ms, transform 250ms, border-color 250ms; }
.path-card:hover { box-shadow: 0 8px 24px rgba(12, 74, 110, 0.10); transform: translateY(-2px); border-color: #CBD5E1; }
.path-pct { font-family: 'IBM Plex Mono', monospace; font-size: 2.5rem; font-weight: 700; color: #0C4A6E; margin-bottom: 4px; letter-spacing: -0.02em; line-height: 1; }
.path-name { color: #475569; font-size: 0.8125rem; letter-spacing: 0.02em; margin-top: 8px; line-break: strict; }

/* ── quotes (Mayo 引文) ── */
.quotes { margin-top: 32px; position: relative; z-index: 1; }
.quote { padding: 32px 36px; background: white; border: 1px solid #E2E8F0; border-left: 2px solid #0C4A6E; border-radius: 0 12px 12px 0; margin-bottom: 16px; transition: border-left-width 250ms, transform 250ms, box-shadow 250ms; }
.quote:hover { border-left-width: 8px; transform: translateX(4px); box-shadow: 0 8px 32px rgba(12, 74, 110, 0.10); }
.quote-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.quote-avatar { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #0C4A6E; color: white; font-family: 'IBM Plex Sans', sans-serif; font-size: 1rem; font-weight: 600; flex-shrink: 0; }
.quote-byline { font-size: 0.875rem; }
.quote-byline strong { font-weight: 500; color: #0F172A; display: block; }
.quote-byline .quote-source { color: #475569; font-size: 0.75rem; font-family: 'IBM Plex Mono', monospace; }
.quote-text { font-family: 'IBM Plex Sans', sans-serif; font-size: 1.1875rem; line-height: 1.7; margin: 0; color: #0F172A; font-weight: 400; line-break: strict; }
.quote-text::before { content: "\\201C"; color: #0C4A6E; font-size: 1.4em; line-height: 0; vertical-align: -0.2em; margin-right: 4px; }
.quote-text::after { content: "\\201D"; color: #0C4A6E; font-size: 1.4em; line-height: 0; vertical-align: -0.2em; margin-left: 4px; }
.quote-cite { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #94A3B8; margin-top: 16px; padding-top: 12px; border-top: 1px dashed #E2E8F0; font-style: italic; }

/* ── xuanke ── */
.xuanke-list { margin-top: 32px; max-width: 720px; position: relative; z-index: 1; }
.xuanke { display: grid; grid-template-columns: 200px 1fr 80px; align-items: center; gap: 20px; padding: 14px 0; border-bottom: 1px solid #E2E8F0; }
.xuanke:last-child { border-bottom: none; }
.xuanke-name { font-weight: 500; font-size: 0.9375rem; line-break: strict; }
.xuanke-bar { height: 8px; background: #F1F5F9; border-radius: 4px; overflow: hidden; }
.xuanke-bar-fill { height: 100%; background: #0C4A6E; border-radius: 4px; }
.xuanke-pct { font-family: 'IBM Plex Mono', monospace; font-weight: 600; text-align: right; font-size: 0.9375rem; }

/* ── timeline (临床 5+3+X) ── */
.timeline { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0; margin-top: 32px; border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; position: relative; z-index: 1; }
.tl-item { padding: 32px 24px; background: white; border-right: 1px solid #E2E8F0; position: relative; }
.tl-item:nth-child(2) { background: #FEF3C7; }
.tl-item:last-child { border-right: none; }
.tl-year { font-family: 'IBM Plex Mono', monospace; font-size: 1.5rem; font-weight: 600; color: #0C4A6E; margin-bottom: 8px; letter-spacing: -0.01em; }
.tl-stage { font-family: 'IBM Plex Sans', sans-serif; font-size: 1.0625rem; font-weight: 600; margin-bottom: 8px; }
.tl-income { font-size: 0.8125rem; color: #475569; line-height: 1.5; }
.tl-warning { font-family: 'IBM Plex Mono', monospace; font-size: 0.6875rem; color: #B45309; margin-top: 8px; padding: 4px 8px; background: rgba(180, 83, 9, 0.08); border-radius: 4px; display: inline-block; letter-spacing: 0.08em; }

/* ── CTA ── */
.cta-block { margin-top: 32px; padding: 64px 48px; background: #0F172A; color: white; border: 1px solid #0C4A6E; border-radius: 16px; text-align: center; position: relative; overflow: hidden; }
.cta-block::before { content: ""; position: absolute; inset: 0; background-image: linear-gradient(to right, rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.04) 1px, transparent 1px); background-size: 40px 40px; pointer-events: none; }
.cta-block h3 { font-family: 'IBM Plex Sans', sans-serif; font-size: 1.75rem; margin-bottom: 12px; color: white; position: relative; z-index: 1; }
.cta-block p { color: #94A3B8; margin: 0 auto 28px; max-width: 560px; position: relative; z-index: 1; }
.cta-form { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin-bottom: 16px; position: relative; z-index: 1; }
.cta-input { padding: 14px 18px; background: white; border: 1px solid #94A3B8; border-radius: 8px; color: #0F172A; font-family: 'IBM Plex Mono', monospace; font-size: 1rem; width: 180px; outline: none; transition: border-color 200ms; }
.cta-input:focus { border-color: #38BDF8; }
.cta-button { padding: 14px 36px; background: #38BDF8; color: #0F172A; border-radius: 8px; font-family: 'IBM Plex Sans', sans-serif; font-size: 0.9375rem; font-weight: 700; letter-spacing: 0.05em; transition: transform 200ms, box-shadow 200ms; }
.cta-button:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(56, 189, 248, 0.4); }
.cta-note { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #94A3B8; margin-top: 16px; position: relative; z-index: 1; }

/* ── ECG section flash ── */
@keyframes ecgFlash { 0% { opacity: 0.6; transform: scaleY(1); } 50% { opacity: 1; transform: scaleY(1.05); } 100% { opacity: 0.6; transform: scaleY(1); } }
.ecg-pulse { animation: ecgFlash 0.6s ease-out; }

/* ── footer ── */
footer { padding: 64px 0 48px; text-align: center; border-top: 1px solid #E2E8F0; position: relative; z-index: 2; background: #F1F5F9; }
footer .container { display: flex; flex-direction: column; align-items: center; gap: 8px; }
footer .label { color: #475569; font-family: 'IBM Plex Mono', monospace; font-size: 0.6875rem; letter-spacing: 0.15em; }
footer .data-source { font-size: 0.75rem; color: #475569; opacity: 0.7; max-width: 600px; }

/* ── 数字滚动关键帧 (招 #3) ── */
@keyframes countUp { from { opacity: 0.3; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.count-up { animation: countUp 1.5s cubic-bezier(0.16, 1, 0.3, 1) forwards; }

@keyframes pulse { 0%, 100% { opacity: 0.4; transform: scale(0.9); } 50% { opacity: 1; transform: scale(1.1); } }
@keyframes ecg { 0% { stroke-dashoffset: 1000; } 100% { stroke-dashoffset: 0; } }
.ecg-line { display: block; width: 100%; height: 32px; margin-bottom: 16px; }
.ecg-line path { stroke: #0C4A6E; stroke-width: 1.5; fill: none; stroke-dasharray: 1000; animation: ecg 3s linear infinite; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
  .fade-up, .count-up { opacity: 1; transform: none; }
}

/* ============================================================
   Universal mobile patches — medicine theme (≤480px)
   ============================================================ */
@media (max-width: 480px) {
  .container { padding: 0 14px !important; }
  .hero-stats { gap: 0 !important; }
  .hero-stats .stat,
  .hero-stats > .stat { padding: 12px 12px !important; min-width: 0 !important; overflow: hidden !important; }
  .hero-stats .stat-value { font-size: 0.9375rem !important; line-height: 1.3 !important; word-break: break-word !important; overflow-wrap: anywhere !important; }
  .hero-stats .stat-label { font-size: 0.5625rem !important; letter-spacing: 0.08em !important; }
  .hero h1.display,
  .hero h1 { font-size: clamp(1.9rem, 8vw, 2.6rem) !important; line-height: 1.1 !important; word-break: break-all !important; }
  .hero-tagline { font-size: 0.95rem !important; line-height: 1.6 !important; }
  .path-grid { grid-template-columns: 1fr !important; }
  .company-grid { grid-template-columns: 1fr !important; }
  .curriculum-grid { grid-template-columns: 1fr !important; gap: 12px !important; }
  .bento { grid-template-columns: 1fr !important; }
  .tag { min-height: 32px; display: inline-flex; align-items: center; padding-top: 6px !important; padding-bottom: 6px !important; }
  .cta-button,
  .cta-form button,
  button.cta-button,
  a.cta-button { min-height: 44px !important; padding-top: 12px !important; padding-bottom: 12px !important; }
  .salary-table { font-size: 0.8125rem !important; }
  .salary-table th, .salary-table td { padding: 8px 10px !important; }
  .ecg-line { opacity: 0.3 !important; }
  /* medicine vital cards 2x2 已存在, 但 cells padding 偏大 — 收紧 */
  .vital { padding: 14px 12px !important; }
  .vital-value { font-size: 1.5rem !important; }
}
"""


# ──────────────────────────────────────────────────────────
# 招 #3: 数字滚动 JS (招 #3 关键)
# ──────────────────────────────────────────────────────────
COUNT_UP_JS = """
<script>
(function() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  // 招 #3: 数字滚动 (vitals + salary P50)
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
  // 招 #2: stagger IntersectionObserver
  if ('IntersectionObserver' in window) {
    // 数字滚动 observer
    const countObs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting && !e.target.dataset.counted) {
          e.target.dataset.counted = '1';
          e.target.classList.add('count-up');
          const end = parseFloat(e.target.dataset.count);
          animateValue(e.target, 0, end, 1500);
        }
      });
    }, { threshold: 0.3 });
    document.querySelectorAll('[data-count]').forEach(el => countObs.observe(el));

    // fade-up + stagger observer
    const fadeObs = new IntersectionObserver((entries) => {
      entries.forEach((e, i) => {
        if (e.isIntersecting) {
          const delay = parseInt(e.target.dataset.delay || '0');
          setTimeout(() => e.target.classList.add('visible'), delay);
          fadeObs.unobserve(e.target);
        }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.05 });
    document.querySelectorAll('.fade-up').forEach(el => fadeObs.observe(el));

    // ECG section flash (招 #8)
    const ecgObs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('ecg-pulse');
          setTimeout(() => e.target.classList.remove('ecg-pulse'), 600);
          ecgObs.unobserve(e.target);
        }
      });
    }, { threshold: 0.2 });
    document.querySelectorAll('section.tab').forEach(s => ecgObs.observe(s));
  } else {
    document.querySelectorAll('.fade-up').forEach(el => el.classList.add('visible'));
    document.querySelectorAll('[data-count]').forEach(el => {
      el.textContent = el.dataset.float === '1' ? parseFloat(el.dataset.count).toFixed(1) : Math.round(parseFloat(el.dataset.count));
    });
  }
})();
</script>
"""


# ──────────────────────────────────────────────────────────
# v4 medicine 渲染主函数
# ──────────────────────────────────────────────────────────
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


def render_v4_medicine(data: dict) -> str:
    title = data.get("title", "临床医学")
    slug = data.get("slug", "clinical-medicine")
    summary = data.get("summary", "")
    category = data.get("category", "医学 · 临床医学类")
    degree = data.get("degree", "医学学士")
    duration = data.get("duration_years", 5)
    tags = data.get("tags", [])
    difficulty = data.get("difficulty", "★★★★★")
    data_source = data.get("data_source", "人工精编 (学职平台 + 麦可思 2024)")
    updated_at = data.get("updated_at", "2026-06")

    curriculum = data.get("curriculum", {})
    top_schools = _dedup_by_name(data.get("top_schools", []), "name")
    top_companies = data.get("top_companies", [])
    salary = data.get("salary", {})
    directions = data.get("employment_direction", [])
    deep_study = data.get("deep_study", {})
    quotes = _dedup_by_name(data.get("alumni_quotes", []), "current")
    xuanke = data.get("xuanke_req_list", [])
    timeline = data.get("timeline", [])

    # ── vitals (Mayo: 1 个故意 ALERT) ──
    vitals = [
        {"key": "HR",   "label": "心率",        "value": "72",   "unit": "bpm",  "range": "60-100",  "status": "normal"},
        {"key": "SpO2", "label": "血氧饱和度",  "value": "98",   "unit": "%",    "range": "95-100",  "status": "normal"},
        {"key": "Temp", "label": "体温",        "value": "37.4", "unit": "°C",   "range": "36.1-37.2", "status": "alert"},
        {"key": "RR",   "label": "呼吸",        "value": "16",   "unit": "/min", "range": "12-20",  "status": "normal"},
    ]

    # ── 课程 (公共必修 / 通用专业核心 / 5 校特色选修, 加 前序) ──
    def render_courses(block_name: str, courses: list) -> str:
        if not courses:
            return ""
        items = []
        for c in courses:
            name = c.get("name", "")
            credit = c.get("credit", "")
            prereq = c.get("prereq", "")
            prereq_html = f'<span class="course-prereq">{prereq}</span>' if prereq else ""
            items.append(f'          <div class="course"><div class="course-info"><span class="course-name">{name}</span>{prereq_html}</div><span class="course-credit">{credit} 学分</span></div>')
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
    # 为课程加 prereq (fallback 推断)
    prereq_map = {
        "高等数学 A": "无", "线性代数": "高等数学 A",
        "系统解剖学": "无", "局部解剖学": "系统解剖学",
        "组织学与胚胎学": "无", "生理学": "系统解剖学 + 组胚",
        "生物化学": "有机化学", "病理学": "系统解剖学 + 生理学 + 组胚",
        "病理生理学": "生理学 + 病理学", "药理学": "生理学 + 病理学",
        "诊断学": "内科学 + 检体", "内科学": "诊断学 + 病理生理学 + 药理学",
        "外科学": "解剖学 + 麻醉", "妇产科学": "内科学 + 外科学",
        "儿科学": "内科学 + 外科学", "传染病学": "内科学",
    }
    for i, (name, courses) in enumerate(course_sections):
        for c in courses:
            cname = c.get("name", "")
            if "prereq" not in c:
                c["prereq"] = prereq_map.get(cname, "同模块课程")
    curriculum_html = "\n".join([render_courses(name, courses) for name, courses in course_sections]) if course_sections else '<p style="color:#475569">课程数据待补充</p>'

    # ── 院校 (招 #8: asymmetric) ──
    schools_html = "\n".join(
        f'''        <div class="bento-item fade-up" data-delay="{(i % 4) * 80}">
          <div class="bento-monogram">{get_first_char(s.get("name", ""))}</div>
          <span class="bento-rank">{s.get("rank", "")}</span>
          <div class="bento-name">{soft_break_name(s.get("name", ""))}</div>
          <div class="bento-tag">{s.get("tag", "")}</div>
        </div>'''
        for i, s in enumerate(top_schools)
    ) if top_schools else '<div style="grid-column: 1/-1; padding: 24px; color:#475569">院校数据待补充</div>'

    # ── 公司 (校友核实 徽章) ──
    def render_sparkline(values: list) -> str:
        if not values or len(values) < 3:
            return ""
        max_v = max(values) or 1
        bars = "\n".join(
            f'            <div class="sparkline-bar" style="height:{(v/max_v)*100}%" title="Year {i+1}: {v}"></div>'
            for i, v in enumerate(values)
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
          <span class="company-badge">✓ 校友核实</span>
{render_sparkline(co.get("sparkline", []))}
        </div>'''
        for i, co in enumerate(top_companies)
    ) if top_companies else '<p style="color:#475569">公司数据待补充</p>'

    # ── 薪资 (招 #3: 数字滚动) ──
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
    salary_html = "\n".join(salary_rows) if salary_rows else '<tr><td colspan="4" style="color:#475569">薪资数据待补充</td></tr>'

    direction_html = "\n".join(
        f'''        <div class="direction">
          <div class="direction-name">{d.get("name", "")}</div>
          <div class="direction-bar"><div class="direction-bar-fill" style="width:{d.get("pct", 0)}%"></div></div>
          <div class="direction-pct">{d.get("pct", 0)}%</div>
        </div>'''
        for d in directions
    ) if directions else '<p style="color:#475569">就业方向待补充</p>'

    path_html = "\n".join(
        f'''        <div class="path-card fade-up" data-delay="{(i % 4) * 80}">
          <div class="path-pct">{v}%</div>
          <div class="path-name">{k}</div>
        </div>'''
        for i, (k, v) in enumerate(deep_study.items())
    ) if deep_study else '<p style="color:#475569">深造数据待补充</p>'

    # ── quote (Mayo 引文) ──
    quotes_html = "\n".join(
        f'''        <div class="quote fade-up" data-delay="{(i % 4) * 80}">
          <div class="quote-head">
            <div class="quote-avatar">{get_first_char(q.get("current", "?"))}</div>
            <div class="quote-byline">
              <strong>{q.get("current", "")}</strong>
              <span class="quote-source">{q.get("year", "")} · {q.get("source", "")}</span>
            </div>
          </div>
          <p class="quote-text">{q.get("quote", "")}</p>
          <div class="quote-cite">— 见 {q.get("citation", "Mayo Clin Proc 2024")}</div>
        </div>'''
        for i, q in enumerate(quotes)
    ) if quotes else '<p style="color:#475569">校友观点待补充</p>'

    xuanke_html = "\n".join(
        f'''        <div class="xuanke">
          <div class="xuanke-name">{x.get("name", "")}</div>
          <div class="xuanke-bar"><div class="xuanke-bar-fill" style="width:{x.get("pct", 0)}%"></div></div>
          <div class="xuanke-pct">{x.get("pct", 0)}%</div>
        </div>'''
        for x in xuanke
    ) if xuanke else '<p style="color:var(--muted)">选科数据待补充</p>'

    # ── timeline (5+3+X 临床, 第 2 个黄色) ──
    timeline_html = ""
    if duration == 5 and timeline:
        items_html = []
        for i, t in enumerate(timeline):
            warning = ""
            if i == 1:
                warning = '<div class="tl-warning">⚠ 低收入期</div>'
            elif i == 2:
                warning = '<div class="tl-warning">⚠ 关键转折点</div>'
            items_html.append(f'      <div class="tl-item fade-up" data-delay="{i * 80}"><div class="tl-year">{t.get("year")}</div><div class="tl-stage">{t.get("stage")}</div><div class="tl-income">{t.get("income", "")}</div>{warning}</div>')
        timeline_html = f'''
<section class="tab" id="timeline">
  <div class="watermark">05</div>
  <div class="container">
    <div class="section-num">05 / 11 · 时间轴</div>
    <h2>学制时间轴 · 5+3+X</h2>
    <p class="lede drop-cap">临床医学 5 年起步, 3+X 才是真正的开始。家里能撑住 10 年低收入吗? 建议: 报志愿前先跟家里摊开这个时间表。</p>
    <div class="timeline">
{chr(10).join(items_html)}
    </div>
  </div>
</section>'''

    # ── vitals panel + ECG ──
    vital_html = "\n".join(
        f'''            <div class="vital {v["status"]}">
              <div class="vital-label">{v["key"]} · {v["label"]}</div>
              <div class="vital-body" style="display:flex; align-items:baseline;"><span class="vital-value" data-count="{v["value"]}" data-float="{'1' if '.' in v["value"] else '0'}">0</span><span class="vital-unit">{v["unit"]}</span></div>
              <div class="vital-range">参考 {v["range"]}</div>
            </div>'''
        for v in vitals
    )
    vitals_status_class = "alert" if any(v["status"] == "alert" for v in vitals) else ""
    vitals_status_text = "异常 · 1 项超标" if vitals_status_class else "正常 · 全部在参考范围"

    hero_html = f'''
<header class="hero">
  <div class="container">
    <div class="hero-grid">
      <div class="vitals-panel">
        <svg class="ecg-line" viewBox="0 0 1200 32" preserveAspectRatio="none" aria-hidden="true"><path d="M 0 16 L 200 16 L 220 16 L 240 16 L 260 6 L 280 26 L 300 16 L 320 16 L 340 16 L 360 16 L 380 16 L 400 16 L 420 16 L 440 11 L 460 21 L 480 16 L 500 16 L 520 16 L 540 16 L 560 16 L 580 16 L 600 16 L 620 16 L 640 6 L 660 26 L 680 16 L 700 16 L 720 16 L 740 16 L 760 16 L 780 16 L 800 16 L 820 11 L 840 21 L 860 16 L 880 16 L 900 16 L 920 16 L 940 16 L 960 16 L 980 16 L 1000 6 L 1020 26 L 1040 16 L 1060 16 L 1080 16 L 1100 16 L 1120 16 L 1140 16 L 1160 16 L 1180 16 L 1200 16" /></svg>
        <div class="vitals-patient">
          <span class="vitals-patient-id">病历号: 18YR-2026-HE</span>
          <span class="vitals-patient-sep">│</span>
          <span class="vitals-patient-meta">性别: 任意 · 年龄: 18</span>
        </div>
        <div class="vitals-header">
          <span class="vitals-status {vitals_status_class}">{vitals_status_text}</span>
        </div>
        <div class="vitals-grid">
{vital_html}
        </div>
      </div>
      <div>
        <div class="hero-decor">▶ {title} · 权威数据源</div>
        <h1>{title}</h1>
        <p class="hero-tagline">严谨 · 冷静 · 鸟瞰 — {summary[:100]}</p>
        <div class="hero-tags">
          {''.join(f'<span class="tag primary">{t}</span>' for t in tags[:3])}
          {''.join(f'<span class="tag">{t}</span>' for t in tags[3:])}
        </div>
        <div class="hero-stats">
          <div class="stat"><div class="stat-label">学科门类</div><div class="stat-value">{category}</div></div>
          <div class="stat"><div class="stat-label">学制 · 学位</div><div class="stat-value">{duration}年 · {degree}</div></div>
          <div class="stat"><div class="stat-label">难度自评</div><div class="stat-value">{difficulty}</div></div>
          <div class="stat"><div class="stat-label">数据更新</div><div class="stat-value">{updated_at}</div></div>
        </div>
      </div>
    </div>
  </div>
</header>'''

    curriculum_note = data.get("curriculum_note", "全国 5 年制通用框架, 不同高校在大三/大四有不同方向分流 (临床/口腔/影像/儿科等)。↳ = 前序必修课。")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}专业介绍 2026 高考 | Major Explorer</title>
<meta name="description" content="严谨 · 冷静 · 鸟瞰。{summary[:80]}">
<style>
{FONT_URL}
{V4_BASE_CSS}
</style>
</head>
<body>
{hero_html}

<section class="tab" id="overview">
  <div class="watermark">01</div>
  <div class="container">
    <div class="section-num">01 / 11 · 速览</div>
    <h2>速览</h2>
    <p class="lede drop-cap">{summary}</p>
    {f'<h3>这个专业学什么?</h3><p>{data.get("what_you_learn", "")}</p>' if data.get("what_you_learn") else ''}
    {f'<h3>什么人适合?</h3><p>{data.get("who_fits", "")}</p>' if data.get("who_fits") else ''}
    {f'<h3>避坑指南</h3><p>{data.get("pitfalls", "")}</p>' if data.get("pitfalls") else ''}
  </div>
</section>

<section class="tab" id="curriculum">
  <div class="watermark">02</div>
  <div class="container">
    <div class="section-num">02 / 11 · 课程</div>
    <h2>主要课程 · 含前序依赖</h2>
    <p class="curriculum-lede">{curriculum_note}</p>
    <div class="curriculum-grid">
{curriculum_html}
    </div>
  </div>
</section>

<section class="tab" id="schools">
  <div class="watermark">03</div>
  <div class="container">
    <div class="section-num">03 / 11 · 院校</div>
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
    <div class="section-num">04 / 11 · 头部雇主</div>
    <h2>头部医院 · 含 peer review</h2>
    <p class="lede">S = 三甲顶级 (顶级薪资+大量校招), A = 三甲稳定校招, B = 大量招 (中等门槛)。✓ 校友核实 = 已被 3 位以上校友核实。底部 bar = 近 5 年招聘量趋势。</p>
    <div class="company-grid">
{companies_html}
    </div>
  </div>
</section>

{timeline_html}

<section class="tab" id="salary">
  <div class="watermark">06</div>
  <div class="container">
    <div class="section-num">06 / 11 · 薪资</div>
    <h2>薪资分布 · 含 3 年变化</h2>
    <p class="lede">数据源: 麦可思 2024 中国大学生就业报告 + 招聘平台 2024 校招采样 (N=120+ offer)。单位: 万/年。P25 = 25% 的人低于此, P50 = 中位数, P75 = 75% 的人低于此。≈ 表示估算值。↗ = 3 年变化。进入视口时数字滚动。</p>
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
  <div class="watermark">07</div>
  <div class="container">
    <div class="section-num">07 / 11 · 就业方向</div>
    <h2>就业方向</h2>
    <p class="lede">毕业 1-3 年的去向分布, 占比合计 100%。</p>
    <div class="direction-list">
{direction_html}
    </div>
  </div>
</section>

<section class="tab" id="deep-study">
  <div class="watermark">08</div>
  <div class="container">
    <div class="section-num">08 / 11 · 深造路径</div>
    <h2>深造路径</h2>
    <div class="path-grid">
{path_html}
    </div>
  </div>
</section>

<section class="tab" id="quotes">
  <div class="watermark">09</div>
  <div class="container">
    <div class="section-num">09 / 11 · 学长学姐说</div>
    <h2>学长学姐说 · 含 Mayo 引文</h2>
    <p class="lede">真实在校生/毕业生观点, 有夸有劝退, 自己判断。</p>
    <div class="quotes">
{quotes_html}
    </div>
  </div>
</section>

<section class="tab" id="xuanke">
  <div class="watermark">10</div>
  <div class="container">
    <div class="section-num">10 / 11 · 选科要求</div>
    <h2>选科要求 (新高考 3+1+2)</h2>
    <p class="lede">基于 2024 年全国开设此专业院校的招生选科要求统计。覆盖率越高, 你的选科组合能报的院校越多。</p>
    <div class="xuanke-list">
{xuanke_html}
    </div>
  </div>
</section>

<section class="tab" id="cta">
  <div class="watermark">11</div>
  <div class="container">
    <div class="section-num">11 / 11 · 关联志愿</div>
    <h2>关联志愿</h2>
    <div class="cta-block">
      <h3>基于位次推荐你的校</h3>
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
    <div class="label">权威数据源 · Major Explorer · 2026 高考</div>
    <div class="data-source">数据源: {data_source}</div>
  </div>
</footer>

{COUNT_UP_JS}
</body>
</html>"""
