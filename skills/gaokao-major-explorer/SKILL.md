---
name: gaokao-major-explorer
description: Generates major-explorer dashboards for high-school students choosing a college major. Two modes — (1) curated: 50 hand-crafted dashboards for popular majors (CS, finance, medicine, law, education...) used as SEO magnets on homepage; (2) long-tail: real-time web search → template render for the other ~700 majors. Use when user says "XX 专业怎么样", "学 XX 有前途吗", "CS/金融/医学/法学/师范 专业介绍", "专业就业", "专业薪资", "专业课程", "帮我做个XX专业的分析", "写个XX专业的介绍页面".
---

# gaokao-major-explorer

高考专业方向调研 skill — 让考生/家长通过精品 HTML 专题页**自己**找到感兴趣的专业方向。

## 触发条件

- "XX 专业怎么样 / 学什么 / 课程 / 就业 / 薪资"
- "帮我做个 XX 专业的分析"
- "写个 XX 专业的介绍页面"
- "了解 XX 专业" / "XX 专业有前途吗"
- "CS/计算机/金融/医学/法学/师范 专业介绍"
- "高考选专业 / 什么专业好"

## 两种模式

| 模式 | 数据源 | 耗时 | 触发条件 |
|---|---|---|---|
| **精品** | 人工精编 JSON (`data/curated/{slug}.json`) | < 1s | 已有 JSON 的 5 个专业直接渲染 |
| **长尾** | 5-query web search → 填 JSON → 渲染 | 5-15s | 其他 ~700 专业, 从搜索实录填 schema 再渲染 |

**视觉一致**: 1 套 JSON schema, 5 套设计风格 (CS 黑客/金融黑金/医学临床/法学卷宗/师范暖橙), 精品和长尾看不出区别。

---

## Quick Start — 一条命令出 HTML

```bash
python3 skills/gaokao-major-explorer/scripts/generate_dashboard.py \
  --data skills/gaokao-major-explorer/data/curated/education.json \
  --style education \
  --output skills/gaokao-major-explorer/data/curated/education.html
```

可选 `--style`: `cs` | `eng` | `finance` | `medicine` | `law` | `education` | `sci` | `humanities` | `administration`

---

## JSON Schema 完整参考

> 精品/长尾填同一份 schema。**标 `*` 的为必填字段**, 其余可选或用默认值。

### 顶层字段

```
{
  "slug": "string*",            // URL slug, e.g. "psychology"
  "title": "string*",           // 专业全称, e.g. "心理学"
  "category": "string*",        // 学科门类 · 专业类, e.g. "理学 · 心理学类"
  "style": "string*",           // cs|eng|finance|medicine|law|education|sci|humanities|administration
  "degree": "string*",          // 学位, e.g. "理学学士"
  "duration_years": 4,          // 学制年数
  "tags": ["string", ...],      // 4-6 个标签, 第一个是 primary
  "difficulty": "string",       // ★★☆☆☆ ~ ★★★★★
  "updated_at": "string",       // "YYYY-MM" 格式
  "data_source": "string",      // 数据来源描述
  "summary": "string*",         // 1 句话定位 (显示在 Hero)
  "what_you_learn": "string",   // 学什么 (1-3 段)
  "who_fits": "string",         // 适合谁 (1-2 段)
  "pitfalls": "string"          // 避坑指南 (❌ emoji 列点)
}
```

### curriculum (课程)

```
"curriculum": {
  "公共必修 (所有院校都开)": [
    {"name": "课程名", "credit": "学分数字"}
  ],
  "通用专业核心 (≈ 80% 院校覆盖)": [...],
  "5 校特色选修 (按方向分流)": [...]
}
```

- 课程名必填, credit 字符串
- 额外 key 可加 (如 `"CS 特色课"`)
- `curriculum_note` (可选顶层字段): 显示在课程 section 的 lede

### top_schools (院校)

```
"top_schools": [
  {"name": "校名*", "rank": "A+|A|A-|B+|B*", "tag": "一句特色"}
]
```

- 8-12 所, **按 name 去重**
- 学科评估 rank 优先, 双一流次之, 软科再次
- tag 必须含城市 (见下方数据规范)

