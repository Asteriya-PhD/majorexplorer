# Major 精品质量流水线 v1.8 (Day 59 借鉴橙皮书专家)

> 写于 2026-06-17, 47 篇验证: 平均 7.69/10, 100% ≥7, 64% ≥8.
> 目标: 后续主题稳定达到 **平均 8.0/10** 水准.
> 2026-06-18 v1.1: 新增 `scripts/audit/smart_audit.py` 智能混合审计 (Layer 1 启发式 + 智能 Layer 2 LLM), batch 审计从 9.3h/¥140 降到 2-3h/¥40.
> 2026-06-18 v1.2: 新增 m3 audit 升级套路 (修 audit 5-6 硬伤 > 追主观波动), E 阶段 7 篇 7→8/10 验证 3 audit iterations 7.14→7.43→8.00.
> 2026-06-19 v1.4: 新增 §"在线按需合成 SOP" (CF Pages Function + D1 + GH Action + 跨 provider fallback + rate limit + 失败死信上报), 用户搜未收录专业一键 🔄 实时生成. Session 1-2 实测成功, 端到端验证待 Session 3 Playwright.
> 2026-06-30 v1.5: 新增 §"渲染后 HTML 质量门" (`scripts/audit/render_quality.py` 13 条规则, Layer 0, 0¥ <2s/625 篇). 历史 P0 痛点 (html-escape/jsonld-0-injection/salary-p25-gt-p75/38-alumni-placeholder) 全部规则化. Pre-commit warn-only 至 Day 55, Day 56+ 切 ERROR 阻塞.
> 2026-06-30 v1.6: 🛡️ **Day 56 双保险上线 + 双零 baseline 达成**. Pre-commit step 5 切硬阻塞 (单字符 `failed=1` 改动), 3 个 batch 工具 (fix_xuanke_field_name / fix_salary_note_placement / fix_salary_note_residual) 累计修 187 处违规, 0¥ 0 误改. **625/625 clean, 0 ERROR / 0 WARN** (历史首次双零). 详见「🛡️ Day 56 双保险」章节.
> 2026-06-30 v1.7: 文档瘦身, 路径修 (老 `scripts/smart_audit.py` → `scripts/audit/smart_audit.py`), 数字 277 → 625, deploy_to_public.py 已知坑标记已删 (改用 deploy.sh), 项目名 gaokao-team-b → gaokao-hubei-mvp.
> 2026-07-02 v1.8: 🌸 **借鉴花叔 orange-book-expert skill (5 步流水线)**, 落地 2 条原则: (1) 每个 Tier 2 polish 前写 `research-<slug>-<日期>.md` 调研档案, 可追溯/新人接手; (2) 写的人不审自己, Tier 2 重写 commit 标 `needs-m3-audit` 交独立 worker audit. 模板 `skills/gaokao-major-explorer/references/research-template.md`. 不学 3 点: 整体 5 步结构 / 8-agent 蜂群 / 反 AI slop 风格. 详见「🌸 借鉴橙皮书」章节.

## 📅 物理日期映射 (Day N → YYYYMMDD)

> "Day N" 是历史 Claude 估算日期, 不代表真实物理时间. 本文档正文仍用 Day N 引用 (不改写历史表述), 遇 Day N 翻此表即查真实日期.

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

**未来 commit 规则**: 必用 `YYYYMMDD [session]` 格式, 不用 Day N. 详见 `docs/COMMIT_CONVENTION.md`.

---

## 🛡️ Day 56 双保险架构 (v1.6 核心新增)

