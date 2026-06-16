// loader.test.mjs — Node 内置 test (>= 20 case)
//
// 覆盖 mobile/loader.js (M.init / M.styleColor / M.ghost):
//   1. styleColor: 读 manifest.theme_color.primary
//   2. styleColor: 未知 style 兜底 #4A4564
//   3. init: 加载 manifest + hierarchy + strategy
//   4. init 幂等: 二次调用不重新 fetch
//   5. hierarchy 兼容: disciplines / 门类 / menjia 多 key
//   6. ghost: title 截首字
//
// Run:  node --test public/m/js/loader.test.mjs

import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// __dirname = public/m/js → 上溯 1 层到 public/m
const ROOT = path.resolve(__dirname, "../..");

// ── 加载 loader.js (IIFE → 取 window.MobileData) ──
function loadLoader(opts = {}) {
  const code = fs.readFileSync(path.join(ROOT, "m/js/loader.js"), "utf-8");
  const mockWindow = { addEventListener: () => {} };
  // 默认 fake fetch 行为: 返回指定 JSON
  const fetchMap = opts.fetchMap || {
    "/data/manifest.json": {
      majors: [
        { slug: "cs", title: "计算机", style: "cs", theme_color: { primary: "#1E5E72" } },
        { slug: "law", title: "法学", style: "law", theme_color: { primary: "#3A3A3A" } },
      ],
    },
    "/data/discipline_hierarchy.json": { disciplines: [{ code: "08", name: "工学", sub: [] }] },
    "/data/strategy_industries.json": { industries: [] },
  };
  const mockFetch = async (url) => {
    if (url in fetchMap) {
      return { ok: true, json: async () => fetchMap[url] };
    }
    return { ok: false, json: async () => ({}) };
  };
  const fn = new Function("window", "fetch", "document", code);
  fn(mockWindow, mockFetch, { addEventListener: () => {} });
  return mockWindow.MobileData;
}

// ══════════════════════════════════════════════════════
// 1. styleColor
// ══════════════════════════════════════════════════════
test("1.1 styleColor: 读 manifest.theme_color.primary", async () => {
  const M = loadLoader();
  await M.init();
  assert.equal(M.styleColor("cs"), "#1E5E72");
  assert.equal(M.styleColor("law"), "#3A3A3A");
});

test("1.2 styleColor: 未知 style 兜底 #4A4564", async () => {
  const M = loadLoader();
  await M.init();
  assert.equal(M.styleColor("nonexistent"), "#4A4564");
});

// ══════════════════════════════════════════════════════
// 2. init 加载 manifest / hierarchy / strategy
// ══════════════════════════════════════════════════════
test("2.1 init: 加载 manifest + hierarchy + strategy", async () => {
  const M = loadLoader();
  await M.init();
  assert.ok(M.manifest, "manifest loaded");
  assert.equal(M.manifest.majors.length, 2);
  assert.ok(M.hierarchy, "hierarchy loaded");
  assert.equal(M.hierarchy.disciplines[0].name, "工学");
  assert.ok(M.strategy, "strategy loaded");
});

test("2.2 init 幂等: 二次调用不重新 fetch (用 ready 缓存)", async () => {
  let fetchCount = 0;
  const code = fs.readFileSync(path.join(ROOT, "m/js/loader.js"), "utf-8");
  const mockWindow = { addEventListener: () => {} };
  const mockFetch = async (url) => {
    fetchCount++;
    return { ok: true, json: async () => ({ majors: [] }) };
  };
  const fn = new Function("window", "fetch", "document", code);
  fn(mockWindow, mockFetch, { addEventListener: () => {} });
  const M = mockWindow.MobileData;
  await M.init();
  await M.init();
  await M.init();
  // 第一次 init 触发 3 个 fetch; 后续 ready 命中 → 总共 3 次
  assert.equal(fetchCount, 3, "幂等, 二次调用不重新 fetch");
});

