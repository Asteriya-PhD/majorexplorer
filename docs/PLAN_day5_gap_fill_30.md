# Day 5 Gap-Fill 30 — 30 篇全新 major 补 6 门类 gap

> 写于 2026-06-18, F 阶段 (309→337) 完工 + 工具链 v1 (pre-commit hook) 上线后.
> **目标**: 337 → 367 篇, 6 门类覆盖率提升 (重点 文学 18% → 24%, 农学 29% → 39%).
> **重开后启动**: 3 个并行 CC (A/B/C 各 10 篇) + 3 worktree + batch audit + push main.

---

## 📊 现状 + 目标

| 门类 | 当前/候选 | 改前覆盖率 | 改后 | Δ 篇数 | 候选 |
|------|-----------|-----------|------|-------|------|
| 文学 (05) | 24/132 | 18.2% | **24%** | +8 | 8 |
| 农学 (09) | 15/51 | 29.4% | **39%** | +5 | 5 |
| 工学 (08) | 97/293 | 33.1% | **36%** | +8 | 8 |
| 艺术学 (13) | 23/67 | 34.3% | **40%** | +4 | 4 |
| 法学 (03 公安学) | 20/56 | 35.7% | **41%** | +3 | 3 |
| 教育学 (04 体育) | 13/36 | 36.1% | **42%** | +2 | 2 |
| **总计** | **329/868 = 37.9%** | | **~42%** | **+30** | **30** |

注: 哲学 100% 满, 历史 67% 高, 跳过. 文学/农学/工学 三大 gap 重点.

---

## 🎯 30 篇目标 (按 6 门类 + Agent 分布)

### Agent A (10 篇 — 文学 8 + 教育 2, 全部 humanities) ⭐

| # | Major | 门类 | Subclass | Style | 故事性 |
|---|-------|------|----------|-------|--------|
| 1 | 汉语言 | 05 | 中国语言文学类 | humanities | 与汉语言文学区分, 应用导向 |
| 2 | 应用中文 | 05 | 中国语言文学类 | humanities | 港台/海外中文热 |
| 3 | 手语翻译 | 05 | 中国语言文学类 | humanities | 公益热点, 无障碍 |
| 4 | 中国古典学 | 05 | 中国语言文学类 | humanities | 国学热, 跨学科 |
| 5 | 马来语 | 05 | 外国语言文学类 | humanities | 一带一路 |
| 6 | 越南语 | 05 | 外国语言文学类 | humanities | 一带一路 |
| 7 | 缅甸语 | 05 | 外国语言文学类 | humanities | 一带一路 |
| 8 | 数字新闻 | 05 | 新闻传播学类 | humanities | 媒体转型 |
| 9 | 电子竞技运动与管理 | 04 | 体育学类 | education | 电竞产业 |
| 10 | 智能体育工程 | 04 | 体育学类 | education | 体育 × AI |

### Agent B (10 篇 — 农学 5 + 法学 3 + 工学 2, 生活服务类) ⭐

| # | Major | 门类 | Subclass | Style | 故事性 |
|---|-------|------|----------|-------|--------|
| 1 | 马业科学 | 09 | 动物生产类 | agri | 特色专业, 就业清晰 |
| 2 | 蜂学 | 09 | 动物生产类 | agri | 特色农业, 乡村振兴 |
| 3 | 中兽医学 | 09 | 动物医学类 | agri | 中兽医特色 |
| 4 | 实验动物学 | 09 | 动物医学类 | agri | 生物医学上游, 紧缺 |
| 5 | 草坪科学与工程 | 09 | 草学类 | agri | 城市绿化 + 高尔夫 |
| 6 | 海警执法 | 03 | 公安学类 | gongan | 海警组建后新专业 |
| 7 | 技术侦查学 | 03 | 公安学类 | gongan | 公安技术 |
| 8 | 国内安全保卫 | 03 | 公安学类 | gongan | 国安方向 |
| 9 | 飞行技术 | 08 | 交通运输类 | eng | 民航缺口大 |
| 10 | 邮政工程 | 08 | 邮政工程类 | eng | 京东物流 / 邮政集团 |

### Agent C (10 篇 — 工学 6 + 艺术学 4, 工科 × 创意) ⭐

| # | Major | 门类 | Subclass | Style | 故事性 |
|---|-------|------|----------|-------|--------|
| 1 | 智能海洋装备 | 08 | 海洋工程类 | eng | 海洋强国战略 |
| 2 | 海洋机器人 | 08 | 海洋工程类 | eng | 智能交叉 |
| 3 | 新能源汽车工程 | 08 | 能源动力类 | eng | 政策风口, 25%+ 增长 |
| 4 | 储能科学与工程 | 08 | 能源动力类 | eng | 双碳风口 |
| 5 | 智能建造 | 08 | 土木类 | eng | 新工科 |
| 6 | 智能交通工程 | 08 | 交通运输类 | eng | 智慧城市 |
| 7 | 数字戏剧 | 13 | 戏剧与影视学类 | arts | 元宇宙戏剧 |
| 8 | 智能影像艺术 | 13 | 戏剧与影视学类 | arts | AI × 影视 |
| 9 | 戏剧教育 | 13 | 戏剧与影视学类 | arts | 戏剧进校园 |
| 10 | 数字演艺设计 | 13 | 戏剧与影视学类 | arts | 沉浸式演艺 |

---

## 🛠️ 流水线 9 步 (复用 Day 4/F 模板, **pre-commit hook 自动检查**)

