# gaokao-major-explorer 技术架构 · 30 天演化

> Technical Architecture · 一个高考专业介绍页生成器的 loop engineering 沉淀
> 2026-06-26 · Python 单进程 + 12 主题 · 1268 JSON · 600 完整精品 · v3.0 → v4.0 · **真实跨度 16 天**

> 配套 HTML 长图版:
> - 桌面优先: [`2026-06-26_skill-architecture.html`](2026-06-26_skill-architecture.html)
> - 公众号推送: [`2026-06-26_skill-architecture_wechat.html`](2026-06-26_skill-architecture_wechat.html)

---

## 00. 一句话定位

**输入**: 一份手编 JSON(18 字段, 70KB, 描述一个高考专业)
**输出**: 一份 60-100KB 的单文件 HTML 长图文, 内嵌 CSS + JS, 双击可开
**中间**: Python 单进程, 从 12 套主题里选一套, 把 JSON 字段装配成设计版面

| 指标 | 值 | 备注 |
|---|---|---|
| 数据规模 | 1268 | JSON 文件数 |
| 完整精品 | 600+ | 篇 (其余为基线) |
| 视觉主题 | 12 | 套 |
| 平均渲染 | <1 | 秒/篇 |
| 质量分 | 8.0+ | avg (m3 LLM 审计) |
| 代码量 | ~300 | KB |

---

## 01. 全景:从输入到输出

整个系统只有 **3 层**: 数据、引擎、产出。质量层和部署层围绕这三层运转。

![架构全景图](assets/skill-arch-2026-06-26/ascii_1.png)

> **核心命题**: 渲染引擎本身只占代码量 30%, 剩下 70% 是**质量审计链**。这才是 loop engineering 的真正价值 — **不期望能一次生成到位**, 而是建一套反馈闭环让内容持续逼近目标分。

---

## 02. 模块依赖图

入口 `generate_dashboard.py` 只做一件事: **按 style 字段路由**。

![模块依赖图](assets/skill-arch-2026-06-26/ascii_2.png)

**v4_styles 包内部**关键设计 — 一切都是 Python 包, 主题是子目录:

![主题目录](assets/skill-arch-2026-06-26/ascii_3.png)

> **关键洞察**: 加一个新主题只需要 1 个 `.py` 文件(几十行 CSS + 1 个 HERO_FN), **完全不用改**任何渲染函数。这就是下面要讲的"主题差异化最小化"原则。

---

## 03. 4 层架构:数据 → 代码 → 质量 → 部署

把视野拉到全局, 有 4 层相互配合:

![4 层架构图](assets/skill-arch-2026-06-26/ascii_4.png)

---

## 04. 3 个核心设计模式

### ① 主题差异化最小化

12 套主题, 共享所有 30+ 渲染函数, 只换 3 块 CSS + 1 个 HERO 函数。

```
所有主题共用:  ─────────────────────────────
                30+ 渲染函数 (render_xxx)
                JSON schema 解析
                数据归一化 (salary/xuanke/curriculum)

主题差异化:    ─────────────────────────────
                3 个 CSS 块 (base + body_bg + theme)
                1 个 HERO_FN 函数 (每个主题一个)
```

### ② HTML 后处理管道化

Cross-cutting concerns(战略 chip、学科评估、面包屑)从渲染逻辑里抽出来, 做 HTML 后处理。

```
JSON → render_v4() 装配 HTML
            ↓
      apply_strategy_tags()        ← 国家战略 chip
            ↓
      apply_chsi_rating()          ← 学科评估标签
            ↓
      apply_discipline_breadcrumb() ← 学科面包屑
            ↓
      写出文件
```

### ③ Schema 容错漏斗

30 天里 JSON schema 演化过 N 次。容错层吸收所有差异, 渲染函数对历史脏数据完全免疫。

```
JSON 原始输入
    ↓
_coerce_named()        ← 字符串/对象兼容
    ↓
_normalize_xuanke()     ← 4 种 schema 变体统一
    ↓
_sort_salary_stages()   ← 主+次键排序
    ↓
_dedup_by_name()        ← schools 去重
    ↓
渲染函数  ← 此时 schema 已稳定
```

> **工程教训**: 没有这层容错, 30 天里每次 schema 调整都要改几十个渲染函数。漏斗模型让渲染函数**对历史脏数据免疫**, 这是 loop engineering 中"演进友好"的关键。

---

## 05. 单篇 JSON 的 1 秒旅程

以 `computer-science.json` 为例:

![端到端时序](assets/skill-arch-2026-06-26/ascii_5.png)

单篇 **< 1 秒**, 600 篇全量重渲染 ~5 分钟。

