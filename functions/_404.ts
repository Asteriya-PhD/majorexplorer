/**
 * functions/_404.ts — Cloudflare Pages 404 handler.
 *
 * Runs when no static asset, API route, or page matched. Returns proper
 * HTTP 404 status with a styled 404 page (not 200 + index.html, which
 * would pollute Google index with duplicate content).
 *
 * Design mirrors /public/index.html (theme-color #B8323A, fonts/system stack,
 * 56-560px responsive container, editorial vibe).
 */

export const onRequest: PagesFunction = async (context) => {
  const { request } = context;
  const url = new URL(request.url);
  const ua = (request.headers.get("user-agent") || "").toLowerCase();
  const isMobile = /iphone|ipad|ipod|android|webos|blackberry|windows phone|opera mini|mobile|tablet|kindle|silk|playbook|bb10|bb11/i.test(ua);
  // Mobile 404 → fall through to /m/ subdir. The 404 handler runs AFTER middleware
  // for static-asset misses, so on mobile the middleware already 302'd us to /m/<path>,
  // and if that 404s we render this page with mobile-prefixed links.
  const prefix = isMobile ? "/m" : "";
  const home = prefix + "/";
  const majors = prefix + "/majors.html";
  const search = prefix + "/search.html";
  const wishlist = prefix + "/wishlist.html";

  // Escape user-supplied path before inlining into HTML
  const safePath = url.pathname
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#B8323A">
<meta name="robots" content="noindex, nofollow">
<title>404 · 页面不存在 · Major Explorer</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 16%22><text y=%2214%22 font-size=%2214%22>📘</text></svg>">
<link rel="stylesheet" href="/css/shared.css">
<style>
  body {
    margin: 0; padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    background:
      radial-gradient(ellipse 80% 60% at 50% 0%, rgba(184,50,58,0.06) 0%, transparent 70%),
      linear-gradient(180deg, #FAFAF7 0%, #F5F2EA 100%);
    color: #14110D;
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    padding: 24px;
  }
  .container {
    max-width: 560px; width: 100%;
    padding: 40px 24px; text-align: center;
  }
  h1 {
    font-size: clamp(4rem, 14vw, 7rem);
    font-weight: 800; color: #B8323A;
    letter-spacing: -0.04em; line-height: 1;
    margin: 0 0 16px;
    font-feature-settings: "tnum";
  }
  h2 {
    font-size: 1.5rem; font-weight: 700;
    margin: 0 0 16px; color: #14110D;
  }
  p {
    color: #6B6157; line-height: 1.7;
    margin: 0 0 16px; font-size: 1rem;
  }
  .path {
    display: inline-block; padding: 6px 14px;
    background: rgba(184,50,58,0.08);
    border: 1px solid rgba(184,50,58,0.18);
    border-radius: 6px;
    font-family: ui-monospace, 'SF Mono', Menlo, monospace;
    font-size: 0.875rem; color: #B8323A;
    margin: 8px 0 28px;
    word-break: break-all; max-width: 100%;
  }
  .links {
    display: flex; gap: 12px;
    justify-content: center; flex-wrap: wrap;
    margin: 8px 0 24px;
  }
  a {
    display: inline-block; padding: 12px 20px; border-radius: 8px;
    text-decoration: none; font-size: 0.9375rem; font-weight: 500;
    transition: transform 150ms, background 150ms, color 150ms;
    line-height: 1.2;
  }
  a:hover { transform: translateY(-1px); }
  .primary { background: #B8323A; color: #FAFAF7; }
  .primary:hover { background: #962830; }
  .secondary {
    border: 1.5px solid #B8323A; color: #B8323A;
    background: transparent;
  }
  .secondary:hover { background: #B8323A; color: #FAFAF7; }
  .hint {
    margin-top: 32px; padding-top: 24px;
    border-top: 1px solid #E8E2D5;
    font-size: 0.8125rem; color: #8B7355;
    line-height: 1.6;
  }
  .disciplines {
    display: flex; gap: 6px;
    justify-content: center; flex-wrap: wrap;
    margin-top: 12px;
  }
  .disciplines a {
    padding: 4px 10px; font-size: 0.75rem;
    border-radius: 4px;
    border: 1px solid #E8E2D5;
    color: #6B6157;
  }
  .disciplines a:hover {
    border-color: #B8323A; color: #B8323A;
    background: rgba(184,50,58,0.04);
  }
  @media (max-width: 600px) {
    .container { padding: 24px 16px; }
    .links { flex-direction: column; }
    a { width: 100%; box-sizing: border-box; }
  }
</style>
</head>
<body>
  <div class="container">
    <h1>404</h1>
    <h2>页面不存在</h2>
    <p>你访问的页面已下架、被合并、或者地址输错了。</p>
    <div class="path">${safePath}</div>
    <div class="links">
      <a class="primary" href="${home}">回到首页</a>
      <a class="secondary" href="${majors}">📚 浏览 13 学科门类</a>
      <a class="secondary" href="${search}">🔍 搜索专业</a>
      <a class="secondary" href="${wishlist}">⭐ 我的心愿单</a>
    </div>
    <p class="hint">
      不知道想查什么? 直接搜个关键词试试 —「编程」「医生」「金融」「设计」「老师」
    </p>
    <div class="disciplines">
      <a href="${majors}#01">01 哲学</a>
      <a href="${majors}#02">02 经济学</a>
      <a href="${majors}#03">03 法学</a>
      <a href="${majors}#04">04 教育学</a>
      <a href="${majors}#05">05 文学</a>
      <a href="${majors}#06">06 历史学</a>
      <a href="${majors}#07">07 理学</a>
      <a href="${majors}#08">08 工学</a>
      <a href="${majors}#09">09 农学</a>
      <a href="${majors}#10">10 医学</a>
      <a href="${majors}#12">12 管理学</a>
      <a href="${majors}#13">13 艺术学</a>
    </div>
  </div>
</body>
</html>`;

  return new Response(html, {
    status: 404,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "X-Robots-Tag": "noindex, nofollow",
      "Cache-Control": "public, max-age=300",
    },
  });
};
