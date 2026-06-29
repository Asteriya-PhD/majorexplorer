# Day 40 Irreducible-8 名单 (2026-06-29)

> **生成方法**: 从 121 stuck 8 + audit_count ≥5 的 slugs 分析历史 audit 中位数 (R1 = registry, R2+ = test_results)
> **数据源**: `data/audit_registry.json` (612 majors) + `test_results/content_audit_*.json` (627 files, 最新到 06-25)
> **核心事实**: Day 39 polish (06-29 commit 9631d120) **之后无任何 audit 验证**, registry 仍是 polish 前状态.
> **修正**: 原 plan 假设 "121 polished 95% 真到 9" **没有验证**. 实测 median 分布显示问题比预期严重.

---

## 📊 实测中位分布 (121 stuck 8 篇, 历史 audit)

| 类别 | Slug 数 | 定义 | Day 40 行动 |
|------|---------|------|------------|
| **A. 噪声 mis-classified** | 估算 ≤30 | R1=8 但历史有 R2 ≥9 | Round 2 audit 验真可 promote |
| **B. 真硬伤 (median ≤7)** | 实测 91 | 5+ 次 audit, 中位 ≤7, 真有短板 | Tier 2 deep rewrite (15-20 min/篇) |
| **C. 边界卡 8 (median=8)** | 实测 30 | 多次 audit 中位 8, 既不 promote 也不 stuck | 1 次 polish 尝试 |
| **D. ≥10 audit 真 irreducible** | 18 | 高重审仍 stuck 7-8, 大概率 irreducible | Tier 3 flag, 不追 |

> 18 篇 irreducible ≥10 audit (Tier 3) ≈ 121 的 15% , 78 篇真硬伤 ≈ 64%, 0 篇类 ≈ 15%, 边界 ≈ 6%.
> **结论**: Day 39 polish 假定"95% 真到 9" 不成立, 实测状态是高 noise + 真硬伤 2 类混合.

---

## 🔴 D 类: ≥10 audit 真 irreducible (18 篇)

| Slug | Title | Audits | Last Audit | 建议 |
|------|-------|--------|------------|------|
| `smart-agriculture` | 智慧农业 | 16 | 06-18 | Tier 3 flag |
| `global-climate-change` | 全球气候变化 | 16 | 06-19 | Tier 3 flag |
| `bioinformatics` | 生物信息学 | 14 | 06-19 | AI 制药风口, Deep Rewrite 候选 |
| `bionic-science-engineering` | 仿生科学与工程 | 14 | 06-18 | Tier 3 flag |
| `advertising` | 广告学 | 14 | 06-18 | 文科, 真硬伤 |
| `ndebele` | 恩德贝莱语 | 14 | 06-21 | 小语种, Tier 3 |
| `criminal-investigation` | 侦查学 | 14 | 06-21 | 公安真实雇主深改 |
| `cross-border-ecommerce` | 跨境电子商务 | 13 | 06-18 | 头部雇主 + 选品方向 |
| `cyber-information-law` | 网络与信息法学 | 12 | 06-18 | 数据合规 / 出境 |
| `safety-engineering` | 安全工程 | 11 | 06-20 | 央企 + 注册安全工程师 |
| `intelligent-marine-equipment-engineering` | 智能海洋装备工程 | 11 | 06-23 | 船舶工业真实雇主 |
| `logistics-management` | 物流管理 | 11 | 06-21 | 京东物流 / 顺丰 / 极兔 |
| `flight-vehicle-control` | 飞行器控制与信息工程 | 11 | 06-21 | 航天科工 / 航空工业 |
| `international-economic-cooperation` | 国际经济发展合作 | 11 | 06-21 | 一带一路国家项目 |
| `intelligent-vehicle-engineering` | 智能车辆工程 | 10 | 06-18 | 比亚迪 / 小鹏 / 小米汽车 |
| `digital-twin-technology` | 数字孪生技术 | 10 | 06-18 | 工信部重点方向 |
| `postal-engineering` | 邮政工程 | 10 | 06-21 | 中国邮政集团 |
| `numerical-foundation-science` | 数理基础科学 | 10 | 06-20 | 基础学科, Tier 3 |

