# 20260630 Phase BC+ — 剩余 23 篇 6-7 + Insurance Polish + Schema Sweep

> **承接**: 20260630 (Day 57) Phase B+C 完工 (8+ 600→608, <6 4→0)
> **当前**: registry `currently_6-7` = 23 篇 (irreducible-7 flag 已标, 但 registry schema 反向派生丢了 flag)
> **新命名约定**: `YYYYMMDD_phase_*.md` (无 Day N 前缀)

---

## 🎯 目标

1. **Registry flag 持久化修复** — rebuild 现在丢 flag 字段,29 篇 irreversible-7 标记全部失效 (registry 显示 `flag=''`)
2. **Insurance salary 倒挂修复** — Phase B 候选 m3 给 7/10, p25 5年=26万 > 10年+=20万致命矛盾
3. **23 篇 6-7 选 5-10 篇 Polish 推 8+** — 按 m3 audit_count 排序, 选 audits=9-11 (上限 ROI), audits≥13 的标 irreducible-7 真 stuck
4. **Schema sweep** — 普查 625 篇 major JSON 的常见 schema 怪癖 (credits/alumni source/theme_color object 5+ 处)
5. **目标**: 8+ 608 → ≥615 (98.4%), 6-7 23 → ≤15

**总估**: 1 session (~2-3h, ~¥10-20, 3-5 commits)

---

## 📋 4 大块任务 (按 ROI 排)

### 🔴 Block 1: Registry flag 持久化修复 (15 min, 必做)

**根因**: `update_audit_registry.py --rebuild` 从 `test_results/content_audit_*.json` 反推 major 状态, 但 audit JSON 不带 flag 字段 (m3 audit 不生成 flag).

**当前数据**:
```bash
$ python3 -c "..."  # 看 registry.majors.<slug>.flag
# 29 篇 (28 Phase B + 1 Phase C/其他) flag=''
```

**修复方案**:
- 改 `update_audit_registry.py` 在 rebuild 时从 `curated/<slug>.json` 读 `flag` 字段 (如果存在) 合并到 registry entry
- 或者: 在 audit JSON 里手填 flag (registry 派生时优先读 audit JSON → fallback curated JSON)

**执行**:
```python
# scripts/audit/update_audit_registry.py --backfill-flag
# 或加新参数: --include-flag (默认 True)
```

**验收**: 28-29 篇 irreducible-7 在 registry.majors.<slug>.flag 里能看到

---

### 🔴 Block 2: Insurance salary 倒挂修复 (10 min, 必做)

**当前 (audit 给 7/10):**
```json
"salary": {
  "5年经验 (持证/资深核保)": {"p25": 26, "p50": 40, "p75": 70, "yoy": 8},
  "10年+ (持证/资深核保)":  {"p25": 20, "p50": 50, "p75": 70, "yoy": 7}
}
```

**P25 5年 26 → 10年 20 是倒挂** (资深应高于中期)

**修复**: 把 10年+ p25 调到 40-45 (保守合理区间)

**单 commit + audit verify ≥7**。

---

### 🟡 Block 3: 23 篇 6-7 选 5-10 篇 Polish (1.5-2h, ¥10-15)

**按 audit_count 升序 (低=真硬伤 ROI 高)**:

| # | slug | audits | 候选策略 |
|---|------|--------|----------|
| P1 | civil-law-jurisprudence | 9 | 民法-9 audits 可能真 stuck, 试 polish |
| P2 | intelligent-sports-engineering | 9 | 跨学科新专业, 可能真硬伤 |
| P3 | marine-information-technology | 9 | 海洋+IT 交叉, 可能 schema 问题 |
| P4 | applied-chinese | 9 | 应用中文小众, 可能 stuck |
| P5 | science-education | 9 | 师范类, 调研员流向 |
| P6 | stomatology | 9 | 口腔医学热门, 一定有真硬伤可修 |
| P7 | flight-technology | 10 | 飞行技术复合, 体检/政审硬门槛 |
| P8 | supply-chain-management | 10 | 商科热门, 可推 |
| P9 | visual-communication-design | 10 | 艺术类, 设计院/广告去向 |
| P10 | medical-imaging | 11 | 医学影像热门, 一定真硬伤 |
| ~~skip~~ | accounting | 11 | 大会计, variance stuck 风险高 |
| ~~skip~~ | ndebele | 17 | 小语种 stuck |
| ~~skip~~ | bionic-science-engineering | 15 | stuck |
| ~~skip~~ | safety-engineering | 15 | stuck |
| ~~skip~~ | engineering-mechanics | 13 | stuck |
| ~~skip~~ | intelligent-vehicle-engineering | 13 | stuck |
| ~~skip~~ | industrial-intelligence | 13 | stuck |
| ~~skip~~ | agricultural-intelligent-equipment | 13 | stuck |
| ~~skip~~ | fintech | 12 | stuck |
| ~~skip~~ | audiology-speech-rehabilitation | 12 | stuck |
| ~~skip~~ | chinese-veterinary-medicine | 12 | stuck |
| ~~skip~~ | marine-fishery-science-technology | 11 | stuck |

