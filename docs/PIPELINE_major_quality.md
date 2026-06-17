# Major 精品质量流水线 v1.0 (Day 3 Team B 经验总结)

> 写于 2026-06-17, 47 篇验证: 平均 7.69/10, 100% ≥7, 64% ≥8.
> 目标: 后续主题稳定达到 **平均 8.0/10** 水准.

---

## 9 步流水线 (每批 30-50 篇)

### Step 1: Audit Driven (必读)

```bash
# 跑 m3 audit 拿到每篇 issue
source .env
python3 scripts/batches/content_audit.py --slugs <slug>:<style>
```

读 audit 输出:
- `overall_score` < 7 必须修复
- `issues` 列出每字段 score, score 0/null 即缺失字段
- `fix_suggestion` 是 m3 给的具体修法建议

### Step 2: Anti-Pollution 4 Rules (前置必避)

| Rule | ❌ 错 | ✅ 对 |
|------|------|------|
| **lede 模板** | "X 是研究...的学科", "传统机械/材料的同学需要主动学 AI/数据/碳中和", "AI 翻译/生成式写作时代, 学科训练的真正价值是问对问题" | "X 的核心是 A+B+C 三栖, 它在 P 时代有 Q 优势, 但 R 是该专业最大风险" |
| **who_fits_no 串台** | 理工科出现"文本阅读/田野调研/历史/语文/写作训练" → 删, 改为物理/数学/工程/实验 | 人文社科出现"数学/统计/经济/考证" → 删, 改为文字功底/理论兴趣/表达沟通 |
| **deep_study CS/金融 12%** | "跨学科就业 (CS/数据/金融)": 12, "国内硕士 (专业相关方向)": 25 | 用专业真实主流去向 (翻译→MTI/外派/出版; 农林→基层公务员; 体育→体育产业) |
| **curriculum 公共必修填专业课** | 公共必修填"工程水文学/卫生法学总论/模拟集成电路/机器人学" | 公共必修只放高数/线代/概率/物理/英语/思政/制图 |

### Step 3: Hand-Write JSON (按专业逐字段)

完整 schema 见 `skills/gaokao-major-explorer/SKILL.md`. 必填字段:

```jsonc
{
  "title": "...", "slug": "...", "style": "eng|finance|...|humanities",
  "category": "学科门类 · 专业类",
  "degree": "...学士", "duration_years": 4,
  "tags": [...], "difficulty": "★★★★☆",
  "summary": "≤150 字, 钩子",
  "hero_quote": "...",
  "overview_v2": {
    "lede": "≤100 字, 主语+独特洞察",
    "what_you_learn": "大一/大二/大三/大四分段",
    "who_fits_yes": [...4 条],
    "who_fits_no": [...4 条],
    "pitfalls": [...5-7 条 myth/reality]
  },
  "curriculum": {
    "公共必修 (所有院校都开)": [高数/英语/思政...],
    "通用专业核心 (≈ 80% 院校覆盖)": [...],
    "5 校特色选修 (按方向分流)": [...按校写, 不是泛泛]
  },
  "top_schools": [...6-10 所, 每所含城市·特色 tag],
  "top_companies": [...6-10 家, S/A/B tier + sparkline],
  "employment_direction": [...5-8 方向, 百分比合计 100%],
  "salary": {"阶段名": {"p25": x, "p50": y, "p75": z, "yoy": w}},
  "alumni_quotes": [...3-5 条, 每条含 year/current/school/source/quote, quote 含"修了X/做过Y/去了Z"],
  "deep_study": {"路径名": 百分比},  // 5-7 路径合计 ≈ 100%
  "xuanke_req_list": [..., 每项含 pct]
}
```

### Step 4: Render + Deploy

```bash
# 渲染
python3 skills/gaokao-major-explorer/scripts/generate_dashboard.py \
  --data skills/gaokao-major-explorer/data/curated/<slug>.json \
  --style <style> \
  --output skills/gaokao-major-explorer/data/curated/<slug>.html

# 部署到 public/ (绕过 deploy_to_public.py ROOT bug)
python3 -c "
import re, pathlib
src = pathlib.Path(f'skills/gaokao-major-explorer/data/curated/{slug}.html').read_text()
new = re.sub(r'(src|href)=\"\.\./\.\./((?:js|css)/[^\"]+)\"', r'\1=\"/\2\"', src)
pathlib.Path(f'public/{slug}.html').write_text(new)
"
```

