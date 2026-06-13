// Batch verify - 跑 6 个代表性分数 fixture, 输出对比表 + 4 张关键截图.
//
// 代表性分数 (湖北物理类 2025 一本线=426):
//   A. 480 分 / 104k 位次 — 一本线偏上, 公办本科主力
//   B. 520 分 / 69k 位次   — 中段公本 + 弱 211
//   C. 560 分 / 37k 位次   — 211 入场
//   D. 600 分 / 14k 位次   — 中端 985 / 强 211
//   E. 635 分 / ~4k 位次    — 强 985
//   F. 660 分 / 885 位次   — C9 / 顶尖

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const FIXTURES = [
  { id: "A_480", label: "A · 480 分 (一本线偏上)",  score: 480, rank: 104222 },
  { id: "B_520", label: "B · 520 分 (中段)",        score: 520, rank: 69316  },
  { id: "C_560", label: "C · 560 分 (211 入场)",    score: 560, rank: 36984  },
  { id: "D_600", label: "D · 600 分 (中端 985)",    score: 600, rank: 14274  },
  { id: "G_620", label: "G · 620 分 (用户原始)",    score: 620, rank: 7436   },
  { id: "E_635", label: "E · 635 分 (强 985)",      score: 635, rank: 4000   },
  { id: "F_660", label: "F · 660 分 (C9/顶尖)",     score: 660, rank: 885    },
];

const COMMON = {
  type: "物理类",
  xuanke: ["物理", "化学", "生物"],
  interests: [
    { major: "计算机", score: 5 },
    { major: "人工智能", score: 4 },
    { major: "软件", score: 3 },
  ],
  cities: [
    { city: "武汉", score: 5 },
    { city: "上海", score: 4 },
    { city: "北京", score: 3 },
  ],
  mode: "均衡",
};

const SUB_ORDER = ["极冲","中冲","微冲","稳压线","稳基本","稳有余","保中坚","保稳妥","保兜底"];
const TIER_ORDER = ["C9","985","211","双一流","公办本科","民办/独立",""];

