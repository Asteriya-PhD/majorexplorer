// recommender.test.mjs — Node 内置 test (>= 20 case)
//
// 覆盖:
//   1. 同义词命中 (用户"人工智能" → 校"智能科学与技术")
//   2. 双向倒查 (用户输入是 synonyms value)
//   3. all_majors → top_specials fallback
//   4. 软科 bonus (+0.5/+0.3/+0.1)
//   5. 空 / null / 不存在 schoolId
//   6. 多 interest 取 max
//   7. 中文括号清洗后命中
//   8. score cap (>5 → min)
//
// Run:  node --test public/js/recommender.test.mjs

import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");

// ── 加载 recommender.js (IIFE → 取 window.Recommender) ──
function loadRecommender() {
  const code = fs.readFileSync(path.join(ROOT, "public/js/recommender.js"), "utf-8");
  const fn = new Function("window", code + "\nreturn window.Recommender;");
  return fn({});
}

// ── 加载测试数据 (一次, 所有 test 共享) ──
const sam = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/school_all_majors.json"), "utf-8"));
const syn = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/major_synonyms.json"), "utf-8"));
const collegesArr = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/colleges.json"), "utf-8"));
// Step 3.4 v1: 数据已重 key 为 chsi_edu_id, 测试 helper 把 school_id 翻译成 edu_id
const sidToEid = {};
for (const c of collegesArr) {
  if (c.school_id != null) sidToEid[String(c.school_id)] = c.chsi_edu_id ? String(c.chsi_edu_id) : `sch_${c.school_id}`;
}
const Rec = loadRecommender();

// ── helper ──
// mm() 自动做 school_id → edu_id 翻译, 调用方仍可用老式 school_id (如 420)
const mm = (sid, interests) => {
  const eid = sidToEid[String(sid)] || String(sid);
  return Rec.majorMatch(eid, interests, null, sam, syn);
};

// ══════════════════════════════════════════════════════
// 1. 同义词命中 (用户 keyword → 同义词集 → 命中校 major)
// ══════════════════════════════════════════════════════
test("1.1 精确命中: 用户 '人工智能' 命中华中师大人工智能", () => {
  // 华中师大 all_majors 含 "人工智能"
  const m = mm(420, [{ major: "人工智能", score: 4 }]);
  assert.equal(m, 4.2, "精确匹配 + all_majors 0.2 bonus = 4.2");
});

test("1.2 同义词展开: 用户 '计算机' 命中华中师大数字媒体技术 (同义集中)", () => {
  // 计算机类目含 "数字媒体技术", 华中师大 all_majors 含此
  const m = mm(420, [{ major: "计算机", score: 5 }]);
  // userScore=5, +0.2 = 5.2, cap 5.0
  assert.equal(m, 5.0, "5+0.2 capped at 5.0");
});

test("1.3 同义词展开: 用户 '计算机' 命中武汉理工'计算机类' (大类兼容)", () => {
  const m = mm(128, [{ major: "计算机", score: 3 }]);
  assert.equal(m, 3.2, "大类 +0.2 bonus");
});

// ══════════════════════════════════════════════════════
// 2. 双向倒查 (用户输入是 synonyms value)
// ══════════════════════════════════════════════════════
test("2.1 反向: 用户 '人工智能' 通过 反向 命中 计算机 类目 (用户输入在 value)", () => {
  // "人工智能" 在 synonyms["计算机"] value 里
  // 同时 also 精确命中华中师大人工智能
  const m = mm(420, [{ major: "人工智能", score: 4 }]);
  assert.equal(m, 4.2, "华中师大有 人工智能 精确命中");
});

test("2.2 反向: 用户 '金融学' 反向命中 经济金融 类目 (用户输入是 value)", () => {
  // "金融学" 在 synonyms["经济金融"] value 里
  // 上海大学 all_majors 含 "金融学"
  const m = mm(76, [{ major: "金融学", score: 5 }]);
  assert.equal(m, 5.0, "精确匹配 5+0.2 capped at 5.0");
});

test("2.3 前缀: 用户 '金融' (2 字) 是 '金融学' 前缀 → 反向展开", () => {
  const m = mm(76, [{ major: "金融", score: 5 }]);
  // 金融学精确命中 → 5+0.2=5.2 capped 5.0
  assert.equal(m, 5.0, "prefix 反向命中, capped 5.0");
});

