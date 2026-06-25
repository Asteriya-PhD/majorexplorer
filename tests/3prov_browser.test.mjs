// tests/3prov_browser.test.mjs — 浏览器端三省端到端验证
// 用 Playwright 真实浏览器, 验证 topbar dropdown 切换 + data 路由
// Run:  node tests/3prov_browser.test.mjs
// Prereq: python3 -m http.server 3000 --directory public/ &

import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import path from "node:path";

const BASE = "http://localhost:3000";
const SHOTS_DIR = path.resolve("test_results/3prov_shots");
mkdirSync(SHOTS_DIR, { recursive: true });

async function verifyProv(provKey, provDisplay) {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();

  // 1. 先打开首页 (此时 sessionStorage 是 hubei 默认)
  await page.goto(`${BASE}/`, { waitUntil: "domcontentloaded" });
  // 2. 设置省份
  await page.evaluate((p) => sessionStorage.setItem("gk.province.v1", p), provKey);
  // 3. Reload
  await page.goto(`${BASE}/`, { waitUntil: "domcontentloaded" });
  // 4. 等 topbar 渲染
  await page.waitForSelector(".topbar", { timeout: 5000 });
  // 5. 验证省份 dropdown 选中
  const selValue = await page.$eval("#topbar-prov-select", (el) => el.value);
  console.log(`[${provKey}] topbar select.value = ${selValue}`);
  if (selValue !== provKey) throw new Error(`select 应为 ${provKey}, 实为 ${selValue}`);

  // 6. 验证省份文字在 brand sub
  const subText = await page.$eval(".brand .sub", (el) => el.textContent.trim());
  console.log(`[${provKey}] brand.sub = "${subText}"`);
  if (!subText.includes(provDisplay)) {
    throw new Error(`brand.sub 应包含 ${provDisplay}, 实为 "${subText}"`);
  }

  // 7. 截图
  await page.screenshot({ path: `${SHOTS_DIR}/${provKey}_home.png`, fullPage: false });
  console.log(`[${provKey}] screenshot → ${SHOTS_DIR}/${provKey}_home.png`);

  // 8. 跳 preferences 看默认城市
  await page.goto(`${BASE}/preferences.html`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".city-item, .city-empty", { timeout: 5000 });
  const defaultCity = await page.evaluate(() => {
    try {
      const list = JSON.parse(sessionStorage.getItem("gk.user.v1") || "null");
      return list && list.cities && list.cities[0] ? list.cities[0].city : "(空 sessionStorage)";
    } catch (e) { return "(parse fail)"; }
  });
  console.log(`[${provKey}] sessionStorage cities[0] = ${defaultCity} (从 preferences 默认加载)`);

  await page.screenshot({ path: `${SHOTS_DIR}/${provKey}_preferences.png`, fullPage: false });

  await browser.close();
  return { provKey, subText, defaultCity };
}

async function main() {
  console.log("=== Playwright 三省浏览器端验证 ===\n");
  const results = [];
  for (const [key, display] of [["hubei", "湖北"], ["guangdong", "广东"], ["jiangsu", "江苏"]]) {
    try {
      const r = await verifyProv(key, display);
      results.push(r);
      console.log(`✓ ${display} 验证通过\n`);
    } catch (e) {
      console.error(`✗ ${display} 验证失败: ${e.message}\n`);
      throw e;
    }
  }
  console.log("=== 全部通过 ===");
  for (const r of results) {
    console.log(`  ${r.provKey}: brand="${r.subText}", city="${r.defaultCity}"`);
  }
}

main().catch((e) => { console.error(e); process.exit(1); });