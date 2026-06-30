/* catalog.js — 13 章节 accordion + 搜索过滤 + URL hash 展开 + sub-row 跳 search */
(async () => {
  // Day 47.11 P2-26 XSS fix
  const _esc = (s) => (s == null ? "" : String(s))
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  await M.init();

  // ───── 动态注入精品专业数 (替换静态 126) ─────
  const total = M.manifest.majors.length;
  document.querySelectorAll(".js-mcount").forEach(el => el.textContent = total);

  const root = document.getElementById("chapters");
  const q = document.getElementById("catalog-q");
  if (!root) return;

  const colorKey = {
    "01":"--c-01","02":"--c-02","03":"--c-03","04":"--c-04","05":"--c-05",
    "06":"--c-06","07":"--c-07","08":"--c-08","09":"--c-09","10":"--c-10",
    "12":"--c-12","13":"--c-13",
  };
  const h = M.hierarchy;
  const disciplines = h?.disciplines || [];

  // hierarchy 真实归属: 哪些 discipline 门类含此 name
  // (重要: 不能信 manifest.discipline, e.g. 心理学 manifest=07 但 hierarchy 在 04 教育学 心理学类)
  const hierNamesByCode = {};
  for (const d of disciplines) {
    const set = new Set();
    for (const s of (d.sub || [])) for (const n of (s.majors || [])) set.add(n);
    hierNamesByCode[d.code] = set;
  }
  // 每个 manifest 精品的真实归属门类 (按 hierarchy name 优先, fallback manifest.discipline)
  // 注意: 用 slug 而非 title, 避免同 title 多 slug (e.g. 汉语言文学 2 个 slug) 漏数
  const slugToRealCode = {};
  for (const m of M.manifest.majors) {
    let code = m.discipline;
    for (const d of disciplines) {
      if (hierNamesByCode[d.code].has(m.title)) { code = d.code; break; }
    }
    slugToRealCode[m.slug] = code;
  }
  // 章节头精品数: 按 slug 计数 (跟 sub-row 一致)
  const star = {};
  for (const m of M.manifest.majors) {
    const code = slugToRealCode[m.slug] || m.discipline;
    star[code] = (star[code] || 0) + 1;
  }

  function render(filter = "") {
    const f = filter.trim().toLowerCase();
    // 精品白名单: 126 个 manifest majors (用户原话"只显示已收录")
    // 用 slug 而不是 title 防漏 (e.g. 汉语言文学 2 个 slug)
    const curatedSlugs = new Set(M.manifest.majors.map(m => m.slug));
    // name → slugs[] (一个 name 可能对应多 slug)
    const nameToSlugs = {};
    for (const m of M.manifest.majors) {
      (nameToSlugs[m.title] = nameToSlugs[m.title] || []).push(m.slug);
    }
    // 该门类下, 按 slug 集合管理未渲染精品
    const discSlugs = {};
    for (const m of M.manifest.majors) {
      const code = slugToRealCode[m.slug] || m.discipline;
      (discSlugs[code] = discSlugs[code] || []).push(m.slug);
    }
    root.innerHTML = disciplines.map(d => {
      const ck = colorKey[d.code] || "--accent";
      // 该门类下所有 hierarchy 已收录 name 集合
      const hierNamesInDisc = hierNamesByCode[d.code] || new Set();
      // 该门类按 slug 跟踪的未渲染精品 (Set 防重复)
      const remaining = new Set(discSlugs[d.code] || []);
      const subs = (d.sub || []).map(s => {
        const name = s.name;
        const match = !f || name.toLowerCase().includes(f);
        if (!match) return "";
        // 该 sub-class 下的 majors 是 name 列表 (e.g. ["法学","知识产权","监狱学",...])
        // 每个 name 查 nameToSlugs, 收集该 sub-class 的所有 curated slugs
        const slugsHere = [];
        for (const majorName of (s.majors || [])) {
          for (const slug of (nameToSlugs[majorName] || [])) {
            if (remaining.has(slug)) slugsHere.push(slug);
          }
        }
        // 从 remaining 移除已渲染的 slug
        for (const slug of slugsHere) remaining.delete(slug);
        if (slugsHere.length === 0) return "";
        const cnt = slugsHere.length;
        // 跳到 search.html?q=大类名, 让用户看到该大类的具体专业
        return `<a class="sub-row" href="search.html?q=${encodeURIComponent(name)}"><span class="sub-name">${_esc(name)}</span><span class="sub-count">${cnt}</span></a>`;
      }).join("");
      // 末尾"其他"行: 该门类剩余未匹配 (e.g. 法学 8 个细分法学: 民法/刑法/商法...)
      // 注意: 0 精品时 sub-class 整条已隐藏, 但"其他"行还要看门类有没有匹配 (e.g. 交叉学科=0 整章不显示)
      const unmatched = remaining.size;
      const otherMatch = !f || "其他".includes(f);
      const otherRow = (unmatched > 0 && otherMatch)
        ? `<a class="sub-row" href="search.html?q=${encodeURIComponent(d.name)}"><span class="sub-name" style="color:var(--muted)">其他</span><span class="sub-count">${unmatched}</span></a>`
        : "";
      const subsHtml = subs + otherRow || `<div class="sub-row"><span class="sub-name" style="color:var(--muted)">暂无下属大类</span></a></div>`;
      // 整章 0 精品 (header star=0) 时整章隐藏
      if ((star[d.code] || 0) === 0) return "";
      return `
        <div class="chapter" data-code="${_esc(d.code)}" data-ghost="${_esc(d.name.slice(0,1))}" style="--theme: var(${ck});">
          <div class="chapter-head" data-toggle>
            <div class="chapter-meta">
              <div class="chapter-num">No. ${_esc(d.code)}</div>
              <div class="chapter-name">${_esc(d.name)}</div>
              <div class="chapter-sub">${(d.sub || []).slice(0,4).map(s=>_esc(s.name)).join(" · ")}${(d.sub||[]).length>4?" …":""}</div>
            </div>
            <div class="chapter-count">
              <span class="n">${star[d.code] || 0}<span class="star">★</span></span>
              <span class="of">${d.total || 0} 专业</span>
            </div>
            <div class="chapter-arrow">›</div>
          </div>
          <div class="chapter-body">
            <div class="sub-list">${subsHtml}</div>
          </div>
        </div>
      `;
    }).join("");

    // URL hash 自动展开 (#d=XX → 展开对应门类; #q=大类名 → 过滤)
    const hash = location.hash || "";
    const mCode = hash.match(/[#&]d=([0-9]+)/);
    const mQuery = hash.match(/[#&]q=([^&]+)/);
    if (mCode) {
      const target = root.querySelector(`.chapter[data-code="${mCode[1]}"]`);
      if (target) {
        target.classList.add("open");
        setTimeout(() => target.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
      }
    } else if (mQuery) {
      if (q) { q.value = decodeURIComponent(mQuery[1]); q.dispatchEvent(new Event("input")); }
    } else {
      // 默认展开 No.04 教育学 (跟 mock 一致)
      const edu = root.querySelectorAll(".chapter")[3];
      if (edu) edu.classList.add("open");
    }

    // 展开 / 折叠
    root.querySelectorAll("[data-toggle]").forEach(h => {
      h.addEventListener("click", () => h.parentElement.classList.toggle("open"));
    });
  }

  render();
  if (q) q.addEventListener("input", e => render(e.target.value));
})();