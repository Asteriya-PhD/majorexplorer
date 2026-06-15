/* detail.js — major 详情页: 心愿打分模态框 + 浏览记录 */
(async () => {
  await M.init();
  const slug = window.__SLUG__;
  const title = window.__TITLE__;
  const WKEY = "m.wishlist.v1";
  const HKEY = "m.history.v1";
  if (!slug) return;

  // ─── localStorage 工具 ───
  function load(k) {
    try {
      const v = JSON.parse(localStorage.getItem(k) || "[]");
      if (!Array.isArray(v)) return [];
      return v;
    } catch { return []; }
  }
  function save(k, v) { localStorage.setItem(k, JSON.stringify(v)); }
  // 兼容旧 string[] 格式: 转成 {slug, rating:3} 默认值
  function normalizeWish(arr) {
    return arr.map(item => typeof item === "string"
      ? { slug: item, rating: 3, tag: "", comment: "", addedAt: 0 }
      : item);
  }
  function findWish() { return normalizeWish(load(WKEY)).find(w => w.slug === slug); }
  function saveWish(item) {
    const arr = normalizeWish(load(WKEY)).filter(w => w.slug !== slug);
    arr.unshift({ ...item, slug, addedAt: Date.now() });
    save(WKEY, arr);
  }
  function removeWish() {
    save(WKEY, normalizeWish(load(WKEY)).filter(w => w.slug !== slug));
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
      saveWish({
        rating: curStar,
        comment: (commentEl && commentEl.value.trim()) || "",
      });
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

  // ─── 浏览历史 (写入 slug + 时间) ───
  const hist = load(HKEY).filter(h => h.slug !== slug);
  const now = new Date();
  hist.unshift({ slug, t: `${now.getMonth() + 1}-${now.getDate()}`, star: true });
  save(HKEY, hist.slice(0, 20));
})();