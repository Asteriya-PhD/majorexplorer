# docs/_archive/ — 已完工的历史文档

> 归档策略: 已完成阶段的 PLAN/PROGRESS/HANDOFF 不删除, 但移到 `_archive/2026-Q2/` 减少 docs/ 噪音.
> 活跃文档保持在 `docs/` 顶层: PIPELINE / DECISIONS / AGENTS / ARCHITECTURE / DEPLOY* / 当前 HANDOFF.

## 2026-Q2/ (2026-04 ~ 2026-06)

### Day 3 阶段 (2026-06-17 ~ 2026-06-18)

| 文档 | 归档原因 |
|------|---------|
| `HANDOFF_day3_team_a.md` (v1) | v1 已完工, 被 v2 替代 |
| `HANDOFF_day3_team_a_v2.md` | v2 已完工, 被 below8 接力 |
| `HANDOFF_day3_team_a_below8.md` | below8 已完工, 合并到 Day 4 |
| `PROGRESS.md` | 早期总进度, 已被 day3_team_b 替代 |
| `PROGRESS_day3.md` | Day 3 阶段进度, 完结 |
| `PROGRESS_day3_team_b.md` | Day 3 Team B 阶段进度, 完结 |
| `PLAN_day3_dual_team.md` | Day 3 早期 A+B 计划, 调整为 3 team |
| `PLAN_day3_team_b_handcode.md` | 仍活跃 (任务清单) |
| `PLAN_field_fix_pipeline.md` | 3 防线方案, 已被 PIPELINE v1.2 收录 |

### Day 2 阶段 (2026-06-15 ~ 2026-06-16)

| 文档 | 归档原因 |
|------|---------|
| `PLAN_day2_cross_disciplinary_50.md` | 50 篇跨学科计划, 完工 |
| `PLAN_batch2.md` | Batch 2 计划, 完工 |
| `chsi-name-normalize-report.md` | 一次性 normalize 报告, 已落地 |
| `chsi-premium-diff-report.md` | 一次性 diff 报告, 已落地 |

### Day 1 阶段 (2026-06-11 ~ 2026-06-14)

| 文档 | 归档原因 |
|------|---------|
| `SYNTH_AGENT_PLAN.md` | 早期 Agent 流水线, 已废弃 (走手写) |
| `TRADITIONAL_BATCH_PLAN.md` | 早期批量生产方案, 已落地 |
| `SYNTH_SCHEMA.md` | 早期 schema 文档, 已被 PIPELINE 替代 |

## 索引

- 活跃: `docs/PIPELINE_major_quality.md` (CLAUDE.md 引用, 9 步流水线 + 4 anti-pollution)
- 活跃: `docs/HANDOFF_day3_team_b_d_e_f.md` (D/E 阶段最新)
- 活跃: `docs/PLAN_day3_team_b_handcode.md` (当前 batch 任务)
- 活跃: `docs/DECISIONS.md` (累计决策日志)
- 活跃: `docs/AGENTS.md` / `ARCHITECTURE.md` / `DATA.md` / `DEPLOY*.md`

## 何时从 archive 调出

- 需要复现某次 polish (5→8) 路径 → 找对应 HANDOFF
- 决策冲突需要查依据 → 找对应 PLAN
- 复盘 day3 流水线演化 → 读 3 份 HANDOFF_day3_team_a* 演进
