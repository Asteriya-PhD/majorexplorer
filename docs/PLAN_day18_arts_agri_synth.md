# Day 18 Plan: Arts + Agri Polish + 5 score=null Synth

> **日期**: 2026-06-21 重开 session  
> **前置**: Day 17 cleanup pushed (305f88d), 8+ **418/518 (80.69%)** 7-8 42 (含 40 irreducible-7) / 6-7 13 / <6 0 / null 5  
> **目标**: 14 篇 1 session 完成 (Phase 1: 9 polish + Phase 2: 5 synth+audit), ~3h 总投入

---

## 🎯 Phase 1: 9 篇 Polish (估时 ~1.5h)

| Worker | slugs | style | ROI |
|--------|-------|-------|-----|
| **A. arts 7** | animation / acting / digital-performance-design / digital-theatre / intelligent-imaging-art / cultural-relics-conservation-restoration / popular-music | arts | 中-高 (m3 variance stuck 多次) |
| **B. agri 2** | apiculture / facility-agriculture-science-engineering | agri | 中 (小众但完整) |

**Tier 策略** (沿用 Day 16 D/E 范式):
- Tier 1 (5-10min): 补 weak field (lede/pitfalls/alumni_quotes)
- Tier 2 (15-20min): 重写 (参考 P0 cultural-relics-museology for arts, electronic-science-technology for eng)
- Tier 3 (≤45min): irreducible-<Y> 标记跳过

**anti-pollution 检查清单** (4 规则):
- ❌ lede 套话 "X 是研究...的学科"
- ❌ who_fits_no 串台 (arts 出现"数学/统计" 删, agri 出现"文本阅读" 删)
- ❌ deep_study CS/金融 12% (改 arts 真实: 剧院/画廊/工作室, agri 真实: 农科院/种业/合作社)
- ❌ curriculum 公共必修填专业课 (高数/英语/思政/制图 才是公共必修)

---

## 🎯 Phase 2: 5 篇 Synth+Audit (估时 ~1.5h, ¥25)

| slug | 当前状态 | 行动 |
|------|---------|------|
| **ophthalmology** | 缺 JSON | synth + audit |
| **smart-grid-information-engineering** | 缺 JSON | synth + audit |
| **global-health** | 缺 JSON (commit 9818866 mobile 已 render) | synth + audit |
| **naval-architecture-and-ocean-engineering** | JSON 存但 5 audit null | 重新 audit (可能 irreducible) |
| **slug** | placeholder slug | 删 placeholder entry |

**Synth 模板** (沿用 Day 13 gap-fill 范式):
- 用 `scripts/batch_synth.py` (已存在)
- 18 字段必填 (Day 17 REQUIRED_FIELDS)
- m3 audit target ≥7

---

## 📋 任务拆分 (3 worker 并行)

### Worker A: arts 7 篇 polish (wt-polish-arts)
```bash
for slug in animation acting digital-performance-design digital-theatre \
  intelligent-imaging-art cultural-relics-conservation-restoration popular-music; do
  python3 scripts/batches/content_audit.py --slugs ${slug}:arts
  # → audit 报告 + 标 weak field
  # → hand-write Tier 1/2 fix
done
```

### Worker B: agri 2 篇 polish (wt-polish-agri)
```bash
for slug in apiculture facility-agriculture-science-engineering; do
  python3 scripts/batches/content_audit.py --slugs ${slug}:agri
  # → 标 weak field → hand-write fix
done
```

### Worker C: 5 篇 synth + audit (wt-synth)
```bash
# 先删 placeholder slug
python3 scripts/update_audit_registry.py --remove-slug slug

# synth 3 篇缺 JSON (用 batch_synth.py)
python3 scripts/batch_synth.py --slugs ophthalmology smart-grid-information-engineering global-health
# 重 audit naval-arch (5 audit 但 null)
python3 scripts/batches/content_audit.py --slugs naval-architecture-and-ocean-engineering:eng
```

---

## 🛡️ 安全 / 验收

| 风险 | 缓解 |
|------|------|
| Tier 2 重写 variance stuck | 接受 6-7 分 (不追死磕), 标 irreducible |
| synth 缺数据 | 用 麦可思 2024 + 教育部 学科目录 真实数据 |
| 多 worker 并发 registry 冲突 | 各自 worktree + amend 单一 commit |
| m3 API filter (gongan) | 5 篇均非 gongan, 0 风险 |

| 指标 | 目标 |
|------|------|
| Phase 1 完成 | 9 篇 polish (至少 5/9 promote ≥7) |
| Phase 2 完成 | 5 篇 score=null → ≥7 或 irreducible 标记 |
| 0 regressions | 8+ 418 (80.69%) 持, <6 0 持 |
| 1 commit | 单 commit push main |

---

## 📝 Commit Message 模板

```
fix(content): Day 18 arts+agri polish + 5 score=null synth (14 篇)

Phase 1 Polish (9 篇, 3 worker):
- arts 7: animation / acting / digital-performance / digital-theatre /
  intelligent-imaging-art / cultural-relics-conservation / popular-music
- agri 2: apiculture / facility-agriculture-science-engineering
- 至少 5/9 promote ≥7

Phase 2 Synth (5 score=null → ≥7 / irreducible):
- synth 3: ophthalmology + smart-grid-info + global-health
- re-audit 1: naval-architecture (5 audit null, 可能 irreducible)
- 删 placeholder 1: slug entry

Registry: 8+ 418 → X (target ≥428), 6-7 13 → Y, null 5 → 0
```

---

## ⏱️ 时间估算 (3 路并行 ~3h)

| 任务 | 估时 |
|------|------|
| A. arts 7 polish | 1-1.5h (wt-polish-arts) |
| B. agri 2 polish | 30min (wt-polish-agri) |
| C. synth 5 + audit | 1.5h (wt-synth) |
| 3 merge + 单 commit push | 30min (main) |
| **总** | **~3h** |

---

## 🔗 关联

- Day 16 D/E polish (本批 arts 沿用同样范式)
- Day 13 30 篇 gap-fill (synth 模式)
- Day 11.5 mobile responsive (synth 后必跑 render_mobile)
- Day 17 schema cleanup (synth 必走 18 字段 schema 校验)