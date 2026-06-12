/* ====================================================================
 * ui-helpers.js
 *
 * 通用 UI 渲染组件 — 4 新页 + 69 专业 HTML 共用.
 *  - renderStars(score, {readonly, onChange}) → HTMLElement
 *  - mountWishlistChip(container) → 自动 mount + subscribe 实时更新
 *  - openWishlistFab({slug, title, style, category}) → 弹窗
 *  - mountWishlistFab({slug, title, style, category}) → 注入 FAB 按钮 + 弹窗
 *  - toast(message, duration?) → 轻量提示
 *  - escapeHtml(str)
 *  - getThemeLabel(style)
 *  - getMajorIndexEntry(slug)   (优先用 manifest, 没有则降级 wishlist 自存)
 * ==================================================================== */

(function (global) {
  "use strict";

  const STYLES = [
    "cs", "finance", "medicine", "education", "law", "humanities",
    "sci", "eng", "administration", "agri", "arts", "gongan", "business",
  ];
  const STYLE_LABEL = {
    cs: "计算机", finance: "财经", medicine: "医学", education: "教育",
    law: "法学", humanities: "人文", sci: "理科", eng: "工科",
    administration: "公管", agri: "农学", arts: "艺术",
    gongan: "公安", business: "工商",
  };

  function escapeHtml(s) {
    if (s == null) return "";
    return String(s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function getThemeLabel(style) {
    return STYLE_LABEL[style] || "通识";
  }

  // ──────────────── 星级控件 ────────────────
  function renderStars(score, opts) {
    opts = opts || {};
    const readonly = !!opts.readonly;
    const wrap = document.createElement("span");
    wrap.className = "stars";
    if (readonly) wrap.setAttribute("data-readonly", "true");
    let current = parseInt(score, 10) || 0;

    for (let i = 1; i <= 5; i++) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "star";
      btn.textContent = "★";
      btn.setAttribute("aria-label", i + " 颗星");
      btn.setAttribute("data-val", String(i));
      if (i <= current) {
        btn.setAttribute("aria-pressed", "true");
        btn.classList.add("on");
      }
      if (!readonly) {
        btn.addEventListener("click", () => {
          current = i;
          // 重画
          wrap.querySelectorAll("button.star").forEach((b) => {
            const v = parseInt(b.dataset.val, 10);
            b.classList.toggle("on", v <= current);
            b.setAttribute("aria-pressed", v <= current ? "true" : "false");
          });
          if (typeof opts.onChange === "function") opts.onChange(current);
        });
      }
      wrap.appendChild(btn);
    }
    return wrap;
  }

  // ──────────────── 顶部 chip ────────────────
  function renderChip(count, max) {
    const a = document.createElement("a");
    a.className = "wishlist-chip";
    a.href = "/wishlist.html";
    a.setAttribute("aria-label", "心愿单 " + count + " / " + max);
    a.innerHTML =
      '<span aria-hidden="true">🎒</span> ' +
      '<span>心愿单</span> ' +
      '<span class="count">' + count + "/" + max + "</span> " +
      '<span class="arrow">→</span>';
    if (count === 0) a.setAttribute("data-state", "empty");
    else if (count >= 4) a.setAttribute("data-state", "ready");
    return a;
  }

  function mountWishlistChip(container) {
    if (!container || !global.WishlistStore) return null;
    const store = global.WishlistStore;
    function paint(items) {
      const c = items.length;
      container.innerHTML = "";
      container.appendChild(renderChip(c, store.MAX));
    }
    return store.subscribe(paint);
  }

  // ──────────────── 右下角 FAB ────────────────
  function _ensureToastEl() {
    let el = document.querySelector(".toast");
    if (!el) {
      el = document.createElement("div");
      el.className = "toast";
      document.body.appendChild(el);
    }
    return el;
  }

  function toast(msg, duration) {
    duration = duration || 1800;
    const el = _ensureToastEl();
    el.textContent = msg;
    el.classList.add("show");
    if (el._t) clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove("show"), duration);
  }

  function mountWishlistFab(meta) {
    if (!meta || !meta.slug || !meta.title || !global.WishlistStore) return null;
    const store = global.WishlistStore;

    // 1) FAB 按钮
    const fab = document.createElement("button");
    fab.className = "fab-wishlist";
    fab.type = "button";
    fab.setAttribute("aria-label", "加入心愿单");
    fab.innerHTML = "<span>⭐</span>";
    document.body.appendChild(fab);

    // 2) 弹窗
    const modal = document.createElement("div");
    modal.className = "fab-modal";
    modal.setAttribute("role", "dialog");
    modal.innerHTML = [
      '<div class="fab-title">' + escapeHtml(meta.title) + "</div>",
      '<div class="fab-sub">给这个专业评几颗星 (1-5)</div>',
      '<div class="fab-stars"></div>',
      '<div class="fab-actions">',
      '  <button class="ghost" data-act="cancel">取消</button>',
      '  <button class="primary" data-act="ok">加入心愿单</button>',
      "</div>",
    ].join("");
    document.body.appendChild(modal);

    const starsHolder = modal.querySelector(".fab-stars");
    let currentScore = store.getScore(meta.slug) || 4;
    const stars = renderStars(currentScore, {
      onChange: (v) => { currentScore = v; },
    });
    starsHolder.appendChild(stars);

    const titleEl = modal.querySelector(".fab-title");
    const subEl = modal.querySelector(".fab-sub");
    const primaryBtn = modal.querySelector('button[data-act="ok"]');

    function syncState() {
      const inList = store.has(meta.slug);
      const full = store.isFull();
      fab.setAttribute("data-state", inList ? "added" : (full ? "full" : "idle"));
      fab.innerHTML = inList
        ? '<span aria-hidden="true">✓</span>'
        : (full ? '<span aria-hidden="true">🎒</span>' : '<span aria-hidden="true">⭐</span>');
      fab.setAttribute("aria-label", inList
        ? "已在心愿单 (点击调整星级)"
        : (full ? "心愿单已满 6 个" : "加入心愿单"));
      // primary 文案
      primaryBtn.textContent = inList ? "保存调整" : "加入心愿单";
      subEl.textContent = inList
        ? "已加入心愿单, 可调整星级"
        : (full ? "心愿单已满 6 个 (去管理)" : "给这个专业评几颗星 (1-5)");
      primaryBtn.disabled = !inList && full;
    }
    syncState();

    function openModal() {
      currentScore = store.getScore(meta.slug) || 4;
      // 同步星级显示
      stars.querySelectorAll("button.star").forEach((b) => {
        const v = parseInt(b.dataset.val, 10);
        b.classList.toggle("on", v <= currentScore);
        b.setAttribute("aria-pressed", v <= currentScore ? "true" : "false");
      });
      modal.setAttribute("data-open", "true");
    }
    function closeModal() { modal.setAttribute("data-open", "false"); }

    fab.addEventListener("click", (e) => {
      e.stopPropagation();
      if (store.isFull() && !store.has(meta.slug)) {
        toast("心愿单已满 6 个, 请到心愿单页管理");
        return;
      }
      const isOpen = modal.getAttribute("data-open") === "true";
      if (isOpen) closeModal(); else openModal();
    });

    modal.querySelector('button[data-act="cancel"]').addEventListener("click", closeModal);
    modal.querySelector('button[data-act="ok"]').addEventListener("click", () => {
      const res = store.upsert({
        slug: meta.slug,
        title: meta.title,
        style: meta.style,
        category: meta.category,
        score: currentScore,
      });
      if (!res.ok && res.reason === "full") {
        toast("心愿单已满 6 个");
        return;
      }
      toast(res.updated ? "已更新星级" : "已加入心愿单");
      closeModal();
    });

    // 点 modal 外关闭
    document.addEventListener("click", (e) => {
      if (modal.getAttribute("data-open") !== "true") return;
      if (modal.contains(e.target) || fab.contains(e.target)) return;
      closeModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.getAttribute("data-open") === "true") closeModal();
    });

    // 订阅其他页修改 → 同步状态
    store.subscribe(() => {
      syncState();
    });
    return { fab, modal };
  }

  global.UIHelpers = {
    renderStars,
    mountWishlistChip,
    mountWishlistFab,
    toast,
    escapeHtml,
    getThemeLabel,
    STYLES,
  };
})(typeof window !== "undefined" ? window : globalThis);
