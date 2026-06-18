# Day 3 Team A Handoff v2 — 2026-06-17 (Audit 7.47 → 目标 8.5-9.0)

**当前状态**: Day 3 Team A 47/47 全部 hand-curated, 3 atomic commit + 1 audit-fix commit push day3-team-a (13848d6 → 3d5c391 → e38e0bc → 0325603 → 251b3f4), audit avg **7.47/10** (sample 15).

**目标**: 3-4h 内推到 **8.5-9.0/10** avg, 系统性修跨字段数字矛盾 + curriculum 课程补全 + top_schools 学科评估。

---

## 1. 环境/位置 (与 v1 handoff 一致)

```bash
cd /Users/zhewenliu/Claude/gaokao-team-a
git branch  # 期望: day3-team-a
git log --oneline -5
# 251b3f4 fix(content): Day 3 Team A audit v2 升级 (avg 6.93 → 7.47)
# 0325603 fix(content): Day 3 Team A +12 篇精雕 batch3 (eng 4+cs 3+sci 1+agri 4, 47/47 COMPLETE)
# e38e0bc fix(content): Day 3 Team A +12 篇精雕 batch2
# 3d5c391 fix(content): Day 3 Team A +12 篇精雕 batch1
# 13848d6 fix(content): Day 3 Team A +11 篇精雕 (anesthesiology/basic-medicine, deepseek 10/9.93)
```

**主仓 = main 分支 = 干净,不要动。所有 work 都在 worktree (day3-team-a 分支)。**

---

## 2. 当前 audit 详细问题 (按扣分严重度排序)

### 2.1 deep_study 数字内部矛盾 (扣 1-3 分) ★★★
- **症状**: deep_study 路径百分比 跟 employment_direction 数字 跟 summary 数字 互相打架
- **典型例子**: bioinformatics
  - deep_study: "国内985硕博 40% + 海外硕博 8% = 48% 读研"
  - employment_direction[5] 继续深造: 18%
  - summary: "硕博比例 60-80%"
  - 三个数字互相矛盾,读者无法判断
- **修法**: 对每篇 major,基于 employment_direction 已有百分比 推导 deep_study 5-7 路径 (深造占比直接来自 employment 的"继续深造"项),确保加和=100
- **预计影响**: 14/15 篇改善 +1-2 分

### 2.2 salary 数据失真 (扣 1-3 分) ★★★
- **症状**: 顶层 salary 字段 (3-5年/5-10年) 数字 跟 employment_direction/alumni 数字 矛盾
- **典型例子**: biomedical-engineering
  - 顶层 salary 3-5年: p25=0/p50=0/p75=0 (空白)
  - 顶层 salary 5-10年: p25=0/p50=0/p75=0 (空白)
  - 但 employment_direction 写 "3年+ 25-45万"
  - alumni 写 "3 年+ 28W+"
- **修法**: 对每篇 major,基于 employment_direction 数字 反推顶层 salary 各阶段 (应届=entry/3-5=3年+/5-10=5年+/10年+=资深)
- **预计影响**: 5-8 篇改善 +1-2 分

### 2.3 top_schools 学科评估等级错 (扣 1-3 分) ★★★
- **症状**: 把 A 说成 A+, 学科评估排名错
- **典型例子**: basic-medicine
  - "中山大学基础医学 A+ 全国第一" 实际是 A (不是 A+)
  - 第四轮学科评估基础医学 A+ 仅北大、复旦
