/* ====================================================================
 * data-loader.js
 *
 * 分级数据加载 (轻包 vs 重包) + IndexedDB 缓存.
 *
 * 轻包 ≈ 295 KB, 用于首页 / 心愿单 / 偏好页:
 *   - colleges.json          (1008 校 基础信息)
 *   - province_lines.json    (本一/特控线)
 *   - yfyd_2025.json         (一分一段)
 *
 * 重包 ≈ 3.4 MB, 用于推荐结果页:
 *   - school_history.json    (4 年位次)
 *   - groups_latest.json     (2025 专业组+选科)
 *   - school_specialties.json (院校主打专业)
 *   - school_all_majors.json  (128 校 × 3 年合并, 完整专业清单) — majorMatch 主源
 *   - major_synonyms.json     (20 类目同义词) — majorMatch 展开用户兴趣
 *
 * 缓存策略:
 *   1) 首次 fetch → 写 IndexedDB (objstore "files", key = name)
 *   2) 命中相同版本 → 直接 IDB 取, < 200ms
 *   3) URL 带 ?v=<DATA_VERSION>; 改版本号清缓存
 *
 * 公开 API (window.DataLoader):
 *   await loadLight()    → {colleges, provinceLines, yfyd}
 *   await loadHeavy()    → {schoolHistory, groupsLatest, specialties, schoolAllMajors, majorSynonyms}
 *   await loadAll()      → 合并两批
 *   await clear()        → 清缓存
 * ==================================================================== */

(function (global) {
  "use strict";

  // 改这里来强制全量重取 (例: 2026-06-13 加 school_all_majors + major_synonyms → 20260613a)
  const DATA_VERSION = "20260613a";
  const DATA_DIR = "/data";
  const DB_NAME = "gk.dataCache.v1";
  const DB_STORE = "files";

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
      if (cached && cached.version === DATA_VERSION) {
        return cached.payload;
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
    return arr;
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
    clear,
  };
})(typeof window !== "undefined" ? window : globalThis);