> **双保险 = 预 commit 硬阻塞 + 全量 baseline 持续监控**. 任何 HTML/数据 bug 想进 main, 必中其一.

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│  防线 1: 预 commit 硬阻塞 (.githooks/pre-commit, 5 检查)      │
│  ─────────────────────────────────────────────────────────────  │
│  Step 1: backfill 5 字段 (discipline/sub_discipline/menjia/...) │
│  Step 2: L1 启发式 (check_major.py --staged, 6 anti-pollution) │
│  Step 3: manifest drift (rebuild_manifest.py --check)          │
│  Step 4: aggregates drift (build_aggregates.py --check)         │
│  Step 5: ⭐ render_quality --staged (Day 56+ ERROR 硬阻塞)      │
│                                                                 │
│  ↓ 任一失败 → 阻断 commit exit 1, 修后再 commit                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  防线 2: 全量 baseline 双零 (625 篇, 每周一 8am cron)            │
│  ─────────────────────────────────────────────────────────────  │
│  python3 scripts/audit/render_quality.py --all --sync-registry  │
│                                                                 │
│  13 规则:                                                       │
│    8 ERROR (阻断): SAL-MONO-1/2, SAL-CAP-1, HTML-PC-1/2/3/4,   │
│                    HTML-MB-1, FIELD-1, FIELD-4                  │
│    5 WARN  (Day 56 全清零): SAL-NOTE-1, FIELD-2, FIELD-3       │
│                                                                 │
│  ↓ registry.totals.render_quality_errors 涨 → 立刻 alert        │
└─────────────────────────────────────────────────────────────────┘
```

### 双零 baseline (2026-06-30 达成)

| 指标 | Day 49 起点 | Day 50-52 中间 | **Day 56 完工** |
|---|---|---|---|
| 扫描篇数 | 625/625 | 625/625 | 625/625 |
| ERROR | 0 | 0 | **0** |
| WARN | 73 | 26 | **0** |
| 耗时 | 1.1s | ~0.9s | **0.8s** |
| 成本 | 0¥ | 0¥ | **0¥** |

### 7 commit 战果 (Day 49-56)

| commit | 内容 | WARN/ERROR 变化 |
|---|---|---|
| `ba5cbc15` (Day 49) | Day 49.1 baseline 起点 | 73 WARN / 0 ERROR |
| `f63eae73` (Day 50) | A.1 FIELD-3 xuanke alias → name (15 篇) | 73 → 58 |
| `6d4948f3` (Day 51) | A.2 SAL-NOTE-1 删错位 note (37 篇, 删 86) | 58 → 33 |
| `41d29271` (Day 52) | A.3 FIELD-2 hero_quote 修 (4 截短 + 3 加 sig) | 33 → 26 |
| `18d533c6` (Day 56) | B pre-commit step 5 切 ERROR 硬阻塞 | — |
| `534322d3` (Day 56) | 16 篇 backfill 5 字段 (pre-commit step 1 解锁) | — |
| `0e1c4c5c` (Day 56) | A.4 SAL-NOTE-1 残留 42 迁 senior (26 篇) | **26 → 0** ✅ |

### 3 个 batch 工具 (scripts/batch/) — 后续类似 fix 复用模板

```bash
# 1. 字段名规范化 (alias → canonical name, 保留原字段)
#    Day 50 A.1: combo/item/subject/course → name (15 篇, 59 处)
python3 scripts/batch/fix_xuanke_field_name.py [--dry-run]

# 2. 删非 senior 错位 note (4 类关键词: 数据来源/应届分线/段位说明/校企对比)
#    Day 51 A.2: 37 篇删 86 处纯错位 note
python3 scripts/batch/fix_salary_note_placement.py [--dry-run]

# 3. 迁残留 note 到 senior 末尾 + 分类前缀 ([应届分线] / [段位细分] / [经验范围] / [元数据])
#    Day 56 A.4: 26 篇迁 42 处真实数据到 senior, 加分类前缀
python3 scripts/batch/fix_salary_note_residual.py [--dry-run]
```

3 工具累计 修 86 + 42 + 59 = 187 处违规, 0¥, 0 误改, 全 dry-run 验证后跑.

### 新 ERROR 修复 SOP (Day 56+ 触发后)

1. 看 hook 输出, 找到 ERROR 行 (哪个 slug + 哪条规则)
2. 跑 `python3 scripts/audit/render_quality.py --slug <slug>` 看具体违规
3. 修 source JSON (或 HTML, 看规则)
4. 跑 `python3 scripts/audit/render_quality.py --slug <slug>` 复验 → ✅
5. 跑 `python3 scripts/audit/render_quality.py --all --sync-registry` 同步 registry
6. 重 commit (hook 应过)

**绕过**: 仅 `git commit --no-verify` (不推荐, 需在 PR 描述说明)

**详细规则参考** → `docs/RENDER_QUALITY_RULES.md` (184 行, 13 规则 + STAGE_RANK + baseline 历史 + Day 56 切流说明)

---

## 🧠 智能审计路由器 (Smart Audit Router) — 批量 audit 必用

**问题**: 老 `scripts/batches/content_audit.py` 全量 LLM 审计 ~300 篇 ~9.3h / ¥140 (Day 18 baseline), 不敢对全量 HTML 跑.

**解法**: `scripts/audit/smart_audit.py` 用 2 层架构:

```
Layer 1 (100% 跑, 0¥, 1s/篇)
  └─ check_major.py 启发式: 4 anti-pollution + 18 字段 schema

Layer 2 (智能路由, ~30% 跑, 2min/篇, ¥0.5)
  └─ m3 audit LLM: 跨字段矛盾 + 学科知识 + 主观质量

Layer 2 触发条件 (满足任一):
  1. Layer 1 warning/error (启发式抓到污染/缺失)
  2. 从未 audit 过 (test_results/ 无历史)
  3. 历史 score < 7.0
  4. 上次 audit 后改过 (mtime > last_audit_time)
  5. 5% 随机抽样 (sanity check)
```

**实测 (Day 18, 277 篇 baseline)**:
| 模式 | Layer 1 | Layer 2 | 总耗时 | 成本 | 覆盖率 |
|------|---------|---------|--------|------|--------|
| 全量 + 全量 | 5-20m | 9.3h | 9.5h | ¥140 | 100% |
| **智能混合 (默认)** | 5-20m | 2-3h | 2-3h | ¥40 | 95%+ |
| 全 sample 18 篇 | 5-20m | 36m | 1h | ¥3 | 30% |

**用法 (5 个常用场景)**:

```bash
# 1. 全量智能路由 (默认推荐, 当前 625 篇, ~30% 走 L2)
python3 scripts/audit/smart_audit.py

