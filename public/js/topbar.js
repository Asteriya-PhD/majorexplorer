/* topbar.js — 全站固定顶部导航 (主页 / 126 精品详情 / 工具页通用)
   渲染位置: <body> 第一个子元素. 自动高亮当前页. 自动同步心愿单计数.
   反馈入口: 顶栏右上"反馈"按钮, 弹 modal → POST /api/report (source="pc")
   依赖: shared.css (.topbar / .topbar-feedback / .feedback-modal 样式)
         + window.WishlistStore (可选, 没加载也不报错)
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
    '    <div class="topbar-right">' +
    '      <nav class="nav-links" aria-label="主导航">' +
    '        <a href="/" class="' + (active === 'home' ? 'active' : '') + '">首页</a>' +
    '        <a href="/majors.html" class="' + (active === 'majors-list' ? 'active' : '') + '">专业目录</a>' +
    '        <a href="/preferences.html" class="' + (active === 'preferences' ? 'active' : '') + '">填偏好</a>' +
    '      </nav>' +
    '      <button class="topbar-feedback" id="topbar-feedback-btn" type="button" aria-label="提个反馈 / 报告问题">反馈</button>' +
    '    </div>' +
    '  </div>' +
    '</header>';

  // 反馈 modal HTML (Day 21: 加 category 细分 — 想看专业 / Bug / 点赞)
  var modalHtml = '' +
    '<div class="feedback-modal" id="topbar-feedback-modal" hidden>' +
    '  <div class="feedback-modal-bg" id="topbar-feedback-modal-bg"></div>' +
    '  <div class="feedback-modal-card">' +
    '    <div class="feedback-modal-head">提个反馈</div>' +
    '    <div class="feedback-modal-hint">选一类, 1 分钟限 1 次 (写多少都行)</div>' +
    '    <div class="fb-category-row" role="radiogroup" aria-label="反馈类型">' +
    '      <label class="fb-cat-label"><input type="radio" name="topbar-fb-cat" value="want" checked>💡 想看某专业</label>' +
    '      <label class="fb-cat-label"><input type="radio" name="topbar-fb-cat" value="bug">🐛 Bug</label>' +
    '      <label class="fb-cat-label"><input type="radio" name="topbar-fb-cat" value="like">👍 点赞</label>' +
    '    </div>' +
    '    <textarea class="feedback-modal-textarea" id="topbar-feedback-text" placeholder="例: 想看「考古学」/ 选科表错了 / 这个排版很棒…"></textarea>' +
    '    <div class="feedback-modal-actions">' +
    '      <button class="fb-btn fb-cancel" id="topbar-fb-cancel" type="button">取消</button>' +
    '      <button class="fb-btn fb-send" id="topbar-fb-send" type="button">发送</button>' +
    '    </div>' +
    '  </div>' +
    '</div>';

  // 注入到 body 第一个子元素位置 (直接 <header>, 不加 wrapper div, 让 sticky 正常 work)
  var body = document.body;
  if (!body) {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }

  function mount() {
    body.insertAdjacentHTML('afterbegin', html);
    // 注入反馈 modal 到 body 末尾 (跟 mobile me.html 一致)
    body.insertAdjacentHTML('beforeend', modalHtml);
    // 隐藏页面原有的 .wl-chip (顶部右上浮动) — 已被新 topbar 取代
    var oldChips = document.querySelectorAll('a.wl-chip');
    oldChips.forEach(function (c) { c.style.display = 'none'; });
    // 心愿单计数 chip
    syncWishlist();
    if (window.WishlistStore && window.WishlistStore.subscribe) {
      window.WishlistStore.subscribe(syncWishlist);
    }
    // 反馈按钮 + modal 事件绑定
    bindFeedback();
  }

  // ── 反馈 modal 事件 (→ /api/report type: feedback, source: "pc") ──
  function bindFeedback() {
    var fbBtn = document.getElementById("topbar-feedback-btn");
    var fbModal = document.getElementById("topbar-feedback-modal");
    var fbBg = document.getElementById("topbar-feedback-modal-bg");
    var fbCancel = document.getElementById("topbar-fb-cancel");
    var fbSend = document.getElementById("topbar-fb-send");
    var fbText = document.getElementById("topbar-feedback-text");
    if (!fbBtn || !fbModal) return;
    function openFb() { fbModal.hidden = false; if (fbText) { fbText.value = ""; fbText.focus(); } }
    function closeFb() { fbModal.hidden = true; }
    fbBtn.addEventListener("click", openFb);
    if (fbBg) fbBg.addEventListener("click", closeFb);
    if (fbCancel) fbCancel.addEventListener("click", closeFb);
    // ESC 关
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !fbModal.hidden) closeFb();
    });
    if (fbSend) {
      // Day 21: 根据当前选中 category 动态换 placeholder
      var fbCatRadios = document.querySelectorAll('input[name="topbar-fb-cat"]');
      var placeholders = {
        want: '想看哪个专业? 写专业名 (例: 考古学 / 中医康复 / 量子信息)',
        bug:  '哪里有 bug? 哪个页面? 怎么复现? — 一句话就行',
        like: '哪点喜欢? 想看更多哪种内容? — 写多少都行',
      };
      fbCatRadios.forEach(function(r) {
        r.addEventListener('change', function() {
          if (fbText) fbText.placeholder = placeholders[r.value] || '';
        });
      });

      fbSend.addEventListener("click", async () => {
        var text = (fbText.value || "").trim();
        // Day 21: 收集当前选中 category
        var checkedCat = document.querySelector('input[name="topbar-fb-cat"]:checked');
        var category = checkedCat ? checkedCat.value : 'want';
        fbSend.disabled = true; fbText.disabled = true; fbCancel.disabled = true;
        var oldText = fbSend.textContent;
        fbSend.textContent = "发送中...";
        try {
          var r = await fetch("/api/report", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type: "feedback", category: category, text: text, source: "pc" }),
          });
          var d = await r.json().catch(function () { return {}; });
          if (r.ok && d.ok) {
            fbSend.textContent = "✓ 已收到, 谢谢!";
            fbSend.classList.add("sent");
            setTimeout(closeFb, 1400);
          } else {
            throw new Error(d.error || ("HTTP " + r.status));
          }
        } catch (e) {
          fbSend.textContent = "✕ 失败, 请稍后重试";
          fbSend.classList.add("failed");
          fbSend.disabled = false; fbText.disabled = false; fbCancel.disabled = false;
          console.error("[topbar.js] feedback failed", e);
          setTimeout(function () {
            fbSend.textContent = oldText; fbSend.classList.remove("failed");
          }, 3000);
        }
      });
    }
  }

  function syncWishlist() {
    var list = (window.WishlistStore && window.WishlistStore.getAll) ? window.WishlistStore.getAll() : [];
    var count = list.length || 0;
    var right = document.querySelector('.topbar .topbar-right');
    if (!right) return;
    // 移除旧的 chip, 创建新的 (放到 .topbar-right 末尾, 跟 nav 同行)
    var old = right.querySelector('.topbar-wishlist-chip');
    if (old) old.remove();
    var chip = document.createElement('a');
    chip.href = '/wishlist.html';
    chip.className = 'topbar-wishlist-chip';
    chip.innerHTML = '🎒 心愿单 <strong>' + count + '</strong>/6 →';
    chip.style.cssText = 'padding: 6px 14px; border: 1.5px solid var(--accent); border-radius: 999px; color: var(--accent); text-decoration: none; font-size: 0.8125rem; font-weight: 500; white-space: nowrap; transition: all 0.2s;';
    right.appendChild(chip);
  }
})();
