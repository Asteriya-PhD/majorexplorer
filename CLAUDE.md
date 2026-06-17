# gaokao-team-b 项目指引

> 这是 **Major 精品/批量生成** 的项目, 写于 2026-06-17, Day 3 Team B 47 篇验证通过后定型.

---

## ⚠️ 强制必读: Major 精品质量流水线

**任何写/改/批量生成 major JSON 的任务, 开始前必读:**

📄 `docs/PIPELINE_major_quality.md` (179 行, 9 步流水线 + 4 大 anti-pollution + Tier 1/2/3 重试策略 + 7 个已知坑 + 3 个 P0 参考案例)

**核心 4 条 anti-pollution rules** (任何 1 条触发 audit ≤6 分):

1. **lede 模板套话** ❌ "X 是研究...的学科" / "传统机械/材料的同学..." / "AI 翻译时代, 学科训练的价值是问对问题" → ✅ "X 的核心是 A+B+C 三栖, 它在 P 时代有 Q 优势, 但 R 是该专业最大风险"
2. **who_fits_no 串台** ❌ 理工科出现"文本阅读/田野调研/历史/语文" → 删; 人文社科出现"数学/统计/经济/考证" → 删
3. **deep_study CS/金融 12%** ❌ "跨学科就业 (CS/数据/金融)": 12 + "国内硕士 (专业相关方向)": 25 占位 → 用专业真实主流去向
4. **curriculum 公共必修填专业课** ❌ 工程水文学/卫生法学总论/模拟集成电路 放公共必修 → 高数/英语/思政/制图才是公共必修

---

## 4 个 P0 优秀参考案例 (Tier 2 重写时必读)

- `skills/gaokao-major-explorer/data/curated/computational-linguistics.json` (humanities, 半文半理 AI)
- `skills/gaokao-major-explorer/data/curated/electronic-science-technology.json` (eng, 器件+IC+材料)
- `skills/gaokao-major-explorer/data/curated/health-law.json` (law, 医学+法学+公共政策)
- `skills/gaokao-major-explorer/data/curated/cultural-relics-museology.json` (humanities, 田野+策展+修复)

复制这 4 篇的 lede 句式 / pitfalls 结构 / alumni_quotes 详细度 / employment_direction schema.

---

## 7 个已知坑 (避免重复踩)

1. **`scripts/deploy_to_public.py` ROOT 写死 `gaokao-hubei-mvp`**, 不能用于本项目.
   绕过: 手动 `re.sub(r'(src|href)="\.\./\.\./((?:js|css)/[^"]+)"', r'\1="/\2"', src)`
2. **`scripts/batches/content_audit.py` slug 用文件名**, 不用 JSON 内 slug.
   例: `computational-linguistics.json` → `--slugs computational-linguistics:humanities`
3. **m3 audit "字段截断" 是显示 bug**, 数据完整即可, 不要因此改.
4. **m3 audit 评分主观** (同一篇 ±1 分波动), 取多次 audit 平均.
5. **CC Write 在某些 worktree 会被 revert**, 启动前用 `echo test > file && cat file` 测试.
6. **session merge 时可能有 working tree 残留** → `git stash` 后再 `git merge --no-ff`.
7. **C session 习惯性留 "自主创业/其他" 占位 + salary string schema**, 合并后必清理.

---

## 流水线 9 步 (每篇)

```
1. Audit Driven (必读 m3 audit issues)
2. Anti-Pollution 4 Rules (前置必避)
3. Hand-Write JSON (按专业逐字段, 完整 18 字段 schema)
4. Render + Deploy (绕过 deploy_to_public.py ROOT bug)
5. Audit Verify (≥7 才继续)
6. Tier 1/2/3 Retry:
   - Tier 1 (5-10min): 补 weak field
   - Tier 2 (15-20min): 完全重写 + 参考 P0 案例
   - Tier 3 (≤45min): flag: irreducible-<Y> 标记跳过
7. Single Commit Per Major
8. Schema Cleanup (合并后批量): 拆细 entrepreneur + 统一 salary
9. Full Batch Audit + Push
```

---

## 验收标准

| 指标 | 目标 | 最低 |
|------|------|------|
| 平均分 | **8.0** | 7.5 |
| ≥7 比例 | 100% | 95% |
| ≥8 比例 | 80%+ | 50% |
| 0 strong 字段 | 0 | ≤5% |
| 单篇耗时 | 30 min | 60 min |

---

## 强制 commit message 模板

```
fix(content): <major中文名> P{0,1,2,3} 重做 (X/10 → Y/10)

补齐/重写 N 项核心字段, 删所有通用模板套话:
- lede N→M <新洞察>
- who_fits_no N→M 删 <旧串台词>, 改 <新专属>
- pitfalls N→M 删 <旧通用>, 改 N 条 <专业独有>:
  1. <myth/reality>
  2. ...
- curriculum N→M 公共必修重写...5校特色按校...
- top_schools N→M 删 <凑数校>, 重排 N 所...
- deep_study 删 CS/金融 12%, 改 N 路径...
- salary schema 统一 p25/p50/p75...
- alumni_quotes 加 year/current/school, N 条具体
- xuanke_req 加 pct...

m3 content_audit: X/10 → Y/10 (优秀/合格, 0 strong, N 项 warning)
```

---

## 项目目录速查

```
gaokao-team-b/
├── skills/gaokao-major-explorer/    # 主要工作区
│   ├── data/curated/                # 47 个 major JSON + HTML
│   ├── scripts/                     # 渲染 + audit 工具
│   └── SKILL.md                     # 技能定义 (379 行)
├── public/                          # 部署镜像 (CF Pages serve)
├── scripts/                         # deploy_to_public.py 等
│   └── batches/content_audit.py    # m3 audit 主入口
├── test_results/                    # audit 历史 JSON
├── docs/
│   ├── PIPELINE_major_quality.md    # ⭐ 质量流水线 (必读)
│   ├── PLAN_day3_team_b_handcode.md
│   ├── PROGRESS_day3_team_b.md
│   └── DEPLOY_HYBRID.md
└── .claude/settings.json            # SessionStart hook (自动提醒读 PIPELINE)
```

---

**核心铁律**: 写 major JSON 之前 → 读 `docs/PIPELINE_major_quality.md` → 4 anti-pollution rules 前置 → hand-write 非模板 → audit verify ≥7 → 单 major 1 commit.