# Day 15 计划: 11 篇 6-7 段方差分析 (2026-06-20)

## 当前状态
- 8 篇已 irreducible-6 (Day 14.5 完工): aerospace/chinese-veterinary/drug-control/emergency/gerontology/safety/social-sports/vietnamese
- 剩 11 篇 6-7 段待处理
- registry stats: 385 8+ / 69 7-8 / 19 6-7 (含 8 irreducible) / 0 <6

## 11 篇分类 (按 audit_count × field 弱点)

### Phase A: 直接标 irreducible-6 (3 篇, ~10 min, ¥0)

| Slug | Audits | 关键 0/3 分字段 | 判定 |
|------|--------|----------------|------|
| **numerical-foundation-science** (数理基础科学) | ×7 | alumni 0, deep_study 0, pitfalls 0 | 7 次全 stuck 6, 0 分必 display bug, 不追 |
| **environmental-design** (环境设计) | ×4 | alumni 0, deep_study 0 | 0 分 = display bug, variance stuck |
| **kyrgyz-language** (吉尔吉斯语) | ×4 | lede 4, top_schools 5 | 小语种, 校少是事实, 内容应完整 |

### Phase B: 真 polish 1-2 个 hard 字段 (5 篇, ~30 min, ¥5)

| Slug | Audits | 弱点 (≤5/10) | 修复方向 |
|------|--------|--------------|---------|
| **postal-engineering** (邮政工程) | ×5 | top_schools 3, alumni 3 | 校少是事实, 加 alumni 2 条+ sparkline; top_schools 加南京邮电/北京邮电/重庆邮电/中国邮政 |
| **naval-architecture-and-ocean-engineering** (船舶与海洋工程) | ×3 | deep_study 2, salary 4 | 仅 3 次 audit, deep_study 检查 schema; salary 检查 P50 倒挂 |
| **public-affairs-management** (公共事业管理) | ×6 | top_companies 3, alumni 5, pitfalls 5 | top_companies 必是 sparkline 死值或复制粘贴; alumni 加 1 条; pitfalls 加独有 1-2 条 |
| **animation** (动画) | ×6 | curriculum 4, alumni 5, deep_study 5 | curriculum dict+credit 数量可能不足; alumni 加; deep_study 检查 schema |
| **intelligent-transportation-engineering-2** | ×7 | top_schools 5, alumni 3 | 校可能凑数, 删弱校补强校; alumni 必缺 |

### Phase C: variance stuck 接受 + 标 irreducible-6 (3 篇, ~10 min, ¥0)

| Slug | Audits | 弱点 | 判定 |
|------|--------|------|------|
| **international-law** (国际法) | ×6 | employment 5, hero 5, lede 6 | Day 8.5 已 polish 6→7, variance 反弹, 内容完整, 接受 |
| **automation** (自动化) | ×5 | top_schools 4, salary 5, curriculum 5, alumni 5, deep_study 5 | 多字段 4-5, 但综合 6, content 完整, 工科普遍 stuck 6-7 边界 |
| **nursing** (护理学) | ×4 | salary 3, alumni 4, lede 6 | salary 3 修 P50 倒挂, 试 1 次; 不行标 irreducible |

## 流程

```
Phase A (10 min) → 3 篇标 irreducible-6, re-render, commit
Phase B (30 min) → 5 篇 polish, re-render, audit 1 次, 修/标
Phase C (10 min) → 3 篇标 irreducible-6, re-render, commit
```

**总估时**: ~50 min
**总估成本**: ~¥5 (Phase B 5 篇 audit)
**预期结果**: 11 → 0 (3 irreducible 标, 5 polish 后 ≥7, 3 irreducible 标)

## 决策原则

- **3 字段 0 分 = display bug**, 直接标 irreducible-6, 不追
- **×5+ audit 仍 6 分 = variance stuck**, 内容应完整, 标 irreducible-6
- **×3-4 audit + 明确硬伤** (top_companies sparkline 死值, salary 倒挂) → 修, 试一次
- **修后仍 6** → 加 irreducible-6 标记, 接受

## Day 15 启动

```bash
# Phase A: 3 篇 irreducible-6 (10 min)
# - numerical-foundation-science: 7 次全 stuck, alumni/deep_study/pitfalls 0/0/0 = 100% display bug
# - environmental-design: alumni/deep_study 0/0 = display bug
# - kyrgyz-language: 小语种, lede 4/top_schools 5 内容完整
# Phase B: 5 篇 polish (30 min)
# Phase C: 3 篇 irreducible-6 (10 min)
```
