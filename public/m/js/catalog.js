/* catalog.js — 13 章节 accordion + 搜索过滤 + URL hash 展开 + sub-row 跳 search */
(async () => {
  await M.init();
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
  // 算每门类精品数
  const star = {};
  for (const m of M.manifest.majors) {
    star[m.discipline] = (star[m.discipline] || 0) + 1;
  }

  function render(filter = "") {
    const f = filter.trim().toLowerCase();
    root.innerHTML = disciplines.map(d => {
      const ck = colorKey[d.code] || "--accent";
      const subs = (d.sub || []).map(s => {
        const cnt = (s.majors || []).length;
        const name = s.name;
        const match = !f || name.toLowerCase().includes(f);
        if (!match) return "";
        // 跳到 search.html?q=大类名, 让用户看到该大类的具体专业
        return `<a class="sub-row" href="search.html?q=${encodeURIComponent(name)}"><span class="sub-name">${name}</span><span class="sub-count">${cnt}</span></a>`;
      }).join("") || `<div class="sub-row"><span class="sub-name" style="color:var(--muted)">暂无下属大类</span></a></div>`;
      return `
        <div class="chapter" data-code="${d.code}" data-ghost="${d.name.slice(0,1)}" style="--theme: var(${ck});">
          <div class="chapter-head" data-toggle>
            <div class="chapter-meta">
              <div class="chapter-num">No. ${d.code}</div>
              <div class="chapter-name">${d.name}</div>
              <div class="chapter-sub">${(d.sub || []).slice(0,4).map(s=>s.name).join(" · ")}${(d.sub||[]).length>4?" …":""}</div>
            </div>
            <div class="chapter-count">
              <span class="n">${star[d.code] || 0}<span class="star">★</span></span>
              <span class="of">${d.total || 0} 专业</span>
            </div>
            <div class="chapter-arrow">›</div>
          </div>
          <div class="chapter-body">
            <div class="sub-list">${subs}</div>
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