function pad(s, n) {
  s = String(s);
  // CJK width=2, ascii=1
  let w = 0; for (const ch of s) w += (ch.charCodeAt(0) > 127 ? 2 : 1);
  return s + " ".repeat(Math.max(0, n - w));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  await page.route("**/*", (route) => {
    const url = route.request().url();
    if (url.startsWith("http://127.0.0.1") || url.startsWith("http://localhost")) route.continue();
    else route.abort();
  });

  // Seed sessionStorage once via preferences page
  await page.goto("http://127.0.0.1:8766/preferences.html", { waitUntil: "commit", timeout: 60000 });
  await page.waitForLoadState("domcontentloaded", { timeout: 60000 });

  const allResults = [];
  const outDir = path.resolve(__dirname);

  for (const fix of FIXTURES) {
    const user = Object.assign({}, COMMON, { score: fix.score, rank: fix.rank });
    await page.evaluate((u) => { sessionStorage.setItem("gk.user.v1", JSON.stringify(u)); }, user);

    await page.goto("http://127.0.0.1:8766/recommendations.html", { waitUntil: "commit", timeout: 60000 });
    await page.waitForFunction(
      () => window.__result && (window.__result["冲"].length > 0 || window.__result["保"].length > 0),
      { timeout: 60000 }
    );

    const result = await page.evaluate(() => window.__result);
    const all = ["冲","稳","保"].flatMap((k) => result[k].map((c) => Object.assign({ cat: k }, c)));

    // sub_tier counts
    const subCnt = {};
    SUB_ORDER.forEach((s) => subCnt[s] = 0);
    all.forEach((c) => { if (subCnt[c.sub_tier] !== undefined) subCnt[c.sub_tier]++; });

    // tier counts per cat
    const tierByCat = { "冲": {}, "稳": {}, "保": {} };
    all.forEach((c) => {
      const t = c.tier || "—";
      tierByCat[c.cat][t] = (tierByCat[c.cat][t] || 0) + 1;
    });

    // probs distinct
    const probs = [...new Set(all.map((c) => c.prob))].sort((a,b) => a - b);

    // monotone
    let monotone = true, last = -1;
    for (const c of all) { if (c.prob < last - 0.001) { monotone = false; break; } last = c.prob; }

    // top 3 chong examples
    const topChong = (result["冲"].slice(0, 3)).map((c) => `${c.school_name}(${c.tier},${c.sub_tier},${Math.round(c.prob*100)}%)`);
    // top 3 bao examples
    const topBao = (result["保"].slice(0, 3)).map((c) => `${c.school_name}(${c.tier},${c.sub_tier},${Math.round(c.prob*100)}%)`);

    const summary = {
      id: fix.id,
      label: fix.label,
      score: fix.score,
      rank: fix.rank,
      counts: {
        "冲": result["冲"].length,
        "稳": result["稳"].length,
        "保": result["保"].length,
        total: all.length,
      },
      pools: result.stats,
      sub_counts: subCnt,
      tier_by_cat: tierByCat,
      probs_used: probs.map((p) => Math.round(p*100) + "%"),
      monotone: monotone,
      chong_min_prob: result["冲"].length ? Math.min(...result["冲"].map((c) => c.prob)) : null,
      sample_chong_top3: topChong,
      sample_bao_top3: topBao,
    };
    allResults.push(summary);

    // 截图所有 6 个 fixture
    await page.screenshot({
      path: path.join(outDir, `rec_${fix.id}.png`),
      fullPage: true,
    });

    console.log(`✓ ${fix.label}: 总 ${summary.counts.total}, 冲 ${summary.counts.冲} / 稳 ${summary.counts.稳} / 保 ${summary.counts.保}`);
  }

  // 写汇总 JSON
  fs.writeFileSync(path.join(outDir, "batch_verify.json"), JSON.stringify(allResults, null, 2));

  // 打印对比表
  console.log("\n" + "=".repeat(110));
  console.log("BATCH 验证报告 — 6 个代表性分数");
  console.log("=".repeat(110));

  // 表 1: 总数 & sub_tier 分布
  console.log("\n[表 1] 9 档分布 + 总数");
  console.log(pad("Fixture", 26) + pad("总", 5) + pad("冲", 5) + pad("稳", 5) + pad("保", 5) +
    SUB_ORDER.map(s => pad(s, 7)).join(""));
  console.log("-".repeat(110));
  for (const r of allResults) {
    let line = pad(r.label, 26) + pad(r.counts.total, 5) + pad(r.counts.冲, 5) + pad(r.counts.稳, 5) + pad(r.counts.保, 5);
    for (const s of SUB_ORDER) line += pad(r.sub_counts[s], 7);
    console.log(line);
  }

  // 表 2: 跨 tier 多样性 (冲档)
  console.log("\n[表 2] 冲档 tier 分布 (用户最在意, 不该全 985)");
  console.log(pad("Fixture", 26) + TIER_ORDER.map(t => pad(t || "—", 12)).join(""));
  console.log("-".repeat(110));
  for (const r of allResults) {
    let line = pad(r.label, 26);
    for (const t of TIER_ORDER) line += pad(r.tier_by_cat["冲"][t] || "·", 12);
    console.log(line);
  }

  // 表 3: 保档 tier 分布
  console.log("\n[表 3] 保档 tier 分布");
  console.log(pad("Fixture", 26) + TIER_ORDER.map(t => pad(t || "—", 12)).join(""));
  console.log("-".repeat(110));
  for (const r of allResults) {
    let line = pad(r.label, 26);
    for (const t of TIER_ORDER) line += pad(r.tier_by_cat["保"][t] || "·", 12);
    console.log(line);
  }

  // 表 4: 冲档样例
  console.log("\n[表 4] 冲档 top 3 实例 (school, tier, sub_tier, prob)");
  for (const r of allResults) {
    console.log(`  ${r.label}`);
    r.sample_chong_top3.forEach((s) => console.log(`    • ${s}`));
  }

  await browser.close();
  console.log("\n截图已存 test_results/rec_*.png, 汇总 JSON 在 test_results/batch_verify.json");
})();
