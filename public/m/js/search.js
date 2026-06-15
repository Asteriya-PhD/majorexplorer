/* search.js — 搜专业 / 大类 */
(async () => {
  try {
    await M.init();
  } catch (e) {
    console.error("[search.js] M.init failed", e);
    return;
  }
  const $ = sel => document.querySelector(sel);
  const $$ = sel => document.querySelectorAll(sel);
  const q = $("#q");
  const clear = $("#clear");
  const filters = $("#filters");
  const results = $("#results");
  if (!results) { console.warn("[search.js] #results not found"); return; }

  let activeType = "all";

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
    // 搜专业 (title + tags + category + sub_discipline + menjia_name 多字段)
    const majors = M.manifest.majors.filter(m => {
      if (m.title.toLowerCase().includes(f)) return true;
      if ((m.tags || []).some(t => t.toLowerCase().includes(f))) return true;
      if ((m.category || "").toLowerCase().includes(f)) return true;
      if ((m.sub_discipline || "").toLowerCase().includes(f)) return true;
      if ((m.menjia_name || "").toLowerCase().includes(f)) return true;
      return false;
    });
    // 搜大类
    const cats = (M.hierarchy?.disciplines || []).flatMap(d =>
      (d.sub || []).filter(s => s.name.toLowerCase().includes(f)).map(s => ({...s, parent: d.name, code: d.code}))
    );
    const sections = [];
    if ((type === "all" || type === "major") && majors.length) {
      sections.push({label: "专业", items: majors.slice(0, 20).map(m => ({
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
    // 院校 — 后续开
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
  // URL ?q= 参数 → 自动填充 + 渲染 (从 catalog 跳转过来)
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