// ══════════════════════════════════════════════════════
// 3. all_majors → top_specials fallback
// ══════════════════════════════════════════════════════
test("3.1 880 校无 all_majors 数据: 不命中 (top_specials 也无)", () => {
  // 999 不存在, 无数据
  const m = mm(999, [{ major: "计算机", score: 5 }]);
  assert.equal(m, 0);
});

test("3.2 128 校 all_majors 有, 但用户兴趣不在校 majors → 返 0", () => {
  // 上海大学 16 majors, 无计算机
  const m = mm(76, [{ major: "计算机", score: 5 }]);
  assert.equal(m, 0, "上海大学 all_majors 无计算机, top_specs 也无 (本次传 null)");
});

test("3.3 短关键词 '管理' (2 字) 不命中 (无前缀, 无子串)", () => {
  // "管理" 是 2 字 < 3, 不走子串 rule; 也不前缀任何 工商管理 major
  // 上海大学 工商管理/信管 都不以 "管理" 开头
  const m = mm(76, [{ major: "管理", score: 4 }]);
  assert.equal(m, 0, "管理 alone too short, 不匹配");
});

// ══════════════════════════════════════════════════════
// 4. 软科 bonus (+0.5/+0.3/+0.1) — 传 specialties 时走 fallback
// ══════════════════════════════════════════════════════
test("4.1 软科 A+ bonus: 命中 top_specials + 0.5", () => {
  // 构造 minimal specialties
  const specs = { "76": { top_specials: [{ name: "计算机科学与技术", xueke_rank_score: "A+" }] } };
  const m = Rec.majorMatch(76, [{ major: "计算机", score: 3 }], specs, sam, syn);
  // 上海大学无 all_majors 计算机 → top_specials 命中
  // userScore=3, +0.5 (A+) = 3.5
  assert.equal(m, 3.5, "A+ bonus 0.5");
});

test("4.2 软科 A bonus: +0.3 (可覆盖 all_majors 0.2)", () => {
  const specs = { "76": { top_specials: [{ name: "金融学", ruanke_level: "A" }] } };
  const m = Rec.majorMatch(76, [{ major: "金融", score: 3 }], specs, sam, syn);
  // all_majors 命中 3.2; top_specs 命中 3+0.3=3.3 → best=3.3
  // 设计: top_specs bonus 软科 A=0.3 > all_majors 0.2, 故 top_specs 胜出
  assert.equal(m, 3.3, "A bonus 0.3 覆盖 all_majors 0.2");
});

test("4.3 软科 B+ bonus: +0.1 (主源不命中时)", () => {
  // 选不存在的校 100, all_majors 里有
  // 改用 999 不存在 → 走 top_specials
  const specs = { "999": { top_specials: [{ name: "哲学", xueke_rank_score: "B+" }] } };
  const m = Rec.majorMatch(999, [{ major: "哲学", score: 3 }], specs, sam, syn);
  // 校 999 无 all_majors → 走 top_specials 命中
  // userScore=3, +0.1 (B+) = 3.1
  assert.equal(m, 3.1, "B+ bonus 0.1");
});

// ══════════════════════════════════════════════════════
// 5. 空 / null / 不存在 schoolId
// ══════════════════════════════════════════════════════
test("5.1 空 interests → 0", () => {
  assert.equal(mm(420, []), 0);
  assert.equal(mm(420, null), 0);
  assert.equal(mm(420, undefined), 0);
});

test("5.2 不存在 schoolId → 0 (all_majors 无 + top_specs null)", () => {
  assert.equal(mm(99999, [{ major: "计算机", score: 5 }]), 0);
  assert.equal(mm("abc", [{ major: "计算机", score: 5 }]), 0);
});

test("5.3 null allMajorsById (880 校场景)", () => {
  // 不传 allMajorsById, 应该不崩
  const m = Rec.majorMatch(76, [{ major: "金融", score: 5 }], null, null, syn);
  // 校 76 all_majors 不在, sam=null → schoolAllMajors=[]
  // topSpecs null → []
  // 全部 0
  assert.equal(m, 0);
});

test("5.4 null synonymMap (老调用方兼容)", () => {
  // 校 420 有 人工智能, 不传 synonyms 时只 exact match (Step 3.4 v1: 用 edu_id)
  const m = Rec.majorMatch(sidToEid["420"], [{ major: "人工智能", score: 4 }], null, sam, null);
  // expanded = {"人工智能"} only, no expand → exact match in 华中师大 all_majors
  // userScore=4, +0.2 = 4.2
  assert.equal(m, 4.2, "null syn 但 exact 仍命中");
});

