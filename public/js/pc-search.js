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

    if (!sections.length) {
      results.innerHTML = renderNoResult(query);
      bindReportCard(results, query);
      updateFilterCounts(0, 0);
      return;
    }
    results.innerHTML = sections.map((s) => `
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

    updateFilterCounts(majors.length, cats.length);
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

  // ── 0 命中: "尚未收录「{query}」" 卡片 (PC 大字号版, source="pc") ──
  function renderNoResult(query) {
    return `
      <div class="no-result-report" data-q="${_esc(query)}">
        <div class="nrr-title">尚未收录「<strong>${_esc(query)}</strong>」</div>
        <div class="nrr-desc">告诉我们你想看, 收齐了我们优先做。报告会在 GitHub Issue 里归档, 我们会跟踪。</div>
        <button class="nrr-btn" type="button">📨 点击报告给我们</button>
        <div class="nrr-fallback">没反应? 邮件 <a href="mailto:major.explorer.feedback@gmail.com">major.explorer.feedback@gmail.com</a></div>
      </div>
    `;
  }
  function bindReportCard(root, query) {
    const card = root.querySelector(".no-result-report");
    if (!card) return;
    const btn = card.querySelector(".nrr-btn");
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      btn.textContent = "发送中...";
      btn.classList.add("loading");
      try {
        const r = await fetch("/api/report", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ type: "missing-major", name: query, source: "pc" }),
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
        btn.textContent = "✕ 发送失败, 用邮件兜底";
        btn.classList.remove("loading");
        btn.classList.add("failed");
        btn.disabled = false;
        console.error("[pc-search.js] report failed", e);
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
