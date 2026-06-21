# Day 20 Plan: 30 篇新专业上线 (5 worker × 6 篇)

> **日期**: 2026-06-21 重开 session  
> **前置**: Day 19 收尾完成, 8+ **429/473 (90.70%)**, 0 ≤6, 0 null, 44 irreducible-7  
> **目标**: 30 篇全新专业上线, 5 worker 并行 (4-5h, ¥100-150), 候选按 13 门类 gap-priority 选

---

## 🎯 30 篇候选 (按 gap-priority, 全 new)

| Worker | 6 篇 | 门类 |
|--------|------|------|
| **A** | 理论与应用力学 / 工程力学 / 机械工程 / 机械设计制造及其自动化 / 材料成型及控制工程 / 机械电子工程 | 08 工学 #1-6 |
| **B** | 工业设计 / 过程装备与控制工程 / 车辆工程 / 汽车服务工程 / 机械工艺技术 / 微机电系统工程 | 08 工学 #7-12 |
| **C** | 管理科学 / 信息管理与信息系统 / 工程管理 / 房地产开发与管理 / 工程造价 / 保密管理 | 12 管理学 |
| **D** | 艺术史论 / 艺术管理 / 非物质文化遗产保护 / 音乐表演 / 音乐学 / 汉语言文学 | 13 艺术 + 05 文学 #1 |
| **E** | 农学 / 园艺 / 植物保护 / 植物科学与技术 / 汉语言 / 汉语国际教育 | 09 农学 + 05 文学 #2 |

---

## 📋 单 worker 流程 (每篇)

1. **Synth JSON** (5min): 用 `scripts/batch_synth.py --slugs {slug}` 或 hand-write 18 字段
2. **Render HTML** (1min): `python3 scripts/render_mobile.py` (bulk 自动)
3. **Audit verify** (3min): `python3 scripts/batches/content_audit.py --slugs {slug}:{style}` ≥7
4. **Tier 1 fix** (5-10min): 补 weak field (lede/pitfalls/alumni)
5. **Tier 2 retry** (15min): 重写 (P0 参考)
6. **Accept variance** (≤5min): stuck 6 标 irreducible-6

**每 worker 6 篇总估时**: ~1.5-2h

---

## 🛡️ 安全 / 验收

| 风险 | 缓解 |
|------|------|
| Synth 数据不准 | CHSI moe_code + 麦可思 2024 + 教育部 学科目录 |
| m3 API filter (gongan) | 30 篇均非 gongan, 0 风险 |
| 5 worker 并发冲突 | 各自 worktree + JSON 文件 disjoint |
| Tier 2 重写 variance stuck | 6/30 接受 6-7, 不追死磕 |
| 30 篇新 → 总比例短期下降 | 预期: 8+ ratio 90.70% → ~75% (新篇多数 6-7 起步), 后续 Day 21 polish 推回 |

| 指标 | 目标 |
|------|------|
| 单 worker 完成 | 6 篇 JSON + render + audit |
| **总产出** | 30 篇 JSON + 30 mobile HTML + 30 audit history |
| **0 break** | 已上线 473 篇不动 |
| **1 commit** | 单 commit push main |

---

## 📝 Commit Message 模板

```
fix(content): Day 20 30 篇新专业上线 (5 worker × 6 篇)

30 篇新候选按 13 门类 gap-priority 选 (08 工学 12 + 12 管理 6 + 13 艺术 5 + 09 农学 4 + 05 文学 3):

Worker A 08 工学 #1-6: 理论与应用力学 / 工程力学 / 机械工程 /
  机械设计制造及其自动化 / 材料成型及控制工程 / 机械电子工程
Worker B 08 工学 #7-12: 工业设计 / 过程装备与控制工程 / 车辆工程 /
  汽车服务工程 / 机械工艺技术 / 微机电系统工程
Worker C 12 管理学: 管理科学 / 信息管理与信息系统 / 工程管理 /
  房地产开发与管理 / 工程造价 / 保密管理
Worker D 13 艺术 + 05 文学 #1: 艺术史论 / 艺术管理 / 非物质文化遗产保护 /
  音乐表演 / 音乐学 / 汉语言文学
Worker E 09 农学 + 05 文学 #2: 农学 / 园艺 / 植物保护 /
  植物科学与技术 / 汉语言 / 汉语国际教育

每篇 18 字段 schema (Day 17 校验) + P0 案例参考 + m3 audit 验证 ≥7

Registry: 473 → 503 (+30), 8+ 比例短期可能下降 (新篇多 6-7 起步),
         后续 Day 21+ polish 推回 ≥8
```

---

## ⏱️ 时间估算 (5 worker 并行 ~4-5h)

| Worker | 任务 | 估时 |
|--------|------|------|
| A | 6 工学 #1-6 | 1.5-2h |
| B | 6 工学 #7-12 | 1.5-2h |
| C | 6 管理 | 1.5-2h |
| D | 5 艺术 + 1 文学 | 1.5-2h |
| E | 4 农学 + 2 文学 | 1.5-2h |
| merge + 单 commit push | 30min | main |
| **总** | **~5h** | 5 路并行 |

---

## 🔗 关联

- Day 4 E Phase 30 篇 (Day 4 batch 30 篇全新 major 全部上线, 7.67 avg)
- Day 13 30 篇 gap-fill (Day 13 polish + Gap-fill)
- Day 17 schema cleanup (18 字段 schema 校验)
- Day 19 variance verify (90.70% 基线)