// ══════════════════════════════════════════════════════
// 6. 多 interest 取 max
// ══════════════════════════════════════════════════════
test("6.1 多 interest 取最强: 金融+经济 都命中 取 5 (capped)", () => {
  const m = mm(76, [
    { major: "经济", score: 4 },  // 经济学类命中 4.2
    { major: "金融", score: 5 },  // 金融学命中 5+0.2 capped 5.0
  ]);
  assert.equal(m, 5.0, "max");
});

test("6.2 多 interest 一个命中一个不命中, 返命中那个", () => {
  const m = mm(420, [
    { major: "口腔医学", score: 5 },  // 校无
    { major: "计算机", score: 3 },     // 命中
  ]);
  assert.equal(m, 3.2, "命中那个");
});

// ══════════════════════════════════════════════════════
// 7. 中文括号/后缀兼容
// ══════════════════════════════════════════════════════
test("7.1 大类兼容: '计算机类' 命中 '计算机' (e + '类')", () => {
  // 武汉理工 all_majors 含 "计算机类"
  // 用户输入 "计算机", 大类兼容应命中
  const m = mm(128, [{ major: "计算机", score: 3 }]);
  assert.equal(m, 3.2);
});

test("7.2 反向兼容: 用户输入大类 '计算机类' 命中 (prefix rule)", () => {
  // "计算机类" 是 "计算机类" 自身的 prefix (rule 3) → expand 计算机类目
  // 数字媒体技术 是 计算机 类目 value → exact match in expanded
  // 华中师大 all_majors 含 "数字媒体技术" → exact → +0.2
  const m = mm(420, [{ major: "计算机类", score: 4 }]);
  assert.equal(m, 4.2, "prefix rule 让 '计算机类' 展开为整个 计算机 类目");
});

// ══════════════════════════════════════════════════════
// 8. score cap (>5 → min)
// ══════════════════════════════════════════════════════
test("8.1 cap: userScore=5 + 0.2 → 5.0 (不超 5)", () => {
  const m = mm(420, [{ major: "人工智能", score: 5 }]);
  assert.equal(m, 5.0);
});

test("8.2 cap: userScore=4 + A+ bonus 0.5 = 4.5, 不超", () => {
  const specs = { "999": { top_specials: [{ name: "哲学", xueke_rank_score: "A+" }] } };
  const m = Rec.majorMatch(999, [{ major: "哲学", score: 4 }], specs, sam, syn);
  assert.equal(m, 4.5, "4 + 0.5 = 4.5");
});

test("8.3 cap: userScore=5 + A+ bonus 0.5 = 5.5, capped 5.0", () => {
  const specs = { "999": { top_specials: [{ name: "哲学", xueke_rank_score: "A+" }] } };
  const m = Rec.majorMatch(999, [{ major: "哲学", score: 5 }], specs, sam, syn);
  assert.equal(m, 5.0, "5.5 capped 5.0");
});

// ══════════════════════════════════════════════════════
// 9. 防误报 (regression tests — 之前发现过的 bug)
// ══════════════════════════════════════════════════════

test("9.0 REGRESSION 兜底反逻辑: 中山大学 985 不应被早期 maxRank*1.2 误判保兜底", () => {
  // 实战 user 场景: user rank 16067, 中山大学 median 7356, max 8645 (2022 worst)
  // 旧 bug: userRank > maxRank * 1.2 (16067 > 10374) 误判为 保兜底 99%
  // 正确: diff = (16067-7356)/7356 = 1.18 → 强冲 (冲档)
  const r = Rec.computeChance(16067, 7356, 8645);
  assert.deepEqual(r, ["冲", 0.25, "强冲"], "985 校不应被 maxRank*1.2 误判兜底");
});

test("9.0b 兜底正确路径: user 位次比 median 还好 65% 以上 (diff <= -0.65)", () => {
  // user rank 2000, median 7356 → diff = -0.73 → 兜底
  const r = Rec.computeChance(2000, 7356, 8645);
  assert.deepEqual(r, ["保", 0.99, "兜底"]);
});

test("9.0c 过冲丢弃: user 位次比 median 差 150% 以上 (diff >= 1.5)", () => {
  // user 30000, median 7356 → diff = 3.08 → 过冲 (null)
  assert.deepEqual(Rec.computeChance(30000, 7356, 8645), [null, null, null]);
});

