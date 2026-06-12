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
 *
 * 缓存策略:
 *   1) 首次 fetch → 写 IndexedDB (objstore "files", key = name)
 *   2) 命中相同版本 → 直接 IDB 取, < 200ms
 *   3) URL 带 ?v=<DATA_VERSION>; 改版本号清缓存
 *
 * 公开 API (window.DataLoader):
 *   await loadLight()    → {colleges, provinceLines, yfyd}
 *   await loadHeavy()    → {schoolHistory, groupsLatest, specialties}
 *   await loadAll()      → 合并两批
 *   await clear()        → 清缓存
 * ==================================================================== */

(function (global) {
  "use strict";

  // 改这里来强制全量重取 (例: 2026-06-12 第一版 → 20260612a)
  const DATA_VERSION = "20260612a";
  const DATA_DIR = "/data";
  const DB_NAME = "gk.dataCache.v1";
  const DB_STORE = "files";

  const LIGHT_FILES = ["colleges.json", "province_lines.json", "yfyd_2025.json"];
  const HEAVY_FILES = ["school_history.json", "groups_latest.json", "school_specialties.json"];
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
    const [colleges, provinceLines, yfyd] = await _loadGroup(LIGHT_FILES, "light");
    // colleges 是 list, 转 by_id 方便取
    const byId = {};
    for (const c of colleges) byId[c.school_id] = c;
    return {
      colleges,
      collegesById: byId,
      provinceLines,
      yfyd,
    };
  }

  async function loadHeavy() {
    const [schoolHistory, groupsLatest, specialties] = await _loadGroup(HEAVY_FILES, "heavy");
    return { schoolHistory, groupsLatest, specialties };
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
