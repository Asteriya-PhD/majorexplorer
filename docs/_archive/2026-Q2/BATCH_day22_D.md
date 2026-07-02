# BATCH D — 公共管理 5 + 美术 5 + 设计 5 (15 篇)

> **Worktree**: `.worktrees/wt-day22-D` · **分支**: `day22-batch-D`
> **任务**: 15 篇全新 major hand-code + audit ≥7 + single commit per major
> **估时**: 7.5h (30min/篇, arts 类 alumni_quotes 资料多, 可能 40min)

---

## 📋 15 篇清单

| # | title | slug | style | 专业类 |
|---|-------|------|-------|--------|
| 1 | 土地资源管理 | land-resource-management | administration | 12-1204 |
| 2 | 城市管理 | urban-management | administration | 12-1204 |
| 3 | 海关管理 | customs-management | administration | 12-1204 |
| 4 | 交通管理 | transport-management | administration | 12-1204 |
| 5 | 养老服务与管理 | elderly-care-service-management | administration | 12-1204 |
| 6 | 绘画 | painting | arts | 13-1304 |
| 7 | 雕塑 | sculpture | arts | 13-1304 |
| 8 | 摄影 | photography | arts | 13-1304 |
| 9 | 书法学 | calligraphy | arts | 13-1304 |
| 10 | 实验艺术 | experimental-art | arts | 13-1304 |
| 11 | 艺术设计学 | art-design-studies | arts | 13-1305 |
| 12 | 产品设计 | product-design | arts | 13-1305 |
| 13 | 服装与服饰设计 | fashion-apparel-design | arts | 13-1305 |
| 14 | 公共艺术 | public-art | arts | 13-1305 |
| 15 | 工艺美术 | arts-crafts | arts | 13-1305 |

---

## 🛠️ 单篇流水线 (30-40min)

```
1. 4 anti-pollution rules 前置避坑 (CLAUDE.md 必读)
2. Hand-Write JSON (18 字段, 参考 P0 卫生健康法学/文化遗产案例)
3. Render HTML:
   python3 skills/gaokao-major-explorer/scripts/generate_dashboard.py \
     --data skills/gaokao-major-explorer/data/curated/<slug>.json \
     --style <administration|arts> \
     --output skills/gaokao-major-explorer/data/curated/<slug>.html
4. Deploy (手动 re.sub)
5. Audit verify: content_audit.py --slugs <slug>:<style>
6. Tier 1/2 重试 (v1.2 SOP)
7. Step 0: repair_top_schools_rank.py
8. Single commit per major
```

## ⚠️ 公共管理类特殊注意 (5 篇 administration)

- 公共管理类现状均分 7.2 (6 篇), 8+ 占比 61% (管理学最低)
- **4 anti-pollution rules 第 2 条**: who_fits_no 不能出现 "数学/统计/经济/考证"
- **第 3 条**: deep_study 不能写 "跨学科就业 (CS/数据/金融)" 12%, 用专业真实去向
- 土地资源管理: top_schools 优先 中国农大 / 中国人民大学 / 浙大 / 南大 / 同济
- 海关管理: 上海海关学院独家强, top_schools 必含
- 养老服务与管理: 老龄化背景下的新兴方向, top_schools 优先 人民大学 / 首都经济贸易大学 / 华东师大 / 浙大 / 武汉大学. 与已有"健康服务与管理"区分: 养老聚焦老龄事业产业 / 养老机构运营 / 老年健康照护管理
- **参考 P0**: `skills/gaokao-major-explorer/data/curated/health-law.json` (卫生法学, 跨学科 + 公共政策)

## ⚠️ 美术/设计类特殊注意 (10 篇 arts)

- arts 类 alumni_quotes 资料多 (知乎/小红书大量), 可写 5 条详细 quote
- **4 anti-pollution rules 第 1 条**: lede 不写 "绘画是研究...的学科", 用 "绘画的核心是 X+Y+Z, 它在 P 时代有 Q 优势, 但 R 是该专业最大风险"
- 绘画/雕塑/书法: 中央美院 / 中国美院 / 广州美院 / 四川美院 / 西安美院 / 鲁迅美院 (6 大美院)
- 摄影: 北京电影学院 / 中国传媒大学 / 中央美院 / 鲁迅美院
- 产品设计: 湖南大学 / 江南大学 / 同济 / 中央美院 / 中国美院 (设计学强校)
- 服装与服饰设计: 东华大学 / 北京服装学院 / 中国美院 / 江南大学
- **参考 P0**: `skills/gaokao-major-explorer/data/curated/cultural-relics-museology.json` (文化遗产, 田野+策展+修复)

## ⚠️ 不做

- **不写 audit_registry.json / manifest.json**
- **不改其他 worktree 文件**
- **不 push**

## 📌 参考模板

- administration P0: `skills/gaokao-major-explorer/data/curated/health-law.json` (跨学科)
- arts P0: `skills/gaokao-major-explorer/data/curated/cultural-relics-museology.json` (田野+策展)
- 公共管理类参考: 现有 行政管理 / 劳动与社会保障 (1204 已有 6 篇)
- 美术学类参考: 现有 美术学 (1304 已有 3 篇)
- 设计学类参考: 现有 视觉传达设计 / 环境设计 / 数字媒体艺术 (1305 已有 8 篇)

## ✅ 完工标准

- [ ] 15 篇 JSON + HTML 全部生成
- [ ] 15 篇 audit ≥ 7 (公共管理类务必 ≥7, 拉升 7.2 均分)
- [ ] 0 anti-pollution violation
- [ ] 15 个 single commit
