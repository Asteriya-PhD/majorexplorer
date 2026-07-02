# Day 22 Plan: 60 篇新专业上线 (4 worktree × 15 篇)

> **日期**: 2026-06-22 (v2 修 Momus 评审 2 个 slug 冲突)
> **前置**: 475 篇上线, 71% 覆盖率, 平均 7.78/10, 8+ 占比 73%
> **目标**: 475 → 535 篇, 71% → 80% 覆盖率, 补 工学 45 + 管理学 5 + 艺术学 10
> **方案**: A (4 路 × 15 篇并行), ~7.5h 整批 + 2-3h merge/audit = **~10h**

---

## 📊 覆盖率目标

| 门类 | 改前 | +新增 | 改后 | 备注 |
|------|------|------|------|------|
| 工学 (08) | 128/223 = 57% | +45 | 173/223 = 78% | 重点 |
| 管理学 (12) | 36/57 = 63% | +5 | 41/57 = 72% | 公共管理类 |
| 艺术学 (13) | 37/58 = 64% | +10 | 47/58 = 81% | 美术 + 设计 |
| **总体** | **475/670 = 71%** | **+60** | **535/670 = 80%** | |

> v2 修正: 工学 +45 (非 +50), 艺术学 +10 (非 +5), 60 篇合计正确. style 分布: eng 41 + sci 1 + cs 3 + administration 5 + arts 10 = 60.

---

## 🎯 60 篇精确清单 (4 worktree × 15 篇)

### Worktree A — 交通运输 8 + 电气 4 + 农业工程 3 (15 篇, 全 eng)

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

### Worktree B — 兵器 5 + 电子信息 5 + 材料 4 + 计算机 1 (15 篇)

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

### Worktree C — 化工 4 + 轻工 4 + 食品 4 + 计算机 2 + 农业工程 1 (15 篇)

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

### Worktree D — 公共管理 5 + 美术 5 + 设计 5 (15 篇)

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

## 🌲 Worktree 创建方案

### 创建命令 (主 worktree 执行)

```bash
# 1. 清理 prunable 旧 worktree
git worktree prune

# 2. 从 main 创建 4 个新 worktree + 分支
git worktree add .worktrees/wt-day22-A -b day22-batch-A main
git worktree add .worktrees/wt-day22-B -b day22-batch-B main
git worktree add .worktrees/wt-day22-C -b day22-batch-C main
git worktree add .worktrees/wt-day22-D -b day22-batch-D main

# 3. 验证
git worktree list
```

### 各 worktree 拷入 BATCH.md 任务清单

每份 BATCH.md 含 15 篇的:
- title / slug / style / 专业类
- 参考模板 (P0 优秀案例)
- 验收标准 (audit ≥7)
- commit message 模板

---

## 📋 单 worktree 流水线 (15 篇 × 30min = 7.5h)

按 [PIPELINE_major_quality.md](PIPELINE_major_quality.md) 9 步:

```
每篇 ~30min:
1. 读 m3 audit (新篇无历史 → skip)
2. 4 anti-pollution rules 前置避坑 (CLAUDE.md 必读)
3. Hand-Write JSON (18 字段, 参考 P0 4 案例结构)
4. render + deploy (绕过 deploy_to_public.py ROOT bug, 手动 re.sub)
5. content_audit.py --slugs <slug>:<style> → 期望 ≥7
6. Tier 1/2 重试 (5-6 分硬伤 → 5-15min 升 8, v1.2 SOP)
7. Step 0: repair_top_schools_rank.py 规整 rank 字段
8. Single commit per major (按 CLAUDE.md commit 模板)
9. worktree 内不写 audit_registry.json (避免合并冲突)
```

### 4 个 P0 优秀参考案例 (Tier 2 重写时必读)

| Major | 风格 | 路径 | 适用场景 |
|-------|------|------|---------|
| 计算语言学 | humanities | `skills/gaokao-major-explorer/data/curated/computational-linguistics.json` | 半文半理 + AI 预备 |
| 电子科学与技术 | eng | `skills/gaokao-major-explorer/data/curated/electronic-science-technology.json` | 器件+IC+材料 (B 路参考) |
| 卫生健康法学 | law | `skills/gaokao-major-explorer/data/curated/health-law.json` | 医学+法学+政策 (D 路公共管理参考) |
| 文化遗产 | humanities | `skills/gaokao-major-explorer/data/curated/cultural-relics-museology.json` | 田野+策展+修复 (D 路美术/设计参考) |

---

## 🔀 Merge 策略 (4 路完工后)

### Merge 顺序

```bash
# 1. main 拉最新
git checkout main && git pull

# 2. 依次 merge 4 路分支 (no-ff 保留分支历史)
git merge --no-ff day22-batch-A -m "merge: day22 batch A (15 majors, 交通/电气/农业工程)"
git merge --no-ff day22-batch-B -m "merge: day22 batch B (15 majors, 兵器/电子信息/材料/计算机)"
git merge --no-ff day22-batch-C -m "merge: day22 batch C (15 majors, 化工/轻工/食品/计算机/农业工程)"
git merge --no-ff day22-batch-D -m "merge: day22 batch D (15 majors, 公共管理/美术/设计)"
```

### 冲突处理

| 文件 | 冲突概率 | 处理 |
|------|---------|------|
| `skills/gaokao-major-explorer/data/curated/*.json` | 0 (60 篇 slug 已验证与 manifest 475 篇无冲突, v2 修复) | 无冲突 |
| `skills/gaokao-major-explorer/data/curated/*.html` | 0 | 无冲突 |
| `public/*.html` | 0 | 无冲突 |
| `public/data/manifest.json` | 高 (4 路都改) | 合并后统一 rebuild |
| `data/audit_registry.json` | 高 | **worktree 内不写**, 合并后统一 smart_audit 重建 |
| `test_results/content_audit_*.json` | 中 (时间戳文件名) | 通常无冲突, 若有取两者 |

