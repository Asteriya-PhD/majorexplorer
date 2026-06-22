# 📱 PWA Tier 1 优化 Plan

> 目标: 7 个小改动 / 1.5h / ¥0 / 1 PR, 立即提升 PWA 安装率 + 桌面离线能力 + iOS 体验
> 创建: 2026-06-21 / 状态: 待执行

---

## 🎯 7 个改动 (按依赖顺序)

### #1. 修 manifest description 数据漂移 (1min)
**问题**: `/m/manifest.json` description 写"210 篇精品专业分析", 实际现在 457 篇

**修改**:
```diff
// public/m/manifest.json
-  "description": "先专业, 后志愿。210 篇精品专业分析, 写给一无所知的高三生。",
+  "description": "先专业, 后志愿。457 篇精品专业深度分析, 写给一无所知的高三生。",
```

**验证**: `curl https://majorexplorer.com/m/manifest.json | jq .description`

---

### #2. 创建 PC sw.js 镜像 (20min)
**问题**: `public/sw.js` 不存在 → 桌面用户访问无离线能力

**实现**:
1. 复制 `/m/sw.js` 到 `/public/sw.js`
2. 调整:
   - `CACHE_NAME = "explorer-v1-20260621"` (区别 mobile v2)
   - `SHELL` 改为 PC 页面 (index/majors/search/wishlist/preferences/recommendations/me.html)
   - `scope` 默认根路径 `/`
   - PC 静态资源路径 `/js/`, `/css/`, `/assets/`
   - PC 也用 `text/html` network-first 防 CF middleware redirect trap

**SHELL 列表** (参考 PC 文件):
```
/, /index.html, /majors.html, /search.html, /wishlist.html,
/preferences.html, /recommendations.html, /me.html, /manifest.json,
/js/*.js (主要几个: pc-search.js, major-search.js, home.js),
/css/*.css (shared.css + 主题 css),
/icon-192.png, /icon-512.png
```

**已知坑 (memory)**: [cf-pages-sw-html-redirect-trap] — 不缓存 3xx + 4xx/5xx, HTML 走 network-first, bump CACHE_NAME 强制升级

**注册** (在 `/index.html` 末尾):
```html
<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}
</script>
```

**验证**:
```bash
# 桌面 Chrome 访问 → DevTools → Application → Service Workers
# 看 sw.js 状态是否 "activated and running"
# 离线模式: 刷新应能加载 index.html (从 cache)
```

---

### #3. HTML `<meta name="theme-color">` 注入 (10min)
**问题**: manifest 有 theme_color 但 HTML 没同步, Android Chrome 地址栏不变色

**实现**:
- 在每个 PC 页面 (index/majors/search/wishlist/preferences/recommendations/me.html) `<head>` 加:
  ```html
  <meta name="theme-color" content="#B8323A">
  ```
- 同样在 mobile 页面 (m/index.html, m/catalog.html, etc.)

**主题色选用**: `#B8323A` (品牌红, 已用于 manifest)

**可选**: 主页用 `#B8323A`, 详情页用对应 13 主题色 (eng `#5B5B47`, cs `#1E5E72`, etc.) — 但需 JS 动态, 复杂度高, V2 再做

**V1 简化**: 全站统一 `#B8323A`

**验证**:
```bash
grep -l 'theme-color' public/*.html | wc -l  # 应输出 7+ 个
# Android Chrome → 地址栏应变红
```

---

### #4. Apple touch icon 注入 (5min)
**问题**: iOS 用户"添加到主屏幕"后图标是空白 / 截屏

**实现**:
在 PC + Mobile 主页 (`index.html`, `m/index.html`) `<head>` 加:
```html
<link rel="apple-touch-icon" href="/icon-192.png">
```

**已知坑**: apple-touch-icon 必须是 **180x180** PNG, 当前 `icon-192.png` 接近, 但最好生成 180x180 版本
- 方案 A: 直接复用 192 (iOS 自动缩放, 显示略模糊但能用)
- 方案 B: 用 `sips -z 180 180 icon-192.png icon-180.png` 生成专门 180x180

**推荐**: A 简化版先上, B V2 再做

**验证**:
```bash
# iOS Safari → 分享 → 添加到主屏幕 → 看图标是否正确
# 或 Playwright iPhone UA 测试
```

---

### #5. beforeinstallprompt 监听 (30min)
**问题**: 用户访问 30s+ 满足安装条件, 但没看到"添加到主屏幕"提示