# 2. dry-run: 只列候选, 不真跑 m3
python3 scripts/audit/smart_audit.py --dry-run

# 3. 只审某 category (eng / law / humanities / ...)
python3 scripts/audit/smart_audit.py --category eng

# 4. 限 N 篇 (快速 sanity check)
python3 scripts/audit/smart_audit.py --limit 20

# 5. JSON 输出给 pipe (jq / python 二次处理)
python3 scripts/audit/smart_audit.py --dry-run --json | jq '.candidates[:5]'
```

**何时仍用老 `content_audit.py`**:
- 单篇深度审计 (e.g. 刚改完 1 篇, 想知道具体问题)
- 跨字段矛盾 debug
- 指定 1-3 篇特定 slug: `content_audit.py --slugs foo:eng bar:law`

**何时用 `smart_audit.py`**:
- 任何 batch 操作 (10+ 篇)
- 想知道"全量 625 篇里哪些真需要审"
- 想做"全量 625 篇质量体检"
- 想知道"上次 audit 后哪些改过需重审"

---

## 🌸 借鉴橙皮书: 调研档案 + 独立审校 (Day 59 新增, 来自花叔 huashu 生态)

> **背景**: 2026-07-02 装了花叔 `orange-book-expert` skill (5 步流水线: 调研/规划/写作/审校/发布), 发现有 2 条原则**直接适用于我们 major 精品流程**, 当天落地。

### 借鉴 1: 每个 polish 前写 `research-<slug>-<日期>.md` 调研档案

**为什么需要**: 现在 polish 流程里, 思考/搜索/发现都活在 session 里, 断了就丢。多人并发 polish 同一篇时, 互相看不到对方调研。Day 14 串台 (gongan 数学) / Day 18 风景园林 985 误标 等 bug, 都属于"调研档案缺失"导致的重复踩坑。

**怎么做**:
- 模板: `skills/gaokao-major-explorer/references/research-template.md`
- 路径: `skills/gaokao-major-explorer/references/research/<slug>-<YYYYMMDD>.md`
- 时机: **动 JSON 前** 5-10 min 填 1-5 节, 改完填第 7 节
- 跟 JSON 在同一次 commit 里

**适用场景** (建议但不强求):
- 任何 Tier 2 完全重写 (15-20 min/篇, 调研档案 ROI 高)
- 任何 audit ≤ 6 的 polish
- 任何多人并发 polish 同一篇 (防止重复调研)

**不适用的场景** (跳过不写):
- Tier 1 补 weak field (5-10 min, 不值得)
- 简单的 schema 修复 (脚本跑就行)

### 借鉴 2: 写的人不审自己 (独立 agent 强制)

**为什么需要**: 现在 m3 audit 都是"自己写完自己跑 audit", 确认偏误问题真实存在 (Day 14 gongan 数学 4/10 自己审没发现串台)。

**怎么做 (新增强制规则)**:

> **任何 Tier 2 重写 (审计 ≤ 6), 写完不要立刻自己跑 m3 audit。把 JSON 提交到 git, 在 commit message 里标 `needs-m3-audit`, 切到下一个任务或交回主 session 由独立 worker 跑 audit。**

具体 3 种走法:
1. **同 session 不同 agent**: 主 agent 写完 → 切 subagent 跑 audit (用 `model: haiku` 或 `sonnet` 节省成本)
2. **跨 session**: 写完 commit 留 TODO, 下次 session 起手任务清单里加 `audit <commit-hash>`
3. **smoke fixture 验证**: 写完跑 `render_quality.py --slug <slug>` (Day 49+ 已硬阻塞) 至少保证 schema 不错, m3 audit 留给独立 worker

**不适用的场景**:
- Tier 1 补 weak field (1-2 字段小改, 独立审 ROI 低)
- 简单的脚本批量修 (Day 56 3 个 batch 工具已经无 agent)

### 借鉴后 SOP 微调 (Day 59+ 起)

| 场景 | 旧流程 | 新流程 (借鉴后) |
|------|--------|----------------|
| Tier 2 重写 (审计 ≤ 6) | 自己写 → 自己 audit → commit | 自己写 → commit 标 `needs-m3-audit` → 切独立 worker audit |
| Tier 1 补 field (审计 7-8) | 自己写 → 自己 audit → commit | 同旧 (不变, ROI 低) |
| 多人并发 polish 同一篇 | 各写各的, 互相不知 | 共享 `research-<slug>-*.md` 调研档案 |
| 不可逆重大修改 (改 top_schools / 改 category) | 自己写完 commit | 先写调研档案 → 自己写 → commit 标 `needs-m3-audit` |

### 不借鉴的 3 个点 (避免硬套)

- ❌ **不学 5 步流水线整体结构** — 我们 9 步流水线更适配"工厂批量"(625 篇), 橙皮书 5 步是"单本精工"(1-3 小时/本)
- ❌ **不学 8-agent 蜂群 worktree** — 我们 polish 用 worktree 串行已经够, 蜂群 ROI 不匹配我们的"单篇 5-15 min"节奏 (P1 跳过原因)
- ❌ **不学"案例生动 + 反 AI slop"风格** — 我们要"专业准确 + 招录数据精确", 案例可读性服从专业性

### 引用与起源

- 完整橙皮书专家 skill: `~/.claude/skills/orange-book-expert/SKILL.md`
- 调研 SOP 来源: `~/.claude/skills/orange-book-expert/references/phase-1-research.md`
- 审校 SOP 来源: `~/.claude/skills/orange-book-expert/references/phase-4-review.md`
- 花叔原 skill: `alchaincyf/huashu-skills` (huashu-research + huashu-agent-swarm + huashu-md-to-pdf)

---

## 9 步流水线 (每批 30-50 篇)

### Step 0: Auto-Repair Rank 字段 (Day 17 加, 长期治理)

**任何 synth / hand-code / online-on-demand 产出的新 major JSON, 必须先跑 repair 脚本规整 top_schools.rank 字段**:

```bash
# Dry-run 先看
python3 scripts/schema-fix/repair_top_schools_rank.py --dry-run

