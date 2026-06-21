# Day 18.5 Plan: 8 7-8 polish + 5 null resolve (13 篇)

> **日期**: 2026-06-21 重开 session  
> **前置**: Day 18 pushed (2b6b73ea), 8+ **422/476 (88.66%)** 7-8 48 (40 irred) / 6-7 0 / <6 0 / null 5  
> **目标**: 13 篇 (Phase A 8 polish + Phase B 5 null resolve), ~2h 总投入

---

## 🎯 Phase A: 8 篇 7-8 polish (估时 ~1.5h)

8 个 7-8 未标 irreducible (audit_count 低, 高 promote 概率):

| slug | audits | discipline | notes |
|------|--------|-----------|-------|
| marine-robotics (海洋机器人) | 2 | 08 | 新 audit, 可能 promote |
| materials-science-engineering (材料科学与工程) | 2 | 08 | 新 audit |
| 050200 (俄语/英语) | 3 | 05 | CHSI stub |
| 050210 (菲律宾语) | 3 | 05 | CHSI stub |
| chinese-international-education (汉语国际教育) | 10 | 05 | variance stuck? |
| additive-manufacturing-engineering (增材制造) | 6 | 08 | Day 16 E polished |
| postal-management (邮政管理) | 5 | 12 | Day 16 C polished |
| intelligent-perception-engineering (智能感知) | 4 | 08 | 新 audit |

**Tier 策略**:
- Tier 1 (5-10min): 补 weak field (典型: lede 钩子 / pitfalls 6-7 条 / alumni 具名)
- Tier 2 (15-20min): 重写 (P0 参考)
- Tier 3: irreducible-7 标 (如果 stuck)

**预期**: 5/8 promote ≥8, 2-3 irreducible-7

---

## 🎯 Phase B: 5 null resolve (估时 ~30min, ¥5)

| slug | 当前 | 行动 |
|------|------|------|
| slug | 缺 JSON + 1 audit | 删 placeholder |
| ophthalmology | 缺 JSON + 1 audit | 删 phantom (真 = ophthalmology-optometry) |
| smart-grid-info | 缺 JSON + 1 audit | 删 phantom (真 = smart-grid-engineering) |
| global-health | JSON 存 + 1 audit null | 重 audit (m3 parse error) |
| naval-architecture | JSON 存 + 5 audit null | 标 irreducible-7 (stuck ≥4) |

**预期**: 5/5 resolved, null 5→0

---

## 📋 任务拆分 (2 worker 并行)

### Worker A: 8 篇 polish (wt-polish-7-8)
```bash
for slug in marine-robotics materials-science-engineering 050200 050210 \
  chinese-international-education additive-manufacturing-engineering \
  postal-management intelligent-perception-engineering; do
  # 读 JSON → m3 audit → hand-write fix → re-audit
done
```

### Worker B: 5 null resolve (wt-null-resolve)
```bash
# 删 3 phantoms 直接编辑 registry
python3 scripts/update_audit_registry.py --remove-slug slug
# (or direct JSON edit per Day 18 Worker C finding)

# 重 audit 2
python3 scripts/batches/content_audit.py --slugs global-health:medicine
python3 scripts/batches/content_audit.py --slugs naval-architecture-and-ocean-engineering:eng
```

---

## 🛡️ 安全 / 验收

| 风险 | 缓解 |
|------|------|
| m3 API 超时 (Worker A 70min) | Tier 1 优先, accept variance |
| registry phantom 删除 format | Day 18 Worker C 已确认需直接 JSON edit |
| 8 篇 polish 边际效用 (Day 8 教训) | 优先 audit_count<5 高 promote 概率 |

| 指标 | 目标 |
|------|------|
| Phase A | 5/8 promote ≥8 (62.5%) |
| Phase B | 5/5 null → resolved |
| **0 regressions** | <6 0 持, 8+ 不掉 |
| **1 commit** | 单 commit push main |

---

## 📝 Commit Message 模板

```
fix(content): Day 18.5 polish 8 7-8 + resolve 5 null (13 篇)

Phase A Polish 8 篇 7-8 (wt-polish-7-8):
- marine-robotics / materials-sci-eng / 050200 / 050210 /
  chinese-international-education / additive-mfg /
  postal-management / intelligent-perception
- X/8 promote ≥8, Y/8 irreducible-7 标

Phase B Resolve 5 null (wt-null-resolve):
- 删 3 phantom: slug / ophthalmology / smart-grid-info
- 重 audit global-health → 8/10 优秀
- 标 naval-architecture irreducible-7

Registry: 8+ 422 → Z, null 5 → 0, <6 0 持
```

---

## ⏱️ 时间估算 (2 路并行 ~2h)

| 任务 | 估时 |
|------|------|
| A. 8 polish | 1.5h (wt-polish-7-8) |
| B. 5 null resolve | 30min (wt-null-resolve) |
| merge + push | 30min (main) |
| **总** | **~2h** |

---

## 🔗 关联

- Day 16 D/E polish (本批 arts/agri 沿用同样范式)
- Day 18 synth (本批 null resolve 沿用 phantom detection pattern)
- Day 17 schema cleanup (新增 18 字段 schema 校验)