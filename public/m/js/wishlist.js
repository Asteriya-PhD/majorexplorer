/* wishlist.js — 心愿单 (mobile UI) · 复用 PC WishlistStore (gk.wishlist.v1)
 *
 * 数据流:
 *   - 读:  window.WishlistStore.all()        → array of {slug, title, style, score, rating, tag, comment, addedAt}
 *   - 写:  WishlistStore.upsert({slug, ...}) / WishlistStore.remove(slug)
 *   - 兼容: PC data via M.manifestBySlug[slug] 补 title/style/category 等展示字段
 */
(async () => {
  await M.init();
  // 兜底: PC WishlistStore 可能没加载 (来自 6 个 dock HTML <script> 注入)
  if (window.WishlistStore && WishlistStore.migrate) {
    const mig = WishlistStore.migrate();
    if (mig.migrated > 0) console.log("[wishlist.js] migrated " + mig.migrated);
  }
  const root = document.getElementById("wishes");
  const bar = document.getElementById("filter-bar");
  if (!root) return;

  // 排序: 评分降序, 然后按 addedAt 降序
  function sortedWishes() {
    const items = (window.WishlistStore ? WishlistStore.all() : []);
    return items
      .map(w => ({ ...w, major: M.manifestBySlug[w.slug] }))
      .filter(w => w.major)
      .sort((a, b) => {
        const ra = a.rating || a.score || 0;
        const rb = b.rating || b.score || 0;
        if (rb !== ra) return rb - ra;
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
      const rating = w.rating || w.score || 0;
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
        if (window.WishlistStore) WishlistStore.remove(s);
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

  // 监听 PC WishlistStore 的变更事件 (跨页同步, 同页多组件同步)
  if (window.WishlistStore && WishlistStore.subscribe) {
    WishlistStore.subscribe(() => render());
  }

  render();
})();
