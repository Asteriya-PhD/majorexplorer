/* detail.js — major 详情页: 收藏 toggle + 浏览记录 */
(async () => {
  await M.init();
  const slug = window.__SLUG__;
  const WKEY = "m.wishlist.v1";
  const HKEY = "m.history.v1";
  if (!slug) return;

  // 收藏 toggle
  const heartIco = document.getElementById("heart-ico");
  const ctaIco = document.getElementById("cta-ico");
  const ctaText = document.getElementById("cta-text");
  const ctaBtn = document.getElementById("cta-btn");
  const ctaDesc = document.getElementById("cta-desc");
  function load(k) { try { return JSON.parse(localStorage.getItem(k) || "[]"); } catch { return []; } }
  function save(k, v) { localStorage.setItem(k, JSON.stringify(v)); }
  function inWish() { return load(WKEY).includes(slug); }
  function syncHeart() {
    const yes = inWish();
    if (heartIco) { heartIco.className = yes ? "heart-on" : "heart-off"; heartIco.textContent = yes ? "♥" : "♡"; }
    if (ctaIco) { ctaIco.textContent = yes ? "♥" : "♡"; }
    if (ctaText) ctaText.textContent = yes ? "已在心愿单" : "加入心愿单";
    if (ctaBtn) ctaBtn.classList.toggle("on", yes);
    if (ctaDesc) ctaDesc.textContent = yes ? "从心愿单移除, 或前往对照院校位次." : "收藏后, 可在推荐里对照院校位次, 看分数能冲哪所.";
  }
  function toggle() {
    const arr = load(WKEY);
    const i = arr.indexOf(slug);
    if (i >= 0) arr.splice(i, 1); else arr.unshift(slug);
    save(WKEY, arr);
    syncHeart();
  }
  document.getElementById("heart-btn")?.addEventListener("click", toggle);
  ctaBtn?.addEventListener("click", e => { e.preventDefault(); toggle(); });
  syncHeart();

  // 浏览历史
  const hist = load(HKEY).filter(h => h.slug !== slug);
  const now = new Date();
  const t = `${now.getMonth() + 1}-${now.getDate()}`;
  hist.unshift({ slug, t, star: true });
  save(HKEY, hist.slice(0, 20));
})();
