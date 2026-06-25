/* ====================================================================
 * data-loader.js
 *
 * 分级数据加载 (轻包 vs 重包) + IndexedDB 缓存.
 *
 * 轻包 ≈ 295 KB, 用于首页 / 心愿单 / 偏好页:
 *   - colleges.json          (1008 校 基础信息)
 *   - province_lines.json    (本一/特控线, 3 省嵌套)
 *   - yfyd_index.json        (一分一段路由, 新)
 *   - yfyd_{prov}_{year}.json (一分一段实际数据, 按省 + 年路由)
 *   - chsi_schools.json
 *
 * 重包 ≈ 3.4 MB, 用于推荐结果页:
 *   - school_history.json    (4 年位次, 全国聚合)
 *   - groups_index.json      (groups_latest 路由, 新)
 *   - groups_latest_{prov}_{year}.json (2024/2025 专业组+选科, 按省 + 年路由)
 *   - school_specialties.json (院校主打专业)
 *   - school_all_majors.json  (128 校 × 3 年合并, 完整专业清单) — majorMatch 主源
 *   - major_synonyms.json     (20 类目同义词) — majorMatch 展开用户兴趣
 *
 * 省份路由 (2026-06-25 改造):
 *   getDataForProvince(prov) → 按 yfyd_index/groups_index 加载对应省份数据
 *   兼容老 loadLight/loadHeavy/loadAll: 走 hubei 默认
 *
 * 缓存策略:
 *   1) 首次 fetch → 写 IndexedDB (objstore "files", key = name)
 *   2) 命中相同版本 → 直接 IDB 取, < 200ms
 *   3) URL 带 ?v=<DATA_VERSION>; 改版本号清缓存
 *
 * 公开 API (window.DataLoader):
 *   await loadLight()    → {colleges, provinceLines, yfyd}     [hubei 默认]
 *   await loadHeavy()    → {schoolHistory, groupsLatest, ...}  [hubei 默认]
 *   await loadAll()      → 合并两批                            [hubei 默认]
 *   await getDataForProvince(prov) → 完整 data 对象, 按省路由
 *   await clear()        → 清缓存
 * ==================================================================== */