### top_companies (头部公司)

```
"top_companies": [
  {
    "name": "公司名*",
    "tier": "S|A|B",
    "headcount": "★|★★|★★★|★★★★|★★★★★",
    "salary": "一句话薪资描述",
    "sparkline": [4, 4, 3, 3, 3]  // 近 5 年招聘量趋势 (1-5 整数)
  }
]
```

- 6-12 家
- S = 顶级薪资+大量校招, A = 稳定校招, B = 大量招/中等门槛

### salary (薪资)

```
"salary": {
  "阶段名 (如 应届/0-2年)": {
    "p25": 数字, "p50": 数字, "p75": 数字,  // 单位: 万/年
    "yoy": 数字  // 同比增长 %, 正/负/0
  }
}
```

- 2-4 个阶段

### employment_direction (就业方向)

```
"employment_direction": [
  {"name": "方向名", "pct": 数字}
]
```

- 5-7 项, **百分比合计 100%**

### deep_study (深造路径)

```
"deep_study": {
  "路径名": 数字  // 百分比
}
```

- 3-5 条路径
- 合计不超 100%

### alumni_quotes (学长学姐说)

```
"alumni_quotes": [
  {
    "year": "2014 届",     // 必须 "YYYY 届" 格式
    "current": "当前职位/公司",
    "source": "来源描述",   // e.g. "校友访谈 @北京"
    "quote": "引文内容 (60字以内)"
  }
]
```

- 3-5 条, **有夸有劝退有中立** (不能全是夸)
- quote 文本内引号用 「」

### xuanke_req_list (选科要求)

```
"xuanke_req_list": [
  {"name": "选科组合", "pct": 数字}
]
```

- 覆盖率数据, 基于 2024 阳光高考

### 可选扩展字段

```
"github_metric": {          // 仅 cs style
  "desc": "描述",
  "p1000_star": "12%",
  "acm_award": "8%",
  "oss_contrib": "30%"
},
"timeline": [               // 仅 5 年制 (medicine)
  {"year": "第1年", "stage": "阶段名", "income": "收入/状态"}
],
"curriculum_note": "自定义课程前提说明"
```

---

## 8 套设计风格

```
STYLES = {
  "cs":             "Dark + JetBrains Mono + 终端 Bento + #22C55E 跑码绿",                    # 11 (含智能科技)
  "eng":            "浅米工程 (CAD 蓝图) + Inter Condensed + 图纸标题栏 + 零件清单表",       # 10 (含工业设计/土木)
  "medicine":       "Light teal + IBM Plex Sans + 手术仪表 + ECG + #0C4A6E",                  # 6
  "education":      "Warm cream + Playfair/Inter + 暖橙学术 + #9A3412 砖 + #F59E0B 银杏",   # 5
  "finance":        "Cream + Bodoni Moda/Jost + 烫金 editorial + #A16207",                   # 5
  "sci":            "米色学术 (Nature 风) + Lora/EB Garamond + 期刊刊头 + 公式 + #C73E1D 红",# 4
  "humanities":     "深棕墨 + 米白宣纸 + 古籍线装 (翻开的善本 + 朱砂引首章 + 校勘式 stats)", # 4
  "administration": "政府蓝 + 米白 + 国发文件 + 红头印章 (公文体 + 案卷目录卡 + 骑缝章)",  # 4
  "law":            "Sepia + EB Garamond/Lato + 羊皮卷宗 + #78350F 琥珀",                      # 1
  "agri":           "嫩芽白 + 橄榄叶绿 + 林奈式植物图鉴 (清新绿配色, 减少赭石) + #E6B422 谷穗金", # 5
  "arts":           "炭黑 + 米白画布 + 调色板 + 包豪斯抽象画 (Studio of Making 主题) + #DC2626 朱红", # 5
}
```

### 风格-学科映射表 (8 主题)

