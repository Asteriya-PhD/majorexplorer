# 对抗性内容审查报告 (2026-10-01)

> 目的: 补 `render_quality.py` 13 规则的盲区。render_quality 只查**结构**
> (字段在不在/段齐不齐/薪资单调), 本轮查**内容正确性**。
> 工具: `scripts/audit/adversarial_check.py` (9 大类规则, 0¥, ~54s / 625 篇)

## 0. 结论摘要

| 指标 | 数值 |
|---|---|
| 扫描专业 | 625 |
| ERROR | 3143 |
| WARN | 1613 |
| 受影响专业 | 602 (96.3%) |
| **其中单一根因占比** | **3072 / 3143 = 97.8%** |
| 真正独立问题 | **71** |

**关键判断**: 现有质量门 13 规则全绿 (625/625 双零), 但线上存在
**全站级内容丢失**。质量门是"结构正确性"意义上的合格, 不是"内容正确"。

---

## 1. P0 — 全站级内容丢失 (已修渲染器, 待重渲)

### 1.1 `employment_direction.desc` 全站丢失 (3072 处)

**现象**: mobile 端 634 个页面中 566 篇的就业方向只剩"标题 + 百分比",
描述文字**完全空白**。`<div class="emp-desc"></div>` 共 **4224 个空 div**。

**根因**: `scripts/build/render_mobile.py:836`
```python
desc = e.get("description", "")   # ← 读的键是 description
```
但 curated JSON 全库 625 篇实测用的键是 **`desc`**:
```json
{"name": "NLP 算法工程师", "pct": 30, "dest": "...", "desc": "应届 22-40 万…"}
```
键名不匹配 → `.get()` 静默返回 `""` → 模板里 `<div class="emp-desc"></div>`
被渲染成空标签。**无任何报错**,所以质量门 13 规则全绿。

**修复** (已改 + 已验证):
```python
desc = e.get("desc") or e.get("description") or ""
```
保留 `description` 兼容 LLM 合成产物 (`scf/synth/`)。

**验证**: 函数级测试 —— 7 个空 div → 7 个有内容, 内容与 JSON 逐字一致。

**待办**: 全量重渲 mobile (见 §4 风险提示)。

### 1.2 `alum-N` 占位符泄漏到线上 (12 篇 PC)

**现象**: 12 个 PC 页面用户可见位置显示 `alum-0#0` / `alum-1#1` …

**根因**: commit `eb570552e` (Day 49 "12 篇 major 修 FIELD-1") 修正了
JSON 里的 `alumni_quotes`, 但**没有重渲 HTML**。当前 JSON 已是
`"current": "校友 (脱敏)"`, HTML 仍是旧的 `alum-0#0`。

**为什么质量门没抓到**: `render_quality.py` FIELD-1 只检查 **JSON**,
不检查 **HTML**。JSON 干净 → 放行。

受影响: `business-administration` `chemical-engineering`
`civil-engineering` `forestry` `industrial-design`
`integrated-circuit-design` `international-economics-trade`
`landscape-architecture` `materials-science-engineering`
`mechanical-engineering` `microelectronics` `vehicle-engineering`

---

## 2. P1 — 内容漂移 (改了数据没重渲)

### 2.1 语录版本分叉 (ndebele / taxation)

`ndebele` 的 HTML 5 条校友语录与 JSON **完全无交集** —— HTML 是旧版本内容。
这类问题 `render_quality` 与本轮 X1 都能抓, 但暴露一个流程漏洞:
**改 JSON 不重渲 = 线上内容不更新**。

### 2.2 顶层 `lede` 与 `overview_v2.lede` 双源不同 (30 篇)

顶层 `lede` 是陈旧旧版, HTML 一律渲染 `overview_v2.lede`。
`scripts/build/sync_lede_to_top.py` 的同步没覆盖到这批。
不影响渲染, 但 meta/SEO 链路若读顶层 lede 会拿到旧文案。

---

## 3. P2 — 数据质量问题 (69 条, 需人工判断)

| 类型 | 数量 | 说明 |
|---|---|---|
| `X6/emp-pct-sum` | 30 | 就业方向 pct 合计 88-94, 应≈100。轻微, 属"未补齐"而非硬错 |
| `X9/what_you_learn` 缺 | 11 | simple 式 schema 声明了却没填 |
| `X8/dup-hero_quote` | 4 | 2 组专业共用同一金句 (核电技术/核工程; 播音/新闻传播) |
| `X8/dup-what_you_learn` | 2 | 生物育种 2 篇 (science/technology) 完全同文案 |
| `X1/pitfalls[*].reality` | 7 | 逐字核验为**误报** (标点全/半角差异), 已修 norm() |

### 3.1 WARN 值得关注的两类

- `X4/no-domain-vocab` **135 篇**: 理工/经管内容里 0 个专业信号词, 内容泛化。
  这是 AGENTS.md anti-pollution 铁律 1「删通用模板套话」的量化指标 ——
  删干净套话后, 好内容应有领域词; 0 个说明**删过头了**。
- `X2/quotes-missing-in-MB` 14 篇: mobile 端缺校友语录。

---

## 4. ⚠️ 重渲风险 (本轮踩到, 务必按此流程)

**`render_mobile.py` 单独重渲会丢失 SEO 注入块。** 实测:
`render_mobile.py --slug X` 后再跑 `inject_twitter_card.py` /
`inject_hreflang.py` —— 注入脚本**非幂等**, 会向 1274 个已注入的文件
**重复插入** (本轮已 `git checkout -- public/` 回滚)。

正确重渲流程:
```bash
# 1. 渲染 (会丢 SEO 块, 这是预期的)
python3 scripts/build/render_mobile.py --slug <slug>
# 2. 重新注入 SEO (仅对刚渲染的 slug 跑, 不要全量)
python3 scripts/build/inject_twitter_card.py   # ← 全量会重复插入, 需先修幂等
python3 scripts/build/inject_hreflang.py
```
**建议**: 先给两个 inject 脚本加幂等保护 (检测 `BEGIN_SEO_*` 标记已存在
则跳过), 再做全量重渲。

---

## 5. 本轮新增工具

`scripts/audit/adversarial_check.py` — 9 类规则:
- X1 渲染漂移 (JSON 值未进 HTML) / X2 双端分叉 / X3 manifest 不一致
- X4 学科串台 / X5 事实硬伤 / X6 数值矛盾
- X7 占位符 / X8 跨专业雷同 / X9 schema 漂移

已接入 `.githooks/pre-commit` 第 6 步 (warn-only; 存量清零后切 ERROR)。

**误报率校准记录** (初版 576 ERROR → 最终 71 独立问题), 关键校准:
1. X4 串台只查 `who_fits_no` (AGENTS.md 铁律 2 原义), 不查全文 blob
2. 串台词表剔除 `考公/考证/田野调研` — 都是真实劝退理由 (18 篇误报)
3. `discipline` 是 MOE 两位代码, 不是中文名
4. 医学类 (41 篇) 走 `v4_medicine.py` 独立渲染器, X1 不适用
5. `overview_v2` 有 simple / v2 两套合法 schema
6. `norm()` 必须归一化全角标点 (渲染器会转换)
7. `mobile` 只渲前 8 个就业方向, 超出不算缺失
