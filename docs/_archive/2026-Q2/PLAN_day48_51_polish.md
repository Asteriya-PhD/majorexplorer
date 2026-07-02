# Day 48 Plan — 51 篇 ≤6 polish 提升到 ≥8

> **承接**: Day 47.11 (commit b842a8e9) 已完成全部 P0/P1/P2 修复
> **目标**: 51 篇 ≤6 提升到 ≥8, 推动 avg 8.14 → 8.5+, ≥7 比例 92% → 97%
> **当前状态**: 639 audited / 22 篇 10 分 / 195 篇 9 分 / 367 篇 8 分 / 4 篇 7 分 / 28 篇 6 分 / 5 篇 5 分 / 18 篇 4 分 / 3 篇 null

---

## 🎯 Top 12 优先 (3-5 session)

按 (score ↑, audits ↓) 排序 — **低分 + 高 audit 数 = variance 真硬伤**, 必须先 polish 否则 R2/R3 也拉不动。

| # | slug | 标题 | 分数 | audits | 主要硬伤 |
|---|------|------|------|--------|----------|
| 1 | logistics-management | 物流管理 | 4 | 14 | lede 数据列表无主语 / salary 京东顺丰 5年 25-40万虚高 / curriculum 上海海事大学方向串课 |
| 2 | food-hygiene-nutrition | 食品卫生与营养学 | 4 | 12 | lede 模板句 / salary 10年+ p75 100万虚高 / curriculum 妇幼/老年营养重复 |
| 3 | journalism | 新闻学 | 4 | 12 | lede 与 summary 复制 / salary 应届 p75 14.4万偏低 / curriculum 人大武大选修重复 |
| 4 | flight-vehicle-control | 飞行器控制与信息工程 | 4 | 12 | lede 时间锚定过窄 / salary 应届 p75 38万偏低 / curriculum 缺导航/制导原理 |
| 5 | land-science-technology | 土地科学与技术 | 4 | 11 | lede "工科"说反 / salary p75 21.6虚高 / curriculum 植物营养学弱 |
| 6 | intelligent-medical-engineering | 智能医学工程 | 4 | 10 | lede "翻一倍"夸大 / salary p75 21.6虚高 / curriculum DSP 偏传统通信 |
| 7 | cryptology-science-technology | 密码科学与技术 | 4 | 10 | lede 数据自相矛盾 / salary 应届 p50 14.4 与 alum 32 冲突 / curriculum 量子密码合并欠妥 |
| 8 | auditing | 审计学 | 4 | 10 | lede 模板 / salary 10年+ p25=80 > p50=70 倒挂 / curriculum Python 不算审计核心 |
| 9 | computational-linguistics | 计算语言学 | 4 | 9 | lede 前100字口号化 / salary p75 应届12 vs overview 18-22 冲突 |
| 10 | intellectual-property | 知识产权 | 4 | 9 | lede "竞争最小"夸大 / salary 应届 12 vs summary 18-30 冲突 / curriculum 缺商标/著作权 |
| 11 | credit-management | 信用管理 | 4 | 8 | salary 应届 p75 15 vs top 蚂蚁 30-50 冲突 |
| 12 | health-law | 卫生健康法学 | 4 | 8 | lede 与 overview_v2.lede 重复 / salary 红圈医事起薪虚高 / curriculum 缺卫生法核心特色课 |

**期望**: 12 篇 polish → 8 篇 promote 到 ≥7 (66.7% ROI), avg +0.8-1.2/篇

---

## 🟡 Tier 2 — 13 篇 stuck 6 (≥9 audits 真硬伤)

这 13 篇 m3 反复跑都没动 — 真硬伤不是 variance。

