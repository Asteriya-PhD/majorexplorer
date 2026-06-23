/* recs.js — 3 档志愿推荐 · 复用 PC Recommender 算法
 *
 * 数据流:
 *   - DataLoader.loadAll(): 加载 5 个数据文件 (light 295KB + heavy 3.4MB)
 *   - Recommender.recommend(user, data, opts): 跑 PC 完整算法,返回 {冲,稳,保} 三档
 *   - 用户输入: score (#score), xuanke (#pick-chips.on), mode (seg[data-pref=weight])
 *   - interests: 从 WishlistStore 读 (用户收藏的专业), score = rating
 *   - cities: 空 (mobile UI 无具体城市)
 *
 * 输出: 3 档 (冲 + 稳 + 保) × 共 20 张卡 (6+8+6)
 *       每张卡: 校名 + 城市 + top_major + 录取概率 + 推荐理由
 */
(async () => {
  // 选科 chip — 3+1+2 严格约束 (湖北新高考)
  //   物理 OR 历史 二选一 (互斥)
  //   化学/生物/地理/政治 4 选 ≤2
  //   总数 ≤3; 选满后第 4 门 auto-off 最早选的 (按 DOM 顺序)
  const FIRST_CHOICE = ["物理", "历史"];
  const MAX_PICKS = 3;
  function refreshPickDisabled() {
    const onChips = Array.from(document.querySelectorAll("#pick-chips .chip.on"));
    const onFirst = onChips.find(c => FIRST_CHOICE.includes(c.dataset.pick));
    document.querySelectorAll("#pick-chips .chip").forEach(c => {
      const p = c.dataset.pick;
      const isOn = c.classList.contains("on");
      // 互斥: 物理/历史 已选 1 个,另 1 个 disabled
      const isFirstOther = FIRST_CHOICE.includes(p) && onFirst && onFirst !== c;
      // 满 3 门: 未选的 disabled
      const isFull = onChips.length >= MAX_PICKS && !isOn;
      c.classList.toggle("disabled", isFirstOther || isFull);
    });
  }
  document.querySelectorAll("#pick-chips .chip").forEach(c => {
    c.addEventListener("click", () => {
      const pick = c.dataset.pick;
      const wasOn = c.classList.contains("on");
      if (wasOn) {
        c.classList.remove("on");
        refreshPickDisabled();
        return;
      }
      // 物理/历史 互斥
      if (FIRST_CHOICE.includes(pick)) {
        FIRST_CHOICE.forEach(p => {
          if (p !== pick) {
            const other = document.querySelector(`#pick-chips .chip[data-pick="${p}"]`);
            if (other) other.classList.remove("on");
          }
        });
      }
      // 总数 ≤ 3 — 满了就 auto-off 最早选的
      const currentOn = Array.from(document.querySelectorAll("#pick-chips .chip.on"));
      if (currentOn.length >= MAX_PICKS) {
        currentOn[0].classList.remove("on");
      }
      c.classList.add("on");
      refreshPickDisabled();
    });
  });
  refreshPickDisabled();
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

  // ─── 3 档颜色 (冲红/稳蓝/保绿, 单色覆盖全档) ───
  const tierColors = {
    "冲": "#B8323A",
    "稳": "#3182CE",
    "保": "#38A169",
  };
  function tierColor(name) { return tierColors[name] || "#B8323A"; }

  // ─── 城市/收藏 UI (与 PC preferences.html 同步: list + 每项 1-5★ + ✕) ───
  // 城市 state: 内存数组 [{city, score}], 默认 [{武汉, 5}], 同步到 localStorage
  const CITY_KEY = "recs.cities.v1";
  let cities = [];
  try {
    const saved = JSON.parse(localStorage.getItem(CITY_KEY) || "null");
    cities = Array.isArray(saved) && saved.length ? saved : [{ city: "武汉", score: 5 }];
  } catch (e) {
    cities = [{ city: "武汉", score: 5 }];
  }
  const cityList = document.getElementById("city-list");
  const cityInput = document.getElementById("city-input");
  const cityAddBtn = document.getElementById("add-city");

  function renderCities() {
    if (!cityList) return;
    cityList.innerHTML = cities.map((c, idx) => {
      const stars = [1, 2, 3, 4, 5].map(v => `<button data-v="${v}" class="${v <= c.score ? "on" : ""}">★</button>`).join("");
      return `<div class="city-item" data-idx="${idx}">
        <span class="city-name">${esc(c.city)}</span>
        <span class="city-stars">${stars}</span>
        <button class="del-city" type="button" aria-label="删除 ${esc(c.city)}">✕</button>
      </div>`;
    }).join("");
    localStorage.setItem(CITY_KEY, JSON.stringify(cities));
  }
  function addCity(name) {
    name = (name || "").trim();
    if (!name) return;
    if (cities.length >= 3) { alert("最多 3 个城市"); return; }
    if (cities.some(c => c.city === name)) { alert("已添加过 " + name); return; }
    cities.push({ city: name, score: 4 });
    renderCities();
  }
  if (cityAddBtn) {
    cityAddBtn.addEventListener("click", () => {
      addCity(cityInput && cityInput.value);
      if (cityInput) { cityInput.value = ""; cityInput.focus(); }
    });
  }
  if (cityInput) {
    cityInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); cityAddBtn && cityAddBtn.click(); }
    });
  }
  if (cityList) {
    cityList.addEventListener("click", (e) => {
      const item = e.target.closest(".city-item");
      if (!item) return;
      const idx = parseInt(item.dataset.idx, 10);
      if (e.target.classList.contains("del-city")) {
        cities.splice(idx, 1);
        if (cities.length === 0) cities = [{ city: "武汉", score: 5 }]; // 兜底
        renderCities();
      } else if (e.target.tagName === "BUTTON" && e.target.dataset.v) {
        cities[idx].score = parseInt(e.target.dataset.v, 10);
        renderCities();
      }
    });
  }
  renderCities();

  // 收藏 summary (实时显示)
  const wsSummary = document.getElementById("wishlist-summary");
  function renderWishlistSummary() {
    if (!wsSummary) return;
    const items = (window.WishlistStore ? WishlistStore.all() : []);
    if (items.length === 0) {
      wsSummary.innerHTML = `<div class="ws-empty">还没有收藏 — <a href="wishlist.html">先去收藏 4 个专业 →</a></div>`;
      return;
    }
    wsSummary.innerHTML = items.map(w => {
      const title = w.title || (M.manifestBySlug[w.slug] && M.manifestBySlug[w.slug].title) || w.slug;
      const score = w.rating || w.score || 0;
      return `<span class="ws-item"><span class="ws-name">${esc(title)}</span><span class="ws-rating">${"★".repeat(score)}</span></span>`;
    }).join("");
  }
  if (window.WishlistStore) WishlistStore.subscribe(renderWishlistSummary);
  renderWishlistSummary();

  // ─── 用户输入收集 ───
  // PC preferences 同款: cities 是 [{city, score}], interests 是 wishlist rating 1-5
  function collectUser() {
    const score = +scoreInput.value || 0;
    if (!score) return null;
    const xuanke = Array.from(document.querySelectorAll("#pick-chips .chip.on"))
      .map(b => b.dataset.pick).filter(Boolean);
    const segBtn = document.querySelector('.seg[data-pref="weight"] button.on');
    const modeMap = { school: "院校优先", balanced: "均衡", major: "专业优先" };
    const mode = modeMap[segBtn && segBtn.dataset.v] || "均衡";
    // interests: wishlist rating 直接作 score (1-5)
    const wishes = (window.WishlistStore ? WishlistStore.all() : []);
    const interests = wishes
      .filter(w => w.rating || w.score)
      .map(w => ({
        major: w.title || (M.manifestBySlug[w.slug] && M.manifestBySlug[w.slug].title) || w.slug,
        score: w.rating || w.score,
        style: w.style,
      }));
    // cities: 内存数组 [{city, score}], 没添加就用空 (PC 默认 [{武汉, 5}], mobile 兜底)
    return { score, type: "物理类", xuanke, interests, cities: cities.length ? cities : [{ city: "武汉", score: 3 }], mode };
  }

  // ─── PC Recommender 调用 + 渲染 ───
  const CATS = [
    { key: "冲", name: "冲", desc: "P 25–50% · 拼一拼", minP: 0.20, maxP: 0.60 },
    { key: "稳", name: "稳", desc: "P 60–88% · 重点关注", minP: 0.60, maxP: 0.90 },
    { key: "保", name: "保", desc: "P 90–99% · 稳妥兜底", minP: 0.90, maxP: 1.01 },
  ];

  function esc(s) { return String(s == null ? "" : s).replace(/[<>&"]/g, c => ({"<":"&lt;",">":"&gt;","&":"&amp;",'"':"&quot;"})[c]); }

  // 推荐理由生成: 根据 score_breakdown 各维度, 突出最强匹配
  function buildReason(school) {
    if (!school) return "—";
    const bk = school.score_breakdown || {};
    const m = bk.major || 0, c = bk.city || 0, t = bk.tier || 0, chsi = bk.chsi || 0;
    const topMajor = (school.top_majors && school.top_majors[0] && school.top_majors[0].name) || "";
    const topRk = (school.top_majors && school.top_majors[0] && (school.top_majors[0].xueke || school.top_majors[0].ruanke)) || "";
    const med = school.median_rank_3y ? `3 年中位位次 ${Math.round(school.median_rank_3y).toLocaleString()}` : "";
    const parts = [];
    if (m >= 4 && topMajor) parts.push(`✦ 专业匹配 ${m.toFixed(1)} · ${topMajor}${topRk ? ` (${topRk})` : ""}`);
    if (c >= 4 && school.city) parts.push(`✦ 城市匹配 · ${school.city}`);
    if (t >= 4) parts.push(`✦ ${school.tier || "强校"}`);
    if (chsi >= 4) parts.push(`✦ 阳光高考满意度 ${chsi}/5`);
    if (parts.length === 0) {
      if (med) parts.push(`综合分 ${(school.score || 0).toFixed(1)} · ${med}`);
      else parts.push(`综合分 ${(school.score || 0).toFixed(1)}`);
    }
    return parts.slice(0, 2).join(" · ");  // 最多 2 条, 不超长
  }

  function renderSchool(school, catKey) {
    if (!school) return "";
    const topMajor = (school.top_majors && school.top_majors[0] && school.top_majors[0].name) || "—";
    const reason = buildReason(school);
    return `
      <div class="rec" style="--theme: ${tierColor(catKey)};">
        <div class="rec-body">
          <div class="rec-cat">${esc(school.tier || "")} · 录取概率 <strong style="color:${tierColor(catKey)};">${Math.round(school.prob * 100)}%</strong></div>
          <h3 class="rec-title">${esc(school.school_name)} · ${esc(topMajor)}</h3>
          <div class="rec-meta">📍 ${esc(school.city || "")} · 位次 ${(school.median_rank_3y || 0).toLocaleString()} · 综合分 ${(school.score || 0).toFixed(1)}</div>
          <div class="rec-reason" style="font-size:0.75rem;color:var(--fg-soft);margin-top:6px;line-height:1.5;border-top:1px dashed var(--line);padding-top:6px;">${esc(reason)}</div>
        </div>
      </div>
    `;
  }

  function renderBucket(cat, schools) {
    if (!schools || schools.length === 0) {
      return `
        <div class="tier-group">
          <div class="tier-head">
            <span class="tier-tag" style="--tier-color: ${tierColor(cat.key)}; background: ${tierColor(cat.key)};">${cat.name}</span>
            <span class="tier-name" style="color: var(--muted);">暂无匹配</span>
            <span class="tier-meta">${cat.desc}</span>
          </div>
          <div class="rec" style="--theme: var(--muted-2); opacity: 0.5;">
            <div class="rec-body">
              <div class="rec-cat">该档位当前分数段无合适院校</div>
            </div>
          </div>
        </div>
      `;
    }
    return `
      <div class="tier-group">
        <div class="tier-head">
          <span class="tier-tag" style="--tier-color: ${tierColor(cat.key)}; background: ${tierColor(cat.key)};">${cat.name}</span>
          <span class="tier-name">${cat.desc}</span>
          <span class="tier-meta">${schools.length} 所</span>
        </div>
        ${schools.map(s => renderSchool(s, cat.key)).join("")}
      </div>
    `;
  }

  document.getElementById("run").addEventListener("click", async () => {
    const user = collectUser();
    if (!user) { alert("先填分数"); return; }
    // 4 wishlist min check (D8: 改在 click 时校验, UI 主动引导)
    if (window.WishlistStore && !WishlistStore.isReady()) {
      const n = WishlistStore.count();
      const out = document.getElementById("results");
      out.innerHTML = `<div class="empty">
        <h3>还差 ${4 - n} 个收藏</h3>
        <div>推荐至少需要 4 个已收藏专业, 当前 ${n} 个。<br>
        <a href="wishlist.html" style="color:var(--accent);">先去收藏几个 →</a></div>
      </div>`;
      return;
    }
    const out = document.getElementById("results");
    out.innerHTML = `<div class="loading">加载数据 + 跑算法… (3-5 秒)</div>`;
    try {
      // 加载 PC 全部数据 (light 295KB + heavy 3.4MB, IDB 缓存后 <200ms)
      const data = await window.DataLoader.loadAll();
      // 3 档共 36 张: 冲 12 + 稳 16 + 保 8
      const result = window.Recommender.recommend(user, data, {
        topChong: 12, topWen: 16, topBao: 8,
      });
      out.innerHTML = CATS.map(c => renderBucket(c, result[c.key])).join("");
    } catch (e) {
      console.error("[recs.js] 推荐失败", e);
      out.innerHTML = `<div class="empty">
        <h3>推荐失败</h3>
        <div>${esc(e.message || String(e))}<br>请刷新重试, 或检查网络.</div>
      </div>`;
    }
  });
})();
