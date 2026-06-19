/* scroll-helpers.js — 全站 mobile UX 工具
 *
 * 1) 回到顶部 FAB (滚动 600px 后浮现, ↑ 按钮)
 * 2) topbar scrolled class (滚动 8px 后加 .scrolled 用于显示 crumb)
 *
 * 用法: 在 HTML body 末尾加 <script src="js/scroll-helpers.js"></script>
 * 与 detail 页面的 _template.html 内部 JS 等效, 但避免重复 4-5 次
 */
(() => {
  // ───── 回到顶部 FAB ─────
  const fab = document.createElement('button');
  fab.className = 'scroll-top-fab';
  fab.setAttribute('aria-label', '回到顶部');
  fab.innerHTML = '↑';
  fab.style.cssText = [
    'position:fixed',
    'right:18px',
    'bottom:calc(var(--dock-h) + 20px)',
    'z-index:90',
    'width:42px',
    'height:42px',
    'border-radius:50%',
    'background:var(--theme, var(--accent))',
    'color:#FBF8F1',
    'border:0',
    'font-family:var(--font-heading)',
    'font-size:1.25rem',
    'font-weight:600',
    'box-shadow:0 4px 14px rgba(0,0,0,0.18)',
    'opacity:0',
    'transform:translateY(12px)',
    'transition:opacity 220ms, transform 220ms',
    'pointer-events:none',
    '-webkit-tap-highlight-color:transparent',
    'cursor:pointer',
  ].join(';');
  document.body.appendChild(fab);
  fab.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

  // ───── topbar scrolled class (详情页用) ─────
  const topbar = document.querySelector('.topbar');

  let ticking = false;
  function update() {
    const y = window.scrollY;
    // FAB
    const show = y > 600;
    fab.style.opacity = show ? '1' : '0';
    fab.style.transform = show ? 'translateY(0)' : 'translateY(12px)';
    fab.style.pointerEvents = show ? 'auto' : 'none';
    // topbar scrolled (only if .is-detail)
    if (topbar && topbar.classList.contains('is-detail')) {
      topbar.classList.toggle('scrolled', y > 8);
    }
    ticking = false;
  }
  window.addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(update); ticking = true; }
  }, { passive: true });
  update();
})();