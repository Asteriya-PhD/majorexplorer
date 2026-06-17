# Day 3 Team B D + E + F 阶段 Handoff (2026-06-18+)

> 写于 2026-06-17, 7 篇 Tier 2 收尾 + 8 commits push main 后.

---

## 当前状态 (2026-06-17 19:00)

- **m3 audit 8+ 篇数**: 7+ 篇 (8 commits push main, 51dca42 → d7dba59)
- **累计精品**: 47 (Day 3 Team B 跨学科) + 8 (Tier 2 polish) = **55 篇 ≥7/10**
- **m3 avg 7.69/10**, 100% ≥7, 64% ≥8

## D 阶段: m3 audit variance 二次确认 (估时 1-2h)

**目标**: 47+8 = 55 篇 m3 audit 二次确认, 排除 variance 后真实 ≤7/10 篇数

```bash
# 1. 跑全量 audit
source .env
python3 scripts/batches/content_audit.py --csv scripts/batches/day3_team_b.csv 2>&1 | tee test_results/day3_v2_audit.log

# 2. 找 ≤7/10 篇
cat test_results/day3_v2_audit.log | grep "7/10\|6/10\|5/10" | head -20

# 3. 二次 audit 确认 (排除 variance)
python3 scripts/batches/content_audit.py --slugs intelligent-marine-equipment:eng food-hygiene-nutrition:eng ...

# 4. 列出真正需要修的篇 (avg < 7 OR 2 次 audit 都 < 7)
```

**已知 ≤7/10 候选 (从最新 audit)**:
- intelligent-marine-equipment 7/10 (eng)
- intelligent-transportation 7/10 (eng)
- industrial-intelligence 7/10 (eng)
- food-hygiene-nutrition 7/10 (eng)
- smart-agriculture 7→8 ✅ (已修, 跳过)
- international-journalism-communication 7/10 (humanities)
- digital-economy 7/10 (finance)
- cross-border-ecommerce 7→9 ✅ (已修, 跳过)
- public-relations 7/10 (humanities)
- cultural-industry-management 7/10 (humanities)
- world-history 7/10 (humanities)
- food-quality-safety 7/10 (eng)
- integrated-chinese-western-medicine 7/10 (medicine)

**估 8-11 篇真 ≤7/10** (扣掉已修的 smart-agriculture, cross-border-ecommerce, bionic, ophthalmology, smart-agriculture, rural-regional-development, service-science, cyber-information-law, remote-sensing, global-climate).

## E 阶段: 11 篇剩余 polish (估时 3-4h)

**3 个并行 agent 跑批 (每 3-4 篇)**:
- agent 1: intelligent-marine-equipment + intelligent-transportation + industrial-intelligence + food-hygiene-nutrition (4 篇 eng)
- agent 2: international-journalism-communication + digital-economy + public-relations + cultural-industry-management (4 篇 humanities/finance/business)
- agent 3: world-history + food-quality-safety + integrated-chinese-western-medicine (3 篇 humanities/eng/medicine)

**每个 agent prompt 模板** (基于 day3-team-b-sop-enforcement-3-layer-2026-06-17):
1. 读 docs/PIPELINE_major_quality.md (必读)
2. 读 4 个 P0 案例 (computational-linguistics/electronic-science-technology/health-law/cultural-relics-museology)
3. 读 docs/HANDOFF_day3_team_b_d_e_f.md (本文件, 看 D 阶段结果)
4. 处理分配的 3-4 篇
5. 每篇按 7 步骤: read JSON → Tier 2 rewrite → verify JSON → render → deploy → audit verify ≥8 → commit
6. 返回 before/after score + commit hash

**4 anti-pollution rules** (任何 1 条触发 audit ≤6):
1. lede 模板套话 ❌ → ✅ 主语+独特洞察
2. who_fits_no 串台 ❌ → ✅ 删文理串台词
3. deep_study CS/金融 12% 占位 ❌ → ✅ 真实主流去向
4. curriculum 公共必修填专业课 ❌ → ✅ 高数/英语/思政

