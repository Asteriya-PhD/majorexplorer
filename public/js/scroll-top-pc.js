/* scroll-top-pc.js — PC 详情页回到顶部 FAB
 *
 * 滚动 800px 后浮现 ↑ 按钮, 点击平滑回顶
 * 与 mobile 版 scroll-helpers.js 分离, 避免 PC 端踩 calc(var(--dock-h)) 移动端变量
 *
 * 用法: 在 HTML body 末尾加 <script src="/js/scroll-top-pc.js" defer></script>
 */
(() => {
  const fab = document.createElement('button');
  fab.className = 'scroll-top-fab';
  fab.setAttribute('aria-label', '回到顶部');
  fab.textContent = '↑';
  fab.style.cssText = 'position:fixed; right:32px; bottom:32px; z-index:90; width:48px; height:48px; border-radius:50%; background:#B8323A; color:#FBF8F1; border:0; font-size:1.4rem; font-weight:600; box-shadow:0 4px 14px rgba(0,0,0,0.18); opacity:0; transform:translateY(12px); transition:opacity 220ms, transform 220ms; pointer-events:none; cursor:pointer;';
  document.body.appendChild(fab);
  fab.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  window.addEventListener('scroll', () => {
    const show = window.scrollY > 800;
    fab.style.opacity = show ? '1' : '0';
    fab.style.transform = show ? 'translateY(0)' : 'translateY(12px)';
    fab.style.pointerEvents = show ? 'auto' : 'none';
  }, { passive: true });
})();
