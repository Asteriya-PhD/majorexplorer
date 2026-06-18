# Plan: 字段级 Fix 流水线设计 (3 防线)

**日期**: 2026-06-16
**目标**: 解决 LLM 跨专业模板污染 (CFA/精算/UI/UX 串到非对应专业)
**触发**: 2026-06-15 day1 跑批 49 篇 m3, 45 篇 pitfalls 全是金融话术模板, 14 篇 employment 工业设计

---

## 1. 根因分析 (更新于 2026-06-16)

### 1.1 LLM 训练数据偏置 (根因 A)

| LLM | 冷门工科 fallback | 测试结果 |
|------|-----------------|---------|
| **deepseek v4-flash** | 工业设计/UI/UX | day1 14/14 employment 全错 |
| **m3 (MiniMax-M3)** | 金融/精算/CFA | day1 45/45 pitfalls 同一模板 |
| **mimo (Xiaomi MiMo V2 Flash)** | 不稳定 (随机 fallback) | 船舶/测绘/食品干净, 但光电又串到 UI/UX |

**结论: 3 个 LLM 都有 fallback 偏置, 没有"换模型"能解决". 模板诱导 + 训练数据同源污染是根本问题.**

### 1.2 模板诱导 (根因 B)

`TEMPLATE.json` 字段提示 LLM "必须填满", 没给"如果不确定可填 N/A"选项.
LLM 收到空白字段 + 模糊主题 → 抓最熟 fallback (金融/工业设计).

---

## 2. 3 防线设计 (验证有效)

### 防线 1: 模板降诱导 (Opt 1)

**改动**: TEMPLATE.json 字段加 "如不确定可填 N/A" 注释

```json
{
  "employment_direction": [{"_note": "5-7 条, 如不确定写 ['数据待补, 需手动研究']"}],
  "pitfalls": [{"_note": "3 条专业独有坑, 想不出就写 '本专业独有坑需人工补充'"}],
}
```

**验证**: 部分有效. mimo 偶尔会写 "数据待补", m3 还是会补 fill. 削弱污染率从 100% → ~40%, 不能根治.

### 防线 2: 关键词扫污染 (Opt 2 - 关键)

**核心**: `scripts/batches/contam_dict.py` (100+ 词, 8 个分类)

| 词库 | 强命中词示例 | 适用 style |
|------|------------|----------|
| FINANCE_STRONG | CFA/精算/CPA/ACCA/FRM/投行/券商/银行风控 | 除 finance 外 |
| INDUSTRIAL_DESIGN_STRONG | UI/UX/IDEO/Frog/洛可可/产品设计 | 除 arts 外 |
| DATA_SCIENCE | 算法岗/大厂/数据科学家 | 除 cs 外 |
| HUMANITIES_DRIFT | 出版编辑/文学评论 | 理工医农 |
| MEDICAL_DRIFT | 规培/执业医师/处方 | 非医学类 |
| LAW_GONGAN_DRIFT | 法考/律师执业/公安联考 | 非法学公安 |
| EDUCATION_DRIFT | 教学法/微格教学/教师编制 | 非教育类 |
| ALL_FORBIDDEN | "毕业=自动高薪" 模板话 | 全专业 |

**伪命中陷阱** (易误判):
- ❌ "四大" 误命中 "四大经典" (中医学) / "四大领域" (测控)
- ❌ "设计院" 误命中 建筑设计院/化工设计院 (工科真实雇主)
- ❌ "MBB" 误命中 "MIT/Berkeley/Stanford"
- ❌ "教师" 误命中 校友 quote "我高中老师推荐"

**对策**: 用精准词组 (e.g. "四大事务所" 而非 "四大"), style 字段白名单 (e.g. arts 类允许 "工业设计").

**验证**: 100% 命中已知 45+ 污染. day1 修复前 45/49 → 修复后 0/49.

### 防线 3: 字段级 Fix (Opt 3 - 兜底)

**核心**: `scripts/batches/auto_fix_pipeline.py`

```python
流程:
  1. 读 JSON
  2. detect_contamination → 列出 (field, level, hits)
  3. 对 strong 命中: m3 字段级重写
     prompt: "{field} 当前内容 + 污染词清单 + '重新生成该字段'"
  4. 写回 JSON
  5. 重检测 (验证 clean)
```

**成本**: 30-60s/字段, ¥0.01/字段. 41 篇 × 2 字段 ≈ 25 min, ¥0.5.

