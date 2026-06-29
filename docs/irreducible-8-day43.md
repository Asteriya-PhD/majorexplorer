# Day 43 Irreducible-8 Flag Report (2026-06-29)

> **目标**: 标记 ≥10 审仍 7-8 分篇, 避免后续 variance noise 误判
> **机制**: registry.majors[slug] 加 `tier: irreducible-8` + 原因 + 日期

---

## 📊 Flag 汇总

- **总标记**: 16 篇
- **标准**: audit_count ≥ 10 + current_score ∈ {7, 8} + max(audit_history.score) ≤ 8
- **拒绝 4 篇**: bioinformatics (R3 升 9) / digital-twin-technology (R3 升 9) / cross-border-ecommerce (历史 max=9) / intelligent-marine-equipment-engineering (历史 max=9)

---

## 📋 16 篇 list (按 audit_count 降序)

| # | slug | style | audit_count | current_score | max | irreducible_reason |
|---|------|-------|-------------|---------------|-----|---------------------|
| 1 | service-science-engineering | cs | 20 | 7 | 8 | variance stuck 5-8 across 20 audits |
| 2 | smart-agriculture | agri | 17 | 8 | 8 | R3 salary inverted 5-10y p25 vs 应届 (minor) |
| 3 | global-climate-change | sci | 16 | 8 | 8 | variance 6-8 across 16 audits |
| 4 | bionic-science-engineering | eng | 14 | 8 | 8 | variance 6-8 across 14 audits |
| 5 | advertising | humanities | 14 | 8 | 8 | variance 5-8, settled 8 since R11 |
| 6 | ndebele | humanities | 14 | 8 | 8 | 小语种 hard fact, cannot enrich |
| 7 | criminal-investigation | gongan | 14 | 8 | 8 | variance 6-8, mostly 7-8 since R8 |
| 8 | cyber-information-law | law | 12 | 8 | 8 | settled 8 since R4 |
| 9 | remote-sensing-science-technology | eng | 12 | 7 | 8 | variance 7-8, stuck at 7 in current |
| 10 | safety-engineering | eng | 11 | 8 | 8 | settled 8 since R8 (R1 was 3 outlier) |
| 11 | logistics-management | administration | 11 | 8 | 8 | variance 4-8, settled 8 since R9 |
| 12 | flight-vehicle-control | eng | 11 | 8 | 8 | variance 6-8 (5 errors before settling) |
| 13 | international-economic-cooperation | finance | 11 | 8 | 8 | variance 4-8, settled 8 since R10 |
| 14 | intelligent-vehicle-engineering | eng | 10 | 8 | 8 | settled 8 since R5 |
| 15 | postal-engineering | eng | 10 | 8 | 8 | settled 8 since R9 |
| 16 | numerical-foundation-science | sci | 11 | 8 | 8 | settled 8 since R8 (R3 verify confirmed) |

---

## 🚫 拒绝 4 篇 (不标 irreducible)

| slug | reason |
|------|--------|
| bioinformatics | R3 promote 8→9 (Day 43 Phase 0) |
| digital-twin-technology | R3 promote 8→9 (Day 43 Phase 0) |
| cross-border-ecommerce | 历史 max=9, 真能 promote ≥9 |
| intelligent-marine-equipment-engineering | 历史 max=9, 真能 promote ≥9 |

---

## ⚙️ 验证方法

**flag 后 polish 仍可能提升**:
- 若 R3+ audit 显示 score ≥9: 升级 `tier: null` + 移除 flag
- 若 R3+ audit 显示 score ≤6 (demote): 保留 flag (但关注 root cause)
- variance stuck 在 7-8: 保留 flag (本次目的)

**agent 决策规则**:
- 看到 `tier: irreducible-8` → 不重新 polish (除非用户明确要求)
- 看到 `tier: irreducible-8` + R3 audit 报告 ≥9 → 升级 tier=null
- 看到 `tier: irreducible-8` + R3 audit 报告 ≤6 → 查 polish 历史,标 variance stuck

---

## 🔧 工具

- `scripts/audit/add_irreducible_8_flags.py --dry-run` 预演
- `scripts/audit/add_irreducible_8_flags.py` 写入
- `jq '.majors | to_entries | map(select(.value.tier == "irreducible-8")) | length' data/audit_registry.json` 查 flag 总数

---

**生成时间**: 2026-06-29 19:25
**分支**: main
**registry version**: 1.1 (schema bump: + tier 字段)
**Phase 0 贡献**: 19 R3 verify, 12 promote 8→9 (63.2% conv)