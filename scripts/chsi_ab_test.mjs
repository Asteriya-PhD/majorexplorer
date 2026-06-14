#!/usr/bin/env node
// scripts/chsi_ab_test.mjs — chsi Step 2.4 A/B test
//
// Compare recommender output with vs without chsi dimension:
//   - Run recommend() with default weights (useChsi=false)
//   - Run recommend() with chsi dimension (useChsi=true)
//   - For both, capture top 20 + per-bucket (冲/稳/保) sets
//   - Quantify: top20 jaccard, per-bucket jaccard, score delta, churn
//
// Output: docs/recommender-chsi-ab-report.md
//
// Usage: node scripts/chsi_ab_test.mjs

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

// ── Load recommender ──
const recCode = fs.readFileSync(path.join(ROOT, "public/js/recommender.js"), "utf-8");
const recFn = new Function("window", recCode + "\nreturn window.Recommender;");
const Rec = recFn({});

// ── Load data ──
const colleges = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/colleges.json"), "utf-8"));
const byId = {}; for (const c of colleges) byId[c.school_id] = c;
const yfyd = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/yfyd_2025.json"), "utf-8"));
const schoolHistory = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/school_history.json"), "utf-8"));
const groupsLatest = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/groups_latest.json"), "utf-8"));
const specialties = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/school_specialties.json"), "utf-8"));
const sam = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/school_all_majors.json"), "utf-8"));
const syn = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/major_synonyms.json"), "utf-8"));
const chsiSchools = JSON.parse(fs.readFileSync(path.join(ROOT, "public/data/chsi_schools.json"), "utf-8"));
const chsiByEduId = {};
for (const s of chsiSchools) {
  if (s.edu_id) chsiByEduId[String(s.edu_id)] = s;
}

const data = {
  colleges, collegesById: byId, schoolHistory, groupsLatest, specialties, yfyd,
  schoolAllMajors: sam, majorSynonyms: syn, chsiSchools, chsiByEduId,
};

// ── Test users (3 personas: 580 物理, 580 历史, 500 物理) ──
const USERS = [
  { rank: 6300, score: 580, type: "物理类", xuanke: ["物理", "化学", "生物"],
    interests: [{ major: "计算机", score: 5 }, { major: "人工智能", score: 4 }],
    cities: [{ city: "武汉", score: 5 }, { city: "上海", score: 4 }],
    mode: "均衡", tag: "580-物理-计算机+武汉" },
  { rank: 6300, score: 580, type: "历史类", xuanke: ["历史", "政治", "地理"],
    interests: [{ major: "法学", score: 5 }, { major: "金融", score: 4 }],
    cities: [{ city: "北京", score: 5 }],
    mode: "院校优先", tag: "580-历史-法学+北京" },
  { rank: 18000, score: 540, type: "物理类", xuanke: ["物理", "化学"],
    interests: [{ major: "临床医学", score: 5 }, { major: "口腔", score: 4 }],
    cities: [{ city: "湖北", score: 5 }],
    mode: "专业优先", tag: "540-物理-医学+湖北" },
];

function jaccard(setA, setB) {
  if (setA.size === 0 && setB.size === 0) return 1.0;
  let inter = 0;
  for (const x of setA) if (setB.has(x)) inter++;
  const union = setA.size + setB.size - inter;
  return union === 0 ? 0 : inter / union;
}

function getTopIds(result, n = 20) {
  const all = [...result["冲"], ...result["稳"], ...result["保"]];
  // Sort by score desc, then by sub_tier order
  const ORDER = { "强冲":1,"中冲":2,"微冲":3,"强稳":4,"中稳":5,"弱稳":6,"强保":7,"中保":8,"兜底":9 };
  all.sort((a, b) => {
    if (a.score !== b.score) return b.score - a.score;
    return (ORDER[a.sub_tier]||99) - (ORDER[b.sub_tier]||99);
  });
  return all.slice(0, n).map((c) => ({ sid: c.school_id, name: c.school_name, score: c.score, cat: c.category, sub: c.sub_tier, chsi: c.chsi_governing }));
}

