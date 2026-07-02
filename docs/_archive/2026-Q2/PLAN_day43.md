# Day 43 Plan: 88 篇精修 + 20 篇 irreducible-8 flag (2026-06-29)

> **目标**: 完成 Day 42 留 88 篇精修 (B2+B3 19 R3 verify + B 桶 28 + C 桶 23) + 20 篇 irreducible-8 flag
> **方法**: 4 阶段流水线 (R3 verify → B 桶 Tier 1 → C 桶 Tier 2 → flag), 按 ROI 排序
> **总估时**: 14-17h (3-4 session, 单 session ≤5h)

---

## 📊 Phase 0 Day 42 现状

| 指标 | Day 42 后 | Day 43+ 目标 |
|------|-----------|--------------|
| R2 完成 | 120 篇 (4 大类硬伤 82 篇 <8) | 88 篇 (82 留 + 6 修复) |
| A 桶 7 分 polish | 14 篇 (5 promote 8, 35.7% conv) | B2 10 + B3 9 R3 verify |
| B 桶 6 分待修 | 28 篇 (含 Day 42 demote 2 篇) | Tier 1 中修, 8-12 min/篇 |
| C 桶 4-5 分待修 | 23 篇 | Tier 2 deep rewrite, 15-20 min/篇 |
| irreducible-8 ≥10 审 | 20 篇 | 加 `flag: irreducible-8` + 接受 |
| 对抗审查 P0/P1 | 15+17 全 ship (Day 36) + 6 移动顶层页 404 (Day 42) | 0 遗留 |
| 8+ 总数 | 587/625 (94.0%) | **655/625 (104.8%, 8+ 30+ 篇 promote)** |

---

## 🌊 4 阶段流水线 (按 ROI 排)

### **阶段 0: B2 + B3 19 篇 R3 verify (1h)**

**目标**: 验 Day 42 polish 真实提升, 跟 B1 35.7% promote 对比

```bash
LLM_PROVIDER=m3 nohup python3 -u scripts/batches/content_audit.py --slugs \
  numerical-foundation-science:sci landscape-architecture2:agri bioinformatics:sci \
  environmental-science:sci smart-agriculture:agri nano-materials-technology:sci \
  business-japanese:humanities apiculture:agri international-journalism:humanities \
  physical-training:education big-data-management-application:administration \
  national-security-protection:gongan public-finance:finance digital-twin-technology:cs \
  theatre-education:arts library-science:administration postal-management:administration \
  criminology:gongan public-relations:arts > /tmp/r3_b2b3.log 2>&1 &
```

**期望结果** (按 Day 42 B1 经验):
- promote ≥8: 30-40% (5-7 篇)
- stayed 7: 50-60% (10-12 篇)
- demote ≤6: 5-15% (1-3 篇)
- 真 promote ≥9: 0 (起点 7 上限 +1)

**Deliverable**: `/tmp/r3_b2b3_results.json` (19 篇 R2→R3 对比)

---

### **阶段 1: B 桶 6 分 28 篇 Tier 1 中修 (5h)**

**目标**: 28 篇 6 → 7 提 1 分, 8-12 min/篇

**B 桶分桶** (按 style):

| Batch | Style | 篇数 | 估时 | 共享硬伤 |
|-------|-------|------|------|----------|
| B1.1 | eng | 11 | 2-2.5h | 工程类 deep_study 校招比例 + top_schools 凑数 |
| B1.2 | humanities | 5 | 1-1.5h | 文科 xuanke_req_list 误填 (ndebele 必改) |
| B1.3 | medicine | 4 | 1-1.5h | 医学 规培口径 + 公务员比例 |
| B1.4 | sci | 1 | 15 min | sci 深造口径 |
| B1.5 | finance | 3 | 1h | 金融薪资口径统一 |
| B1.6 | administration + others | 4 | 1h | 管理学 deep_study 与 employment 口径 |

