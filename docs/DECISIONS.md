# DECISIONS.md — 决策记录 (ADR 风格)

> Architecture Decision Records。锁定关键设计选择,防止"为什么这样做"在 6 个月后被改回去。
> 格式: 上下文 → 决定 → 后果。每次重大修改要更新对应 ADR 或加新的。

---

## ADR-001: 3-source merge 策略

**日期**: 2026-06-07
**状态**: ✅ 锁定

### 上下文
2024 历史/物理 真实完整版需要 ~280/~380 行数据,但没有任何单一公开源能完整覆盖 (gk100 只覆盖 1-3 万名,555edu 只覆盖 135 校湖北本地,dxsbb 6261 只覆盖 985/211/重点一本)。

### 决定
3 源合并,优先级:
1. **555edu 逐校抓** (最高优,135 校 × 平均 5 个专业组 = ~600 行,覆盖广)
2. **dxsbb 6261 一本** (中,140 行,985/211 准确)
3. **硬编码锚点** (最低,33 行,作为最后兜底)

代码: `scripts/merge_real_2024.py`,按 `_priority` dict 排序后 `drop_duplicates(subset=["school_name", "group_id"], keep="first")`。

### 后果
- ✅ 254 行物理 / 140 行历史真实本科 (2024 湖北)
- ✅ 优先级明确,改 fetcher 不影响 merge
- ⚠️ 多源 schema 不一致 (`normalize()` 函数处理)
- ⚠️ 同校同 group 跨年可能不一致 (需 `group_id` 跨年稳定)

---

## ADR-002: 555edu per-school 抓取 over gk100 单表

**日期**: 2026-06-07
**状态**: ✅ 锁定

### 上下文
gk100.com/read_38500828.htm 2025 物理 205 行,但 2024 历史只有 33 行 (覆盖前 1-3 万名,普通本科无)。需要更全的数据。

### 决定
555edu.com/hubei/ 列 135 校,每校 `/school-{id}-1-780/{page}` 列文章 (最多 25 页)。对每校找 "2024年湖北{物理/历史}类" 文章,parse 4-schema 通用表。

代码: `scripts/fetch_555edu_hubei.py` + `fetch_555edu_2023.py` + `fetch_555edu_guangdong_jiangsu.py`

### 后果
- ✅ 135 校 × 平均 5 个专业组 = ~600 行,覆盖本地普通本科
- ✅ 4-schema 通用解析 (10-col 本科 / 9-col 高职高专 / 8-col 2023 / 7-col 广东)
- ⚠️ GBK 编码,需 `txt = data.decode("gbk", errors="replace")`
- ⚠️ 每校单独 fetch,~10-15 分钟全量,生产前要 cron 化

---

## ADR-003: 3+3 模式分开 filter 而非合并到 3+1+2

**日期**: 2026-06-07
**状态**: ✅ 锁定

### 上下文
新高考两种模式: 3+1+2 (湖北等 8 省,首选物理/历史必匹配 + 再选任一) / 3+3 (京/沪/津/浙/鲁/琼,6 选 3 无首选概念)。代码里若把 3+3 当 "3+1+2 退化版" 会污染首选概念。

### 决定
`core/filter.py` 分两个函数: `_match_xuanke_3_plus_1_plus_2` / `_match_xuanke_3_plus_3`。`get_xuanke_mode(province)` 按省份集合分发。

```python
def match_xuanke(student_xuanke, required_subjects, mode="3+1+2"):
    if mode == "3+3":
        return _match_xuanke_3_plus_3(student_xuanke, required_subjects)
    return _match_xuanke_3_plus_1_plus_2(student_xuanke, required_subjects)
```

### 后果
- ✅ 概念清晰,无首选污染
- ✅ 3+3 院校要求格式 "X,Y" (任一) 或 "X+Y" (都需) 单独解析
- ⚠️ 加新模式要新加函数 (扩展点已留)

---

## ADR-004: Gaussian CDF 估录取概率

**日期**: 2026-06-06 (Day 1)
**状态**: ✅ 锁定

### 上下文
离散分位表 (p10/p50/p90) 需要每年投档表的详细分位,公开数据通常只给最低分/最低位次。Gaussian CDF 可以只用 1 个数 (median rank) 估连续概率。

### 决定
```python
σ = max(0.25 * median_rank, 1)              # 浮动 25%
z = (student_rank - median_rank) / σ
P = 0.5 * (1 + erf((-z + 0.7) / √2))         # 偏 +0.7 让稳档更宽
category = "冲" if P<0.30 else "稳" if P<0.70 else "保"
```

`+0.7` 偏置: 让学生排名略好于 median 时也归"稳"档,避免 Gaussian 太严格导致志愿太少。

代码: `core/probability.py:estimate_admission_probability`

### 后果
- ✅ 只需 median rank,数据需求低
- ✅ 概率连续,排序更平滑
- ⚠️ 假设 Gaussian — 真实录取分布可能偏态 (头部厚尾)
- ⚠️ σ=25% 是经验值,未在不同年份校准

---

## ADR-005: `strategy_bonus` 不进 sort key

