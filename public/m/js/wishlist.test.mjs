// wishlist.test.mjs — Node 内置 test (>= 20 case)
//
// 覆盖 wishlist-store.js 关键路径 (mobile 心愿单):
//   1. migrate 旧 m.wishlist.v1 → gk.wishlist.v1
//   2. migrate 幂等
//   3. upsert 旧记录只 update score, 保留 rating
//   4. upsert 新建 + score/rating 都存
//   5. upsert tag/comment 都能存
//   6. MAX 限制 (6)
//   7. subscribe 跨组件同步
//   8. count/isReady
//
// Run:  node --test public/m/js/wishlist.test.mjs

import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// __dirname = public/m/js → 上溯 1 层到 public/m
const ROOT = path.resolve(__dirname, "../..");

// ── 加载 wishlist-store.js (IIFE → 取 window.WishlistStore) ──
function loadWishlistStore() {
  const code = fs.readFileSync(path.join(ROOT, "js/wishlist-store.js"), "utf-8");
  // 提供一个真发事件的 mock window (用 Map 存 handlers)
  const handlers = new Map();
  const win = {
    addEventListener: (e, fn) => {
      if (!handlers.has(e)) handlers.set(e, new Set());
      handlers.get(e).add(fn);
    },
    removeEventListener: (e, fn) => {
      handlers.get(e)?.delete(fn);
    },
    dispatchEvent: (evt) => {
      const set = handlers.get(evt.type);
      if (set) for (const fn of set) fn(evt);
      return true;
    },
  };
  const store = {};
  const mockLS = {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
    clear: () => { for (const k in store) delete store[k]; },
  };
  const fn = new Function("window", "localStorage", "globalThis", code + "\nreturn window.WishlistStore;");
  return {
    W: fn(win, mockLS, {}),
    store,
    window: win,
  };
}

function fresh() {
  return loadWishlistStore();
}

// ══════════════════════════════════════════════════════
// 1. migrate 旧 m.wishlist.v1 → gk.wishlist.v1
// ══════════════════════════════════════════════════════
test("1.1 migrate: 旧 string[] 数组 → 新 schema, rating 取默认 3", () => {
  const { W, store } = fresh();
  store["m.wishlist.v1"] = JSON.stringify(["cs", "law", "math"]);
  const r = W.migrate();
  assert.equal(r.migrated, 3);
  const items = W.all();
  assert.equal(items.length, 3);
  // 无 rating 字段 → 默认 3
  assert.equal(items.find(x => x.slug === "cs").rating, 3);
  assert.equal(items.find(x => x.slug === "cs").score, 3);
  // 旧 key 已删
  assert.equal(store["m.wishlist.v1"], undefined);
});

test("1.2 migrate: 旧 schema object[] → 保留 rating/tag/comment, score 同 rating", () => {
  const { W, store } = fresh();
  const old = [
    { slug: "cs", rating: 5, tag: "冲", comment: "想去" },
    { slug: "law", rating: 4, tag: "稳" },
    { slug: "math", rating: 2 },
  ];
  store["m.wishlist.v1"] = JSON.stringify(old);
  const r = W.migrate();
  assert.equal(r.migrated, 3);
  const items = W.all();
  const cs = items.find(x => x.slug === "cs");
  assert.equal(cs.score, 5);
  assert.equal(cs.rating, 5);
  assert.equal(cs.tag, "冲");
  assert.equal(cs.comment, "想去");
});

test("1.3 migrate 幂等: 二次调用 migrated=0", () => {
  const { W, store } = fresh();
  store["m.wishlist.v1"] = JSON.stringify(["cs", "law"]);
  W.migrate();
  const r = W.migrate();
  assert.equal(r.migrated, 0);
  assert.equal(r.source, null);
  assert.equal(W.count(), 2);
});

test("1.4 migrate: 容错, 旧 key 是垃圾 JSON 不崩", () => {
  const { W, store } = fresh();
  store["m.wishlist.v1"] = "not json{";
  const r = W.migrate();
  assert.equal(r.migrated, 0);
  // 旧 key 仍残留 (parse 失败时不该误删)
  assert.equal(store["m.wishlist.v1"], "not json{");
});

// ══════════════════════════════════════════════════════
// 2. upsert: 旧记录 update vs 新建
// ══════════════════════════════════════════════════════
test("2.1 upsert 新建: score/rating 都存", () => {
  const { W } = fresh();
  const r = W.upsert({ slug: "cs", score: 5, rating: 5, title: "计算机" });
  assert.equal(r.ok, true);
  assert.equal(r.added, true);
  const item = W.get("cs");
  assert.equal(item.score, 5);
  assert.equal(item.rating, 5);
  assert.equal(item.title, "计算机");
});