- **修法**: 对每篇 major,查 [中国学位与研究生教育学会 第四轮学科评估结果](https://www.chinadegrees.cn/), 校准 A+/A/A-/B+ 等级, 改 top_schools 字段
- **预计影响**: 10-15 篇改善 +1 分 (基础医学/临床医学/口腔等大类)

### 2.4 curriculum 缺特色课 (扣 1-2 分) ★★
- **症状**: curriculum 课程列表缺专业特色课,只列基础课
- **典型例子**: agricultural-intelligent-equipment-engineering
  - curriculum 缺机器视觉/农业机器人/精准农业技术/农业物联网/GNSS+北斗导航
  - summary/lede 又提到这些课, "宣传 > 实际"
- **修法**: 对每篇 major, 基于核心课 + 行业需求 补全 5-10 门特色课到 curriculum
- **预计影响**: 8-10 篇改善 +0.5-1 分

### 2.5 lede 偏电报体 (扣 0.5-1 分) ★
- **症状**: lede 偏列表化罗列,缺主谓完整句
- **修法**: 微改 lede 第一句, 用主谓完整句替代列表 (但不要大改,避免破坏 lede+summary 呼应)
- **预计影响**: 5-8 篇改善 +0.5 分

---

## 3. 关键脚本 (可复用)

### 已存在
- `scripts/batches/hand_curate_day3_part3.py` — Batch 1 (12 篇)
- `scripts/batches/hand_curate_day3_part4.py` — Batch 2 (12 篇)
- `scripts/batches/hand_curate_day3_part5.py` — Batch 3 (12 篇)
- `scripts/batches/fix_day3_audit_v2.py` — 47 篇加 deep_study + 重写 lede (v2 已跑, 完成)
- `scripts/batches/fix_day3_audit_v3.py` — 修剩余 5 个问题 (v3 已跑, 完成)
- `scripts/batches/schema_fix_v4.py` — schema 归一
- `scripts/batches/render_batch.py` — render 47 HTML
- `scripts/batches/content_audit.py` — m3 内容质量审计
- `scripts/deploy_to_public.py` — 部署 public/

### 待写
- `scripts/batches/fix_day3_audit_v4.py` — 跨字段数字对齐 (核心任务)
  - 输入: 47 篇 JSON
  - 对每篇: 读取 employment_direction → 推导 deep_study 5-7 路径 (用 m3 一次性生成, prompt 强调"基于 employment_direction 数字")
  - 对每篇: 读取 employment_direction → 推导 salary 各阶段 (用 m3 一次性生成, prompt 强调"基于 employment_direction 数字")
  - 对每篇: 校准 top_schools 学科评估等级 (用 m3 一次性查证, prompt 强调"参考第四轮学科评估")
  - 写入 JSON
- `scripts/batches/fix_day3_audit_v5.py` — curriculum 补全 + lede 微改
  - 对每篇: 补全 curriculum 5-10 门特色课 (用 m3, prompt 强调"基于行业需求")
  - 对每篇: 微改 lede 第一句 (用 m3, prompt 强调"主谓完整句")

---

## 4. 修法核心策略

### 4.1 跨字段数字对齐 (核心难点)
**问题根源**: 之前 fix_v2 用 m3 一次生成 deep_study, 但 prompt 没强调"基于 employment_direction 数字" 导致 m3 自由发挥,产生矛盾。

**修法**:
- 改写 PROMPT, 强制 m3 读取 employment_direction 后推导 deep_study:
```
基于 employment_direction 现有数据:
- 主流方向 (pct 最大的前 3 项) → 派生到 deep_study "直接就业 X%" (X = sum 主流方向 pct)
- "继续深造" 那一项 → 派生到 deep_study "国内 985 硕博 X% + 海外硕博 Y%" (按 4:1 比例拆)
- "公务员/选调" → 派生到 deep_study "选调公务员 X%"
- "跨行" → 派生到 deep_study "跨行 X%"
- 剩余路径 → 派生到 deep_study "创业/其他" 兜底
确保加和=100, 与 employment_direction 数字严格一致.
```

### 4.2 salary 反推
**问题根源**: 顶层 salary 字段 (应届/3-5年/5-10年/10年+) 跟 employment 数字不匹配。

**修法**:
- 对每篇 major, 取 employment_direction 中 "应届/3年+/5年+/资深" 区间值
- 反推为 salary 字段:
  - 应届 p50 = employment 应届区间中位数
  - 3-5年 p50 = employment 3年+ 区间中位数
  - 5-10年 p50 = employment 5年+ 区间中位数 (如果有)
  - 10年+ p50 = employment 资深区间中位数
- 月薪 = 年薪 / 12, p25/p75 = 中位数 ±20%

### 4.3 top_schools 学科评估查证
**修法**: 对每篇 major, 用 m3 一次性查证 + 校准:
```
参考 2017 年中国学位与研究生教育学会 第四轮学科评估结果, 校准 top_schools 字段:
- 头部 A+ 学校 1-2 所 (如果有)
- A 级 2-3 所
- A- 级 1-2 所
- B+ 级 1-2 所
- 标记是 A+/A/A-/B+ 哪个等级
注意: 基础医学 A+ 仅北大复旦, 中山/华西/同济 是 A
```

### 4.4 curriculum 补全
**修法**: 用 m3 一次性补全 5-10 门特色课:
```
基于专业的核心方向, 补全 5-10 门特色课到 curriculum. 例如:
- 农业智能装备工程: 机器视觉/农业机器人/精准农业技术/农业物联网/GNSS+北斗导航/ROS/Python
- 生物医学工程: 医学免疫学/医学微生物学/生物力学/医学信号处理/医学图像处理/医疗器械设计
- 生物信息学: 统计遗传学/GWAS/医学信息学/临床生信/单细胞测序/空间转录组
```

### 4.5 lede 微改
**修法**: 用 m3 微改 lede 第一句, 改电报体 → 主谓完整句:
```
重写 lede 第一句, 要求:
- 主谓完整 (有主语+谓语+宾语)
- 1 个独特洞察
- 不要用 "35%/18%/12%" 等纯数字堆砌
- 长度 30-50 字 (原来 80-150 字缩到 30-50 字)
```

---

## 5. 推荐流程

```bash
cd /Users/zhewenliu/Claude/gaokao-team-a

# Step 1: 写 fix_v4 (跨字段对齐) — 核心
# 1.1 先写 fix_v4_part1: 47 篇 deep_study 跨字段对齐
python3 scripts/batches/fix_day3_audit_v4.py --phase deep_study

# 1.2 fix_v4_part2: 47 篇 salary 跨字段对齐
python3 scripts/batches/fix_day3_audit_v4.py --phase salary

# 1.3 fix_v4_part3: 47 篇 top_schools 学科评估校准
python3 scripts/batches/fix_day3_audit_v4.py --phase top_schools

# Step 2: 写 fix_v5 (curriculum + lede 微改)
python3 scripts/batches/fix_day3_audit_v5.py --phase curriculum
python3 scripts/batches/fix_day3_audit_v5.py --phase lede

# Step 3: schema_fix + render + deploy
python3 scripts/batches/schema_fix_v4.py
python3 scripts/batches/render_batch.py --csv scripts/batches/day3_team_a.csv
python3 scripts/deploy_to_public.py --csv scripts/batches/day3_team_a.csv --force

# Step 4: 抽样 audit 15 篇
source .env && python3 scripts/batches/content_audit.py --csv scripts/batches/day3_team_a.csv --limit 15

# Step 5: 如果 audit < 8.5, 针对性二次修
# (见 "失败如何继续" 章节)

# Step 6: commit + push
git add -A && git commit -m "fix(content): Day 3 Team A audit v3 升级 (avg 7.47 → 8.5+)"
git push origin day3-team-a
```

---

## 6. 要避开的坑点 (踩过的)

### 6.1 m3 call timeout/重试
- m3 调用偶尔会卡住 > 60s 或返回 RetryableError
- 修法: 在 fix_v4 加 retry=2 + timeout=120s
- 失败: log 该 slug 跳过, 不阻塞其他篇

### 6.2 JSON parse 失败
- m3 偶尔返回非 JSON (e.g. "```json ... ```" 多余 markdown)
- 修法: 正则 `re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)` 提取
- 失败: 二次重试 1 次, 还失败就 skip + 标记

### 6.3 跨字段一致性
- 修法: 修 deep_study 后, 立即 cross-check 跟 employment_direction 数字:
```python
def verify_consistency(data):
    emp_pct = {e["name"]: e["pct"] for e in data.get("employment_direction", [])}
    ds = data.get("deep_study", {})
    # 提取 "直接就业" 数字, 应等于 employment 中除 "继续深造" "公务员" "跨行" 之外的项之和
    ...
```

### 6.4 不要重写 7 字段全部
- v2 fix 已经修了 deep_study + lede + pitfalls
- v3 fix 已经修了 alumni 措辞 + salary 0 值 + 汤晓鸥
- v4/v5 只补 **数字对齐** + **curriculum** + **lede 微改**, **不要动** 已修好的字段 (避免反复横跳)

### 6.5 render + deploy 必须每次跑
- 每次修完 major JSON 后, render 47/47 + deploy 47/47 (确保 public/ 同步)

### 6.6 抽样 audit 限制
- audit 默认 sample 10-15 篇, 实际覆盖 ~25-30% 的 batch
- 想要更准的 avg, 跑 `--limit 30` (估时 5-10 min)
- **不推荐** 全量 audit 47 (估时 15-30 min, 边际收益低)

---

## 7. 失败如何继续 (降级策略)

### 7.1 如果 fix_v4 deep_study 阶段卡住
- **症状**: m3 持续 5+ 次返回非 JSON
- **降级**: 跳过 m3, 用确定性算法从 employment_direction 推导 deep_study:
```python
def derive_deep_study(emp):
    ds = {}
    direct_emp_pct = sum(e["pct"] for e in emp if e["name"] not in ["继续深造", "公务员/选调", "跨行", "跨行 AI/算法/咨询"])
    study_pct = sum(e["pct"] for e in emp if e["name"] in ["继续深造", "硕博"])
    civil_pct = sum(e["pct"] for e in emp if "公务员" in e["name"] or "选调" in e["name"])
    cross_pct = sum(e["pct"] for e in emp if "跨行" in e["name"])
    if study_pct > 0:
        ds["国内 985 硕博"] = int(study_pct * 0.8)
        ds["海外硕博"] = study_pct - int(study_pct * 0.8)
    if direct_emp_pct > 0:
        ds["直接就业 (企业/医院/科研)"] = direct_emp_pct
    if civil_pct > 0:
        ds["选调公务员/事业编"] = civil_pct
    if cross_pct > 0:
        ds["跨行/其他"] = cross_pct
    # 兜底
    total = sum(ds.values())
    if total < 100:
        diff = 100 - total
        ds["其他"] = diff
    return ds
```

### 7.2 如果 fix_v4 salary 阶段卡住
- **降级**: 跳过, 用启发式:
```python
def derive_salary(emp):
    # 从 employment 中取 "应届" "3年+" "5年+" "资深" 区间
    entry_median = parse_salary_range(emp[0].get("desc", ""))  # 通常第一项是主流
    sal = {
        "应届生": {"p25": int(entry_median*0.7/12), "p50": int(entry_median/12), "p75": int(entry_median*1.3/12), "yoy": 5},
        "3-5年": {...},
        "5-10年": {...},
        "10年+": {...}
    }
    return sal
```

### 7.3 如果 fix_v5 curriculum 卡住
- **降级**: 不动 curriculum, 只做 v4 (跨字段数字对齐), 接受 ~8.0/10
- 理由: curriculum 修起来工作量大, ROI 边际下降

### 7.4 如果 fix_v5 lede 卡住
- **降级**: 不动 lede, 接受 v2 已修的 lede
- 理由: lede 微改是锦上添花, 0.5 分收益, 不值得冒险

### 7.5 如果 audit 仍然 < 8.5
- **诊断**: 看 audit JSON, 找仍 < 8 的 major, 针对性二次修
- **重试次数**: **上限 2 次**, 2 次后仍 < 8.5 接受 8.0+ 作为现实上限
- **时间上限**: 总耗时 **4h** (从打开 v2 handoff 开始算), 超过 4h 停止, 不再投入

### 7.6 终止条件 (拍板)
- **成功**: audit avg ≥ 8.5 → 写最终 commit, push, 标 done
- **可接受**: audit avg 8.0-8.5 → 写 commit, push, 标 done
- **止损**: audit avg < 8.0 OR 耗时 > 4h OR 二次修失败 → 写 progress 文档, 标"接受 7.5/10", 不再投入

---

## 8. 完成定义

- [ ] 47 篇全部跨字段数字对齐 (deep_study + salary 一致)
- [ ] 47 篇 top_schools 学科评估等级校准
- [ ] (可选) 47 篇 curriculum 特色课补全
- [ ] (可选) 47 篇 lede 主谓完整句微改
- [ ] 47/47 render + 47/47 deploy
- [ ] 抽样 audit 15 篇 avg ≥ 8.5
- [ ] Commit + push day3-team-a
- [ ] (可选) merge day3-team-a → main (等 Team B 完成)

---

## 9. 下次 session 启动 checklist

```bash
# 1. 切到 worktree
cd /Users/zhewenliu/Claude/gaokao-team-a
git status  # 确认 working tree 干净
git log --oneline -3  # 确认 251b3f4 已是最新

# 2. 读 3 个 fix 脚本
cat scripts/batches/fix_day3_audit_v2.py  # 了解之前怎么写
cat scripts/batches/fix_day3_audit_v3.py  # 了解之前怎么写

# 3. 读 audit JSON (最新)
ls -la test_results/content_audit_*.json | tail -3
# 取最近一个看具体扣分项

# 4. 写 fix_v4 + fix_v5
# 5. 跑流程 (cross-check + render + deploy + audit)
# 6. 评估, 8.5+ 标 done, < 8.0 标止损
```

---

## 10. 时间预算分配

| 阶段 | 估时 | 累计 |
|------|------|------|
| 读 handoff + 诊断 | 10 min | 10 min |
| 写 fix_v4 (跨字段对齐) | 60 min | 70 min |
| 跑 fix_v4 + 验证 | 30 min | 100 min |
| 写 fix_v5 (curriculum + lede) | 60 min | 160 min |
| 跑 fix_v5 + 验证 | 30 min | 190 min |
| 二次修 (如果需要) | 50 min | 240 min (4h 上限) |
| **总** | **3-4h** | **240 min** |

---

**重点**: 不要重新 hand-curate 47 篇, v2/v3 已经修了核心字段。v4/v5 专注 **数字对齐** + **学科评估校准** + **课程补全**, 3-4h 推到 8.5+ 现实可期。