| # | slug | 标题 | audits | 核心问题 |
|---|------|------|--------|----------|
| 13 | clinical-engineering-technology | 临床工程技术 | 8 | lede 与 overview_v2.lede 重复 / salary 数据混入生物医学工程 082601 |
| 14 | quantum-information-engineering | 量子信息工程 | 8 | lede 营销文案 / salary 顶尖 PhD 50-100虚高 / 5校特色填学校简介而非课程 |
| 15 | humanities-education | 人文教育 | 8 | lede 与 summary 脱节 / salary 县城 7万虚高 / curriculum 高数 B 4学分偏高 |
| 16 | statistics | 统计学 | 8 | lede 风险罗列 / salary 10年+ p25=20 < 5年 p25=25 倒挂 |
| 17 | breeding-science | 生物育种科学 | 6 | lede "80% 去农资" 无源 / salary 应届 p50 14 vs top 隆平 30-60 冲突 / 5校特色 credit=0 |
| 18 | judicial-police-studies | 司法警察学 | 6 | lede 句法混乱 / salary 副处 p75 45虚高 / curriculum 缺刑诉/刑执 |
| 19 | engineering-mechanics | 工程力学 | 13 | lede 200字过长 / salary 数字偏高 / curriculum ✅ |
| 20 | intelligent-vehicle-engineering | 智能车辆工程 | 13 | lede 数字夹杂 / salary 10年+ 高位虚高 |
| 21 | industrial-intelligence | 工业智能 | 13 | lede 与 summary 重复 / salary p25=100 > p50=70 倒挂 / curriculum credit=0 |
| 22 | safety-engineering | 安全工程 | 15 | lede 与 summary 重复 / salary 5年 p75 50 与"低于 IC"矛盾 / 缺河南理工 |
| 23 | bionic-science-engineering | 仿生科学与工程 | 15 | lede 后半堆数字 / salary 应届 p75 21.6虚高 |
| 24 | fintech | 金融科技 | 12 | lede "1500亿"无源 / salary 10年+ p25=20 < 5年 p50=40 倒挂 |
| 25 | audiology-speech-rehabilitation | 听力与言语康复学 | 12 | lede "30万缺口"未互证 / salary 10年+ p75 100虚高 / top 腾讯阿里应届 20-32 虚高 |

---

## 🟢 Tier 3 — 26 篇 5-6 分 (需 polish, 部分可 irreducible-7 flag)

5 分 (5 篇): chemistry, recording-arts, economic-law, overseas-interests-security, economics-finance
6 分 (26 篇): marine-fishery, accounting, supply-chain, flight-technology, visual-communication, stomatology, intelligent-medical-engineering, intelligent-sports, applied-chinese, civil-law, science-education, kyrgyz, ethnology, intelligent-science-technology, criminal-procedure, insurance, digital-humanities, chinese-veterinary-medicine, marine-information-technology, agricultural-intelligent-equipment, ndebele, credit-management 等

**策略**: m3 audit 反复跑仍 5-6 的 (≥8 audits) 标 `irreducible-<N>`, 跳过 R2/R3 防止浪费 LLM 成本。

---

## 📋 4 大 Anti-Pollution 前置 (任何 polish 必读)

1. **lede 模板套话** ❌ "X 是研究...的学科" / "传统机械/材料的同学..." / "AI 翻译时代, 学科训练的价值是问对问题"
   → ✅ "X 的核心是 A+B+C 三栖, 它在 P 时代有 Q 优势, 但 R 是该专业最大风险"
2. **who_fits_no 串台** ❌ 理工科出现"文本阅读/田野调研/历史/语文"
3. **deep_study CS/金融 12%** ❌ "跨学科就业 (CS/数据/金融)": 12 + "国内硕士": 25 占位
4. **curriculum 公共必修填专业课** ❌ 工程水文学/卫生法学总论 放公共必修

---

## 🔁 流水线 (每篇)