**28 篇 list** (按 audit_count 降序排):
1. engineering-mechanics (eng) — 校招比例失衡, top_schools 学科评估错
2. safety-engineering (eng) — Day 30 已 polish, 仍 6/10
3. intelligent-vehicle-engineering (eng) — 比亚迪/小鹏/小米车 BU 风向
4. fintech (finance) — 5 大所 + CFA + MBA 路径
5. medical-imaging (medicine) — 医学影像规培
6. stomatology (medicine) — 口腔医院 + 诊所
7. ethnology (humanities) — 田野调研 + 民族学
8. supply-chain-management (finance) — 京东/顺丰/极兔
9. marine-information-technology (cs) — 海洋信息
10. audiology-speech-rehabilitation (medicine) — 听力学
11. digital-humanities (humanities) — 数字人文
12. bionic-science-engineering (eng) — 仿生
13. intelligent-science-technology (cs) — 智能科技
14. intelligent-sports-engineering (education) — 智能体育
15. flight-technology (eng) — 飞行技术
16. chinese-veterinary-medicine (agri) — 中兽医
17. ndebele (humanities) — 小语种 必改
18. applied-chinese (humanities) — 实用中文
19. civil-law-jurisprudence (law) — 民法学
20. criminal-procedure (law) — 刑事诉讼
21. insurance (finance) — 保险学
22. science-education (education) — 学科教学
23. kyrgyz-language (humanities) — 吉尔吉斯语
24. marine-fishery-science-technology (agri) — 海洋渔业
25. accounting (business) — 会计学 Day 30 修过
26. visual-communication-design (arts) — 视传 Day 30 修过
27. agricultural-intelligent-equipment-engineering (eng) — Day 42 修复后 6 → 7 polish
28. industrial-intelligence (eng) — Day 42 修复后 6 → 7 polish

**单篇 polish 流程 (8-12 min)**:
1. R3 audit 看 m3 真实问题
2. 修 2-3 个硬伤 (vs A 桶 1-2 个)
3. 验证 salary 4 阶段 + top_schools 教育部代码 + deep_study 100%
4. 跑 `python3 scripts/build/render_one.py <slug>` 重生
5. 1 commit per major (Day 36+ 老规矩)

**预期**:
- 16-20 篇 promote ≥7 (60-70% conv, vs A 桶 35.7% — B 桶起点低 1 分, 提升空间大)
- 8+ 总数 587 → 605 (+18)
- 7-8 段 26 → 14 (-12)

---

### **阶段 2: C 桶 4-5 分 23 篇 Tier 2 deep rewrite (8-9h)**

**目标**: 23 篇 4-5 → ≥7 提 2-3 分, 15-20 min/篇

**Tier 2 deep rewrite 区别于 Tier 1**:
- Tier 1: 1-3 个硬伤, 修字段, 数据保持
- Tier 2: 全文重写 lede + pitfalls + alumni + curriculum, 不止修字段

**23 篇 list** (按 audit_count 降序排):
1. computational-linguistics (humanities) — 4/10, 跨学科半文半理 AI, Day 30 P0 案例
2. health-law (law) — 4/10, 医学+法学+公共政策, Day 30 P0 案例
3. cultural-relics (humanities) — 已 ship, 不在 list
4. credit-management (finance) — 4/10, 信用管理
5. intelligent-medical-engineering (medicine) — 4/10, 智能医学工程
6. clinical-engineering-technology (medicine) — 4/10, 临床工程
7. food-hygiene-nutrition (medicine) — 4/10, 食品卫生
8. land-science-technology (agri) — 4/10, 土地科学
9. quantum-information-engineering (eng) — 4/10, 量子信息
10. cryptology-science-technology (cs) — 4/10, 密码科学
11. journalism (humanities) — 4/10, 新闻学
12. auditing (business) — 4/10, 审计学
13. recording-arts (arts) — 5/10, 录音艺术
14. chemistry (sci) — 5/10, 化学
15. economic-law (law) — 5/10, 经济法
16. humanities-education (education) — 4/10, 人文教育
17. intellectual-property (law) — 4/10, 知识产权
18. logistics-management (administration) — 4/10, 物流管理 Day 30 修过
19. overseas-interests-security (law) — 5/10, 海外利益安全
20. statistics (sci) — 4/10, 统计学
21. breeding-science (agri) — 4/10, 生物育种
22. flight-vehicle-control (eng) — 4/10, 飞行器控制
23. economics-finance (finance) — 5/10, 经济与金融
24. judicial-police-studies (gongan) — 4/10, 司法警察学

**Tier 2 流程 (15-20 min/篇)**:
1. R3 audit 看 m3 真实问题 (3 min)
2. **完全重写** 而非 patch (8-12 min):
   - lede 重写 (一句核心洞察, 不用"X 是研究...的学科"模板)
   - pitfalls 全部用 overview_v2.pitfalls 替换通用版
   - top_schools 用真实开设院校 (不凑数)
   - salary 4 阶段校准 (10年+ ≥ 5年 p25, 100 万 cap)
   - deep_study 100% (避免与 employment 矛盾)