| 学科/气质 | style | 理由 |
|---|---|---|
| 编程 / CS / 数据 / AI / 智能 | `cs` | 终端黑客 |
| 金融 / 商科 / 经济 / 管理 (会计/工商/国贸) | `finance` | 烫金 editorial |
| 法学 / 政治 | `law` | 羊皮卷宗 |
| 师范 / 教育 / 心理 / 应心 / 文学 / 英语 / 新闻 | `education` | 暖橙学术 + 书本 |
| 医学 / 药学 / 护理 / 公卫 / 麻醉 / 口腔 / 中医 | `medicine` | 手术仪表 + ECG |
| **数学 / 物理 / 化学 / 大气 / 生物** | **`sci`** | **米色学术 + 公式 + 元素周期表课程** |
| **机械 / 材料 / 化工 / 微电子 / 集成电路 / 车辆 / 航天 / 食品 / 土木 / 工业设计** | **`eng`** | **浅米工程 + 蓝图 + 零件清单表** |
| **冷门文科 (汉语言/历史/哲学/考古)** | **`humanities`** | **深棕墨 + 米白宣纸 + 古籍线装 (翻开的善本 + 朱砂引首章 + 校勘式 stats + 壹貳參肆目录)** |
| **商业文员 (财管/行管/信管/图书馆)** | **`administration`** | **政府蓝 + 米白 + 国发文件 + 红头印章 (公文体 + 案卷目录卡 + 骑缝章)** |

---

## 数据填写规范 (5 条铁律)

### 1. 引号全用 「」
中文学术内容**禁止** ASCII 引号 `''` `""`。
- ✅ 「编程是载体, 数学是底层」
- ❌ "编程是载体, 数学是底层"

### 2. 学校 tag 必须含城市
名字里没城市的学校, tag 前置「城市 · 」。
- 清华 → tag: `"北京 · 工科之首"`
- 复旦 → tag: `"上海 · 综合强校"`
- 华中科技大学 → tag: `"工医双雄"` (名字已有"华中", 可不加)

### 3. alumni_quotes.year 必须是「YYYY 届」格式
模板不追加任何文字。错误格式: `"2014"` / `"2014级"` → 正确: `"2014 届"`

### 4. top_schools 按 name 去重, 无重复
渲染引擎有 `_dedup_by_name()`, 但 JSON 源数据也应去重。

### 5. 百分比字段合理
- `employment_direction` 累计 ≈ 100%
- `deep_study` 累计 ≤ 100%
- `xuanke_req_list` 累计 ≈ 100%

---

## 精品模式工作流

已有 JSON 的专业直接渲染:

```
1. 确认 JSON 在 `data/curated/{slug}.json`
2. 选 style (查映射表)
3. 跑 generate_dashboard.py
4. (可选) Playwright 截图验证
```

## 长尾模式工作流

搜索新专业:

```
1. 确定 style (查映射表)
2. 5 query 并行 web search:
   a. "{major} 主要课程 培养方案"
   b. "{major} 就业方向 头部公司 薪资"
   c. "{major} 学科评估 哪些学校开设"
   d. "{major} 选科要求 高考 招生"
   e. "{major} 学长学姐 知乎 体验"
3. 从搜索结果提取数据 → 填入 JSON
4. 跑 generate_dashboard.py
5. 另存 JSON 到 data/curated/{slug}.json (可选, 用于缓存)
```

### 数据提取优先级
| 字段 | 一级源 | 二级源 | 三级源 |
|---|---|---|---|
| 课程 | 高校官网培养方案 | 知乎/学长 | 学职平台 |
| 院校分布 | 教育部学科评估 (第四轮) | 双一流名单 | 软科 |
| 头部公司 | 校招官方公告 | 知乎/脉脉 | BOSS |
| 薪资 | 麦可思 (年度) | 校招 offer 墙 | 行业报告 |
| 选科 | 阳光高考 | 高校招生章程 | — |
| 校友 quote | 知乎 100+ 赞 | 校友访谈 | 小红书/微博 |

---

## 质量自检清单 (精品 7 条)

