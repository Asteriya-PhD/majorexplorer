/* Major Explorer · Mobile Service Worker
 * 缓存策略 (修复 dock tab "Response served by service worker has redirections"):
 *   - HTML 文档 (text/html, navigation): network-first, 不缓存 (让 CF middleware 处理 302)
 *   - 静态资源 (CSS/JS/PNG/JPG/WOFF): stale-while-revalidate
 *   - 数据 (manifest.json, hierarchy): stale-while-revalidate
 *   - 网络失败 HTML 请求 → fallback 到 /m/offline (CF Pages 308 去掉 .html, 直接缓存最终 URL)
 * 版本号: 改这里强制升级
 * Day 47 bump: v3 → v4 (launch SOP)
 * Day 47.5: PC vs mobile 拆开 cache 名 (避免 install 互相覆盖 SHELL)
 */
const CACHE_NAME = "explorer-mobile-v4-day48-1";
const OFFLINE_URL = "/m/offline";
const SHELL = [
  "/m/",
  "/m/index.html",
  "/m/catalog.html",
  "/m/recommendations.html",
  "/m/search.html",
  "/m/wishlist.html",
  "/m/me.html",
  "/m/offline",
  "/m/manifest.json",
  "/m/css/base.css",
  "/m/css/topbar.css",
  "/m/css/dock.css",
  "/m/css/share.css",
  "/js/share.js",
  "/m/js/loader.js",
  "/m/js/dock.js",
  "/m/js/home.js",
  "/m/js/catalog.js",
  "/m/js/recs.js",
  "/m/js/search.js",
  "/m/js/wishlist.js",
  "/m/js/me.js",
  "/m/js/detail.js",
  "/m/icon-192.png",
  "/m/icon-512.png",
];
const DATA_HOSTS = ["/data/"];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(c => c.addAll(SHELL).catch(() => null))
  );
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  // 仅处理同源 GET
  if (e.request.method !== "GET") return;
  if (url.origin !== location.origin) return;

  // 数据 (manifest, hierarchy, strategy): stale-while-revalidate
  if (DATA_HOSTS.some(h => url.pathname.startsWith(h))) {
    e.respondWith(staleWhileRevalidate(e.request));
    return;
  }

  // HTML 文档请求 (navigation 或 text/html): network-first, 不缓存
  // 这样 CF Pages middleware 的 302 redirect 才能正常工作, 不被 sw 拦截
  const isHTML =
    e.request.mode === "navigate" ||
    (e.request.headers.get("accept") || "").includes("text/html");
  if (isHTML) {
    e.respondWith(networkFirstWithOffline(e.request));
    return;
  }

  // 静态资源 (CSS/JS/PNG/JPG/WOFF 等): stale-while-revalidate
  if (url.pathname.startsWith("/m/")) {
    e.respondWith(staleWhileRevalidate(e.request));
    return;
  }

  // 其他: network-first
  e.respondWith(networkFirst(e.request));
});

async function staleWhileRevalidate(req) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(req);
  const network = fetch(req).then(r => {
    // 不缓存 3xx redirect / 4xx 5xx error
    if (r && r.ok) cache.put(req, r.clone());
    return r;
  }).catch(() => cached);
  return cached || network;
}

async function networkFirst(req) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const r = await fetch(req);
    // HTML 不缓存, 这里只 cache 静态资源成功响应
    if (r && r.ok) {
      const ct = r.headers.get("content-type") || "";
      // 不缓存 HTML 文档, 防止 redirect response 被缓存
      if (!ct.includes("text/html")) {
        cache.put(req, r.clone());
      }
    }
    return r;
  } catch (e) {
    const cached = await cache.match(req);
    return cached || new Response("", { status: 504 });
  }
}

// HTML 网络失败 → 返回 offline.html 兜底
async function networkFirstWithOffline(req) {
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
    // 网络失败 + 无缓存 → 返回 offline.html
    const offline = await cache.match(OFFLINE_URL);
    if (offline) return offline;
    return new Response("Offline", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  }
}