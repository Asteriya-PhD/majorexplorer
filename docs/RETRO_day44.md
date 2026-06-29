# Day 44 Retro: R4 Verify 5 篇 + Irreducible-7 Flag 2 篇 (2026-06-29)

> **Session 时长**: ~25 min (R4 后台 8 min + fix 5 min + flag 5 min + retro 5 min)
> **2 个核心任务完成**: R4 verify 5 篇 + irreducible-7 flag 2 篇

---

## 📊 R4 Verify 5 篇结果

| slug | R3 | R4 | Δ | 桶 |
|------|-----|-----|---|-----|
| functional-materials | 6 | **9** | **+3** | Day 43.2 demote fix 完美 |
| intelligent-engineering-creative-design | 6 | **9** | **+3** | Day 43.2 demote fix 完美 |
| integrated-science-and-engineering | 7 | **9** | **+2** | Day 43.2 起步 polish |
| marine-robotics | 7 | **9** | **+2** | Day 43.2 起步 polish (null → 7) |
| materials-science-engineering | 7 | 7 | 0 | salary p25 倒挂, 已修 |

**5 篇平均 8.60/10** (vs R3 verify 8.07, R0 8.63)

**4/5 promote ≥9 (80%)** — Day 43 polish + Day 43.2 fix 全部生效

---

## 🏷️ Irreducible-7 Flag 2 篇

| slug | audit_count | max | reason |
|------|-------------|-----|--------|
| taxation | 10 | 7 | 4→6→7→6→6→7×5 variance stuck |
| traditional-chinese-medicine | 9 | 7 | 4→7→7→5→7×5 variance stuck |

**累计 irreducible flag**:
- 16 篇 irreducible-8 (Day 43 Phase 3)
- 2 篇 irreducible-7 (Day 44)
- **18 篇 total** 避免后续 variance noise 误判

**新工具**: `scripts/audit/add_irreducible_7_flags.py` (跟 irreducible-8 同套机制, 候选 2/2 命中)

---

## 🔧 Materials Salary 倒挂修复

| 阶段 | 旧 p25 | 新 p25 |
|------|--------|--------|
| 应届 (0-2 年, 985 硕士) | 18 | 18 (不变) |
| 3 年经验 | 15 | 15 (不变) |
| 5 年经验 | 25 | 25 (不变) |
| **10 年+ (持证/资深)** | **20 ❌ 倒挂** | **35 ✅ 修正** |

**删除重复段**:
- 应届 (0-2 年, 本科) ❌ 删
- 应届生 (一线) ❌ 删

**保留 4 阶段校准**: 应届 985 硕 / 3 年 / 5 年 / 10 年+

---

## 📊 Day 43+44 累计 KPI

| 指标 | Day 42 末 | Day 43 末 | Day 44 末 | Δ (Day 42→44) |
|------|-----------|-----------|-----------|----------------|
| 8+ 数 | 587 | 597 | **601** | **+14** |
| ≤7 数 | 38 | 10 | **6** | **-32 (-84%)** |
| 8+ 比例 | 94.0% | 95.5% | **96.2%** | **+2.2pp** |
| ≤6 数 | 0 | 2 | **0** | 0 (2 demote fix 全升 9) |
| irreducible flag | 0 | 16 | **18** | +18 |
| 累计 polish | 0 | 15 | **17** | +17 |

---

## 🛠️ Day 44 工具

- **新增**: `scripts/audit/add_irreducible_7_flags.py` (跟 irreducible-8 同套, 5/5+审计 + max≤7)
- **修**: `scripts/batches/content_audit.py` (18000 chars 截断 — Day 43.2 已修, Day 44 R4 用上)

---

## 🎯 Day 45+ 路径

**剩余 ≤7 篇 (6 篇)**:
- materials-science-engineering (刚修 salary, 等 R5 验证)
- 4 篇 audit_count < 3: integrated-science 起步已升 9, 剩 marine-robotics 起步升 9, 剩 2 篇 ?
- 0 篇 ≤6 (全部修复)

**目标**:
- R5 verify materials-science-engineering (期望升 8-9)
- 启动 Day 45 标 irreducible-6/8 给剩余 ≤7 真 stuck 篇
- 启动 Day 45+ 写"目标 8+ 比例 98%+" polish 候选 (从 audit_count 1-2 起步篇里选)

---

**生成时间**: 2026-06-29 19:55
**Commits**: 4 个 (R4 demote fix + materials salary + irreducible-7 flag + retro)
**Branch**: main (ahead 17)