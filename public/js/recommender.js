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

  // ───────── 3. 位次法 — 冲稳保 9 档细分桶 ─────────
  // diff = (userRank - medRank) / medRank
  //   diff > 0 : 校位次更靠前 (校更强), 用户在冲
  //   diff < 0 : 用户位次更靠前 (用户更强), 用户在保
  // 设计原则: 冲档底线 25%; 9 档单调; 内部拉梯度.
  // maxRank (可选): 该校该类别历史最深录取位次. 用户位次远超 maxRank 时, 强制归为"保兜底".
  function computeChance(userRank, medRank, maxRank) {
    if (!medRank || medRank <= 0) return [null, null, null];

    // ── 强保底: 用户位次比"该校最深录取线"还差 20% 以上, 闭眼能上 ──
    if (maxRank && maxRank > 0 && userRank > maxRank * 1.2) {
      return ["保", 0.99, "保兜底"];
    }

    const diff = (userRank - medRank) / medRank;

    // ── 过冲丢弃: 用户位次比校 median 高 150% 以上 (= 校录取位次 < 用户的 40%), 纯赌博, 不推荐 ──
    if (diff >= 1.5) return [null, null, null];

    // ── 冲档 (3 级, 25% → 50%) ──
    if (diff >= 0.50)  return ["冲", 0.25, "极冲"]; // 校强自己 50%+
    if (diff >= 0.25)  return ["冲", 0.38, "中冲"]; // 校强自己 25-50%
    if (diff >= 0.10)  return ["冲", 0.50, "微冲"]; // 校强自己 10-25%
    // ── 稳档 (3 级, 65% → 88%) ──
    if (diff >= -0.05) return ["稳", 0.65, "稳压线"]; // ±5% borderline
    if (diff >= -0.15) return ["稳", 0.78, "稳基本"]; // 自己强 5-15%
    if (diff >= -0.28) return ["稳", 0.88, "稳有余"]; // 自己强 15-28%
    // ── 保档 (3 级, 93% → 99%) ──
    if (diff >= -0.45) return ["保", 0.93, "保中坚"]; // 自己强 28-45%
    if (diff >= -0.65) return ["保", 0.97, "保稳妥"]; // 自己强 45-65%
    return                  ["保", 0.99, "保兜底"]; // 自己强 65%+
  }

  // sub_tier 在最终列表里的排序权重 (按概率单调升序排列)
  const SUB_TIER_ORDER = {
    "极冲": 1, "中冲": 2, "微冲": 3,
    "稳压线": 4, "稳基本": 5, "稳有余": 6,
    "保中坚": 7, "保稳妥": 8, "保兜底": 9,
  };
  // 各 sub_tier 所属档位
  const SUB_TO_CAT = {
    "极冲": "冲", "中冲": "冲", "微冲": "冲",
    "稳压线": "稳", "稳基本": "稳", "稳有余": "稳",
    "保中坚": "保", "保稳妥": "保", "保兜底": "保",
  };
  // 同档内借调时优先顺序 (相邻 sub_tier 先借, 边缘 sub_tier 后借)
  const FILL_ORDER = {
    "冲": ["微冲", "中冲", "极冲"],
    "稳": ["稳基本", "稳有余", "稳压线"],
    "保": ["保中坚", "保稳妥", "保兜底"],
  };

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

  function majorMatch(schoolId, interests, specialties, allMajorsById, synonymMap) {
    if (!interests || interests.length === 0) return 0;
    const sid = String(schoolId);
    const spData = specialties && specialties[sid];
    const topSpecs = (spData && spData.top_specials) || [];
    // all_majors 主源: 128 校 admissions_raw 全量, 命中给 +0.2 (校真有这个专业, 强证据)
    // 880 校无 all_majors 数据, schoolAllMajors[sid] 为 undefined → 自然 fallback
    const schoolAllMajors = (allMajorsById && allMajorsById[sid] && allMajorsById[sid].all_majors) || [];
    // synonyms 兼容: 老调用方可能没传 synonymMap
    synonymMap = synonymMap || {};

    // 同义词展开 (4 路):
    //   1) 正向: kw 是 category key → 整个类目
    //   2) 反向: kw 精确等于某 category value (e.g. "金融学")
    //   3) 前缀: kw 是某 major 的前 N 字 (e.g. "金融" 是 "金融学"/"金融工程" 前缀)
    //   4) 子串: kw (>=3 字) 是某 major 的子串
    // 注: kw 自身永远在 set (用户可能直接打完整 major 名)
    function expandInterest(kw) {
      const out = new Set([kw]);
      if (!kw) return out;
      // 1) 正向
      if (synonymMap[kw]) synonymMap[kw].forEach((m) => out.add(m));
      // 2/3/4) 扫描全 synonyms, 找匹配
      for (const cat of Object.keys(synonymMap)) {
        if (cat === "_meta") continue;
        const list = synonymMap[cat];
        if (!Array.isArray(list)) continue;
        for (const m of list) {
          if (out.has(m)) continue; // 已加 (1) 或 (2)
          if (m === kw) {
            // 2) 精确
            list.forEach((x) => out.add(x));
            break;
          } else if (kw.length >= 2 && m.indexOf(kw) === 0) {
            // 3) 前缀: kw 是 m 的开头 (e.g. "金融" → "金融学")
            list.forEach((x) => out.add(x));
            break;
          } else if (kw.length >= 3 && m.indexOf(kw) !== -1) {
            // 4) 子串: kw (>=3) 出现在 m 里
            out.add(m);
          }
        }
      }
      return out;
    }

    // 匹配 helper: major name vs expanded set
    // 设计原则: matchAny 是最后兜底, 主要匹配逻辑在 expandInterest 已完成 (双向 + 前缀 + 子串).
    // 这里只保留两类: exact 命中 + 大类兼容. 双向 indexOf 容易误报 (e.g. "信息工程" ⊂ "智能电网信息工程"),
    // 走 expandInterest 的 prefix rule 处理.
    function matchAny(sname, expanded) {
      if (!sname) return false;
      if (expanded.has(sname)) return true;
      for (const e of expanded) {
        if (!e) continue;
        // 学科大类兼容: "计算机" → "计算机类" (sname 是 e + "类")
        if (sname === e + "类" || sname === e + "（...）") return true;
      }
      return false;
    }

    let best = 0;
    for (const it of interests) {
      const kw = it.major;
      if (!kw) continue;
      const userScore = it.score || 0;
      const expanded = expandInterest(kw);

      // ── 主源: 校 all_majors (128 校有, 880 校跳过) ──
      if (schoolAllMajors.length > 0) {
        for (const m of schoolAllMajors) {
          if (matchAny(m, expanded)) {
            const score = Math.min(5.0, userScore + 0.2); // 真有这个专业, 强证据
            if (score > best) best = score;
            break; // 1 个 interest × 1 校只计最强
          }
        }
      }

      // ── Fallback: top_specials (软科 bonus 替代 all_majors 0.2) ──
      if (best < userScore + 0.5 && topSpecs.length > 0) {
        for (const spec of topSpecs) {
          const sname = spec.name || "";
          if (matchAny(sname, expanded)) {
            let bonus = 0;
            const rk = spec.xueke_rank_score || spec.ruanke_level || "";
            if (rk.indexOf("A+") === 0) bonus = 0.5;
            else if (rk.indexOf("A") === 0) bonus = 0.3;
            else if (rk.indexOf("B") === 0) bonus = 0.1;
            const score = Math.min(5.0, userScore + bonus);
            if (score > best) best = score;
            break;
          }
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

  function computeScore(user, college, specialties, allMajorsById, synonymMap) {
    const w = WEIGHTS[user.mode] || WEIGHTS["均衡"];
    const [a, b, g] = w;
    const m = majorMatch(college.school_id, user.interests || [], specialties, allMajorsById, synonymMap);
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
    // 9 个 sub_tier 各自的配额 (合计 12+16+8=36 张卡)
    // 内部强制每个 sub_tier 至少 1 条, 保证档内梯度.
    const subQuotas = Object.assign({
      "极冲": 4, "中冲": 4, "微冲": 4,    // 冲 12
      "稳压线": 6, "稳基本": 6, "稳有余": 4, // 稳 16
      "保中坚": 4, "保稳妥": 3, "保兜底": 1, // 保 8
    }, opts.subQuotas || {});
    const topChong = opts.topChong || (subQuotas["极冲"] + subQuotas["中冲"] + subQuotas["微冲"]);
    const topWen = opts.topWen || (subQuotas["稳压线"] + subQuotas["稳基本"] + subQuotas["稳有余"]);
    const topBao = opts.topBao || (subQuotas["保中坚"] + subQuotas["保稳妥"] + subQuotas["保兜底"]);

    const { collegesById, schoolHistory, groupsLatest, specialties, yfyd, schoolAllMajors, majorSynonyms } = data;
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
      const recentMaxes = [];
      for (const yr of histKeys) {
        const y = parseInt(yr, 10);
        const r = hist[yr];
        if (y >= 2023 && r && r.median_rank) recentMedians.push(r.median_rank);
        if (y >= 2023 && r && r.max_rank) recentMaxes.push(r.max_rank);
      }
      if (recentMedians.length < 2) continue;
      const med3y = median(recentMedians);
      // max_rank = 该校历史最深录取位次 (录取门槛上限). 用于"强保底"判定.
      const maxRank3y = recentMaxes.length > 0 ? Math.max.apply(null, recentMaxes) : null;

      const passing = schoolGroups.filter((g) =>
        passesXuanke(g.sg_info, userSet, user.type)
      );
      if (passing.length === 0) continue;

      const [cat, prob, subTier] = computeChance(user.rank, med3y, maxRank3y);
      if (!cat) continue;

      const scoreInfo = computeScore(user, college, specialties, schoolAllMajors, majorSynonyms);

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
        sub_tier: subTier,
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

    // ── 9 sub_tier 细分桶, 每桶按 score 降序 ──
    const subBuckets = {};
    for (const k of Object.keys(SUB_TIER_ORDER)) subBuckets[k] = [];
    for (const c of candidates) {
      if (c.sub_tier && subBuckets[c.sub_tier]) subBuckets[c.sub_tier].push(c);
    }
    for (const k of Object.keys(subBuckets)) {
      subBuckets[k].sort((a, b) => b.score - a.score);
    }

    // ── 第一轮: 按 sub_tier 配额取数 ──
    const result = { "冲": [], "稳": [], "保": [] };
    const taken = new Set();
    for (const sub of Object.keys(subQuotas)) {
      const need = subQuotas[sub] || 0;
      const picks = subBuckets[sub].slice(0, need);
      for (const p of picks) {
        result[SUB_TO_CAT[sub]].push(p);
        taken.add(p.school_id);
      }
      subBuckets[sub] = subBuckets[sub].slice(need); // 剩下的作 fallback 池
    }

    // ── 第二轮: 档内额度不足时, 从相邻 sub_tier 借 ──
    function fillCategory(cat, target) {
      const order = FILL_ORDER[cat];
      while (result[cat].length < target) {
        let filled = false;
        for (const sub of order) {
          if (subBuckets[sub].length > 0) {
            const p = subBuckets[sub].shift();
            if (taken.has(p.school_id)) continue;
            result[cat].push(p);
            taken.add(p.school_id);
            filled = true;
            if (result[cat].length >= target) break;
          }
        }
        if (!filled) break; // 池全空
      }
    }
    fillCategory("冲", topChong);
    fillCategory("稳", topWen);
    fillCategory("保", topBao);

    // ── 第三轮: 保档配额不足时, 从稳档"稳有余"借 (边缘用户位次太低没保底时兜底) ──
    // 用户低分段 (e.g. 480) 保档常为空, 此时让稳档"稳有余"晋升当保, 是合理 fallback.
    function crossFillBaoFromWen(target) {
      const sources = ["稳有余", "稳基本"]; // 稳档里最稳的先借
      while (result["保"].length < target) {
        let filled = false;
        for (const sub of sources) {
          if (subBuckets[sub].length > 0) {
            const p = subBuckets[sub].shift();
            if (taken.has(p.school_id)) continue;
            // 重打标签: 显示为"保"档但保留原 prob, sub_tier 标 "保(原稳有余)"
            p.category = "保";
            p.sub_tier = "保" + p.sub_tier; // e.g. "保稳有余", chip 走默认色
            result["保"].push(p);
            taken.add(p.school_id);
            filled = true;
            if (result["保"].length >= target) break;
          }
        }
        if (!filled) break;
      }
    }
    crossFillBaoFromWen(topBao);

    // ── 档内按概率升序排 (整 36 条单调递增, 冲→保 prob 25%→99%) ──
    for (const k of Object.keys(result)) {
      result[k].sort((a, b) => {
        if (a.prob !== b.prob) return a.prob - b.prob;
        // 同 prob 时 按 score 降序 (热门校优先)
        return b.score - a.score;
      });
    }

    return {
      "冲": result["冲"],
      "稳": result["稳"],
      "保": result["保"],
      stats: {
        total_candidates: candidates.length,
        chong_pool: candidates.filter((c) => c.category === "冲").length,
        wen_pool: candidates.filter((c) => c.category === "稳").length,
        bao_pool: candidates.filter((c) => c.category === "保").length,
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
