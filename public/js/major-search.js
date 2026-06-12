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
    "律师": ["law"],
    "法学": ["law"],
    "法考": ["law"],

    // 教育 + 人文 + 设计
    "教师": ["education", "chinese-language-literature", "english", "psychology", "history"],
    "老师": ["education"],
    "师范": ["education", "english", "chinese-language-literature"],
    "公费师范": ["education"],
    "心理": ["psychology", "applied-psychology"],
    "心理学": ["psychology", "applied-psychology"],
    "心理咨询": ["psychology", "applied-psychology"],
    "新闻": ["journalism-communication"],
    "传媒": ["journalism-communication"],
    "记者": ["journalism-communication"],
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
    "公务员": ["public-administration", "law", "library-science", "financial-management"],
    "考公": ["public-administration", "law", "library-science", "chinese-language-literature"],
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

  // 主页 chat 栏下方默认快捷 chip
  const DEFAULT_CHIPS = [
    { label: "🧑‍💻 编程", q: "编程" },
    { label: "🩺 当医生", q: "医生" },
    { label: "📚 当老师", q: "教师" },
    { label: "💰 金融", q: "金融" },
    { label: "⚖️ 法律", q: "法律" },
    { label: "🎨 设计", q: "设计" },
    { label: "🏛️ 考公", q: "考公" },
    { label: "🧠 心理", q: "心理" },
    { label: "🤖 人工智能", q: "人工智能" },
    { label: "🚗 新能源车", q: "新能源车" },
    { label: "🌱 农学", q: "农学" },
    { label: "🎬 动画游戏", q: "游戏" },
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
  width: 40px; height: 40px; border-radius: 10px;
  background: #14110D; color: #FAFAF7; border: none; cursor: pointer;
  transition: background 180ms, transform 180ms;
  font-size: 1.125rem;
}
.ms-send:hover { background: #B8323A; transform: translateY(-1px); }
.ms-send:disabled { background: #BFB9AB; cursor: not-allowed; transform: none; }
.ms-shell.compact .ms-send { width: 36px; height: 36px; font-size: 1rem; }

.ms-chips {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-top: 16px; justify-content: center;
  max-height: 200px; opacity: 1; overflow: hidden;
  transition: max-height 240ms ease, opacity 180ms ease, margin-top 180ms ease;
}
.ms-shell.compact .ms-chips { justify-content: flex-start; }
/* 下拉打开时折叠 chips, 让 results 紧贴 input 下方 */
.ms-shell[data-active="true"] .ms-chips {
  max-height: 0; opacity: 0; margin-top: 0; pointer-events: none;
}
.ms-chip {
  font-size: 0.8125rem; padding: 7px 14px; border-radius: 999px;
  background: #FAFAF7; color: #14110D; border: 1px solid #E2DFD5;
  cursor: pointer; transition: all 160ms;
  font-family: 'Inter', 'PingFang SC', sans-serif;
}
.ms-chip:hover { border-color: #14110D; transform: translateY(-1px); }

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
.ms-synth-cta {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  margin-top: 14px; flex-wrap: wrap;
}
.ms-synth-btn {
  appearance: none; border: 0; cursor: pointer;
  padding: 10px 20px; border-radius: 999px;
  background: linear-gradient(135deg, #B8323A 0%, #8B2329 100%);
  color: #fff; font-size: 0.9375rem; font-weight: 600;
  letter-spacing: 0.02em; box-shadow: 0 2px 8px rgba(184, 50, 58, 0.25);
  transition: transform 0.15s, box-shadow 0.15s;
}
.ms-synth-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(184, 50, 58, 0.35);
}
.ms-synth-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ms-synth-hint {
  font-size: 0.75rem; color: #94A3B8; font-weight: 400;
}
.ms-synth-progress {
  margin-top: 12px; padding: 10px 16px;
  background: #FAF7F2; border-radius: 8px;
  font-size: 0.8125rem; color: #6F6A60;
}
.ms-synth-bar {
  height: 4px; background: #E8E0D4; border-radius: 2px;
  overflow: hidden; margin-bottom: 6px;
}
.ms-synth-bar-fill {
  height: 100%; background: linear-gradient(90deg, #B8323A, #E89097);
  transition: width 0.4s ease;
}
.ms-synth-msg { font-weight: 500; color: #14110D; }
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
      (compact ? "搜其他专业 (比如「编程」「医生」「金融」)…" : "想了解什么专业?  比如「编程」「医生」「教师」「设计」…");
    const chips = opts.chips || DEFAULT_CHIPS;

    const shell = document.createElement("div");
    shell.className = "ms-shell" + (compact ? " compact" : "");
    shell.innerHTML = [
      '<form class="ms-bar" autocomplete="off" role="search">',
      '  <input class="ms-input" type="text" placeholder="' + placeholder.replace(/"/g, "&quot;") + '" aria-label="搜索专业">',
      '  <button class="ms-send" type="submit" aria-label="搜索"><span aria-hidden="true">→</span></button>',
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

    // chips
    chips.forEach((c) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "ms-chip"; b.textContent = c.label;
      b.addEventListener("click", () => { input.value = c.q; doSearch(); input.focus(); });
      chipBar.appendChild(b);
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

    function _render(list, query) {
      results.innerHTML = "";
      if (list.length === 0) {
        // ── 改造: 现场按需生成 CTA ──
        results.innerHTML =
          '<div class="ms-empty">' +
          '  没找到匹配「<strong>' + _escapeHtml(query) + '</strong>」的精品样板。' +
          '  <br>要不要让 AI 现场为你合成一份？约 5-15 分钟出报告。' +
          '  <div class="ms-synth-cta">' +
          '    <button type="button" class="ms-synth-btn" data-query="' + _escapeHtml(query) + '">' +
          '      🪄 现场为我合成' +
          '    </button>' +
          '    <span class="ms-synth-hint">基于 Web 搜索 + 60 精品样板</span>' +
          '  </div>' +
          '  <div class="ms-synth-progress" hidden></div>' +
          '  <a class="ms-suggest" href="#majors">浏览已上线的精品样板 →</a>' +
          '</div>';
        // 绑定 CTA 按钮 → 调 synth-client
        const btn = results.querySelector(".ms-synth-btn");
        if (btn) {
          btn.addEventListener("click", () => {
            if (global.SynthClient && global.SynthClient.start) {
              global.SynthClient.start(btn.dataset.query, results);
            } else {
              console.warn("SynthClient 未加载, 走 fallback 文案");
            }
          });
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
