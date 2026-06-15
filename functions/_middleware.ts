/**
 * functions/_middleware.ts — 手机 UA sniff → 自动 302 到 /m/
 *
 * 触发:
 *   1) user-agent 命中 mobile 特征
 *   2) 路径不在排除列表 (/m/ 自身, /api/, /data/, 静态资源)
 *   3) query string 不含 ?desktop=1
 *
 * 桌面访问保持原样. 用户主动加 ?desktop=1 可强制桌面版.
 * PagesFunction 类型由 CF Pages Functions 自动注入, 不需 import.
 */

export const onRequest: PagesFunction = async (context) => {
  const { request, next } = context;
  const url = new URL(request.url);

  // 1) 已经在 mobile 路径下: 不动
  if (url.pathname === "/m" || url.pathname.startsWith("/m/")) {
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
  return Response.redirect(target, 302);
};