test("9.1 REGRESSION: 上海大学+计算机 不应误报 (信息工程 vs 智能电网信息工程)", () => {
  // 上海大学 all_majors 含 "信息工程"/"信息管理与信息系统", 但用户输入 "计算机"
  // 旧 bug: "信息工程" 是 "智能电网信息工程" 子串, 误命中
  // 新 fix: matchAny 只保留 exact + 大类, 不再做双向 indexOf
  const m = mm(76, [{ major: "计算机", score: 5 }]);
  assert.equal(m, 0, "不应误报");
});

test("9.2 REGRESSION: 短前缀 '信息' (2 字) 命中 '信息工程'", () => {
  // "信息" 长度 2, 应该走到 prefix rule
  // 但 "信息" 在 synonyms 里? 否, 我们的 synonyms 没有"信息" category
  // 但 "信息" 是 "信息工程"/"信息管理与信息系统"/"信息与计算科学" 的 prefix
  // prefix rule: m.indexOf(kw) === 0 → 加入 m 整个 list
  // expanded("信息") → 含 "信息工程", "信息管理与信息系统", "信息与计算科学", "信息安全", "网络工程"...
  // 上海大学 all_majors 含 "信息工程" → exact match
  // 4+0.2 = 4.2
  const m = mm(76, [{ major: "信息", score: 4 }]);
  // prefix rule matches "信息工程" exact in expanded → +0.2
  assert.equal(m, 4.2, "短前缀 '信息' 命中 '信息工程'");
});

test("9.3 校 420 含 '汉语言文学', 用户 '文学' 不命中 (boundary)", () => {
  // "文学" 2 字, 不到 3 不走子串; 不是任何 major 前缀
  // "汉语言文学".indexOf("文学") = 4 (非 0) 故 prefix rule 不触发
  // 用户期望: 中文系. 实际返 0, 是 acceptable 的 false negative
  // 提示: 用户应输入 "中文" 或 "汉语言" 或 "汉语" 等更具体的词
  const m = mm(420, [{ major: "文学", score: 3 }]);
  assert.equal(m, 0, "短词 '文学' 边界不命中, 用户应输入更具体的 '中文'/'汉语言'");
});

test("9.4 校 420 含 '新闻传播学类', 用户 '新闻' 命中 (prefix 展开)", () => {
  // "新闻" 在 新闻传播学类 value → 整个类目
  // "新闻传播学类" in expanded → exact
  const m = mm(420, [{ major: "新闻", score: 3 }]);
  assert.equal(m, 3.2, "prefix 展开命中");
});

test("9.5 校 420 含 '数据科学与大数据技术', 用户 '数据' 命中 (反向 prefix)", () => {
  // "数据" 是 "数据科学与大数据技术" prefix
  const m = mm(420, [{ major: "数据", score: 3 }]);
  assert.equal(m, 3.2, "数据 → 数据科学与大数据技术");
});

// ══════════════════════════════════════════════════════
// 10. computeScore / recommend 主流程 smoke
// ══════════════════════════════════════════════════════
test("10.1 computeScore: 武汉 5★ + 计算机 5★ + 均衡 → 武汉大学 4.85 (T4 demo)", () => {
  const colleges = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/colleges.json"), "utf-8"));
  const byId = {}; for (const c of colleges) byId[c.school_id] = c;
  const wuhanUniv = byId[10183]; // 武汉大学 (实际 id 待查)
  if (!wuhanUniv) {
    // 跳过, 找不到
    return;
  }
  const s = Rec.computeScore(
    { mode: "均衡", interests: [{ major: "计算机", score: 5 }], cities: [{ city: "武汉", score: 5 }] },
    wuhanUniv, null, sam, syn
  );
  // 均衡 0.4/0.3/0.3, 计算机命中 5 (cap), 武汉命中 5, tier 985 4.5
  // 0.4*5 + 0.3*5 + 0.3*4.5 = 2 + 1.5 + 1.35 = 4.85
  assert.equal(s.total, 4.85, "均衡 4.85");
});

