# gaokao-hubei-mvp 项目指引

> 这是 **Major 精品/批量生成** 的项目, 写于 2026-06-17, Day 3 47 篇验证通过后定型.
> 2026-06-18 v1.1: 新增 `scripts/audit/smart_audit.py` 智能混合审计 (Layer 1 + 智能 Layer 2), batch 审计 9.3h→2-3h, ¥140→¥40.
> 2026-06-30 v1.6: 质量管线双保险上线 + 双零 baseline 达成 (625/625 clean, 0 ERROR / 0 WARN). 详见末尾「🛡️ Day 56 双保险」章节.

## 📅 物理日期映射 (Day N → YYYYMMDD)

> "Day N" 是历史 Claude 估算日期, 不代表真实物理时间. 遇 Day N 翻此表即查真实日期. 2026-06-30 当天多 session (a/b/c/d/e/f) 都映射到同日.

| Day | 日期 | 备注 |
|---|---|---|
| Day 1 | 20260606 | 项目起点 (DECISIONS.md ADR-001) |
| Day 3 | 20260617 | Team B 47 篇验证通过 |
| Day 5-7 | 20260618 | Batch 1-4 + smoke fixtures |
| Day 8-15 | 20260619-21 | polish 8/11/5/14/5/6 + irreducible-6/7 |
| Day 17-18 | 20260623 | 23 篇 R2 + Tier 2 12 篇 |
| Day 22-28 | 20260624-25 | polish 100% + xuanke schema + chip |
| Day 31-32 | 20260627 | deploy.sh 7 步 + Cache 三层 |
| Day 35-47 | 20260629 | mobile PWA / SEO / 校友脱敏 / polish 收尾 |
| Day 47.5-47.11 | 20260630-a | 8 commit (P0/P1/P2 收尾) |
| Day 48 | 20260630-b | 5 commit (Day 48 phase) |
| Day 49 | 20260630-c | 11 commit (render_quality 100% clean baseline) |
| Day 50-52 | 20260630-d | 3 commit (FIELD-3 / SAL-NOTE / FIELD-2 清理) |
| Day 56 | 20260630-e | 4 commit (backfill 16 篇 + 3 batch tool + 切硬阻塞 + 双零) |
| Day 57 | 20260630-f | 1 commit (smart_audit 大修) |

**当天多 session 排序**: 同日多 commit 按时间升序, `a` 最早 → `f` 最晚.
**未来 commit 规则**: 必用 `YYYYMMDD [session]` 格式, 不用 Day N. 详见 `docs/COMMIT_CONVENTION.md`.

---

## 🧠 批量 audit 必用 smart_audit.py (2026-06-18 新增)

**任何 ≥10 篇的 batch audit, 用 `scripts/audit/smart_audit.py` 替代老 `content_audit.py`**.

- 老方法: 全量 277 篇 ~9.3h / ¥140 (Day 18 baseline)
- 新方法: 启发式 100% + LLM 智能路由 ~30% → 2-3h / ¥40, 覆盖 95%+ 真实 bug

```bash
# 1. dry-run 看候选 (5s, 不花钱)
python3 scripts/audit/smart_audit.py --dry-run

# 2. 真跑 (2-3h, ~¥40)
python3 scripts/audit/smart_audit.py

# 3. 单篇深审 (用老 content_audit.py)
python3 scripts/batches/content_audit.py --slugs <slug>:<style>
```

Layer 2 触发条件 (满足任一): L1 warning / 无历史 / 历史 < 7 / 改过 / 5% 抽样.

详见 `docs/PIPELINE_major_quality.md` "🧠 智能审计路由器" 章节.

---

## 📋 强制必读: Audit Registry (单一真相)

**任何 audit 行动后, 必须保证 `data/audit_registry.json` (git tracked) 同步**:

- ✅ **content_audit.py 跑完自动 sync** (2026-06-18+): 不再需要手动跑 `update_audit_registry.py`
- ✅ **smart_audit.py 跑完自动 sync**: Layer 2 m3 结果直接写 registry
- ✅ **render_quality.py 跑完自动 sync** (2026-06-30+): `--sync-registry` 模式
- ⚠️ **手审 / 第三方 audit**: 手动跑 `python3 scripts/audit/update_audit_registry.py --from-file <file>`

📄 **Schema 必读**: `docs/audit_registry_schema.md` (version/字段/stats/totals 完整定义)

```bash
# 查当前统计 (8+/7-8/6-7/<6 分布)
python3 scripts/audit/update_audit_registry.py --stats

# 查 <7 待修 (用于 4 篇 polish 决策)
jq '.majors | to_entries | map(select(.value.current_score < 7)) | map({slug: .key, score: .value.current_score, title: .value.title})' data/audit_registry.json

# 查 render_quality 双零状态 (Day 56+ 必查)
jq '.totals.render_quality_errors, .totals.render_quality_warnings' data/audit_registry.json

# 全量重建 (test_results/ → registry, 初始化/Schema 升级时用)
python3 scripts/audit/update_audit_registry.py --rebuild
```

