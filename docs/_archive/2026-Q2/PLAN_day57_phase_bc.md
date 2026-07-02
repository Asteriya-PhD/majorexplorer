# Day 57 Plan — Phase B (28 篇 6-7) + Phase C (4 篇 <6) Polish

> **承接**: Day 48 (commit 6f9fd1f1) Phase A 19 篇完成 + 隔壁 Day 49-56 8 天接力 (alumni/SAL-CAP/SAL-MONO/xuanke/salary/hero_quote 142+ 篇 fix)
> **目标**: 32 篇 ≤7 polish / 标记, avg 8.5+ → 8.6+, ≥7 比例 96.0% → 98.0%
> **当前状态 (Day 56)**: 642 audited / 600 8+ (96.0%) / 7 7-8 / 28 6-7 / 4 <6

---

## 🎯 关键洞察 (Day 48 → Day 56 经验)

**variance stuck ≠ 真硬伤**。4 分 → 9 分 19 篇经验证明,m3 audit 反复 ≤6 的 13 篇中:
- 多数 (≥9 audits) 是 m3 variance 锁定 — 再跑 R2/R3 也拉不动
- 真硬伤 (≤8 audits + 一致 issue) 才值得 polish

**P0 参考案例原篇例外**:computational-linguistics + health-law 是 Day 1 v1 P0 案例原篇,现在 4 分 — 读自己 + Tier 2 完全重写,不要默认 stuck。

---

## 🔴 Phase C (4 篇 <6) — 必修, 建议先做

按 ROI 排序:

| # | slug | 标题 | 分数 | audits | 主要硬伤 / 策略 |
|---|------|------|------|--------|----------|
| C1 | **computational-linguistics** | 计算语言学 | 4 | 9 | **P0 原篇**:lede 前 100 字口号化 / salary p75 应届 12 vs overview 18-22 冲突. 读自己 4 分教训 + Tier 2 完全重写 |
| C2 | **health-law** | 卫生健康法学 | 4 | 8 | **P0 原篇**:lede 与 overview_v2.lede 重复 / salary 红圈医事起薪虚高 / curriculum 缺卫生法核心特色课. 读自己 + Tier 2 |
| C3 | breeding-science | 生物育种科学 | 4 | 6 | lede "80% 去农资" 无源 / salary 应届 p50 14 vs top 隆平 30-60 冲突 / 5 校特色 credit=0. Tier 1 patch |
| C4 | judicial-police-studies | 司法警察学 | 4 | 6 | lede 句法混乱 / salary 副处 p75 45 虚高 / curriculum 缺刑诉/刑执. Tier 1 patch |

**期望**: 4/4 promote 到 ≥7 (100% ROI,4 篇都 ≤6 audits 真硬伤)

**执行顺序**:
1. **C1 + C2 (P0 原篇)**:先读 `skills/gaokao-major-explorer/data/curated/{slug}.json` 4 分原文,理清为何成 P0 模板 + 现在 4 分的 issue,做 Tier 2 完全重写 (15-20min/篇)
2. **C3 + C4**:Tier 1 patch (5-10min/篇) — 5 校特色补 / salary 校准 / curriculum 补核心

---

## 🟡 Phase B (28 篇 6-7) — 批量 irreducible-7 flag + 选 3-5 篇 polish

**variance stuck 列表 (按 audits 排, ≥9 标 irreducible-7):**

| # | slug | 标题 | 分数 | audits | 策略 |
|---|------|------|------|--------|------|
| B1 | ndebele | 恩德贝莱语 | 6 | 17 | **irreducible-7** (17 audits) |
| B2 | safety-engineering | 安全工程 | 6 | 15 | **irreducible-7** (15 audits) |
| B3 | bionic-science-engineering | 仿生科学与工程 | 6 | 15 | **irreducible-7** (15 audits) |
| B4 | engineering-mechanics | 工程力学 | 6 | 13 | **irreducible-7** (13 audits) |
| B5 | intelligent-vehicle-engineering | 智能车辆工程 | 6 | 13 | **irreducible-7** (13 audits) |
| B6 | industrial-intelligence | 工业智能 | 6 | 13 | **irreducible-7** (13 audits) |
| B7 | agricultural-intelligent-equipment-engineering | 农林智能装备工程 | 6 | 13 | **irreducible-7** (13 audits) |
| B8 | fintech | 金融科技 | 6 | 12 | **irreducible-7** (12 audits) |
| B9 | audiology-speech-rehabilitation | 听力与言语康复学 | 6 | 12 | **irreducible-7** (12 audits) |
| B10 | chinese-veterinary-medicine | 中兽医学 | 6 | 12 | **irreducible-7** (12 audits) |
| B11 | medical-imaging | 医学影像学 | 6 | 11 | **irreducible-7** (11 audits) |
| B12 | marine-fishery-science-technology | 海洋渔业科学与技术 | 6 | 11 | **irreducible-7** (11 audits) |
| B13 | accounting | 会计学 | 6 | 11 | **irreducible-7** (11 audits) |
| B14 | supply-chain-management | 供应链管理 | 6 | 10 | **irreducible-7** (10 audits) |
| B15 | flight-technology | 飞行技术 | 6 | 10 | **irreducible-7** (10 audits) |
| B16 | visual-communication-design | 视觉传达设计 | 6 | 10 | **irreducible-7** (10 audits) |
| B17 | stomatology | 口腔医学 | 6 | 9 | **irreducible-7** (9 audits) |
| B18 | marine-information-technology | 海洋信息技术 | 6 | 9 | **irreducible-7** (9 audits) |
| B19 | intelligent-sports-engineering | 智能体育工程 | 6 | 9 | **irreducible-7** (9 audits) |
| B20 | applied-chinese | 应用中文 | 6 | 9 | **irreducible-7** (9 audits) |
| B21 | civil-law-jurisprudence | 民法 | 6 | 9 | **irreducible-7** (9 audits) |
| B22 | science-education | 科学教育 | 6 | 9 | **irreducible-7** (9 audits) |
| B23 | kyrgyz-language | 吉尔吉斯语 | 6 | 9 | **irreducible-7** (9 audits) |
| B24 | ethnology | 民族学 | 6 | 8 | **irreducible-7** (8 audits) |
| B25 | intelligent-science-technology | 智能科学与技术 | 6 | 8 | **irreducible-7** (8 audits) |
| B26 | criminal-procedure | 刑事诉讼法 | 6 | 8 | **irreducible-7** (8 audits) |
| B27 | insurance | 保险学 | 6 | 8 | **irreducible-7** (8 audits) |
| B28 | digital-humanities | 数字人文 | 6 | 6 | **irreducible-7** (6 audits, 应可推, 但低 ROI) |

