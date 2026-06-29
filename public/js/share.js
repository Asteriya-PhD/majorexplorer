/* share.js — 通用分享 + 长图导出 (PC + 移动)
 *
 * 4 能力:
 *   1) Web Share API (移动端优先, 调起系统分享面板 → 微信/朋友圈/QQ/小红书)
 *   2) 复制链接 (兜底, 任何浏览器都支持)
 *   3) 唤起微信/微博 scheme (桌面浏览器降级)
 *   4) html2canvas 截图 → 长图导出 (带 majorexplorer.com 水印, 用于转发扩散品牌)
 *
 * 用法:
 *   <button data-share-trigger>分享</button>
 *   按钮点击自动打开弹层; 长图按钮触发生成.
 *   弹层需要 .share-sheet 元素 (js 自动创建)
 *
 * Plausible 事件: share_open / share_wechat / share_image / share_copy
 */
(function () {
  'use strict';

  const SITE = 'majorexplorer.com';
  const SHARE_CSS_HREF = '/css/share.css';
  const H2C_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';

  // ── 动态加载样式 (避免改 600+ HTML) ──
  function loadCSS(href) {
    if (document.querySelector('link[href="' + href + '"]')) return;
    const l = document.createElement('link');
    l.rel = 'stylesheet';
    l.href = href;
    document.head.appendChild(l);
  }

  // ── 动态加载 html2canvas (CDN, 走 plausible.io 同源白名单思路) ──
  // CSP connect-src 需要加 https://cdnjs.cloudflare.com; script-src 允许 https://cdnjs.cloudflare.com
  function loadHtml2Canvas() {
    return new Promise((resolve, reject) => {
      if (window.html2canvas) return resolve(window.html2canvas);
      const s = document.createElement('script');
      s.src = H2C_CDN;
      s.crossOrigin = 'anonymous';
      s.onload = () => resolve(window.html2canvas);
      s.onerror = () => reject(new Error('html2canvas load failed'));
      document.head.appendChild(s);
    });
  }

  // ── 复制链接 fallback ──
  async function copyLink(url) {
    try {
      await navigator.clipboard.writeText(url);
      return true;
    } catch (e) {
      // 降级: 选中文本
      const ta = document.createElement('textarea');
      ta.value = url;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (_) { ok = false; }
      document.body.removeChild(ta);
      return ok;
    }
  }

  // ── 长图生成 (html2canvas → canvas → blob → 触发下载) ──
  // 根因 (Day 35 v2): 原 selector 选到 hero 内的 .container, 只截首屏
  // 修法: 用 wrapper div 临时包住 body 所有子节点, 截 wrapper (html2canvas 官方推荐)
  // 根因 (Day 35.4): .fade-up 滚动入场动画 opacity:0, wrapper 后 IntersectionObserver
  //   不触发, html2canvas 渲染出来整片透明空白. 修: 临时强制所有 .fade-up 到 visible 状态.
  async function exportImage() {
    const html2canvas = await loadHtml2Canvas();
    const tip = showToast('正在生成图片…');

    // ── 临时 wrapper: 把所有 body 子节点包进一个 div, 让 html2canvas 知道完整尺寸 ──
    const wrapper = document.createElement('div');
    wrapper.id = '__share-wrapper-tmp';
    wrapper.style.cssText = 'position:relative;width:100%;background:#FFFFFF;';
    // 把 body 的所有子节点先搬进 wrapper (排除 share-sheet 自身 + share-fab)
    const nodes = Array.from(document.body.children).filter(n =>
      !n.classList.contains('share-sheet') &&
      !n.classList.contains('share-fab') &&
      !n.classList.contains('share-toast') &&
      !n.classList.contains('share-qr-modal')
    );
    const originals = nodes.map(n => ({ node: n, parent: n.parentNode, next: n.nextSibling }));
    nodes.forEach(n => wrapper.appendChild(n));
    document.body.appendChild(wrapper);

    // ── Day 35.4 关键修复: 强制所有 fade-up/scroll 动画元素到 visible 终态 ──
    // IntersectionObserver 在 DOM 重组后不再触发, .visible class 没加, 元素 opacity:0
    // 临时清空 transition + 强制 opacity:1 / transform:none
    const animatedSelectors = ['.fade-up', '.fade-in', '.reveal', '.scroll-reveal', '[data-reveal]'];
    const restoreOps = [];
    animatedSelectors.forEach(sel => {
      wrapper.querySelectorAll(sel).forEach(el => {
        const op = {
          el,
          opacity: el.style.opacity,
          transform: el.style.transform,
          transition: el.style.transition,
        };
        restoreOps.push(op);
        el.style.setProperty('opacity', '1', 'important');
        el.style.setProperty('transform', 'none', 'important');
        el.style.setProperty('transition', 'none', 'important');
        el.classList.add('visible', 'is-visible', 'is-revealed'); // 兜底加可见 class
      });
    });

    // 等 layout settle (字体/图片/SVG 异步加载)
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    await (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve());

    let canvas;
    try {
      const W = Math.max(wrapper.scrollWidth, document.documentElement.scrollWidth);
      const H = Math.max(wrapper.scrollHeight, document.documentElement.scrollHeight);
      canvas = await html2canvas(wrapper, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#FFFFFF',
        logging: false,
        width: W,
        height: H,
        windowWidth: W,
        windowHeight: H,
        scrollX: 0,
        scrollY: 0,
        // Day 35.4: 禁掉 html2canvas 的 foreignObject rendering (对 inline style + animation 支持差)
        foreignObjectRendering: false,
      });
    } catch (e) {
      console.error('[share] export failed', e);
      tip.textContent = '生成失败, 请尝试复制链接';
      setTimeout(() => tip.remove(), 2200);
      return;
    } finally {
      // ── 恢复动画元素 style ──
      restoreOps.forEach(({ el, opacity, transform, transition }) => {
        el.style.opacity = opacity;
        el.style.transform = transform;
        el.style.transition = transition;
      });
      // ── 恢复 DOM: 把节点搬回 body 原位置 ──
      originals.forEach(({ node, parent, next }) => {
        if (next && next.parentNode === wrapper) {
          wrapper.insertBefore(node, next);
        } else if (next) {
          parent.insertBefore(node, next);
        } else {
          parent.appendChild(node);
        }
      });
      wrapper.remove();
    }

    // 加水印域名 (底部)
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    const pad = Math.round(w * 0.025);
    ctx.save();
    // 背景条
    ctx.fillStyle = 'rgba(184, 50, 58, 0.92)';
    const tagH = Math.round(h * 0.04);
    ctx.fillRect(0, h - tagH, w, tagH);
    // 文字
    ctx.fillStyle = '#FFFFFF';
    ctx.font = `600 ${Math.round(tagH * 0.4)}px "Songti SC", "PingFang SC", serif`;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    ctx.fillText(SITE, pad, h - tagH / 2);
    // 右边小字
    ctx.textAlign = 'right';
    ctx.font = `${Math.round(tagH * 0.32)}px "PingFang SC", sans-serif`;
    ctx.fillText('Major Explorer · 高考专业导览', w - pad, h - tagH / 2);
    ctx.restore();

    // 触发下载
    canvas.toBlob((blob) => {
      if (!blob) { tip.textContent = '生成失败'; return; }
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const slug = location.pathname.split('/').pop().replace('.html', '') || 'major';
      a.download = `${slug}-${SITE}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      tip.textContent = '已保存到下载文件夹';
      setTimeout(() => tip.remove(), 2200);
    }, 'image/png', 0.92);
  }

  // ── Toast ──
  function showToast(msg) {
    const old = document.querySelector('.share-toast');
    if (old) old.remove();
    const el = document.createElement('div');
    el.className = 'share-toast';
    el.textContent = msg;
    document.body.appendChild(el);
    return el;
  }

  // ── 弹层 ──
  // Day 35.3 简化: 移动端只 2 选项 (复制 + 长图), PC 端 6 选项 (微信扫码 + 4 平台 + 长图)
  function buildSheet() {
    if (document.querySelector('.share-sheet')) return;
    loadCSS(SHARE_CSS_HREF);
    const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
    const gridHTML = isMobile ? `
      <button class="share-opt" data-action="copy">
        <span class="share-ico" style="background:#666">链</span>
        <span class="share-label">复制链接</span>
      </button>
      <button class="share-opt" data-action="image">
        <span class="share-ico" style="background:#B8323A">图</span>
        <span class="share-label">生成长图</span>
      </button>
    ` : `
      <button class="share-opt" data-action="wechat">
        <span class="share-ico" style="background:#07C160">微</span>
        <span class="share-label">微信好友</span>
      </button>
      <button class="share-opt" data-action="moments">
        <span class="share-ico" style="background:#07C160">圈</span>
        <span class="share-label">朋友圈</span>
      </button>
      <button class="share-opt" data-action="qq">
        <span class="share-ico" style="background:#12B7F5">Q</span>
        <span class="share-label">QQ</span>
      </button>
      <button class="share-opt" data-action="weibo">
        <span class="share-ico" style="background:#E6162D">博</span>
        <span class="share-label">微博</span>
      </button>
      <button class="share-opt" data-action="xhs">
        <span class="share-ico" style="background:#FF2442">书</span>
        <span class="share-label">小红书</span>
      </button>
      <button class="share-opt" data-action="copy">
        <span class="share-ico" style="background:#666">链</span>
        <span class="share-label">复制链接</span>
      </button>
    `;
    const sheet = document.createElement('div');
    sheet.className = 'share-sheet';
    sheet.innerHTML = `
      <div class="share-sheet-mask" data-share-close></div>
      <div class="share-sheet-panel" role="dialog" aria-label="分享">
        <div class="share-sheet-handle"></div>
        <div class="share-sheet-title">${isMobile ? '保存后分享给朋友' : '分享给朋友'}</div>
        <div class="share-sheet-grid ${isMobile ? 'is-mobile-compact' : ''}">
          ${gridHTML}
        </div>
        ${!isMobile ? '<div class="share-sheet-divider"></div>' : ''}
        ${!isMobile ? `
        <button class="share-opt share-opt-wide" data-action="image">
          <span class="share-ico" style="background:#B8323A">图</span>
          <span class="share-label">生成长图 (带水印, 适合转发)</span>
        </button>` : ''}
        <button class="share-cancel" data-share-close>取消</button>
        <div class="share-sheet-brand">来自 ${SITE} · 长图带品牌水印, 适合转发</div>
      </div>
    `;
    document.body.appendChild(sheet);

    // 事件
    sheet.addEventListener('click', async (ev) => {
      const close = ev.target.closest('[data-share-close]');
      if (close) { closeSheet(); return; }
      const opt = ev.target.closest('.share-opt');
      if (!opt) return;
      const action = opt.dataset.action;
      const url = location.href;
      const title = document.title;
      const text = title + ' — ' + SITE;

      // 优先 Web Share API (移动端最爽)
      if (action === 'native' && navigator.share) {
        try {
          await navigator.share({ title, text, url });
          track('share_native');
        } catch (e) { /* 用户取消 */ }
        closeSheet();
        return;
      }

      // scheme URL (微信/朋友圈/QQ/微博/小红书)
      const schemes = {
        wechat: 'weixin://',
        moments: 'weixin://',
        qq: 'https://connect.qq.com/widget/shareqq/index.html?url=' + encodeURIComponent(url) + '&title=' + encodeURIComponent(title),
        weibo: 'https://service.weibo.com/share/share.php?url=' + encodeURIComponent(url) + '&title=' + encodeURIComponent(text),
        xhs: 'https://www.xiaohongshu.com/discovery/item?url=' + encodeURIComponent(url),
      };
      if (schemes[action]) {
        // 微信/朋友圈 在桌面浏览器走二维码提示, 移动端直接 scheme
        if (action === 'wechat' || action === 'moments') {
          if (/Mobi|Android/i.test(navigator.userAgent)) {
            location.href = schemes[action];
          } else {
            // PC: 弹二维码 (用第三方 API)
            showQRCode(url, action === 'moments' ? '用微信扫一扫，分享到朋友圈' : '用微信扫一扫，分享给好友');
          }
        } else {
          window.open(schemes[action], '_blank', 'noopener');
        }
        track('share_' + action);
        closeSheet();
        return;
      }

      if (action === 'copy') {
        const ok = await copyLink(url);
        showToast(ok ? '已复制链接' : '复制失败, 请手动复制');
        track('share_copy');
        setTimeout(closeSheet, 1200);
        return;
      }

      if (action === 'image') {
        closeSheet();
        exportImage();
        track('share_image');
        return;
      }
    });
  }

  function openSheet() {
    // Day 35.3: 移动端优先 Web Share API (iOS Safari / Android Chrome 原生支持, 弹系统面板)
    // 失败 (桌面浏览器/不支持) 才显示自定义弹层
    const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
    if (isMobile && navigator.share) {
      const url = location.href;
      const title = document.title;
      const text = title + ' — ' + SITE;
      navigator.share({ title, text, url })
        .then(() => { track('share_native'); })
        .catch(() => {
          // 用户取消 / 系统不支持 → fallback 弹层
          buildSheet();
          document.documentElement.classList.add('share-sheet-open');
          requestAnimationFrame(() => {
            const sheet = document.querySelector('.share-sheet');
            if (sheet) sheet.setAttribute('data-open', 'true');
          });
        });
      track('share_open');
      return;
    }
    buildSheet();
    document.documentElement.classList.add('share-sheet-open');
    requestAnimationFrame(() => {
      const sheet = document.querySelector('.share-sheet');
      if (sheet) sheet.setAttribute('data-open', 'true');
    });
    track('share_open');
  }

  function closeSheet() {
    const sheet = document.querySelector('.share-sheet');
    if (sheet) {
      sheet.setAttribute('data-open', 'false');
      setTimeout(() => { sheet.remove(); }, 220);
    }
    document.documentElement.classList.remove('share-sheet-open');
  }

  // ── QR Code (仅 PC 用, 移动端走 scheme) ──
  function showQRCode(url, hint) {
    const modal = document.createElement('div');
    modal.className = 'share-qr-modal';
    modal.innerHTML = `
      <div class="share-qr-mask" data-qr-close></div>
      <div class="share-qr-panel">
        <div class="share-qr-hint">${hint}</div>
        <img class="share-qr-img" alt="QR"
             src="https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(url)}"
             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
        <div class="share-qr-fallback" style="display:none;">
          <div class="share-qr-fallback-url">${url}</div>
          <div class="share-qr-fallback-tip">截图发给朋友, 或在微信粘贴打开</div>
        </div>
        <div class="share-qr-url">${SITE}</div>
        <button class="share-qr-close" data-qr-close>关闭</button>
      </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
      if (e.target.closest('[data-qr-close]')) modal.remove();
    });
    setTimeout(() => modal.remove(), 90000); // 90s 自动关闭
  }

  // ── Plausible 事件追踪 ──
  function track(name) {
    if (typeof window.plausible === 'function') {
      try { window.plausible(name); } catch (_) {}
    }
  }

  // ── 初始化 ──
  function init() {
    // 所有 [data-share-trigger] 自动绑
    document.querySelectorAll('[data-share-trigger]').forEach((btn) => {
      if (btn.__shareBound) return;
      btn.__shareBound = true;
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        openSheet();
      });
    });

    // 全局快捷: Cmd/Ctrl+S 触发生成长图 (桌面端快捷)
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'S') {
        e.preventDefault();
        exportImage();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();