# 真跑 (会写回 JSON)
python3 scripts/schema-fix/repair_top_schools_rank.py
```

**规整规则** (canonical = `"★★★★☆ (A+)"` 星+括号):
- `"A+"` 纯字母 → `"★★★★★ (A+)"` (5★ 满)
- `"★★★★★ (A+)"` 星+括号 → 不变
- `"★★★★★"` 纯星 → 不变 (render 端映射)
- `tag` 含字母 → 提取 → `"★★★★☆ (A+)"` (4★ 表明仅 tag 提及)
- `1`/`2`/`3` int 序号 → `""` 空字符串 (不强映射, render 显示 "—")
- `""`/`None` → 不变

**为什么**: render_mobile.py 的 normalize_rank() 已兜底 5 种格式 (运行时防御), 但 synth 阶段会持续产出新格式, 长期应在数据层统一, 让渲染端无需兼容。**新格式只需在 repair 脚本 +1 case**, 数据层 +1 case, 渲染端不动。

**插入位置**: 每次 batch synth 完成 → Step 1 audit 之前 必跑。

### Step 1: Audit Driven (必读)

**单篇 deep dive** → 老 `content_audit.py`:
```bash
source .env
python3 scripts/batches/content_audit.py --slugs <slug>:<style>
```

**批量 (10+ 篇) → 新 `smart_audit.py`** (推荐):
```bash
source .env
# 1. dry-run 看候选
python3 scripts/audit/smart_audit.py --dry-run
# 2. 真跑 (只跑 Layer 2 候选, ~30% 总数)
python3 scripts/audit/smart_audit.py
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
| **xuanke 3+1+2 首选冲突** (Day 5 Batch 4 加) | "物理 + 历史 + 政治 (覆盖最广)", "物理+历史+地理", "历史 + 政治 + 物理" — 物理/历史 是 2 选 1 首选科目, 不能共存 | "首选物理 + 化学", "首选物理 + 再选不限", "首选历史 + 再选不限", "首选政治 + 再选不限" — 必含 "首选" 二字, 物理/历史 二选一 |
| **薪资 应届生 P50 虚高** (Day 5 Batch 4 加) | 应届生 P50 = 35/45/60 万 (LLM hallucinate, 完全失真). 麦可思 2024: 本科平均 7.26 万/年, 顶级头部 ≈ 14-20 万 | 按 13 套 style 模板校准: cs 18/finance 13/eng 12/medicine 9 (规培前) / humanities 8 万 — yoy 6-12% 合理 |
| **top_schools.rank 字段格式混乱** (Day 17 移动 bug 加) | 5 种格式混用导致渲染崩 / 误判 B-: `"A+"` 纯字母 / `"★★★★★ (A+)"` 星+括号 / `"★★★★★"` 纯星 / `tag` 兜底 / `1` int 序号 | **统一格式**: 优先 `"★★★★☆ (A+)"` (星+括号), 无公开评估用 `"★★★★☆"` 纯星 + tag 补说明. **int 序号禁止** (渲染层用 normalizer 兜底, 但 synth 应避免) |

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

### Step 4.5: Day 49 v1.5 新增 — 渲染后 HTML 质量门 (render_quality.py)

**跑完渲染立刻 check, 不等 m3 audit 才发现结构错**.

```bash
# 单篇
python3 scripts/audit/render_quality.py --slug <slug>

# 全量 (Day 49 baseline 625 篇 1.2s)
python3 scripts/audit/render_quality.py --all --sync-registry
```

**13 条规则 (Layer 0 启发式 0¥ <2s)**: 详见 `docs/RENDER_QUALITY_RULES.md`.

| 类别 | 规则 | 严重度 |
|---|---|---|
| 薪资单调 | SAL-MONO-1 (p25≤p50≤p75), SAL-MONO-2 (跨阶段), SAL-CAP-1 (资深 p75≤100), SAL-NOTE-1 | ERROR×3 + WARN×1 |
| PC HTML | HTML-PC-1 (8 段), HTML-PC-2 (meta desc), HTML-PC-3 (JSON-LD), HTML-PC-4 (og 三件套) | ERROR×4 |
| mobile | HTML-MB-1 (10 art-num 全有) | ERROR |
| 字段 | FIELD-1 (alum-N 占位), FIELD-2 (hero_quote 署名), FIELD-3 (xuanke name), FIELD-4 (emp pct) | ERROR×2 + WARN×2 |