test("2.2 upsert 旧记录: 只 update score, 保留 rating", () => {
  const { W } = fresh();
  W.upsert({ slug: "cs", score: 3, rating: 4 });
  // 改 score, 不传 rating → rating 保留 4
  W.upsert({ slug: "cs", score: 5 });
  const item = W.get("cs");
  assert.equal(item.score, 5);
  assert.equal(item.rating, 4, "rating 保留");
});

test("2.3 upsert 旧记录: tag/comment 都能存", () => {
  const { W } = fresh();
  W.upsert({ slug: "cs", score: 3 });
  W.upsert({ slug: "cs", tag: "冲", comment: "冲一冲" });
  const item = W.get("cs");
  assert.equal(item.tag, "冲");
  assert.equal(item.comment, "冲一冲");
});

test("2.4 upsert MAX=6: 第 7 个返 full, 列表保持 6", () => {
  const { W } = fresh();
  for (let i = 1; i <= 6; i++) W.upsert({ slug: `m${i}`, score: 3 });
  const r = W.upsert({ slug: "m7", score: 3 });
  assert.equal(r.ok, false);
  assert.equal(r.reason, "full");
  assert.equal(W.count(), 6);
});

// ══════════════════════════════════════════════════════
// 3. count / isReady / isFull
// ══════════════════════════════════════════════════════
test("3.1 count: 0/3/4/6 边界值", () => {
  const { W } = fresh();
  assert.equal(W.count(), 0);
  assert.equal(W.isReady(), false);
  W.upsert({ slug: "a", score: 3 });
  W.upsert({ slug: "b", score: 3 });
  W.upsert({ slug: "c", score: 3 });
  assert.equal(W.count(), 3);
  assert.equal(W.isReady(), false);
  W.upsert({ slug: "d", score: 3 });
  assert.equal(W.count(), 4);
  assert.equal(W.isReady(), true, "4 个 isReady");
  assert.equal(W.isFull(), false);
  for (let i = 5; i <= 6; i++) W.upsert({ slug: `x${i}`, score: 3 });
  assert.equal(W.count(), 6);
  assert.equal(W.isFull(), true);
});

// ══════════════════════════════════════════════════════
// 4. subscribe 跨组件同步
// ══════════════════════════════════════════════════════
test("4.1 subscribe: upsert 后 handler 立刻收到新 items", () => {
  const { W } = fresh();
  const calls = [];
  W.subscribe(items => calls.push(items.length));
  W.upsert({ slug: "a", score: 3 });
  W.upsert({ slug: "b", score: 3 });
  W.remove("a");
  // 首次同步 + 每次变更触发: 0 → 1 → 2 → 1
  assert.deepEqual(calls, [0, 1, 2, 1]);
});

test("4.2 subscribe: unsub 后不再触发", () => {
  const { W } = fresh();
  const calls = [];
  const unsub = W.subscribe(items => calls.push(items.length));
  W.upsert({ slug: "a", score: 3 });
  unsub();
  W.upsert({ slug: "b", score: 3 });
  assert.deepEqual(calls, [0, 1], "unsub 后不再触发");
});

// ══════════════════════════════════════════════════════
// 5. remove / setScore / clear
// ══════════════════════════════════════════════════════
test("5.1 remove: 存在的删, 不存在的返 false", () => {
  const { W } = fresh();
  W.upsert({ slug: "a", score: 3 });
  assert.equal(W.remove("a"), true);
  assert.equal(W.remove("a"), false);
  assert.equal(W.count(), 0);
});

test("5.2 setScore: 只改 score (clamp 1-5)", () => {
  const { W } = fresh();
  W.upsert({ slug: "a", score: 3, rating: 4 });
  W.setScore("a", 7);
  assert.equal(W.get("a").score, 5, "clamp 5");
  W.setScore("a", -1);
  assert.equal(W.get("a").score, 1, "clamp 1");
});

test("5.3 clear: 全清, count=0", () => {
  const { W } = fresh();
  W.upsert({ slug: "a", score: 3 });
  W.upsert({ slug: "b", score: 3 });
  W.clear();
  assert.equal(W.count(), 0);
  assert.equal(W.isReady(), false);
});

// ══════════════════════════════════════════════════════
// 6. toInterests
// ══════════════════════════════════════════════════════
test("6.1 toInterests: 导出 recommender 期望格式", () => {
  const { W } = fresh();
  W.upsert({ slug: "cs", score: 5, rating: 5, title: "计算机", style: "cs" });
  W.upsert({ slug: "law", score: 4, rating: 4, title: "法学", style: "law" });
  const interests = W.toInterests();
  assert.equal(interests.length, 2);
  assert.equal(interests[0].slug, "cs");
  assert.equal(interests[0].major, "计算机");
  assert.equal(interests[0].score, 5);
  assert.equal(interests[0].style, "cs");
});
