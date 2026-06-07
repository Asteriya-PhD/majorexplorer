# DATA.md — 数据源 / Schema / 真实性 / Sourcing 策略

> 高考数据是这项目的命门。**改 schema = 改算法**,**改数据源 = 改 fetcher**,**改真实性 = 改 PROGRESS.md 矩阵**。
> 决策动机看 `DECISIONS.md`,架构看 `ARCHITECTURE.md`。

## 1. 数据真实性总览

| 省份 | 科目 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| 湖北 | 物理 | — | ⚠️ 242 | ✅ 254 | ✅ 205 |
| 湖北 | 历史 | — | ⚠️ 128 | ✅ 140 | ✅ 103 |
| 广东 | 物理 | — | — | ⚠️ 70 | — |
| 广东 | 历史 | — | — | ⚠️ 64 | — |
| 江苏 | 物理 | — | — | ⚠️ 79 | — |
| 江苏 | 历史 | — | — | ⚠️ 74 | — |
| 京/沪/津/浙/鲁/琼 | 物理/历史 | — | — | ❌ | — |

**一分一段表**:
- 湖北 2023/2024/2025 ✅ 全真
- 广东/江苏 2024 ⚠️ 公开锚点插值
- 其他 ❌ 无

**图例**: ✅ 全真可生产 / ⚠️ 锚点级 (普通本科靠 555edu 抓,可能不全) / ❌ 无数据 / — 未抓

## 2. CSV Schema 详解

### 2a. 一分一段表
**文件**: `{province}_rank_{subject}_{year}.csv`
**列**: `score, rank, count` (3 列)
- `score`: int 150-700
- `rank`: int 累计位次 (1=第一名)
- `count`: int 本分数段人数

**重要**: 部分行用范围字符串 `"695-750"` 解析为下界 695,见 `core/data_loader._normalize_rank_table`。

**代码读法**: `core/data_loader.load_rank_table(province, subject, year)` 返回排序后的 DataFrame。

### 2b. 院校专业组投档表 (canonical)
**文件**: `{province}_admission_{subject}_{year}.csv` (无 `_real_*` 后缀,这是 `merge_real_2024.py` 的最终产物)
**列** (13 列,顺序固定):

| 列 | 类型 | 说明 |
|---|---|---|
| `year` | int | 年份 |
| `subject` | str | 物理 / 历史 |
| `school_name` | str | 院校全称 |
| `school_type` | str | 985 / 211 / 普通 / 专科 |
| `group_id` | str | 专业组编号(同校每年编号一致!) |
| `xuanke_req` | str | 选科要求(展示用,如 "物理+化学") |
| `xuanke_subjects` | str | 选科要求(机读, `\|` 分隔;空=不限) |
| `plan_count` | int | 招生计划人数 |
| `min_score` | int | 当年最低投档分 |
| `min_rank` | int | 当年最低投档位次 |
| `tuition_yuan` | int | 学费(元/年) |
| `city` | str | 所在城市 |
| `is_special` | str | 是 / 否(中外合作/国家专项等) |

**读法**: `core/data_loader.load_admission_table(province, subject, year)`

### 2c. 中间产物 (不直接用,但保留供溯源)
- `{prov}_admission_*_real_555edu.csv` — 555edu 抓的原始 9-10 列
- `{prov}_admission_*_real_dxsbb6261.csv` — dxsbb 抓的 7 列

## 3. 数据源层级 (从高到低权威性)

| 源 | 类型 | 覆盖 | 权威 | 抓取脚本 |
|---|---|---|---|---|
| 湖北教育考试院 (hbea.edu.cn) | 一分一段 / 投档表 | 湖北全 | ⭐⭐⭐⭐⭐ | 未直接抓 (页面 JavaScript 渲染) |
| eol.cn / gxzsxxw.com.cn | 一分一段表 | 6+ 省 | ⭐⭐⭐⭐ | `fetch_real_data.py` |
| gk100.com | 锚点 + 投档位次对应 | 1-3 万名 | ⭐⭐⭐ | `fetch_admission.py` |
| 555edu.com | 逐校 录取分数线 | 125 校湖北 + 169 GD + 170 JS | ⭐⭐⭐ | `fetch_555edu_*.py` |
| dxsbb.com/news/6261 | 一本 表 | ~140 行/省 | ⭐⭐⭐ | `fetch_dxsbb_6261.py` |
| 今日头条/大鹏老师 文章 | 985/211 锚点 | 几十条 | ⭐⭐ | 硬编码到 `fetch_2024_2023_anchors.py` |
| 自主招生在线 (zizzs.com) | 985 完整 (2023) | ~50 行 | ⭐⭐ | 缓存 `data/_cache/zizzs_*.html` 但未自动化抓 |
| 大学生必备网 (dxsbb.com) | 完整 投档表 (2024) | ~280 行/省 | ⭐⭐ | `data/_cache/dxsbb_imgs/*.png` OCR (tesseract) |

