/* ====================================================================
 * recommender.js — 湖北高考志愿推荐引擎 (browser port)
 *
 * 直译自 scripts/recommender.py.
 * 7 个核心函数 + 1 个 recommend 主流程, 无外部依赖.
 *
 * 输入:
 *   user = {
 *     score: 580, rank: 6300,             // 任一即可
 *     type: '物理类' | '历史类',
 *     xuanke: ['物理','化学','生物'],
 *     interests: [{major:'计算机', score:5}, ...],
 *     cities:    [{city:'武汉', score:5}, ...],
 *     mode: '院校优先' | '专业优先' | '均衡',
 *   }
 *   data  = {colleges, schoolHistory, groupsLatest, specialties, yfyd, ...}
 *
 * 输出:
 *   {'冲':[...6], '稳':[...10], '保':[...4], stats:{...}}
 *
 * 与 Python 输出对齐 (DEMO_USER 验证: 同样 20 个学校 + 同 prob/score)
 * ==================================================================== */

(function (global) {
  "use strict";

  // 手写 median (无 statistics 包)
  function median(arr) {
    if (!arr || arr.length === 0) return null;
    const s = arr.slice().sort((a, b) => a - b);
    const n = s.length;
    if (n % 2 === 0) return (s[n / 2 - 1] + s[n / 2]) / 2;
    return s[Math.floor(n / 2)];
  }

  // ───────── 1. 分数 / 位次互转 (一分一段) ─────────
  function scoreToRank(score, type, yfyd) {
    const bucket = type === "物理类" ? "wuli" : "lishi";
    const rows = (yfyd[bucket] && yfyd[bucket].rows) || [];
    for (const r of rows) {
      if (r.score <= score) return r.rank;
    }
    return rows.length ? rows[rows.length - 1].rank : null;
  }

  function rankToScore(rank, type, yfyd) {
    const bucket = type === "物理类" ? "wuli" : "lishi";
    const rows = (yfyd[bucket] && yfyd[bucket].rows) || [];
    for (const r of rows) {
      if (r.rank >= rank) return r.score;
    }
    return rows.length ? rows[rows.length - 1].score : null;
  }

  // ───────── 2. 选科硬过滤 ─────────
  function passesXuanke(sgInfo, userSet, type) {
    if (!sgInfo) return false;
    const first = type === "物理类" ? "物理" : "历史";
    if (sgInfo.indexOf("首选" + first) === -1) return false;
    let tail = "";
    const idx = sgInfo.indexOf("再选");
    if (idx >= 0) tail = sgInfo.slice(idx + 2);
    if (!tail || tail.indexOf("不限") !== -1) return true;
    tail = tail.trim().replace(/[。.]+$/, "");
    if (tail.indexOf("和") !== -1) {
      const reqs = tail.split("和").map((s) => s.trim()).filter(Boolean);
      return reqs.every((r) => userSet.has(r));
    }
    if (tail.indexOf("或") !== -1) {
      const alts = tail.split("或").map((s) => s.trim()).filter(Boolean);
      return alts.some((a) => userSet.has(a));
    }
    return userSet.has(tail);
  }

  // ───────── 3. 位次法 — 冲稳保分桶 ─────────
  function computeChance(userRank, medRank) {
    if (!medRank || medRank <= 0) return [null, null];
    const diff = (userRank - medRank) / medRank;
    if (diff >= 0.30) return ["冲", 0.20];
    if (diff >= 0.10) return ["冲", 0.35];
    if (diff >= -0.05) return ["稳", 0.60];
    if (diff >= -0.20) return ["稳", 0.75];
    if (diff >= -0.40) return ["保", 0.88];
    return ["保", 0.95];
  }

  // ───────── 4. 偏好评分 ─────────
  const WEIGHTS = {
    "院校优先": [0.3, 0.2, 0.5],
    "专业优先": [0.6, 0.2, 0.2],
    "均衡":   [0.4, 0.3, 0.3],
  };
  const TIER_SCORE = {
    "C9": 5.0, "985": 4.5, "211": 4.0,
    "双一流": 3.5, "公办本科": 2.5, "民办/独立": 1.5,
  };

  function majorMatch(schoolId, interests, specialties) {
    if (!interests || interests.length === 0 || !specialties) return 0;
    const spData = specialties[String(schoolId)];
    if (!spData) return 0;
    const topSpecs = spData.top_specials || [];
    if (topSpecs.length === 0) return 0;

    let best = 0;
    for (const spec of topSpecs) {
      const sname = spec.name || "";
      for (const it of interests) {
        const kw = it.major;
        if (!kw) continue;
        // 双向包含 / 首 2 字相同
        if (sname.indexOf(kw) !== -1 || kw.indexOf(sname) !== -1 || sname.slice(0, 2) === kw.slice(0, 2)) {
          let bonus = 0;
          const rk = spec.xueke_rank_score || spec.ruanke_level || "";
          if (rk.indexOf("A+") === 0) bonus = 0.5;
          else if (rk.indexOf("A") === 0) bonus = 0.3;
          else if (rk.indexOf("B") === 0) bonus = 0.1;
          const score = Math.min(5.0, (it.score || 0) + bonus);
          if (score > best) best = score;
          break;
        }
      }
    }
    return best;
  }

  function cityMatch(schoolCity, cities) {
    if (!cities || cities.length === 0 || !schoolCity) return 0;
    for (const c of cities) {
      if (!c || !c.city) continue;
      if (schoolCity.indexOf(c.city) !== -1 || c.city.indexOf(schoolCity) !== -1) {
        return c.score || 0;
      }
    }
    return 0;
  }

  function computeScore(user, college, specialties) {
    const w = WEIGHTS[user.mode] || WEIGHTS["均衡"];
    const [a, b, g] = w;
    const m = majorMatch(college.school_id, user.interests || [], specialties);
    const c = cityMatch(college.city || "", user.cities || []);
    const t = TIER_SCORE[college.tier || "民办/独立"] || 1.5;
    return {
      total: Math.round((a * m + b * c + g * t) * 100) / 100,
      major: m,
      city: c,
      tier: t,
      weights: [a, b, g],
    };
  }

  // ───────── 5. 主流程 ─────────
  function recommend(user, data, opts) {
    opts = opts || {};
    const topChong = opts.topChong || 6;
    const topWen = opts.topWen || 10;
    const topBao = opts.topBao || 4;

    const { collegesById, schoolHistory, groupsLatest, specialties, yfyd } = data;
    if (!collegesById || !schoolHistory || !groupsLatest || !specialties || !yfyd) {
      throw new Error("recommend: data is incomplete");
    }
    // 自动反查位次
    if ((user.rank == null) && (user.score != null)) {
      user.rank = scoreToRank(user.score, user.type, yfyd);
    }
    if (user.rank == null) {
      throw new Error("recommend: 缺少分数或位次");
    }

    const userSet = new Set(user.xuanke || []);
    const bucket = user.type === "物理类" ? "wuli" : "lishi";

    // 把 groups 按 school_id 聚合
    const bySchool = new Map();
    for (const g of (groupsLatest[bucket] || [])) {
      const arr = bySchool.get(g.school_id) || [];
      arr.push(g);
      bySchool.set(g.school_id, arr);
    }

    const candidates = [];
    for (const [sid, schoolGroups] of bySchool.entries()) {
      const college = collegesById[sid];
      if (!college) continue;
      const hist = (schoolHistory[String(sid)] || {})[user.type] || {};
      const histKeys = Object.keys(hist);
      if (histKeys.length === 0) continue;

      const recentMedians = [];
      for (const yr of histKeys) {
        const y = parseInt(yr, 10);
        const r = hist[yr];
        if (y >= 2023 && r && r.median_rank) recentMedians.push(r.median_rank);
      }
      if (recentMedians.length < 2) continue;
      const med3y = median(recentMedians);

      const passing = schoolGroups.filter((g) =>
        passesXuanke(g.sg_info, userSet, user.type)
      );
      if (passing.length === 0) continue;

      const [cat, prob] = computeChance(user.rank, med3y);
      if (!cat) continue;

      const scoreInfo = computeScore(user, college, specialties);

      // 用户位次 ±30% 的专业组排前
      let rankTargets = passing.filter((pg) =>
        pg.min_rank && Math.abs((user.rank - pg.min_rank) / pg.min_rank) < 0.30
      );
      rankTargets.sort((x, y) =>
        Math.abs(user.rank - (x.min_rank || 0)) - Math.abs(user.rank - (y.min_rank || 0))
      );
      if (rankTargets.length === 0) {
        rankTargets = passing.slice().sort((x, y) => -(x.min_score || 0) - (-(y.min_score || 0)));
      }

      const spData = specialties[String(sid)] || {};
      const topMajors = (spData.top_specials || []).slice(0, 5).map((s) => ({
        name: s.name,
        xueke: s.xueke_rank_score || "",
        ruanke: s.ruanke_level || "",
      }));

      // 4 年位次 history brief
      const histBrief = {};
      for (const yr of Object.keys(hist)) {
        histBrief[yr] = hist[yr].median_rank;
      }

      candidates.push({
        school_id: sid,
        school_name: college.name,
        city: college.city || "",
        tier: college.tier || "",
        type: college.type || "",
        nature: college.nature || "",
        category: cat,
        prob: prob,
        median_rank_3y: med3y,
        history_brief: histBrief,
        score: scoreInfo.total,
        score_breakdown: scoreInfo,
        top_groups: rankTargets.slice(0, 3).map((g) => ({
          sg_name: g.sg_name,
          sg_info: g.sg_info,
          min_score_2025: g.min_score,
          min_rank_2025: g.min_rank,
        })),
        top_majors: topMajors,
      });
    }

    // 分桶 + 桶内按总分降序
    const buckets = { "冲": [], "稳": [], "保": [] };
    for (const c of candidates) buckets[c.category].push(c);
    for (const k of Object.keys(buckets)) {
      buckets[k].sort((a, b) => b.score - a.score);
    }

    return {
      "冲": buckets["冲"].slice(0, topChong),
      "稳": buckets["稳"].slice(0, topWen),
      "保": buckets["保"].slice(0, topBao),
      stats: {
        total_candidates: candidates.length,
        chong_pool: buckets["冲"].length,
        wen_pool: buckets["稳"].length,
        bao_pool: buckets["保"].length,
        user_rank: user.rank,
        user_score: user.score,
      },
    };
  }

  // Demo (与 Python DEMO_USER 一致)
  const DEMO_USER = {
    rank: 6300,
    score: 580,
    type: "物理类",
    xuanke: ["物理", "化学", "生物"],
    interests: [
      { major: "计算机", score: 5 },
      { major: "人工智能", score: 4 },
      { major: "软件", score: 3 },
      { major: "电子", score: 3 },
    ],
    cities: [
      { city: "武汉", score: 5 },
      { city: "上海", score: 4 },
      { city: "北京", score: 3 },
    ],
    mode: "均衡",
  };

  global.Recommender = {
    DEMO_USER,
    median,
    scoreToRank,
    rankToScore,
    passesXuanke,
    computeChance,
    majorMatch,
    cityMatch,
    computeScore,
    recommend,
  };
})(typeof window !== "undefined" ? window : globalThis);
