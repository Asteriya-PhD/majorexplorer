/**
 * discipline-pills.js — 主页 📚 学科门类 chip 渲染
 *
 * 数据源: /data/discipline_hierarchy.json
 * 注入点: #discipline-host (public/index.html)
 *
 * 行为: 点击 chip → /?discipline={code}#majors 跳回主页 + 预选门类过滤
 *       (聚合页 majors.html 留待后续 session)
 */
(function () {
  "use strict";

  const host = document.getElementById("discipline-host");
  if (!host) return;

  fetch("/data/discipline_hierarchy.json", { cache: "no-cache" })
    .then((r) => (r.ok ? r.json() : null))
    .then((data) => {
      if (!data || !data.门类) return;
      const disciplines = data.门类;

      // 按编码排序(01, 02, 03 ... 14),11 缺位自动跳过
      const codes = Object.keys(disciplines).sort();

      host.innerHTML = codes
        .map((code) => {
          const d = disciplines[code];
          const subCount = Object.keys(d.sub_classes || {}).length;
          const majorCount = Object.values(d.sub_classes || {}).reduce(
            (sum, sc) => sum + (sc.majors ? sc.majors.length : 0),
            0
          );
          return `
        <a href="/?discipline=${code}#majors" class="discipline-pill" data-discipline="${code}">
          <span class="discipline-pill-icon">${d.icon || "📚"}</span>
          <span class="discipline-pill-name">${d.name}</span>
          <span class="discipline-pill-count">${subCount} 类 · ${majorCount} 专业</span>
        </a>`;
        })
        .join("");

      // 处理 hash 跳转: ?discipline=08 自动滚到精品区
      const url = new URL(window.location.href);
      const preSelect = url.searchParams.get("discipline");
      if (preSelect && disciplines[preSelect]) {
        // 高亮选中的 chip
        const target = host.querySelector(`[data-discipline="${preSelect}"]`);
        if (target) {
          target.style.borderColor = "#2A6F4F";
          target.style.boxShadow = "0 2px 8px rgba(42,111,79,0.25)";
          target.style.fontWeight = "600";
        }
        // 滚动到精品区
        const majorsSection = document.getElementById("majors");
        if (majorsSection) {
          setTimeout(() => majorsSection.scrollIntoView({ behavior: "smooth" }), 200);
        }
        console.log(`[discipline-pills] 预选门类 ${preSelect} (${disciplines[preSelect].name})`);
      }
    })
    .catch((e) => {
      console.warn("[discipline-pills] fetch failed:", e);
    });
})();