# Day 40 Plan: Variance 验证 + Day 39 收口 + 9→10 + chsi 接入 (2026-06-29)

> **目标**: 跑 Day 39 variance verify + 清理日 + 9→10 Tier 2 polish + chsi 2025 数据接入
> **方法**: 4 阶段流水线 (verifier → cleanup → polish → chsi prep), 按 ROI 排序
> **总估时**: 4-6h 单 session

---

## 📊 Phase 0 Day 39 现状预估

| 指标 | Day 39 polish 前 | Day 39 polish 后 (估) | Day 40 目标 |
|------|------------------|------------------------|------------|
| 8 分 stuck (5+ 审) | 121 | **≤ 30** (variance noise) | **≤ 10** (留 irreducible) |
| 9 分 stuck (3+ 审) | ~80 | ~80 (单 polish 没动) | **≥ 30 (Tier 2 真提升 9→10)** |
| -alum-N 占位 | 0 (Day 37 收口) | 0 | **0** (sweep 验) |
| mobile preferences.html | 缺 | 缺 | **0 error** |
| aggregates phantom_html_samples | 10 dead ref | 10 dead ref | **0** |
| chsi 招生数据 (阳光高考) | 2024 snapshot | 2024 | **2025-06-29 live cache** |

---

## 🌊 4 阶段流水线

### **阶段 1: Variance 验证 (30 min)**

**目标**: 验 Day 39 polish 真提升 9 分, 找 irreducible-8 真 stuck 名单.

```bash
# Step 1.1 跑 variance_verify (跨 8 → 9 路径)
python3 scripts/audit/variance_verify_7boundary.py --from-day 39
# 期望: ≥ 95 true promoted 8 → 9

# Step 1.2 跑 smart_audit 看 L1 warning
python3 scripts/audit/smart_audit.py --dry-run | grep "L1 warning"
# 期望: < 30 真 warning (vs Day 36 启 200+)

# Step 1.3 生成 irreducible-8 报告
jq '[.majors | to_entries[]
    | select(.value.current_score == 8 and .value.audit_count >= 5)
    | {slug: .key, score: .value.current_score, audits: .value.audit_count, title: .value.title}]
   | sort_by(-.audits)' data/audit_registry.json
# 输出 ≤ 30 个 irreducible-8 名单
```

**Deliverable**: `docs/irreducible-8-day39.md` 25-30 篇 (Tier 3 flag 候选)

---

### **阶段 2: 清理日 (30 min)**

**目标**: 5 件快赢 (15min/batch ROI 极高).

| # | 项 | 时间 | 命令 |
|---|----|------|------|
| 2.1 | mobile/preferences.html 补 (verify_mobile 0 error) | 10 min | `python3 scripts/build/render_mobile.py --slug preferences` (但要 JSON). 看是否真要建 JSON/HTML |
| 2.2 | aggregates.json phantom_html_samples 清 (10 dead ref) | 5 min | 直接 sed 删 `phantom_html_samples: []` 字段 |
| 2.3 | alumni 扫描 `-alum-N` 占位 + `某.+届.*某.*` 关键词 | 5 min | `jq` sweep 所有 JSON |
| 2.4 | `public/m/majors/manifest` false positive (verify_mobile 报) | 2 min | `python3 -c "..."` 加 filter 或 rm 该假文件 |
| 2.5 | `_redirects` `/*` 404 兜底验证 (Day 36 已修) | 3 min | `curl -I https://majorexplorer.com/non-existent.html` 应该 404 而非 CF default |
| 2.6 | `land-science-technology` 等 5 篇 `< 5 所` 等描述残留 | 5 min | `grep -l "< 5 所\|< 20 所\|< 10 所" public/*.html \| head -5` 然后 re-render 这些 |

---

### **阶段 3: 9 → 10 Tier 2 polish (2-3h)**

**目标**: 把 9 分 stuck 3+ 审真硬伤 polish 到 10.

**9→10 vs 8→9 难度差异**:
- 8→9: 单硬伤 fix (pitfalls=0), 5-10 min/篇
- 9→10: 多硬伤 deep rewrite (lede+pitfalls+deep_study+校友), 15-20 min/篇

**Top 候选 (按 audit_count)**:

| 候选 | 专业 | 5+ 审 | 难点 |
|------|------|-------|------|
| `engineering-mechanics` | 工程力学 | 8 审 | top_schools 含 985 误标? lede 长? |
| `safety-engineering` | 安全工程 | 11 审 | 央企 + 注册安全工程师 |
| `robotics-engineering` | 机器人工程 | 5 审 | 大疆/优必选 Top 5 |
| `bioinformatics` | 生物信息学 | 14 审 | AI 制药风口 |
| `intelligent-vehicle-engineering` | 智能车辆工程 | 10 审 | 小米/华为车 BU 风向 |
| ... | ... | ... | (估 50-80 篇 9分 stuck) |

**每篇 Tier 2 流程 (15-20 min)**:
1. `python3 -c "..."` 看数据完整度 (lead/deep_study/alumni/pitfalls)
2. 修 2-3 个硬伤 (不是 1 个, 因为 9→10 比 8→9 难)
3. 加 1-2 条校友真数据 (Day 37 alumni 模板)
4. `python3 scripts/build/render_one.py <slug>`
5. git commit 单篇

