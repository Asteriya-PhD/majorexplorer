/* wishlist.js — 心愿单 (localStorage) */
(async () => {
  await M.init();
  const KEY = "m.wishlist.v1";
  const root = document.getElementById("wishes");
  const bar = document.getElementById("filter-bar");
  if (!root) return;

  function load() { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch { return []; } }
  function save(arr) { localStorage.setItem(KEY, JSON.stringify(arr)); }

  // 用 manifest 解析 (slug → major)
  function lookup(slug) { return M.manifestBySlug[slug]; }

  let activeCat = "all";
  function render() {
    const all = load().map(s => lookup(s)).filter(Boolean);
    const filtered = activeCat === "all" ? all : all.filter(m => (m.tags || []).includes(activeCat) || m.category.includes(activeCat));
    if (!filtered.length) {
      root.innerHTML = `<div class="empty">
        <h3>${all.length ? "这个分类下没收藏" : "还没有收藏"}</h3>
        <div>${all.length ? "试试切回 '全部'" : "进精品详情点 ♥, 收藏的专业会出现在这里."}</div>
      </div>`;
      return;
    }
    root.innerHTML = filtered.map(m => `
      <div class="wish" style="--theme: ${M.styleColor(m.style)};">
        <div class="wish-head">
          <div>
            <div class="wish-cat">${m.category}<span class="star">★</span></div>
            <h3 class="wish-title">${m.title}</h3>
          </div>
          <span class="wish-x" data-rm="${m.slug}" aria-label="移除">×</span>
        </div>
        <a class="wish-quote" href="majors/${m.slug}.html">
          ${m.tags && m.tags[0] ? `「${m.tags[0]}」 — 继续看 →` : "查看详情 →"}
        </a>
      </div>
    `).join("");
    root.querySelectorAll("[data-rm]").forEach(el => {
      el.addEventListener("click", e => {
        e.preventDefault();
        const slug = el.dataset.rm;
        save(load().filter(s => s !== slug));
        render();
      });
    });
  }

  bar.querySelectorAll(".filter").forEach(f => {
    f.addEventListener("click", () => {
      bar.querySelectorAll(".filter").forEach(x => x.classList.remove("on"));
      f.classList.add("on");
      activeCat = f.dataset.cat;
      render();
    });
  });
  render();
})();
