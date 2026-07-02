# BATCH C — 化工 4 + 轻工 4 + 食品 4 + 计算机 2 + 农业工程 1 (15 篇)

> **Worktree**: `.worktrees/wt-day22-C` · **分支**: `day22-batch-C`
> **任务**: 15 篇全新 major hand-code + audit ≥7 + single commit per major
> **估时**: 7.5h (30min/篇, 化妆品/酿酒等特色专业可能 45min)

---

## 📋 15 篇清单

| # | title | slug | style | 专业类 |
|---|-------|------|-------|--------|
| 1 | 资源循环科学与工程 | resource-recycling-engineering | eng | 08-0813 |
| 2 | 能源化学工程 | energy-chemical-engineering | eng | 08-0813 |
| 3 | 化学工程与工业生物工程 | chemical-engineering-industrial-bioengineering | eng | 08-0813 |
| 4 | 化工安全工程 | chemical-safety-engineering | eng | 08-0813 |
| 5 | 轻化工程 | light-chemical-engineering | eng | 08-0817 |
| 6 | 包装工程 | packaging-engineering | eng | 08-0817 |
| 7 | 印刷工程 | printing-engineering | eng | 08-0817 |
| 8 | 化妆品技术与工程 | cosmetics-technology-engineering | eng | 08-0817 |
| 9 | 粮食工程 | grain-engineering | eng | 08-0825 |
| 10 | 乳品工程 | dairy-engineering | eng | 08-0825 |
| 11 | 酿酒工程 | brewing-engineering | eng | 08-0825 |
| 12 | 葡萄与葡萄酒工程 | viticulture-enology | eng | 08-0825 |
| 13 | 新媒体技术 | new-media-technology | cs | 08-0809 |
| 14 | 电影制作 | film-production | cs | 08-0809 |
| 15 | 农业智能装备工程 | agricultural-intelligent-equipment | eng | 08-0821 |

---

## 🛠️ 单篇流水线 (30-45min)

```
1. 4 anti-pollution rules 前置避坑
2. Hand-Write JSON (18 字段, 参考 P0 电子科学技术案例)
3. Render HTML (generate_dashboard.py)
4. Deploy (手动 re.sub 绕 ROOT bug)
5. Audit verify: content_audit.py --slugs <slug>:eng
6. Tier 1/2 重试 (v1.2 SOP)
7. Step 0: repair_top_schools_rank.py
8. Single commit per major
```

## ⚠️ 化工类特殊注意

- 化工与制药类现状均分 7.2 (4 篇), 新加 4 篇务必避开 lede 模板套话
- 4 anti-pollution rules 第 4 条: curriculum 公共必修只放高数/英语/思政/制图
- 资源循环/能源化学/化工安全 是新兴交叉, employment_direction 多去新能源/环保
- 化工与工业生物工程 涉生物制药, top_schools 优先天大/华东理工/浙大

## ⚠️ 轻工/食品类特殊注意

- 化妆品 (上海应用技术大学独家强) / 酿酒 (中国农大/江南大学) / 葡萄与葡萄酒 (西北农林)
- top_schools 必须写特色强校, 不要凑清北复交
- employment_direction 体现行业细分 (化妆品→原料/配方/品牌方; 酿酒→酒厂/检测/品牌)

## ⚠️ 不做

- **不写 audit_registry.json / manifest.json**
- **不改其他 worktree 文件**
- **不 push**

## 📌 参考模板

- eng P0: `skills/gaokao-major-explorer/data/curated/electronic-science-technology.json`
- 化工类参考: 现有 化学工程与工艺 (0813 已有 4 篇)
- 农业工程类参考: 现有 4 篇 0821 (看现有风格)
- 计算机/新媒体: 现有 17 篇 cs (看现有风格)

## ✅ 完工标准

- [ ] 15 篇 JSON + HTML 全部生成
- [ ] 15 篇 audit ≥ 7
- [ ] 0 anti-pollution violation
- [ ] 15 个 single commit