**日期**: 2026-06-07
**状态**: ✅ 锁定 (重要)

### 上下文
`core/strategy.py` 算出 `strategy_bonus(student_goal, family_bg, school_type)`(0-40 分)。理论上可加进 sort key 让"考公导向"考生优先看 985/211。

### 决定
**不加**。`strategy_bonus` 只用于 `VolunteerItem.strategy_note` 文字,排序仍按 `_sort_key = city·100k + layer·1万 + prob·10`。

### 后果
- ✅ 985/211 主导排序,不会因 family=困难 而把 985 排到普通本科之后
- ✅ 策略建议是"参考",不"颠覆"主排序
- ⚠️ 用户需自己看 `strategy_note` 文字理解差异
- ⚠️ 与典型"个性化推荐"系统期望不符 — 这是有意为之

**为什么**: 让"考公"的差学生也能看到冲档的 985 机会,不会因为"考公加权"把志愿限定在 211/普通。

---

## ADR-006: 2024/2023 数据用合成补普通本科

**日期**: 2026-06-07
**状态**: ⚠️ 临时方案 (生产前必须替换)

### 上下文
真实数据:
- 985 完整 (gk100/今日头条整理)
- 211 部分 (gk100 锚点)
- 本省 重点本科 部分 (555edu 抓)

普通本科 + 专科 公开源几乎没有。

### 决定
`fetch_2024_2023_anchors.py` 用 2025 基础 + ±5/±10 名次 波动合成普通/专科部分。`data_source` 字段标 "合成(基于 2025+波动)" 以明示。

### 后果
- ✅ 96 志愿生成有 足够候选 (~140-250 行)
- ⚠️ 普通本科的位次是估的,可能 ±20% 误差
- ⚠️ 文档必须明示用户这是估算
- ❌ 生产前必须替换为 hbea.edu.cn 官方 PDF/Excel

---

## ADR-007: Guangdong/Jiangsu 投档表 group_id 简化为 "01"

**日期**: 2026-06-07
**状态**: ⚠️ 临时方案 (广东/江苏有完整数据后改)

### 上下文
555edu 广东/江苏 2024 文章 schema 是 7-col: `院校名称 | 年份 | 科类 | 选科要求 | 批次 | 投档线 | 投档线位次 | 备注` — **没有专业组代码字段**。

湖北 schema 是 10-col 含 `院校专业组代码` (如 A14108)。

### 决定
广东/江苏 投档表 `group_id` 全部填 "01" (占位)。

### 后果
- ✅ fetcher 通用,广东/江苏 可用
- ⚠️ 同校多组无法区分 (实际广东 2024 改革无专业组,所以单组合理)
- ❌ 若广东/江苏 改革后恢复专业组,要重新设计

---

## ADR-008: dxsbb 6261 缺位次用 score→rank 一分一段反查

**日期**: 2026-06-07
**状态**: ✅ 锁定

### 上下文
dxsbb 6261 表格只有 投档线 (score),没有 投档线位次 (rank)。其他源 (555edu / 锚点) 都直接给 rank。

### 决定
`scripts/fetch_dxsbb_6261.py` 加载 2024 一分一段表,对每个 score 反查 rank:

```python
def score_to_rank(score, rank_table):
    eligible = rank_table[rank_table["score_int"] <= score]
    return int(eligible.loc[eligible["score_int"].idxmax()]["rank"])
```

### 后果
- ✅ 唯一缺位次的数据源被挽救
- ⚠️ 反查是近似 (同分有多个考生,实际位次是范围)
- ⚠️ 误差约 1-5 名,不影响 96 志愿生成

---

## ADR-009 (待写): 3+3 模式真实数据未做

**日期**: —
**状态**: ⏳ pending

### 上下文
京/沪/津/浙 4 省 3+3 模式代码 ready,但无真实一分一段表 / 投档表。

### 决定
(待做) — `eol.cn` 抓 3+3 一分一段表; 3+3 投档表按 2024 新高考 (教育部统一) 抓 hbea 等价源。

---

## ADR-010 (待写): PDF 报告省份硬编码

**日期**: —
**状态**: ⏳ pending

### 上下文
`api/pdf_report.py` 中 `province` 映射只有 湖北/广东/江苏/其他,其他省份 PDF 文件名 fallback。

### 决定
(待做) — 用 `core/data_loader.get_all_provinces()` 替代硬编码。

---

## 如何添加新 ADR

```bash
# 1. 复制本文件末尾的"待写"模板
# 2. 编号递增
# 3. 状态: 提议 → 锁定 / 弃用 / 过期
# 4. 引用代码路径 (file:line)
# 5. 后果必须列"好处"和"坏处"
```

模板:
```markdown
## ADR-NNN: <一句话>

**日期**: YYYY-MM-DD
**状态**: ⏳ pending / ✅ 锁定 / ❌ 弃用 / 🕐 过期

### 上下文
<为什么做这个决定>

### 决定
<做了什么>

### 后果
- ✅ 好处
- ⚠️ 风险
- ❌ 失败条件
```