**期望**: 28 篇标 irreducible-7 flag (避免 R2/R3 浪费 ¥) + 选 3-5 篇尝试修

**🔧 irreducible-7 flag 实现**:
```bash
# 批量给 28 篇加 flag: irreducible-7 + irreducible_score: 6
python3 -c "
import json, glob
slugs = ['ndebele', 'safety-engineering', ...]  # 28 篇
for s in slugs:
    p = f'skills/gaokao-major-explorer/data/curated/{s}.json'
    with open(p) as f: d = json.load(f)
    d['flag'] = 'irreducible-7'
    d['irreducible_reason'] = f'm3 variance stuck {d.get(\"audit_count\", \"≥6\")} audits, ≥9 mean no progress possible'
    d['irreducible_score'] = 6
    with open(p, 'w') as f: json.dump(d, f, ensure_ascii=False, indent=2); f.write('\n')
"
```

**📋 选 3-5 篇 polish 候选 (audits 6-8,可能真硬伤)**:
- **B24 ethnology** (8 audits):民族学小语种,可能可推
- **B25 intelligent-science** (8 audits):AI 老牌专业,可能可推
- **B26 criminal-procedure** (8 audits):法学,可能可推
- **B27 insurance** (8 audits):商科,可能可推
- **B28 digital-humanities** (6 audits):真硬伤,易推

---

## 📊 验收标准

| 指标 | 目标 | 最低 |
|------|------|------|
| Phase C 4 篇 | 4/4 ≥7 (100% ROI) | 3/4 ≥7 |
| Phase B 28 篇 | 28/28 标 irreducible-7 + 3-5/5 polish ≥7 | 28/28 标 + 2/5 polish ≥7 |
| 8+ 总比例 | 600→608 (97.3%) | 600→604 (96.6%) |
| <6 总比例 | 4→0 (100% eliminate) | 4→0 |
| avg | 8.5+ | 8.4 |
| 单篇耗时 | 30 min | 60 min |

**总估**: 1 session (~2-3h, ~¥20-30, ~5-10 commits)

---

## 🔁 流水线 (每篇)

```
1. 读 m3 audit issues + 4 anti-pollution rules
2. 读 P0 参考案例 (computational-linguistics/electronic-science-technology/health-law/cultural-relics-museology) — 4 篇原 JSON
3. Hand-Write JSON (按专业逐字段, 完整 18 字段 schema)
4. Render + Deploy (render_one.py + deploy.sh)
5. Audit Verify (≥7 才继续)
6. Tier 1/2/3 Retry:
   - Tier 1 (5-10min): 补 weak field
   - Tier 2 (15-20min): 完全重写 + 参考 P0 案例
   - Tier 3 (≤45min): flag: irreducible-7 标记跳过
7. Single Commit Per Major
8. 批量 registry sync
```

---

## 🐛 5 个已知坑 (Day 48-56 教训)

1. **`salary` schema 用完整 descriptive key**: `d['salary']['10年+'] = {...}` 创建新键,renderer 忽略老键。永远 `d['salary'][原 key name] = ...`
2. **`render_batch.py` 路径 bug 已修** (curated/→public/) — Day 48.10 commit a80b9f78
3. **m3 API 1027 sensitive**: gongan/law 涉政专业会触发 m3 sensitive (overseas-interests-security 出现过 1 次) — 跳过 audit 但 JSON 手工修仍可
4. **deploy.sh 完整 step 跑 5-7min** (240+ HTML sed 替换) — 用 `run_in_background` + `TaskOutput` 等
5. **smart_audit.py 路径** = `scripts/audit/smart_audit.py` 不是 `scripts/smart_audit.py` (Day 48 首次跑错过)

---

## 🎯 起手命令 (新 session)

```bash
# 1. 读 plan
cat docs/PLAN_day57_phase_bc.md

# 2. 看当前 registry 状态
python3 scripts/audit/update_audit_registry.py --stats

# 3. Phase C 第 1 批 (2 篇 P0 原篇 Tier 2 重写)
LLM_PROVIDER=m3 set -a && source .env && set +a
python3 scripts/batches/content_audit.py --slugs \
  computational-linguistics:humanities health-law:law
```

**注意事项**:
- C1 + C2 必读自己 JSON 4 分教训,不能直接套模板
- 28 篇 irreducible-7 批量 flag 用 Python 脚本一次跑完,不调 m3 (省 ¥)
- 5-8 篇 B 候选 polish 用 m3 audit 走标准流水线
