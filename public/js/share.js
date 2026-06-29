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
  async function exportImage() {
    const html2canvas = await loadHtml2Canvas();
    // 选最长一段 (PC: .ovv-container 找不到就用 main, 移动: 整页)
    const target =
      document.querySelector('main, .container, .ovv-container') ||
      document.body;

    // 提示
    const tip = showToast('正在生成图片…');

    try {
      const canvas = await html2canvas(target, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#FFFFFF',
        logging: false,
        windowWidth: target.scrollWidth,
        windowHeight: target.scrollHeight,
      });

      // 加水印域名 (右下角)
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
    } catch (e) {
      console.error('[share] export failed', e);
      tip.textContent = '生成失败, 请尝试复制链接';
      setTimeout(() => tip.remove(), 2200);
    }
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
  function buildSheet() {
    if (document.querySelector('.share-sheet')) return;
    loadCSS(SHARE_CSS_HREF);
    const sheet = document.createElement('div');
    sheet.className = 'share-sheet';
    sheet.innerHTML = `
      <div class="share-sheet-mask" data-share-close></div>
      <div class="share-sheet-panel" role="dialog" aria-label="分享">
        <div class="share-sheet-handle"></div>
        <div class="share-sheet-title">分享给朋友</div>
        <div class="share-sheet-grid">
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
        </div>
        <div class="share-sheet-divider"></div>
        <button class="share-opt share-opt-wide" data-action="image">
          <span class="share-ico" style="background:#B8323A">图</span>
          <span class="share-label">生成长图 (带水印, 适合转发)</span>
        </button>
        <button class="share-cancel" data-share-close>取消</button>
        <div class="share-sheet-brand">来自 ${SITE}</div>
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
        <img class="share-qr-img" alt="QR" src="https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(url)}">
        <div class="share-qr-url">${SITE}</div>
        <button class="share-qr-close" data-qr-close>关闭</button>
      </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
      if (e.target.closest('[data-qr-close]')) modal.remove();
    });
    setTimeout(() => modal.remove(), 60000); // 60s 自动关闭
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