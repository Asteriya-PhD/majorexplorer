# Day 4 F 阶段 Plan — 30 篇全新 major 补 4 门类 gap

> 写于 2026-06-18, D 阶段 (E 阶段 polish) 完工后.
> **目标**: 309 → 339 篇, 4 门类覆盖率从 47.3% → 53% (一次性补 4 大 gap).
> **重开后启动**: 3 个并行 CC (A/B/C 各 10 篇) + 3 worktree + batch audit + push main.

---

## 📊 现状 + 目标

| 门类 | 当前 | 目标 | Δ 篇数 | 候选 |
|------|------|------|-------|------|
| 08 工学 | 73/188 = 39% | 50% (94/188) | +12 | 12 |
| 13 艺术学 | 15/49 = 31% | 47% (23/49) | +8 | 8 |
| 09 农学 | 9/29 = 31% | 48% (14/29) | +5 | 5 |
| 14 交叉学科 | 1/10 = 10% | 60% (6/10) | +5 | 5 |
| **总计** | **47.3%** | **53%** | **+30** | **30** |

---

## 🎯 30 篇目标 (按 menjia 分布)

### Agent A (10 篇 eng — 08 工学) ⭐
1. 智能电网信息工程 (eng, 0806 电气类)
2. 复合材料与工程 (eng, 0802 材料类)
3. 功能材料 (eng, 0802 材料类)
4. 智能装备与系统 (eng, 0808 自动化类)
5. 智能工程与创意设计 (eng, 0808 自动化类)
6. 建筑电气与智能化 (eng, 0810 土木类)
7. 道路桥梁与渡河工程 (eng, 0810 土木类)
8. 给排水科学与工程 (eng, 0810 土木类)
9. 水文与水资源工程 (eng, 0811 水利类)
10. 核工程与核技术 (eng, 0820 核工程类)

### Agent B (10 篇 mixed) ⭐
1. 辐射防护与核安全 (eng, 0820 核工程类)
2. 武器系统与工程 (gongan, 0819 兵器类)
3. 集成电路设计与集成系统(交叉) (eng, 1401 集成电路)
4. 集成电路技术 (eng, 1401 集成电路)
5. 纳米材料与技术 (sci, 1402 纳米)
6. 纳米科学与工程 (sci, 1402 纳米)
7. 认知神经科学 (sci, 1405 脑科学)
8. 植物保护 (agri, 0901 植物生产)
9. 种子科学与工程 (agri, 0901 植物生产)
10. 设施农业科学与工程 (agri, 0901 植物生产)

### Agent C (10 篇 arts/agri) ⭐
1. 戏剧影视导演 (arts, 1303 戏剧与影视)
2. 表演 (arts, 1303 戏剧与影视)
3. 影视摄影与制作 (arts, 1303 戏剧与影视)
4. 录音艺术 (arts, 1303 戏剧与影视)
5. 戏剧影视美术设计 (arts, 1303 戏剧与影视)
6. 作曲与作曲技术理论 (arts, 1302 音乐与舞蹈)
7. 流行音乐 (arts, 1302 音乐与舞蹈)
8. 文物保护与修复 (arts, 1304 美术学)
9. 农业资源与环境 (agri, 0902 自然保护)
10. 兽医公共卫生 (agri, 0904 动物医学)

---

## 🛠️ 流水线 9 步 (复用 Day 4 模板)

```
1. Audit Driven    → 不需要 (新专业无历史)
2. Anti-Pollution  → 4 rules 前置必避 (见 shared context §3)
3. Hand-Write JSON → 按 18 字段 schema
4. Render + Deploy → 手动 re.sub 绕过 deploy_to_public.py ROOT bug
5. Audit Verify    → 3 parallel content_audit.py --csv (各 10 篇) ~20 min
6. Tier Retry      → 5-6 → Tier 1 补字段; <5 → Tier 2 重写; 仍 <5 → Tier 3 跳过
7. Single Commit   → 单篇 1 commit (per-major) OR 1 batch commit (≥10 篇)
8. Schema Cleanup  → 合并后批量: 拆细 entrepreneur + 统一 salary p25/p50/p75
9. Full Audit+Push → smart_audit.py + rebuild registry + push main
```

---

## 📂 已就绪文件 (重开后直接用)

```bash
# 1. 30 篇 selection (json + csv)
/tmp/day4-F-selection.json
/tmp/day4-F-30-majors.csv

# 2. Shared context (11 章节 SOP, 复用 Day 4 模板)
/tmp/day4-shared-context.md

# 3. 3 个 Agent prompts (待写)
/tmp/day4-F-prompt-A.md  (eng 10 篇)
/tmp/day4-F-prompt-B.md  (mixed 10 篇)
/tmp/day4-F-prompt-C.md  (arts/agri 10 篇)
```

---

## 🚀 重开后启动步骤 (5 步)

```bash
# Step 1: 创建 3 个 worktree (基于 main)
cd /Users/zhewenliu/Claude/gaokao-hubei-mvp
for X in A B C; do
  git worktree add -b day4-F-batch-$X .worktrees/day4-F-$X main
  cp .env .worktrees/day4-F-$X/.env  # worktree 不自动继承 .env
done

# Step 2: 启动 3 个 CC sub-agent (run_in_background=true, 互不阻塞)
# Agent A: cd .worktrees/day4-F-A, 处理 10 篇 eng
# Agent B: cd .worktrees/day4-F-B, 处理 10 篇 mixed
# Agent C: cd .worktrees/day4-F-C, 处理 10 篇 arts/agri

# Step 3: 完工后 merge 3 branches (--no-ff)
# 顺序: A → B → C
git merge --no-ff day4-F-batch-A -m "merge: Day 4 F-A 10 篇 eng (08 工学)"
git merge --no-ff day4-F-batch-B -m "merge: Day 4 F-B 10 篇 mixed"
git merge --no-ff day4-F-batch-C -m "merge: Day 4 F-C 10 篇 arts/agri"

# Step 4: 合并后清理 schema (拆 entrepreneur + 统一 salary)
# + 跑 smart_audit (or 3 parallel content_audit 验证)

# Step 5: Push main + manifest + registry
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
- **目标**: 309 → 339 篇, 13 门类覆盖率 47.3% → 53%

---

## 🔑 复用 Day 4 经验 (避免重复踩坑)

1. **3 worktree 不自动继承 .env** — 必须手动 cp
2. **m3 audit 0/10 不一定是真 bug** — JSON 截断是 display bug (PIPELINE §3)
3. **真 bug**: top_schools 凑数校 / lede 偏长 / 学科评估等级错
4. **3 parallel content_audit 比串行快 3×** — 但不要 >3 并行 (m3 rate limit)
5. **parallel run 后必须 rebuild registry** (auto-sync 不触发)
6. **CC Write 在 worktree 可能 silent revert** — 启动前用 `echo test > file && cat file` 测试
7. **CC 不自动 cd worktree** — prompt 必须明确 cd 路径

---

## 📊 F 阶段 完成后覆盖率

```
08 工学:    73/188 = 39% → 85/188 = 45% (+6pp) — 仍最大 gap
13 艺术学:  15/49  = 31% → 23/49  = 47% (+16pp) ✅
09 农学:     9/29  = 31% → 14/29  = 48% (+17pp) ✅
14 交叉学科: 1/10  = 10% →  6/10  = 60% (+50pp) ✅ 突破!
13 门类总: 248/524 = 47.3% → 278/524 = 53% (+6pp) ✅
```

---

**Co-Authored-By**: Claude Opus 4.8 <noreply@anthropic.com>