test("10.2 recommend 主流程: DEMO_USER 不崩", () => {
  const colleges = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/colleges.json"), "utf-8"));
  // Step 3.4 v1: 双 index, data 文件已重 key 为 edu_id
  const byId = {}; const byEid = {};
  for (const c of colleges) {
    if (c.school_id != null) byId[c.school_id] = c;
    const key = c.chsi_edu_id ? String(c.chsi_edu_id) : (c.school_id != null ? `sch_${c.school_id}` : null);
    if (key) byEid[key] = c;
  }
  const yfyd = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/yfyd_hubei_2025.json"), "utf-8"));
  const schoolHistory = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/school_history.json"), "utf-8"));
  const groupsLatest = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/groups_latest_hubei_2025.json"), "utf-8"));
  const specialties = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/school_specialties.json"), "utf-8"));
  const data = { colleges, collegesById: byId, collegesByEid: byEid, schoolHistory, groupsLatest, specialties, yfyd, schoolAllMajors: sam, majorSynonyms: syn };
  const r = Rec.recommend(Rec.DEMO_USER, data);
  assert.equal(r["冲"].length > 0, true);
  assert.equal(r["稳"].length > 0, true);
  // 9 档梯度: 至少 4 个不同 sub_tier
  const allSubs = new Set([...r["冲"], ...r["稳"], ...r["保"]].map((c) => c.sub_tier));
  assert.ok(allSubs.size >= 4, `期望 ≥4 个 sub_tier, 实有 ${[...allSubs].join(",")}`);
});

// ══════════════════════════════════════════════════════
// 11. 三省 scoreToRank (2026-06-25 省份切换)
// ══════════════════════════════════════════════════════
const yfydByProv = {
  hubei: JSON.parse(fs.readFileSync(path.join(ROOT, "data/yfyd_hubei_2025.json"), "utf-8")),
  guangdong: JSON.parse(fs.readFileSync(path.join(ROOT, "data/yfyd_guangdong_2024.json"), "utf-8")),
  jiangsu: JSON.parse(fs.readFileSync(path.join(ROOT, "data/yfyd_jiangsu_2024.json"), "utf-8")),
};

test("11.1 湖北 580 分 → 位次 24295 (2025 yfyd)", () => {
  const r = Rec.scoreToRank(580, "物理类", yfydByProv.hubei);
  assert.ok(r >= 23000 && r <= 25500, `期望 23000-25500, 实有 ${r}`);
});

test("11.2 广东 580 分 → 位次 33000 (2024 yfyd)", () => {
  const r = Rec.scoreToRank(580, "物理类", yfydByProv.guangdong);
  assert.ok(r >= 31000 && r <= 35000, `期望 31000-35000, 实有 ${r}`);
});

test("11.3 江苏 580 分 → 位次 35000 (2024 yfyd)", () => {
  const r = Rec.scoreToRank(580, "物理类", yfydByProv.jiangsu);
  assert.ok(r >= 33000 && r <= 37000, `期望 33000-37000, 实有 ${r}`);
});

// ══════════════════════════════════════════════════════
// 12. DEMO_USERS 3 套存在 + 字段完整
// ══════════════════════════════════════════════════════
test("12.1 DEMO_USERS.hubei/guangdong/jiangsu 全存在", () => {
  assert.ok(Rec.DEMO_USERS.hubei, "缺 hubei");
  assert.ok(Rec.DEMO_USERS.guangdong, "缺 guangdong");
  assert.ok(Rec.DEMO_USERS.jiangsu, "缺 jiangsu");
  for (const prov of ["hubei", "guangdong", "jiangsu"]) {
    const u = Rec.DEMO_USERS[prov];
    assert.ok(u.rank && u.score && u.type && u.xuanke && u.interests && u.cities && u.mode,
      `${prov} DEMO 字段不全`);
  }
});

test("12.2 DEMO_USER alias 兼容老调用方", () => {
  assert.equal(Rec.DEMO_USER, Rec.DEMO_USERS.hubei, "DEMO_USER 应等价 DEMO_USERS.hubei");
});

// ══════════════════════════════════════════════════════
// 13. passesXuanke 跨省 sg_info 兼容 (粤苏 CSV 转 sg_info 后能命中)
// ══════════════════════════════════════════════════════
test("13.1 广东 sg_info '首选物理，再选不限' 命中 物理类用户选 物化生", () => {
  const ok = Rec.passesXuanke("首选物理，再选不限", new Set(["物理", "化学", "生物"]), "物理类");
  assert.equal(ok, true);
});

test("13.2 江苏 sg_info '首选物理，再选物理和化学' 命中 物理类用户选 物化", () => {
  const ok = Rec.passesXuanke("首选物理，再选物理和化学", new Set(["物理", "化学"]), "物理类");
  assert.equal(ok, true);
});

test("13.3 广东 sg_info '首选物理，再选化学' 不命中 物生地 (无化学)", () => {
  const ok = Rec.passesXuanke("首选物理，再选化学", new Set(["物理", "生物", "地理"]), "物理类");
  assert.equal(ok, false);
});
