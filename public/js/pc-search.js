/* pc-search.js — PC 端 search.html 搜索逻辑
 *
 * 设计原则:
 * - 复用 PC MajorSearch.search() (SYNONYMS 词典 + 子串打分) — 跟 mobile search.js 一致
 * - 大类匹配: 直接遍历 discipline_hierarchy.json 13 门类 / 92 专业类
 * - 0 命中: 复用 no-result-report 卡片 (PC 大字号版), source="pc" → /api/report
 * - 热门搜索: 8 个固定 chip
 *
 * 跟 mobile search.js 的区别:
 * - 路径: 全部用绝对路径 /js/, /data/
 * - 字体 / 间距: PC 大字号 (由 search.html 的 CSS 控)
 * - 调 /api/report 时 source="pc"
 */
(async () => {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const q = $("#q");
  const clear = $("#clear");
  const filters = $("#filters");
  const results = $("#results");
  const hotRegion = $("#hot-region");
  const hotList = $("#hot-list-inner");
  if (!results) { console.warn("[pc-search.js] #results not found"); return; }

  let activeType = "all";
  let manifest = null;        // {majors: [...], total, ...}
  let manifestBySlug = {};    // slug → major
  let hierarchy = null;       // {disciplines: [...]}
  let styleColorMap = {};     // style → "#XXXXXX" 来自 major.theme_color.primary

  // ── 加载数据 ──
  try {
    const [m, h] = await Promise.all([
      fetch("/data/manifest.json").then((r) => r.json()),
      fetch("/data/discipline_hierarchy.json").then((r) => r.json()).catch(() => null),
    ]);
    manifest = m;
    hierarchy = h;
    for (const maj of m.majors || []) {
      manifestBySlug[maj.slug] = maj;
      if (maj.style && maj.theme_color && maj.theme_color.primary) {
        // 用该 style 第一个出现的主题色, 避免 N majors 重复
        if (!styleColorMap[maj.style]) styleColorMap[maj.style] = maj.theme_color.primary;
      }
    }
    // PC 跟 mobile 一样 normalize hierarchy
    if (hierarchy) {
      let list = hierarchy.disciplines || hierarchy.menjia || null;
      const menjaDict = hierarchy["门类"];
      if (!list && menjaDict) {
        list = Object.entries(menjaDict).map(([code, v]) => {
          const subRaw = v.sub_classes || v.sub || v["大类"] || {};
          const sub = Array.isArray(subRaw) ? subRaw : Object.entries(subRaw).map(([k, sv]) => ({
            code: k, name: sv.name || "", majors: sv.majors || [], total: (sv.majors || []).length,
          }));
          return { code, name: v.name, total: sub.reduce((a, s) => a + (s.total || 0), 0), sub };
        });
      }
      if (!list) list = [];
      hierarchy.disciplines = list.map((d) => ({
        code: d.code || d["代码"] || "",
        name: d.name || d["名称"] || "",
        total: d.total || d["专业总数"] || 0,
        sub: Array.isArray(d.sub) ? d.sub : Object.entries(d.sub || {}).map(([k, sv]) => ({
          code: k, name: sv.name || "", majors: sv.majors || [], total: (sv.majors || []).length,
        })),
      }));
    }
  } catch (e) {
    console.error("[pc-search.js] data load failed", e);
    results.innerHTML = `<div style="text-align:center; padding: 60px 24px; color: var(--muted);">搜索数据加载失败, 刷新页面重试。</div>`;
    return;
  }

  // ── 大类搜索: 遍历 13 门类 / 92 专业类 ──
  function searchCategories(query) {
    const f = query.toLowerCase();
    const out = [];
    for (const d of (hierarchy?.disciplines || [])) {
      for (const s of (d.sub || [])) {
        if (s.name.toLowerCase().includes(f)) {
          out.push({ ...s, parent: d.name, code: d.code });
        }
      }
    }
    return out;
  }

  function _styleColor(style) {
    return styleColorMap[style] || "#4A4564";
  }

  function _esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function _highlight(text, q) {
    const i = text.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return _esc(text);
    return _esc(text.slice(0, i))
      + "<em>" + _esc(text.slice(i, i + q.length)) + "</em>"
      + _esc(text.slice(i + q.length));
  }

  // ── 主搜索 ──
  function searchMajors(query) {
    if (!window.MajorSearch) return [];
    // MajorSearch.search 需要先 loadManifest()
    // 但 mobile 也是同样路径, MajorSearch.loadManifest() 内部 fetch /data/manifest.json
    // PC 这边我们已经有 manifest, 用 MajorSearch._manifest 直接喂
    if (MajorSearch.loadManifest && !MajorSearch._manifest) {
      // 尝试 lazy load
      MajorSearch.loadManifest().catch(() => {});
    }
    return MajorSearch.search(query) || [];
  }

  // 等待 MajorSearch manifest 加载完成
  async function waitManifest() {
    if (window.MajorSearch && MajorSearch.loadManifest) {
      try { await MajorSearch.loadManifest(); } catch (e) {}
    }
  }
  await waitManifest();

  // ── 渲染结果 ──
  function render(query, type) {
    const f = (query || "").trim().toLowerCase();
    if (!f) {
      // 空 query: 显示热门搜索 (占 results 位置)
      hotRegion.hidden = false;
      renderHot();
      results.innerHTML = "";
      return;
    }
    hotRegion.hidden = true;
    hotList.innerHTML = "";

    // 1) 专业匹配
    let majors = [];
    if (window.MajorSearch) {
      const pcResults = MajorSearch.search(query);
      majors = (pcResults || []).slice(0, 20);
    } else {
      // 兜底: 5 字段子串
      majors = (manifest.majors || []).filter((m) => {
        return (m.title || "").toLowerCase().includes(f)
          || (m.tags || []).some((t) => t.toLowerCase().includes(f))
          || (m.category || "").toLowerCase().includes(f)
          || (m.sub_discipline || "").toLowerCase().includes(f)
          || (m.menjia_name || "").toLowerCase().includes(f);
      }).slice(0, 20);
    }

    // 2) 大类匹配
    const cats = searchCategories(query);

    const sections = [];
    if ((type === "all" || type === "major") && majors.length) {
      sections.push({ label: "专业", count: majors.length, items: majors.map((m) => ({
        title: _highlight(m.title, f),
        cat: m.category || "",
        star: true,
        href: "/" + m.slug + ".html",
        theme: _styleColor(m.style),
      }))});
    }
    if ((type === "all" || type === "category") && cats.length) {
      sections.push({ label: "大类", count: cats.length, items: cats.slice(0, 10).map((c) => ({
        title: _highlight(c.name, f),
        cat: c.parent,
        star: false,
        href: "/majors.html#q=" + encodeURIComponent(c.name),
        theme: "#5A4632",
      }))});
    }

    // Bug fix (2026-06-25): 「未收录/想看」CTA 仅在 0 命中时展示.
    // 之前 majors 相似命中但无字面匹配时也展示, 误导用户误点上报 (issue #11 医生/#12 考公/#14 公费师范 等都是这种误触发).
    // 命中 ≥1 条时, 让用户正常浏览结果; 真想反馈走顶栏「反馈」入口.
    const noResultHtml = sections.length === 0 ? renderNoResult(query) : "";

    if (!sections.length) {
      results.innerHTML = noResultHtml;
      bindReportCard(results, query);
      updateFilterCounts(0, 0);
      // Day 32 v2 (#10): 0 命中也要上报搜索词, 看哪些词是真 0 命中 (后续补 manifest)
      if (window.trackSearch) window.trackSearch(query, 0, 'pc-search');
      return;
    }
    results.innerHTML = noResultHtml + sections.map((s) => `
      <div class="result-section">
        <div class="result-section-head" data-cat="${_esc(s.label)}">
          <span class="l">${_esc(s.label)} <span class="tag">${_esc(s.label === "专业" ? "精品" : "学科")}</span></span>
          <span class="n"><strong>${s.count}</strong> 条</span>
        </div>
        ${s.items.map((it) => `
          <a class="result" href="${it.href}" style="--theme: ${it.theme};">
            <div class="result-body">
              <h3 class="result-title">${it.title}${it.star ? '<span class="star">★</span>' : ''}</h3>
              <div class="result-cat">${_esc(it.cat)}</div>
            </div>
            <div class="result-arrow">→</div>
          </a>
        `).join("")}
      </div>
    `).join("");
    if (noResultHtml) bindReportCard(results, query);

    updateFilterCounts(majors.length, cats.length);
    // Day 32 v2 (#10): 上报搜索词 + 命中数 + 是否意图词
    if (window.trackSearch) {
      window.trackSearch(query, majors.length + cats.length, 'pc-search');
    }
  }

  function updateFilterCounts(nM, nC) {
    const nAll = Number(nM) + Number(nC);
    const $nM = $("#n-major");
    const $nC = $("#n-cat");
    const $nAll = $("#n-all");
    const $nAllBtn = $("#n-all-btn");
    if ($nM) $nM.textContent = nM;
    if ($nC) $nC.textContent = nC;
    if ($nAll) $nAll.textContent = nAll;
    if ($nAllBtn) $nAllBtn.textContent = nAll;
  }

  // ── 同义词词典 (2026-06-25 新增) ──
  // 搜索 0 命中时, 用户经常搜的是职业/政策/城市 而非本科专业名.
  // 这里把常见"非专业名"映射到对口本科专业 slug, 引导用户跳转, 减少误上报.
  // slug 必须与 manifest.json 中真实存在一致 (改前用 curl 验过).
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
  // style key → emoji (用于同义词卡片左侧 icon, Day 32 v2)
  const STYLE_ICON = {
    cs:'💻', medicine:'🩺', finance:'💰', law:'⚖️', education:'📚',
    humanities:'📖', sci:'🔬', eng:'⚙️', administration:'🏛️',
    agri:'🌱', arts:'🎨', gongan:'🛡️',
  };
  // 政策/城市/技术领域: 不是本科专业, 给一段引导说明
  const INTENT_GUIDANCE = {
    "深圳": "「深圳」是城市, 不是本科专业. 想了解深圳的大学或具体专业, 直接看 /majors.html 或选个学科门类.",
    "北京": "「北京」是城市, 不是本科专业. 想了解北京的大学或具体专业, 直接看 /majors.html.",
    "上海": "「上海」是城市, 不是本科专业. 想了解上海的大学或具体专业, 直接看 /majors.html.",
    "公费师范": "「公费师范」是国家政策 (6 所部属师范院校), 不是单一本科专业. 想读师范专业? 看「教师」相关的 6 个对口专业.",
    "考公": "「考公」是就业方向. 想提高考公竞争力, 选对口专业 (法学/行政管理/汉语言文学 等).",
    "全部": "输入专业名 (例: 临床医学) 或学科门类 (例: 医学) — 不支持搜「全部」.",
  };

  // 在已加载的 manifest 中, 把同义词 slug 解析成 {title, slug, theme, style}
  function resolveSynonyms(query) {
    const q = (query || "").trim();
    const slugs = INTENT_SYNONYMS[q];
    if (!slugs) return [];
    const out = [];
    const seen = new Set();
    for (const slug of slugs) {
      if (seen.has(slug)) continue;
      const m = manifestBySlug[slug];
      if (!m) continue;
      seen.add(slug);
      out.push({
        title: m.title,
        slug: m.slug,
        cat: m.category || "",
        theme: _styleColor(m.style),
        style: m.style || "",   // Day 32 v2: 给 emoji icon lookup 用
        icon: STYLE_ICON[m.style] || "📘",  // Day 32 v4: emoji 圆徽
      });
    }
    return out;
  }

  // ── 0 命中: "尚未收录「{query}」" 卡片 (PC 大字号版, source="pc")
  //    2026-06-25 改造: 标题/描述改为「职业/政策/城市 引导」+ 同义词推荐, 减少散户误上报.
  function renderNoResult(query) {
    const syns = resolveSynonyms(query);
    const guidance = INTENT_GUIDANCE[query];
    const isLikelyIntent = !!guidance || syns.length > 0;
    const title = isLikelyIntent
      ? `「<strong>${_esc(query)}</strong>」不是本科专业名`
      : `尚未收录「<strong>${_esc(query)}</strong>」`;
    const desc = guidance
      ? guidance
      : (syns.length > 0
          ? `本站只收 13 门类本科专业. 您可能是想看:`
          : `告诉我们你想看哪个专业, 我们优先收录 (精品报告持续扩充中).`);
    const synBlock = syns.length > 0 ? `
      <div class="nrr-synonyms">
        <div class="nrr-syn-label">可能是想看 <span>(${syns.length} 个)</span></div>
        <div class="nrr-syn-list">
          ${syns.slice(0, 6).map(s => `
            <a class="nrr-syn" href="/${_esc(s.slug)}.html" style="--theme:${_esc(s.theme)};">
              <span class="nrr-syn-emoji" aria-hidden="true">${_esc(s.icon || "📘")}</span>
              <span class="nrr-syn-text">
                <span class="nrr-syn-title">${_esc(s.title)}</span>
                <span class="nrr-syn-cat">${_esc(s.cat)}</span>
              </span>
            </a>
          `).join("")}
        </div>
      </div>
    ` : "";
    const showReportBtn = !isLikelyIntent;  // 是职业/政策/城市就别再诱导用户想看 XX 了
    const reportBlock = showReportBtn ? `
      <div class="nrr-actions">
        <button class="nrr-btn" type="button">💡 想看「${_esc(query)}」</button>
      </div>
    ` : "";
    return `
      <div class="no-result-report" data-q="${_esc(query)}">
        <div class="nrr-title">${title}</div>
        <div class="nrr-desc">${_esc(desc)}</div>
        ${synBlock}
        ${reportBlock}
        <div class="nrr-synth-status"></div>
      </div>
    `;
  }
  function bindReportCard(root, query) {
    const card = root.querySelector(".no-result-report");
    if (!card) return;
    const btn = card.querySelector(".nrr-btn");
    if (!btn) return;  // 2026-06-25: 职业/政策/城市类不再展示「想看 XX」按钮, 跳过 event 绑定
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      btn.textContent = "发送中...";
      btn.classList.add("loading");
      try {
        const r = await fetch("/api/report", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ type: "missing-major", category: "want", name: query, source: "pc" }),
        });
        const d = await r.json().catch(() => ({}));
        if (r.ok && d.ok) {
          btn.textContent = "✓ 已收到, 谢谢!";
          btn.classList.remove("loading");
          btn.classList.add("sent");
        } else {
          throw new Error(d.error || `HTTP ${r.status}`);
        }
      } catch (e) {
        btn.textContent = "✕ 发送失败, 用顶栏「反馈」按钮重试";
        btn.classList.remove("loading");
        btn.classList.add("failed");
        btn.disabled = false;
        console.error("[pc-search.js] report failed", e);
      }
    });
    // Day 21: 删除 bindSynthCard 调用 (取消实时合成 UI, 后端端点仍保留)
  }

  // ── 4 段进度映射 (与 worker step 对齐, UI 友好) ──
  function synthStepName(step) {
    if (!step) return "排队中";
    if (step === "init" || step === "validate") return "正在准备";
    if (step === "search" || step === "route_style" || step === "synthesize") return "正在生成内容";
    if (step === "render") return "正在渲染页面";
    if (step === "manifest") return "正在发布";
    if (step === "complete") return "即将完成";
    return "处理中";
  }

  // ── 🔄 实时合成 handler (PC + mobile 共享逻辑) ──
  async function bindSynthCard(root, query, source) {
    const card = root.querySelector(".no-result-report");
    if (!card) return;
    const btn = card.querySelector(".nrr-synth-btn");
    const statusEl = card.querySelector(".nrr-synth-status");
    if (!btn) return;

    btn.addEventListener("click", async () => {
      btn.disabled = true;
      const originalLabel = btn.textContent;
      btn.textContent = "排队中...";
      statusEl.textContent = "";
      statusEl.className = "nrr-synth-status";

      try {
        // 1) POST 入队
        const r = await fetch("/api/synth/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: query, source }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok || !d.ok) {
          if (r.status === 429) throw new Error("请求太频繁, 请 1 分钟后再试");
          throw new Error(d.error || `HTTP ${r.status}`);
        }

        // 2) dedup hit: 同 slug 已 done → 直接跳
        if (d.deduped && d.status === "done" && d.output_url) {
          statusEl.textContent = "✅ 已存在, 跳转中...";
          statusEl.classList.add("ok");
          setTimeout(() => { location.href = d.output_url; }, 600);
          return;
        }

        // 3) 轮询 status (3s 间隔, 最长 5min = 100 次)
        const runId = d.run_id;
        statusEl.textContent = "⏳ 正在准备, 预计 60-120 秒";
        statusEl.classList.add("running");
        btn.textContent = "正在合成...";

        let attempts = 0;
        const poll = setInterval(async () => {
          attempts++;
          try {
            const sr = await fetch(`/api/synth/status?run_id=${runId}`);
            const s = await sr.json().catch(() => ({}));
            if (!sr.ok) {
              if (attempts > 3) {
                clearInterval(poll);
                throw new Error(`状态查询失败 (HTTP ${sr.status})`);
              }
              return;
            }
            if (s.status === "done" && s.output_url) {
              clearInterval(poll);
              statusEl.textContent = "✅ 合成完成, 跳转中...";
              statusEl.classList.remove("running");
              statusEl.classList.add("ok");
              setTimeout(() => { location.href = s.output_url; }, 600);
              return;
            }
            if (s.status === "failed" || s.status === "dead") {
              clearInterval(poll);
              statusEl.innerHTML = `❌ 合成失败: ${_esc(s.error || "未知错误")}. <a href="#" class="nrr-report-link">📨 报告给我们</a>`;
              statusEl.classList.remove("running");
              statusEl.classList.add("failed");
              btn.disabled = false;
              btn.textContent = originalLabel;
              return;
            }
            // queued / running → 4 段进度
            statusEl.textContent = `⏳ ${synthStepName(s.step)} (第 ${attempts} 次查询)`;
          } catch (pollErr) {
            console.error("[pc-search.js] poll error", pollErr);
          }
          if (attempts > 100) {
            clearInterval(poll);
            statusEl.textContent = "⏰ 超时 (5min), 请刷新重试";
            statusEl.classList.remove("running");
            statusEl.classList.add("failed");
            btn.disabled = false;
            btn.textContent = originalLabel;
          }
        }, 3000);
      } catch (e) {
        statusEl.innerHTML = `❌ ${_esc(e.message || "提交失败")}. <a href="#" class="nrr-report-link">📨 报告给我们</a>`;
        statusEl.classList.add("failed");
        btn.disabled = false;
        btn.textContent = originalLabel;
        console.error("[pc-search.js] synth failed", e);
      }

      // 失败 fallback: 引导用户走 GH Issue 上报
      const reportLink = statusEl.querySelector(".nrr-report-link");
      if (reportLink) {
        reportLink.addEventListener("click", async (ev) => {
          ev.preventDefault();
          const rr = await fetch("/api/report", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type: "missing-major", name: query, source }),
          });
          const rd = await rr.json().catch(() => ({}));
          if (rr.ok && rd.ok) {
            statusEl.innerHTML = "✅ 已上报, 我们会跟进";
            statusEl.classList.remove("failed");
            statusEl.classList.add("ok");
          }
        });
      }
    });
  }

  // ── 热门搜索 chip ──
  const HOT_TERMS = ["人工智能", "临床医学", "金融", "计算机", "法学", "教育", "心理学", "会计", "设计", "考公"];
  function renderHot() {
    if (!hotList) return;
    hotList.innerHTML = HOT_TERMS.map((t) =>
      `<button class="hot" type="button" data-q="${_esc(t)}">${_esc(t)}</button>`
    ).join("");
    hotList.querySelectorAll(".hot").forEach((b) => {
      b.addEventListener("click", () => {
        const term = b.dataset.q;
        if (q) { q.value = term; clear?.classList.add("on"); }
        render(term, activeType);
        q?.focus();
      });
    });
  }

  // ── 初始: URL ?q= 支持 ──
  const urlQ = new URLSearchParams(location.search).get("q") || "";
  if (urlQ) {
    if (q) q.value = urlQ;
    if (clear) clear.classList.add("on");
    render(urlQ, activeType);
  } else {
    render("", activeType);
  }
  // 初始 filter 计数 (manifest 全量)
  const totalM = (manifest.majors || []).length;
  const totalC = (hierarchy?.disciplines || []).reduce((a, d) => a + (d.sub || []).length, 0);
  updateFilterCounts(totalM, totalC);

  // ── 事件 ──
  let timer;
  if (q) {
    q.addEventListener("input", () => {
      clear?.classList.toggle("on", !!q.value);
      clearTimeout(timer);
      timer = setTimeout(() => render(q.value, activeType), 120);
    });
  }
  if (clear) {
    clear.addEventListener("click", () => {
      if (q) q.value = "";
      clear.classList.remove("on");
      render("", activeType);
      q?.focus();
    });
  }
  if (filters) {
    filters.querySelectorAll(".filter[data-type]").forEach((f) => {
      f.addEventListener("click", () => {
        if (f.disabled) return;
        filters.querySelectorAll(".filter").forEach((x) => x.classList.remove("on"));
        f.classList.add("on");
        activeType = f.dataset.type;
        render(q.value, activeType);
      });
    });
  }
})();
