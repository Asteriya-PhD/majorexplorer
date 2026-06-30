# RENDER_QUALITY_RULES.md — 渲染后 HTML 质量门 13 条规则参考

> Day 49 (2026-06-30) 上线, 13 条规则全为启发式 (0¥, <2s/625 篇).
> 入口: `python3 scripts/audit/render_quality.py --all` / `--slug <slug>` / `--staged` / `--fixtures <dir>`.

---

## 规则清单

| ID | 严重度 | 检查对象 | 公式/正则 |
|---|---|---|---|
| **SAL-MONO-1** | ERROR | salary 阶段内 | `p25 ≤ p50 ≤ p75` (LLM drift 倒挂) |
| **SAL-MONO-2** | ERROR | salary 跨阶段 | 应届 < 3年 < 5年 < 10年+ p50 单调递增 |
| **SAL-CAP-1** | ERROR | senior stage | 10年+/资深 p75 ≤ 100, 含头部例外仍 ≤ 200 |
| **SAL-NOTE-1** | WARN | salary | `note` 字段仅允许 senior stage |
| **HTML-PC-1** | ERROR | PC HTML | 8 段齐备 (id=overview/curriculum/schools/companies/salary/directions/quotes/xuanke) |
| **HTML-PC-2** | ERROR | PC HTML | meta description 长度 ∈ [50, 160] + 无未转义 `<`/`>` |
| **HTML-PC-3** | ERROR | PC HTML | `<script type="application/ld+json">` 块存在且合法 JSON |
| **HTML-PC-4** | ERROR | PC HTML | og:title + og:description + og:image 三件套 content 非空 |
| **HTML-MB-1** | ERROR | mobile HTML | 10 个 art-num (`一二三四五六七八十十一`, **无九**) 全有 |
| **FIELD-1** | ERROR | JSON | alumni_quotes 无 `alum-N` 字面占位符 |
| **FIELD-2** | WARN | JSON | hero_quote 长度 ∈ [10, 200] + 含署名标记 (`——`/`—`/`「`/`"`/hero_quote_sig) |
| **FIELD-3** | WARN | JSON | xuanke_req_list 每个 item 有 `name` 字段 (renderer normalize 兜底) |
| **FIELD-4** | ERROR | JSON | employment_direction pct 合计 ∈ [80, 120] |

---

## STAGE_RANK (跨阶段排序关键字)

```python
STAGE_RANK = [
    ('应届', 0),
    ('0-2', 1),
    ('1-3', 2),
    ('2年', 2),
    ('3年', 3),
    ('5年', 4),
    ('8年', 5),
    ('10年', 6),
    ('资深', 6),
    ('主编', 6),
]
```

未匹配的 stage name 跳过(不报错), 仅按 rank 排序后检查相邻对的 p50 单调.

## SENIOR_KEYWORDS (资深判定)

```python
SENIOR_KEYWORDS = ['10年', '资深', '高级', '专家', '合伙人', '管理层', '主编']
```

`10年+/资深` → SAL-CAP-1 触发 (p75 ≤ 100).

## NOTE_EXCEPTION_KEYWORDS (头部例外)

```python
NOTE_EXCEPTION_KEYWORDS = ['头部', '合伙人', 'CTO', '明星', '顶级', '首席', 'VP']
```

含此类关键字的 `note` 时, SAL-CAP-1 阈值放宽到 200.

---

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | clean (0 ERROR) |
| 1 | ≥1 ERROR 违规 |
| 2 | catastrophic (manifest 坏或文件读不出来) |

## CLI

```bash
# 全量 baseline (~2s for 625 majors)
python3 scripts/audit/render_quality.py --all

# 全量 + 同步到 registry
python3 scripts/audit/render_quality.py --all --sync-registry

# 单 slug
python3 scripts/audit/render_quality.py --slug computational-linguistics

# git staged diff (pre-commit 调用)
python3 scripts/audit/render_quality.py --staged

# fixtures 模式 (15 fixture 全自动验证)
python3 scripts/audit/render_quality.py --fixtures scripts/audit/render_quality_fixtures

# 不显示 WARNING (CI 模式)
python3 scripts/audit/render_quality.py --all --no-warn
```

## 输出

- `test_results/render_quality_{ts}.json` — 完整结果
- stdout — 摘要 (扫了多少篇, 各 rule 命中次数, 通过/失败/警告数)

---

## Day 49 Baseline 实测 (修 SAL-MONO-2 同 stage 细分误报后)