```
1. cd worktree (A/B/C 各自)
2. 读 /tmp/day5-prompt-X.md 拿 10 篇清单
3. 4 anti-pollution rules 前置避坑 (CLAUDE.md 必读)
4. Hand-Write 10 个 JSON (18 字段 schema, 复制 P0 优秀案例结构)
5. Render: python3 skills/gaokao-major-explorer/scripts/render_batch.py --slugs <10个> (0¥)
6. Deploy: 手动 re.sub 绕过 deploy_to_public.py ROOT bug
7. m3 content_audit:  source .env && python3 scripts/batches/content_audit.py --csv /tmp/day5-30-majors.csv (估 30 min ¥15)
8. Tier retry (per-major): Tier 1 补字段 / Tier 2 重写 / Tier 3 跳过
9. Single commit (per worktree): git add + commit "fix(content): Day 5 X 10 篇 (08 工学) 全新上线 (audit X.X/10)"
   ↑ pre-commit hook 自动跑 3 检查: backfill + L1 + manifest drift
```

---

## 📂 已就绪文件 (重开后直接用)

```bash
# 1. 30 篇 selection (json + csv)
/tmp/day5-30-majors.csv
/tmp/day5-selection.json

# 2. Shared context (11 章节 SOP, 复用 Day 4 模板 + Day 5 注意事项)
/tmp/day5-shared-context.md

# 3. 3 个 Agent prompts (待写)
/tmp/day5-prompt-A.md  (10 篇 humanities)
/tmp/day5-prompt-B.md  (10 篇 生活服务类)
/tmp/day5-prompt-C.md  (10 篇 工科 × 创意)
```

---

## 🚀 重开后启动步骤 (5 步)

```bash
# Step 1: 创建 3 个 worktree (基于 main)
cd /Users/zhewenliu/Claude/gaokao-hubei-mvp
for X in A B C; do
  git worktree add -b day5-batch-$X .worktrees/day5-$X main
  cp .env .worktrees/day5-$X/.env
  (cd .worktrees/day5-$X && git config core.hooksPath .githooks)
done

# Step 2: 启动 3 个 CC sub-agent (run_in_background=true, 互不阻塞)
# Agent A: cd .worktrees/day5-A, 处理 10 篇 humanities (文学 8 + 教育 2)
# Agent B: cd .worktrees/day5-B, 处理 10 篇 生活服务 (农学 5 + 公安 3 + 工学 2)
# Agent C: cd .worktrees/day5-C, 处理 10 篇 工科 × 创意 (工学 6 + 艺术 4)

# Step 3: 完工后 merge 3 branches (--no-ff)
# 顺序: A → B → C
git merge --no-ff day5-batch-A -m "merge: Day 5 A 10 篇 humanities (文学 8 + 教育 2)"
git merge --no-ff day5-batch-B -m "merge: Day 5 B 10 篇 生活服务 (农学 5 + 公安 3 + 工学 2)"
git merge --no-ff day5-batch-C -m "merge: Day 5 C 10 篇 工科×创意 (工学 6 + 艺术 4)"

# Step 4: 合并后 schema cleanup (拆 entrepreneur + 统一 salary)
# 跑 rebuild_manifest.py 自动同步

# Step 5: Push main
git push origin main
python3 scripts/update_audit_registry.py --rebuild
```

---

## ⏱️ 预期

- **3 agent 并行**: ~60 min (vs 串行 3h)
- **3 parallel content_audit**: ~20 min (vs 60 min)
- **合并 + 清理 + push**: ~30 min
- **总耗时**: ~2h
- **总成本**: ~¥150 (3 agent × 10 篇 × ¥5)
- **目标**: 337 → 367 篇, 总覆盖率 37.9% → 42%, 6 门类各涨 3-6pp

---

## 🔑 复用 F 阶段经验 (避免重复踩坑)

1. **3 worktree 不自动继承 .env** — 必须手动 cp
2. **m3 audit "字段截断" display bug** (PIPELINE §3) — 数据完整即可
3. **m3 audit ±1 分波动** — 取多次 audit 平均
4. **3 parallel content_audit 比串行快 3×** — 但不要 >3 并行 (m3 rate limit)
5. **parallel run 后必须 rebuild manifest + registry** (auto-sync 不触发)
6. **CC Write 在 worktree 可能 silent revert** — 启动前用 `echo test > file && cat file` 测试
7. **CC 不自动 cd worktree** — prompt 必须明确 cd 路径
8. **🆕 pre-commit hook 装上**: commit 时自动跑 3 检查 (backfill/L1/manifest drift)
9. **🆕 5 字段 100% 必填** (backfill 工具已就绪): discipline/sub_discipline/menjia_moe/menjia_name/theme_color
10. **🆕 ANTI-POLLUTION RULE 4 必修修**: 公共必修严格只放通识 (高数/英语/思政/制图/计算机/物理)

---

## 📊 阶段完成后覆盖率

```
文学 (05):     24/132 = 18% → 32/132 = 24% (+6pp)
农学 (09):     15/51  = 29% → 20/51  = 39% (+10pp)
工学 (08):     97/293 = 33% → 105/293= 36% (+3pp)
艺术学 (13):   23/67  = 34% → 27/67  = 40% (+6pp)
公安学:        8/56   = 14% → 11/56  = 20% (+6pp)  [含在 03 法学]
教育学 (04):   13/36  = 36% → 15/36  = 42% (+6pp)  [体育类]
总:            329/868 = 37.9% → 359/868 = 41.4% (+3.5pp)
```

---

**Co-Authored-By**: Claude Opus 4.8 <noreply@anthropic.com>
