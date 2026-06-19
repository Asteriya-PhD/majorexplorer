/* home.js — 主页: 本日精读 + 国家战略 + 13 门类 */
(async () => {
  await M.init();

  // ───── 动态注入精品专业数 (替换静态 126) ─────
  const total = M.manifest.majors.length;
  document.querySelectorAll(".js-mcount").forEach(el => el.textContent = total);

  // ───── 本日精读 (4 篇随机) ─────
  const featList = document.getElementById("feat-list");
  if (featList) {
    const all = M.manifest.majors;
    // 简单的日期种子 + 哈希, 让 4 篇每天固定
    const today = new Date();
    const seed = today.getFullYear() * 10000 + (today.getMonth() + 1) * 100 + today.getDate();
    function pick(arr, n) {
      const out = [];
      let pool = arr.slice();
      let s = seed;
      for (let i = 0; i < n && pool.length; i++) {
        s = (s * 9301 + 49297) % 233280;
        const idx = Math.floor((s / 233280) * pool.length);
        out.push(pool.splice(idx, 1)[0]);
      }
      return out;
    }
    const feats = pick(all, 4);
    featList.innerHTML = feats.map(m => {
      const tags = (m.tags || []).slice(0, 3);
      const discNum = m.discipline ? `No. ${m.discipline}` : "";
      return `
      <a class="feat" href="majors/${m.slug}.html" style="--theme: ${M.styleColor(m.style)};">
        <div class="feat-body">
          <div class="feat-meta">
            <span class="feat-cat">${m.category || "—"}<span class="star">★</span></span>
            <span class="feat-disc">${discNum}</span>
          </div>
          <h3 class="feat-title">${m.title}</h3>
          <div class="feat-tags">
            ${tags.map(t => `<span class="feat-tag">${t}</span>`).join("")}
          </div>
        </div>
        <div class="feat-arrow">→</div>
      </a>
    `;
    }).join("");
  }

  // ───── 国家战略 chip ─────
  const chips = document.getElementById("strat-chips");
  if (chips) {
    // 找含"国家战略"tag 的专业, 聚合
    const strat = M.manifest.majors.filter(m => (m.tags || []).some(t => /国家战略|战略|集成电路|人工智能|新能源|储能|网络空间|生物医药|新材料|航空航天|量子/.test(t)));
    // 按 style 聚合 5-7 个 chip
    const groups = {};
    strat.forEach(m => {
      const tag = (m.tags || []).find(t => /集成电路|人工智能|网络空间|生物医药|储能|新材料|新能源|航空航天|量子|信息安全|密码|大数据/.test(t)) || m.style;
      groups[tag] = (groups[tag] || 0) + 1;
    });
    const top = Object.entries(groups).sort((a, b) => b[1] - a[1]).slice(0, 8);
    chips.innerHTML = top.map(([name, n]) => `
      <a class="strat-chip" href="catalog.html#q=${encodeURIComponent(name)}"><span class="star">★</span>${name}<span class="n">${n}</span></a>
    `).join("");
  }

  // ───── 13 门类 ─────
  const chapters = document.getElementById("chapters");
  if (chapters) {
    // 从 hierarchy 拿门类信息
    const list = M.hierarchy?.disciplines || M.hierarchy?.menjia || [];
    const colorKey = {
      "01":"--c-01","02":"--c-02","03":"--c-03","04":"--c-04","05":"--c-05",
      "06":"--c-06","07":"--c-07","08":"--c-08","09":"--c-09","10":"--c-10",
      "12":"--c-12","13":"--c-13",
    };
    const fallback = [
      {code:"01",name:"哲学",sub:"哲学类",ghost:"哲"},
      {code:"02",name:"经济学",sub:"经济学 · 财政学 · 金融 · 经贸",ghost:"经"},
      {code:"03",name:"法学",sub:"法学 · 政治学 · 社会学 · 公安学",ghost:"法"},
      {code:"04",name:"教育学",sub:"教育学 · 体育学",ghost:"教"},
      {code:"05",name:"文学",sub:"中国语言文学 · 外国语言文学 · 新闻传播",ghost:"文"},
      {code:"06",name:"历史学",sub:"历史学类",ghost:"史"},
      {code:"07",name:"理学",sub:"数学 · 物理 · 化学 · 生物 · 心理 · 统计",ghost:"理"},
      {code:"08",name:"工学",sub:"计算机 · 电子 · 机械 · 土木 · 化工 · 材料",ghost:"工"},
      {code:"09",name:"农学",sub:"植物 · 动物 · 林学 · 水产 · 草学",ghost:"农"},
      {code:"10",name:"医学",sub:"临床 · 口腔 · 公卫 · 中医 · 药学 · 护理",ghost:"医"},
      {code:"12",name:"管理学",sub:"工商 · 公管 · 物流 · 旅游 · 电商",ghost:"管"},
      {code:"13",name:"艺术学",sub:"音乐 · 戏剧 · 美术 · 设计",ghost:"艺"},
      {code:"14",name:"交叉学科",sub:"集成电路 · 国家安全 · 区域国别",ghost:"交"},
    ];
    const items = list.length ? list.map(d => ({
      code: d.code, name: d.name, sub: (d.sub || []).slice(0, 5).map(s => s.name).join(" · "),
      ghost: d.name.slice(0, 1), total: d.total || (d.sub || []).reduce((a, s) => a + (s.total || 0), 0),
    })) : fallback.map(f => ({...f, total: 0}));

    // 算 精品数 / 总专业数
    const counts = {};
    for (const m of M.manifest.majors) {
      const code = m.discipline;
      counts[code] = counts[code] || {star: 0, all: 1};
      counts[code].star++;
    }
    const totalAll = {};
    for (const d of (M.hierarchy?.disciplines || [])) {
      totalAll[d.code] = d.total || 0;
    }

    chapters.innerHTML = items.map(d => {
      const c = counts[d.code] || {star: 0};
      const total = totalAll[d.code] || d.total || 0;
      const ck = colorKey[d.code] || "--accent";
      return `
        <a class="chapter" href="catalog.html#d=${d.code}" data-ghost="${d.ghost}" style="--theme: var(${ck});">
          <div class="chapter-head">
            <div class="chapter-meta">
              <div class="chapter-num">No. ${d.code}</div>
              <div class="chapter-name">${d.name}</div>
              <div class="chapter-sub">${d.sub}</div>
            </div>
            <div class="chapter-count">
              <span class="n">${c.star}<span class="star">★</span></span>
              <span class="of">${total > 0 ? `/ ${total} 专业` : `/ ${c.star}`}</span>
            </div>
            <div class="chapter-arrow">›</div>
          </div>
        </a>
      `;
    }).join("");
  }
})();