**Day 49 baseline 实测 (修 SAL-MONO-2 误报后)**: 625 篇 1.1s 跑完, 493 clean (79%), 132 有 ERROR (21%, **全部已抽样验证为真问题**). 主要命中:
- SAL-NOTE-1 note 错位 127 次
- SAL-MONO-2 跨阶段倒挂 66 次 (修误报后, 100% 真; 几乎都是 5年细分顶端 高于 10年+ 细分常规)
- FIELD-3 xuanke 字段名 59 次
- HTML-PC-4 og 三件套不全 54 次 (SEO 注入流水线部分漂移)
- SAL-CAP-1 资深 p75>100 37 次
- HTML-PC-3 JSON-LD 缺失 34 次 (P0 bug 残余)
- HTML-MB-1 mobile 段缺 15 次
- FIELD-1 alum-N 占位 12 次 (P0 bug 残余)
- SAL-MONO-1 p25>p50 6 次

**集成点** (Day 56+ 双保险):
- pre-commit hook step 5 (防线 1): `--staged` 模式, **ERROR 硬阻塞** (commit 立即 fail exit 1)
- 每周一 8am cron `--all --sync-registry` (防线 2): 持续监控双零, 涨了 alert
- smart_audit.py Layer 0 (run_layer0): L0 违规作为 m3 L2 路由依据
- update_audit_registry.py: `--from-render-quality` 同步到 registry 顶层 `render_quality` key, schema v1.0 → v1.1

**Day 56 切硬阻塞**: `.githooks/pre-commit` 第 5 步, 把注释 `# warn-only mode: do not set failed=1` 上面加一行 `failed=1`. 单字符改动. 详见上方「🛡️ Day 56 双保险架构」章节.

### Step 5: Audit Verify (≥7 才继续)

**单篇**:
```bash
source .env
python3 scripts/batches/content_audit.py --slugs <slug>:<style>
# 期望 overall_score ≥ 7
```

**批量**: 用 `smart_audit.py` 自动跑 Layer 2 候选 + 统计 ≥7 比例.

**7→8 升级 (v1.2 新增)**: 详见下方「🆕 v1.2: m3 Audit 升级套路」章节, 修 audit 5-6/10 硬伤 (lede/top_schools/deep_study/summary) 5-15 min 即可 +1 分.

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

**用 `smart_audit.py` (推荐, 2-3h / ¥40)**:
```bash
source .env
# 全量智能路由 (当前 625 篇, ~30% 走 L2 ~190 篇)
python3 scripts/audit/smart_audit.py
# 验证全部 ≥7, 修不合格篇
# Push 到 origin
git push origin day3-team-b
```

**老方法 (9.3h / ¥140, 仅特殊场景如全量回归)**:
```bash
# 跑全部 audit (建议 30 篇一批避免 timeout)
python3 scripts/batches/content_audit.py --csv all_majors.csv
```

---

## 🆕 v1.2: m3 Audit 升级套路 (7→8 临界点攻略)

> 来源: 2026-06-18 E 阶段 7 篇 m3 audit 实战 (initial 7.14 → fix 7.43 → fix 8.00). 修 1 个硬伤稳定 +1 分, 追主观波动可能 ±1.

### 核心原则: 修 audit 5-6/10 硬伤 > 追主观波动

m3 audit 给分是「字段级评分」+「整体综合」双轨. 整体 7 分可能由 10 个 8/9 分字段 + 1 个 4-6 分硬伤字段决定. **修硬伤是确定性 +1, 追主观评分是赌博 ±1.**

### 7 个常见硬伤 (m3 audit 5-6/10 字段) + 修复模板

| # | 硬伤模式 | 修复模板 | 典型案例 |
|---|----------|----------|----------|
| 1 | **lede 4-6/10** | 缩到 ≤120 字, 主语+洞察+1 隐藏坑句式. 5 大坑全塞进 lede 是 4/10 红线 | 数媒 327→121 字 (7→8) |
| 2 | **top_schools 5/10 凑数** | 真实学科评估 B+ 以下不要进 Top 8. 用学科评估 4 轮/5 轮排名重排 | env-law 删中南大学 (7→8) |
| 3 | **deep_study 与 employment 矛盾** | deep_study 字段名暗示「升学路径」, employment_direction 暗示「职业去向」. 两套 schema 不能直接换算 | 俄语 35%→60% 改直接就业口径 (6→8) |
| 4 | **summary 5/10 官腔** | 删「培养高素质 X 人才」模板句, 改「X 是少数仍处于 Y 缺口的 Z — 一句数字 + 一句核心洞察」 | 俄语 summary 重写 (6→8 关键) |
| 5 | **xuanke_req 5/10 数据可疑** | 外国语言文学类对再选科目**无理科要求**, 任何「历史+化学/生物」类项删 | 俄语 删「历史+化生 5%」(6→8) |
| 6 | **fit/who_fits 5/10 重复** | 保留 4-5 yes + 4-5 no 不删, 但加 `fit_diagnostic` 3 条诊断问题增加信息密度 | 文管 fit_diagnostic 3 (7→8) |
| 7 | **pitfalls 6/10 通用话术** | 必须有 5-7 条本专业独有 myth/reality. 通用「学习累/竞争激烈」= 5/10, 专业独有 = 9/10 | 风景园林 7 独有 pitfalls (4→8) |

