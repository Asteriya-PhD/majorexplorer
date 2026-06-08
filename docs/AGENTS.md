# AGENTS.md — 高考志愿推荐 MVP · AI Agent 入口

> 这是给 AI agent 看的项目入口。如果你是人类开发者,先看 `README.md`;想做架构/数据/决策/进度调研,看 `docs/` 下的其他 4 份。

## 项目一句话

**湖北高考志愿推荐 MVP v0.2.0** — 输入考生**全省位次 + 选科 + 体检 + 偏好**,输出**96 个志愿**(冲 32 / 稳 32 / 保 32)。

- 模式: 3+1+2(湖北/广东/江苏等 9 省)+ 3+3(京/沪/津/浙/鲁/琼)两种新高考
- 省份: 湖北(全)/ 广东 + 江苏(锚点级)
- 核心算法: 位次驱动 + 等效分跨年 + Gaussian CDF 估概率
- **OCR: 走 MinerU SDK (`pip install mineru`), Flash 模式免 token**. 详见 `docs/ARCHITECTURE.md` § 11. ⭐⭐⭐架构级规定, 不要加 PaddleOCR/Tesseract/EasyOCR.

## 代码地图

```
gaokao-hubei-mvp/
├── core/                       # 7 个纯函数算法模块 (无 IO, 无网络)
│   ├── data_loader.py          # CSV 加载 (lru_cache),多省自动发现
│   ├── rank_utils.py           # score ↔ rank 双向
│   ├── equivalent.py           # 跨年等效分 / 历年位次查询
│   ├── filter.py               # 3 层硬过滤:选科 + 体检 + 学费 (含 3+3 模式)
│   ├── probability.py          # Gaussian CDF 估录取概率 + 冲稳保分类
│   ├── strategy.py             # 张雪峰式策略:GOAL_PROFESSION_BONUS + FAMILY_PENALTY
│   └── recommender.py          # 主流程 recommend() 入口
│
├── api/                        # FastAPI 层
│   ├── main.py                 # 7 个 endpoint (见 ARCHITECTURE.md)
│   └── pdf_report.py           # reportlab PDF 报告
│
├── scripts/                    # 数据获取 (独立 CLI, 写到 data/)
│   ├── fetch_real_data.py      # 一分一段表 fetcher (eol.cn / 555edu)
│   ├── fetch_admission.py      # 2025 投档表 fetcher (gk100)
│   ├── fetch_555edu_hubei.py   # 555edu 逐校抓湖北 (135 校)
│   ├── fetch_555edu_2023.py    # 555edu 2023 专项
│   ├── fetch_555edu_guangdong_jiangsu.py  # 555edu 广东/江苏
│   ├── fetch_dxsbb_6261.py     # dxsbb 一本 (985/211/重点)
│   ├── fetch_2024_2023_anchors.py  # 硬编码锚点 + 2025 合成
│   ├── merge_real_2024.py      # 多源合并去重 → 标准 CSV
│   └── generate_sample_rank_gd_js.py  # 广东/江苏 rank table 生成
│
├── tests/                      # 4 文件,20 用例,1 个用 pytest.mark.parametrize
│   ├── test_recommender.py     # 9 个,核心算法回归
│   ├── test_backtest.py        # 3 个场景回测
│   ├── test_backtest_real.py   # 4 个锚点校验
│   └── test_backtest_real_admission.py  # 4 个 (2024/2025 物理/历史) 真实投档表回测
│
├── data/
│   ├── {province}_rank_{subject}_{year}.csv           # 一分一段表
│   ├── {province}_admission_{subject}_{year}.csv      # 投档表 (标准,推荐用)
│   ├── {province}_admission_*_real_{555edu|dxsbb6261}.csv  # 中间产物
│   ├── _cache/555edu/                                  # 抓取的 HTML 缓存 (gitignored)
│   ├── _cache/dxsbb_imgs/                              # 抓取的 PNG 缓存 (gitignored)
│   ├── _logs/                                          # 抓取日志 + 备份 (gitignored)
│   ├── generate_sample_data.py                         # 旧湖北样本生成器
│   └── README.md                                       # CSV schema
│
├── cli_demo.py                 # 命令行演示入口
├── skills/zhangxuefeng_perspective.md  # 策略思想 (4/5 思维模型 + 6/8 启发式)
├── docs/                       # ← 你在这里
├── README.md                   # 人类入口
└── requirements.txt
```

