"""
wishlist_inject.py — 给 69 个专业 HTML 注入 3 块新内容:

  A) 顶部右上角浮动 chip "🎒 心愿单 N/6 →"  (跳 /wishlist.html)
  B) 右下角浮动 FAB ⭐ + 弹窗 (1-5⭐ 加入 / 调整)
  C) 页面底部"精品主题"区 — 12 张推荐卡 (3 × 4 网格)
       - 4 同主题相关 (从 manifest.json 同 style 取)
       - 4 跨主题热门 (固定 Top 12 热门列表)
       - 4 反差扩展 (其余 style 各 1)

输出 4 个常量 + 1 个 render 函数:
  WISHLIST_INJECT_HEAD_LINKS  — head 内 <link> (CSS 引用)
  WISHLIST_INJECT_STYLE       — head 内 <style> (chip+FAB+themes CSS)
  build_wishlist_init_js(...) — body 末 <script> (chip 挂载 + FAB 挂载)
  render_related_themes_section(slug, manifest) — body 内 12 主题卡 section

共用前提:
  /js/wishlist-store.js   (会通过 <script src> 加载)
  /js/ui-helpers.js
"""
import json
import random
from pathlib import Path

# ── 固定全站 Top 12 热门 (按 P0 名单 + 现有 manifest 已覆盖项) ──
TOP_12_HOT = [
    "computer-science", "clinical-medicine", "finance", "electrical-engineering-automation",
    "mechanical-engineering", "law", "education", "english",
    "artificial-intelligence", "stomatology", "accounting", "vehicle-engineering",
]

# ── 反差扩展候选 (各 style 1-2 个代表, 与 cs 主题对照鲜明) ──
DIVERSE_REPRESENTATIVES = {
    "humanities": ["chinese-language-literature", "history", "philosophy", "archaeology"],
    "education": ["psychology", "applied-psychology", "industrial-design", "journalism-communication"],
    "law": ["law"],
    "agri": ["agronomy", "horticulture", "landscape-architecture", "forestry", "animal-science"],
    "arts": ["fine-arts", "visual-communication-design", "animation", "digital-media-arts"],
    "sci": ["mathematics", "physics", "chemistry", "atmospheric-science"],
    "administration": ["public-administration", "library-science", "financial-management", "information-management-systems"],
    "medicine": ["clinical-medicine", "anesthesiology", "stomatology", "pharmacy", "traditional-chinese-medicine", "preventive-medicine"],
    "finance": ["accounting", "finance", "economics", "international-economics-trade", "business-administration"],
    "eng": ["aircraft-design-engineering", "chemical-engineering", "food-science-engineering", "integrated-circuit-design", "materials-science-engineering", "microelectronics", "vehicle-engineering"],
    "cs": ["computer-science", "artificial-intelligence", "software-engineering", "cybersecurity", "data-science-big-data", "communication-engineering", "electrical-engineering-automation", "electronic-information-engineering", "intelligent-science-technology", "civil-engineering", "architecture", "automation"],
    "gongan": [],
    "business": [],
}