## 4. 新省 onboarding checklist (4 步)

加一个新省 (比如 湖南) 需要 4 步,顺序不可乱:

### Step 1: 校准一分一段表
- 抓 2024 一分一段表 (eol.cn → 湖南)
- 命名: `hunan_rank_物理_2024.csv` / `hunan_rank_历史_2024.csv`
- 验证: 700 分附近位次与公开锚点偏差 <2% (`tests/test_backtest_real.py:test_known_*_anchors` 自动化)

### Step 2: 抓投档表
- 优先 eol.cn / hbea 等价源
- 备选 555edu per-school (代码已支持 GD/JS 模式,可复用)
- 命名: `hunan_admission_{物理,历史}_2024.csv`
- 验证: 985 学校 (清华/北大) 投档线与公开锚点匹配

### Step 3: 验证 schema
- 跑 `python3 cli_demo.py --province hunan --rank 10000 --subject 物理 --xuanke 物+化+生 --year 2024`
- 跑 `python3 -m pytest tests/ -v` (参数化 4 个 backtest 应仍过)

### Step 4: 加省份到 filter 集合
- 若新省是 3+1+2: 加到 `core/filter.py:PROVINCES_3_PLUS_1_PLUS_2`
- 若新省是 3+3: 加到 `core/filter.py:PROVINCES_3_PLUS_3`
- `data_loader.get_all_xuanke_options(province)` 自动返回对应选科

### 失败常见原因
- 一分一段表没分首选/再选 → 需双表 (e.g. 北京 物理/历史 不分)
- 选科要求字段名不同 (e.g. 北京 用 "选考 物理,化学" vs 湖北 用 "物理+化学")
- 院校代号 / 专业组代码规则不同 (e.g. 北京 5 位 vs 湖北 7 位 "A14108")

## 5. fetcher 脚本清单 (10 个)

| 脚本 | 用途 | 数据源 | 产物 |
|---|---|---|---|
| `fetch_real_data.py` | 一分一段表 (cron 6/25) | eol.cn, hbea, 555edu | `*_rank_*.csv` |
| `fetch_admission.py` | 2025 投档表 (gk100 单表) | gk100, zizzs, eol | `*_admission_*_2025.csv` |
| `fetch_555edu_hubei.py` | 555edu 湖北逐校 (135 校) | 555edu.com/hubei/ | `*_real_555edu.csv` |
| `fetch_555edu_2023.py` | 555edu 2023 专项 (4-schema 解析) | 555edu | `*_real_555edu.csv` |
| `fetch_555edu_guangdong_jiangsu.py` | 555edu GD/JS 逐校 (169+170 校) | 555edu.com/{guangdong,jiangsu}/ | `*_real_555edu.csv` |
| `fetch_dxsbb_6261.py` | 一本 表 (140 行/省) | dxsbb.com/news/6261.html | `*_real_dxsbb6261.csv` |
| `fetch_2024_2023_anchors.py` | 硬编码锚点 + 2025 合成 | 公开锚点 | (in-script dict → merge input) |
| `merge_real_2024.py` | 多源合并去重 | 上面所有 `_real_*` | canonical `*_admission_*_2024.csv` |
| `generate_sample_rank_gd_js.py` | GD/JS 一分一段 锚点插值 | 公开锚点 (700/600/580/525/400) | `guangdong/jiangsu_rank_*.csv` |
| `generate_sample_data.py` | 旧湖北样本生成器 (合成) | 全部合成 | `hubei_*_*.csv` (历史产物) |

**全部 fetcher 都写 `data/` 子目录,缓存到 `data/_cache/`,日志到 `data/_logs/`。** gitignore 已包含。

## 6. 数据质量门

