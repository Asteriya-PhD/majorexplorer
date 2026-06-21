# Day 21 Plan: 6 NEW + 2 stuck-7 polish + Variance verify 6 borderline 8+

> **日期**: 2026-06-21 重开 session  
> **前置**: Day 20 pushed (9d25f53f), 8+ **428/474 (90.30%)** 7-8 46 / 6-7 0 / <6 0 / null 0  
> **目标**: Phase A 推 6 NEW + 2 stuck-7 → 8+ 比例回 ≥90.7%; Phase B variance verify 6 8+ borderline 真实

---

## 🎯 Phase A: Polish 8 篇 (估时 ~1.5h)

**6 NEW score=null (merge conflict 未同步)**:
1. theoretical-applied-mechanics (080101) - style=eng
2. mechanical-design-manufacturing-automation (080202) - style=eng
3. material-forming-control-engineering (080203) - style=eng
4. plant-science-technology (090104) - style=agri
5. chinese-linguistics (050102) - style=humanities
6. teaching-chinese-foreign-language (050103) - style=humanities

**2 stuck-7 (not yet irreducible)**:
7. mechatronic-engineering (080204) - score=7, audits=4 - style=eng
8. horticulture (090102) - score=7, audits=4 - style=agri

**Tier 策略**: 
- 6 NEW: m3 audit (应有 7-8, 同步 registry) → Tier 1 补 weak
- 2 stuck-7: Tier 2 重写 weak field (P0 参考 electronic-science-technology / cultural-relics-museology)

**预期**: 5/8 promote ≥8 (62.5%), 3 stuck 标 irreducible

---

## 🎯 Phase B: Variance Verify 6 borderline 8+ (估时 ~30min ¥5)

6 8+ with audits<5 (potential variance stuck):

1. optoelectronic-information-science-engineering (audits=4)
2. internet-of-things-engineering (audits=4)
3. polymer-materials-engineering (audits=3)
4. materials-forming-control-engineering (audits=3)
5. measurement-control-technology-instruments (audits=3)
6. information-security (audits=4)

**Workflow**: 跑 m3 audit 取多次结果 (3 次), 若稳定 8+ → 标 "variance-verified"; 若有 ±1 → 标 irreducible-8

---

## 📋 任务拆分 (2 worker 并行)

### Worker A: Phase A polish 8 篇 (wt-day21-polish)
```bash
for slug in theoretical-applied-mechanics mechanical-design-manufacturing-automation \
  material-forming-control-engineering plant-science-technology \
  chinese-linguistics teaching-chinese-foreign-language \
  mechatronic-engineering horticulture; do
  python3 scripts/batches/content_audit.py --slugs ${slug}:{style}
  # → Tier 1/2 fix as needed
done
```

### Worker B: Phase B variance verify 6 篇 (wt-day21-verify)
```bash
for slug in optoelectronic-information-science-engineering internet-of-things-engineering \
  polymer-materials-engineering materials-forming-control-engineering \
  measurement-control-technology-instruments information-security; do
  python3 scripts/batches/content_audit.py --slugs ${slug}:{style}  # 3 次取 median
done
```

---

## 🛡️ 安全 / 验收

| 风险 | 缓解 |
|------|------|
| Merge conflict 残留 (6 NEW score=null) | Worker A m3 audit 自动 sync |
| Phase B variance verify 假阴性 | 取 3 次 audit median |
| m3 API 超时 | accept variance |

| 指标 | 目标 |
|------|------|
| Phase A | 5/8 promote ≥8 (62.5%) |
| Phase B | 6/6 variance verify 确认 ≥8 |
| **0 regressions** | <6 0 持 |
| **1 commit** | 单 commit push main |

---

## 📝 Commit Message 模板

```
fix(content): Day 21 polish 6 NEW + 2 stuck-7 + variance verify 6 (16 篇)

Phase A Polish 8 篇 (wt-day21-polish):
- 6 NEW score=null sync (merge conflict 修复):
  theoretical-applied-mechanics / mechanical-design-mfg-automation /
  material-forming-control / plant-science-technology /
  chinese-linguistics / teaching-chinese-foreign-language
- 2 stuck-7 polish:
  mechatronic-engineering / horticulture

Phase B Variance Verify 6 8+ borderline (wt-day21-verify):
- optoelectronic-info-science / IoT-engineering /
  polymer-materials / materials-forming-control /
  measurement-control / information-security

Registry: 8+ 428 → X (target ≥431), 7-8 46 → Y
```

---

## ⏱️ 时间估算 (2 worker 并行 ~1.5h)

| 任务 | 估时 |
|------|------|
| A. 8 polish | 1.5h (wt-day21-polish) |
| B. 6 variance verify | 30min (wt-day21-verify) |
| merge + push | 30min (main) |
| **总** | **~2h** |

---

## 🔗 关联

- Day 16 D/E polish (m3 audit + Tier 1/2 fix 范式)
- Day 19 variance verify (Day 14.5 R2 R3 模式)
- Day 17 schema cleanup (18 字段 schema 校验)