# ── 一句话钩子 (按 slug; manifest 没有, 就根据 title 短描) ──
ONE_LINER = {
    "computer-science": "代码是术, 数学是道",
    "artificial-intelligence": "算法堆顶, 博士起步",
    "software-engineering": "工程化的代码艺术",
    "data-science-big-data": "数据驱动决策的语言",
    "cybersecurity": "攻防红蓝, 国家战略",
    "electrical-engineering-automation": "国家电网的最爱",
    "electronic-information-engineering": "硬件 + 软件, 半导体风口",
    "communication-engineering": "5G/6G 双风口",
    "intelligent-science-technology": "AI + 机器人, 交叉新专业",
    "civil-engineering": "基建脊梁, 工地+工程师",
    "architecture": "甲方乙方, 五年制设计",
    "automation": "控制理论 + 嵌入式, 万金油工科",
    "mechanical-engineering": "制造业脊梁, 越老越香",
    "vehicle-engineering": "新能源车的核心",
    "aircraft-design-engineering": "大飞机/航天, 985 强校门槛",
    "chemical-engineering": "流程工业, 万华中石化",
    "food-science-engineering": "伊利蒙牛, 食药监公务员",
    "integrated-circuit-design": "卡脖子的芯片设计",
    "materials-science-engineering": "宽口径, 新能源半导体",
    "microelectronics": "芯片设计, 高薪风口",
    "clinical-medicine": "5+3+X, 35 岁后越值钱",
    "anesthesiology": "手术台的幕后守护者",
    "stomatology": "高薪不值班, 诊所创业",
    "pharmacy": "药企/医院双选, 读研才香",
    "preventive-medicine": "疾控中心对口, 公务员事编",
    "traditional-chinese-medicine": "师承制, 越老越值钱",
    "finance": "高薪, 名校导向, 资源敏感",
    "accounting": "考证, 稳定, 越老越值钱",
    "economics": "理论扎实, 名校导向",
    "international-economics-trade": "跨境电商风口, 英语硬门槛",
    "business-administration": "名校红利, MBA 深造",
    "financial-management": "CPA 万金油, 偏会计",
    "law": "法考 + 红圈所, 卷学历",
    "education": "稳定 + 寒暑假 + 入编",
    "english": "教学/翻译/考公考编",
    "psychology": "用户研究 + 认知神经科学",
    "applied-psychology": "HCI/UX + 工业组织, 万金油",
    "industrial-design": "汽车/手机/家电设计",
    "journalism-communication": "新媒体 + 短视频, 内卷",
    "chinese-language-literature": "语文教师 + 考公 + 出版社",
    "history": "考公友好 + 师范对口",
    "philosophy": "纯文冷门, 考博长线",
    "archaeology": "田野 + 文博 + 事业编",
    "mathematics": "万金油基础 + 深造率高",
    "physics": "四大力学, 转工科友好",
    "chemistry": "天坑之首, 深造导向",
    "atmospheric-science": "气象局对口, 民航空管",
    "public-administration": "公务员对口, 万金油",
    "library-science": "事业单位 + 考公考编",
    "information-management-systems": "ERP/BA + 管信交叉",
    "agronomy": "袁隆平精神, 国之根基",
    "horticulture": "果树蔬菜花卉, 不种地",
    "landscape-architecture": "设计院主力, CAD/PS/SU",
    "forestry": "林草局直属, 国考多",
    "animal-science": "温氏新希望, 饲料配方",
    "fine-arts": "九大美院, 央美国美",
    "visual-communication-design": "UI/UX + 品牌, 字节腾讯",
    "animation": "追光原力, 国漫崛起",
    "digital-media-arts": "影视 + 游戏 + 交互",
    "environmental-design": "室内 + 室外, 设计院",
}