## 常用命令

```bash
# 跑推荐 (CLI)
python3 cli_demo.py --rank 5000 --subject 历史 --xuanke 历+政+地 --year 2024 --city 武汉 北京

# 起 API + 前端
uvicorn api.main:app --reload
open frontend/index.html

# 测试 (20/20)
python3 -m pytest tests/ -v

# 重新抓数据
python3 scripts/fetch_real_data.py --year 2025 --subject 物理
python3 scripts/fetch_555edu_hubei.py  # 全 135 校, ~10-15 分钟
python3 scripts/merge_real_2024.py     # 合并 → hubei_admission_*.csv

# OCR (PDF / PNG / JPG 通用, MinerU SDK, 免 token)
pip install mineru
python3 -c "from mineru import MinerU; c = MinerU(token=None); print(c.flash_extract('input.png', is_ocr=True, enable_table=True).markdown[:200])"
```

## 约定 (写代码前必读)

### 数据 schema 硬编码
- 改 CSV 列名 = 改算法。`core/recommender.recommend` 假设的列: `year, subject, school_name, school_type, group_id, xuanke_req, xuanke_subjects, plan_count, min_score, min_rank, tuition_yuan, city, is_special`
- `group_id` 必须**跨年一致**(算法用 `(school_name, group_id)` 在 `equivalent.historical_min_rank` 取近 3 年历史位次)
- `xuanke_subjects` 格式 `"物理|化学"`(首选|再选;再选是"或"关系);空 = 不限

### 选科模式
- 3+1+2 (湖北/广东/江苏/湖南/河北/重庆/辽宁/福建/海南): 12 种,首选必匹配 + 再选任一
- 3+3 (京/沪/津/浙/鲁/琼): 20 种,`get_all_xuanke_options_3_plus_3()`
- `get_xuanke_mode(province)` 自动选;`filter_schools(..., province=)` 必须传

### 数据真实 vs 合成
详见 `docs/DATA.md` 真实性矩阵。简版:
- ✅ 2025 湖北 物理 205 / 历史 103 (全真,gk100)
- ✅ 2024 湖北 物理 254 / 历史 140 (3 源合并: 555edu + dxsbb6261 + 锚点)
- ⚠️ 2023 湖北 物理 242 / 历史 128 (555edu 43 校 + 锚点)
- ⚠️ 广东/江苏 2024 物理/历史 ~70-80 (555edu 锚点级)

## 做什么 / 不做什么

### DO ✅
- 改 data 时先跑对应 fetcher,不动 schema
- 改核心算法时: 先看 `core/recommender.recommend` 主流程;再追 `core/probability.estimate_admission_probability`;再追 `core/filter.match_xuanke`
- 加新省: 4 步 (校准 rank table → 抓 admission → 验 schema → 跑回测)— 见 `docs/DATA.md`
- 加 endpoint: 在 `api/main.py` 现有 7 个后面加,保持 FastAPI 风格
- 跑回测: `tests/test_backtest_real_admission.py` 用 `pytest.mark.parametrize` 跑 (物理/历史 × 2024/2025)

### DON'T ❌
- **不要把 `strategy_bonus` 加进 sort key** (已 ADR-005 锁定)— 详见 `docs/DECISIONS.md`
- 不要改 CSV 列名
- 不要 hardcode 院校名(用 `SCHOOL_TYPE` / `CITY_BY_SCHOOL` 推断或 fetcher 抓)
- 不要在 `core/` 加网络/文件 IO(纯函数层)
- 不要动 fetcher 缓存目录 `_cache/` 直接读(用 fetcher 的 `fetch()` 函数)
- 不要把"个人意见"写进 `core/strategy.py` 的 `GOAL_PROFESSION_BONUS` 注释(那是"张雪峰式"数据)