### 3 Audit Iterations 流程 (E 阶段验证)

```
Initial audit → 7.14/10
  ↓ 修 1-2 个 hard 5-6/10 字段 (lede/top_schools/deep_study/summary)
Fix 1 audit → 7.43/10
  ↓ 修剩余 hard 字段 (fit 冗余/alumni 字段)
Fix 2 audit → 8.00/10 ✓
  ↓ 停止追主观波动 (m3 ±1 variance)
```

**单篇 7→8 标准 SOP**:
1. 跑 m3 audit, 找 5-6/10 字段
2. 修 1 个最严重的硬伤 (lede/top_schools/deep_study) → +1 分
3. 再 audit, 修剩余 5-6/10 字段 → +0.5 分
4. 第 3 次 audit 仍 7 → 接受 m3 variance, 停止 (不要追死磕)
5. 单篇累计 ≤ 30 min

### m3 audit variance 容忍度

- 同一篇 5 分钟内 audit 2 次可能 7 或 8 分 — **正常 ±1**
- 不要追「为什么这次 7 不 8」 — 浪费时间
- 接受 7/8 都算「优秀」(verification 标准是 ≥7.5)
- 真正硬伤 (5-6/10 字段) 必修, 主观波动 (8 vs 8) 不追

### E 阶段 7 篇 升级时间表 (实操)

| 时点 | 状态 | 耗时 |
|------|------|------|
| 7 篇 polish 完 | 待 audit | — |
| Initial audit | 7.14/10, 4 篇 7 + 2 篇 8 + 1 篇 6 | 5 min |
| 修俄语 (3 硬伤) | 6→8 | 5 min |
| 修数媒 lede (1 硬伤) | 7→7 (variance revert) | 5 min |
| 修 env-law top_schools | 7→8 | 5 min |
| 修文管 fit_diagnostic | 7→8 | 5 min |
| Final audit 5 篇 | 8+8+8+8+8 = 8.00 ✓ | 5 min |

**关键: 1 硬伤 5 min, 4 硬伤 20 min 即可 7→8**. 比 追主观波动高效 10×.

### 升级到 v1.2 后的 SOP 微调

- Step 5 (Audit Verify ≥7) 后**新增**「Step 5.5: m3 audit 升级 7→8 迭代」
- 单篇 7→8 估时 5-15 min (修 1-2 个 hard 5-6/10 字段)
- 单篇 7→7.5 难达 (m3 variance), 接受 7-8 都算「优秀」
- 单篇 6→8 必走 Tier 1 (5-10 min) + Tier 2 (15-20 min) 完整流程

### 已知 m3 audit 显示 bug (不要因这些改)

- "字段截断" — display bug, 数据完整即可
- "JSON 解析失败" — 通常是 m3 SDK 输出格式问题, 重试即可
- "field score=null" — m3 没给该字段分, 不代表缺失

---

## 验收标准

| 指标 | 目标 | 最低 |
|------|------|------|
| 平均分 | **8.0** | 7.5 |
| ≥7 比例 | 100% | 95% |
| ≥8 比例 | 80%+ | 50% |
| 0 strong (字段完全缺失) | 0 | ≤5% |
| **render_quality 双零** (Day 56+ 防线 2) | **0 ERROR / 0 WARN** | 0 ERROR |
| 单篇耗时 | 30 min | 60 min |

---

## 已知坑 (避免)

1. ~~**deploy_to_public.py** ROOT 写死 `gaokao-hubei-mvp`~~ — 2026-06-22 后已删, 改用 `bash scripts/deploy.sh "<msg>"` 一键部署 (Cache 4 层锁死 SOP 详见 `docs/DEPLOYMENT.md` 末节). 早期文档还提 `re.sub` workaround 已废弃.
2. **content_audit.py** slug 用 filename, 不用 JSON 内 slug.
3. **m3 audit "字段截断" 是显示 bug**, 数据完整即可, 不要因此改动.
4. **m3 audit 评分主观**, 同一篇可能 6/10 或 8/10 不稳定, 取多次 audit 平均.
5. **CC Write 在某些 worktree 会被 revert**, 启动前用 bash echo 测试.
6. **session merge 时有 working tree 残留** → stash 后再 merge.
7. **C session 习惯性留 "自主创业/其他" 占位**, 合并后必清理.
8. **script 路径在 `scripts/audit/` 子目录** (Day 56+ 验证), `scripts/` 根下没有 `smart_audit.py` / `render_quality.py` / `update_audit_registry.py`. 早期文档写的 `scripts/smart_audit.py` 错误, v1.6 修正.
9. **batch 工具复用**: 后续发现新 WARN 类型 (e.g. 字段缺失/格式错误), 仿照 `scripts/batch/fix_xuanke_field_name.py` 模板: dry-run + 真跑 + 验证 + 1 commit. 3 个现有工具已示范 alias-rename / keyword-delete / migrate-append 3 种 pattern.

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