**判定逻辑**: 5-16 次重审都上不去 9, variance noise 概率 ≤20%, 视为 irreducible.
**Day 40 行动**: 标 `irreducible-8` flag (需要扩展 registry schema 加 `tier` 字段).

---

## 🔴 B 类: 真硬伤 (median ≤7, 91 篇)

> 91 篇全是真正短板, 但**没有 1 个能从 polish 直接 promote**.
> Day 40 选 8-12 篇做 Tier 2 deep rewrite, 其余做 Day 41+ 候选池.

**Top 10 by audit_count** (历史重审越多次 = 越卡死):

| Slug | Title | Audits | 历史中位 | 关键 |
|------|-------|--------|----------|------|
| `global-climate-change` | 全球气候变化 | 16 | 7.0 | 真硬伤, ≥10 audit 不能 promote |
| `advertising` | 广告学 | 14 | 7.0 | 文科大专业, 深改空间大 |
| `ndebele` | 恩德贝莱语 | 14 | 7.0 | 小语种难, Tier 3 flag |
| `bioinformatics` | 生物信息学 | 14 | 7.0 | AI 制药风口, 缺 5校特色真实雇主 |
| `criminal-investigation` | 侦查学 | 14 | 7.0 | 公安系统真实雇主 + 选调 |
| `cross-border-ecommerce` | 跨境电子商务 | 13 | 7.0 | 头部雇主 + 选品方向 |
| `cyber-information-law` | 网络与信息法学 | 12 | 7.0 | 数据合规 / 出境 / 平台治理 |
| `safety-engineering` | 安全工程 | 11 | 7.0 | 央企 + 注册安全工程师 |
| `intelligent-marine-equipment-engineering` | 智能海洋装备工程 | 11 | 7.0 | 船舶工业真实雇主 |
| `logistics-management` | 物流管理 | 11 | 7.0 | 京东物流 / 顺丰 / 极兔 |

(剩余 81 篇: `flight-vehicle-control` / `international-economic-cooperation` / `intelligent-vehicle-engineering` / `digital-twin-technology` / `postal-engineering` / ...)

---

## 🟡 C 类: 边界 (median=8, 30 篇)

> 既不 promote 也不 stuck, 仅 1 次 polish 尝试, 失败归 irreducible.
> Day 40 优先做 A 类 R2 promote + B 类 Tier 2, C 类跳过.

---

## 🎯 Day 40 Phase 1 决策

**核心矛盾**: registry 121 stuck 8 没验证过 polish 提升. **3 种走法**:

### 方案 A (推荐): R2 audit 全跑 121 篇
- **时间**: ~60 min m3 audit (~¥30)
- **预期**: ≥30 篇真 promote ≥9 (median 历史 ≥9 的)
- **风险**: m3 variance 噪声 ±1 分, 真 promote 可能被新 audit 拉回 7-8

### 方案 B (省): 仅 R2 18 篇 ≥10 audit + 91 篇 B 类 Polish
- **时间**: 跳过 audit verify, 直接 Tier 2 改 8-12 篇
- **风险**: registry 仍是旧分, 提升未量化, Day 41 又会重复

### 方案 C (空): 只写 deliverable doc, 不动 registry
- **时间**: doc only
- **风险**: 全部留给 Day 41

**Day 40 决策**: **方案 A** — 跑 R2 audit 121 篇, ROI 最高 (¥30 → 估 ≥30 promote), 还能同步验 Day 39 polish 真实提升.

---

## 🔁 与 Day 36-39 关系

| Session | 主功能 | Day 40 接续 |
|---------|--------|-------------|
| Day 36 | 部署收口 | Phase 2.5 curl 验 404 兜底 |
| Day 37 | 校友真数据 | Phase 2.3 alumni 扫 0 占位 |
| Day 38 | polish 模板化 | 模板复用 Day 40 Phase 3 |
| Day 39 | 121 stuck 8 → 9 | **Day 40 R2 验真** (发现: 中位 ≤7 真硬伤 91, 不全 noise) |

---

**生成时间**: 2026-06-29 (Day 40 Phase 1)
**起点**: main `7c634654`, branch `fix/day40-variance-polish-chsi`
**关键文件**: `/tmp/irreducible-8-day40.json` (full classification)
**下阶段**: Phase 1.5 R2 audit run + Phase 2 清理日 + Phase 3 9→10 polish
