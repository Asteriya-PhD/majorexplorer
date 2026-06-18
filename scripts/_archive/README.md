# scripts/_archive/ — 已完工的一次性脚本

> 归档策略: 一次性 batch 任务脚本 (Day 3 hand-curate x 篇) 移到 `_archive/2026-Q2/`,
> 节省 scripts/ 噪音. 活跃工具保持在 `scripts/` 根 + `scripts/batches/`.

## 2026-Q2/ (2026-04 ~ 2026-06)

### Day 3 Team A hand-curate (2026-06-17)

| 脚本 | 处理 | 备注 |
|------|------|------|
| `hand_curate_day3.py` | 6+3 篇手改 (audit 5.0 + top_schools 污染 + synth fail) | Day 3 早期版 |
| `hand_curate_day3_part2.py` | 38 篇手写 (未手改) | 格式紧凑版 |
| `hand_curate_day3_part3.py` | 12 篇 Batch 1 (medicine+eng+cs+sci+agri) | 紧凑模板 |
| `hand_curate_day3_part4.py` | 12 篇 Batch 2 | 同模板, 不同 slug |
| `hand_curate_day3_part5.py` | 12 篇 Batch 3 FINAL | 同模板 |
| `hand_curate_b1.py` | 早期 batch 实验 | — |
| `hand_curate_b2.py` | 早期 batch 实验 | — |
| `hand_curate_b3.py` | 早期 batch 实验 | — |
| `hand_curate_b4.py` | 早期 batch 实验 | — |
| `hard_fix_remaining.py` | 后期 hard-fix (schema 怪癖手动修) | 已完工 |

## 何时调出

- 需要复现某次 hand-curate (改 X 篇怎么改的) → 找对应 part 文件
- audit 历史跨查 → 已移至 `data/audit_registry.json` (git tracked 单一真相)
- 后续 Day 4+ 大 batch 时参考 part3 紧凑模板

## 为什么不删

- 已 commit 进 git history, 删除仅本地收益
- 未来可能需要回看"我们怎么手改 X 篇" (audit 决策依据)
- 跟 docs 归档策略保持一致

## scripts/batches/ 仍在用的工具 (活跃, 不归档)

| 工具 | 用途 |
|------|------|
| `normalize.py` (300K) | **核心** LLM 输出 schema 归一器, render.py 依赖. **下次大改再拆** |
| `content_audit.py` | m3 audit 主入口 (单篇/批量) |
| `audit_all.py` | 全量 audit (老模式) |
| `tier3_opus_30.py` | Tier 3 兜底 (Opus 重写) |
| `smart_audit.py` ⭐ | **在 scripts/ 根**, Layer 1+2 智能路由 |
| `fix_*.py` 多个 | 已知 schema 怪癖 fix (偶尔用) |
| `auto_fix_pipeline.py` | 字段级 auto-fix 流水线 |
| `contam_dict.py` | 强污染检测 |
| `upgrade_quality.py` | 通用 quality 升级 |
| `fix_employment_direction.py` | employment 字段专修 |
| `hand_curate.py` (19K) | 通用 hand-curate 入口 (active) |
| `schema_fix_v4.py` | schema v4 修复 |
| `fix_day3_audit_v3/v4/v5.py` | 迭代 fix 工具, 偶尔用 |

## 备注

> normalize.py 300K 是大单文件, **下次大改 (LLM schema 重设计时) 再拆**.
> 当前不拆, 风险 (改坏影响所有 LLM 输出归一) > 收益 (300K 不是磁盘问题, 是 review 难度).
> 详见本次 session memory: scripts-archive-2026-06-18.
