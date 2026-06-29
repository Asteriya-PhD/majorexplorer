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
 *       title: "计算机科学与技术",          // 可选 (旧 mobile 数据迁移可能缺)
 *       style: "cs",                      // 主题色 / 徽章, 可选
 *       category: "工学 · 计算机类",       // 分类, 可选
 *       score: 5,                          // 1..5 (PC recommender 用)
 *       rating: 5,                         // 1..5 (mobile UI 用, 同 score 同步)
 *       tag: "冲",                         // mobile 标签, 可选
 *       comment: "...",                    // mobile 备注, 可选
 *       addedAt: "2026-06-12T08:23:14Z"    // ISO 时间戳
 *     },
 *     ...
 *   ]
 *
 * 兼容: mobile 旧数据 (key "m.wishlist.v1", schema {slug, rating, tag, comment, addedAt})
 *       通过 migrate() 一次性迁到 gk.wishlist.v1,迁移完删除旧 key。
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
    // Day 36 P1-10: 仅在非数字时 fallback 3, 不要把 0/NaN 一律替换为 1
    if (!Number.isFinite(n)) return 3;
    const i = parseInt(n, 10);
    if (isNaN(i)) return 3;
    if (i < 1) return 1;
    if (i > 5) return 5;
    return i;
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
     *
     * 可选 extras: rating (1-5 同 score 同步), tag (string), comment (string)
     *  - rating 用于 mobile UI 5 星显示 (与 score 同步存双份)
     *  - tag/comment 是 mobile UI 字段
     */
    upsert({ slug, title, style, category, score, rating, tag, comment }) {
      if (!slug) return { ok: false, reason: "missing slug" };
      const items = _read();
      const idx = items.findIndex((x) => x.slug === slug);
      const cleanScore = _clamp(score != null ? score : rating);
      if (idx >= 0) {
        items[idx].score = cleanScore;
        if (rating !== undefined) items[idx].rating = _clamp(rating);
        else if (items[idx].rating == null) items[idx].rating = cleanScore;
        if (tag !== undefined) items[idx].tag = tag;
        if (comment !== undefined) items[idx].comment = comment;
        if (style) items[idx].style = style;
        if (category) items[idx].category = category;
        if (title) items[idx].title = title;
        _write(items);
        return { ok: true, updated: true };
      }
      // Day 36 P0-7: 与 upsert 区别 — update 不要求 slug 存在, 不抛错 (silent fallback to upsert for new)
      return this.upsert({ slug, title, style, category, score, rating, tag, comment });
    },

    /**
     * Day 36 P0-7: 增量更新已存在条目 (来自 share.js:864 shareScore modal)
     * patch = { score?, tag?, comment?, style?, category?, title? }
     * 不存在时 silent fallback: 调用 upsert 创建
     */
    update(slug, patch = {}) {
      if (!slug) return { ok: false, reason: "missing slug" };
      const items = _read();
      const idx = items.findIndex((x) => x.slug === slug);
      if (idx < 0) {
        // slug 不存在 -> silent upsert 创建
        return this.upsert({ slug, ...patch });
      }
      // 存在 -> 浅合并, 保留未指定字段
      for (const k of ["title", "style", "category", "tag", "comment"]) {
        if (patch[k] !== undefined && patch[k] !== "") items[idx][k] = patch[k];
      }
      if (patch.rating !== undefined || patch.score !== undefined) {
        items[idx].score = _clamp(patch.rating != null ? patch.rating : patch.score);
        items[idx].rating = items[idx].score;
      }
      _write(items);
      return { ok: true, updated: true };
    },
      if (items.length >= MAX) {
        return { ok: false, reason: "full", limit: MAX };
      }
      items.push({
        slug,
        title: title || "",
        style: style || "humanities",
        category: category || "",
        score: cleanScore,
        rating: rating !== undefined ? _clamp(rating) : cleanScore,
        tag: tag || "",
        comment: comment || "",
        addedAt: new Date().toISOString(),
      });
      _write(items);
      return { ok: true, added: true };
    },

    /** 从 mobile 旧 localStorage key 一次性迁移数据
     *  - old schema: {slug, rating, tag?, comment?, addedAt?}
     *  - new schema (gk.wishlist.v1): 含 score (同 rating), title/style/category 缺失
     *  - 迁移后删除 old key (幂等: 已删过则 noop)
     *  - 失败 try/catch, 不阻塞主流程
     */
    migrate() {
      const OLD_KEY = "m.wishlist.v1";
      try {
        const raw = typeof localStorage === "undefined" ? null : localStorage.getItem(OLD_KEY);
        if (!raw) return { migrated: 0, source: null };
        const old = JSON.parse(raw);
        if (!Array.isArray(old) || old.length === 0) {
          localStorage.removeItem(OLD_KEY);
          return { migrated: 0, source: "empty" };
        }
        const cur = _read();
        const slugs = new Set(cur.map((x) => x.slug));
        let n = 0;
        for (const item of old) {
          const slug = typeof item === "string" ? item : item && item.slug;
          if (!slug || slugs.has(slug)) continue;
          const rating = (item && typeof item.rating === "number") ? item.rating : 3;
          // 不带 title/style/category, render 时由 manifest lookup 补
          this.upsert({
            slug,
            rating,
            tag: item && item.tag,
            comment: item && item.comment,
          });
          slugs.add(slug);
          n++;
        }
        localStorage.removeItem(OLD_KEY);
        return { migrated: n, source: OLD_KEY };
      } catch (e) {
        console.warn("[wishlist] migrate failed", e);
        return { migrated: 0, source: null, error: String(e && e.message || e) };
      }
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
