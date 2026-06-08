---
name: canghe-major-explorer
description: Generates major-explorer dashboards for high-school students choosing a college major. Two modes — (1) curated: 50 hand-crafted dashboards for popular majors (CS, finance, medicine, law, education...) used as SEO magnets on homepage; (2) long-tail: real-time web search → template render for the other ~700 majors. Use when user says "XX 专业怎么样", "学 XX 有前途吗", "CS/金融/医学/法学/师范 专业介绍", "专业就业", "专业薪资", "专业课程".
---

# canghe-major-explorer

高考专业探索 skill — 让考生/家长**自己**找到感兴趣的专业方向, 再调志愿 recommender。

## 双模式

| 模式 | 数据源 | 适用 | 输出 |
|---|---|---|---|
| **精品** (50 热门) | 人工精编 JSON (`data/curated/{slug}.json`) | CS / 金融 / 临床医学 / 法学 / 师范 / ... | 静态 HTML, 放首页, SEO 收录 |
| **长尾** (~700) | 5-query 并行 web search → 模板渲染 | 量子信息 / 宠物医疗 / 水族科学 / ... | 临时 HTML, 5-15s 出 |

**视觉一致**: 1 套模板, 5 套设计风格 (CS 黑客/金融黑金/医学临床/法学经典/师范暖橙), 精品和长尾**看不出来**。

## 触发条件

- "XX 专业怎么样 / 学什么 / 课程"
- "XX 专业 就业 / 薪资 / 头部公司"
- "CS/计算机/金融/医学/法学/师范 介绍"
- "高考选专业"

## 10 个 Tab (统一 schema)

1. **速览** — 是什么 / 学几年 / 学位 / 难度自评
2. **主要课程** — 公共课 / 专业核心 / 方向选修
3. **院校分布** — 8-12 所代表校, 含学科评估 + 特色
4. **头部公司** — 6-10 家代表企业, 含 tier + 招聘量 + 校招薪资
5. **薪资箱型** — 应届 / 1-3 年 / 3-5 年 P25/P50/P75
6. **就业方向** — 占比饼图 (5-7 类)
7. **深造路径** — 保研 / 考研 / 出国 / 就业 比例
8. **学长学姐说** — 3-5 条 unique quote
9. **选科要求** — 物理 / 化学 / 生物 组合覆盖率
10. **关联志愿** — CTA: "基于位次推荐这些校+组" → 调 recommender

## 5 套设计 (style 参数)

```python
STYLES = {
  "cs":        "Dark + JetBrains Mono + 终端 Bento + #22C55E 跑码绿",
  "finance":   "Cream + Bodoni Moda/Jost + 黑金 Liquid Glass + #A16207 金",
  "medicine":  "Light teal + Figtree/Noto Sans + 临床极简 + #0F766E 青",
  "law":       "Sepia + EB Garamond/Lato + 瑞士网格 + #D97706 琥珀",
  "education": "Warm cream + Playfair/Inter + 暖橙学术 + #9A3412 砖 + #F59E0B 银杏",
}
```

## Script Directory

| Script | 用途 |
|---|---|
| `scripts/generate_dashboard.py` | **核心**: 1 函数 `generate_dashboard(data, style, output_path)`, 精品/长尾共用 |
| `scripts/web_search.py` | 长尾: 5 query 并行 (TODO, P0 仅占位) |

## 调用

```bash
# 精品 (离线, < 1s)
python3 skills/canghe-major-explorer/scripts/generate_dashboard.py \
  --data skills/canghe-major-explorer/data/curated/computer-science.json \
  --style cs \
  --output skills/canghe-major-explorer/data/curated/computer-science.html

# 长尾 (实时, 5-15s, 需先实现 web_search.py)
python3 skills/canghe-major-explorer/scripts/generate_dashboard.py \
  --query "量子信息工程" \
  --style cs \
  --output /tmp/quantum-info.html
```

## 关联项目资产

| 资产 | 复用方式 |
|---|---|
| `core/recommender.py` | Tab 10 "关联志愿" 调它, 输入 (rank, score, school_pool) |
| `data/{province}_admission_*.csv` | Tab 3 院校 + Tab 10 关联志愿 校池来源 |
| `data/{province}_rank_*.csv` | Tab 10 "你的位次" 锚点 |

## 跟 canghe-tianyancha 的关系

仿照 (skill pattern: data → template → HTML), 但**双模式混合**:
- tianyancha 100% 依赖 Kimi search
- major-explorer **50 精品 + 长尾 search** (内容营销 + AI 工具)

## 写作规范

详见 [references/curation-checklist.md](references/curation-checklist.md) — 每个精品 2-3h 人工编辑的标尺。
