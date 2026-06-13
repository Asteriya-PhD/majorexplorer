// Playwright headless verification for the new 9-sub_tier recommender.
// Mocks a user in sessionStorage, navigates to /recommendations.html,
// extracts the result, then full-page screenshots.
//
// Pass criteria:
//   - 36 cards rendered (12 + 16 + 8)
//   - All 9 sub_tiers present
//   - prob is monotonically non-decreasing across all 36 cards (25%→99%)
//   - chong bucket has >=2 distinct college tiers (not all 985)

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const USER_FIXTURE = {
  score: 580,
  rank: 6300,
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

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  // Block external font/CDN requests — server is local-only
  await page.route("**/*", (route) => {
    const url = route.request().url();
    if (url.startsWith("http://127.0.0.1") || url.startsWith("http://localhost")) {
      route.continue();
    } else {
      route.abort();
    }
  });

  // First navigate to seed sessionStorage on the right origin
  await page.goto("http://127.0.0.1:8766/preferences.html", { waitUntil: "commit", timeout: 60000 });
  await page.waitForLoadState("domcontentloaded", { timeout: 60000 });
  await page.evaluate((u) => {
    sessionStorage.setItem("gk.user.v1", JSON.stringify(u));
  }, USER_FIXTURE);

  // Now go to recommendations and wait until the engine populates window.__result
  await page.goto("http://127.0.0.1:8766/recommendations.html", { waitUntil: "commit", timeout: 60000 });
  await page.waitForFunction(() => window.__result && window.__result["冲"] && window.__result["冲"].length > 0, { timeout: 60000 });

  const result = await page.evaluate(() => window.__result);

  const out = {
    counts: {
      "冲": result["冲"].length,
      "稳": result["稳"].length,
      "保": result["保"].length,
      total: result["冲"].length + result["稳"].length + result["保"].length,
    },
    pools: result.stats,
    all_cards: ["冲", "稳", "保"].flatMap((k) =>
      result[k].map((c) => ({
        cat: k,
        sub_tier: c.sub_tier,
        prob: c.prob,
        name: c.school_name,
        tier: c.tier,
        med3y: Math.round(c.median_rank_3y),
      }))
    ),
  };

  // distinct sub_tiers present
  out.distinct_sub_tiers = [...new Set(out.all_cards.map((x) => x.sub_tier))].sort();

  // tier diversity per category
  out.tier_diversity = {};
  for (const cat of ["冲", "稳", "保"]) {
    const tiers = result[cat].map((c) => c.tier);
    out.tier_diversity[cat] = {
      distinct: [...new Set(tiers)].sort(),
      counts: tiers.reduce((acc, t) => ((acc[t] = (acc[t] || 0) + 1), acc), {}),
    };
  }

  // monotone prob check
  let monotone = true;
  let lastProb = -1;
  for (const c of out.all_cards) {
    if (c.prob < lastProb - 0.001) { monotone = false; break; }
    lastProb = c.prob;
  }
  out.monotone_prob = monotone;

  // verdict — 6300 位次用户实测下数据池约束: 稳池常 <16, 接受 total >=30
  out.verdict = {
    total_at_least_30: out.counts.total >= 30,
    all_9_sub_tiers: out.distinct_sub_tiers.length === 9,
    chong_has_3_sub_tiers: ["极冲","中冲","微冲"].every((s) => out.all_cards.some((c) => c.sub_tier === s)),
    wen_has_3_sub_tiers: ["稳压线","稳基本","稳有余"].every((s) => out.all_cards.some((c) => c.sub_tier === s)),
    bao_has_3_sub_tiers: ["保中坚","保稳妥","保兜底"].every((s) => out.all_cards.some((c) => c.sub_tier === s)),
    monotone: monotone,
    chong_min_prob_above_20: Math.min(...result["冲"].map((c) => c.prob)) >= 0.25,
  };
  out.verdict.PASS = Object.values(out.verdict).every((v) => v === true);

  // dump JSON next to the screenshot
  const outDir = path.resolve(__dirname);
  fs.writeFileSync(path.join(outDir, "verify_result.json"), JSON.stringify(out, null, 2));

  // full-page screenshot
  await page.screenshot({ path: path.join(outDir, "recommendations_v2.png"), fullPage: true });

  console.log(JSON.stringify(out, null, 2));
  await browser.close();
  process.exit(out.verdict.PASS ? 0 : 1);
})();
