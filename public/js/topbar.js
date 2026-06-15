/* topbar.js — 全站固定顶部导航 (主页 / 126 精品详情 / 工具页通用)
   渲染位置: <body> 第一个子元素. 自动高亮当前页. 自动同步心愿单计数.
   依赖: shared.css (.topbar 样式) + window.WishlistStore (可选, 没加载也不报错)
*/
(function () {
  'use strict';
  if (window.__TOPBAR_MOUNTED__) return;
  window.__TOPBAR_MOUNTED__ = true;

  var path = location.pathname;
  var slugMatch = path.match(/\/([a-z][a-z0-9-]*)\.html$/);
  var slug = slugMatch ? slugMatch[1] : '';

  // 决定哪个链接 active
  function activeKey() {
    if (path === '/' || path === '/index.html') return 'home';
    if (slug === 'majors') return 'majors-list';
    if (slug === 'wishlist') return 'wishlist';
    if (slug === 'preferences') return 'preferences';
    if (slug === 'recommendations') return 'recommendations';
    if (slug === 'strategy') return 'strategy';
    if (path === '/majors.html') return 'majors-list';
    if (path === '/wishlist.html') return 'wishlist';
    if (path === '/preferences.html') return 'preferences';
    if (path === '/recommendations.html') return 'recommendations';
    if (path === '/strategy.html') return 'strategy';
    // 精品详情: 高亮 "majors-list" (顶部链接的"精品专业"组)
    if (path.match(/^\/[a-z][a-z0-9-]*\.html$/)) return 'majors-list';
    return '';
  }
  var active = activeKey();

  var html = '' +
    '<header class="topbar">' +
    '  <div class="container">' +
    '    <a class="brand" href="/">' +
    '      Major Explorer<span class="sub">2026 高考 · 湖北 · 先专业, 后志愿</span>' +
    '    </a>' +
    '    <nav class="nav-links" aria-label="主导航">' +
    '      <a href="/" class="' + (active === 'home' ? 'active' : '') + '">首页</a>' +
    '      <a href="/majors.html" class="' + (active === 'majors-list' ? 'active' : '') + '">精品专业</a>' +
    '      <a href="/majors.html" class="' + (active === 'majors-list' ? 'active' : '') + '">专业目录</a>' +
    '      <a href="/preferences.html" class="' + (active === 'preferences' ? 'active' : '') + '">填偏好</a>' +
    '    </nav>' +
    '  </div>' +
    '</header>';

  // 注入到 body 第一个子元素位置 (直接 <header>, 不加 wrapper div, 让 sticky 正常 work)
  var body = document.body;
  if (!body) {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }

  function mount() {
    body.insertAdjacentHTML('afterbegin', html);
    // 隐藏页面原有的 .wl-chip (顶部右上浮动) — 已被新 topbar 取代
    var oldChips = document.querySelectorAll('a.wl-chip');
    oldChips.forEach(function (c) { c.style.display = 'none'; });
    // 心愿单计数 chip
    syncWishlist();
    if (window.WishlistStore && window.WishlistStore.subscribe) {
      window.WishlistStore.subscribe(syncWishlist);
    }
  }

  function syncWishlist() {
    var list = (window.WishlistStore && window.WishlistStore.getAll) ? window.WishlistStore.getAll() : [];
    var count = list.length || 0;
    var topbar = document.querySelector('.topbar');
    if (!topbar) return;
    var container = topbar.querySelector('.container');
    if (!container) return;
    // 移除旧的 chip, 创建新的
    var old = container.querySelector('.topbar-wishlist-chip');
    if (old) old.remove();
    var chip = document.createElement('a');
    chip.href = '/wishlist.html';
    chip.className = 'topbar-wishlist-chip';
    chip.innerHTML = '🎒 心愿单 <strong>' + count + '</strong>/6 →';
    chip.style.cssText = 'margin-left: auto; padding: 6px 14px; border: 1.5px solid var(--accent); border-radius: 999px; color: var(--accent); text-decoration: none; font-size: 0.8125rem; font-weight: 500; white-space: nowrap; transition: all 0.2s;';
    container.appendChild(chip);
  }
})();
