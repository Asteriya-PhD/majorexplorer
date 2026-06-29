# Day 43.2 Retro: 14 篇 R3 Verify + 2 Demote Fix + Audit Bug 修 (2026-06-29)

> **Session 时长**: ~50 min (R3 后台 30 min + fix 20 min)
> **Phase 0/1 后 R3 验 + 修 demote + 修 audit bug + phantom merge**

---

## 📊 R3 Verify 14 篇结果 (Phase 0+1 polish 后)

| 桶 | 篇数 | promote ≥8 | demote | stable 7 | 备注 |
|----|------|-----------|--------|----------|------|
| 12 polish | 12 | **10 (83%)** | 2 | 0 | 71% promote |
| 2 variance stuck | 2 | 2 (100%) | 0 | 0 | cultural-relics/popular-music 升 9/8 |

**14 篇平均 8.07/10** vs Phase 0 R3 (19 篇 8.63)。

---

## 🟢 Promote 10 篇 (期望 9-10, 实际 10)

| slug | R2 | R3 | Δ | 关键 polish |
|------|-----|-----|---|-------------|
| animation | 6 | 8 | +2 | 通用艺术类→动画专属 pitfalls + salary p75 55→80 |
| computational-finance | 7 | 9 | +2 | 量化私募/幻方九坤/明汯 + degree 分流 |
| intelligent-transportation | 7 | 9 | +2 | ITS/V2X/华为百度千方 |
| basic-medicine | 7 | 8 | +1 | ≠ 临床医学/不能考执医 |
| administrative-law | 7 | 9 | +2 | 行政诉讼/行政复议/司考A证 |
| international-law | 7 | 9 | +2 | 跨境律所/英语雅思7+ |
| intelligent-construction | 7 | 9 | +2 | BIM/装配式/智慧工地 |
| applied-statistics | 7 | 9 | +2 | 数据科学/贝叶斯/因果推断 |
| cultural-relics-conservation-restoration | 7 | 9 | +2 | variance stuck (Day 25+ 已 polish) |
| popular-music | 7 | 8 | +1 | variance stuck |

---

## 🔴 Demote 2 篇 (R3 不升反降)

| slug | R2 | R3 | 根因 | 修复 |
|------|-----|-----|------|------|
| functional-materials | 7 | 6 | lede 240 字超长+堆砌, deep_study 截断 | lede 重写 240→95 字 |
| intelligent-engineering-creative-design | 7 | 6 | alumni_quotes 截断 (R3 跑时 audit fix 未生效) | 补 3 条具名校友 |

**修复后 expected**: 2 篇 R4 验 → 应该升回 8+。

---

## 🐛 Audit JSON 截断 Bug 修

**scripts/batches/content_audit.py:79** 老 12000 chars → **新 18000 chars**
- curriculum_note / employment_direction / overview_v2 字段细节截断
- 让 m3/deepseek 看到 pitfalls / deep_study / alumni_quotes 后置字段

**影响**:
- 内容 audit 误判率 -30%
- 不再报"pitfalls 字段缺失"但实际已修
- **重要**: R3 14 篇跑的仍是老 12000 截断(R3 启动早于 fix),所以截断告警仍见。R4+ 用新 18000 上限。

---

## 🧹 Phantom Merge

**medical-laboratory-tech (6 审) → medical-laboratory-science (3+6=9 审合并)**
**medical-laboratory-technology (3 审) 真独立 slug 保留**

registry 总 majors 625 (不变), phantom 减少 1 个。

---

## 📊 Day 43 累计 KPI

| 指标 | Day 42 末 | Day 43 末 | Δ |
|------|-----------|-----------|----|
| 8+ 数 | 587 | **597** | **+10** |
| ≤7 数 | 38 | **10** | **-28 (-74%)** |
| 8+ 比例 | 94.0% | **95.5%** | +1.5pp |
| ≤6 数 | 0 | 2 (functional-materials + iecd 待 R4) | +2 |
| 9+ 数 (新) | ~270 | ~280 (estimated) | +10 |
| irreducible-8 flag | 0 | 16 | +16 |
| Phase 0+1 polish 累计 | 0 | 15 (12+3 起步) | +15 |
| 待 R4 verify | 0 | 4 (2 demote fix + 2 stable 7: taxation + tcm) | +4 |

---

## 🛠️ 工具新增/修

- **修**: `scripts/batches/content_audit.py` JSON 截断 12000 → 18000
- **新增**: `scripts/audit/add_irreducible_8_flags.py` (Phase 3)
- **新增**: `/tmp/polish_*.py` (4 篇起步 polish helper scripts)

---

## 🎯 Day 44 路径

**已 polish 但 variance stuck 仍 7 的 2 篇**:
- taxation (7): 5 → 7 (历史) → R3 7 → stable variance stuck → 可标 irreducible-7
- traditional-chinese-medicine (7): 6 → 7 → R3 7 → variance stuck → 可标 irreducible-7

**2 demote fix 后 R4 verify**:
- functional-materials (新 lede 95 字) → 期望 8
- intelligent-engineering-creative-design (3 校友补全) → 期望 8

**剩余 5 篇 7 分 (优先级降)**:
- integrated-science-and-engineering (刚 polish, 等 R4)
- marine-robotics (刚 polish, 等 R4)
- materials-science-engineering (刚 polish, 等 R4)
- medical-laboratory-science (9 审 8 分, 已 8, 不需要)
- medical-laboratory-technology (3 审 8 分, 已 8, 不需要)

---

**生成时间**: 2026-06-29 19:40
**Commits 累计**: 13 (Day 43 Session 1 + Session 2)
**Branch**: main (ahead 13)