/* wishlist.js — 心愿单 (localStorage) · 适配 {slug, rating, tag, comment, addedAt} schema */
(async () => {
  await M.init();
  const KEY = "m.wishlist.v1";
  const root = document.getElementById("wishes");
  const bar = document.getElementById("filter-bar");
  if (!root) return;

  function load() {
    try {
      const v = JSON.parse(localStorage.getItem(KEY) || "[]");
      return Array.isArray(v) ? v : [];
    } catch { return []; }
  }
  function save(arr) { localStorage.setItem(KEY, JSON.stringify(arr)); }
  // 兼容旧 string[] 格式
  function normalize(arr) {
    return arr.map(it => typeof it === "string"
      ? { slug: it, rating: 0, tag: "", comment: "", addedAt: 0 }
      : it);
  }
  function lookup(slug) { return M.manifestBySlug[slug]; }

  // 排序: 评分降序, 然后按 addedAt 降序
  function sortedWishes() {
    return normalize(load())
      .map(w => ({ ...w, major: lookup(w.slug) }))
      .filter(w => w.major)
      .sort((a, b) => {
        if (b.rating !== a.rating) return (b.rating || 0) - (a.rating || 0);
        return (b.addedAt || 0) - (a.addedAt || 0);
      });
  }

  function starStr(r) {
    if (!r) return "";
    return "★".repeat(r) + "☆".repeat(5 - r);
  }

  let activeCat = "all";
  let activeSort = "rating"; // rating | time

  function render() {
    const wishes = sortedWishes();
    const filtered = activeCat === "all" ? wishes : wishes.filter(w => {
      const m = w.major;
      return (m.tags || []).includes(activeCat) || (m.category || "").includes(activeCat);
    });
    const sorted = activeSort === "time"
      ? [...filtered].sort((a, b) => (b.addedAt || 0) - (a.addedAt || 0))
      : filtered;

    if (!sorted.length) {
      root.innerHTML = `<div class="empty">
        <h3>${wishes.length ? "这个分类下没收藏" : "还没有收藏"}</h3>
        <div>${wishes.length ? "试试切回 '全部'" : "进精品详情点 ♥ 打分, 收藏的专业会按评分排序出现."}</div>
      </div>`;
      return;
    }

    root.innerHTML = sorted.map(w => {
      const m = w.major;
      const rating = w.rating || 0;
      const tag = w.tag || "";
      const comment = w.comment || "";
      const hasMeta = rating || tag || comment;
      return `
      <div class="wish" style="--theme: ${M.styleColor(m.style)};">
        <div class="wish-head">
          <div>
            <div class="wish-cat">${m.category}</div>
            <h3 class="wish-title">${m.title}</h3>
            ${hasMeta ? `<div class="wish-meta">
              ${rating ? `<span class="wish-stars">${starStr(rating)}</span>` : ""}
              ${tag ? `<span class="wish-tag">${tag}</span>` : ""}
            </div>` : ""}
            ${comment ? `<div class="wish-comment">"${comment}"</div>` : ""}
          </div>
          <span class="wish-x" data-rm="${m.slug}" aria-label="移除">×</span>
        </div>
        <a class="wish-quote" href="majors/${m.slug}.html">
          ${m.tags && m.tags[0] ? `「${m.tags[0]}」 — 继续看 →` : "查看详情 →"}
        </a>
      </div>
    `}).join("");
    root.querySelectorAll("[data-rm]").forEach(el => {
      el.addEventListener("click", e => {
        e.preventDefault();
        const s = el.dataset.rm;
        save(normalize(load()).filter(w => w.slug !== s));
        render();
      });
    });
  }

  if (bar) {
    bar.querySelectorAll(".filter").forEach(f => {
      f.addEventListener("click", () => {
        bar.querySelectorAll(".filter").forEach(x => x.classList.remove("on"));
        f.classList.add("on");
        activeCat = f.dataset.cat;
        render();
      });
    });
  }
  render();
})();