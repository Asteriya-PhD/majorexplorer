/* ====================================================================
 * major-search.js — chat 风专业搜索路由器
 *
 * 设计原则: 项目核心是"专业介绍系统", 不是"志愿推荐工具".
 * 18 岁高中生对专业一无所知, 第一步必须是"看清专业".
 * 本组件让用户在主页 / 各专业页底部用自然语言找到精品专业页.
 *
 * 公开 API (window.MajorSearch):
 *   mountChat(container, opts) → 挂载大 chat 输入框 + 下拉建议
 *      opts.placeholder  自定义 placeholder
 *      opts.chips        快速主题 chip 列表 (默认 8 个)
 *      opts.size         "hero" (主页大版) | "compact" (专业页底)
 *
 *   search(query)        → 返回匹配的 majors [{slug, title, style, score, why}]
 *
 *   loadManifest()       → 加载 manifest, 必须先 await
 *
 * 关键词词表 (中 + 英 + 同义词) → slug 映射;
 * 匹配规则: title / category / tags / 别名 子串命中 → 加分.
 * ==================================================================== */

(function (global) {
  "use strict";

  let _manifest = null;
  let _loadPromise = null;

  // ── 关键词 / 同义词 → slug 列表 (高频项) ────────────────────
  // 同义词加分: title 包含 = 5, tag 包含 = 3, category 包含 = 2, 同义词 = 4
  const SYNONYMS = {
    // 计算机 / IT
    "编程": ["computer-science", "software-engineering"],
    "码农": ["computer-science", "software-engineering"],
    "程序员": ["computer-science", "software-engineering"],
    "代码": ["computer-science", "software-engineering"],
    "coding": ["computer-science", "software-engineering"],
    "计算机": ["computer-science", "software-engineering", "data-science-big-data"],
    "软件": ["software-engineering", "computer-science"],
    "ai": ["artificial-intelligence", "intelligent-science-technology", "data-science-big-data"],
    "人工智能": ["artificial-intelligence", "intelligent-science-technology"],
    "机器学习": ["artificial-intelligence", "data-science-big-data"],
    "数据": ["data-science-big-data", "artificial-intelligence"],
    "大数据": ["data-science-big-data"],
    "网络安全": ["cybersecurity"],
    "黑客": ["cybersecurity"],
    "通信": ["communication-engineering", "electronic-information-engineering"],
    "5g": ["communication-engineering"],
    "电子": ["electronic-information-engineering", "microelectronics", "integrated-circuit-design"],
    "芯片": ["integrated-circuit-design", "microelectronics", "electronic-information-engineering"],
    "半导体": ["microelectronics", "integrated-circuit-design", "materials-science-engineering"],
    "电气": ["electrical-engineering-automation"],
    "国家电网": ["electrical-engineering-automation"],
    "自动化": ["automation", "intelligent-science-technology"],
    "控制": ["automation"],
    "嵌入式": ["automation", "electronic-information-engineering"],
    "机器人": ["intelligent-science-technology", "automation"],

    // 工程
    "土木": ["civil-engineering"],
    "建筑": ["architecture", "civil-engineering"],
    "盖楼": ["civil-engineering", "architecture"],
    "机械": ["mechanical-engineering", "vehicle-engineering"],
    "汽车": ["vehicle-engineering", "mechanical-engineering"],
    "新能源车": ["vehicle-engineering"],
    "比亚迪": ["vehicle-engineering"],
    "材料": ["materials-science-engineering"],
    "化工": ["chemical-engineering"],
    "化学工程": ["chemical-engineering"],
    "食品": ["food-science-engineering"],
    "航空": ["aircraft-design-engineering"],
    "飞机": ["aircraft-design-engineering"],
    "航天": ["aircraft-design-engineering"],

    // 医学
    "医生": ["clinical-medicine", "anesthesiology", "stomatology"],
    "临床": ["clinical-medicine"],
    "麻醉": ["anesthesiology"],
    "口腔": ["stomatology"],
    "牙医": ["stomatology"],
    "中医": ["traditional-chinese-medicine"],
    "药学": ["pharmacy"],
    "药剂": ["pharmacy"],
    "预防医学": ["preventive-medicine"],
    "疾控": ["preventive-medicine"],
    "公共卫生": ["preventive-medicine"],

    // 财经
    "金融": ["finance", "economics", "international-economics-trade"],
    "投行": ["finance"],
    "经济": ["economics", "finance", "international-economics-trade"],
    "经济学": ["economics"],
    "会计": ["accounting", "financial-management"],
    "cpa": ["accounting", "financial-management"],
    "管理": ["business-administration", "public-administration", "financial-management"],
    "工商管理": ["business-administration"],
    "国际贸易": ["international-economics-trade"],
    "外贸": ["international-economics-trade"],

    // 法律
    "法律": ["law"],
    "法学": ["law"],
    "法考": ["law"],
    // "律师" 已迁移到 INTENT_SYNONYMS (职业意图词 → 走 0 命中同义词推荐)

    // 教育 + 人文 + 设计
    // "教师"/"老师" 已迁移到 INTENT_SYNONYMS (职业意图词)
    "师范": ["education", "english", "chinese-language-literature"],
    // "公费师范" 已迁移到 INTENT_GUIDANCE (政策引导)
    "心理": ["psychology", "applied-psychology"],
    "心理学": ["psychology", "applied-psychology"],
    "心理咨询": ["psychology", "applied-psychology"],
    // "心理咨询师" 已迁移到 INTENT_SYNONYMS (职业意图词)
    "新闻": ["journalism-communication"],
    "传媒": ["journalism-communication"],
    // "记者" 已迁移到 INTENT_SYNONYMS (职业意图词)
    "短视频": ["journalism-communication", "digital-media-arts"],
    "汉语言": ["chinese-language-literature"],
    "中文": ["chinese-language-literature"],
    "英语": ["english"],
    "翻译": ["english"],
    "历史": ["history", "archaeology"],
    "考古": ["archaeology", "history"],
    "哲学": ["philosophy"],
    "工业设计": ["industrial-design"],

    // 公管 / 图情
    // "公务员"/"考公" 已迁移到 INTENT_SYNONYMS (职业意图词)
    "行政管理": ["public-administration"],
    "图书馆": ["library-science"],
    "档案": ["library-science", "information-management-systems"],
    "信管": ["information-management-systems"],

    // 理科
    "数学": ["mathematics"],
    "物理": ["physics"],
    "化学": ["chemistry", "chemical-engineering", "materials-science-engineering"],
    "大气": ["atmospheric-science"],
    "气象": ["atmospheric-science"],

    // 农学
    "农学": ["agronomy", "horticulture"],
    "种地": ["agronomy", "horticulture"],
    "园林": ["landscape-architecture"],
    "园艺": ["horticulture"],
    "林业": ["forestry"],
    "林学": ["forestry"],
    "动物": ["animal-science"],
    "兽医": ["animal-science"],

    // 艺术
    "美术": ["fine-arts"],
    "画画": ["fine-arts", "visual-communication-design", "animation"],
    "美院": ["fine-arts", "visual-communication-design", "environmental-design", "animation"],
    "设计": ["visual-communication-design", "environmental-design", "industrial-design", "digital-media-arts"],
    "ui": ["visual-communication-design", "digital-media-arts"],
    "动画": ["animation"],
    "游戏": ["digital-media-arts", "animation"],
    "影视": ["digital-media-arts", "animation"],
    "数字媒体": ["digital-media-arts"],
    "环艺": ["environmental-design"],
    "室内设计": ["environmental-design"],
  };

  // 主页 chat 栏下方默认快捷 chip (2026-06-25 改造: 全部改为本科专业名, 不再引导搜职业/政策)
// 选 8 个: 覆盖理工文法商医艺农 7 门类 + 用户最高频搜索意图
  const DEFAULT_CHIPS = [
    { label: "🧑‍💻 计算机科学与技术", q: "计算机科学与技术" },
    { label: "🩺 临床医学", q: "临床医学" },
    { label: "⚖️ 法学", q: "法学" },
    { label: "💰 金融学", q: "金融学" },
    { label: "📚 汉语言文学", q: "汉语言文学" },
    { label: "🤖 人工智能", q: "人工智能" },
    { label: "🔬 物理学", q: "物理学" },
    { label: "🎨 视觉传达设计", q: "视觉传达设计" },
  ];

  function loadManifest() {
    if (_manifest) return Promise.resolve(_manifest);
    if (_loadPromise) return _loadPromise;
    _loadPromise = fetch("/data/manifest.json").then((r) => r.json()).then((m) => {
      _manifest = m;
      return m;
    });
    return _loadPromise;
  }

  // 同义词找 slug
  function _synonymHits(q) {
    const lower = q.toLowerCase().trim();
    if (!lower) return [];
    const out = new Set();
    for (const key of Object.keys(SYNONYMS)) {
      // 严匹配: 仅当 key 完整出现在 q 开头(后跟空/学/类/方向/工程 等限定)
      // 避免"天体物理"包含"物理"这种 false positive
      if (lower === key) {
        SYNONYMS[key].forEach((s) => out.add(s));
      } else if (lower.startsWith(key)) {
        const suffix = lower.slice(key.length);
        // 限定词白名单: 学/类/方向/工程/技术/专业/系/学院/学专业/专业方向
        if (suffix === "" || /^(学|类|方向|工程|技术|专业|系|学院|学专业|专业方向)$/.test(suffix)) {
          SYNONYMS[key].forEach((s) => out.add(s));
        }
      }
    }
    return Array.from(out);
  }

  // 主搜索: 在 manifest 内做 title / category / tag 子串匹配, 加同义词命中
  function search(query) {
    if (!_manifest) return [];
    const q = (query || "").trim();
    if (!q) return [];
    const lower = q.toLowerCase();
    const majors = _manifest.majors || [];

    // 同义词词典命中的 slug 加 6 分基础分
    const synSet = new Set(_synonymHits(q));

    const scored = [];
    for (const m of majors) {
      let s = 0;
      const titleL = (m.title || "").toLowerCase();
      const catL = (m.category || "").toLowerCase();
      const tagsL = (m.tags || []).map((t) => (t || "").toLowerCase());

      // title 完全相等 = 100
      if (titleL === lower) s += 100;
      // title 子串 = 8 (双向)
      else if (titleL.includes(lower) || (lower.length >= 2 && lower.includes(titleL))) s += 8;

      // category 子串 = 3
      if (catL.includes(lower)) s += 3;
      // tag 子串 = 4
      tagsL.forEach((t) => { if (t && (t.includes(lower) || lower.includes(t))) s += 4; });

      // 同义词命中 = 6
      if (synSet.has(m.slug)) s += 6;

      if (s > 0) scored.push({
        slug: m.slug, title: m.title, style: m.style, category: m.category,
        tags: (m.tags || []).slice(0, 3),
        score: s,
      });
    }
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, 8);
  }

  // ── CSS (整块自带, 不依赖 theme) ─────────────────
  const STYLE = `
.ms-shell { position: relative; max-width: 720px; margin: 0 auto; }
.ms-shell.compact { max-width: 640px; }
.ms-bar {
  display: flex; align-items: center; gap: 0;
  background: #fff; border: 1px solid #BFB9AB; border-radius: 14px;
  padding: 8px 8px 8px 20px; transition: all 200ms;
  box-shadow: 0 2px 8px rgba(20,17,13,0.04);
}
.ms-bar:focus-within {
  border-color: #B8323A; box-shadow: 0 0 0 4px rgba(184,50,58,0.10), 0 4px 14px rgba(20,17,13,0.08);
}
.ms-input {
  flex: 1; border: none; outline: none; background: transparent;
  font: inherit; font-size: 1.0625rem; color: #14110D; padding: 12px 0;
  font-family: 'Inter', 'PingFang SC', sans-serif;
}
.ms-input::placeholder { color: #BFB9AB; }
.ms-shell.compact .ms-input { font-size: 0.9375rem; padding: 8px 0; }
.ms-send {
  display: inline-flex; align-items: center; justify-content: center;
  gap: 6px;
  height: 40px; padding: 0 16px; border-radius: 10px;
  background: #14110D; color: #FAFAF7; border: none; cursor: pointer;
  transition: background 180ms, transform 180ms;
  font-size: 0.9375rem; font-weight: 600; white-space: nowrap;
}
.ms-send-arrow { font-size: 1.0625rem; transition: transform 180ms; }
.ms-send:hover { background: #B8323A; transform: translateY(-1px); }
.ms-send:hover .ms-send-arrow { transform: translateX(2px); }
.ms-send:disabled { background: #BFB9AB; cursor: not-allowed; transform: none; }
.ms-send:disabled .ms-send-arrow { transform: none; }
.ms-shell.compact .ms-send { height: 36px; padding: 0 12px; font-size: 0.875rem; }

.ms-chips {
  display: flex; flex-wrap: nowrap; gap: 8px;
  margin-top: 22px; justify-content: flex-start;
  max-height: 200px; opacity: 1;
  transition: max-height 240ms ease, opacity 180ms ease, margin-top 180ms ease;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  /* hero mode 下让 chips 单行, 节省页面高度 */
}
.ms-chips::-webkit-scrollbar { display: none; }
.ms-chip { flex-shrink: 0; }
/* 移动端窄屏允许换行 */
@media (max-width: 640px) {
  .ms-chips { flex-wrap: wrap; overflow-x: visible; justify-content: center; }
}
.ms-shell.compact .ms-chips { justify-content: flex-start; flex-wrap: nowrap; }
/* 下拉打开时折叠 chips, 让 results 紧贴 input 下方 */
.ms-shell[data-active="true"] .ms-chips {
  max-height: 0; opacity: 0; margin-top: 0; pointer-events: none;
}
.ms-chip {
  display: inline-block;
  font-size: 0.8125rem; padding: 7px 12px; border-radius: 999px;
  background: #FAFAF7; color: #14110D; border: 1px solid #E2DFD5;
  cursor: pointer; transition: all 160ms;
  font-family: 'Inter', 'PingFang SC', sans-serif;
  text-decoration: none;
  line-height: 1.4;
  white-space: nowrap;
}
.ms-chip:hover { border-color: #14110D; transform: translateY(-1px); text-decoration: none; }
.ms-chip:visited { color: #14110D; }

.ms-results {
  position: absolute; top: calc(100% + 8px); left: 0; right: 0;
  background: #fff; border: 1px solid #BFB9AB; border-radius: 12px;
  box-shadow: 0 12px 32px rgba(20,17,13,0.16);
  max-height: 480px; overflow-y: auto;
  z-index: 50; padding: 8px 0;
  opacity: 0; transform: translateY(-4px); pointer-events: none;
  transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
}
/* 下拉打开时 z-index 拔高, 防止被 chips 区域以外的元素覆盖 */
.ms-results.open { opacity: 1; transform: translateY(0); pointer-events: auto; z-index: 90; }
.ms-result {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 18px; cursor: pointer;
  border-bottom: 1px solid #F2F2EB;
  transition: background 140ms; text-decoration: none; color: #14110D;
}
.ms-result:last-child { border-bottom: none; }
.ms-result:hover, .ms-result.active { background: #F2F2EB; opacity: 1; }
.ms-result .ms-r-mark {
  font-family: 'JetBrains Mono', monospace; font-size: 0.5625rem;
  font-weight: 600; padding: 2px 6px; border-radius: 3px;
  color: #FAFAF7; letter-spacing: 0.1em;
}
.ms-result.cs .ms-r-mark { background: #2A4A7F; }
.ms-result.finance .ms-r-mark { background: #5A4632; }
.ms-result.medicine .ms-r-mark { background: #8B2424; }
.ms-result.education .ms-r-mark { background: #5C7C4A; }
.ms-result.law .ms-r-mark { background: #3A3A3A; }
.ms-result.humanities .ms-r-mark { background: #6B4F35; }
.ms-result.sci .ms-r-mark { background: #1E5E72; }
.ms-result.eng .ms-r-mark { background: #5B5B47; }
.ms-result.administration .ms-r-mark { background: #4A4564; }
.ms-result.agri .ms-r-mark { background: #6B7A3F; }
.ms-result.arts .ms-r-mark { background: #8B3A62; }
.ms-result .ms-r-text { flex: 1; min-width: 0; }
.ms-result .ms-r-title { font-family: 'Source Han Serif SC', serif; font-size: 0.9375rem; font-weight: 600; }
.ms-result .ms-r-cat { font-size: 0.75rem; color: #6F6A60; margin-top: 2px; }
.ms-result .ms-r-arr { color: #BFB9AB; font-size: 0.875rem; }

.ms-empty {
  padding: 24px 20px; text-align: center;
  font-size: 0.875rem; color: #6F6A60; line-height: 1.6;
}
.ms-empty strong { color: #14110D; }
.ms-empty .ms-suggest {
  display: inline-block; margin-top: 8px;
  font-size: 0.8125rem; color: #B8323A; font-weight: 600;
}
`;

  function _injectStyle() {
    if (document.getElementById("ms-style")) return;
    const s = document.createElement("style");
    s.id = "ms-style";
    s.textContent = STYLE;
    document.head.appendChild(s);
  }

  function mountChat(container, opts) {
    opts = opts || {};
    if (!container) return null;
    _injectStyle();

    const compact = opts.size === "compact";
    const placeholder = opts.placeholder ||
      (compact ? "搜其他专业 (比如「计算机」「临床医学」「金融学」)…" : "想了解什么专业?  比如「计算机」「临床医学」「法学」…");
    const chips = opts.chips || DEFAULT_CHIPS;

    const shell = document.createElement("div");
    shell.className = "ms-shell" + (compact ? " compact" : "");
    shell.innerHTML = [
      '<form class="ms-bar" autocomplete="off" role="search">',
      '  <input class="ms-input" type="text" placeholder="' + placeholder.replace(/"/g, "&quot;") + '" aria-label="搜索专业">',
      '  <button class="ms-send" type="submit" aria-label="搜索专业">搜专业 <span class="ms-send-arrow" aria-hidden="true">→</span></button>',
      '</form>',
      '<div class="ms-chips" role="list"></div>',
      '<div class="ms-results" role="listbox"></div>',
    ].join("");
    container.appendChild(shell);

    const form = shell.querySelector("form.ms-bar");
    const input = shell.querySelector(".ms-input");
    const send = shell.querySelector(".ms-send");
    const chipBar = shell.querySelector(".ms-chips");
    const results = shell.querySelector(".ms-results");

    // chips: 用 <a> 链接到 /search.html?cat=<keyword>, 让主搜索页处理 (语义 + 可分享 + 可爬)
    chips.forEach((c) => {
      const a = document.createElement("a");
      a.href = "/search.html?cat=" + encodeURIComponent(c.q);
      a.className = "ms-chip";
      a.textContent = c.label;
      a.setAttribute("role", "button");
      a.addEventListener("click", (e) => {
        // 允许 Cmd/Ctrl/middle-click 新窗口, 其他情况即时填入 input 并触发搜索
        if (e.metaKey || e.ctrlKey || e.button === 1) return;
        e.preventDefault();
        input.value = c.q; doSearch(); input.focus();
      });
      chipBar.appendChild(a);
    });

    function _escapeHtml(s) {
      return (s == null ? "" : String(s))
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }

    function _styleLabel(style) {
      const M = { cs: "计算机", finance: "财经", medicine: "医学", education: "教育", law: "法学", humanities: "人文", sci: "理科", eng: "工科", administration: "公管", agri: "农学", arts: "艺术" };
      return M[style] || style;
    }

    function _bindDropdownCTA(query) {
      const card = results.querySelector(".ms-no-result");
      if (!card) return;
      const reportBtn = card.querySelector(".ms-report-btn");
      const statusEl = card.querySelector(".nrr-synth-status");

      if (reportBtn) reportBtn.addEventListener("click", async () => {
        reportBtn.disabled = true;
        const oldLabel = reportBtn.textContent;
        reportBtn.textContent = "发送中...";
        try {
          const r = await fetch("/api/report", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type: "missing-major", category: "want", name: query, source: "pc" }),
          });
          const d = await r.json().catch(() => ({}));
          if (r.ok && d.ok) {
            statusEl.textContent = "✅ 已上报, 我们会优先收录, 谢谢!";
            reportBtn.textContent = "✓ 已收到";
          } else {
            throw new Error(d.error || `HTTP ${r.status}`);
          }
        } catch (e) {
          statusEl.textContent = `❌ ${e.message || "提交失败, 请稍后重试"}`;
          reportBtn.disabled = false;
          reportBtn.textContent = oldLabel;
          console.error("[major-search] report failed", e);
        }
      });
    }

    // ── 0 命中引导用同义词/政策词典 (2026-06-25 新增) ──
  // 跟 pc-search.js INTENT_SYNONYMS 一致; 放在 IIFE 顶部, _render 调用.
  const INTENT_SYNONYMS = {
    "医生":   ["clinical-medicine","stomatology","traditional-chinese-medicine","nursing","basic-medicine","preventive-medicine"],
    "医师":   ["clinical-medicine","stomatology","traditional-chinese-medicine","psychiatry"],
    "护士":   ["nursing","midwifery"],
    "考公":   ["law","public-administration","chinese-language-literature","accounting","financial-management","economics"],
    "公务员": ["law","public-administration","chinese-language-literature","accounting","financial-management","economics"],
    "教师":   ["chinese-language-literature","mathematics","english","physics","history","pedagogy","preschool-education"],
    "老师":   ["chinese-language-literature","mathematics","english","pedagogy","preschool-education"],
    "律师":   ["law","intellectual-property","prison-studies"],
    "警察":   ["public-order","criminal-investigation","police-management"],
    "心理咨询师": ["psychology","applied-psychology","psychiatry"],
    "会计":   ["accounting","financial-management","auditing"],
    "银行":   ["finance","economics","financial-engineering","insurance"],
    "码农":   ["computer-science","software-engineering","data-science-big-data","artificial-intelligence","network-engineering","information-security"],
    "程序员": ["computer-science","software-engineering","data-science-big-data","artificial-intelligence"],
    "建筑":   ["architecture","urban-planning","civil-engineering","engineering-management"],
  };
  const INTENT_GUIDANCE = {
    "深圳": "「深圳」是城市, 不是本科专业. 想了解深圳的大学或具体专业, 直接看 /majors.html.",
    "北京": "「北京」是城市, 不是本科专业. 想了解北京的大学或具体专业, 直接看 /majors.html.",
    "上海": "「上海」是城市, 不是本科专业. 想了解上海的大学或具体专业, 直接看 /majors.html.",
    "公费师范": "「公费师范」是国家政策 (6 所部属师范院校), 不是单一本科专业. 想读师范专业? 看「教师」相关的 6 个对口专业.",
    "考公": "「考公」是就业方向. 想提高考公竞争力, 选对口专业 (法学/行政管理/汉语言文学 等).",
    "全部": "输入专业名 (例: 临床医学) 或学科门类 (例: 医学) — 不支持搜「全部」.",
  };
  function _resolveIntentSynonyms(query) {
    const slugs = INTENT_SYNONYMS[query];
    if (!slugs || !_manifest) return [];
    const out = [];
    const seen = new Set();
    for (const slug of slugs) {
      if (seen.has(slug)) continue;
      const m = (_manifest.majors || []).find(x => x && x.slug === slug);
      if (!m) continue;
      seen.add(slug);
      out.push({ title: m.title, slug: m.slug, style: m.style, category: m.category || "" });
    }
    return out;
  }

    function _render(list, query) {
      results.innerHTML = "";
      // Bug fix (2026-06-25): 「未收录/想看」CTA 仅在 0 命中时展示.
      // 之前 list 相似命中但无字面匹配时也展示 (Day 7 fix), 导致搜「教师」命中 6 条相关 (汉语言文学/学前教育等) 时仍出现「未收录「教师」」CTA, 误导用户误点上报 (issue #9-#14 多条都是这种误触发).
      // 命中 ≥1 条时让用户正常浏览, 真要反馈走顶栏「反馈」入口.
      const showSynthCTA = list.length === 0;

      // CTA 卡片 (2026-06-25 改造: 加「职业/政策/城市 引导」+ 同义词推荐, 减少散户误上报)
      if (showSynthCTA) {
        const syns = _resolveIntentSynonyms(query);
        const guidance = INTENT_GUIDANCE[query];
        const isLikelyIntent = !!guidance || syns.length > 0;
        const title = isLikelyIntent
          ? '「<strong>' + _escapeHtml(query) + '</strong>」不是本科专业名'
          : '未收录「<strong>' + _escapeHtml(query) + '</strong>」';
        const desc = guidance
          ? guidance
          : (syns.length > 0
              ? '本站只收 13 门类本科专业. 您可能是想看:'
              : '告诉我们你想看哪个专业, 我们优先收录 (精品收录持续扩充中)');
        const synBlock = syns.length > 0
          ? '<div class="ms-synonyms" style="display:flex;flex-direction:column;gap:6px;margin-bottom:10px;">' +
              syns.slice(0, 6).map(s =>
                '<a class="ms-syn" href="/' + _escapeHtml(s.slug) + '.html" style="display:flex;align-items:center;justify-content:space-between;padding:10px 12px;background:#fff;border:1px solid var(--border);border-radius:6px;text-decoration:none;color:var(--fg);">' +
                '  <span style="font-weight:600;font-size:14px;">' + _escapeHtml(s.title) + '</span>' +
                '  <span style="font-size:11px;color:var(--muted);">' + _escapeHtml(s.category) + '</span>' +
                '</a>'
              ).join("") +
            '</div>'
          : "";
        const showReportBtn = !isLikelyIntent;
        const reportBlock = showReportBtn
          ? '<div class="nrr-actions" style="display:flex;gap:8px;flex-wrap:wrap;">' +
              '<button type="button" class="ms-report-btn nrr-btn" style="flex:1;min-width:160px;padding:8px 14px;background:#1f2937;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:600;font-size:13px;">💡 想看「' + _escapeHtml(query) + '」</button>' +
              '</div>'
          : "";
        const ctaHtml =
          '<div class="ms-no-result no-result-report" data-q="' + _escapeHtml(query) + '" style="padding:14px 16px;border-bottom:1px solid var(--border);background:linear-gradient(135deg,#fef9f2,#fff);">' +
          '  <div style="font-weight:600;font-size:14px;margin-bottom:6px;color:#92400e;">' + title + '</div>' +
          '  <div style="font-size:12px;color:#6b5d4f;margin-bottom:10px;line-height:1.5;">' + _escapeHtml(desc) + '</div>' +
            synBlock +
            reportBlock +
          '  <div class="nrr-synth-status" style="margin-top:8px;font-size:12px;color:#6b5d4f;"></div>' +
          '</div>';
        results.innerHTML = ctaHtml;
        // 绑定 CTA handler (只剩 report, 没按钮就不绑)
        if (showReportBtn) _bindDropdownCTA(query);
      }

      if (list.length === 0) {
        if (!showSynthCTA) {
          // 已渲染 CTA, 不再重复
        } else {
          // 上面已渲染 CTA, 这里只加 "没找到" 提示 + 浏览入口
          results.insertAdjacentHTML("beforeend",
            '<div class="ms-empty" style="padding:12px 16px;font-size:12px;color:#6b5d4f;border-top:1px dashed #e5dcc8;">' +
            '  没找到匹配「<strong>' + _escapeHtml(query) + '</strong>」的精品样板。' +
            '  <a class="ms-suggest" href="#majors" style="margin-left:4px;color:var(--accent);">浏览已上线的 →</a>' +
            '</div>');
        }
      } else {
        list.forEach((r, idx) => {
          const a = document.createElement("a");
          a.className = "ms-result " + r.style;
          if (idx === 0) a.classList.add("active");
          a.href = "/" + r.slug + ".html";
          a.innerHTML = [
            '<span class="ms-r-mark">' + _escapeHtml(_styleLabel(r.style)) + '</span>',
            '<span class="ms-r-text">',
            '  <span class="ms-r-title">' + _escapeHtml(r.title) + '</span>',
            '  <span class="ms-r-cat">' + _escapeHtml(r.category || "") + '</span>',
            '</span>',
            '<span class="ms-r-arr">→</span>',
          ].join("");
          results.appendChild(a);
        });
      }
      // 打开下拉时让 shell 进入 active 状态, CSS 会折叠 chips, 让 results 紧贴 input
      shell.setAttribute("data-active", "true");
      results.classList.add("open");
    }

    function doSearch() {
      const q = input.value.trim();
      if (!q) {
        results.classList.remove("open");
        shell.removeAttribute("data-active");
        return;
      }
      loadManifest().then(() => {
        const list = search(q);
        _render(list, q);
      });
    }

    let _t;
    input.addEventListener("input", () => {
      clearTimeout(_t);
      _t = setTimeout(doSearch, 120);
    });
    input.addEventListener("focus", () => {
      if (input.value.trim()) doSearch();
    });
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const list = _manifest ? search(input.value.trim()) : [];
      if (list.length > 0) {
        window.location.href = "/" + list[0].slug + ".html";
      } else {
        doSearch();
      }
    });
    input.addEventListener("keydown", (e) => {
      const items = results.querySelectorAll(".ms-result");
      if (items.length === 0) return;
      let idx = Array.from(items).findIndex((el) => el.classList.contains("active"));
      if (e.key === "ArrowDown") {
        e.preventDefault();
        idx = (idx + 1) % items.length;
        items.forEach((el) => el.classList.remove("active"));
        items[idx].classList.add("active");
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        idx = (idx - 1 + items.length) % items.length;
        items.forEach((el) => el.classList.remove("active"));
        items[idx].classList.add("active");
      } else if (e.key === "Enter") {
        e.preventDefault();
        const target = items[Math.max(0, idx)];
        if (target) window.location.href = target.href;
      } else if (e.key === "Escape") {
        results.classList.remove("open");
        shell.removeAttribute("data-active");
      }
    });

    // 点外面关
    document.addEventListener("click", (e) => {
      if (shell.contains(e.target)) return;
      results.classList.remove("open");
      shell.removeAttribute("data-active");
    });

    // 提前加载 manifest (无 await; 失败不阻塞)
    loadManifest().catch(() => {});

    return { shell, focus: () => input.focus(), search: doSearch };
  }

  global.MajorSearch = {
    loadManifest,
    search,
    mountChat,
    SYNONYMS,
    DEFAULT_CHIPS,
  };
})(typeof window !== "undefined" ? window : globalThis);