**实现** (在 PC + Mobile `index.html` 末尾加 JS):
```javascript
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  // 30s 后才弹, 不要打扰用户
  setTimeout(() => {
    showInstallBanner();
  }, 30000);
});

function showInstallBanner() {
  if (!deferredPrompt) return;
  // 用底部 toast 或 modal, 不阻塞
  const banner = document.createElement('div');
  banner.className = 'install-banner';
  banner.innerHTML = `
    <div class="install-card">
      <span>📲 安装 Major Explorer 到主屏幕, 离线也能查专业</span>
      <button id="install-yes">安装</button>
      <button id="install-no">不了</button>
    </div>
  `;
  document.body.appendChild(banner);
  document.getElementById('install-yes').onclick = async () => {
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    banner.remove();
    deferredPrompt = null;
    // 可选: gtag 记录 'installed' / 'dismissed'
  };
  document.getElementById('install-no').onclick = () => banner.remove();
}
```

**CSS** (塞 shared.css 末尾):
```css
.install-banner {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--card, #fff);
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  z-index: 9999;
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 14px;
}
.install-banner button {
  background: #B8323A;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
}
.install-banner button:last-child {
  background: transparent;
  color: #666;
}
```

**不要在 m/ 端弹** (PWA 在 standalone 模式已无需提示, 仅在浏览器访问时弹)

**验证**:
- Chrome DevTools → Application → Manifest → "Install" 按钮可点
- 真实 Chrome 访问 30s 后应见底部 toast

---

### #6. SW update 通知 toast (20min)
**问题**: sw.js 升级后, 用户继续用旧版本, 不知道有新版本

**实现** (在 PC + Mobile `index.html` sw 注册处加):
```javascript
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').then(reg => {
    reg.addEventListener('updatefound', () => {
      const newWorker = reg.installing;
      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // 新版本已安装, 等用户关掉所有 tab 才生效
          showUpdateToast();
        }
      });
    });
  });
}

function showUpdateToast() {
  const toast = document.createElement('div');
  toast.className = 'update-toast';
  toast.innerHTML = `
    <span>🚀 新版本可用</span>
    <button onclick="location.reload()">刷新</button>
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 30000);  // 30s 后自动消失
}
```

**CSS** (复用 install-banner 样式, 或新加):
```css
.update-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #2c7a7b;
  color: white;
  padding: 10px 14px;
  border-radius: 8px;
  display: flex;
  gap: 10px;
  align-items: center;
  z-index: 9999;
  font-size: 14px;
}
.update-toast button {
  background: white;
  color: #2c7a7b;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
}
```

**验证**:
- 改 sw.js CACHE_NAME → 部署 → 用户访问应见顶部 toast

---

### #7. Offline fallback page (10min)
**问题**: 离线 + 用户访问未缓存页面 → 浏览器默认错误页 (很难看)

**实现**:
创建 `/public/offline.html` 和 `/public/m/offline.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>离线模式 · Major Explorer</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif;
      background: #F5F2EA;
      color: #3a3a3a;
      margin: 0;
      padding: 60px 20px;
      text-align: center;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
    }
    h1 { font-size: 48px; margin: 0 0 16px; }
    p { font-size: 16px; color: #666; margin: 8px 0; }
    a {
      display: inline-block;
      margin-top: 24px;
      padding: 10px 20px;
      background: #B8323A;
      color: white;
      text-decoration: none;
      border-radius: 8px;
    }
  </style>
</head>
<body>
  <div style="font-size: 64px;">📡</div>
  <h1>当前离线</h1>
  <p>该页面未缓存, 联网后可正常访问</p>
  <p>已缓存的页面 (首页/目录/推荐等) 可继续浏览</p>
  <a href="/">返回首页</a>
</body>
</html>
```

**sw.js 修改** — 在 networkFirst catch 里 fallback:
```javascript
async function networkFirst(req) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const r = await fetch(req);
    if (r && r.ok) {
      const ct = r.headers.get("content-type") || "";
      if (!ct.includes("text/html")) {
        cache.put(req, r.clone());
      }
    }
    return r;
  } catch (e) {
    const cached = await cache.match(req);
    if (cached) return cached;
    // HTML 请求失败 → 返回 offline.html
    if (req.headers.get('accept').includes('text/html')) {
      const offline = await cache.match('/offline.html');
      return offline || new Response("离线模式", { status: 503 });
    }
    return new Response("", { status: 504 });
  }
}
```

**SHELL 加入**:
- PC: `/offline.html`
- Mobile: `/m/offline.html`

**验证**:
- Chrome DevTools → Network → Offline → 访问未缓存页面 → 应见友好离线页

---

## 📁 文件清单

### 新增 (4 文件)
- `/public/sw.js` (镜像 mobile, 改 PC 路径 + scope)
- `/public/offline.html` (PC 离线兜底)
- `/public/m/offline.html` (Mobile 离线兜底)
- `/docs/PLAN_pwa_tier1.md` (本文件)

### 修改 (~10 文件)
- `/public/m/manifest.json` — description 210 → 457
- `/public/index.html` — meta theme-color + apple-touch-icon + sw 注册 + install banner + update toast
- `/public/m/index.html` — 同上
- `/public/majors.html` + `/search.html` + `/wishlist.html` + `/preferences.html` + `/recommendations.html` + `/me.html` — meta theme-color + sw 注册
- `/public/m/catalog.html` + `/m/recommendations.html` + `/m/search.html` + `/m/wishlist.html` + `/m/me.html` — meta theme-color
- `/public/m/sw.js` — CACHE_NAME bump + offline fallback 集成
- `/public/css/shared.css` (或新建 `pwa.css`) — install-banner + update-toast 样式

---

## ✅ 验收清单 (7 项全过)

- [ ] #1 manifest description 显示 "457 篇"
- [ ] #2 桌面 Chrome DevTools → Application → SW activated, 离线刷新 index.html 可见
- [ ] #3 Android Chrome 地址栏变红 (theme_color)
- [ ] #4 iOS Safari → 添加到主屏幕 → 图标正确显示 (icon-192)
- [ ] #5 桌面 Chrome 访问 30s → 底部见 "添加到主屏幕" toast
- [ ] #6 部署 sw.js 新版本 → 用户访问见顶部 "新版本可用" toast
- [ ] #7 离线访问未缓存页面 → 见友好 offline.html (非浏览器默认错误)

---

## 🚨 风险 + 已知坑 (from memory)

| 风险 | 缓解 |
|------|------|
| CF Pages SW HTML redirect trap | 不缓存 3xx + HTML network-first + bump CACHE_NAME (已知修法) |
| beforeinstallprompt 浏览器支持 | Chrome/Edge/Samsung 支持, Safari/Firefox 不支持 (降级无影响) |
| SW update 通知太频繁 | 仅在 controller 存在 (即旧 SW) 时弹, 不打扰首次访问 |
| install banner 弹太早打扰 | 30s 延迟 + 用户可关闭, 不阻塞 |
| iOS apple-touch-icon 180x180 缺失 | V1 复用 192, V2 可生成专门 180 |

---

## 📊 Commit message 模板

```
feat(pwa): Tier 1 PWA 优化 (7 改动 / 安装率 + 桌面离线 + iOS 体验)