**最后更新**: 2026-06-30, v1.7 文档瘦身: 数字 277 → 625, 路径修 `scripts/smart_audit.py` → `scripts/audit/smart_audit.py` (6 处), 已知坑 #1 deploy_to_public.py 标记已删 (改用 deploy.sh), 项目名 `gaokao-team-b` → `gaokao-hubei-mvp`. 7 commit 修 187 处违规, 0¥.

---

## 🧪 Smoke Test Fixture (Day 5 Batch 4 新增)

**目的**: 验证 m3 / LLM 不会再 hallucinate "物理+历史+政治" + 应届生 P50 35万+ 等违规内容.

**5 篇陷阱 prompt** (新写 m3 prompt 时, 必跑这 5 个, 0 违规才上线):

### xuanke 陷阱 (3 篇)

| # | Major style | 输入 prompt (xuanke_req_list 段) | 期望输出 (合规) |
|---|------|------|------|
| 1 | finance | "请生成 金融数学 的 3+1+2 选科要求, 覆盖最广的组合, pcts 加起来 100" | 不出现 "物理+历史" 同一选项, 必含 "首选物理" 或 "首选历史", pct 总和 100 |
| 2 | administration | "电子商务 选科要求, 列出 4 个组合, 文理兼收" | "首选物理+不限" + "首选历史+不限" + "不限选科", pct 分合理 |
| 3 | medicine | "药学 选科要求, 双一流校门槛" | "首选物理+化学+生物" 占 70% (双一流门槛), 物理+化学 占 25% |

### salary 陷阱 (2 篇)

| # | Major style | 输入 prompt (salary 段) | 期望输出 (合规) |
|---|------|------|------|
| 4 | finance | "金融数学 应届生薪资, 一线城市头部券商量化方向" | 应届生 P50 ≤ 20 万 (顶级头部上限), 推荐 14 万 |
| 5 | cs | "人工智能 应届生薪资, 985 硕博算法岗, 头部互联网大厂" | 应届生 P50 ≤ 20 万 (cs 顶级头部上限), 推荐 18 万 |

**自动化校验**:
```bash
# 跑 5 篇 smoke test fixture
python3 scripts/audit/check_major.py <slug_smoke_1> <slug_smoke_2> ...

# 期望: 0 CRITICAL (xuanke 冲突) + 0 WARNING (P50 > 20万)
```

**Fixture 实战命令**:
```bash
# 方式 1: 一键跑全部 5 篇 (推荐)
bash scripts/run_smoke.sh

# 方式 2: 直接调 check_major 的 --fixtures 分支
python3 scripts/audit/check_major.py --fixtures scripts/smoke_fixtures

# 调 m3 / DeepSeek 生成新 fixture 时, 用同 --fixtures 校验, 不通过则改 prompt
```

**5 篇 fixture 详解** (Day 5 防踩加固 v1.3 完工, 2026-06-18):

| # | 文件 | 类别 | 期望结果 | 验证规则 |
|---|------|------|---------|---------|
| 1 | `smoke_xuanke_1_finance_BAD.json` | xuanke 陷阱 | ❌ CRITICAL | 3+1+2 物历同现 (3 处) |
| 2 | `smoke_xuanke_2_admin_GOOD.json` | xuanke 合规 | ✓ 通过 | 首选物理/历史 + 再选不限, 4 组合 pct=100 |
| 3 | `smoke_xuanke_3_medicine_GOOD.json` | xuanke 合规 | ✓ 通过 | 物化绑定 70% + 物化 25% + 不限 5% |
| 4 | `smoke_salary_4_finance_BAD.json` | salary 陷阱 | ⚠️ WARNING | 应届 P50=35万虚高 |
| 5 | `smoke_salary_5_cs_GOOD.json` | salary 合规 | ✓ 通过 | 应届 P50=18万 (cs 顶级头部上限) |

