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

  // 3. data-prov-text: 替换 {prov} 占位符 (与 PC topbar.js 一致)
  //    之前只有 PC topbar.js 做替换, mobile recommendations/preferences 裸显 "{prov}位次"
  try {
    var PROV_DISPLAY = { hubei: '湖北', guangdong: '广东', jiangsu: '江苏' };
    var provKey = sessionStorage.getItem('gk.province.v1');
    var provDisplay = PROV_DISPLAY[provKey] || '湖北';
    document.querySelectorAll('[data-prov-text]').forEach(function (el) {
      el.textContent = el.dataset.provText.replace('{prov}', provDisplay);
    });
  } catch (e) { /* sessionStorage 不可用时保持占位符原文 */ }
})();