**7 已知坑**:
1. deploy_to_public.py ROOT 写死 (手动 re.sub)
2. content_audit.py slug 用 filename
3. m3 字段截断是 display bug
4. m3 ±1 variance (取多次平均)
5. CC Write worktree revert (启动前 echo test)
6. merge 时 stash
7. C session 自主创业占位 (合并后清理)

## F 阶段: Day 4 30 篇全新 major (估时 6-10h, 0¥ 0 违规)

**3 类主题方向**:
- 跨学科 (12 篇): 计算社会科学/数字艺术/AI 伦理/碳金融/新能源材料/海洋技术 等
- 一带一路 (8 篇): 阿语/俄语/西班牙语/葡语 等小语种 + 国际经贸/国际法 等
- AI 时代新工科 (10 篇): 人工智能/数据科学/量子信息/区块链/生物信息 等

**复用 3 agent 并行 playbook** (每 agent 10 篇).

**单篇成本**:
- deepseek-v4-flash: ¥0.02/M (cache hit), 30 篇 ≈ ¥5
- m3 audit: ¥1.75/篇, 30 篇 ≈ ¥52
- 渲染 + 部署: 0¥

**流水线**:
1. 选题 (30 篇)
2. 3 agent 并行写 (10 篇/agent)
3. 批量 audit 验证
4. 合并 + 推送
5. D 阶段 (m3 variance 二次确认) → E 阶段 (polish) → F 阶段 (新批)

## 关键 commands 速查

```bash
# Audit
source .env
python3 scripts/batches/content_audit.py --slugs <slug>:<style>
python3 scripts/batches/content_audit.py --csv <file>.csv

# Render
python3 skills/gaokao-major-explorer/scripts/generate_dashboard.py \
  --data skills/gaokao-major-explorer/data/curated/<slug>.json \
  --style <style> \
  --output skills/gaokao-major-explorer/data/curated/<slug>.html

# Deploy (绕过 deploy_to_public.py ROOT bug)
python3 -c "
import re, pathlib
src = pathlib.Path(f'skills/gaokao-major-explorer/data/curated/<slug>.html').read_text()
new = re.sub(r'(src|href)=\"\.\./\.\./((?:js|css)/[^\"]+)\"', r'\1=\"/\2\"', src)
pathlib.Path(f'public/<slug>.html').write_text(new)
"

# Commit
git add skills/gaokao-major-explorer/data/curated/<slug>.{json,html} public/<slug>.html
git commit -m "fix(content): <major中文名> Tier 2 重做 (X/10 → Y/10)
- lede N→M <新洞察>
- deep_study N→M 拆 X, 合并 Y
- pitfalls N→M 删 <旧通用>, 改 N 条 <专业独有>:
  1. <myth/reality>
- top_schools N→M 删 <凑数校>, 加 N 所 <缺失校>
- salary N→M 调整 <失真项>
- employment_direction N→M 合并重复路径

m3 content_audit: X/10 → Y/10 (优秀/合格)"

# Push
git push origin main
```

## 验收标准

| 指标 | 目标 | 最低 |
|------|------|------|
| avg score | **8.0** | 7.5 |
| ≥7 比例 | 100% | 95% |
| ≥8 比例 | 80%+ | 50% |
| 0 strong | 0 | ≤5% |
| 单篇耗时 | 30 min | 60 min |

## 参考资源

- `docs/PIPELINE_major_quality.md` (179 行 9 步流水线)
- `skills/gaokao-major-explorer/data/curated/computational-linguistics.json` (P0 humanities)
- `skills/gaokao-major-explorer/data/curated/electronic-science-technology.json` (P0 eng)
- `skills/gaokao-major-explorer/data/curated/health-law.json` (P0 law)
- `skills/gaokao-major-explorer/data/curated/cultural-relics-museology.json` (P0 humanities)
- `memory/day3-team-b-*.md` (SOP + LLM audit + 9 篇 P0 + 12 篇 P1)

---

**最后更新**: 2026-06-17 19:00, 7 篇 Tier 2 收尾 + 8 commits push main.
