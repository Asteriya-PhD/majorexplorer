# SYNTH_SCHEMA.md — 按需生成 JSON Schema 规范

> **目的**: 规范 LLM 合成专业 JSON 的字段,与 `skills/gaokao-major-explorer/scripts/v4_styles/render.py` 渲染器消费字段**完全一致**。
> **依据**: 60 精品样板 + `anesthesiology.json` 完整样本 + `generate_dashboard.py:32-53` 渲染器入口读取字段清单。

---

## 0. 配置

### DeepSeek API key

`scf/synth/llm.py` 用 raw HTTP 调 DeepSeek (Anthropic 兼容端点). **不要用 anthropic SDK**, 因为它会注入 Claude 自家 auth token, 覆盖用户 key.

```bash
# 方式 1: .env (gitignored)
echo "DEEPSEEK_API_KEY=sk-..." > /Users/zhewenliu/Claude/gaokao-hubei-mvp/.env

# 方式 2: 直接 export
export DEEPSEEK_API_KEY="sk-..."
```

**端点**: `https://api.deepseek.com/anthropic/v1/messages`
**Header**:
- `x-api-key: <DEEPSEEK_API_KEY>`
- `anthropic-version: 2023-06-01`
- `Content-Type: application/json`

**模型**: `deepseek-chat` (V3)

### 不在 key 时的降级

`scf/synth/mock_llm.py` 提供 template-based mock, 让 pipeline 仍可跑 (供 T9 调优 + CI 测试).

`get_llm_client()` 自动选择: `DEEPSEEK_API_KEY` 设 → DeepSeek, 否则 mock.

---

## 1. 顶层必填字段 (10 个)

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `slug` | string (kebab-case) | URL 友好,用作文件名 | `"insurance"` |
| `title` | string (中文) | 专业全称 | `"保险学"` |
| `category` | string | 学科门类·专业类 | `"经济学 · 金融学类"` |
| `style` | enum (13) | 主题 | `"finance"` |
| `degree` | string | 学位 | `"经济学学士"` |
| `duration_years` | int (4 or 5) | 学制 | `4` |
| `tags` | list[str] (≥4) | 标签 | `["考证","稳定",...]` |
| `summary` | string (50-200 字) | Hero lede | `"..."` |
| `curriculum` | object (≥3 块) | 课程结构 | 见 §3 |
| `top_schools` | list[object] (≥5) | 头部院校 | 见 §4 |

**13 个合法 style** (必须严格匹配):
- `cs` / `eng` / `medicine` / `education` / `finance` / `law` / `humanities` / `sci` / `administration` / `agri` / `arts` / `gongan` / `business`

**校验失败 = 整篇废弃**,LLM 必须按以下规范重生成。

---

## 2. 强必填字段 (缺则视觉崩坏) (8 个)

| 字段 | 类型 | 最小值 | 说明 |
|------|------|--------|------|
| `salary` | object | ≥3 stage | 薪资表 (应届/3年/5年) |
| `employment_direction` | list[object] | ≥3 | 就业方向 + 占比 |
| `alumni_quotes` | list[object] | ≥2 | 校友访谈 |
| `xuanke_req_list` | list[object] | ≥3 | 选科要求 |
| `data_source` | string | - | 数据出处 |
| `difficulty` | string | 1-5 星 | 学习难度 |
| `updated_at` | string (YYYY-MM) | - | 数据日期 |
| `hero_quote` | string | - | Hero 金句 (默认可空,渲染器兜底) |

---

## 3. `curriculum` 块结构

3 个**特殊 key** 优先渲染(命名严格):

```json
{
  "公共必修 (所有院校都开)": [{"name": "...", "credit": "3"}, ...],
  "通用专业核心 (≈ 80% 院校覆盖)": [...],
  "5 校特色选修 (按方向分流)": [...]
}
```

**注意**: 渲染器读 key 的字符串是 `"公共必修"` / `"通用专业核心"` / `"5 校特色选修"` (后跟括号说明)。

**通用规则**:
- 每个块 3-12 门课
- `name` 必填
- `credit` 必填,可为 `int` 或 `"3"` 字符串

**任意追加块**: 除 3 个特殊 key 外,可加任意 key 渲染器会自动列出。

---

## 4. `top_schools` 列表元素

```json
{
  "name": "中国人民大学",        // 必填
  "rank": "★★★★★",            // 可选
  "tag": "985 / 公共管理 A+"   // 可选
}
```

**硬要求**: `name` 字段必须有,渲染器靠 `name` 取首字做 monogram。

---

## 5. `salary` 嵌套结构

```json
{
  "应届生": {"p25": 8, "p50": 12, "p75": 18, "yoy": 5},
  "3 年经验": {"p25": 15, "p50": 22, "p75": 35, "yoy": 8},
  "5 年经验": {"p25": 25, "p50": 40, "p75": 60, "yoy": 3}
}
```

**键名**: 任意字符串,常用 `应届生` / `3 年经验` / `5 年经验`
**数值**: 整数万元
**yoy**: 同比百分比,可正可负可零

---

## 6. `employment_direction` 列表元素

```json
{"name": "互联网/产品经理", "pct": 28}
```

**规则**:
- 至少 3 项
- `pct` 整数 0-100
- `name` 简练 (≤12 字)