```
── render_quality ──
扫描 manifest 625 篇
  SAL-NOTE-1: 127 次  ← note 错位
  SAL-MONO-2: 66 次   ← 跨阶段倒挂 (修误报后, 100% 真)
  FIELD-3:    59 次   ← xuanke 字段名
  HTML-PC-4:  54 次   ← og: 三件套不全
  SAL-CAP-1:  37 次   ← 资深 p75>100
  HTML-PC-3:  34 次   ← JSON-LD 缺失 (P0)
  HTML-MB-1:  15 次   ← mobile 段缺
  FIELD-1:    12 次   ← alum-N 占位 (P0)
  FIELD-2:     7 次
  SAL-MONO-1:  6 次   ← p25>p50
──
✓ 通过: 493 篇 (79%)
❌ 失败: 132 篇 (21%, 全部已抽样验证为真问题)
⏱️  1.1s
```

### SAL-MONO-2 同 stage 多细分场景的处理

实际数据中常见同一 career stage 拆多个细分(如"应届生(一线)" + "应届生(二三线)")。这些细分场景间 p50 不同是合理的(一线 > 二三线)。规则修正:
- 取每个 rank 内的**最低 p50** 作代表值
- 同 rank 不比较
- 只比较相邻 rank 的代表值

修误报前 SAL-MONO-2 误报 ~190 个,修后 66 个全部为真实倒挂(几乎都是"5年经验细分(高端)" 高于 "10年+ 细分(常规)" 的市场顶端重叠)。

---

## 集成点

1. **pre-commit hook** (`.githooks/pre-commit` 第 5 步): `--staged` 模式, **warn-only 至 Day 55**, Day 56+ 切 ERROR 阻塞
2. **smart_audit.py Layer 0** (Day 49 新增): 路由 m3 audit 时, L0 violation 也作为 L2 触发依据
3. **update_audit_registry.py**: `--from-render-quality <path>` 同步到 registry 顶层 `render_quality` key

## 已知限制

- **PC HTML 缺失 → WARN** (Day 49 baseline 期间不少 major 还没渲染)
- **mobile HTML 缺失 → 不报错** (mobile 覆盖不全)
- **xuanke 字段名 → WARN** (renderer 已 defensive normalize 到 `name`, 不阻断)
- **note 仅 senior → WARN** (历史数据沿用, 阻断风险大)

## Day 56 切硬阻塞 (2026-06-30)

**触发条件**: Day 49-55 期间 render_quality ERROR 走 warn-only, 累积 100% 0-ERROR baseline
**改动**: `.githooks/pre-commit` step 5 把 `warn_only` 改为 `failed=1`, 任何新 HTML ERROR 立即阻断 commit

**新 ERROR 修复 SOP**:
1. 跑 `python3 scripts/audit/render_quality.py --slug <slug>` 看具体违规规则
2. 修 source JSON (或 HTML, 看规则)
3. 跑 `python3 scripts/audit/render_quality.py --slug <slug>` 复验
4. 跑 `python3 scripts/audit/render_quality.py --all --sync-registry` 同步 registry
5. 重 commit (hook 应过)

**绕过**: 仅 `git commit --no-verify` (不推荐, 需在 PR 描述说明原因)

**持续监控**:
- 每周一 8am cron 跑 `--all --sync-registry`, 结果 `test_results/render_quality_weekly.json` 留历史
- `data/audit_registry.json` 的 `totals.render_quality_errors` 应保持 0, 涨了立刻 alert

## Day 50-52 WARN 清理 (2026-06-30 完工)

| 规则 | 修前 | 修后 | 工具 |
|---|---|---|---|
| FIELD-3 xuanke 字段名 (combo/item → name) | 59 | 0 | `scripts/batch/fix_xuanke_field_name.py` (15 篇) |
| SAL-NOTE-1 非 senior note 删 | 128 | 42 | `scripts/batch/fix_salary_note_placement.py` (37 篇, 删 86) |
| FIELD-2 hero_quote 10-200 字 + 署名 | 7 | 0 | 手审 7 篇 (4 截短 + 3 加 sig) |

**SAL-NOTE-1 残留 42 处** (经验范围 + 真实段位) → 下个 session 手审
**scripts/batch/***: 留作后续类似批量 fix 复用

## 修复指引 (baseline 249 ERROR)

| Rule | 修法 |
|---|---|
| HTML-PC-3 (JSON-LD 缺失) | `python3 scripts/build/inject_jsonld_v2.py` 跑全量 |
| HTML-PC-4 (og 三件套) | 检查 SEO 注入流水线 `scripts/build/inject_seo.py` |
| SAL-MONO-1/2 | 手修 JSON salary, 按 STAGE_RANK 重排 |
| SAL-CAP-1 | 资深 p75 改 ≤ 100 或加 note 说明头部例外 |
| HTML-MB-1 | 重渲 mobile: `python3 scripts/build/render_mobile.py --slug <slug>` |
| FIELD-1 | 替换 alumni_quotes 里的 `alum-N` 占位 |