- [ ] ≥ 4 条校友 quote, 有夸有劝退 (不能全夸)
- [ ] ≥ 1 个独特数据可视化 (临床有时轴, CS 有 GitHub metric)
- [ ] 选科要求覆盖率 100% 准确 (来自阳光高考)
- [ ] 薪资标了截止日期 + 采样源 (不写"年薪 30-50 万")
- [ ] 头部公司 ≥ 6 家, 含 S/A/B 层级
- [ ] ≥ 3 个易踩坑 (劝退清单)
- [ ] 1 句话 Hero 定位

### 反例 (绝对不写)
- ❌ "本专业就业前景广阔, 薪资待遇优厚" (废话)
- ❌ "适合所有对该专业感兴趣的同学" (没说啥)
- ❌ 校友 quote 全是夸的
- ❌ 薪资只给"30-50 万" (缺 P25/P50/P75)
- ❌ 头部公司没层级 (字节和不知名公司并列)

---

## 8 个 Root Cause Warning

> 这些 bug 曾导致渲染崩溃/数据丢失, **编辑 CSS 或 JSON 前必读**。

1. **CSS 括号必须配对** — 编辑 v4_medicine.py / v4_styles.py 时, 每个 `{` 必须配 `}`。括号不配对会吞掉后续大段 CSS。用 `grep -n '\{[^}]*$'` 自查
2. **Python 字符串中 CSS Unicode 转义** — 写 `"\\201C"` 或直接用 `「`, 不要单反斜杠
3. **模板不要重复拼接字段** — JSON 中 `year` 已是 `"2014 届"`, 模板不要再加「届」字
4. **JSON 层去重** — `_dedup_by_name()` 已进渲染, 但数据录入时就该去重
5. **长中文文本 nowrap** — stat-value 默认 nowrap, 长内容要 `!important` 覆盖
6. **学校名换行** — 用 `soft_break_name()` 在「大学/学院/医学院」后插 `<wbr>`
7. **`.path-card:nth-child(3n)` 无 translateY** — 已删错位偏移, 别加回来
8. **CSS Unicode 引号不回退** — v4_styles.py 5 套引号已统一用 `「」`, 不要回退成 `\201C` / `\201D` 转义

---

## 脚本目录

```
scripts/
├── generate_dashboard.py    # 核心引擎 + entry (精品/长尾共用)
├── v4_styles.py             # 4 套极致: cs/finance/law/education
├── v4_medicine.py           # 医学独立: Mayo Clinic 级
data/curated/
├── manifest.json            # 已收录专业索引
├── {slug}.json              # 数据文件
├── {slug}.html              # 渲染输出
references/
├── data-sources.md          # 数据源 + 合规指南
├── curation-checklist.md    # 精品写作规范
```

### 调用关系
```
generate_dashboard.py
  ├─ style == "medicine"  → v4_medicine.render_v4_medicine(data)
  └─ style in [cs, eng, finance, law, education, sci, humanities, administration] → v4_styles.render_v4(data, style)
```

---

## 5 个成品参考 (按质量倒序)

| 专业 | 文件 | 大小 | 特色 |
|---|---|---|---|
| 师范教育 | `education.html` | 60K | 双页跨页扉页, 最优雅 |
| 临床医学 | `clinical-medicine.html` | 60K | vitals 手术仪表, ECG, 数据最全 |
| 计算机科学 | `computer-science.html` | 57K | 终端面板, GitHub metric |
| 金融学 | `finance.html` | 56K | 烫金 letterhead |
| 法学 | `law.html` | 56K | 羊皮卷宗 docket |

---

## 关联项目资产

| 资产 | 复用方式 |
|---|---|
| `core/recommender.py` | Tab "关联志愿" 调它, 输入 (rank, score, school_pool) |
| `data/{province}_admission_*.csv` | 院校 + 关联志愿 校池来源 |
| `data/{province}_rank_*.csv` | 位次锚点 |

---

## 示例: 一句话触发

> 用户: "帮我做个心理学专业的分析页面"

AI 执行:
1. 确定 style = `education` (心理学偏教育/社科)
2. 5 query web search 心理学课程/就业/院校/选科/校友
3. 从搜索结果提取 → 填入 JSON
4. `python3 scripts/generate_dashboard.py --data /tmp/psychology.json --style education --output /tmp/psychology.html`
5. 返回 HTML 路径 + 关键数据摘要