def _load_manifest(manifest_path: str | Path) -> dict:
    """加载 manifest.json, 返回 dict (slug → record)"""
    p = Path(manifest_path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return {m["slug"]: m for m in data.get("majors", [])}


def _pick_related(slug: str, manifest: dict, k_same: int = 4, k_hot: int = 4, k_diverse: int = 4) -> list[dict]:
    """选 4+4+4 = 12 张相关卡片"""
    current = manifest.get(slug)
    if not current:
        return []
    own_style = current["style"]
    own_slug = current["slug"]
    all_slugs = set(manifest.keys()) - {own_slug}

    # 1) 同主题 (排除自己)
    same = [s for s, m in manifest.items() if m["style"] == own_style and s != own_slug]
    random.Random(slug).shuffle(same)   # 用 slug 当种子保证稳定
    same_pick = same[:k_same]
    used = set(same_pick) | {own_slug}

    # 2) 跨主题热门 (Top 12 - 已用)
    hot = [s for s in TOP_12_HOT if s in manifest and s not in used]
    hot_pick = hot[:k_hot]
    used |= set(hot_pick)

    # 3) 反差扩展 — 从 8 个其他 style 各取 1
    diverse_pick = []
    other_styles = [st for st in DIVERSE_REPRESENTATIVES.keys() if st != own_style]
    random.Random(slug + "diverse").shuffle(other_styles)
    for st in other_styles:
        if len(diverse_pick) >= k_diverse:
            break
        candidates = [s for s in DIVERSE_REPRESENTATIVES.get(st, []) if s in manifest and s not in used]
        if not candidates:
            continue
        chosen = candidates[0]
        diverse_pick.append(chosen)
        used.add(chosen)

    # 拼装结果 (按 same+hot+diverse 顺序)
    out = []
    for s in same_pick + hot_pick + diverse_pick:
        m = manifest.get(s)
        if not m:
            continue
        out.append({
            "slug": s,
            "title": m["title"],
            "style": m["style"],
            "category": m.get("category", ""),
            "hook": ONE_LINER.get(s, m.get("title", "")[:14]),
        })
    return out[:12]


# ── A) <link> 引用 (浏览器并行加载, 比 inline 块小, 也能缓存) ──
WISHLIST_INJECT_HEAD_LINKS = """<!-- Wishlist UI: 共享 store + helpers (顶部 chip / 右下 FAB / 12 主题卡 / 搜专业) -->
<link rel="preload" href="/js/wishlist-store.js" as="script">
<link rel="preload" href="/js/ui-helpers.js" as="script">
<link rel="preload" href="/js/major-search.js" as="script">
"""

# ── B) <style> 块 (自带颜色 — 不依赖各主题 CSS var, 防止冲突) ──
WISHLIST_INJECT_STYLE = """
/* ─── Wishlist inject: 顶部 chip + 右下 FAB + 12 主题卡 ─── */
.wl-chip {
  position: fixed; top: 16px; right: 16px; z-index: 95;
  display: inline-flex; align-items: center; gap: 6px;
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
  font-size: 0.75rem; font-weight: 600;
  padding: 7px 12px; border-radius: 999px;
  background: rgba(250,250,247,0.95); color: #14110D;
  border: 1px solid #BFB9AB; cursor: pointer;
  backdrop-filter: saturate(180%) blur(8px);
  -webkit-backdrop-filter: saturate(180%) blur(8px);
  transition: all 180ms; letter-spacing: 0.02em;
  text-decoration: none; box-shadow: 0 2px 8px rgba(20,17,13,0.06);
}
.wl-chip:hover { background: #B8323A; color: #FAFAF7; border-color: #B8323A; transform: translateY(-1px); opacity: 1; }
.wl-chip[data-state="ready"] { background: #B8323A; color: #FAFAF7; border-color: #B8323A; }
.wl-chip .count { font-weight: 700; }
@media (max-width: 640px) {
  .wl-chip { top: 10px; right: 10px; font-size: 0.6875rem; padding: 6px 10px; }
}

.wl-fab {
  position: fixed; right: 24px; bottom: 24px; z-index: 9000;
  width: 56px; height: 56px; border-radius: 50%;
  background: #B8323A; color: #FAFAF7;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; box-shadow: 0 8px 24px rgba(20,17,13,0.16);
  cursor: pointer; border: none; transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
}
.wl-fab:hover { transform: translateY(-2px) scale(1.05); box-shadow: 0 12px 32px rgba(184,50,58,0.32); }
.wl-fab[data-state="added"] { background: #2F5F3E; }
@media (max-width: 640px) { .wl-fab { right: 16px; bottom: 16px; width: 50px; height: 50px; font-size: 1.25rem; } }

.wl-modal {
  position: fixed; right: 24px; bottom: 96px; z-index: 9001;
  width: min(320px, calc(100vw - 32px));
  background: #FAFAF7; color: #14110D;
  border: 1px solid #BFB9AB; border-radius: 12px; padding: 20px;
  box-shadow: 0 20px 48px rgba(20,17,13,0.24);
  transform: translateY(8px); opacity: 0; pointer-events: none;
  transition: all 220ms cubic-bezier(0.16, 1, 0.3, 1);
  font-family: 'Inter', 'PingFang SC', sans-serif;
}
.wl-modal[data-open="true"] { transform: translateY(0); opacity: 1; pointer-events: auto; }
.wl-modal .wl-mt { font-family: 'Source Han Serif SC', 'Songti SC', serif; font-size: 1.0625rem; font-weight: 600; margin-bottom: 4px; }
.wl-modal .wl-msub { font-size: 0.8125rem; color: #6F6A60; margin-bottom: 16px; }
.wl-modal .wl-stars { display: flex; gap: 4px; align-items: center; margin-bottom: 16px; }
.wl-modal .wl-stars button { font-size: 1.25rem; padding: 4px 2px; color: #BFB9AB; background: none; border: none; cursor: pointer; transition: color 120ms, transform 120ms; }
.wl-modal .wl-stars button.on { color: #B8323A; }
.wl-modal .wl-stars button:hover { transform: scale(1.12); }
.wl-modal .wl-act { display: flex; gap: 8px; }
.wl-modal .wl-act button { font: inherit; cursor: pointer; padding: 10px 14px; border-radius: 8px; font-weight: 600; font-size: 0.875rem; border: none; }
.wl-modal .wl-act .wl-ok { flex: 1; background: #14110D; color: #FAFAF7; }
.wl-modal .wl-act .wl-cancel { background: transparent; color: #6F6A60; border: 1px solid #E2DFD5; }
.wl-modal .wl-act .wl-ok:disabled { opacity: 0.4; cursor: not-allowed; }
@media (max-width: 640px) { .wl-modal { right: 16px; bottom: 80px; } }

.wl-toast {
  position: fixed; left: 50%; bottom: 96px; transform: translateX(-50%) translateY(20px);
  background: #14110D; color: #FAFAF7; padding: 10px 16px;
  border-radius: 8px; font-size: 0.8125rem; box-shadow: 0 8px 24px rgba(20,17,13,0.16);
  opacity: 0; pointer-events: none; transition: all 220ms; z-index: 9100;
  font-family: 'Inter', 'PingFang SC', sans-serif;
}
.wl-toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

/* ─── 心意框 CTA (在 wl-related 之上) — 看完专业必出 ─── */
.wl-decide {
  padding: 64px 0 32px;
  background: linear-gradient(180deg, #FAFAF7 0%, #F5F2EA 100%);
  border-top: 1px solid #E2DFD5;
  font-family: 'Inter', 'PingFang SC', sans-serif; color: #14110D;
  position: relative; z-index: 2;
}
.wl-decide .container { max-width: 880px; margin: 0 auto; padding: 0 32px; text-align: center; }
.wl-decide-eyebrow {
  font-family: 'JetBrains Mono', monospace; font-size: 0.6875rem;
  color: #B8323A; letter-spacing: 0.2em; text-transform: uppercase;
  margin-bottom: 12px; font-weight: 600;
}
.wl-decide-title {
  font-family: 'Source Han Serif SC', serif; font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 600; line-height: 1.3; margin-bottom: 32px; letter-spacing: -0.01em;
}
.wl-decide-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  max-width: 720px; margin: 0 auto;
}
.wl-decide-card {
  display: flex; flex-direction: column; align-items: flex-start; gap: 4px;
  padding: 28px 24px; background: #fff;
  border: 1.5px solid #E2DFD5; border-radius: 14px;
  text-decoration: none; color: #14110D;
  cursor: pointer; transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
  text-align: left; font: inherit;
}
.wl-decide-card:hover {
  transform: translateY(-3px);
  border-color: #BFB9AB;
  box-shadow: 0 12px 28px rgba(20,17,13,0.10);
  opacity: 1;
}
.wl-decide-card.primary {
  background: linear-gradient(180deg, #B8323A 0%, #9F2A31 100%);
  color: #FAFAF7; border-color: #B8323A;
}
.wl-decide-card.primary:hover { border-color: #9F2A31; box-shadow: 0 14px 32px rgba(184,50,58,0.28); }
.wl-decide-card .wl-decide-emoji { font-size: 1.875rem; line-height: 1; margin-bottom: 12px; }
.wl-decide-card .wl-decide-h { font-family: 'Source Han Serif SC', serif; font-size: 1.0625rem; font-weight: 700; }
.wl-decide-card .wl-decide-sub { font-size: 0.8125rem; opacity: 0.8; line-height: 1.5; margin-top: 4px; }
.wl-decide-card.primary .wl-decide-sub { color: #FAEAEB; opacity: 0.95; }
.wl-decide-card[data-state="added"] {
  background: linear-gradient(180deg, #2F5F3E 0%, #244E32 100%);
  border-color: #2F5F3E;
}
@media (max-width: 640px) {
  .wl-decide { padding: 48px 0 24px; }
  .wl-decide .container { padding: 0 16px; }
  .wl-decide-grid { grid-template-columns: 1fr; gap: 12px; }
  .wl-decide-card { padding: 22px 20px; }
}

/* ── 12 主题相关卡 (3×4) ───────────────── */
.wl-related {
  padding: 80px 0 64px;
  background: #F2F2EB; border-top: 1px solid #E2DFD5;
  font-family: 'Inter', 'PingFang SC', sans-serif; color: #14110D;
  position: relative; z-index: 2;
}
.wl-related .container { max-width: 1120px; margin: 0 auto; padding: 0 32px; }
.wl-related .wl-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 0.6875rem; color: #6F6A60; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 8px; }
.wl-related h2 { font-family: 'Source Han Serif SC', serif; font-size: clamp(1.5rem, 3vw, 2rem); font-weight: 600; line-height: 1.2; margin-bottom: 12px; letter-spacing: -0.01em; }
.wl-related .wl-lede { font-size: 0.9375rem; color: #6F6A60; max-width: 520px; line-height: 1.7; margin-bottom: 36px; }
.wl-related .wl-cta-bar { display: flex; gap: 12px; margin-bottom: 36px; flex-wrap: wrap; }
.wl-related .wl-cta-bar a {
  font-family: inherit; font-size: 0.875rem; font-weight: 600;
  padding: 10px 18px; border-radius: 8px; text-decoration: none; transition: all 180ms;
}
.wl-related .wl-cta-bar .wl-primary { background: #14110D; color: #FAFAF7; }
.wl-related .wl-cta-bar .wl-primary:hover { background: #B8323A; opacity: 1; }
.wl-related .wl-cta-bar .wl-ghost { background: transparent; color: #14110D; border: 1px solid #BFB9AB; }
.wl-related .wl-cta-bar .wl-ghost:hover { background: #FAFAF7; opacity: 1; }
.wl-related .wl-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
}
@media (max-width: 900px) { .wl-related .wl-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 640px) { .wl-related .wl-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; } .wl-related { padding: 56px 0 40px; } .wl-related .container { padding: 0 16px; } }
.wl-card {
  display: flex; flex-direction: column; gap: 6px;
  padding: 16px 16px 14px; background: #FAFAF7;
  border: 1px solid #E2DFD5; border-radius: 10px;
  text-decoration: none; color: #14110D;
  transition: all 200ms; min-height: 120px;
  position: relative; overflow: hidden;
}
.wl-card:hover { transform: translateY(-2px); border-color: #BFB9AB; box-shadow: 0 8px 20px rgba(20,17,13,0.08); opacity: 1; }
.wl-card .wl-badge {
  display: inline-block; font-family: 'JetBrains Mono', monospace;
  font-size: 0.5625rem; font-weight: 600; padding: 2px 6px; border-radius: 3px;
  letter-spacing: 0.1em; text-transform: uppercase; color: #FAFAF7;
  align-self: flex-start;
}
.wl-card.cs .wl-badge { background: #2A4A7F; }
.wl-card.finance .wl-badge { background: #5A4632; }
.wl-card.medicine .wl-badge { background: #8B2424; }
.wl-card.education .wl-badge { background: #5C7C4A; }
.wl-card.law .wl-badge { background: #3A3A3A; }
.wl-card.humanities .wl-badge { background: #6B4F35; }
.wl-card.sci .wl-badge { background: #1E5E72; }
.wl-card.eng .wl-badge { background: #5B5B47; }
.wl-card.administration .wl-badge { background: #4A4564; }
.wl-card.agri .wl-badge { background: #6B7A3F; }
.wl-card.arts .wl-badge { background: #8B3A62; }
.wl-card.gongan .wl-badge { background: #1F2A44; }
.wl-card.business .wl-badge { background: #6F5A3A; }
.wl-card .wl-title { font-family: 'Source Han Serif SC', serif; font-size: 0.9375rem; font-weight: 600; margin-top: 2px; line-height: 1.3; }
.wl-card .wl-hook { font-size: 0.75rem; color: #6F6A60; line-height: 1.5; margin-top: auto; }
.wl-related .wl-sec-tag { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.625rem; color: #6F6A60; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px; }
"""

# ── C) 12 主题卡 section HTML ─────────────────
STYLE_LABEL = {
    "cs": "计算机", "finance": "财经", "medicine": "医学", "education": "教育",
    "law": "法学", "humanities": "人文", "sci": "理科", "eng": "工科",
    "administration": "公管", "agri": "农学", "arts": "艺术",
    "gongan": "公安", "business": "工商",
}


def render_related_themes_section(slug: str, manifest_path: str | Path) -> str:
    """生成 心意框 CTA + 12 主题卡 section. manifest_path 是 manifest.json 绝对路径.

    ✅ Day 5 Bug 3 fix (2026-06-18): 当 _pick_related 返回空 (slug 不在 manifest 或
    manifest 缺数据) 时, 仍渲染一个最小 fallback section (wishlist CTA + 返回链接),
    保证"页面结束就死胡同"问题 100% 兜底. 旧行为是返回 "", 170/338 页底部没有任何出口.
    """
    try:
        manifest = _load_manifest(manifest_path)
        picks = _pick_related(slug, manifest)
    except Exception:
        manifest, picks = {}, []

    current = manifest.get(slug, {})
    cur_title = current.get("title", "这个专业")

    # ── Fallback 1: manifest 没该 slug (新专业未入册) ──
    if not picks and not current:
        return f"""
<!-- 心意框 fallback (slug 不在 manifest: {slug}) -->
<section class="wl-decide" id="wl-decide">
  <div class="container">
    <div class="wl-decide-eyebrow">看完了, 怎么想?</div>
    <h2 class="wl-decide-title">「{cur_title}」<br>是你愿意学 4 年的方向吗?</h2>
    <div class="wl-decide-grid">
      <button class="wl-decide-card primary" data-act="add">
        <span class="wl-decide-emoji">🌟</span>
        <span class="wl-decide-h">心仪 · 加入心愿单</span>
        <span class="wl-decide-sub">打 1-5 颗星, 凑齐 4 个跑志愿推荐</span>
      </button>
      <a class="wl-decide-card" href="/majors.html">
        <span class="wl-decide-emoji">📚</span>
        <span class="wl-decide-h">返回专业目录</span>
        <span class="wl-decide-sub">浏览全部 365 个精品专业报告</span>
      </a>
    </div>
  </div>
</section>

<!-- 底部兜底导航 (Bug 3 L3 死链修复) -->
<section class="wl-related" id="wl-related">
  <div class="container">
    <div class="wl-eyebrow">More to explore</div>
    <h2>没找到想看的? 搜一下别的专业</h2>
    <p class="wl-lede">目前精品报告覆盖工科 / 医学 / 财经 / 法律 / 教育 / 艺术 / 农学 等主流方向, 持续扩充中. 暂未覆盖? 留邮箱等更新.</p>
    <div class="wl-chat-host" id="wl-chat-host" style="margin-bottom: 32px;"></div>
    <div class="wl-cta-bar">
      <a class="wl-primary" href="/majors.html">📚 浏览全部 365 个专业 →</a>
      <a class="wl-ghost" href="/wishlist.html">🎒 我的心愿单</a>
      <a class="wl-ghost" href="/preferences.html">📝 直接填偏好</a>
    </div>
  </div>
</section>
"""

    # ── Fallback 2: slug 在 manifest 但 _pick_related 找不到相关 (极少见) ──
    if not picks:
        return f"""
<!-- 心意框 (slug 在 manifest 但无相关推荐: {slug}) -->
<section class="wl-decide" id="wl-decide">
  <div class="container">
    <div class="wl-decide-eyebrow">看完了, 怎么想?</div>
    <h2 class="wl-decide-title">「{cur_title}」<br>是你愿意学 4 年的方向吗?</h2>
    <div class="wl-decide-grid">
      <button class="wl-decide-card primary" data-act="add">
        <span class="wl-decide-emoji">🌟</span>
        <span class="wl-decide-h">心仪 · 加入心愿单</span>
        <span class="wl-decide-sub">打 1-5 颗星, 凑齐 4 个跑志愿推荐</span>
      </button>
      <a class="wl-decide-card" href="/majors.html">
        <span class="wl-decide-emoji">🔄</span>
        <span class="wl-decide-h">再看看别的专业</span>
        <span class="wl-decide-sub">下方浏览全部 365 个精品专业</span>
      </a>
    </div>
  </div>
</section>

<section class="wl-related" id="wl-related">
  <div class="container">
    <div class="wl-eyebrow">More to explore</div>
    <h2>没找到想看的? 搜一下别的专业</h2>
    <p class="wl-lede">目前精品报告覆盖工科 / 医学 / 财经 / 法律 / 教育 / 艺术 / 农学 等主流方向, 持续扩充中.</p>
    <div class="wl-chat-host" id="wl-chat-host" style="margin-bottom: 32px;"></div>
    <div class="wl-cta-bar">
      <a class="wl-primary" href="/majors.html">📚 浏览全部 365 个专业 →</a>
      <a class="wl-ghost" href="/wishlist.html">🎒 我的心愿单</a>
      <a class="wl-ghost" href="/preferences.html">📝 直接填偏好</a>
    </div>
  </div>
</section>
"""

    current = manifest.get(slug, {})
    cur_title = current.get("title", "这个专业")

    # 分 3 段渲染 (same/hot/diverse 视觉一致, 但用 tag 标识来源)
    cards_html = []
    for i, p in enumerate(picks):
        tag = "同主题" if i < 4 else ("热门" if i < 8 else "跨界")
        label = STYLE_LABEL.get(p["style"], p["style"])
        cards_html.append(
            f'      <a class="wl-card {p["style"]}" href="/{p["slug"]}.html" data-tag="{tag}">'
            f'<span class="wl-badge">{label}</span>'
            f'<span class="wl-title">{p["title"]}</span>'
            f'<span class="wl-hook">{p["hook"]}</span>'
            f'</a>'
        )
    cards_str = "\n".join(cards_html)
    return f"""
<!-- 心意框 — 看完一个专业后必出的明显 CTA (替代旧"关联志愿"section) -->
<section class="wl-decide" id="wl-decide">
  <div class="container">
    <div class="wl-decide-eyebrow">看完了, 怎么想?</div>
    <h2 class="wl-decide-title">「{cur_title}」<br>是你愿意学 4 年的方向吗?</h2>
    <div class="wl-decide-grid">
      <button class="wl-decide-card primary" data-act="add">
        <span class="wl-decide-emoji">🌟</span>
        <span class="wl-decide-h">心仪 · 加入心愿单</span>
        <span class="wl-decide-sub">打 1-5 颗星, 凑齐 4 个跑志愿推荐</span>
      </button>
      <a class="wl-decide-card" href="#wl-related">
        <span class="wl-decide-emoji">🔄</span>
        <span class="wl-decide-h">再看看别的专业</span>
        <span class="wl-decide-sub">下方搜其他专业 / 浏览 12 个相关主题</span>
      </a>
    </div>
  </div>
</section>

<section class="wl-related" id="wl-related">
  <div class="container">
    <div class="wl-eyebrow">More to explore</div>
    <h2>没找到想看的? 搜一下别的专业</h2>
    <p class="wl-lede">目前精品报告覆盖工科 / 医学 / 财经 / 法律 / 教育 / 艺术 / 农学 等主流方向, 持续扩充中. 暂未覆盖? 留邮箱等更新.</p>
    <div class="wl-chat-host" id="wl-chat-host" style="margin-bottom: 32px;"></div>

    <div class="wl-eyebrow" style="margin-top: 8px;">Related majors · 同主题 / 热门 / 跨界</div>
    <h3 style="font-family: 'Source Han Serif SC', serif; font-size: 1.25rem; font-weight: 600; margin-bottom: 12px; letter-spacing: -0.01em;">继续逛 12 个相关主题</h3>
    <p class="wl-lede">把感兴趣的攒到心愿单, 凑齐 4 个就能跑湖北 1008 所院校 + 4 年位次推荐.</p>
    <div class="wl-cta-bar">
      <a class="wl-primary" href="/#majors">📚 浏览精品报告 →</a>
      <a class="wl-ghost" href="/wishlist.html">🎒 我的心愿单</a>
      <a class="wl-ghost" href="/preferences.html">📝 直接填偏好</a>
    </div>
    <div class="wl-grid">
{cards_str}
    </div>
  </div>
</section>
"""


# ── D) FAB 挂载脚本 (每页注入, 含本页 slug/title/style/category) ──
def build_wishlist_init_js(slug: str, title: str, style: str, category: str = "") -> str:
    """生成 chip + FAB 启动脚本. 引用外部 wishlist-store.js + ui-helpers.js."""
    # 防止 ' 和 " 注入
    def esc(s: str) -> str:
        return (s or "").replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")

    s_slug = esc(slug); s_title = esc(title); s_style = esc(style); s_cat = esc(category)
    return f"""
<!-- Wishlist UI: 共享 store + helpers + 本页 chip/FAB 启动 + 搜专业 chat -->
<script src="/js/wishlist-store.js"></script>
<script src="/js/ui-helpers.js"></script>
<script src="/js/major-search.js"></script>
<script>
(function () {{
  "use strict";
  if (!window.WishlistStore || !window.UIHelpers) return;
  var META = {{ slug: '{s_slug}', title: '{s_title}', style: '{s_style}', category: '{s_cat}' }};

  // 0) 12 主题卡上方的 chat 栏 — 让用户从一个专业页跳到另一个
  if (window.MajorSearch) {{
    var chatHost = document.getElementById('wl-chat-host');
    if (chatHost) {{
      window.MajorSearch.mountChat(chatHost, {{
        size: 'compact',
        placeholder: '搜其他专业…  比如「编程」「医生」「考公」「金融」',
      }});
    }}
  }}

  // 1) 顶部右上角 chip
  var chip = document.createElement('a');
  chip.className = 'wl-chip';
  chip.href = '/wishlist.html';
  chip.setAttribute('aria-label', '心愿单');
  document.body.appendChild(chip);
  function paintChip(items) {{
    var c = items.length;
    chip.innerHTML = '<span aria-hidden="true">🎒</span> <span>心愿单</span> <span class="count">' + c + '/6</span> <span class="arrow">→</span>';
    if (c >= 4) chip.setAttribute('data-state', 'ready'); else chip.removeAttribute('data-state');
  }}
  window.WishlistStore.subscribe(paintChip);

  // 2) 右下 FAB + 弹窗 (复用 UIHelpers.mountWishlistFab 的样式但用本注入的类名)
  var fab = document.createElement('button');
  fab.className = 'wl-fab'; fab.type = 'button';
  fab.setAttribute('aria-label', '加入心愿单');
  fab.textContent = '⭐';
  document.body.appendChild(fab);

  var modal = document.createElement('div');
  modal.className = 'wl-modal';
  modal.setAttribute('role', 'dialog');
  modal.innerHTML =
    '<div class="wl-mt">' + META.title + '</div>' +
    '<div class="wl-msub">给这个专业评几颗星 (1-5)</div>' +
    '<div class="wl-stars"></div>' +
    '<div class="wl-act"><button class="wl-cancel">取消</button><button class="wl-ok">加入心愿单</button></div>';
  document.body.appendChild(modal);

  var current = window.WishlistStore.getScore(META.slug) || 4;
  var starsHolder = modal.querySelector('.wl-stars');
  for (var i = 1; i <= 5; i++) (function (v) {{
    var b = document.createElement('button');
    b.type = 'button'; b.textContent = '★'; b.dataset.v = String(v);
    if (v <= current) b.classList.add('on');
    b.addEventListener('click', function () {{
      current = v;
      starsHolder.querySelectorAll('button').forEach(function (bb) {{
        bb.classList.toggle('on', parseInt(bb.dataset.v, 10) <= current);
      }});
    }});
    starsHolder.appendChild(b);
  }})(i);

  function syncFab() {{
    var inList = window.WishlistStore.has(META.slug);
    var full = window.WishlistStore.isFull();
    fab.setAttribute('data-state', inList ? 'added' : (full ? 'full' : 'idle'));
    fab.textContent = inList ? '✓' : (full ? '🎒' : '⭐');
    var ok = modal.querySelector('.wl-ok');
    ok.textContent = inList ? '保存调整' : '加入心愿单';
    modal.querySelector('.wl-msub').textContent = inList ? '已加入心愿单, 可调整星级' : (full ? '心愿单已满 6 个 (去管理)' : '给这个专业评几颗星 (1-5)');
    ok.disabled = !inList && full;
    // 同步「心意框」主按钮
    var decideBtn = document.querySelector('.wl-decide-card[data-act="add"]');
    if (decideBtn) {{
      decideBtn.setAttribute('data-state', inList ? 'added' : 'idle');
      var dh = decideBtn.querySelector('.wl-decide-h');
      var ds = decideBtn.querySelector('.wl-decide-sub');
      var de = decideBtn.querySelector('.wl-decide-emoji');
      if (dh && ds && de) {{
        if (inList) {{
          de.textContent = '✓';
          dh.textContent = '已加入心愿单 · 调整星级';
          ds.textContent = '当前 ' + (window.WishlistStore.getScore(META.slug) || 4) + ' 颗星, 点击修改';
        }} else if (full) {{
          de.textContent = '🎒';
          dh.textContent = '心愿单已满 6 个';
          ds.textContent = '先去心愿单页删一个';
        }} else {{
          de.textContent = '🌟';
          dh.textContent = '心仪 · 加入心愿单';
          ds.textContent = '打 1-5 颗星, 凑齐 4 个跑志愿推荐';
        }}
      }}
    }}
  }}
  syncFab();

  function openModal() {{
    current = window.WishlistStore.getScore(META.slug) || 4;
    starsHolder.querySelectorAll('button').forEach(function (bb) {{
      bb.classList.toggle('on', parseInt(bb.dataset.v, 10) <= current);
    }});
    modal.setAttribute('data-open', 'true');
  }}
  function closeModal() {{ modal.setAttribute('data-open', 'false'); }}

  fab.addEventListener('click', function (e) {{
    e.stopPropagation();
    if (window.WishlistStore.isFull() && !window.WishlistStore.has(META.slug)) {{
      window.UIHelpers.toast('心愿单已满 6 个, 去管理 → /wishlist.html');
      return;
    }}
    if (modal.getAttribute('data-open') === 'true') closeModal(); else openModal();
  }});

  // 「心意框」主按钮 → 直接触发 FAB modal
  var decideBtn = document.querySelector('.wl-decide-card[data-act="add"]');
  if (decideBtn) {{
    decideBtn.addEventListener('click', function (e) {{
      e.preventDefault();
      e.stopPropagation();
      if (window.WishlistStore.isFull() && !window.WishlistStore.has(META.slug)) {{
        window.UIHelpers.toast('心愿单已满 6 个, 去管理 → /wishlist.html');
        return;
      }}
      openModal();
    }});
  }}
  modal.querySelector('.wl-cancel').addEventListener('click', closeModal);
  modal.querySelector('.wl-ok').addEventListener('click', function () {{
    var res = window.WishlistStore.upsert({{ slug: META.slug, title: META.title, style: META.style, category: META.category, score: current }});
    if (!res.ok && res.reason === 'full') {{ window.UIHelpers.toast('心愿单已满 6 个'); return; }}
    window.UIHelpers.toast(res.updated ? '已更新星级' : '已加入心愿单');
    closeModal();
  }});
  document.addEventListener('click', function (e) {{
    if (modal.getAttribute('data-open') !== 'true') return;
    if (modal.contains(e.target) || fab.contains(e.target)) return;
    closeModal();
  }});
  document.addEventListener('keydown', function (e) {{
    if (e.key === 'Escape' && modal.getAttribute('data-open') === 'true') closeModal();
  }});
  window.WishlistStore.subscribe(syncFab);
}})();
</script>
"""