**核心约束**:
- registry 是派生视图, 真理性在 `public/data/manifest.json` (major 列表) + `test_results/content_audit_*.json` (审计原始) + `test_results/render_quality_*.json` (渲染质量)
- git tracked → 跨 session 同步, 任何 agent 行动前先 `git pull`
- smart_audit.py 路由决策依赖 registry, 漏登记 = 重复审计浪费 ¥
- render_quality 每周一 8am cron 跑 `--all --sync-registry`, 涨了立刻 alert

---

## ⚠️ 强制必读: Major 精品质量流水线

**任何写/改/批量生成 major JSON 的任务, 开始前必读:**

📄 `docs/PIPELINE_major_quality.md` (v1.6 Day 56 双保险, 9 步流水线 + 6 大 anti-pollution + Tier 1/2/3 重试策略 + 7 个已知坑 + 4 个 P0 参考案例 + 3 个 batch 工具)

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

1. ~~**`scripts/deploy_to_public.py` ROOT 写死 `gaokao-hubei-mvp`**, 不能用于本项目.~~  (Day 22 后 `deploy_to_public.py` 已删, 改用 `scripts/deploy.sh "<msg>"` 一键部署, 详见 `docs/DEPLOYMENT.md`).
2. **`scripts/batches/content_audit.py` slug 用文件名**, 不用 JSON 内 slug.
   例: `computational-linguistics.json` → `--slugs computational-linguistics:humanities`
   **批量 (≥10 篇) 用 `scripts/audit/smart_audit.py` 替代**, 不要全量跑 content_audit.
3. **m3 audit "字段截断" 是显示 bug**, 数据完整即可, 不要因此改.
4. **m3 audit 评分主观** (同一篇 ±1 分波动), 取多次 audit 平均.
5. **CC Write 在某些 worktree 会被 revert**, 启动前用 `echo test > file && cat file` 测试.
6. **session merge 时可能有 working tree 残留** → `git stash` 后再 `git merge --no-ff`.
7. **C session 习惯性留 "自主创业/其他" 占位 + salary string schema**, 合并后必清理.
8. **script 路径**: 所有 audit 工具在 `scripts/audit/` (不是 `scripts/`). `smart_audit.py` / `render_quality.py` / `update_audit_registry.py` 全在子目录. 早期文档写的 `scripts/smart_audit.py` 错误, v1.6 修正.

---

## 流水线 9 步 (每篇)

```
1. Audit Driven (必读 m3 audit issues)
2. Anti-Pollution 4 Rules (前置必避)
3. Hand-Write JSON (按专业逐字段, 完整 18 字段 schema)
4. Render + Deploy (用 scripts/deploy.sh)
4.5 render_quality.py 质量门 (Day 49+, 13 规则 0¥ <2s/625 篇)
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
| **render_quality 双零** (Day 56+) | **0 ERROR / 0 WARN** | 0 ERROR |
| 单篇耗时 | 30 min | 60 min |

---

## 🛡️ Day 56 双保险 (2026-06-30 上线)

> **背景**: Day 49 上线 render_quality.py 13 规则 (HTML 渲染质量门), 但 pre-commit step 5 走 warn-only. Day 56 切 ERROR 硬阻塞 + 双零 baseline 达成, 任何新 HTML/数据 bug commit 立刻 fail.

### 双保险架构

```
┌─────────────────────────────────────────────────────────────┐
│  防线 1: 预 commit 硬阻塞 (.githooks/pre-commit, 5 检查)   │
│  ─────────────────────────────────────────────────────────  │
│  1. backfill: 5 字段 (discipline/sub_discipline/menjia/...) │
│  2. L1 启发式: check_major.py --staged (6 anti-pollution)  │
│  3. manifest drift: rebuild_manifest.py --check            │
│  4. aggregates drift: build_aggregates.py --check           │
│  5. render_quality: --staged (Day 56+ ERROR 阻塞, ⭐新)     │
│                                                             │
│  ↓ 任一失败 → 阻断 commit exit 1                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  防线 2: 全量 baseline 双零 (625 篇, 每周一 cron)            │
│  ─────────────────────────────────────────────────────────  │
│  python3 scripts/audit/render_quality.py --all --sync-registry │
│                                                             │
│  8 ERROR 规则: SAL-MONO-1/2, SAL-CAP-1, HTML-PC-1/2/3/4,   │
│                HTML-MB-1, FIELD-1, FIELD-4                  │
│  5 WARN 规则: SAL-NOTE-1, FIELD-2, FIELD-3 (Day 56 全清零) │
│                                                             │
│  ↓ registry.totals.render_quality_errors 涨 → 立刻 alert    │
└─────────────────────────────────────────────────────────────┘
```

### 双零 baseline (2026-06-30 达成)

| 指标 | 状态 |
|---|---|
| 扫描篇数 | 625/625 (100%) |
| ERROR | **0** |
| WARN | **0** |
| 耗时 | ~0.8s |
| 成本 | 0¥ |

### 7 commit 推 main 战果 (Day 49-56)

| commit | 内容 | 警告/错误 |
|---|---|---|
| `ba5cbc15` (Day 49) | Day 49.1 baseline 起点 | 73 |
| `f63eae73` (Day 50) | A.1 FIELD-3 xuanke alias → name | 59 → 0 |
| `6d4948f3` (Day 51) | A.2 SAL-NOTE-1 非 senior note 删 | 128 → 42 |
| `41d29271` (Day 52) | A.3 FIELD-2 hero_quote 修 | 7 → 0 |
| `18d533c6` (Day 56) | B pre-commit step 5 切硬阻塞 | — |
| `534322d3` (Day 56) | 16 篇补 5 字段 (pre-commit step 1 解锁) | — |
| `0e1c4c5c` (Day 56) | A.4 SAL-NOTE-1 42 → 0 (迁 senior) | **0** ✅ |

### 3 个 batch 工具 (scripts/batch/) — 后续类似 fix 复用模板

```bash
# 1. 字段名规范化 (alias → canonical name, 保留原字段)
python3 scripts/batch/fix_xuanke_field_name.py [--dry-run]