(function (global) {
  "use strict";

  // 改这里来强制全量重取 (2026-06-25 加省份路由 → 20260625a)
  // bump: 每次改数据 schema 必须 bump, 否则用户 IDB cache 不刷新
  const DATA_VERSION = "20260625e";
  const DATA_DIR = "/data";
  const DB_NAME = "gk.dataCache.v1";
  const DB_STORE = "files";
  // cache 最大寿命 (小时) — 超过强制重 fetch, 避免版本号没 bump 时用户卡老数据
  const CACHE_MAX_AGE_HOURS = 24;

  // 兼容旧引用: 仍列出 yfyd_2025.json 作为湖北默认, 但新代码用 getDataForProvince(prov)
  // 2026-06-25 改造: 实际路径是 yfyd_hubei_2025.json (湖北 default)
  // 注: loadLight 走老路径, 老 HTML 可能直接读 yfyd_2025.json — 保持兼容
  // 实际新代码应使用 getDataForProvince(prov)
  const LIGHT_FILES = ["colleges.json", "province_lines.json", "yfyd_2025.json", "chsi_schools.json"];
  const HEAVY_FILES = [
    "school_history.json",
    "groups_latest.json",
    "school_specialties.json",
    "school_all_majors.json",   // 128 校全量专业 (T1 产物, majorMatch 主源)
    "major_synonyms.json",      // 20 类目同义词 (T2 产物, majorMatch 展开)
  ];
  const SPECIAL_FILES = ["linkage.json"]; // 可选, 当前不强制

  // ─────────────── IndexedDB 极简封装 ───────────────
  function _openDB() {
    return new Promise((resolve, reject) => {
      if (typeof indexedDB === "undefined") return reject(new Error("no IndexedDB"));
      const req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(DB_STORE)) {
          db.createObjectStore(DB_STORE, { keyPath: "name" });
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function _idbGet(name) {
    try {
      const db = await _openDB();
      return await new Promise((resolve) => {
        const tx = db.transaction(DB_STORE, "readonly");
        const store = tx.objectStore(DB_STORE);
        const req = store.get(name);
        req.onsuccess = () => resolve(req.result || null);
        req.onerror = () => resolve(null);
      });
    } catch (e) {
      return null;
    }
  }

  async function _idbPut(name, version, payload) {
    try {
      const db = await _openDB();
      return await new Promise((resolve) => {
        const tx = db.transaction(DB_STORE, "readwrite");
        const store = tx.objectStore(DB_STORE);
        const req = store.put({ name, version, payload, savedAt: Date.now() });
        req.onsuccess = () => resolve(true);
        req.onerror = () => resolve(false);
      });
    } catch (e) {
      return false;
    }
  }

  async function _idbClear() {
    try {
      const db = await _openDB();
      return await new Promise((resolve) => {
        const tx = db.transaction(DB_STORE, "readwrite");
        tx.objectStore(DB_STORE).clear();
        tx.oncomplete = () => resolve(true);
        tx.onerror = () => resolve(false);
      });
    } catch (e) { return false; }
  }

  // ─────────────── 单文件加载 (cache → fetch) ───────────────
  async function loadFile(name, { force } = {}) {
    if (!force) {
      const cached = await _idbGet(name);
      if (cached) {
        // 1) 版本不匹配 → 重 fetch
        // 2) 版本匹配但 cache 太老 (CACHE_MAX_AGE_HOURS+) → 重 fetch
        //    防止 version 没 bump 时用户卡老数据 (Day 31 教训)
        const versionMatch = cached.version === DATA_VERSION;
        const ageHours = cached.savedAt ? (Date.now() - cached.savedAt) / 3600000 : Infinity;
        const tooOld = ageHours > CACHE_MAX_AGE_HOURS;
        if (versionMatch && !tooOld) {
          return cached.payload;
        }
      }
    }
    const url = DATA_DIR + "/" + name + "?v=" + DATA_VERSION;
    const res = await fetch(url, { cache: "force-cache" });
    if (!res.ok) throw new Error("Failed to fetch " + name + ": " + res.status);
    const json = await res.json();
    _idbPut(name, DATA_VERSION, json); // 不 await; 写入后台
    return json;
  }

  async function _loadGroup(files, label) {
    const started = performance.now();
    const arr = await Promise.all(files.map((f) => loadFile(f)));
    const elapsed = (performance.now() - started).toFixed(0);
    if (typeof console !== "undefined") {
      console.log("[data-loader] " + label + " loaded in " + elapsed + "ms");
    }
    // Staleness 检查 — 任何文件被重 fetch (stale >24h 或 version mismatch),
    // 提示用户刷新 (Day 31 教训: 用户卡老数据不知情)
    _checkStalenessAndWarn(files);
    return arr;
  }

  // ─────────────── Staleness banner (2026-06-25 新增) ───────────────
  // 检查所有 IDB cache entries, 如果 stale (>24h 或 version mismatch), 显示软提示
  // 用户点 → 清 IDB + reload, 拿到新数据
  // 不强制 reload, 给用户选择权 (vs Day 31 强 reload 卡 6 小时)
  async function _checkStalenessAndWarn(files) {
    try {
      const db = await _openDB();
      const tx = db.transaction(DB_STORE, "readonly");
      const store = tx.objectStore(DB_STORE);
      const allKeys = await new Promise((resolve) => {
        const req = store.getAllKeys();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve([]);
      });
      let staleCount = 0;
      for (const key of allKeys) {
        const entry = await new Promise((resolve) => {
          const req = store.get(key);
          req.onsuccess = () => resolve(req.result || null);
          req.onerror = () => resolve(null);
        });
        if (!entry) continue;
        const versionMatch = entry.version === DATA_VERSION;
        const ageHours = entry.savedAt ? (Date.now() - entry.savedAt) / 3600000 : Infinity;
        if (!versionMatch || ageHours > CACHE_MAX_AGE_HOURS) staleCount++;
      }
      if (staleCount > 0) _showStalenessBanner(staleCount);
    } catch (e) { /* IDB 不可用, 静默 */ }
  }

  function _showStalenessBanner(staleCount) {
    if (typeof document === "undefined") return;
    // 防重复
    if (document.getElementById("gk-staleness-banner")) return;
    const banner = document.createElement("div");
    banner.id = "gk-staleness-banner";
    banner.style.cssText = [
      "position: fixed",
      "top: 12px",
      "left: 50%",
      "transform: translateX(-50%)",
      "z-index: 9999",
      "background: #FFF8E1",
      "border: 1px solid #E8C766",
      "border-left: 4px solid #D4AF37",
      "border-radius: 8px",
      "padding: 10px 16px",
      "font-size: 0.875rem",
      "color: #5C4A1F",
      "box-shadow: 0 4px 12px rgba(0,0,0,0.08)",
      "display: flex",
      "align-items: center",
      "gap: 12px",
      "max-width: calc(100vw - 24px)",
    ].join(";");
    banner.innerHTML = [
      '<span>🔄 检测到 ' + staleCount + ' 个数据文件可能过期</span>',
      '<button id="gk-staleness-refresh" type="button" style="',
        'background: #D4AF37; color: #fff; border: none; border-radius: 6px;',
        'padding: 4px 12px; font-weight: 600; cursor: pointer;',
      '">刷新数据</button>',
      '<button id="gk-staleness-dismiss" type="button" aria-label="忽略" style="',
        'background: transparent; border: none; color: #8B6914; cursor: pointer;',
        'font-size: 1.125rem; padding: 0 4px;',
      '">✕</button>',
    ].join("");
    document.body.appendChild(banner);
    document.getElementById("gk-staleness-refresh").addEventListener("click", async () => {
      // 清 IDB + reload
      banner.querySelector("button").textContent = "刷新中...";
      await clear();
      location.reload();
    });
    document.getElementById("gk-staleness-dismiss").addEventListener("click", () => {
      banner.remove();
    });
  }

  async function loadLight() {
    const [colleges, provinceLines, yfyd, chsiSchools] = await _loadGroup(LIGHT_FILES, "light");
    // 双 index (Step 3.4 v1): byId 用 school_id (向后兼容), byEid 用 edu_id 主键
    const byId = {};
    const byEid = {};
    for (const c of colleges) {
      if (c.school_id != null) byId[c.school_id] = c;
      const eid = c.chsi_edu_id;
      const key = eid ? String(eid) : (c.school_id != null ? `sch_${c.school_id}` : null);
      if (key) byEid[key] = c;
    }
    // chsi_schools 按 edu_id 索引 (用于 recommender 加 chsi 维度, Step 2.3)
    const chsiByEduId = {};
    for (const s of (chsiSchools || [])) {
      if (s.edu_id) chsiByEduId[String(s.edu_id)] = s;
    }
    return {
      colleges,
      collegesById: byId,        // legacy: school_id → college
      collegesByEid: byEid,      // new (Step 3.4 v1): edu_id (or sch_<sid>) → college
      provinceLines,
      yfyd,
      chsiSchools,
      chsiByEduId,
    };
  }

  async function loadHeavy() {
    const [schoolHistory, groupsLatest, specialties, schoolAllMajors, majorSynonyms] = await _loadGroup(HEAVY_FILES, "heavy");
    return { schoolHistory, groupsLatest, specialties, schoolAllMajors, majorSynonyms };
  }

  async function loadAll() {
    const [light, heavy] = await Promise.all([loadLight(), loadHeavy()]);
    return Object.assign({}, light, heavy);
  }

  // ─────────────── 省份路由 (2026-06-25 新增) ───────────────
  // 加载 yfyd_index + groups_index, 按省份路由 yfyd / groups_latest 文件
  // 老 API (loadLight/loadHeavy/loadAll) 走 hubei 默认不破坏兼容
  async function getDataForProvince(prov = "hubei") {
    // Load indices
    const [yfydIndex, groupsIndex] = await Promise.all([
      loadFile("yfyd_index.json"),
      loadFile("groups_index.json"),
    ]);

    const provKey = yfydIndex.provinces[prov] ? prov : (yfydIndex.default_province || "hubei");
    const provDisplay = (yfydIndex.provinces[provKey] && yfydIndex.provinces[provKey].display) || "湖北";

    const yfCfg = yfydIndex.provinces[provKey];
    const gCfg = groupsIndex.provinces[provKey];

    const yfydFile = yfCfg.files[yfCfg.latest];
    const groupsFile = gCfg.files[gCfg.latest_year];

    // Parallel: light (3 省无关 + yfyd 按省) + heavy (school_history 省无关 + groups 按省 + 3 通用品)
    const [colleges, provinceLinesAll, yfyd, chsiSchools, schoolHistory, groupsLatest, specialties, schoolAllMajors, majorSynonyms] = await Promise.all([
      loadFile("colleges.json"),
      loadFile("province_lines.json"),
      loadFile(yfydFile),
      loadFile("chsi_schools.json"),
      loadFile("school_history.json"),
      loadFile(groupsFile),
      loadFile("school_specialties.json"),
      loadFile("school_all_majors.json"),
      loadFile("major_synonyms.json"),
    ]);

    // Build indices (跟 loadLight 一样)
    const byId = {};
    const byEid = {};
    for (const c of colleges) {
      if (c.school_id != null) byId[c.school_id] = c;
      const eid = c.chsi_edu_id;
      const key = eid ? String(eid) : (c.school_id != null ? `sch_${c.school_id}` : null);
      if (key) byEid[key] = c;
    }
    const chsiByEduId = {};
    for (const s of (chsiSchools || [])) {
      if (s.edu_id) chsiByEduId[String(s.edu_id)] = s;
    }

    // Extract province-specific provinceLines (新 schema 是 {hubei:{...}, guangdong:{...}, jiangsu:{...}})
    const provinceLines = provinceLinesAll.provinces
      ? provinceLinesAll.provinces[provKey] || {}
      : provinceLinesAll;  // 老 schema 兜底

    return {
      province: provKey,
      provinceDisplay: provDisplay,
      colleges,
      collegesById: byId,
      collegesByEid: byEid,
      provinceLines,
      provinceLinesAll,
      yfyd,
      chsiSchools,
      chsiByEduId,
      schoolHistory,
      groupsLatest,
      specialties,
      schoolAllMajors,
      majorSynonyms,
    };
  }

  async function clear() {
    await _idbClear();
  }

  global.DataLoader = {
    DATA_VERSION,
    DATA_DIR,
    LIGHT_FILES,
    HEAVY_FILES,
    loadFile,
    loadLight,
    loadHeavy,
    loadAll,
    getDataForProvince,
    clear,
  };
})(typeof window !== "undefined" ? window : globalThis);
