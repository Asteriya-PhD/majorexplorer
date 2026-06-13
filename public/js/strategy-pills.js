/**
 * strategy-pills.js — 主页 ⭐ 国家战略产业 chip 渲染
 *
 * 数据源: /data/strategy_industries.json
 * 注入点: #strategy-host (public/index.html)
 *
 * 行为: 点击 chip → /strategy.html#<产业名> 锚点跳转(展开产业详情)
 */
(function () {
  "use strict";

  const host = document.getElementById("strategy-host");
  if (!host) return;

  fetch("/data/strategy_industries.json", { cache: "no-cache" })
    .then((r) => (r.ok ? r.json() : null))
    .then((data) => {
      if (!data || !data.industries) return;
      const industries = data.industries;

      host.innerHTML = Object.entries(industries)
        .map(
          ([name, info]) => `
        <a href="/strategy.html#${encodeURIComponent(name)}" class="strategy-pill">
          <span class="strategy-pill-icon">${info.icon || "⭐"}</span>
          <span class="strategy-pill-name">${name}</span>
          <span class="strategy-pill-tier">${info.tier || ""}</span>
        </a>`
        )
        .join("");

      // 处理 hash 跳转(从其他页面带 #集成电路 跳过来时,自动滚动)
      const hash = decodeURIComponent(window.location.hash.slice(1));
      if (hash && industries[hash]) {
        // 略过,主页没有锚点目标
      }
    })
    .catch((e) => {
      console.warn("[strategy-pills] fetch failed:", e);
    });
})();
