# Day 2 计划: 跨学科 50 篇精品专业 (待 user 重开会话启动)

**日期**: 2026-06-16
**触发**: Day 1 v8 完工, 4 决策点全拍板
**用户拍板**: 都按推荐 (mimo 默认 + hard-code 兜底 + 30 篇/批 + 一键流水线 + 跨学科 50 篇)

---

## 1. 5 大决策点 (Day 1 已拍板)

| # | 决策 | 选择 | 原因 |
|---|------|------|------|
| 1 | Provider 默认 | **mimo (12min/50篇) + m3 字段级 fix 兜底** | mimo 速度 5x, 70% clean, 仍需 hard-fix 兜底 |
| 2 | 字段级 fix 策略 | **hard-code 前 10 篇 + mimo fix 后续** | 已知 LLM 永远会复发同源污染, 早期批次 hard-code 才能真干净 |
| 3 | 批量大小 | **30 篇/批** | 30/批 ≈ 30min synth + 30min fix + 10min render/deploy, 节奏舒服 |
| 4 | 流水线开关 | **synth→audit→fix 一键** (auto_fix_pipeline.py 加 --all flag) | 减少手动操作, 节省 50% 时间 |
| 5 | Day 2 范围 | **跨学科 50 篇** (工科/理科/医学/农学/人文/法学/管理 全覆盖, 防止单一 fallback 偏置) | 多学科验证 3 防线通用性, 扩 50 篇精品库 |

---

## 2. Day 2 启动清单 (按顺序)

### 阶段 1: 流水线一键化 (15min, 一次性)
- [ ] 把 `auto_fix_pipeline.py` 串到 `batch_synth.py` 加 `--auto-fix` flag
- [ ] 改 `normalize.py` 加 `--skip-normalize` 避免覆盖 hard-fix
- [ ] 改 `deploy_to_public.py` 加 `--force` 强制 rm + 同步
- [ ] 测试一链: 30 篇 synth → 30 篇 fix → 30 篇 render → 30 篇 deploy

### 阶段 2: Day 2 50 篇 majors 清单 (待 user 给)
- [ ] 50 篇分 2 批, 各 25 篇 (便于 hard-code 头部 + 验证)
- [ ] **批次 1 (前 25)**: 优先 hard-code (避免 LLM 复发, 确保第一批 100% clean)
- [ ] **批次 2 (后 25)**: mimo synth + auto_fix_pipeline 兜底 (验证流水线通用性)
- [ ] user 启动前请提供具体 50 篇清单 (style 分布 + 是否含新增方向)

### 阶段 3: 收尾 (15min)
- [ ] content_audit 抽样 5-10 篇 (m3 内容质量检查)
- [ ] Playwright 截图 3-5 篇关键专业 (视觉验证)
- [ ] commit push main
- [ ] 更新 MEMORY.md + day2 总结

---

## 3. 启动命令模板 (Day 2 启动后用)

```bash
# 阶段 1: 流水线一键化
git checkout -b day2-pipeline
# 改 3 个脚本, 测试一键流水线

# 阶段 2: 批次 1 (前 25 篇 hard-code)
python3 scripts/batches/hard_fix_remaining.py --csv scripts/batches/day2_batch1.csv
python3 scripts/batches/render_batch.py --csv scripts/batches/day2_batch1.csv
python3 scripts/deploy_to_public.py --csv scripts/batches/day2_batch1.csv
# content_audit + 截图

# 阶段 2 续: 批次 2 (后 25 篇一键流水线)
python3 -m scripts.batch_synth --file scripts/batches/day2_batch2.csv --provider mimo --auto-fix --audit mimo
python3 scripts/batches/render_batch.py --csv scripts/batches/day2_batch2.csv
python3 scripts/deploy_to_public.py --csv scripts/batches/day2_batch2.csv
# content_audit + 截图
```

---

## 4. 风险 & 兜底

| 风险 | 兜底 |
|------|------|
| mimo API rate limit | 串行调用, 每篇间隔 1s |
| hard-code 知识不够 | 参考公开行业报告 (脉脉/猎聘/智联), 招股书 |
| normalize 覆盖 hard-fix | 加 `--skip-normalize` flag |
| deploy cache 误判 | 强制 `rm public/*.html` + re-render |
| 新增 direction 需补 m3 content_audit | 5 篇/批抽样, 阈值 7/10 |

---

## 5. Day 2 期望产出

- 50 篇精品专业 v2 上线 (含 Day 1 44 篇, 累计 ~174 篇)
- 流水线一键化 (auto-fix 集成 batch_synth)
- 文档: 3 防线 (PLAN_field_fix_pipeline.md) + Day 2 plan (本文件)
- 总耗时估计: 4-6h (50 篇 synth + fix + render + deploy)
- 总成本: ~¥0.5 (含 50 篇 mimo audit + 必要 hard-fix + content_audit 抽样)

---

## 6. 下次 session 第一句话

> "Day 2 启动, 50 篇 majors 清单如下: ..."