**期望**: 5-10 篇 polish 中 3-5 篇 promote ≥8 (50% conv, Day 16 Tier 2 ROI 12/14=85% 高, 但这里都是单字段 fix ROI 中等)

**执行**:
```bash
# 每篇 8-12 min, 并行 3 worker worktree
LLM_PROVIDER=m3 set -a && source .env && set +a
python3 scripts/batches/content_audit.py --slugs \
  civil-law-jurisprudence:law intelligent-sports-engineering:eng \
  marine-information-technology:eng applied-chinese:humanities \
  science-education:education stomatology:medicine \
  flight-technology:eng supply-chain-management:management \
  visual-communication-design:arts medical-imaging:medicine
```

**每个 polish 后**: m3 audit verify ≥7 才 commit, 否则 skip 标 irreducible-7

---

### 🟢 Block 4: Schema sweep (30 min, ¥0)

**普查 625 篇 major JSON, 找常见 schema 怪癖**:

```python
# patterns to check:
1. curriculum.credit 是 string "3" 而非 int 3
2. alumni_quotes 用 school 字段而非 source
3. theme_color 是 string 而非 {primary, accent, soft} object
4. top_companies 缺 salary/headcount 字段
5. salary key 末尾 ":" + " {" (Day 57 JSON parse 致命坑)
6. summary vs lede 完全重复
7. deep_study sum ≠ 100
8. lede 字段缺失 (用 overview_v2.lede fallback)
9. discipline/ menjia_moe 缺失
```

**Python one-pass script** 生成 `docs/SCHEMA_SWEEP_20260630.md`:
- 每类怪癖列出 affected slugs
- 自动 fix 安全项 (credit string→int, alumni school→source, theme_color string→object)
- 标记 需人工 review 项 (salary 倒挂, lede 冗余)

**总 fix 数**: 估计 10-30 篇需要 schema fix (与 Block 3 5 篇 polish 重叠, 取并集)

---

## 🔁 流水线 (复用 Day 57 经验)

```
1. Block 1 (15 min): registry flag backfill (scripts/audit/update_audit_registry.py 改 5 行)
2. Block 2 (10 min): insurance salary 倒挂修复 + 单 commit
3. Block 3 (1.5-2h): 9 篇 polish (3 worker worktree 并行, 每篇 12 min)
   每篇: m3 audit issues → surgical fix → render → audit verify ≥7 → commit
   stuck (verify <7 二次) → 标 irreducible-7
4. Block 4 (30 min): schema sweep Python script → 自动 fix 安全项 → 单 commit
5. 最终: registry sync + push + stats 验证
```

---

## 📊 验收标准

| 指标 | Day 57 完工 | 目标 | 最低 |
|------|-----|-----|-----|
| 8+ | 608 (97.3%) | ≥615 (98.4%) | ≥611 (97.8%) |
| 6-7 | 23 | ≤15 | ≤18 |
| 7-8 | 8 | 10-15 | 12 |
| <6 | 0 | 0 | 0 |
| registry flag 持久 | ❌ 丢 | ✅ 修复 | - |
| insurance m3 | 7/10 | ≥7 | ≥7 |
| 平均 m3 分 | 8.5+ | 8.5+ | 8.4 |

---

## 🐛 5 个已知坑 (从 Day 57 移植)

1. **JSON key 不要 `:` 结尾** — salary 用 `-` 替代 `(...)`
2. **deploy.sh 后台不稳** — 手动 `git add && git commit && git push`
3. **m3 variance 极强** — surgical patch 常 ≥ Tier 2 重写
4. **registry stats 滞后** — 必跑 `--rebuild`
5. **audit_registry.py 路径** — `scripts/audit/`

---

## 🎯 起手命令 (新 session)

```bash
# 1. 读 plan
cat docs/PLAN_20260630_phase_bc_plus.md

# 2. 验当前状态
python3 scripts/audit/update_audit_registry.py --stats

# 3. Block 1: registry flag backfill (改 update_audit_registry.py 加 5 行)
# 4. Block 2: insurance salary fix
# 5. Block 3: 9 篇 polish (3 worker worktree 并行)
# 6. Block 4: schema sweep
```

**关键决策点 (新 session 拍板)**:
- Block 3 选哪 5-10 篇? (默认: P1-P10 audits=9-11 按 ROI 排, 可调)
- Block 4 schema sweep 阈值: 自动 fix vs 人工 review 切分?
- registry flag backfill: 改脚本 vs 加新参数?

---

## 📁 命名约定 (新规则)

**Plan 文件**: `YYYYMMDD_phase_*` 或 `YYYYMMDD_session_a/b/c_*` (同日多 session 后缀)
- 例: `20260630_phase_bc_plus.md` (本文档)
- 例: `20260630_session_a.md` / `20260630_session_b.md` (同日多次)

**Memory 文件**: `YYYYMMDD-*` kebab-case
- 例: `day57-phase-bc-complete-2026-06-30.md` (旧, 本次保留)

**Session title**: 无 Day N, 直接 `/goal "<plan 路径>"`
