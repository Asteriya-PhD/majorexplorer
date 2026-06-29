/* detail.js — major 详情页: 心愿打分 + 浏览历史 + 主题色动态注入
 *
 * 复用 PC 算法:
 *   - WishlistStore (gk.wishlist.v1): 心愿单 CRUD (替换原 localStorage 重复实现)
 *   - WishlistStore.migrate(): 启动时一次性把 m.wishlist.v1 旧数据迁过来
 *   - MobileData.manifestBySlug[slug].theme_color: 主题色 4 色注入
 *
 * PC 算法层 (data-loader / wishlist-store / recommender / major-search) 通过
 * 动态注入加载 (避免改 126 个 detail HTML),路径 ../../js/ = public/js/
 */
(async () => {
  // ─── 动态加载 PC 算法层 (避免改 126 个 detail HTML 的 <head>) ───
  async function loadScript(src) {
    if (document.querySelector('script[src="' + src + '"]')) return;
    await new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = () => reject(new Error("load failed: " + src));
      document.head.appendChild(s);
    });
  }
  try {
    await Promise.all([
      loadScript("../../js/data-loader.js"),
      loadScript("../../js/wishlist-store.js"),
    ]);
  } catch (e) {
    console.warn("[detail.js] PC 算法层加载失败,心愿单功能降级", e);
  }

  // ─── Mobile 数据 + PC 心愿单迁移 ───
  await M.init();
  const slug = window.__SLUG__;
  const HKEY = "m.history.v1";
  if (!slug) return;

  // 一次性迁移: m.wishlist.v1 → gk.wishlist.v1 (幂等)
  if (window.WishlistStore && WishlistStore.migrate) {
    const m = WishlistStore.migrate();
    if (m.migrated > 0) {
      console.log("[detail.js] migrated " + m.migrated + " wishlist items from m.wishlist.v1");
    }
  }

  // ─── 主题色动态注入 (覆盖 HTML :root SSR fallback, 防 FOUC 已写在 :root 里) ───
  const m = M.manifestBySlug[slug];
  if (m && m.theme_color) {
    const root = document.documentElement.style;
    root.setProperty("--theme", m.theme_color.primary);
    root.setProperty("--theme-deep", m.theme_color.deep);
    root.setProperty("--theme-soft", m.theme_color.soft);
    root.setProperty("--theme-gold", m.theme_color.gold);
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", m.theme_color.primary);
  }

  // ─── 心愿单 helpers (基于 PC WishlistStore) ───
  function findWish() {
    return (window.WishlistStore && WishlistStore.get(slug)) || null;
  }
  function saveWish(rating, tag, comment) {
    if (!window.WishlistStore) return { ok: false };
    const maj = M.manifestBySlug[slug] || {};
    return WishlistStore.upsert({
      slug,
      title: maj.title || slug,
      style: maj.style || "humanities",
      category: maj.category || "",
      score: rating,
      rating,
      tag: tag || "",
      comment: comment || "",
    });
  }
  function removeWish() {
    return !!(window.WishlistStore && WishlistStore.remove(slug));
  }

  // ─── 同步按钮状态 ───
  const heartBtn = document.getElementById("heart-btn");
  const heartIco = document.getElementById("heart-ico");
  const heartLabel = document.getElementById("heart-label");
  const ctaIco = document.getElementById("cta-ico");
  const ctaText = document.getElementById("cta-text");
  const ctaBtn = document.getElementById("cta-btn");
  const ctaDesc = document.getElementById("cta-desc");

  function syncHeart() {
    const w = findWish();
    const yes = !!w;
    if (heartIco) {
      heartIco.className = yes ? "heart-on" : "heart-off";
      heartIco.textContent = yes ? "♥" : "♡";
    }
    if (heartLabel) heartLabel.textContent = yes ? (w.rating ? `${w.rating}★` : "已收藏") : "收藏";
    if (heartBtn) heartBtn.classList.toggle("is-on", yes);
    if (ctaIco) ctaIco.textContent = yes ? "♥" : "♡";
    if (ctaText) ctaText.textContent = yes ? "已加入心愿单" : "加入心愿单";
    if (ctaBtn) ctaBtn.classList.toggle("on", yes);
    if (ctaDesc) ctaDesc.textContent = yes
      ? `评分 ${w.rating || "—"}/5 · ${w.tag || "未分类"} · 长按修改`
      : "收藏后打分排序, 后续在心愿单对照院校位次";
  }
  syncHeart();

  // ─── 模态框逻辑 ───
  const modal = document.getElementById("wish-modal");
  const starRow = document.getElementById("star-row");
  const starHint = document.getElementById("star-hint");
  const saveBtn = document.getElementById("wish-save");
  const removeBtn = document.getElementById("wish-remove");
  const commentEl = document.getElementById("wish-comment");
  const starBtns = starRow ? starRow.querySelectorAll(".star-btn") : [];

  const HINTS = ["再想想", "一般般", "还可以", "很不错", "非常推荐"];
  let curStar = 0;

  function resetModal() {
    curStar = 0;
    if (commentEl) commentEl.value = "";
    starBtns.forEach(b => b.classList.remove("is-on"));
    if (starHint) starHint.textContent = "点击星星选择评分";
    if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = "保存到心愿单"; }
    if (removeBtn) removeBtn.hidden = true;
  }
  function fillModal(w) {
    curStar = w.rating || 0;
    if (commentEl) commentEl.value = w.comment || "";
    starBtns.forEach((b, i) => b.classList.toggle("is-on", i < curStar));
    if (starHint) starHint.textContent = curStar > 0 ? `${curStar} 星 · ${HINTS[curStar - 1]}` : "点击星星选择评分";
    if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = "更新心愿单"; }
    if (removeBtn) removeBtn.hidden = false;
  }
  function openModal() {
    if (!modal) return;
    resetModal();
    const existing = findWish();
    if (existing) fillModal(existing);
    modal.hidden = false;
    document.body.style.overflow = "hidden";
  }
  function closeModal() {
    if (!modal) return;
    modal.hidden = true;
    document.body.style.overflow = "";
  }

  // 星星点击
  starBtns.forEach((b, i) => {
    b.addEventListener("click", () => {
      curStar = i + 1;
      starBtns.forEach((bb, idx) => bb.classList.toggle("is-on", idx < curStar));
      if (starHint) starHint.textContent = `${curStar} 星 · ${HINTS[curStar - 1]}`;
      if (saveBtn) saveBtn.disabled = false;
    });
  });
  // 关闭
  if (modal) {
    modal.querySelectorAll("[data-close]").forEach(el => {
      el.addEventListener("click", closeModal);
    });
  }
  // 保存 / 更新
  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      if (curStar === 0) return;
      saveWish(curStar, "", (commentEl && commentEl.value.trim()) || "");
      closeModal();
      syncHeart();
      if (window.M && M.toast) M.toast(`已收藏 · ${curStar}星`);
    });
  }
  // 移除
  if (removeBtn) {
    removeBtn.addEventListener("click", () => {
      removeWish();
      closeModal();
      syncHeart();
      if (window.M && M.toast) M.toast("已从心愿单移除");
    });
  }

  // ─── 触发: 爱心按钮 + 底部 CTA ───
  if (heartBtn) heartBtn.addEventListener("click", openModal);
  if (ctaBtn) ctaBtn.addEventListener("click", e => { e.preventDefault(); openModal(); });

  // Day 36 P1-12: 顶部 heart 按钮 (mobile _template.html 专用)
  // Day 41 fix: PC /js/share.js 也绑 #top-heart-btn (Day 35.9) → 双弹窗.
  // 检测 __heartBound flag (share.js 行 770 设), 若已绑则跳过.
  const topHeartBtn = document.getElementById("top-heart-btn");
  if (topHeartBtn && !topHeartBtn.__heartBound) {
    topHeartBtn.__heartBound = true;
    topHeartBtn.addEventListener("click", (e) => {
      e.preventDefault();
      openModal();
    });
  }

  // ─── 浏览历史 (写入 slug + 时间) ───
  function loadHistory() {
    try {
      const v = JSON.parse(localStorage.getItem(HKEY) || "[]");
      return Array.isArray(v) ? v : [];
    } catch { return []; }
  }
  function saveHistory(arr) { localStorage.setItem(HKEY, JSON.stringify(arr)); }

  const hist = loadHistory().filter(h => h.slug !== slug);
  const now = new Date();
  hist.unshift({ slug, t: `${now.getMonth() + 1}-${now.getDate()}`, star: true });
  saveHistory(hist.slice(0, 20));
})();