3. 跑 `render_one.py` + `python3 scripts/audit/update_audit_registry.py --from-file <r2报告>`
4. 1 commit per major

**P0 参考案例** (4 个, Tier 2 重写时必读):
- `computational-linguistics.json` (humanities, 半文半理 AI)
- `electronic-science-technology.json` (eng, 器件+IC+材料)
- `health-law.json` (law, 医学+法学+公共政策)
- `cultural-relics-museology.json` (humanities, 田野+策展+修复)

**预期**:
- 18-20 篇 promote ≥7 (78-87% conv, C 桶 Tier 2 ROI 最高)
- 8+ 总数 605 → 625 (+20, 4 个已 ship 不算)
- ≤7 总数 38 → 5-10 (留 irreducible)

---

### **阶段 3: 20 篇 irreducible-8 flag (30 min)**

**目标**: 标记 ≥10 审仍 7-8 分篇为 irreducible, 避免后续 variance noise 误判

**20 篇 list** (按 audit_count 降序):
```
service-science-engineering        20审 7/10  cs
smart-agriculture                  16审 8/10  agri
global-climate-change              16审 8/10  sci
bioinformatics                     14审 8/10  sci   [B2 留 R3 verify]
bionic-science-engineering         14审 8/10  eng   [B 桶 #12]
advertising                        14审 8/10  humanities
ndebele                            14审 8/10  humanities [B 桶 #17]
criminal-investigation             14审 8/10  gongan
cross-border-ecommerce             13审 8/10  finance
cyber-information-law              12审 8/10  law    [B1 升 8]
remote-sensing-science-technology  12审 7/10  eng
safety-engineering                 11审 8/10  eng    [B 桶 #2]
intelligent-marine-equipment-eng   11审 8/10  eng    [B1 升 8]
logistics-management               11审 8/10  administration
flight-vehicle-control             11审 8/10  eng    [C 桶 #22]
international-economic-cooperation 11审 8/10  finance
intelligent-vehicle-engineering    10审 8/10  eng    [B 桶 #3]
digital-twin-technology            10审 8/10  cs
postal-engineering                 10审 8/10  eng
numerical-foundation-science       10审 8/10  sci    [B2 R3 verify]
```

**Flag 机制** (registry schema 扩展):
```json
{
  "majors": {
    "<slug>": {
      "current_score": 8,
      "audit_count": 16,
      "tier": "irreducible-8",   // 新增字段
      "irreducible_reason": "≥10 审仍 7-8, variance noise 概率 ≤20%"
    }
  }
}
```

**action**:
1. 改 `scripts/audit/update_audit_registry.py` 加 `tier` 字段
2. 加 20 条 entry
3. 1 commit 1 docs/irreducible-8-day43.md (20 篇报告)

---

## 📋 总验收清单 (Day 43-46 收口)

```bash
# 阶段 0 验证
jq '.majors | to_entries | map(select(.value.current_score == 7 and .value.audit_count >= 5)) | length' data/audit_registry.json  # 阶段 0 后 ≤ 30 (从 35 减 5)

# 阶段 1 验证
jq '.majors | to_entries | map(select(.value.current_score == 6 and .value.audit_count >= 3)) | length' data/audit_registry.json  # 阶段 1 后 ≤ 5 (从 28 减 23)

# 阶段 2 验证
jq '.majors | to_entries | map(select(.value.current_score <= 5 and .value.audit_count >= 3)) | length' data/audit_registry.json  # 阶段 2 后 ≤ 5 (从 23 减 18)

# 阶段 3 验证
jq '.majors | to_entries | map(select(.value.tier == "irreducible-8")) | length' data/audit_registry.json  # = 20

# 总 8+ 比例
jq '.majors | to_entries | map(select(.value.current_score >= 8)) | length' data/audit_registry.json  # ≥ 655
```

---

## 🧵 并行 vs 串行 决策

**串行 4 阶段** (沿用 Day 36-42 决策):
- 阶段 0: 1h (B2+B3 R3 verify 跑后台, 同时修阶段 1 的 polish)
- 阶段 1: 5h (B 桶 28 篇 Tier 1)
- 阶段 2: 8-9h (C 桶 23 篇 Tier 2 — **2 session 必跑**)
- 阶段 3: 30 min (registry schema 扩展 + flag)

**总耗时**: 14-17h (3-4 session, 每个 ≤5h)