### Step 5: Audit Verify (≥7 才继续)

```bash
source .env
python3 scripts/batches/content_audit.py --slugs <slug>:<style>
# 期望 overall_score ≥ 7
```

### Step 6: Tier Retry (audit < 7 时)

| Tier | 触发 | 操作 | 时间 |
|------|------|------|------|
| 🟡 Tier 1 | audit 5-6 | 补 weak field (见 audit issues) | 5-10 min |
| 🟠 Tier 2 | 仍 < 7 | 完全重写 + 参考 P0 优秀案例 (计算语言学/电子科技/卫生法学) | 15-20 min |
| 🔴 Tier 3 | 3 次仍 < 7 | commit `flag: irreducible-<Y>` + 继续下一篇 | ≤45 min |

### Step 7: Single Commit Per Major

```bash
git add skills/gaokao-major-explorer/data/curated/<slug>.{json,html} public/<slug>.html
git commit -m "fix(content): <major中文名> P{0,1,2,3} 重做 (X/10 → Y/10)
... (具体改了什么)
m3 content_audit: X/10 → Y/10 (优秀/合格)"
```

### Step 8: Schema Cleanup (合并后批量)

每次 batch merge 后**必做**:

```python
# 拆细 "自主创业/其他" 占位 (按专业映射具体路径)
ENTREPRENEUR_MAP = {
    '<slug>': '自主创业 (具体路径)',
    ...
}

# 统一 salary string → p25/p50/p75 对象
# 解析 '月薪 8K-12K' → {p25, p50, p75, yoy}
```

然后重渲染 + deploy 受影响篇。

### Step 9: Full Batch Audit + Push

```bash
# 跑全部 audit (建议 30 篇一批避免 timeout)
python3 scripts/batches/content_audit.py --csv all_majors.csv

# 验证全部 ≥7, 修不合格篇
# Push 到 origin
git push origin day3-team-b
```

---

## 验收标准

| 指标 | 目标 | 最低 |
|------|------|------|
| 平均分 | **8.0** | 7.5 |
| ≥7 比例 | 100% | 95% |
| ≥8 比例 | 80%+ | 50% |
| 0 strong (字段完全缺失) | 0 | ≤5% |
| 单篇耗时 | 30 min | 60 min |

---

## 已知坑 (避免)

1. **deploy_to_public.py** ROOT 写死 `gaokao-hubei-mvp`, 不能用于 gaokao-team-b. 用手动 re.sub 替换路径.
2. **content_audit.py** slug 用 filename, 不用 JSON 内 slug.
3. **m3 audit "字段截断" 是显示 bug**, 数据完整即可, 不要因此改动.
4. **m3 audit 评分主观**, 同一篇可能 6/10 或 8/10 不稳定, 取多次 audit 平均.
5. **CC Write 在某些 worktree 会被 revert**, 启动前用 bash echo 测试.
6. **session merge 时有 working tree 残留** → stash 后再 merge.
7. **C session 习惯性留 "自主创业/其他" 占位**, 合并后必清理.

---

## 4 个 P0 优秀参考案例 (供 Tier 2 重写参考)

| Major | 风格 | 路径 | 链接 |
|-------|------|------|------|
| 计算语言学 | humanities | computational-linguistics.json | 半文半理 + AI 预备 |
| 电子科学与技术 | eng | electronic-science-technology.json | 器件+IC+材料 + 示范性微电子学院 |
| 卫生健康法学 | law | health-law.json | 医学常识+法学硬核心+公共政策 |

复制这 3 篇的:
- lede 句式 (≤100 字, 主语+洞察)
- pitfalls 结构 (5-7 条 myth/reality, 每条 ≥80 字)
- alumni_quotes 详细度 (year/current/school/source/quote 五字段)
- employment_direction schema (name/pct/desc/dest, 6-8 个方向)

---

**最后更新**: 2026-06-17, Day 3 Team B 47 篇验证通过