```
1. Audit Driven (必读 m3 audit issues)
2. Anti-Pollution 4 Rules (前置必避)
3. Hand-Write JSON (按专业逐字段, 完整 18 字段 schema)
4. Render + Deploy (wrangler pages deploy public/)
5. Audit Verify (≥7 才继续)
6. Tier 1/2/3 Retry:
   - Tier 1 (5-10min): 补 weak field
   - Tier 2 (15-20min): 完全重写 + 参考 P0 案例
   - Tier 3 (≤45min): flag: irreducible-<N> 标记跳过
7. Single Commit Per Major
8. Schema Cleanup (合并后批量)
9. Full Batch Audit + Push
```

---

## 🎯 4 P0 优秀参考案例 (Tier 2 重写时必读)

- `skills/gaokao-major-explorer/data/curated/computational-linguistics.json` (humanities, 半文半理 AI) — **注意**: 这篇 score 4, 模板已列但需 Tier 2 完全重写
- `skills/gaokao-major-explorer/data/curated/electronic-science-technology.json` (eng, 器件+IC+材料)
- `skills/gaokao-major-explorer/data/curated/health-law.json` (law, 医学+法学+公共政策) — **注意**: 这篇 score 4, 需 Tier 2
- `skills/gaokao-major-explorer/data/curated/cultural-relics-museology.json` (humanities, 田野+策展+修复)

---

## ⚠️ 6 个已知坑

1. **`scripts/batches/content_audit.py` slug 用文件名**, 不用 JSON 内 slug. 例: `computational-linguistics.json` → `--slugs computational-linguistics:humanities`
2. **批量 (≥10 篇) 用 `scripts/audit/smart_audit.py` 替代**, 不要全量跑 content_audit
3. **m3 audit "字段截断" 是显示 bug**, 数据完整即可
4. **m3 audit 评分主观** (同一篇 ±1 分波动), 取多次 audit 平均
5. **CC Write 在某些 worktree 会被 revert**, 启动前用 `echo test > file && cat file` 测试
6. **C session 习惯性留 "自主创业/其他" 占位 + salary string schema**, 合并后必清理

---

## 📊 验收标准

| 指标 | 目标 | 最低 |
|------|------|------|
| Top 12 polish promote | 8/12 ≥7 | 6/12 |
| 13 篇 stuck promote | 6/13 ≥7 | 4/13 |
| 26 篇 Tier 3 | 14/26 ≥7 (含 8 篇 irreducible flag) | 10/26 |
| 8+ 总比例 | 95%+ | 92% |
| avg | 8.5+ | 8.3 |
| 单篇耗时 | 30 min | 60 min |

**总估**: 3-5 session, ~¥80-120, ~150 commits

---

## 🔍 51 篇全部列表 (按 score + audits 排)