## 关键入口 (最常被改)

下表 line number 由 codegraph 索引 (`.codegraph/codegraph.db`,gitignored) 验证 — 改代码后跑 `codegraph index` 刷新。

| 文件 | 入口 | 行 | 改前必读 |
|---|---|---:|---|
| `core/recommender.py` | `recommend()` | L63 | `docs/DECISIONS.md` ADR-005 (sort key) |
| `core/recommender.py` | `RecommendRequest` | L16 | 17 字段 Pydantic schema |
| `core/recommender.py` | `_build_advice` / `_build_strategy_note` | L205 / L223 | advisory text 生成 |
| `core/probability.py` | `estimate_admission_probability()` | L23 | ADR-004 (Gaussian CDF 公式) |
| `core/filter.py` | `match_xuanke()` / `get_xuanke_mode()` | L60 / L27 | 3+1+2 vs 3+3 模式 |
| `core/filter.py` | `_match_xuanke_3_plus_1_plus_2` / `_match_xuanke_3_plus_3` | L82 / L104 | 模式实现细节 |
| `core/filter.py` | `filter_schools()` | L146 | 3 层硬过滤主入口 |
| `core/strategy.py` | `strategy_bonus()` | L93 | 仅 advisory,不入排序 |
| `core/equivalent.py` | `historical_min_rank()` | L42 | 3 年位次查询(被 probability 调用) |
| `core/data_loader.py` | `load_admission_table` / `load_rank_table` | L50 / L31 | `@lru_cache(64)`,改 schema 失效 |
| `api/main.py` | 7 endpoint (见 ARCHITECTURE.md §4) | L57~L179 | `version="0.2.0"` |
| `data/{prov}_admission_*.csv` | 真实数据 | — | 改 schema = 改算法 |
| `scripts/fetch_555edu_hubei.py` | 4-schema 通用解析器 | — | 555edu 改版时优先改这里 |

## 用 codegraph 反查代码 (本项目已启用)

`.codegraph/` 已 gitignore(索引 DB 不入库),但本地有 938KB 索引,26 文件 364 节点 584 边。

```bash
# 1 次性: 新机器上重建索引
cd /Users/zhewenliu/Claude/gaokao-hubei-mvp
codegraph init && codegraph index   # ~250ms,生成 .codegraph/codegraph.db

# 改了 ≥5 文件后,刷一下
codegraph index
```

**MCP 工具用法** (已在 Claude Code 配 `mcp__codegraph__*`):

| 任务 | 工具 | 例子 |
|---|---|---|
| "X 函数怎么工作" | `codegraph_context` | `task="how does recommend sort volunteers"` |
| "X 到 Y 的调用链" | `codegraph_trace` | `from=recommend to=load_admission_table` |
| "X 的源码" | `codegraph_node` | `symbol=estimate_admission_probability` |
| "X 调谁" / "谁调 X" | `codegraph_callees` / `codegraph_callers` | `symbol=match_xuanke` |
| "改 X 会影响啥" | `codegraph_impact` | `symbol=recommend` |
| "路由清单" | (在 codegraph_context 输出末尾) | `task="api routes"` |
| "列文件" | `codegraph_files` | `path=core/` |
| "状态" | `codegraph_status` | (无需参数) |

**反漂移约定**:
- 改代码后,任何 doc (含本文件) 里的行号引用以 codegraph 索引为准
- ADR 里的 `file:line` 引用若漂移,改 ADR 并 commit (而非静默)

## 文档地图 (其他 4 份)

- **架构** → `docs/ARCHITECTURE.md` (系统流 + 模块边界 + API 表面)
- **进度** → `docs/PROGRESS.md` (状态 + 数据真实性矩阵 + 已知缺口)
- **决策** → `docs/DECISIONS.md` (8 个 ADR)
- **数据** → `docs/DATA.md` (数据源 + schema + 新省 onboarding)
