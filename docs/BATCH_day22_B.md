# BATCH B — 兵器 5 + 电子信息 5 + 材料 4 + 计算机 1 (15 篇)

> **Worktree**: `.worktrees/wt-day22-B` · **分支**: `day22-batch-B`
> **任务**: 15 篇全新 major hand-code + audit ≥7 + single commit per major
> **估时**: 7.5h (30min/篇, 兵器类资料稀缺可能 45min/篇)

---

## 📋 15 篇清单

| # | title | slug | style | 专业类 |
|---|-------|------|-------|--------|
| 1 | 武器发射工程 | weapon-launch-engineering | eng | 08-0819 |
| 2 | 探测制导与控制技术 | detection-guidance-control | eng | 08-0819 |
| 3 | 弹药工程与爆炸技术 | ammunition-explosion-engineering | eng | 08-0819 |
| 4 | 特种能源技术与工程 | special-energy-engineering | eng | 08-0819 |
| 5 | 装甲车辆工程 | armored-vehicle-engineering | eng | 08-0819 |
| 6 | 信息工程 | information-engineering | eng | 08-0807 |
| 7 | 电子封装技术 | electronic-packaging-technology | eng | 08-0807 |
| 8 | 电磁场与无线技术 | em-fields-wireless-technology | eng | 08-0807 |
| 9 | 电波传播与天线 | radio-propagation-antenna | eng | 08-0807 |
| 10 | 海洋信息工程 | marine-information-engineering | eng | 08-0807 |
| 11 | 材料物理 | materials-physics | sci | 08-0802 |
| 12 | 金属材料工程 | metallic-materials-engineering | eng | 08-0802 |
| 13 | 无机非金属材料工程 | inorganic-nonmetallic-materials | eng | 08-0802 |
| 14 | 焊接技术与工程 | welding-technology-engineering | eng | 08-0802 |
| 15 | 空间信息与数字技术 | spatial-information-digital-technology | cs | 08-0809 |

---

## 🛠️ 单篇流水线 (30-45min)

```
1. 4 anti-pollution rules 前置避坑 (CLAUDE.md 必读)
2. Hand-Write JSON (18 字段, 参考 P0 电子科学技术案例)
3. Render HTML (用 generate_dashboard.py)
4. Deploy (绕过 deploy_to_public.py ROOT bug, 手动 re.sub)
5. Audit verify: content_audit.py --slugs <slug>:<style>
6. Tier 1/2 重试 (audit < 7 时, v1.2 SOP)
7. Step 0: repair_top_schools_rank.py
8. Single commit per major
```

## ⚠️ 兵器类特殊注意

- 兵器类 5 篇 (1-5) 涉及国防专业, 数据公开度低
- top_schools 优先: 北京理工 / 南京理工 / 中北大学 / 沈阳理工 / 长春理工
- employment_direction 多涉国防军工, 不写敏感单位
- 兵器类 audit 可能 7 起步, 不追 8 (资料稀缺, m3 给分保守)

## ⚠️ 不做

- **不写 audit_registry.json / manifest.json**
- **不改其他 worktree 文件**
- **不 push**

## 📌 参考模板

- eng P0: `skills/gaokao-major-explorer/data/curated/electronic-science-technology.json`
- 电子信息类参考: 现有 光电信息科学与工程 / 通信工程 / 人工智能 (0807 已有 7 篇)
- 材料类参考: 现有 增材制造工程 / 智能交互设计 (0802 已有 8 篇)
- 计算机类参考: 现有 计算机科学与技术 / 软件工程 (0809 已有 10 篇)

## ✅ 完工标准

- [ ] 15 篇 JSON + HTML 全部生成
- [ ] 15 篇 audit ≥ 7 (兵器类允许 6-7 起步, v1.2 SOP 升 7)
- [ ] 0 anti-pollution violation
- [ ] 15 个 single commit
