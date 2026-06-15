/* me.js — 浏览历史 + 收藏统计 */
(async () => {
  await M.init();
  const HKEY = "m.history.v1";
  const WKEY = "m.wishlist.v1";
  const histRoot = document.getElementById("history");
  if (!histRoot) return;

  function load(k) { try { return JSON.parse(localStorage.getItem(k) || "[]"); } catch { return []; } }
  function save(k, v) { localStorage.setItem(k, JSON.stringify(v)); }

  // 头部统计
  const histCount = load(HKEY);
  const wishCount = load(WKEY);
  document.getElementById("hist-count").textContent = histCount.length;
  document.getElementById("wish-count").textContent = wishCount.length;

  // 历史列表
  if (!histCount.length) {
    histRoot.innerHTML = `<div class="hist-row">
      <div class="hist-body">
        <div class="hist-cat">—</div>
        <div class="hist-title" style="color: var(--muted);">还没读过任何专业</div>
      </div>
    </div>`;
  } else {
    histRoot.innerHTML = histCount.slice(0, 10).map(h => {
      const m = M.manifestBySlug[h.slug];
      if (!m) return "";
      return `<a class="hist-row" href="majors/${m.slug}.html" style="--theme: ${M.styleColor(m.style)};">
        <div class="hist-body">
          <div class="hist-cat">${m.category}${h.star ? '<span class="star">★</span>' : ''}</div>
          <div class="hist-title">${m.title}</div>
        </div>
        <div class="hist-time">${h.t || ''}</div>
      </a>`;
    }).join("");
  }

  // 清空
  const clr = document.getElementById("hist-clear");
  if (clr) clr.addEventListener("click", () => {
    if (!confirm("清空所有浏览记录?")) return;
    save(HKEY, []);
    location.reload();
  });
})();