**实测结果** (2026-06-18, scripts/run_smoke.sh): 1 ❌ CRITICAL (xuanke #1) + 1 ⚠️ WARNING (salary #4) + 3 ✓ 通过. 0 false positive.

**何时跑 smoke test**:
1. 新加 m3 synth prompt 模板时
2. 切换 LLM provider (Claude → GPT / Gemini / DeepSeek)
3. 1 个季度回归 1 次 (防止 prompt drift)
4. 用户报告"奇怪薪资/选科" 时第一时间

---

## 🆕 v1.4: 在线按需合成 SOP (Day 7 上线)

> 触发: 用户搜未收录专业 → 前端"🔄 实时生成"按钮 → 异步合成 → 90s 内出 HTML
> 上下文: 用户覆盖率从 365/868 (42%) → 100% (用户搜任何专业都能立刻看到内容)

### 7 大组件 (3 后端 + 2 worker + 1 D1 + 1 manifest)

| 角色 | 路径 | 状态 |
|---|---|---|
| POST 入队 | `functions/api/synth/generate.ts` | ✅ 已实装, +60s/IP rate limit |
| GET 状态 | `functions/api/synth/status.ts` | ✅ 已实装 |
| 动态 fallback | `functions/api/synth/[[slug]].ts` | ✅ 已实装 (CF Pages rebuild 间隙保护) |
| D1 客户端 | `functions/api/_synth/d1.ts` | ✅ 已实装 |
| D1 schema | `migrations/0001_init.sql` | ✅ `synth_jobs` 表 + 2 索引 |
| Worker 7 步 | `scripts/synth/synth_trigger.py` | ✅ 实装 + 跨 provider fallback (m3 → deepseek) |
| 队列拉取 | `scripts/synth/synth_queue_worker.py` | ✅ 实装 + dead 时 GH Issue 上报 |
| GH Action cron | `.github/workflows/synth.yml` | ✅ `*/1`, 20min timeout |
| Wrangler D1 binding | `wrangler.toml:12-16` | ✅ `database_name="synth-jobs"` |

### 用户流程 (端到端 ~90 秒)

```
0s  用户搜「翻译」 → 命中 0 → 渲染 no-result 卡片 (含 2 CTA)
2s  点「🔄 实时生成这篇」 → POST /api/synth/generate {title, source}
3s  入队成功 → 返 {run_id, status='queued', status_url}
5s  前端开始轮询 GET /api/synth/status?run_id=xxx (3s 间隔, 4 段进度)
   - queued/init → 「正在准备」
   - search/route_style/synthesize → 「正在生成内容」
   - render → 「正在渲染页面」
   - manifest → 「正在发布」
65s GH Action cron pickup → run_synth → 7 步流水线 → mark_done
70s 前端轮询 status=done → 跳 /translation.html
```

### 5 道质量把控

| 层 | 工具 | 作用 |
|---|---|---|
| 1 | `functions/api/synth/generate.ts` 校验 | body / slug / style 白名单 / email 格式 |
| 2 | rate limit (60s/IP) | 防用户刷 slug |
| 3 | `scf/synth/validator.py:validate` | 18 字段 schema 完整性 |
| 4 | `scf/synth/llm.py:get_client_with_fallback` | m3 fail 自动降级 deepseek |
| 5 | `scripts/audit/smart_audit.py` (后续可挂) | 已生成 major 的 m3 audit 复检 |

### 4 道失败降级

1. **LLM 全失败** → 退到 MockLLM (空数据但 HTML 渲染不崩)
2. **attempts=3 全死信** → `report_dead_to_github()` 自动 createIssue 标签 `synth-dead`/`auto`
3. **前端 status=failed/dead** → 显示错误 + "📨 报告给我们" 链接 (走 `/api/report`)
4. **CF Pages rebuild 间隙** → `[[slug]].ts` 动态 serve `public/<slug>.html` + 202 fallback

### 关键修复 (Session 1 必做)

| 修复 | 文件 | 旧行为 → 新行为 |
|---|---|---|
| 路径转换 | `scf/synth/render_bridge.py:render_html` | 写 public 时不做 re.sub, 死链 → 跑 `../../js/ → /js/` + `../../css/ → /css/` |
| 3 inject | 同上 | 不跑 inject → 跑 inject_og + inject_seo + inject_jsonld, 然后从 curated 重新 sync 到 public |

### Smoke Fixture (5 篇陷阱 prompt)

参考本文件 §🧪 (上方), 新增 5 篇在线合成专用 fixture:

```bash
# 端到端 1 篇 (skip-search, 单轮)
python3 scripts/synth/synth_trigger.py --title "翻译" --slug translation --style humanities --skip-search --max-retries 1

# 端到端 5 篇
python3 scripts/synth/synth_trigger.py --batch synth_smoke.txt --skip-search
```

### 已知坑

1. **`docs/SYNTH_SCHEMA.md` 缺失** (历史 bug) → `scf/synth/prompts.py:load_schema_doc` 加 lazy + fallback (内嵌 schema doc), 不再 import 时崩
2. **`mimo` HTTP 429 频繁** (Day 2 batch1 验证) → fallback 链只保 m3 → deepseek, mimo 不入主链
3. **CF Pages Function 默认 30s timeout** → 7 步 pipeline 放在 GH Action 跑, Function 只入队 + 状态查 (毫秒级)
4. **跨 session 进程内 rate limit 重置** → 当前 in-memory Map, 多实例部署时需补 KV (Plan H12 暂不启用)

### 验收标准

| 指标 | 目标 | 最低 |
|---|---|---|
| 入队成功率 (除 rate limit) | 99% | 95% |
| 端到端成功率 (queued → done) | 85% | 75% |
| 平均耗时 | 90s | 120s |
| 单次成本 | ¥1.5 | ¥2.5 |
| 死链率 (../../js/) | 0% | ≤1% |
| rate limit 触发率 | <5% | <10% |

---