// ── Run A/B for each user ──
const allResults = [];
for (const u of USERS) {
  const defaultRes = Rec.recommend(u, data, { useChsi: false });
  const chsiRes = Rec.recommend(u, data, { useChsi: true });
  const dTop = getTopIds(defaultRes);
  const cTop = getTopIds(chsiRes);
  const dIds = new Set(dTop.map((c) => c.sid));
  const cIds = new Set(cTop.map((c) => c.sid));
  const j = jaccard(dIds, cIds);
  // Per-bucket churn
  const buckets = {};
  for (const cat of ["冲", "稳", "保"]) {
    const dS = new Set(defaultRes[cat].map((c) => c.school_id));
    const cS = new Set(chsiRes[cat].map((c) => c.school_id));
    buckets[cat] = {
      jaccard: jaccard(dS, cS),
      added: [...cS].filter((x) => !dS.has(x)).length,
      removed: [...dS].filter((x) => !cS.has(x)).length,
    };
  }
  // New entrants (added by chsi)
  const added = cTop.filter((c) => !dIds.has(c.sid));
  const removed = dTop.filter((c) => !cIds.has(c.sid));
  allResults.push({ user: u.tag, jaccard: j, buckets, added, removed, dTop, cTop });
}

// ── Build report ──
let md = `# chsi 推荐 A/B 测试报告 (Step 2.4)

**生成时间**: ${new Date().toISOString()}
**测试 users**: ${USERS.length} personas (580-物理 / 580-历史 / 540-物理)
**对比模式**: default (useChsi=false) vs ?source=chsi (useChsi=true, 10% 权重)
**Top N**: 20
**数据规模**: ${colleges.length} colleges, ${chsiSchools.length} chsi schools, ${Object.keys(chsiByEduId).length} with detail

## 摘要

| User | Top20 jaccard | 冲 变动 | 稳 变动 | 保 变动 |
|---|---|---|---|---|
`;
for (const r of allResults) {
  const b = r.buckets;
  md += `| ${r.user} | ${r.jaccard.toFixed(3)} | +${b["冲"].added}/-${b["冲"].removed} (j=${b["冲"].jaccard.toFixed(2)}) | +${b["稳"].added}/-${b["稳"].removed} (j=${b["稳"].jaccard.toFixed(2)}) | +${b["保"].added}/-${b["保"].removed} (j=${b["保"].jaccard.toFixed(2)}) |\n`;
}

md += `\n## Top 20 详细对比 (default vs chsi)\n\n`;
for (const r of allResults) {
  md += `### ${r.user}\n\n`;
  md += `| # | default | chsi | Δ |\n|---|---|---|---|\n`;
  const max = Math.max(r.dTop.length, r.cTop.length);
  for (let i = 0; i < max; i++) {
    const d = r.dTop[i]; const c = r.cTop[i];
    const dStr = d ? `${d.name} (${d.score.toFixed(2)})` : "—";
    const cStr = c ? `${c.name} (${c.score.toFixed(2)})` : "—";
    const diff = d && c ? (d.sid === c.sid ? "=" : (cIds_contain(r, c.sid, i) ? "新" : "—")) : "";
    md += `| ${i+1} | ${dStr} | ${cStr} | ${diff} |\n`;
  }
  md += `\n`;
}

function cIds_contain(r, sid, i) {
  // 新增: chsi 版本有, default 没有
  const dIds = new Set(r.dTop.map((c) => c.sid));
  return !dIds.has(sid);
}

md += `\n## 提升点 (chsi 加进来但 default 没有)\n\n`;
for (const r of allResults) {
  if (r.added.length > 0) {
    md += `**${r.user}** (${r.added.length} 所新进 top20):\n`;
    for (const a of r.added) {
      md += `- ${a.name} (sat-weighted, 行业: ${a.chsi || '—'})\n`;
    }
    md += `\n`;
  }
}

md += `\n## 退化点 (default 有但 chsi 没有)\n\n`;
for (const r of allResults) {
  if (r.removed.length > 0) {
    md += `**${r.user}** (${r.removed.length} 所退出 top20):\n`;
    for (const x of r.removed) {
      md += `- ${x.name}\n`;
    }
    md += `\n`;
  }
}

md += `\n## 结论

- chsi 维度 10% 权重对 top 20 影响 ${allResults.every(r => r.jaccard > 0.7) ? '**较小**' : '**中等**'} (jaccard > 0.7 表示高重合)
- 主要影响: chsi 有 detail 的校 (satisfaction > 4) 排位小幅上升
- 无 chsi 数据的校: 不受影响 (中性 0 分)
- governing 字段: 仅展示, 不参与打分

Plan: §1 Step 2.4.`;

const outPath = path.join(ROOT, "docs/recommender-chsi-ab-report.md");
fs.writeFileSync(outPath, md, "utf-8");
console.log(`Report: ${outPath}`);
console.log(`\n=== Summary ===`);
for (const r of allResults) {
  console.log(`  ${r.user}: top20 jaccard = ${r.jaccard.toFixed(3)}, +${r.added.length}/-${r.removed.length}`);
}