# 2. 删非 senior 错位 note (4 类关键词: 数据来源/应届分线/段位说明/校企对比)
python3 scripts/batch/fix_salary_note_placement.py [--dry-run]

# 3. 迁残留 note 到 senior 末尾 + 分类前缀
python3 scripts/batch/fix_salary_note_residual.py [--dry-run]
```

3 个工具累计 修 86 + 42 + 59 = 187 处违规, 0¥, 0 误改, 全 dry-run 验证后跑.

### 新 ERROR 修复 SOP (Day 56+)

预 commit hook 阻断了 → 怎么修:

1. 看 hook 输出, 找到 ERROR 行 (哪个 slug + 哪条规则)
2. 跑 `python3 scripts/audit/render_quality.py --slug <slug>` 看具体违规
3. 修 source JSON (或 HTML, 看规则)
4. 跑 `python3 scripts/audit/render_quality.py --slug <slug>` 复验 → ✅
5. 跑 `python3 scripts/audit/render_quality.py --all --sync-registry` 同步 registry
6. 重 commit (hook 应过)

**绕过**: 仅 `git commit --no-verify` (不推荐, 需在 PR 描述说明)

**详细规则 + STAGE_RANK + NOTE_EXCEPTION_KEYWORDS** → `docs/RENDER_QUALITY_RULES.md` (184 行, 13 规则参考 + baseline 历史 + Day 56 切流说明)

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
gaokao-hubei-mvp/
├── skills/gaokao-major-explorer/    # 主要工作区
│   ├── data/curated/                # 625 个 major JSON + HTML
│   ├── scripts/                     # 渲染 + audit 工具
│   └── SKILL.md                     # 技能定义
├── public/                          # 部署镜像 (CF Pages serve, 638 HTML)
├── scripts/                         # build_sitemap / inject_* / smart_audit / synth_*
│   ├── audit/                       # ⭐ 质量门工具 (Day 49+)
│   │   ├── render_quality.py        # 13 规则 Layer 0 (Day 49+, 双保险防线 2)
│   │   ├── smart_audit.py           # 智能混合审计 (Day 18+)
│   │   └── update_audit_registry.py # registry 同步
│   ├── batch/                       # ⭐ 批量 fix 工具 (Day 50+)
│   │   ├── fix_xuanke_field_name.py
│   │   ├── fix_salary_note_placement.py
│   │   └── fix_salary_note_residual.py
│   ├── schema-fix/                  # schema backfill / normalize
│   ├── build/                       # build_aggregates / inject_seo / inject_jsonld
│   └── batches/content_audit.py     # m3 audit 主入口 (单篇深审)
├── test_results/                    # audit 历史 JSON (gitignored)
├── data/                            # audit_registry.json (git tracked, 单一真相)
├── docs/
│   ├── PIPELINE_major_quality.md    # ⭐ 质量流水线 v1.6 (必读)
│   ├── RENDER_QUALITY_RULES.md      # ⭐ 13 规则参考 (Day 49+)
│   ├── audit_registry_schema.md     # registry 字段定义
│   ├── ARCHITECTURE.md              # 系统架构
│   ├── DEPLOYMENT.md                # 部署 + Cache 4 层锁死
│   └── DEPLOY_HYBRID.md             # 部署
├── .githooks/pre-commit             # ⭐ 5 检查硬阻塞 (Day 56+)
└── .claude/settings.json            # SessionStart hook (自动提醒读 PIPELINE)
```

---

**核心铁律 (Day 56 升级版)**:
1. 写 major JSON 之前 → 读 `docs/PIPELINE_major_quality.md` → 6 anti-pollution rules 前置
2. hand-write 非模板 → audit verify ≥7 → 单 major 1 commit
3. commit 前 hook 5 检查会自动跑 (Day 56+ step 5 硬阻塞, 不需要手动)
4. 任何新 ERROR → 看 hook 输出 → 修 → 重 commit
5. 每周一 cron 跑 `--all --sync-registry` 留历史, 双零状态保持
