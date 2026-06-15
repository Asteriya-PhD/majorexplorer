/* recs.js — 9 档志愿推荐 · 复用 PC Recommender 算法
 *
 * 数据流:
 *   - DataLoader.loadAll(): 加载 5 个数据文件 (light 295KB + heavy 3.4MB)
 *   - Recommender.recommend(user, data, opts): 跑 PC 完整算法,返回 {冲,稳,保} 三档
 *   - 用户输入: score (#score), xuanke (#pick-chips.on), mode (seg[data-pref=weight])
 *   - interests: 从 WishlistStore 读 (用户收藏的专业), score = rating
 *   - cities: 空 (mobile UI 无具体城市)
 *
 * 输出: 9 sub_tier (强冲/中冲/微冲 + 强稳/中稳/弱稳 + 强保/中保/兜底) × 1 校/档
 *       每校显示 top_major[0] 作为代表专业 + 校名 + 城市 + score
 */
(async () => {
  // 选科 chip / 偏好星 / 偏好 seg 交互 (复用 mobile 自己的 UI 控件)
  document.querySelectorAll("#pick-chips .chip").forEach(c => {
    c.addEventListener("click", () => c.classList.toggle("on"));
  });
  const pt = document.getElementById("pref-toggle");
  if (pt) pt.addEventListener("click", () => document.getElementById("pref-panel").classList.toggle("open"));
  document.querySelectorAll(".pref-stars").forEach(g => {
    g.querySelectorAll(".pref-star").forEach(s => {
      s.addEventListener("click", () => {
        g.querySelectorAll(".pref-star").forEach(x => x.classList.remove("on"));
        s.classList.add("on");
      });
    });
  });
  document.querySelectorAll(".seg").forEach(g => {
    g.querySelectorAll("button").forEach(b => {
      b.addEventListener("click", () => {
        g.querySelectorAll("button").forEach(x => x.classList.remove("on"));
        b.classList.add("on");
      });
    });
  });

  await M.init();
  if (window.WishlistStore && WishlistStore.migrate) WishlistStore.migrate();

  // 分数 → 位次 估算 (沿用 mobile 简化表, 仅做实时展示; 真排位走 PC Recommender)
  const scoreInput = document.getElementById("score");
  const rankOut = document.getElementById("rank-out");
  const table = {
    700: 80, 680: 320, 660: 900, 640: 2200, 620: 4500,
    600: 8500, 580: 14500, 560: 23000, 540: 34000, 520: 48000,
    500: 65000, 480: 84000, 460: 105000, 440: 130000, 420: 160000,
  };
  function scoreToRank(s) {
    if (!s) return "—";
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
    rankOut.textContent = scoreToRank(+scoreInput.value || 580);
  }

  // ─── 9 档 UI 颜色 (跟 PC 端 sub_tier 同款色) ───
  const tierColors = {
    "强冲": "#B8323A", "中冲": "#C44E55", "微冲": "#D1757B",
    "强稳": "#B5934A", "中稳": "#C7A766", "弱稳": "#D6BE85",
    "强保": "#5C7C4A", "中保": "#7B9669", "兜底": "#9AB089",
  };
  function tierColor(name) { return tierColors[name] || "#B8323A"; }

  // ─── 用户输入收集 ───
  function collectUser() {
    const score = +scoreInput.value || 0;
    if (!score) return null;
    const xuanke = Array.from(document.querySelectorAll("#pick-chips .chip.on"))
      .map(b => b.dataset.pick).filter(Boolean);
    const segBtn = document.querySelector('.seg[data-pref="weight"] button.on');
    const modeMap = { school: "院校优先", balanced: "均衡", major: "专业优先" };
    const mode = modeMap[segBtn && segBtn.dataset.v] || "均衡";
    // interests: 从 WishlistStore 取 (用户收藏), 评分 = rating (1-5)
    const wishes = (window.WishlistStore ? WishlistStore.all() : []);
    const interests = wishes
      .filter(w => w.rating || w.score)
      .map(w => ({
        major: w.title || (M.manifestBySlug[w.slug] && M.manifestBySlug[w.slug].title) || w.slug,
        score: w.rating || w.score,
        style: w.style,
      }));
    return { score, type: "物理类", xuanke, interests, cities: [], mode };
  }

  // ─── PC Recommender 调用 + 渲染 ───
  const SUB_TIERS = ["强冲", "中冲", "微冲", "强稳", "中稳", "弱稳", "强保", "中保", "兜底"];

  function groupBySubTier(result) {
    // 把 {冲:[...], 稳:[...], 保:[...]} 摊平, 按 sub_tier 分组成 9 桶
    const buckets = {};
    for (const t of SUB_TIERS) buckets[t] = null;
    for (const cat of ["冲", "稳", "保"]) {
      for (const school of (result[cat] || [])) {
        const tier = school.sub_tier;
        if (!tier || !buckets.hasOwnProperty(tier)) continue;
        // 桶里只放分数最高的 1 个
        if (!buckets[tier] || school.score > buckets[tier].score) buckets[tier] = school;
      }
    }
    return buckets;
  }

  function esc(s) { return String(s == null ? "" : s).replace(/[<>&"]/g, c => ({"<":"&lt;",">":"&gt;","&":"&amp;",'"':"&quot;"})[c]); }

  function render(school, tier) {
    if (!school) {
      return `
        <div class="tier-group">
          <div class="tier-head">
            <span class="tier-tag" style="--tier-color: ${tierColor(tier)}; background: ${tierColor(tier)};">${tier}</span>
            <span class="tier-name" style="color: var(--muted);">暂无匹配</span>
          </div>
          <div class="rec" style="--theme: var(--muted-2); opacity: 0.5;">
            <div class="rec-body">
              <div class="rec-cat">该档位当前分数段无合适院校</div>
            </div>
          </div>
        </div>
      `;
    }
    const topMajor = (school.top_majors && school.top_majors[0] && school.top_majors[0].name) || "—";
    return `
      <div class="tier-group">
        <div class="tier-head">
          <span class="tier-tag" style="--tier-color: ${tierColor(tier)}; background: ${tierColor(tier)};">${tier}</span>
          <span class="tier-name">${esc(school.school_name)}</span>
          <span class="tier-meta">${esc(school.city || "")} · ${esc(topMajor)}</span>
        </div>
        <div class="rec" style="--theme: var(--accent);">
          <div class="rec-body">
            <div class="rec-cat">${esc(school.tier || "")}${school.prob ? ` · 录取概率 ${Math.round(school.prob * 100)}%` : ""}</div>
            <h3 class="rec-title">${esc(topMajor)}</h3>
            <div class="rec-meta">位次 ${(school.median_rank_3y || 0).toLocaleString()} · 综合分 ${school.score || "—"}</div>
          </div>
          <div class="rec-arrow">→</div>
        </div>
      </div>
    `;
  }

  document.getElementById("run").addEventListener("click", async () => {
    const user = collectUser();
    if (!user) { alert("先填分数"); return; }
    const out = document.getElementById("results");
    out.innerHTML = `<div class="loading">加载数据 + 跑算法… (3-5 秒)</div>`;
    try {
      // 加载 PC 全部数据 (light 295KB + heavy 3.4MB, IDB 缓存后 <200ms)
      const data = await window.DataLoader.loadAll();
      const result = window.Recommender.recommend(user, data, {
        topChong: 6, topWen: 8, topBao: 4,
      });
      const buckets = groupBySubTier(result);
      out.innerHTML = SUB_TIERS.map(t => render(buckets[t], t)).join("");
    } catch (e) {
      console.error("[recs.js] 推荐失败", e);
      out.innerHTML = `<div class="empty">
        <h3>推荐失败</h3>
        <div>${esc(e.message || String(e))}<br>请刷新重试, 或检查网络.</div>
      </div>`;
    }
  });
})();