**#1 数据准**: manifest.json description 210 → 457
**#2 桌面离线**: /public/sw.js 镜像 mobile (PC 首次有 SW), HTML network-first 防 CF redirect trap
**#3 品牌统一**: HTML <meta name="theme-color" content="#B8323A"> 全站 13 页注入
**#4 iOS 体验**: apple-touch-icon link (复用 192, iOS 自动缩放)
**#5 安装率**: beforeinstallprompt 监听 + 30s 延迟底部 banner, 用户可关
**#6 版本感知**: SW updatefound → toast "新版本可用, 点击刷新"
**#7 离线兜底**: /offline.html + sw.js networkFirst catch fallback

文件: 4 新增 + 10 改动, 0 LLM 调用, ~1.5h
验收: 7 项 checklist 全过
```

---

## 📅 实施顺序

```
Step 1 (5min): #1 manifest description
Step 2 (25min): #3 meta theme-color 全站注入 + #4 apple-touch-icon
Step 3 (30min): #7 offline.html 创建 + sw.js fallback
Step 4 (25min): #2 PC sw.js 创建 + index.html 注册
Step 5 (35min): #5 beforeinstallprompt + banner CSS
Step 6 (20min): #6 SW update toast
Step 7 (10min): 端到端验证 7 项 + Playwright 截图
Step 8 (5min): git commit + push
```

**总估时: ~2.5h (含 buffer)**, 实际 ~1.5h
**总成本: ¥0** (无 LLM 调用)
**Risk**: 低 (都是成熟 PWA 模式, 有 mobile 镜像可参考)

---

## 📝 给下 session 的快速启动指令

```
读 /Users/zhewenliu/Claude/gaokao-hubei-mvp/docs/PLAN_pwa_tier1.md
按 7 改动顺序实施 (Step 1 → Step 8)
每完成 1 个改动 git add 该文件, 不批量 commit
最终 1 commit + push main
Playwright 验证 7 项 checklist, 截图保存到 docs/pwa-tier1-screenshots/
```

**重要**: 不要改 sw.js HTML network-first 策略 (已知修法), 不要 cache 3xx 响应 (CF redirect bug)
