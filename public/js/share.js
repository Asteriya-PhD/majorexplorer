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
  // Day 35.5 PC 简化: 微信 (scheme) + QQ (scheme) + 复制链接 + 长图, 去微博/小红书/朋友圈
  function buildSheet() {
    if (document.querySelector('.share-sheet:not([data-mobile-fallback])')) return;
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
            <span class="share-label">微信</span>
          </button>
          <button class="share-opt" data-action="qq">
            <span class="share-ico" style="background:#12B7F5">Q</span>
            <span class="share-label">QQ</span>
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

      // ── PC scheme URL 调起客户端 (Day 35.5.1) ──
      // 微信 PC: weixin:// 100% 有效
      // QQ PC: tencent:// 各版本兼容性差, 用户多装了 NT 新版 QQ
      //   修法: 微信走 scheme + 复制, QQ 只复制链接 + Toast 引导手动操作
      //        (避免误报"未检测到", 用户体验更直接)
      if (action === 'wechat') {
        const ok = await copyLink(url);
        setTimeout(() => {
          showToast(ok
            ? '链接已复制, 打开微信粘贴发送'
            : `请手动复制链接: ${url}`);
        }, 200);
        // 唤起微信 PC 客户端
        setTimeout(() => {
          try { window.location.href = 'weixin://'; } catch (_) {}
        }, 100);
        track('share_wechat');
        closeSheet();
        return;
      }

      if (action === 'qq') {
        // QQ 不尝试唤起 (tencent:// 各版本兼容性差, 误判多)
        // 直接复制 + 提示, 用户去 QQ 粘贴更可靠
        const ok = await copyLink(url);
        showToast(ok
          ? '链接已复制, 打开 QQ 粘贴发送 (Ctrl+V)'
          : `请手动复制链接: ${url}`);
        track('share_qq');
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
    // Day 35.5 移动端: 先生成长图, 直接 navigator.share({files:[blob]})
    // iOS/Android 系统面板会出现「保存到相册/微信好友/朋友圈/QQ/微博/小红书」一键分发
    // 失败 (桌面浏览器 / 老 WebView) 才降级到自建弹层
    const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
    if (isMobile) {
      openMobileShare();
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

  // ── Day 35.5 移动端分享: 直接 share files ──
  // ── Day 35.8 移动端分享: 直接显示名片 modal ──
  // 完全不调 navigator.share (iOS 微信内置面板唤不起, 体验差)
  // 改成直接 showShareCardModal 显示 <img>, 用户长按 → 保存到相册 → 微信选图发送
  async function openMobileShare() {
    const tip = showToast('正在生成分享名片…');
    let blob;
    try {
      blob = await generateImageBlob('card');
    } catch (e) {
      console.error('[share mobile] card failed', e);
      tip.textContent = '生成失败, 请尝试复制链接';
      setTimeout(() => tip.remove(), 1800);
      buildMobileFallback();
      return;
    }
    tip.remove();
    // 直接显示 modal (iOS/Android 都用, 不再尝试 navigator.share)
    showShareCardModal(blob);
  }

  // ── 移动端名片 modal (iOS 长按保存) ──
  function showShareCardModal(blob) {
    const url = URL.createObjectURL(blob);
    const slug = location.pathname.split('/').pop().replace('.html', '') || 'major';
    // 自动复制链接兜底
    copyLink(location.href);

    // 先关闭现有 sheet
    document.querySelectorAll('.share-sheet, .share-card-modal').forEach(el => el.remove());

    const modal = document.createElement('div');
    modal.className = 'share-card-modal';
    modal.innerHTML = `
      <div class="share-card-mask" data-card-close></div>
      <div class="share-card-panel" role="dialog" aria-label="分享名片">
        <div class="share-card-handle"></div>
        <div class="share-card-title">长按图片 → 保存到相册</div>
        <div class="share-card-tip">然后在微信/朋友圈/小红书选择图片发送, 朋友扫码即可查看完整专业介绍</div>
        <img class="share-card-img" src="${url}" alt="分享名片" draggable="false">
        <div class="share-card-actions">
          <button class="share-card-btn-primary" data-card-close>我已保存, 完成</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    document.documentElement.classList.add('share-sheet-open');

    modal.addEventListener('click', (ev) => {
      if (ev.target.closest('[data-card-close]')) {
        modal.remove();
        document.documentElement.classList.remove('share-sheet-open');
        URL.revokeObjectURL(url);
      }
    });
    setTimeout(() => modal.setAttribute('data-open', 'true'), 16);
    track('share_card_modal');
  }

  // ── 用户切回页面 (share 后从微信/QQ 回来) 提示 ──
  function onReturnFromShare() {
    const handler = () => {
      if (document.visibilityState === 'visible') {
        document.removeEventListener('visibilitychange', handler);
        showToast('已分享 ✓ 到目标 App, 长按粘贴链接');
        setTimeout(() => {
          document.querySelector('.share-toast')?.remove();
        }, 3500);
      }
    };
    document.addEventListener('visibilitychange', handler);
  }

  // ── 移动端降级弹层: 复制链接 + 生成长图 ──
  function buildMobileFallback() {
    // 复用 buildSheet 但强制 isMobile 风格
    const sheet = document.createElement('div');
    sheet.className = 'share-sheet';
    sheet.setAttribute('data-mobile-fallback', 'true');
    sheet.innerHTML = `
      <div class="share-sheet-mask" data-share-close></div>
      <div class="share-sheet-panel" role="dialog" aria-label="分享">
        <div class="share-sheet-handle"></div>
        <div class="share-sheet-title">分享给朋友</div>
        <div class="share-sheet-grid is-mobile-compact">
          <button class="share-opt" data-action="copy">
            <span class="share-ico" style="background:#666">链</span>
            <span class="share-label">复制链接</span>
          </button>
          <button class="share-opt" data-action="image">
            <span class="share-ico" style="background:#B8323A">图</span>
            <span class="share-label">保存长图</span>
          </button>
        </div>
        <button class="share-cancel" data-share-close>取消</button>
        <div class="share-sheet-brand">来自 ${SITE} · 长图带品牌水印, 适合转发</div>
      </div>
    `;
    document.body.appendChild(sheet);
    sheet.addEventListener('click', async (ev) => {
      const close = ev.target.closest('[data-share-close]');
      if (close) { closeSheet(); return; }
      const opt = ev.target.closest('.share-opt');
      if (!opt) return;
      const action = opt.dataset.action;
      const url = location.href;
      if (action === 'copy') {
        const ok = await copyLink(url);
        showToast(ok ? '已复制链接' : '复制失败');
        track('share_copy');
        setTimeout(closeSheet, 1200);
      }
      if (action === 'image') {
        closeSheet();
        exportImage();
        track('share_image');
      }
    });
    document.documentElement.classList.add('share-sheet-open');
    requestAnimationFrame(() => sheet.setAttribute('data-open', 'true'));
  }

  // ── 提取长图生成逻辑, 让 openMobileShare / exportImage 复用 ──
  // Day 35.6 加 mode: 'full' (PC 长图, 整页) 或 'card' (移动端分享名片 1080×1500)
  async function generateImageBlob(mode = 'full') {
    if (mode === 'card') return await generateShareCard();
    return await generateFullPageImage();
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  // ── 移动端分享名片 (Day 35.6) ──
  // 1080×1500 固定比例, 含: 大标题 + 简介 + 二维码 + 网址 + 水印
  // iOS 长按 <img> 可保存到相册, 这是 iOS Web 唯一可靠的存相册方式
  async function generateShareCard() {
    const html2canvas = await loadHtml2Canvas();
    const card = document.createElement('div');
    card.id = '__share-card-tmp';
    card.style.cssText = `
      width: 1080px;
      padding: 80px 70px 140px;
      background: linear-gradient(155deg, #FAF7F2 0%, #F0E8DA 100%);
      font-family: 'Songti SC', 'SimSun', serif;
      color: #1A1A1A;
      position: fixed;
      top: -10000px; left: 0;
      z-index: -1;
      box-sizing: border-box;
    `;
    const slug = (location.pathname.split('/').pop().replace('.html', '') || 'major').trim();
    const title = (window.__TITLE__ || document.title.split(' · ')[0] || slug).trim();
    const url = location.href;
    const tagline = (document.querySelector('.hero-tagline, .lede, p.lede')?.textContent || '').trim().slice(0, 200);
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(url)}`;

    card.innerHTML = `
      <div style="font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 22px; letter-spacing: 4px; color: #B8323A; text-transform: uppercase; margin-bottom: 30px;">
        § Major Explorer · 高考专业导览
      </div>
      <div style="font-size: 96px; font-weight: 600; line-height: 1.15; color: #1A1A1A; margin-bottom: 40px; letter-spacing: 0.02em;">
        ${escapeHtml(title)}
      </div>
      <div style="width: 80px; height: 4px; background: #B8323A; margin-bottom: 36px;"></div>
      <div style="font-size: 30px; line-height: 1.65; color: #4A4A4A; margin-bottom: 50px; max-width: 940px;">
        ${escapeHtml(tagline) || '专业介绍 · 课程 · 院校 · 雇主 · 薪资 · 避坑'}
      </div>
      <div style="display: flex; align-items: flex-start; gap: 50px; margin-top: 40px;">
        <img src="${qrUrl}" crossorigin="anonymous" style="width: 260px; height: 260px; border: 1px solid rgba(0,0,0,0.08); border-radius: 12px; background: white; padding: 10px;" alt="QR">
        <div style="flex: 1; padding-top: 12px;">
          <div style="font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 20px; color: #8B7355; letter-spacing: 2px; margin-bottom: 16px; text-transform: uppercase;">
            SCAN TO READ
          </div>
          <div style="font-size: 26px; line-height: 1.55; color: #1A1A1A; word-break: break-all; font-family: 'PingFang SC', sans-serif;">
            扫码查看完整专业介绍<br>课程 · 院校 · 雇主 · 薪资 · 避坑
          </div>
          <div style="margin-top: 20px; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 22px; color: #B8323A; letter-spacing: 1px;">
            ${escapeHtml(SITE)}
          </div>
        </div>
      </div>
      <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 100px; background: linear-gradient(90deg, #B8323A 0%, #D97706 100%); display: flex; align-items: center; justify-content: space-between; padding: 0 70px; box-sizing: border-box;">
        <div style="font-family: 'Songti SC', serif; font-size: 32px; font-weight: 600; color: white; letter-spacing: 0.05em;">
          ${escapeHtml(SITE)}
        </div>
        <div style="font-family: 'PingFang SC', sans-serif; font-size: 22px; color: rgba(255,255,255,0.92);">
          Major Explorer · 高考专业导览
        </div>
      </div>
    `;
    document.body.appendChild(card);

    // 等 QR 图加载完成
    const qrImg = card.querySelector('img');
    await new Promise((resolve) => {
      if (qrImg.complete && qrImg.naturalWidth > 0) return resolve();
      qrImg.onload = () => resolve();
      qrImg.onerror = () => resolve();
      setTimeout(resolve, 4000);
    });
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));

    try {
      const canvas = await html2canvas(card, {
        scale: 1,
        useCORS: true,
        backgroundColor: '#FAF7F2',
        logging: false,
        width: 1080,
        height: card.scrollHeight,
        windowWidth: 1080,
        windowHeight: card.scrollHeight,
        foreignObjectRendering: false,
      });
      return await new Promise((resolve, reject) => {
        canvas.toBlob(b => b ? resolve(b) : reject(new Error('toBlob null')), 'image/png', 0.92);
      });
    } finally {
      card.remove();
    }
  }

  // ── PC 端长图 (整页 + 水印) ──
  async function generateFullPageImage() {
    const html2canvas = await loadHtml2Canvas();
    const wrapper = document.createElement('div');
    wrapper.id = '__share-wrapper-tmp';
    wrapper.style.cssText = 'position:relative;width:100%;background:#FFFFFF;';
    const nodes = Array.from(document.body.children).filter(n =>
      !n.classList.contains('share-sheet') &&
      !n.classList.contains('share-fab') &&
      !n.classList.contains('share-toast') &&
      !n.classList.contains('share-qr-modal') &&
      !n.classList.contains('hero-heart-bubble')
    );
    const originals = nodes.map(n => ({ node: n, parent: n.parentNode, next: n.nextSibling }));
    nodes.forEach(n => wrapper.appendChild(n));
    document.body.appendChild(wrapper);

    const animatedSelectors = ['.fade-up', '.fade-in', '.reveal', '.scroll-reveal', '[data-reveal]'];
    const restoreOps = [];
    animatedSelectors.forEach(sel => {
      wrapper.querySelectorAll(sel).forEach(el => {
        const op = { el, opacity: el.style.opacity, transform: el.style.transform, transition: el.style.transition };
        restoreOps.push(op);
        el.style.setProperty('opacity', '1', 'important');
        el.style.setProperty('transform', 'none', 'important');
        el.style.setProperty('transition', 'none', 'important');
        el.classList.add('visible', 'is-visible', 'is-revealed');
      });
    });

    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    await (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve());

    try {
      const W = Math.max(wrapper.scrollWidth, document.documentElement.scrollWidth);
      const H = Math.max(wrapper.scrollHeight, document.documentElement.scrollHeight);
      const canvas = await html2canvas(wrapper, {
        scale: 2, useCORS: true, backgroundColor: '#FFFFFF', logging: false,
        width: W, height: H, windowWidth: W, windowHeight: H,
        scrollX: 0, scrollY: 0, foreignObjectRendering: false,
      });

      // 加水印
      const ctx = canvas.getContext('2d');
      const w = canvas.width, h = canvas.height;
      const pad = Math.round(w * 0.025);
      ctx.save();
      ctx.fillStyle = 'rgba(184, 50, 58, 0.92)';
      const tagH = Math.round(h * 0.04);
      ctx.fillRect(0, h - tagH, w, tagH);
      ctx.fillStyle = '#FFFFFF';
      ctx.font = `600 ${Math.round(tagH * 0.4)}px "Songti SC", "PingFang SC", serif`;
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'left';
      ctx.fillText(SITE, pad, h - tagH / 2);
      ctx.textAlign = 'right';
      ctx.font = `${Math.round(tagH * 0.32)}px "PingFang SC", sans-serif`;
      ctx.fillText('Major Explorer · 高考专业导览', w - pad, h - tagH / 2);
      ctx.restore();

      return await new Promise((resolve, reject) => {
        canvas.toBlob(b => b ? resolve(b) : reject(new Error('toBlob null')), 'image/png', 0.92);
      });
    } finally {
      restoreOps.forEach(({ el, opacity, transform, transition }) => {
        el.style.opacity = opacity; el.style.transform = transform; el.style.transition = transition;
      });
      originals.forEach(({ node, parent, next }) => {
        if (next && next.parentNode === wrapper) wrapper.insertBefore(node, next);
        else if (next) parent.insertBefore(node, next);
        else parent.appendChild(node);
      });
      wrapper.remove();
    }
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
  // Day 35.5: 加顶栏心心 + hero-heart 心愿单联动
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

    // ── 心愿单联动 (顶栏心心 + hero-heart) ──
    bindHeartButtons();

    // 全局快捷: Cmd/Ctrl+S 触发生成长图 (桌面端快捷)
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'S') {
        e.preventDefault();
        exportImage();
      }
    });
  }

  // ── Day 35.5 心愿单联动 ──
  // Day 35.9: 只绑顶栏心心 (#top-heart-btn), 不绑 .hero-heart (那个有 generator 自带逻辑)
  // 避免两个 handler 重复触发 + 视觉上"两个爱心"实际就是同一个功能
  function bindHeartButtons() {
    const slug = (window.__SLUG__ || location.pathname.split('/').pop().replace('.html', '')).trim();
    const title = (window.__TITLE__ || document.title.split(' · ')[0] || '').trim();

    const btn = document.querySelector('#top-heart-btn');
    if (!btn) return;

    const isOn = !!(window.WishlistStore && WishlistStore.get && WishlistStore.get(slug));
    if (isOn) btn.classList.add('is-on');

    // 同步 hero-heart 视觉状态 (用户点顶栏或 hero 都应联动)
    const heroHeart = document.querySelector('.hero-heart');
    if (heroHeart && isOn) heroHeart.classList.add('is-on');

    function beat() {
      btn.classList.remove('beat');
      void btn.offsetWidth;
      btn.classList.add('beat');
    }

    if (btn.__heartBound) return;
    btn.__heartBound = true;
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!window.WishlistStore) {
        showToast('心愿单暂不可用');
        return;
      }
      const nowOn = WishlistStore.get(slug);
      if (nowOn) {
        WishlistStore.remove(slug);
        btn.classList.remove('is-on');
        if (heroHeart) heroHeart.classList.remove('is-on');
        showToast('已移出心愿单');
      } else {
        WishlistStore.upsert({
          slug,
          title,
          tags: [],
          score: 0,
          note: '',
          addedAt: Date.now(),
        });
        btn.classList.add('is-on');
        if (heroHeart) {
          heroHeart.classList.add('is-on');
          // 触发 hero-heart 原本的 beat 动画 (如果有)
          const heroIco = heroHeart.querySelector('.heart-ico, .heart-on, .heart-off');
          if (heroIco) {
            heroIco.classList.remove('beat');
            void heroIco.offsetWidth;
            heroIco.classList.add('beat');
          }
        }
        showToast('已加入志愿推荐 ✓');
      }
      beat();
      track(nowOn ? 'wishlist_remove' : 'wishlist_add');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();