---

## 06. 演化时间线(以 git 实测日期为锚)

| 真实日期 | 里程碑 | 数据量 |
|---|---|---:|
| 2026-06-10 | v3.0 引擎 + rebrand + 早期 4 主题 (commit `e5b0aabd`) | ~50 |
| 2026-06-12 | **v4.0 拆分**: `v4_styles.py` → `v4_styles/` package (commit `afc5869c`) | ~200 |
| 2026-06-17 | Day 3 Team B 大批 (47 篇全新 major + 6 polish) | 365+ |
| 2026-06-18 | **smart_audit.py** 上线 (commit `72d1e7b9`) — L1 启发式 + L2 智能路由 | 500+ |
| 2026-06-22 | Day 24-25 MED/HIGH polish, 8+ 比例 → 91% | ~600 |
| 2026-06-25 | Day 30 polish 完工, 8+ → 97% | 600+ |

> ⚠️ **诚实声明**: 上表日期**全部来自 `git log --format="%ad"` 实测**, 不是事后回忆。真实跨度 **2026-06-10 → 2026-06-26 = 16 天**(不是 30 天, 也不是 14 天)。版本号真实可锚定的只有 **v3.0 → v4.0**(commit `afc5869c`)。
>
> **核心教训**: 项目迭代太快, 没空天天维护"Day X 完成 Y"日志, 也没有用 GitHub Issue / Project Board 跟踪里程碑。下次类似项目应该从 Day 1 就建 issue 跟踪, 而不是事后回忆 + git 反查。

---

## 07. 9 步质量闭环(loop engineering 的核心)

渲染引擎只是骨架。下面这套 9 步流水线才是让 600+ 篇精品稳定 ≥7 分的关键 — 藏在 [`docs/PIPELINE_major_quality.md`](../PIPELINE_major_quality.md)(v1.4) 里。

| Step | 动作 | 目的 |
|:---:|---|---|
| 0 | Auto-Repair Rank 字段 | 长期治理数据漂移 |
| 1 | Audit Driven | 必读历史 m3 audit issues |
| 2 | Anti-Pollution 4 Rules | 前置必避的 4 大污染 |
| 3 | Hand-Write JSON | 按专业逐字段手填 |
| 4 | Render + Deploy | 单篇渲染 + 部署 |
| 5 | Audit Verify | **≥7 才继续**, 否则进 Step 6 |
| 6 | Tier Retry (1/2/3) | 补字段 → 重写 → 标记跳过 |
| 7 | Single Commit Per Major | 单专业单 commit, 可回滚 |
| 8/9 | Schema Cleanup + Full Batch Audit | 合并后批量 + 全量重审 |

### Smart Audit Router (Step 5 的执行器)

Step 5 不是朴素全审, 而是 **Layer 1 启发式 + 智能路由 Layer 2 LLM** 的两层架构:

```
Layer 1: check_major.py 启发式 (1s/篇, 0¥)
   ↓
智能路由决策: 哪些篇需要 Layer 2?
   触发条件 (满足任一):
     1. L1-error  (污染/缺失)
     2. L1-warning
     3. 无历史 audit
     4. 历史 score < 7
     5. 改过
   ↓
Layer 2: m3 LLM audit (2min/篇, ¥0.5, thinking=ON)

混合模式: L1 100% + L2 ~30% = 2-3h / ¥40, 覆盖率 95%+
朴素全审: 9.3h / ¥140, 100%
```

> **核心洞察**: 9 步流水线 + Smart Router 才是 loop engineering 的核心。渲染引擎只是 Step 4 的执行器 — **没有 Step 0-3 的输入治理和 Step 5-9 的反馈闭环, 内容质量会停在 5-6 分**。

---

## 08. 5 条经验沉淀

1. **9 步流水线比渲染引擎重要** — 引擎只占代码量 30%, 流水线贡献 70% 的质量提升。Loop engineering 的本质是建反馈闭环。
2. **schema 容错比严格重要** — 30 天 schema 必演化, 提前建漏斗比反复改 schema 划算 10 倍。
3. **主题差异化最小化** — 从 4 套扩到 12 套, 渲染代码一行没动。
4. **Cross-cutting 后处理化** — 战略 chip / 学科评估 / 面包屑都不该污染渲染函数。
5. **质量闭环 = 单一真理表** — `audit_registry.json` git tracked, 所有 agent 行动前先 pull, 避免重复审计浪费 ¥。

---

· · · · ·

*gaokao-major-explorer · v3.0 → v4.0 · 2026-06-26*
*本文是 30 天 loop engineering 实践的技术沉淀, 如有反馈欢迎在 GitHub Issue 交流。*