| # | slug | title | score | audits |
|---|------|-------|-------|--------|
| 1 | logistics-management | 物流管理 | 4 | 14 |
| 2 | food-hygiene-nutrition | 食品卫生与营养学 | 4 | 12 |
| 3 | journalism | 新闻学 | 4 | 12 |
| 4 | flight-vehicle-control | 飞行器控制与信息工程 | 4 | 12 |
| 5 | land-science-technology | 土地科学与技术 | 4 | 11 |
| 6 | intelligent-medical-engineering | 智能医学工程 | 4 | 10 |
| 7 | cryptology-science-technology | 密码科学与技术 | 4 | 10 |
| 8 | auditing | 审计学 | 4 | 10 |
| 9 | computational-linguistics | 计算语言学 | 4 | 9 |
| 10 | intellectual-property | 知识产权 | 4 | 9 |
| 11 | credit-management | 信用管理 | 4 | 8 |
| 12 | health-law | 卫生健康法学 | 4 | 8 |
| 13 | clinical-engineering-technology | 临床工程技术 | 4 | 8 |
| 14 | quantum-information-engineering | 量子信息工程 | 4 | 8 |
| 15 | humanities-education | 人文教育 | 4 | 8 |
| 16 | statistics | 统计学 | 4 | 8 |
| 17 | breeding-science | 生物育种科学 | 6 | 6 |
| 18 | judicial-police-studies | 司法警察学 | 6 | 6 |
| 19 | economics-finance | 经济与金融 | 5 | 10 |
| 20 | chemistry | 化学 | 5 | 9 |
| 21 | recording-arts | 录音艺术 | 5 | 8 |
| 22 | economic-law | 经济法 | 5 | 8 |
| 23 | overseas-interests-security | 海外利益安全 | 5 | 8 |
| 24 | ndebele | 恩德贝莱语 | 6 | 17 |
| 25 | safety-engineering | 安全工程 | 6 | 15 |
| 26 | bionic-science-engineering | 仿生科学与工程 | 6 | 15 |
| 27 | engineering-mechanics | 工程力学 | 6 | 13 |
| 28 | intelligent-vehicle-engineering | 智能车辆工程 | 6 | 13 |
| 29 | industrial-intelligence | 工业智能 | 6 | 13 |
| 30 | agricultural-intelligent-equipment-engineering | 农林智能装备工程 | 6 | 13 |
| 31 | fintech | 金融科技 | 6 | 12 |
| 32 | audiology-speech-rehabilitation | 听力与言语康复学 | 6 | 12 |
| 33 | chinese-veterinary-medicine | 中兽医学 | 6 | 12 |
| 34 | medical-imaging | 医学影像学 | 6 | 11 |
| 35 | marine-fishery-science-technology | 海洋渔业科学与技术 | 6 | 11 |
| 36 | accounting | 会计学 | 6 | 11 |
| 37 | supply-chain-management | 供应链管理 | 6 | 10 |
| 38 | flight-technology | 飞行技术 | 6 | 10 |
| 39 | visual-communication-design | 视觉传达设计 | 6 | 10 |
| 40 | stomatology | 口腔医学 | 6 | 9 |
| 41 | marine-information-technology | 海洋信息技术 | 6 | 9 |
| 42 | intelligent-sports-engineering | 智能体育工程 | 6 | 9 |
| 43 | applied-chinese | 应用中文 | 6 | 9 |
| 44 | civil-law-jurisprudence | 民法 | 6 | 9 |
| 45 | science-education | 科学教育 | 6 | 9 |
| 46 | kyrgyz-language | 吉尔吉斯语 | 6 | 9 |
| 47 | ethnology | 民族学 | 6 | 8 |
| 48 | intelligent-science-technology | 智能科学与技术 | 6 | 8 |
| 49 | criminal-procedure | 刑事诉讼法 | 6 | 8 |
| 50 | insurance | 保险学 | 6 | 8 |
| 51 | digital-humanities | 数字人文 | 6 | 6 |

---

## 🎯 开 session 后执行顺序

1. **Phase A** (前 3 session): Top 12 (4-5 分) + 5 篇 5 分 = 17 篇 polish
   - 用 `smart_audit.py` 跑 Layer 2 LLM
   - 单篇 Tier 1 patch → Tier 2 完全重写 (参考 4 P0 案例)
2. **Phase B** (4 session): 13 篇 stuck 6 + 14 篇 6 分 = 27 篇 polish
   - 8 篇反复 stuck (≥8 audits) 标 `irreducible-7`, 跳过 R2/R3
3. **Phase C** (5 session): 7 篇剩余 6 分 + 全量 final audit + push
4. **Phase D**: 聚合统计 — ≥7 比例 92% → 97%, avg 8.14 → 8.5

**起手命令**:
```bash
python3 scripts/smart_audit.py --dry-run --min-score 6  # 看 Phase A 候选
LLM_PROVIDER=m3 set -a && source .env && set +a
python3 scripts/batches/content_audit.py --slugs logistics-management:eng food-hygiene-nutrition:medicine journalism:humanities flight-vehicle-control:eng land-science-technology:agri intelligent-medical-engineering:medicine
```

**pre-session reminder**:
- 读 `docs/PIPELINE_major_quality.md` 4 anti-pollution
- 读 `CLAUDE.md` Day 47 上下文
- 用 `python3 scripts/audit/update_audit_registry.py --stats` 看进度