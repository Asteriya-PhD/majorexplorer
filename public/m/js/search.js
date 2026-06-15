/* search.js — 搜专业 / 大类
 *
 * 专业匹配: 复用 PC MajorSearch.search() (SYNONYMS 词典 + 子串/同义词打分)
 * 大类匹配: 保持 mobile 自己的 hierarchy 遍历
 * UI: 保持 mobile 分段 + 大类 + filter 计数
 */
(async () => {
  try {
    await M.init();
  } catch (e) {
    console.error("[search.js] M.init failed", e);
    return;
  }
  // 确保 PC MajorSearch manifest 已加载 (PC 内部 lazy load)
  if (window.MajorSearch && MajorSearch.loadManifest) {
    await MajorSearch.loadManifest();
  }

  const $ = sel => document.querySelector(sel);
  const q = $("#q");
  const clear = $("#clear");
  const filters = $("#filters");
  const results = $("#results");
  if (!results) { console.warn("[search.js] #results not found"); return; }

  let activeType = "all";

  // 大类搜索 (mobile 独有的 hierarchy 遍历)
  function searchCategories(query) {
    const f = query.toLowerCase();
    return (M.hierarchy?.disciplines || []).flatMap(d =>
      (d.sub || []).filter(s => s.name.toLowerCase().includes(f)).map(s => ({...s, parent: d.name, code: d.code}))
    );
  }

  // 把 PC MajorSearch.search 结果格式补齐 (补 discipline/style/theme)
  function mapMajor(matched) {
    const full = M.manifestBySlug[matched.slug];
    return {
      ...matched,
      // PC result 已有 slug/title/style/category/tags/score
      // mobile UI 还需要 theme (styleColor) + 链接
      _full: full,
    };
  }

  function render(query, type) {
    const f = (query || "").trim().toLowerCase();
    if (!f) {
      results.innerHTML = `
        <div class="hot-list">
          <div style="width:100%;">
            <div style="font-family: var(--font-num); color: var(--muted); font-size: 0.75rem; letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 8px;">热门搜索</div>
            <div style="display:flex; flex-wrap:wrap; gap:8px;">
              ${["人工智能","临床医学","金融","计算机","法学","教育","心理学","会计"].map(t => `<a class="hot" href="javascript:void(0)" onclick="document.getElementById('q').value='${t}'; document.getElementById('q').dispatchEvent(new Event('input'));">${t}</a>`).join("")}
            </div>
          </div>
        </div>
      `;
      return;
    }
    // ── 专业匹配: 复用 PC MajorSearch.search (SYNONYMS 词典 + 子串打分) ──
    let majors = [];
    if (window.MajorSearch && typeof MajorSearch.search === "function") {
      const pcResults = MajorSearch.search(query);
      majors = pcResults.map(mapMajor).filter(m => m._full).slice(0, 20);
    } else {
      // 兜底: 5 字段子串 (PC 不可用时)
      majors = M.manifest.majors.filter(m => {
        return (m.title || "").toLowerCase().includes(f)
          || (m.tags || []).some(t => t.toLowerCase().includes(f))
          || (m.category || "").toLowerCase().includes(f)
          || (m.sub_discipline || "").toLowerCase().includes(f)
          || (m.menjia_name || "").toLowerCase().includes(f);
      }).slice(0, 20).map(m => mapMajor(m));
    }
    // ── 大类匹配: mobile 独有 ──
    const cats = searchCategories(query);

    const sections = [];
    if ((type === "all" || type === "major") && majors.length) {
      sections.push({label: "专业", items: majors.map(m => ({
        title: highlight(m.title, f),
        cat: m.category,
        star: true,
        href: `majors/${m.slug}.html`,
        theme: M.styleColor(m.style),
      }))});
    }
    if ((type === "all" || type === "category") && cats.length) {
      sections.push({label: "大类", items: cats.slice(0, 10).map(c => ({
        title: highlight(c.name, f),
        cat: c.parent,
        star: false,
        href: `catalog.html#q=${encodeURIComponent(c.name)}`,
        theme: "#5A4632",
      }))});
    }
    if (!sections.length) {
      results.innerHTML = `<div class="hot-list"><div style="width:100%; text-align:center; padding: 40px 0; color: var(--muted); font-family: var(--font-body);">没找到 "<strong>${esc(query)}</strong>" 相关结果. 试试 "金融" / "临床" / "法学".</div></div>`;
      return;
    }
    results.innerHTML = sections.map(s => `
      <div class="result-section">
        <div class="result-section-head">
          <span class="l">${s.label}</span>
          <span class="n"><strong>${s.items.length}</strong> 条</span>
        </div>
        ${s.items.map(it => `
          <a class="result" href="${it.href}" style="--theme: ${it.theme};">
            <div class="result-body">
              <h3 class="result-title">${it.title}${it.star ? '<span class="star">★</span>' : ''}</h3>
              <div class="result-cat">${it.cat}</div>
            </div>
            <div class="result-arrow">→</div>
          </a>
        `).join("")}
      </div>
    `).join("");

    // 更新 filter 计数
    const nM = majors.length, nC = cats.length;
    $("#n-major") && ($("#n-major").textContent = nM);
    $("#n-cat") && ($("#n-cat").textContent = nC);
    $("#n-all") && ($("#n-all").textContent = Number(nM) + Number(nC));
  }

  function highlight(text, q) {
    const i = text.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return esc(text);
    return esc(text.slice(0, i)) + "<em>" + esc(text.slice(i, i + q.length)) + "</em>" + esc(text.slice(i + q.length));
  }
  function esc(s) { return String(s).replace(/[<>&"]/g, c => ({"<":"&lt;",">":"&gt;","&":"&amp;",'"':"&quot;"})[c]); }

  // 初始渲染 + 计数
  const urlQ = new URLSearchParams(location.search).get("q") || "";
  if (urlQ && q) {
    q.value = urlQ;
    if (clear) clear.style.display = "flex";
    render(urlQ, activeType);
  } else {
    render("");
  }
  const nM = M.manifest.majors.length;
  const nC = (M.hierarchy?.disciplines || []).reduce((a, d) => a + (d.sub || []).length, 0);
  if ($("#n-major")) $("#n-major").textContent = nM;
  if ($("#n-cat")) $("#n-cat").textContent = nC;
  if ($("#n-all")) $("#n-all").textContent = nM + nC;

  if (q) {
    let timer;
    q.addEventListener("input", () => {
      clear.style.display = q.value ? "flex" : "none";
      clearTimeout(timer);
      timer = setTimeout(() => render(q.value, activeType), 120);
    });
  }
  if (clear) {
    clear.addEventListener("click", () => { q.value = ""; clear.style.display = "none"; render("", activeType); q.focus(); });
  }
  if (filters) {
    filters.querySelectorAll(".filter[data-type]").forEach(f => {
      f.addEventListener("click", () => {
        if (f.disabled) return;
        filters.querySelectorAll(".filter").forEach(x => x.classList.remove("on"));
        f.classList.add("on");
        activeType = f.dataset.type;
        render(q.value, activeType);
      });
    });
  }
})();
