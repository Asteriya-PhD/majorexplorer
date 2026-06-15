/* ─────────────────────────────────────────────
   Mobile Shared JS
   - topbar scrolled 状态 (passive scroll listener)
   - dock active tab 高亮 (pathname 匹配)
   ───────────────────────────────────────────── */

(function () {
  // 1. topbar scrolled class
  const topbar = document.querySelector('.topbar');
  if (topbar) {
    const onScroll = () => topbar.classList.toggle('scrolled', window.scrollY > 8);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // 2. dock active tab (按当前页路径匹配 data-tab 属性)
  const dockTabs = document.querySelectorAll('.dock-tab[data-tab]');
  if (dockTabs.length) {
    const path = location.pathname.replace(/\/$/, '').split('/').pop() || 'index.html';
    const stem = path.replace('.html', '');
    dockTabs.forEach(tab => {
      const t = tab.dataset.tab;
      if (t === stem || (t === 'home' && (stem === 'index' || stem === ''))) {
        tab.classList.add('active');
      }
    });
  }
})();
