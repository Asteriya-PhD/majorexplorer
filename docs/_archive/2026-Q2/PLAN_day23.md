# Day 23 Plan: 1 stuck-8 polish + 80 8+ variance verify

> **日期**: 2026-06-21 重开 session  
> **前置**: Day 22 pushed (994df5de), 8+ **434/479 (90.62%)** 7-8 45 (irred 45) / 6-7 0 / <6 0 / null 0  
> **目标**: 1 stuck-8 Tier 2 + 80 8+ variance verify (sample), 3 worker 并行 ~2-3h, ¥30-50

---

## 🎯 Phase A: Polish 1 stuck-8 (估时 ~30min)

**transportation-engineering** (irreducible-8, audits=2):
- Tier 2 完全重写 weak field (lede/pitfalls/employment_direction)
- 参考 P0 `electronic-science-technology.json`
- 目标: variance 稳定 8+ (移除 irreducible-8 标)

---

## 🎯 Phase B+C: Variance verify 80 8+ borderline (估时 ~2h ¥30)

**50 8+ audits=1 (新近 audit)**:
- 单次 audit rerun
- 检测 7 regression (1 个就升级)
- variance-verified tag

**30 8+ audits=2 (borderline)**:
- 2 次 audit rerun
- 检测 ±1 variance, 升级 irreducible-8 或 stable

**样本列表**: `/tmp/day23_verify_50.json` + `/tmp/day23_verify_30.json`

---

## 📋 任务拆分 (3 worker 并行)

### Worker A: Polish 1 (wt-day23-polish)
```bash
# Tier 2 重写 transportation-engineering
# Read JSON → hand-write fix → audit verify
python3 scripts/batches/content_audit.py --slugs transportation-engineering:eng
```

### Worker B: Variance verify 50 (wt-day23-verify-50)
```bash
# Read /tmp/day23_verify_50.json
# Loop 50 slugs, 1 audit each, detect regressions
for slug in $(cat /tmp/day23_verify_50.json); do
  python3 scripts/batches/content_audit.py --slugs ${slug}:{style}
done
```

### Worker C: Variance verify 30 (wt-day23-verify-30)
```bash
# Read /tmp/day23_verify_30.json
# Loop 30 slugs, 2 audits each for stability
for slug in $(cat /tmp/day23_verify_30.json); do
  for i in 1 2; do
    python3 scripts/batches/content_audit.py --slugs ${slug}:{style}
  done
done
```

---

## 🛡️ 安全 / 验收

| 风险 | 缓解 |
|------|------|
| m3 variance ±1 拉低 score | accept 7+ for borderline |
| m3 1026 filter (gongan/religious) | skip + mark filter-blocked |
| Tier 2 重写 variance stuck | 接受 7-8, irreducible-8 |

| 指标 | 目标 |
|------|------|
| Phase A | transportation-engineering score 稳定 ≥8 |
| Phase B | 50 audit reruns, detect 0-3 regressions |
| Phase C | 30 2-runs, variance-verified stable |
| **0 regressions** | <6 0 持 |
| **1 commit** | 单 commit push main |

---

## 📝 Commit Message 模板

```
fix(registry): Day 23 polish 1 + variance verify 80 8+ borderline

Phase A Polish (wt-day23-polish):
- transportation-engineering Tier 2 重写 → variance-stable 8+
- 移除 irreducible-8 标

Phase B Variance Verify 50 audits=1 (wt-day23-verify-50):
- X/50 stable 8+ (variance-verified)
- Y/50 regression detected (real issue → escalate)

Phase C Variance Verify 30 audits=2 (wt-day23-verify-30):
- A/30 stable 8+ (variance-verified)
- B/30 variance ±1 (irreducible-8 mark)

Registry: 8+ 434 (90.62%) → 434 (verified), 7-8 45 → C
```

---

## ⏱️ 时间估算 (3 worker 并行 ~3h)

| 任务 | 估时 |
|------|------|
| A. polish 1 | 30min (wt-day23-polish) |
| B. verify 50 | 2h (wt-day23-verify-50) |
| C. verify 30 | 1.5h (wt-day23-verify-30) |
| merge + push | 30min (main) |
| **总** | **~3h** |

---

## 🔗 关联

- Day 22 variance verify (15 篇 precedent)
- Day 16 D/E Tier 2 重写模式
- Day 17 schema cleanup (18 字段 schema 校验)