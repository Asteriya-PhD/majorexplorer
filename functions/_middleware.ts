/**
 * functions/_middleware.ts — 手机 UA sniff → 自动 302 到 /m/
 *
 * 触发:
 *   1) user-agent 命中 mobile 特征
 *   2) 路径不在排除列表 (/m/ 自身, /api/, /data/, 静态资源)
 *   3) query string 不含 ?desktop=1
 *
 * 桌面访问保持原样. 用户主动加 ?desktop=1 可强制桌面版.
 */

const MOBILE_TOP_PAGES = new Set([
  "search", "index", "catalog", "recommendations", "wishlist", "me", "offline",
]);

export async function onRequest(context) {
  const { request, next, env } = context;
  const url = new URL(request.url);

  // 1) 已经在 mobile 路径下: 不动 (但要先排除 m/ 顶层页通配)
  if (url.pathname === "/m" || url.pathname.startsWith("/m/")) {
    // Day 41+: m/ 顶层页 (search/index/catalog/...) 被 _redirects /m/:slug 通配误吞 → 404
    // 在 middleware 层直接 serve 物理文件, 绕过 _redirects 通配.
    const segs = url.pathname.replace(/^\/m\/?/, "").split("/").filter(Boolean);
    // 只对 /m/{slug} 或 /m/{slug}.html (单段) 拦截, 不动 /m/majors/{x} (双段)
    if (segs.length === 1) {
      let slug = segs[0];
      // 去掉 .html 后缀
      if (slug.endsWith(".html")) slug = slug.slice(0, -5);
      if (MOBILE_TOP_PAGES.has(slug)) {
        const target = `/m/${slug}.html`;
        try {
          // 用 env.ASSETS 直接拿物理文件 (CF Pages 提供)
          const assetResp = await env.ASSETS.fetch(new URL(target, url));
          if (assetResp && assetResp.status === 200) return assetResp;
        } catch (e) {
          console.warn("[m-middleware] asset fetch failed", slug, e);
        }
        // fallback: 302 浏览器跟 target, 让浏览器拿到 .html
        return Response.redirect(new URL(target, url), 302);
      }
    }
    return next();
  }
  // 2) 排除 API / data / 静态资源
  if (
    url.pathname.startsWith("/api/") ||
    url.pathname.startsWith("/data/") ||
    url.pathname.startsWith("/functions/") ||
    url.pathname.startsWith("/cdn-cgi/") ||
    /\.(js|mjs|css|png|jpe?g|gif|svg|webp|ico|json|xml|txt|woff2?|ttf|map|webmanifest|mp4|webm)$/i.test(url.pathname)
  ) {
    return next();
  }
  // 2.5) Day 41: PC 顶层页 (/search.html) 响应式自适应, mobile UA 直通不要 302 到 /m/
  if (url.pathname === "/search.html" || url.pathname === "/search") {
    return next();
  }
  // 3) ?desktop=1 → 跳过 sniff
  if (url.searchParams.get("desktop") === "1") {
    return next();
  }
  // 4) UA 检测
  const ua = (request.headers.get("user-agent") || "").toLowerCase();
  const isMobile = /iphone|ipad|ipod|android|webos|blackberry|windows phone|opera mini|mobile|tablet|kindle|silk|playbook|bb10|bb11/i.test(ua);
  if (!isMobile) {
    return next();
  }
  // 5) 移动端 → 302 到 /m/<原路径>
  const target = "/m" + (url.pathname === "/" ? "/" : url.pathname) + url.search;
  return new Response(null, {
    status: 302,
    headers: { Location: target },
  });
}