---

## 7. `alumni_quotes` 列表元素

```json
{
  "year": "2020",
  "current": "字节跳动 · 数据分析师",
  "quote": "保险精算的核心是数据敏感度...",
  "source": "中央财经大学 2020 届"        // 可选
}
```

**注意**: 渲染器会按 `current` 去重。

---

## 8. `xuanke_req_list` 列表元素

```json
{"name": "物理", "pct": 95}
```

**说明**: 高考 3+1+2 模式下各科要求占比,`pct` 0-100。

---

## 9. 选填字段 (强烈推荐) (6 个)

| 字段 | 类型 | 说明 |
|------|------|------|
| `overview_v2` | object | 速览 3 卡 (lede/what/fit/pitfalls) |
| `curriculum_note` | string | 课程区上方的引导文字 |
| `top_companies` | list[object] (≥3) | 头部雇主 |
| `deep_study` | object | 深造方向 (key→pct int) |
| `hero_quote_sig` | string | hero_quote 的署名 |
| `what_you_learn` / `who_fits` / `pitfalls` | string | 旧版速览,fallback |

---

## 10. `overview_v2` 嵌套 (新版速览)

```json
{
  "lede": "一句话总结",
  "what": {
    "foundations": ["基础课 1", "基础课 2", ...],
    "directions": [{"name": "方向 1", "desc": "..."}, ...],
    "skills": ["能力 1", "能力 2", ...],
    "bonus": "加分项"
  },
  "fit": {
    "yes": ["适合 1", "适合 2", ...],
    "no": ["不适合 1", ...]
  },
  "pitfalls": [{"myth": "误区", "reality": "真相"}, ...]
}
```

**数组最小值**:
- `foundations` ≥3
- `directions` ≥3
- `skills` ≥3
- `yes` ≥3, `no` ≥2
- `pitfalls` ≥2

---

## 11. 风格特例 (按 style 增减)

| style | 必加 | 选加 |
|-------|------|------|
| `cs` | - | `github_metric` (object) |
| `medicine` | `top_companies` 可省 | - |
| 5 年制 (duration_years=5) | - | `timeline` (list of `{year, stage, income}`) |
| `law` | - | 可加 `bar_exam_rate` (string) |

---

## 12. 反幻觉护栏 (LLM 必读)

**`summary` / `alumni_quotes.quote` / `top_schools` 字段严禁编造**:

- 排名/薪资/校友身份: 标"基于 2024 公开数据估算"或"未知"
- 校友访谈: 标"基于 X 平台公开访谈综合"
- 学科评估等级 (A+ / A / B+): 必须有出处,否则标"评估中"

校验器会扫:
- 标"清华"在前 3 但无引用源 → 标 warning
- 校友身份含"阿里 P8"等高帽 → 标 warning
- 薪资异常 (应届 > 50 万) → 标 warning

---

## 13. 完整最小示例

```json
{
  "slug": "insurance",
  "title": "保险学",
  "category": "经济学 · 金融学类",
  "style": "finance",
  "degree": "经济学学士",
  "duration_years": 4,
  "tags": ["精算师", "稳定", "考证", "央企", "CFA", "小众"],
  "difficulty": "★★★★☆",
  "updated_at": "2026-06",
  "data_source": "Web 搜索综合 (中央财经大学/西南财经 培养方案 + 中国银保监会 + 5 位精算校友访谈)",
  "summary": "保险学是金融学的'精算 + 风控'分支, 对接银行/保险/资管三大去向。精算师是 7 门 SOA 考试 + 多年工作年限, 难但天花板高 (资深精算年薪 80-150 万)。",
  "hero_quote": "精算不是算术, 是概率 + 财务 + 监管的三角",
  "hero_quote_sig": "—— 中央财经大学保险学院",
  "curriculum": {
    "公共必修": [{"name": "高等数学 A", "credit": "5"}],
    "通用专业核心": [{"name": "保险学原理", "credit": "4"}],
    "5 校特色选修": [{"name": "精算实务", "credit": "3"}]
  },
  "top_schools": [
    {"name": "中央财经大学", "rank": "★★★★★", "tag": "211 / 保险学 A+"},
    {"name": "西南财经大学", "rank": "★★★★★", "tag": "211 / 保险学 A"},
    {"name": "对外经济贸易大学", "rank": "★★★★☆", "tag": "211 / 保险学 A-"}
  ],
  "salary": {
    "应届生": {"p25": 10, "p50": 15, "p75": 22, "yoy": 3},
    "3 年经验": {"p25": 18, "p50": 28, "p75": 40, "yoy": 5},
    "5 年经验": {"p25": 30, "p50": 50, "p75": 80, "yoy": 2}
  },
  "employment_direction": [
    {"name": "保险/精算", "pct": 35},
    {"name": "银行/资管", "pct": 25},
    {"name": "互联网金融", "pct": 20}
  ],
  "alumni_quotes": [
    {"year": "2019", "current": "中国人寿 · 精算师", "quote": "...", "source": "中央财经大学 2019 届"}
  ],
  "xuanke_req_list": [
    {"name": "物理", "pct": 60},
    {"name": "不限", "pct": 40}
  ]
}
```