test("2.3 init: hierarchy/strategy fetch 抛错时 catch 走 null", async () => {
  const code = fs.readFileSync(path.join(ROOT, "m/js/loader.js"), "utf-8");
  const mockWindow = { addEventListener: () => {} };
  const mockFetch = async (url) => {
    if (url.includes("manifest.json")) return { ok: true, json: async () => ({ majors: [] }) };
    throw new Error("404");
  };
  const fn = new Function("window", "fetch", "document", code);
  fn(mockWindow, mockFetch, { addEventListener: () => {} });
  const M = mockWindow.MobileData;
  await M.init();
  assert.equal(M.manifest.majors.length, 0);
  assert.equal(M.hierarchy, null, "catch 走 null");
  assert.equal(M.strategy, null, "catch 走 null");
});

// ══════════════════════════════════════════════════════
// 3. hierarchy 兼容多种 key 命名
// ══════════════════════════════════════════════════════
test("3.1 hierarchy 兼容 disciplines[]", async () => {
  const M = loadLoader({
    fetchMap: {
      "/data/manifest.json": { majors: [] },
      "/data/discipline_hierarchy.json": {
        disciplines: [{ code: "01", name: "哲学", sub: [{ code: "0101", name: "哲学类", majors: ["哲学", "逻辑学"] }] }],
      },
      "/data/strategy_industries.json": {},
    },
  });
  await M.init();
  assert.equal(M.hierarchy.disciplines[0].name, "哲学");
  assert.equal(M.hierarchy.disciplines[0].sub[0].majors.length, 2);
});

test("3.2 hierarchy 兼容 门类→sub_classes 旧格式", async () => {
  const M = loadLoader({
    fetchMap: {
      "/data/manifest.json": { majors: [] },
      "/data/discipline_hierarchy.json": {
        门类: {
          "04": {
            name: "教育学",
            sub_classes: { "0403": { name: "心理学类", majors: ["心理学", "应用心理学"] } },
          },
        },
      },
      "/data/strategy_industries.json": {},
    },
  });
  await M.init();
  // loader 应把 门类 转换为 disciplines
  assert.equal(M.hierarchy.disciplines.length, 1);
  assert.equal(M.hierarchy.disciplines[0].name, "教育学");
  assert.equal(M.hierarchy.disciplines[0].sub[0].name, "心理学类");
  assert.equal(M.hierarchy.disciplines[0].sub[0].majors.length, 2);
});

// ══════════════════════════════════════════════════════
// 4. manifestBySlug
// ══════════════════════════════════════════════════════
test("4.1 manifestBySlug: slug → major", async () => {
  const M = loadLoader();
  await M.init();
  assert.equal(M.manifestBySlug["cs"].title, "计算机");
  assert.equal(M.manifestBySlug["law"].style, "law");
});

test("4.2 manifestBy[discipline]: 门类分组", async () => {
  const M = loadLoader({
    fetchMap: {
      "/data/manifest.json": {
        majors: [
          { slug: "cs1", title: "计1", style: "cs", discipline: "08" },
          { slug: "cs2", title: "计2", style: "cs", discipline: "08" },
          { slug: "law1", title: "法1", style: "law", discipline: "03" },
        ],
      },
      "/data/discipline_hierarchy.json": { disciplines: [] },
      "/data/strategy_industries.json": {},
    },
  });
  await M.init();
  assert.equal(M.manifestBy["08"].length, 2);
  assert.equal(M.manifestBy["03"].length, 1);
});

// ══════════════════════════════════════════════════════
// 5. ghost
// ══════════════════════════════════════════════════════
test("5.1 ghost: title 截首字, 缺省 ?", async () => {
  const M = loadLoader();
  assert.equal(M.ghost("计算机"), "计");
  assert.equal(M.ghost(""), "?");
  assert.equal(M.ghost(null), "?");
});
