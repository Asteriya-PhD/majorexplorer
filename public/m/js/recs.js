/* recs.js — 分数 + 选科 + 偏好 → 9 档推荐 (mock 简化版, 接 recommender 后续) */
(async () => {
  await M.init();
  const $ = sel => document.querySelector(sel);

  // 选科 chip
  document.querySelectorAll("#pick-chips .chip").forEach(c => {
    c.addEventListener("click", () => c.classList.toggle("on"));
  });
  // 偏好折叠
  const pt = $("#pref-toggle");
  if (pt) pt.addEventListener("click", () => $("#pref-panel").classList.toggle("open"));
  // 偏好星
  document.querySelectorAll(".pref-stars").forEach(g => {
    g.querySelectorAll(".pref-star").forEach(s => {
      s.addEventListener("click", () => {
        g.querySelectorAll(".pref-star").forEach(x => x.classList.remove("on"));
        s.classList.add("on");
      });
    });
  });
  // 偏好 seg
  document.querySelectorAll(".seg").forEach(g => {
    g.querySelectorAll("button").forEach(b => {
      b.addEventListener("click", () => {
        g.querySelectorAll("button").forEach(x => x.classList.remove("on"));
        b.classList.add("on");
      });
    });
  });

  // 分数 → 位次 (简化: 线性近似湖北 2025 一分一段)
  const scoreInput = $("#score");
  const rankOut = $("#rank-out");
  function scoreToRank(s) {
    if (!s) return "—";
    // 简化估算 (基于 2025 yfyd 实际表太复杂, 走近似)
    const table = {
      700: 80, 680: 320, 660: 900, 640: 2200, 620: 4500,
      600: 8500, 580: 14500, 560: 23000, 540: 34000, 520: 48000,
      500: 65000, 480: 84000, 460: 105000, 440: 130000, 420: 160000,
    };
    const keys = Object.keys(table).map(Number).sort((a, b) => a - b);
    if (s >= 700) return "80+";
    if (s <= 420) return "16w+";
    for (let i = 0; i < keys.length - 1; i++) {
      if (s >= keys[i] && s < keys[i + 1]) {
        const a = table[keys[i]], b = table[keys[i + 1]];
        const t = (s - keys[i]) / (keys[i + 1] - keys[i]);
        return Math.round(a + (b - a) * t).toLocaleString();
      }
    }
    return "—";
  }
  if (scoreInput) {
    scoreInput.addEventListener("input", () => {
      rankOut.textContent = scoreToRank(+scoreInput.value);
    });
    rankOut.textContent = scoreToRank(+scoreInput.value);
  }

  // 9 档推荐生成 (mock 版 — 真版接 recommender.js)
  const tierColors = {
    "强冲": "#B8323A", "中冲": "#C44E55", "微冲": "#D1757B",
    "强稳": "#B5934A", "中稳": "#C7A766", "弱稳": "#D6BE85",
    "强保": "#5C7C4A", "中保": "#7B9669", "兜底": "#9AB089",
  };
  function tierColor(name) { return tierColors[name] || "#B8323A"; }

  $("#run").addEventListener("click", () => {
    const score = +scoreInput.value || 0;
    if (!score) { alert("先填分数"); return; }
    // 简化: 拿所有精品, 按 score 排序分段
    const all = M.manifest.majors.slice();
    // 简化为 9 个固定档位, 每个抽 1-2 个
    const tiers = ["强冲", "中冲", "微冲", "强稳", "中稳", "弱稳", "强保", "中保", "兜底"];
    const picks = tiers.map((t, i) => {
      const idx = (i * 14 + (score % 13)) % all.length;
      return { tier: t, m: all[idx] };
    });
    const out = $("#results");
    out.innerHTML = tiers.map(t => {
      const p = picks.find(x => x.tier === t);
      return `
        <div class="tier-group">
          <div class="tier-head">
            <span class="tier-tag" style="--tier-color: ${tierColor(t)}; background: ${tierColor(t)};">${t}</span>
            <span class="tier-name">${p.m.title}</span>
            <span class="tier-meta">${p.m.category}</span>
          </div>
          <a class="rec" href="majors/${p.m.slug}.html" style="--theme: ${M.styleColor(p.m.style)};">
            <div class="rec-body">
              <div class="rec-cat">${p.m.category}<span style="color:var(--accent); margin-left:4px;">★</span></div>
              <h3 class="rec-title">${p.m.title}</h3>
              <div class="rec-meta">${(p.m.tags || []).slice(0, 3).join(" · ") || p.m.degree}</div>
            </div>
            <div class="rec-arrow">→</div>
          </a>
        </div>
      `;
    }).join("");
  });
})();