**预期**: 8-12 篇 9→10 polish (2h), 避免 variance stuck

---

### **阶段 4: chsi 2025 招生数据接入 (1-2h prep)**

**目标**: cache chsi 2025 新数据, 准备 Phase 1 (抓取) 给后续 session 跑.

**当前状态** (Day 14 chsi Phase 2 已 ship):
- `public/data/chsi_majors.json` 2950 校 + 868 专业
- `patchright` 破阿里云反爬, scrape 已部署
- 测试脚本在 `scripts/build/chsi_*.py`

**Phase 1-4 actions**:
| 阶 | 描述 | 估时 |
|----|------|------|
| 1 | 检查 chsi_majors.json 时间戳 + 备份 | 5 min |
| 2 | `python3 scripts/build/chsi_fetch.py --year 2025` 半自动刷新 | 30 min |
| 3 | diff 2024 vs 2025 招生代码 / 新增专业 | 30 min |
| 4 | 写 docs/PLAN_chsi_2025_integration.md (后续 session 用) | 30 min |

**预期 Phase 1-3 完成**: chsi 2025 数据 live cache, Day 41+ 可接聚合页

---

## 🧵 时间预期 (总 4-6h)

| 阶段 | 估时 |
|------|------|
| Phase 1 variance 验 | 30 min |
| Phase 2 清理日 | 30 min |
| Phase 3 9→10 polish | 2-3h |
| Phase 4 chsi 2025 prep | 1-2h |
| **总计** | **4-6h** |

---

## ⚠️ 风险 + 应对

| 风险 | 应对 |
|------|------|
| **variance verify 全 stale (noise)** | Tier 3 flag, 不追死磕 |
| **9→10 polish ROI 极低** | max 8-12 篇, 不强行 |
| **chsi 2025 scrape 失败** (反爬升级) | 备份 2024, 接 Day 41 manual update |
| **移动端 preferences 真要建 JSON** | 跳过 (Phase 2 5min 验收, 不强求建数据) |

---

## 💡 5 决策点

| # | 决策 | 选定 | 影响 |
|---|------|------|------|
| 1 | Variance verify 全跑 vs 抽样 | **A**: 全跑 (registry 已有 121 数据) | 一次性真数据 |
| 2 | 9→10 polish 篇数 | **A**: 8-12 篇 (Tier 2 限 20min, 不强冲) | ROI 边界 |
| 3 | Phase 2 5 项全清 vs 选 3 | **A**: 全清 (5-10 min/项, ROI 高) | 闭环 |
| 4 | chsi 2025 Phase 1-2 vs 仅 prep doc | **A**: Phase 1-3 + plan doc (真抓) | 数据真 |
| 5 | merge main 时机 | **A**: Phase 1-4 全完合并 (4 commits) | 收口 |

---

## 🔁 与 Day 36-39 关系

| Session | 主功能 | Day 40 接续 |
|---------|--------|-------------|
| Day 36 | 部署收口 | Phase 2.5 curl 验 404 兜底 |
| Day 37 | 校友真数据 | Phase 2.3 alumni 扫 0 占位 |
| Day 38 | polish 模板化 | 模板复用 Phase 3 9→10 |
| Day 39 | 121 stuck 8 → 9 | Phase 1 variance 验 + Phase 3 polish 9→10 |

---

## 📋 验收清单 (Day 40 收工)

```bash
# Phase 1
test -f docs/irreducible-8-day39.md && wc -l docs/irreducible-8-day39.md  # 25-30

# Phase 2
python3 scripts/audit/verify_mobile.py  # 0 error
grep -c "phantom_html_samples" public/data/aggregates.json  # 0
grep -r "-alum-N" skills/gaokao-major-explorer/data/curated/ | wc -l  # 0

# Phase 3
jq '.majors | to_entries[] | select(.value.current_score == 10) | .key' data/audit_registry.json | wc -l  # ≥ 30 (vs Day 39 估 18)

# Phase 4
test -f public/data/chsi_majors.json && jq '.updated_at' public/data/chsi_majors.json  # 2025-06-29+
test -f docs/PLAN_chsi_2025_integration.md
```

**总预期**: 4-6h 单 session, 估 3-4 commit (Phase 1+2+3+4 各 1 大 commit or 合)
**最终**: Day 39 polish 真提升 ≥ 95 + 清理日 5 项闭环 + 9→10 polish 8-12 篇 + chsi 2025 live cache

---

## 📅 时间预期

- **Phase 1**: 30 min (variance 数据 + irreducible 名单)
- **Phase 2**: 30 min (5 清理项)
- **Phase 3**: 2-3h (9→10 polish batch)
- **Phase 4**: 1-2h (chsi 2025 fetch + diff)

---

**生成时间**: 2026-06-29 17:30 (Day 39 收口 + 用户确认)
**下 session 起**: 重开会话后执行
**起点**: main `9631d120` (Day 39 已 push)