**验证**: 41 篇污染 → 0 篇污染, 全部 strong 命中清理.

---

## 3. 推荐生产流水线 (1 + 2 + 3 联动)

```bash
# 1. Synth (mimo default, m3 兜底)
python3 -m scripts.batch_synth --file day1_v1.csv --provider mimo --audit mimo

# 2. Field-level fix (auto, m3 only for contaminated fields)
python3 scripts/batches/auto_fix_pipeline.py --csv day1_v1.csv

# 3. Content audit (m3, 找出剩余质量分低)
python3 scripts/batches/content_audit.py --csv day1_v1.csv --limit 49

# 4. Render + deploy
python3 scripts/batches/normalize.py day1_v1.csv
python3 scripts/batches/render_batch.py --csv day1_v1.csv
python3 scripts/deploy_to_public.py --csv day1_v1.csv
```

**Day 1 实际跑下来**: 44 篇 synth (12 min) → 0 篇 strong 污染 (4 min) → 8 min 渲染部署 = 24 min 总.

---

## 4. 4 项优化实测结果

| 优化 | 期望收益 | 实测结果 | 是否纳入 |
|------|---------|---------|---------|
| **Opt 1**: 模板加 N/A 注释 | 降低诱导 | 略有效, 不根治 | ✅ 纳入 (低成本) |
| **Opt 2**: 100+ 词污染字典 | 精确检测 | 100% 命中已知 45 污染 | ✅ 关键防线 |
| **Opt 3**: auto_fix_pipeline 串联 | 自动化修复 | 41 篇 → 0 篇, 25min | ✅ 关键防线 |
| **Opt 4**: 换 mimo provider | 不同 fallback 偏置 | 统计上更好 (更少污染), 但仍随机串 | ✅ 默认 provider, 仍需 2+3 |

---

## 5. Day 1 重做对比 (4 阶段状态)

| 阶段 | 工具 | 状态 | 备注 |
|------|------|------|------|
| v1 (deepseek) | deepseek synth | ❌ 14 工业设计 + 45 金融话术 | 0/49 干净 |
| v2 (m3) | m3 synth | ⚠️ 45 金融话术残留 | m3 同源污染 |
| v3 (m3 + fix) | m3 + fix_pitfalls_whofits | ✅ 0 金融, 0 工业设计 | 但有 1-2 个 random 残留 |
| **v4 (mimo + auto-fix)** | mimo + auto_fix_pipeline | ✅ 0 强污染, 0 模板 | **Day 1 最终** |

---

## 6. 残留问题 + 下次迭代

### 6.1 短期 (Day 2 前)
- [x] Opt 1-4 全部纳入
- [ ] lede 仍通用化 ("X 是 Y 学科下...") — 用 m3 fix_field lede 字段
- [ ] 5 校特色选修 偶有填错 (高数当特色) — 用 m3 fix_field 5 校特色选修
- [ ] 翻译 pitfalls 4 → 3 (mimo fallback 默认 3) — 已经在 v3 trim 过了
- [ ] IoT employment_direction [空数组] — 需要重新 synth

### 6.2 中期 (Day 2-3)
- [ ] m3 content_audit 自动化 (目前是手动跑, 1.5min/篇)
- [ ] contamination 字典扩到 200+ 词 (含 "战略管理/BCG 大中华/红圈所" 等)
- [ ] 多模型 consensus: mimo + m3 + deepseek 3 选 2 投票 (高成本, 高质量)
- [ ] 字段长度一致性检查 (curriculum 总学分 30 vs 60 等)

### 6.3 长期 (Day 4+)
- [ ] RAG 注入: 每个 major 注入 5-10 篇真实 知乎/高考资讯文章作为 ground truth
- [ ] 学科门类知识图谱: 让 LLM 先查图谱再填字段
- [ ] 用户 A/B 测试: 同一专业 3 个版本让用户盲评, 取最高分

---

## 7. 总结 (一句话)

**3 防线设计** (模板降诱导 + 100+ 词字典检测 + m3 字段级 fix) **实测有效**, 把 day1 49 篇从 0% 干净提升到 100% 干净. mimo 默认 provider 比 m3 快 5x, 但仍需 2+3 兜底 (因为 mimo 也会随机污染). Day 1 最终版 mimo + auto_fix_pipeline 已 push main, 立即可用.

**下一 session**: 把这个流水线串到 batch_synth 的 `--auto-fix` flag, 让 day2 跑批"开箱即用".