| 门 | 工具 | 阈值 |
|---|---|---|
| 锚点偏差 | `tests/test_backtest_real.py:test_known_*_anchors` | < 2% |
| 真实投档表回测 | `tests/test_backtest_real_admission.py` (参数化 4 个) | 冲/稳/保 分类正确率 > 50% |
| Schema 完整 | `merge_real_2024.py:normalize()` | 13 列全有 |
| group_id 跨年稳定 | `equivalent.historical_min_rank` | (school, group) 跨年 match |
| 一分一段表 单调 | `_normalize_rank_table` | rank 严格递增 |

**自动回归**: `python3 -m pytest tests/ -v` 跑全 20 个用例,约 90 秒。

## 7. 未解决的数据缺口

| 缺口 | 后果 | 解决路径 |
|---|---|---|
| 2022 及以前数据 | 历史回测无 3 年基线 | 抓 hbea 历年 PDF (需 OCR) |
| 招生计划年际变化 | 同校缩招 5% vs 20% 风险未量化 | 加 `plan_count` 历史序列 + 缩放比字段 |
| 高职高专与本科合并过滤 | 推 32 个"保"档 误推 高职 | merge 时按 `batch` 过滤 (`merge_real_2024.py` 已加) |
| 2024 广东/江苏 无 985 完整 | 推荐冲档少 | 抓 555edu 985 文章 (代码已支持) |
| eol.cn 完整投档表 (含专业组) | 555edu 广东/江苏 是 7-col 简版 | 找 eol.cn 完整版 或 dxsbb 各省列表 |
| 物理/历史 之外 (新高考有些省份有"第三类") | 不支持 | 加 3+3 模式变体 (北京已有) |
| LLM 解释层需要的数据 | 推荐报告无个性化解读 | 候选专业 → 就业/考研 数据 (要另外抓) |

## 8. 数据相关 FAQ

### Q: 为什么不用 gk100 单表覆盖 2024?
A: gk100 的 2024 数据只覆盖 1-3 万名,普通本科 4-10 万名 没有。555edu per-school 覆盖 135 校 × 平均 5 组 = 600+ 行,远多于 gk100。

### Q: 为什么不用 hbea.edu.cn 官方 PDF/Excel?
A: hbea 页面用 JavaScript 渲染,直接 fetch 拿不到内容,需要 headless browser (e.g. Playwright) 或 PDF 下载。已下载 3 张 dxsbb 完整表 (147537 2024 历史) PNG 到 `_cache/dxsbb_imgs/`,但 OCR 精度有限 (chi_sim PSM 4 ~80%)。hbea PDF 优先做。

### Q: 为什么湖北 2023 是 ⚠️ 而不是 ✅?
A: 555edu 抓了 43 校,还有 90+ 校没抓到 (主要是民办/独立学院/职业),所以"非完整"。生产前需 OCR dxsbb 2023 完整表或补抓 555edu 90 校。

### Q: 广东/江苏 rank table 是 锚点插值 准确吗?
A: 偏差约 ±5-10 名/10000 名,比完全无数据好得多。生产前要 eol.cn 抓完整表。

### Q: group_id 为什么重要?
A: `equivalent.historical_min_rank(school, group_id, prov, subj)` 用 `(school, group_id)` 查近 3 年位次 — 若 group_id 跨年不一致,历史查询失败,推荐回退到 0.5 概率。

### Q: data_source 字段怎么用?
A: `merge_real_2024.py` 的 canonical CSV 加了 `data_source` 列 ("555edu 逐校" / "dxsbb 6261 一本" / "真实锚点" / "合成(基于2025+波动)"),UI 可以过滤只看真实数据。

## 9. 数据相关 memory 指针 (人类经验沉淀)

- `gaokao-admission-table-source-survey-2026-06-06` — 3 源对湖北真实投档表的对比
- `gaokao-no-hubei-aggregate-school-list-page` — 湖北所有招生院校的'列表页'不存在
- `gaokao-fake-admission-tables-mask-real-hitrate` — 假 admission table 掩盖真实命中率
- `gaokao-self-corrected-on-unverified-2026-06-06` — 招生计划缩放比之前未量化已承认
- `gaokao-anchor-validation-tuple-bug-fix-2026-06-06` — 锚点 dict 用 tuple 比较 bug
- `gaokao-hubei-mvp-final-calibration-params-2026-06-` — v0.1 最终校准参数
- `gaokao-hubei-mvp-v01-runs-end-to-end-2026-06-06` — v0.1 端到端运行
- `gaokao-sample-data-fake-ranks-clearly-labeled` — 样本数据假位次明示

(以上是 session-memory MCP 写入,每次新 session 可调用 `mcp__session-memory__memory-recall --query "gaokao data"` 加载)