**Session 切分建议**:
- **Session 1 (Day 43)**: 阶段 0 (1h) + 阶段 1 (5h) — **6h (超限, 拆 2 session)**
  - 实际: 阶段 0 + B 桶 B1.1-B1.3 (20 篇) 4h + 阶段 3 (30 min)
- **Session 2 (Day 44)**: 阶段 1 余 (B1.4-B1.6, 8 篇) 2h + 阶段 2 开头 (C 桶 #1-10) 4h = 6h
- **Session 3 (Day 45)**: 阶段 2 余 (C 桶 #11-23) 5h

---

## ⚠️ 风险 + 应对

| 风险 | 应对 |
|------|------|
| **B 桶 28 篇 polish 5h 超 session** | 拆 2 session (B1.1-B1.3 + B1.4-B1.6) |
| **C 桶 Tier 2 deep rewrite 单篇超时 30 min** | 真 irreducible 标 flag 跳过, 优先级让给 ROI 高的 |
| **R3 verify 与 B 桶 polish working tree 冲突** | B2+B3 R3 先跑完, 再做 B 桶 (working tree 干净) |
| **linter 反复 revert content_audit.py 工厂方法** | 不动 .py 文件, 用 git revert --hard 锁住 commit (4d769656 已含 4 fix) |
| **跨 session registry 冲突** | 每 session 末尾必 `git pull` + `update_audit_registry.py --rebuild` |
| **20 篇 irreducible 标 flag 后被 polish 提升** | 验证方法: 若 polish 后 R3 ≥9, 升级 tier = null + 移除 flag |
| **m3 thinking on 7+ min/篇 (linter 改回)** | PID 启动后 Python 进程内 .pyc 缓存, 监控; 改 think 关 .pyc |
| **Day 36 adversarial audit P1 留 8 项** | 留 P3 长期, 优先级 P0 当前 (移动 6 顶层页 404 已修) |

---

## 💡 与 Day 36-42 区别

**Day 36-42 是修"bug" + 模板化**:
- 13 P0 部署 bug + 18 P1 数据债 + Day 39 polish 121 篇
- 单 session 4-6h, 1 commit 1 bug

**Day 43+ 是修"主观质量" 深度重写**:
- 主观 KPI: m3 audit (3-5 分真硬伤 vs 4-8 分 variance noise)
- 真正薄利多销 — C 桶 Tier 2 deep rewrite 是 8+ 比例从 94% → 99%+ 关键
- **核心 ROI**: 23 篇 × 18 min = 7h 投入, 20 篇 promote ≥7 → +20 audit tier label

---

## 🎯 Day 43 Session 1 决策 (4-5h)

| # | 决策 | 选定 | 影响 |
|---|------|------|------|
| 1 | B2+B3 R3 verify 跑法 | **A** nohup 后台 1h, 同时手修 B 桶 | 2 并行, 省 1h |
| 2 | B 桶起始 batch | **A** B1.1 eng 11 篇 (audit_count 最高) | ROI 优先 |
| 3 | C 桶是否分 2 session | **A** 是 (8-9h 单 session 跑不完) | Day 44 接力 |
| 4 | irreducible-8 flag 实施 | **A** registry schema 扩展 + 1 docs | 30 min, 留 Day 43 末尾 |
| 5 | B 桶 28 篇单 commit vs 分 6 batch | **A** 单 commit "B 桶 6 分 Tier 1 28 篇 polish" | 简洁, 跟 Day 36-42 |

---

## 📅 时间预期

- **Session 1 (Day 43, 4-5h)**: 阶段 0 (1h 后台) + 阶段 1 B1.1-B1.3 (20 篇) (3-4h) + 阶段 3 (30 min) — 5h
- **Session 2 (Day 44, 5-6h)**: 阶段 1 余 (8 篇) (2h) + 阶段 2 开头 (C 桶 #1-12) (4h) — 6h
- **Session 3 (Day 45, 4h)**: 阶段 2 余 (C 桶 #13-23) (4h) — 4h

**总预期**: 14-17h (3-4 session, 跟 plan 估一致)

---

**生成时间**: 2026-06-29 19:15 (Day 42 polish+redirects session 末尾)
**分支**: `main` (Day 42 后 6 commits ahead)
**起点**: 88 篇待修 + 20 篇 irreducible-8 待 flag
**目标**: 0 桶剩 + 20 篇 flag + 8+ 比例 99%+ (Day 46 末)
