/* Major Explorer · PC Service Worker (v1)
 * 缓存策略 (与 mobile 一致, 防 CF Pages SW HTML redirect trap):
 *   - HTML 文档: network-first, 不缓存
 *   - 静态资源 (/js/, /css/, /assets/): stale-while-revalidate
 *   - 数据 (/data/): stale-while-revalidate
 *   - HTML 网络失败 → fallback 到 /offline (CF Pages 308 去掉 .html, 直接缓存最终 URL)
 * 版本号: 改这里强制升级
 */
const CACHE_NAME = "explorer-v3-30ea0279";
const OFFLINE_URL = "/offline";
const SHELL = [
  "/",
  "/index.html",
  "/majors.html",
  "/search.html",
  "/wishlist.html",
  "/preferences.html",
  "/recommendations.html",
  "/offline",
  "/manifest.json",
  "/css/shared.css",
  "/css/share.css",
  "/js/data-loader.js",
  "/js/share.js",
  "/js/major-search.js",
  "/js/pc-search.js",
  "/js/topbar.js",
  "/js/ui-helpers.js",
  "/js/wishlist-store.js",
  "/js/recommender.js",
  "/js/preferences-form.js",
  "/js/discipline-pills.js",
  "/js/strategy-pills.js",
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

  // 数据 (manifest.json, hierarchy, strategy): stale-while-revalidate
  if (DATA_HOSTS.some(h => url.pathname.startsWith(h))) {
    e.respondWith(staleWhileRevalidate(e.request));
    return;
  }

  // HTML 文档请求: network-first + offline fallback
  const isHTML =
    e.request.mode === "navigate" ||
    (e.request.headers.get("accept") || "").includes("text/html");
  if (isHTML) {
    e.respondWith(networkFirstWithOffline(e.request));
    return;
  }

  // 静态资源 (CSS/JS/PNG/JPG/WOFF): stale-while-revalidate
  if (url.pathname.startsWith("/js/") ||
      url.pathname.startsWith("/css/") ||
      url.pathname.startsWith("/assets/") ||
      url.pathname.startsWith("/m/")) {
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
    if (r && r.ok) {
      const ct = r.headers.get("content-type") || "";
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
    const offline = await cache.match(OFFLINE_URL);
    if (offline) return offline;
    return new Response("Offline", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  }
}