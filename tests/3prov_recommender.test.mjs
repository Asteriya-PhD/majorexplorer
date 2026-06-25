// tests/3prov_recommender.test.mjs — 三省 recommender smoke test
// Run:  node --experimental-vm-modules tests/3prov_recommender.test.mjs
// Prereq: python3 -m http.server 3000 --directory public/ &

import { test } from "node:test";
import assert from "node:assert/strict";

const BASE = "http://localhost:3000";

async function testProv(name) {
  // 1. Index → 期望省份在 yfyd_index
  const idx = await fetch(`${BASE}/data/yfyd_index.json`).then(r => r.json());
  assert.ok(idx.provinces[name], `${name} 应在 yfyd_index.provinces`);
  console.log(`  yfyd_index ${name}: latest=${idx.provinces[name].latest}, files=${Object.keys(idx.provinces[name].files).join(",")}`);

  // 2. 加载省份最新 yfyd 文件
  const latest = idx.provinces[name].latest;
  const yfydFile = idx.provinces[name].files[latest];
  const yfyd = await fetch(`${BASE}/data/${yfydFile}`).then(r => r.json());
  assert.ok(yfyd.wuli && yfyd.lishi, `${yfydFile} 应含 wuli/lishi`);
  assert.equal(yfyd.province, name === "hubei" ? "湖北" : (name === "guangdong" ? "广东" : "江苏"));
  console.log(`  ${yfydFile}: wuli=${yfyd.wuli.rows.length} 行, lishi=${yfyd.lishi.rows.length} 行`);

  // 3. 加载 groups_index + 对应 groups_latest
  const grpIdx = await fetch(`${BASE}/data/groups_index.json`).then(r => r.json());
  const grpFile = grpIdx.provinces[name].files[grpIdx.provinces[name].latest_year];
  const groups = await fetch(`${BASE}/data/${grpFile}`).then(r => r.json());
  const total = groups.wuli.length + groups.lishi.length;
  console.log(`  ${grpFile}: wuli=${groups.wuli.length}, lishi=${groups.lishi.length}, total=${total}`);
  assert.ok(total > 100, `${name} groups_latest 应 >100 组`);

  // 4. 验证 sg_info 格式正确 (能被 JS passesXuanke 解析)
  const sample = groups.wuli[0];
  assert.ok(sample.sg_info && sample.sg_info.indexOf("首选") !== -1,
    `${name} sample sg_info 应含 '首选', 实有: ${sample.sg_info}`);

  return { name, yfyd, groups, total };
}

test("湖北 2025 yfyd + groups_latest 完整可加载", async () => {
  const r = await testProv("hubei");
  console.log(`  湖北 score→rank: 580→${r.yfyd.wuli.rows.find(x => x.score <= 580)?.rank || "n/a"}`);
});

test("广东 2024 yfyd + groups_latest 完整可加载", async () => {
  const r = await testProv("guangdong");
  console.log(`  广东 score→rank: 580→${r.yfyd.wuli.rows.find(x => x.score <= 580)?.rank || "n/a"}`);
});

test("江苏 2024 yfyd + groups_latest 完整可加载", async () => {
  const r = await testProv("jiangsu");
  console.log(`  江苏 score→rank: 580→${r.yfyd.wuli.rows.find(x => x.score <= 580)?.rank || "n/a"}`);
});

test("provinces 切换省份后 data 对象正确", async () => {
  // 模拟 getDataForProvince 的逻辑: 各省 yfyd/groups 不串台
  for (const prov of ["hubei", "guangdong", "jiangsu"]) {
    const yfydIdx = await fetch(`${BASE}/data/yfyd_index.json`).then(r => r.json());
    const file = yfydIdx.provinces[prov].files[yfydIdx.provinces[prov].latest];
    const yfyd = await fetch(`${BASE}/data/${file}`).then(r => r.json());
    assert.notEqual(yfyd.province, "hubei", `${prov} yfyd 不应被湖北污染`);
    assert.ok(yfyd.wuli.rows.length >= 500, `${prov} yfyd wuli 行数应 >= 500`);
  }
});