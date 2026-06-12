/* ====================================================================
 * wishlist-store.js
 *
 * localStorage 封装 — Major Explorer 心愿单 (最多 6 个专业, 每个 1-5⭐).
 * 全局唯一的 window.WishlistStore, 4 页 + 69 专业 HTML 共用。
 *
 * Schema (localStorage key "gk.wishlist.v1"):
 *   [
 *     {
 *       slug: "computer-science",
 *       title: "计算机科学与技术",
 *       style: "cs",                      // 主题色 / 徽章
 *       category: "工学 · 计算机类",       // 分类
 *       score: 5,                          // 1..5
 *       addedAt: "2026-06-12T08:23:14Z"    // ISO 时间戳
 *     },
 *     ...
 *   ]
 *
 * 同时广播 storage / custom event 让 chip 实时更新。
 * ==================================================================== */

(function (global) {
  "use strict";

  const KEY = "gk.wishlist.v1";
  const MIN = 4;       // 启用推荐的下限
  const MAX = 6;       // 心愿单上限
  const EVENT = "wishlist:change";

  function _safeParse(str) {
    if (!str) return [];
    try {
      const v = JSON.parse(str);
      return Array.isArray(v) ? v : [];
    } catch (e) {
      console.warn("[wishlist] parse failed, resetting", e);
      return [];
    }
  }

  function _read() {
    if (typeof localStorage === "undefined") return [];
    return _safeParse(localStorage.getItem(KEY));
  }

  function _write(items) {
    if (typeof localStorage === "undefined") return;
    try {
      localStorage.setItem(KEY, JSON.stringify(items));
    } catch (e) {
      console.warn("[wishlist] write failed", e);
      return;
    }
    // 跨页通过 storage 事件; 同页通过 custom event
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent(EVENT, { detail: { items } }));
    }
  }

  function _clamp(n) {
    n = parseInt(n, 10);
    if (isNaN(n)) return 3;
    if (n < 1) return 1;
    if (n > 5) return 5;
    return n;
  }

  const WishlistStore = {
    MIN,
    MAX,
    EVENT,
    KEY,

    /** 当前所有项 (新到旧 order 与 add 顺序一致) */
    all() {
      return _read();
    },

    /** 当前数量 */
    count() {
      return _read().length;
    },

    /** 是否满 4 个 (可以生成推荐) */
    isReady() {
      return _read().length >= MIN;
    },

    /** 是否已达上限 */
    isFull() {
      return _read().length >= MAX;
    },

    /** 是否包含 slug */
    has(slug) {
      return _read().some((x) => x.slug === slug);
    },

    /** 获取某 slug 的星级 (不存在返回 null) */
    getScore(slug) {
      const item = _read().find((x) => x.slug === slug);
      return item ? item.score : null;
    },

    /** 获取单条 */
    get(slug) {
      return _read().find((x) => x.slug === slug) || null;
    },

    /** 加入 / 更新一条
     * 已存在 → 更新 score
     * 不存在 + 未满 → push
     * 不存在 + 已满 → 返回 false
     */
    upsert({ slug, title, style, category, score }) {
      if (!slug || !title) return { ok: false, reason: "missing slug/title" };
      const items = _read();
      const idx = items.findIndex((x) => x.slug === slug);
      const cleanScore = _clamp(score);
      if (idx >= 0) {
        items[idx].score = cleanScore;
        if (style) items[idx].style = style;
        if (category) items[idx].category = category;
        if (title) items[idx].title = title;
        _write(items);
        return { ok: true, updated: true };
      }
      if (items.length >= MAX) {
        return { ok: false, reason: "full", limit: MAX };
      }
      items.push({
        slug,
        title,
        style: style || "humanities",
        category: category || "",
        score: cleanScore,
        addedAt: new Date().toISOString(),
      });
      _write(items);
      return { ok: true, added: true };
    },

    /** 删除 slug */
    remove(slug) {
      const items = _read();
      const next = items.filter((x) => x.slug !== slug);
      if (next.length === items.length) return false;
      _write(next);
      return true;
    },

    /** 仅改星级 */
    setScore(slug, score) {
      const items = _read();
      const idx = items.findIndex((x) => x.slug === slug);
      if (idx < 0) return false;
      items[idx].score = _clamp(score);
      _write(items);
      return true;
    },

    /** 清空 */
    clear() {
      _write([]);
    },

    /** 订阅变更 (同页 + 跨页) → 返回 unsub */
    subscribe(handler) {
      if (typeof window === "undefined") return () => {};
      const onCustom = (e) => handler(e.detail.items);
      const onStorage = (e) => {
        if (e.key === KEY) handler(_read());
      };
      window.addEventListener(EVENT, onCustom);
      window.addEventListener("storage", onStorage);
      // 首次同步
      handler(_read());
      return () => {
        window.removeEventListener(EVENT, onCustom);
        window.removeEventListener("storage", onStorage);
      };
    },

    /** 导出 recommender.js 期望的 interests 数组
     *  心愿单 score 直接当 interests score
     */
    toInterests() {
      return _read().map((x) => ({
        major: x.title,
        slug: x.slug,
        score: x.score,
        style: x.style,
      }));
    },
  };

  global.WishlistStore = WishlistStore;
})(typeof window !== "undefined" ? window : globalThis);
