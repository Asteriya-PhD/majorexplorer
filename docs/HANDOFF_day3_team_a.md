# Day 3 Team A Handoff — 2026-06-17

**给下个 session agent 的话**:
读这份文件,继续手写 36 篇剩余 majors,目标 m3 audit ≥ 8/10 (实际已达 9.93-10.0/10 for hand-coded)。

---

## 1. 环境/位置 (重要)

```bash
# Team A worktree (不是主仓!)
cd /Users/zhewenliu/Claude/gaokao-team-a

# 分支
git branch  # 期望: day3-team-a
git log --oneline -3
# 13848d6 fix(content): +11 篇精雕 (anesthesiology/basic-medicine 9.93-10.0)
# 13d3b3f fix(content): 47 篇 m3 synth + 9 篇精雕 + render+deploy + schema fix
```

**主仓 = main 分支 = 干净,不要动。**
**所有 work 都在 ../gaokao-team-a (worktree)**。

---

## 2. 现状

| 项目 | 状态 |
|------|------|
| m3 synth 47 篇 | ✅ 全在 worktree |
| Hand-code 11 篇 | ✅ deepseek 9.49-10.0/10 |
| Render + Deploy 47 篇 | ✅ public/ 已推送 |
| Audit 抽 10 篇 | ✅ avg 5.30 (都是未手改的 38 篇) |
| Commit + push | ✅ day3-team-a 分支 |

**已完成 11 篇** (part1 9 + part2 2):
- blockchain-engineering, chemical-biology, clinical-engineering-technology, preventive-medicine, psychiatry
- geoinformation-science-technology, digital-twin-technology, intelligent-mining-engineering, medical-imaging
- anesthesiology, basic-medicine

**剩 36 篇未手改** (按 style 分):
- **medicine (8)**: audiology-speech-rehabilitation, clinical-medicine, food-hygiene-nutrition, forensic-medicine, intelligent-medical-engineering, ophthalmology-optometry, stomatology, tcm-rehabilitation
- **eng (13)**: aircraft-design-engineering, bionic-science-engineering, energy-power-engineering, energy-storage-science-engineering, food-science-engineering, industrial-intelligence, intelligent-construction, intelligent-manufacturing-engineering, intelligent-marine-equipment, intelligent-transportation, intelligent-vehicle-engineering, new-energy-science-engineering, smart-energy-engineering
- **cs (7)**: cryptology-science-technology, intelligent-science-technology, marine-information-technology, network-space-security, quantum-information-engineering, service-science-engineering, virtual-reality-technology
- **sci (3)**: bioinformatics, biomedical-engineering, global-climate-change
- **agri (5)**: agricultural-intelligent-equipment-engineering, land-science-technology, marine-fishery-science-technology, rural-regional-development, smart-agriculture

---

## 3. 关键脚本 (已 commit)

### `scripts/batches/hand_curate_day3.py`
- 9 篇精雕 (part1) — **是最佳模板参考**
- 每篇 ~150 行: top_schools (8 条) + employment_direction (8 条) + alumni_quotes (3 条) + pitfalls (5 条) + who_fits_yes (4 条) + who_fits_no (3 条) + lede + summary

### `scripts/batches/hand_curate_day3_part2.py`
- 2 篇精雕 (part2) — **紧凑模板 ~60 行/篇**,推荐继续用
- 用 helper `apply(p_slug, *, top_schools, employment_direction, alumni_quotes, pitfalls, who_fits_yes, who_fits_no, lede, summary)`
- p_slug 不含 `.json` 后缀 (否则会拼成 `.json.json` 报错)

### `scripts/batches/schema_fix_v4.py`
- 必需: m3 synth 输出 schema 跟 v4_medicine.py 期望不匹配
- 自动 fix: curriculum / top_schools / top_companies / alumni_quotes / deep_study / salary / xuanke_req_list
- 每次 hand-code 后**必须跑** (否则 render 失败)

### 其他
- `scripts/batches/content_audit.py` — m3 content_audit (单篇 5-15s)
- `scripts/batches/render_batch.py` — render 47 HTML (但需 schema_fix 先跑)
- `scripts/deploy_to_public.py --csv ... --force` — deploy 到 public/

---

## 4. 推荐流程

```bash
cd /Users/zhewenliu/Claude/gaokao-team-a

# Step 1: 写 part2/3/4 (用 hand_curate_day3_part2.py 模板)
# 加 8-10 篇到 hand_curate_day3_part2.py 的 apply() 调用
python3 scripts/batches/hand_curate_day3_part2.py

# Step 2: schema fix (每次 hand-code 后跑)
python3 scripts/batches/schema_fix_v4.py

# Step 3: re-render
python3 scripts/batches/render_batch.py --csv scripts/batches/day3_team_a.csv
# 应保持 47/47 成功

# Step 4: deploy
python3 scripts/deploy_to_public.py --csv scripts/batches/day3_team_a.csv --force

# Step 5: 抽样 audit (10 篇)
source .env && python3 scripts/batches/content_audit.py --csv scripts/batches/day3_team_a.csv --limit 10

# Step 6: commit + push
git add -A && git commit -m "fix(content): Day 3 Team A +N 篇精雕"
git push origin day3-team-a
```

---

## 5. 已知坑

1. **part2 apply()**: 传 `"anesthesiology"` (不加 `.json`)
2. **deep_study**: v4 期望 dict[key]=int(pct), m3 输出 str/dict-of-list/嵌套, 需 schema_fix
3. **salary**: v4 期望 `{stage: {p25, p50, p75, yoy}}`, m3 输出嵌套 regions/avg_entry 等多种格式
4. **xuanke_req_list**: v4 期望 list[dict], m3 输出 list[str]
5. **top_companies**: v4 期望 list[dict{name, ...}], 旧版 list[str] 需转 dict
6. **top_schools str list**: "校名 (描述)" 拆成 `{name, rank: ★★★★☆, tag: 描述}`

---

## 6. 关联 Plan / 文档

- `docs/PLAN_day3_dual_team.md` — 完整 7 阶段 plan
- `docs/PROGRESS_day3.md` — 进度跟踪 (47 篇清单 + commit 历史)
- `memory/session-2026-06-17-day3-team-a-handoff.md` — (待写) session memory

---

## 7. 完成定义

- [ ] 47 篇全部 hand-code (deepseek audit ≥ 9/10)
- [ ] Render 47/47 OK
- [ ] Deploy 47/47 OK
- [ ] Final audit 10 篇 avg ≥ 9/10
- [ ] Commit + push day3-team-a 分支
- [ ] (可选) merge day3-team-a → main (等 Team B 完成)