> v2 修复: Momus 评审发现原 `marine-engineering` (已有 "海洋工程") 和 `public-relations` (已有 "公共关系学" arts) 冲突. 已改为 `marine-power-engineering` (轮机工程) 和 `elderly-care-service-management` (养老服务与管理, 替代公共关系学 1204 分类).

---

## 🧪 全量检查 (merge 后)

```bash
# 1. Step 0: repair top_schools.rank (新产出的 60 篇)
python3 scripts/schema-fix/repair_top_schools_rank.py --dry-run
python3 scripts/schema-fix/repair_top_schools_rank.py

# 2. manifest 重建 (新增 60 篇)
python3 scripts/build_manifest.py  # 或对应脚本名

# 3. 全量 smart_audit (475 + 60 = 535 篇, 2-3h, ¥40)
source .env
python3 scripts/audit/smart_audit.py

# 4. 修 < 7 的篇 (历史 11 篇未审 + 新 60 篇中失分)
# 5. 修 4 个均分 <7.5 专业类的硬伤 (化工/公共管理/音乐/数学, v1.2 SOP 5-15min/篇)
# 6. Push
git push origin main
```

---

## ⚠️ 风险 + 缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| `audit_registry.json` 合并冲突 | 4 路都改同一文件 | **worktree 内不写 registry**, 合并后统一 smart_audit 重建 |
| `manifest.json` 合并冲突 | 各路加新 slug | 合并后统一 rebuild |
| m3 API rate limit | 4 路同时 audit | 各路顺序跑 15 篇, 4 路总并发=4, m3 历史未报限流 |
| CC Write 在某些 worktree 被 revert | 单篇丢失 | 启动前 `echo test > file && cat file` 测试 (已知坑 #5) |
| session merge 残留 | working tree 污染 | merge 前 `git stash` (已知坑 #6) |
| 单篇 30min 估时太乐观 | 整批超时 | 兵器/轻工/化妆品等资料稀缺专业可能 45-60min, 预留 20% buffer |
| 公共管理类现均分 7.2 | 新加 5 篇可能也 7-8 | 优先用 P0 卫生法学/计算语言学模板, 避免重蹈覆辙 |
| `可 ignorable fields` 留空 | schema_drift | 合并后跑 `cleanup_entrepreneur.py` + salary schema 统一 |

---

## ✅ 验收标准

| 指标 | 目标 | 最低 |
|------|------|------|
| 60 篇全部上线 (JSON + HTML) | 60/60 | 55/60 |
| 60 篇 audit ≥ 7 比例 | 100% | 90% |
| 60 篇 audit ≥ 8 比例 | 50% | 30% (新篇多 7 起步) |
| 0 strong 字段缺失 | 0 | ≤5% |
| 0 anti-pollution violation | 0 | 0 |
| 总覆盖率 | 80% | 78% |
| 整批耗时 | 10h | 12h |
| 单篇耗时 | 30min | 45min |
| merge 冲突 | 0 (rebuild 解决) | 2 (手动 reconcile) |

---

## 📝 Commit Message 模板

### 单篇 commit (每篇 1 commit)

```
fix(content): <major中文名> P0 新增 (新专业, X/10)

新增 <专业类> 缺口专业, 按 P0 案例结构 hand-write 18 字段:
- lede <洞察+门槛>
- who_fits_yes/no 4+4 条 <专业专属>
- pitfalls 5-7 条 <本专业独有 myth/reality>
- curriculum 公共必修+通用核心+5 校特色
- top_schools 6-10 所 <学科评估真实排名>
- employment_direction 5-8 方向, 合计 100%
- salary p25/p50/p75/yoy <13 套 style 校准>
- alumni_quotes 3-5 条 (含 year/current/school)
- deep_study 5-7 路径, 合计 ≈100%
- xuanke_req_list 含 pct, 首选物理/历史 二选一

m3 content_audit: X/10 (优秀/合格, 0 strong, N 项 warning)
```

### Merge commit (4 路)

```
merge: day22 batch X (15 majors, <专业类汇总>)

15 篇新增 + 各篇 audit ≥7:
- <专业 1> (X/10)
- <专业 2> (X/10)
...

Registry: 475 → 490 (+15), 全量 smart_audit 待跑
```

---

## ⏱️ 时间线

| 时点 | 任务 | 耗时 |
|------|------|------|
| T+0 | 创建 4 worktree + 4 份 BATCH.md | 10min |
| T+0.2h | 4 路 agent 开工 (并行) | - |
| T+7.5h | 4 路 15 篇全部完工 (期望) | 7.5h |
| T+7.5h | Merge 4 路分支 (含冲突处理) | 30min |
| T+8h | Step 0 repair rank + manifest rebuild | 15min |
| T+8.25h | 全量 smart_audit (535 篇, 2-3h) | 2.5h |
| T+10.75h | 修 <7 + 修 4 个均分 <7.5 专业类 | 1h |
| T+11.75h | Push main | 5min |
| **总耗时** | | **~12h** |

---

## 📌 启动前 Checklist

- [ ] 用户确认本 PLAN
- [ ] `git pull` main 最新
- [ ] `git worktree prune` 清理旧 prunable
- [ ] 创建 4 worktree + 4 分支
- [ ] 生成 4 份 BATCH.md 拷入各 worktree
- [ ] 各 worktree `echo test > file && cat file` 测试 CC Write
- [ ] 各 worktree `source .env` 验证 m3 API key
- [ ] 4 路 agent 开工
