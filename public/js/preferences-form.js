/* ====================================================================
 * preferences-form.js
 *
 * 偏好填写页表单逻辑.
 *  - 校验: 至少分数 或 位次 ≥1; 选科 ≤3; 城市 ≤3
 *  - 提交: 写 sessionStorage("gk.user.v1"), 跳 recommendations.html
 *
 * 表单字段 → user 对象:
 *   score      number
 *   rank       number  (可空, 自动反查)
 *   type       '物理类' | '历史类'
 *   xuanke     string[]
 *   cities     [{city, score}]
 *   mode       '院校优先' | '专业优先' | '均衡'
 *
 * interests 由 WishlistStore.toInterests() 提供, 不在此填写.
 * ==================================================================== */

(function (global) {
  "use strict";

  const KEY_USER = "gk.user.v1";
  // 3 省城市池 (2026-06-25 改造)
  const CITIES_BY_PROV = {
    hubei: [
      "武汉", "上海", "北京", "广州", "深圳", "南京", "杭州", "成都",
      "西安", "天津", "重庆", "苏州", "厦门", "长沙", "合肥", "济南",
      "青岛", "宁波", "大连", "沈阳", "哈尔滨", "郑州", "福州", "昆明",
      "石家庄", "太原", "兰州", "贵阳", "南宁", "海口", "南昌",
      "黄石", "宜昌", "襄阳", "荆州", "十堰", "孝感", "黄冈", "鄂州", "咸宁",
    ],
    guangdong: [
      "广州", "深圳", "佛山", "东莞", "珠海", "中山", "惠州", "汕头",
      "湛江", "江门", "肇庆", "茂名", "揭阳", "潮州", "梅州", "清远",
      "韶关", "阳江", "河源", "云浮",
      "上海", "北京", "武汉", "南京", "杭州", "成都", "西安",
    ],
    jiangsu: [
      "南京", "苏州", "无锡", "常州", "徐州", "南通", "扬州", "盐城",
      "淮安", "连云港", "镇江", "泰州", "宿迁",
      "上海", "北京", "杭州", "合肥", "武汉",
    ],
  };
  // 向后兼容老代码
  const HUBEI_CITIES = CITIES_BY_PROV.hubei;

  const XUANKE = ["物理", "历史", "化学", "生物", "地理", "政治"];

  function _getCurrentProv() {
    try {
      var raw = sessionStorage.getItem('gk.province.v1');
      if (raw && CITIES_BY_PROV[raw]) return raw;
    } catch (e) {}
    return 'hubei';
  }

  function _read() {
    try { return JSON.parse(sessionStorage.getItem(KEY_USER) || "null") || {}; }
    catch (e) { return {}; }
  }
  function _write(user) {
    sessionStorage.setItem(KEY_USER, JSON.stringify(user));
  }

  function defaultUser() {
    const prov = _getCurrentProv();
    const defaultCity = ({ hubei: "武汉", guangdong: "广州", jiangsu: "南京" })[prov] || "武汉";
    return {
      province: prov,
      score: null,
      rank: null,
      type: "物理类",
      xuanke: prov === "jiangsu" ? ["物理", "化学"] : ["物理", "化学", "生物"],
      cities: [{ city: defaultCity, score: 5 }],
      mode: "均衡",
    };
  }

  /** 渲染城市挑选区. wrap = .city-list */
  function renderCityList(wrap, cities) {
    const UI = global.UIHelpers;
    wrap.innerHTML = "";
    if (cities.length === 0) {
      const empty = document.createElement("div");
      empty.className = "city-empty";
      empty.textContent = "还没选城市 (点下方按钮加)";
      empty.style.cssText = "padding: 16px; background: var(--bg-soft); border-radius: 8px; color: var(--muted); font-size: 0.875rem; text-align: center;";
      wrap.appendChild(empty);
    }
    cities.forEach((c, idx) => {
      const item = document.createElement("div");
      item.className = "city-item fade-in";
      item.style.cssText = "display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: #fff; border: 1px solid var(--line); border-radius: 8px; margin-bottom: 8px;";
      item.innerHTML = [
        '<span style="font-family: var(--font-num); color: var(--muted); font-size: 0.75rem; min-width: 20px;">#' + (idx + 1) + '</span>',
        '<span style="font-family: var(--font-heading); font-weight: 600; min-width: 60px;">' + UI.escapeHtml(c.city) + '</span>',
        '<span class="stars-holder" style="flex: 1;"></span>',
        '<button type="button" class="del-city" aria-label="删除 ' + UI.escapeHtml(c.city) + '" style="color: var(--muted); padding: 4px 8px; font-size: 1rem;">✕</button>',
      ].join("");

      const starsHolder = item.querySelector(".stars-holder");
      starsHolder.appendChild(UI.renderStars(c.score, {
        onChange: (v) => { c.score = v; },
      }));
      item.querySelector(".del-city").addEventListener("click", () => {
        cities.splice(idx, 1);
        renderCityList(wrap, cities);
      });
      wrap.appendChild(item);
    });
  }

  /** 城市添加 datalist 互动 */
  function bindCityAdder(input, btn, cities, wrap) {
    btn.addEventListener("click", () => {
      const name = input.value.trim();
      if (!name) return;
      if (cities.length >= 3) {
        global.UIHelpers.toast("最多 3 个城市");
        return;
      }
      if (cities.some((c) => c.city === name)) {
        global.UIHelpers.toast("已添加过 " + name);
        return;
      }
      cities.push({ city: name, score: 4 });
      input.value = "";
      renderCityList(wrap, cities);
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        btn.click();
      }
    });
  }

  /** 主初始化 */
  function init() {
    const $ = (s) => document.querySelector(s);
    const $$ = (s) => document.querySelectorAll(s);

    // 读 cache (用户可能回填)
    const prev = _read();
    const user = Object.assign(defaultUser(), prev);
    // 兼容 cities 是字符串列表的老 schema
    user.cities = (user.cities || []).map((c) =>
      typeof c === "string" ? { city: c, score: 5 } : c
    );
    if (!Array.isArray(user.xuanke)) user.xuanke = ["物理", "化学", "生物"];

    // 字段回填
    const scoreEl = $("#f-score");
    const rankEl = $("#f-rank");
    const typeRadios = $$('input[name="f-type"]');
    const xuankeChecks = $$('input[name="f-xuanke"]');
    const cityList = $("#city-list");
    const cityInput = $("#f-city");
    const cityBtn = $("#add-city");
    const modeRadios = $$('input[name="f-mode"]');

    scoreEl.value = user.score == null ? "" : user.score;
    rankEl.value = user.rank == null ? "" : user.rank;
    typeRadios.forEach((r) => { r.checked = (r.value === user.type); });
    xuankeChecks.forEach((c) => { c.checked = user.xuanke.indexOf(c.value) !== -1; });
    renderCityList(cityList, user.cities);
    bindCityAdder(cityInput, cityBtn, user.cities, cityList);
    modeRadios.forEach((r) => { r.checked = (r.value === user.mode); });

    // 物理 / 历史互斥 — 首选自动反映到 xuanke
    typeRadios.forEach((r) => {
      r.addEventListener("change", () => {
        if (!r.checked) return;
        const newType = r.value;
        // 自动把首选钩上, 取消另一个
        const want = (newType === "物理类" ? "物理" : "历史");
        const drop = (newType === "物理类" ? "历史" : "物理");
        xuankeChecks.forEach((c) => {
          if (c.value === want) c.checked = true;
          if (c.value === drop) c.checked = false;
        });
      });
    });

    // 选科上限 3, 物理/历史只能选一个
    xuankeChecks.forEach((c) => {
      c.addEventListener("change", () => {
        // 物理 + 历史 互斥
        if (c.value === "物理" && c.checked) {
          xuankeChecks.forEach((x) => { if (x.value === "历史") x.checked = false; });
        }
        if (c.value === "历史" && c.checked) {
          xuankeChecks.forEach((x) => { if (x.value === "物理") x.checked = false; });
        }
        const checked = Array.from(xuankeChecks).filter((x) => x.checked);
        if (checked.length > 3) {
          c.checked = false;
          global.UIHelpers.toast("最多选 3 科");
        }
      });
    });

    // 心愿单存在性 hint
    const wsCount = global.WishlistStore.count();
    const wsHint = $("#ws-hint");
    if (wsCount < global.WishlistStore.MIN) {
      wsHint.innerHTML = "⚠️ 心愿单只有 <strong>" + wsCount + "</strong> 个专业, 至少需要 4 个 → <a href=\"/wishlist.html\">补一下</a>";
      wsHint.style.color = "var(--accent)";
    } else {
      wsHint.innerHTML = "✓ 心愿单已有 <strong>" + wsCount + "</strong> 个专业 (心愿单决定专业匹配权重)";
      wsHint.style.color = "var(--ok)";
    }

    // 提交
    $("#cta-go").addEventListener("click", () => {
      const score = parseFloat(scoreEl.value);
      const rank = parseInt(rankEl.value, 10);
      const type = Array.from(typeRadios).find((r) => r.checked).value;
      const xuanke = Array.from(xuankeChecks).filter((c) => c.checked).map((c) => c.value);
      const mode = Array.from(modeRadios).find((r) => r.checked).value;

      // 校验
      if (isNaN(score) && isNaN(rank)) {
        global.UIHelpers.toast("分数或位次至少填一个");
        return;
      }
      if (!isNaN(score) && (score < 200 || score > 750)) {
        global.UIHelpers.toast("分数应在 200–750 之间");
        return;
      }
      if (!isNaN(rank) && (rank < 1 || rank > 600000)) {
        global.UIHelpers.toast("位次应在 1–600000 之间");
        return;
      }
      if (xuanke.length < 3) {
        global.UIHelpers.toast("请选 3 门科目");
        return;
      }
      const first = type === "物理类" ? "物理" : "历史";
      if (xuanke.indexOf(first) === -1) {
        global.UIHelpers.toast(type + " 必须选 " + first);
        return;
      }
      if (global.WishlistStore.count() < global.WishlistStore.MIN) {
        if (!confirm("心愿单不足 4 个专业, 推荐结果会偏向通用院校。继续吗?")) return;
      }

      const finalUser = {
        score: isNaN(score) ? null : score,
        rank: isNaN(rank) ? null : rank,
        type,
        xuanke,
        cities: user.cities,
        mode,
      };
      _write(finalUser);
      window.location.href = "/recommendations.html";
    });
  }

  global.PreferencesForm = {
    init,
    KEY_USER,
    defaultUser,
    HUBEI_CITIES,
    XUANKE,
  };
})(typeof window !== "undefined" ? window : globalThis);
