# Day 6 Plan — 30 篇单 agent gap-fill

> 写于 2026-06-18, Day 5 30 篇完工 (100%≥7) + 工具链 v2 (9 件套) 上线后.
> **目标**: 337 → 367 篇, 6 门类覆盖率提升 (文学 18% → 25%, 农学 29% → 34%, 艺术 34% → 39%, 公安学 35% → 38%, 教育 36% → 42%).
> **单 CC 跑** (用户决策, 不用 3 agent 并行): 1 agent 30 篇, 估 2-2.5h / ¥80-100.

---

## 📊 现状 + 目标

| 门类 | 当前/候选 | 改前覆盖率 | 改后 | Δ 篇数 |
|------|-----------|-----------|------|-------|
| 文学 05 | 24/132 | 18.2% | 24% | +10 |
| 农学 09 | 15/51 | 29.4% | 35% | +4 |
| 艺术学 13 | 23/67 | 34.3% | 39% | +3 |
| 公安学 03 | 8/56 | 14% | 18% | +2 |
| 教育学 04 (体育) | 13/36 | 36.1% | 50% | +5 |
| 工学 08 | 96/293 | 32.8% | 35% | +6 |
| **总计** | | | | **+30** |

---

## 🎯 30 篇目标 (单 agent 跑)

### 文学 10 篇 (humanities) ⭐ 主力
1. **古典文献学** (中国语言文学类) — 古籍整理
2. **比较文学** (中国语言文学类) — 中外比较
3. **应用语言学** (中国语言文学类) — 语言应用
4. **社会语言学** (中国语言文学类) — 社会+语言
5. **朝鲜语** (外国语言文学类) — 韩国方向
6. **泰语** (外国语言文学类) — 一带一路
7. **阿拉伯语** (外国语言文学类) — 中东
8. **德语** (外国语言文学类) — 欧洲
9. **国际新闻与传播** (新闻传播学类) — 涉外新闻
10. **网络与新媒体** (新闻传播学类) — 新媒体

### 教育学 5 篇 (体育 education)
11. 武术与民族传统体育
12. 冰雪运动
13. 体育旅游
14. 社会体育指导与管理
15. 运动能力开发

### 工学 6 篇 (新工科 eng)
16. 智能电网信息工程
17. 智能采矿工程
18. 智能感知工程
19. 量子信息工程
20. 工业智能
21. 智慧能源工程

### 农学 4 篇 (现代畜牧/植物保护 agri)
22. 经济动物学
23. 蚕学
24. 植物保护
25. 草学

### 艺术学 3 篇 (arts)
26. 艺术管理
27. 艺术史论
28. 艺术批评

### 公安学 2 篇 (gongan)
29. 海警学
30. 网络空间安全 (公安学方向)

---

## 📂 已就绪文件 (重开后直接用)

```bash
# 1. 30 篇 selection (JSON + CSV)
/tmp/day6-30-majors.csv
/tmp/day6-selection.json

# 2. Single agent prompt
/tmp/day6-prompt-single.md
```

---

## 🚀 单 CC 启动步骤 (5 步)

```bash
# Step 1: 不开 worktree, 直接在 main 跑
cd /Users/zhewenliu/Claude/gaokao-hubei-mvp

# Step 2: 启动 1 CC sub-agent (run_in_background=true)
# 必读 /tmp/day6-prompt-single.md
# 30 篇 claim 一次性 (防串领):
python3 scripts/claim.py --agent day6-single --slugs $(cut -d, -f1 /tmp/day6-30-majors.csv | tail -30 | tr '\n' ' ') --task "Day 6 30 篇单 CC"

# Step 3: 完工后 commit + 跑 rebuild
git add skills/gaokao-major-explorer/data/curated/<30>.json public/<30>.html
git commit -m "fix(content): Day 6 30 篇单 CC 全新上线 (audit X.X/10 avg)"

# Step 4: rebuild + release
python3 scripts/rebuild_manifest.py
python3 scripts/update_audit_registry.py --rebuild
python3 scripts/build_directory.py
python3 scripts/claim.py --release day6-single

# Step 5: Push
git push origin main
```

---

## ⏱️ 预期

- 单 agent 30 篇: 2-2.5h (vs 3 agent 并行 60-90min, 但 quality + 一致性更好)
- 总成本: ¥80-100 (2-3 轮 m3 audit × 30 篇)
- 目标: 337 → 367 篇, 总覆盖率 41.4% → 44.9% (+3.5pp)

---

## 🔑 复用 Day 5 经验 (避免重复踩坑)

1. **pre-commit hook 已装** (commit 时自动跑 3 检查: backfill + L1 + manifest drift)
2. **claim.py 已就绪** (30 个 slug 一次性 claim 防串领)
3. **m3 audit "字段截断" 是 display bug** (PIPELINE §3) — 数据完整即可
4. **m3 audit ±1 分波动** — 取多次 audit 平均
5. **deploy_to_public.py ROOT 写死** — 用手动 re.sub 替代
6. **公共必修严格只放通识** (ANTI-POLLUTION RULE 4) — 专业课放通用专业核心
7. **5 字段必填** (discipline/sub_discipline/menjia_moe/menjia_name/theme_color)
8. **顶层 `lede` + `pitfalls`** (m3 读顶层)
9. **deep_study 跟 employment_direction 数字对齐** (8 路径 ≤ 100%)

---

## 🎯 Day 6 完成后覆盖率

```
文学 05:     24/132 = 18% → 34/132 = 26% (+8pp 最大赢家)
教育学 04:   13/36  = 36% → 18/36  = 50% (+14pp)
农学 09:     15/51  = 29% → 19/51  = 37% (+8pp)
艺术学 13:   23/67  = 34% → 26/67  = 39% (+5pp)
工学 08:     96/293 = 33% → 102/293= 35% (+2pp)
公安学 03:   8/56   = 14% → 10/56  = 18% (+4pp)
总:          329/868 = 37.9% → 359/868 = 41.4% (+3.5pp)
```

---

## 🛠️ 工具链 v2 完整清单 (9 件套)

1. `scripts/batches/content_audit.py` — 单篇 m3 audit, 跑完 auto-sync registry
2. `scripts/smart_audit.py` — 批量智能路由 (Layer 1 启发式 + Layer 2 m3)
3. `scripts/rebuild_manifest.py` — 从 curated/ 重建 manifest.json (含 --check / --add-slug)
4. `scripts/backfill_manifest_fields.py` — 5 字段 100% 填全 (含 --check / --apply)
5. `scripts/update_audit_registry.py` — registry 单一真相 (含 --rebuild / --from-file / --from-stdin / --stats)
6. `scripts/build_directory.py` — 13 门类完整目录 + stats (含 --check / --render-md)
7. `scripts/claim.py` — 防串领 (含 --agent / --list / --check-conflict / --release / --cleanup)
8. `scripts/next_pick.py` — 智能跨门类挑 N 篇 (含 --claim 集成)
9. `.githooks/pre-commit` — 3 检查自动拦截 (安装: `./scripts/install-hooks.sh`)

---

**Co-Authored-By**: Claude Opus 4.8 <noreply@anthropic.com>
