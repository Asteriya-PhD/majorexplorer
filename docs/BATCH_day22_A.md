# BATCH A — 交通运输 8 + 电气 4 + 农业工程 3 (15 篇, 全 eng)

> **Worktree**: `.worktrees/wt-day22-A` · **分支**: `day22-batch-A`
> **任务**: 15 篇全新 major hand-code + audit ≥7 + single commit per major
> **估时**: 7.5h (30min/篇)

---

## 📋 15 篇清单

| # | title | slug | style | 专业类 |
|---|-------|------|-------|--------|
| 1 | 交通运输 | traffic-transportation | eng | 08-0815 |
| 2 | 交通工程 | traffic-engineering | eng | 08-0815 |
| 3 | 航海技术 | marine-navigation-technology | eng | 08-0815 |
| 4 | 轮机工程 | marine-power-engineering | eng | 08-0815 |
| 5 | 交通建设与装备 | transportation-construction-equipment | eng | 08-0815 |
| 6 | 海事管理 | maritime-management | eng | 08-0815 |
| 7 | 轨道工程 | rail-track-engineering | eng | 08-0815 |
| 8 | 邮轮工程 | cruise-engineering | eng | 08-0815 |
| 9 | 光源与照明 | light-source-illumination | eng | 08-0806 |
| 10 | 电气工程与智能控制 | electrical-engineering-intelligent-control | eng | 08-0806 |
| 11 | 电机电器智能化 | motor-appliance-intelligence | eng | 08-0806 |
| 12 | 电缆工程 | cable-engineering | eng | 08-0806 |
| 13 | 农业工程 | agricultural-engineering | eng | 08-0821 |
| 14 | 农业建筑环境与能源工程 | agricultural-building-energy-engineering | eng | 08-0821 |
| 15 | 农业水利工程 | agricultural-water-resources-engineering | eng | 08-0821 |

---

## 🛠️ 单篇流水线 (30min)

```
1. 4 anti-pollution rules 前置避坑 (CLAUDE.md 必读)
2. Hand-Write JSON (18 字段, 参考 P0 电子科学技术案例)
3. Render HTML:
   python3 skills/gaokao-major-explorer/scripts/generate_dashboard.py \
     --data skills/gaokao-major-explorer/data/curated/<slug>.json \
     --style eng \
     --output skills/gaokao-major-explorer/data/curated/<slug>.html
4. Deploy (绕过 deploy_to_public.py ROOT bug):
   python3 -c "
   import re, pathlib
   src = pathlib.Path(f'skills/gaokao-major-explorer/data/curated/<slug>.html').read_text()
   new = re.sub(r'(src|href)=\"\.\./\.\./((?:js|css)/[^\"]+)\"', r'\1=\"/\2\"', src)
   pathlib.Path(f'public/<slug>.html').write_text(new)
   "
5. Audit verify:
   source .env
   python3 scripts/batches/content_audit.py --slugs <slug>:eng
   # 期望 overall_score ≥ 7
6. Tier 1/2 重试 (audit < 7 时, 5-15min 升 8, v1.2 SOP)
7. Step 0: repair_top_schools_rank.py 规整 rank 字段
8. Single commit:
   git add skills/gaokao-major-explorer/data/curated/<slug>.{json,html} public/<slug>.html
   git commit -m "fix(content): <中文名> P0 新增 (新专业, X/10)..."
```

## ⚠️ 不做

- **不写 audit_registry.json** (合并后统一 smart_audit 重建)
- **不写 manifest.json** (合并后统一 rebuild)
- **不改其他 worktree 的文件**
- **不 push** (留待 main 合并后统一 push)

## 📌 参考模板

- eng 风格 P0: `skills/gaokao-major-explorer/data/curated/electronic-science-technology.json`
- 交通运输类参考: 现有 飞行技术 (0815 已有 1 篇)
- 农业工程类参考: 现有 农业工程 1 篇 (0821 已有 4 篇, 看现有风格)

## ✅ 完工标准

- [ ] 15 篇 JSON + HTML 全部生成
- [ ] 15 篇 audit ≥ 7
- [ ] 0 anti-pollution violation
- [ ] 0 strong 字段缺失
- [ ] 15 个 single commit
- [ ] 不动 audit_registry / manifest
