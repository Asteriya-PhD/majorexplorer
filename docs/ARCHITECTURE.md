# ARCHITECTURE.md — 系统架构

> 给架构师/资深 agent 看的全景。开发日常问题看 `AGENTS.md`;决策动机看 `DECISIONS.md`;数据细节看 `DATA.md`。

## 1. 系统流图(文字版)

```
                          ┌──────────────────────────┐
                          │     User Input            │
                          │ rank + 选科 + 体检 + 偏好 │
                          │ + 省份/年份/科类          │
                          └──────────┬───────────────┘
                                     │ RecommendRequest (Pydantic)
                                     ▼
            ┌────────────────────────────────────────────────┐
            │  core/recommender.recommend(req)               │
            │  ──────────────────────────────────────────     │
            │  1. load_admission_table(prov, subj, year)     │
            │  2. filter_schools (3 层硬过滤)                │
            │       ├─ 选科 (match_xuanke, mode=自动)        │
            │       ├─ 体检 (check_medical_constraints)      │
            │       └─ 学费 (<= max_tuition)                 │
            │  3. 排除 avoid_schools / avoid_special          │
            │  4. 算 _city_score (偏好城市加权)              │
            │  5. estimate_admission_probability (per row)   │
            │       └─ historical_min_rank (3 年)            │
            │  6. 算 _layer_score (985/211/普通/专科)        │
            │  7. sort by _sort_key                          │
            │     = city·100k + layer·1万 + prob·10          │
            │  8. 冲/稳/保 top 32/32/32                       │
            │  9. _build_advice + _build_strategy_note        │
            │ 10. 拼 RecommendResponse                        │
            └─────────────┬──────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
   ┌─────────────────┐         ┌─────────────────┐
   │  CLI 入口       │         │  FastAPI 入口   │
   │  cli_demo.py    │         │  api/main.py    │
   │  (argparse)     │         │  7 endpoints    │
   └─────────────────┘         └────────┬────────┘
                                        │
                          ┌─────────────┴──────────┐
                          ▼                        ▼
                  ┌──────────────┐         ┌──────────────┐
                  │ JSON resp   │         │ PDF resp     │
                  │ POST        │         │ POST         │
                  │ /api/recommend│       │ /api/recommend│
                  │              │         │ /pdf         │
                  └──────────────┘         └──────────────┘
```

## 2. 模块依赖图

**codegraph 索引**: 26 文件 364 节点 584 边,7 routes。本节所有行号已通过 `codegraph_node` / `grep` 验证。

```
CLI / API
    │
    ├── cli_demo.py:main (L51) ─────────► RecommendRequest (core/recommender.py:L16)
    │                                         │
    │                                         ▼
    │                                   recommend() (L63) ◄── api_recommend (L131), api_recommend_pdf (L143)
    │                                         │
    │                              ┌──────────┼──────────┐
    │                              ▼          ▼          ▼
    │                       load_admission_  filter_    estimate_admission_
    │                       table            schools    probability
    │                       (data_loader     (filter    (probability
    │                        L50)            L146)      L23)
    │                              │           │            │
    │                              │           │            ▼
    │                              │           │      historical_min_rank
    │                              │           │      (equivalent L42)
    │                              │           │            │
    │                              │           │            ▼
    │                              │           │      load_admission_table (recursive,
    │                              │           │      跨年查 2023-2025)
    │                              │           │
    │                              │           ▼
    │                              │     match_xuanke (filter L60)
    │                              │           │
    │                              │           ├── get_xuanke_mode (L27) → "3+1+2" / "3+3"
    │                              │           ├── _match_xuanke_3_plus_1_plus_2 (L82)  ◄── 湖北/广东/江苏
    │                              │           └── _match_xuanke_3_plus_3 (L104)         ◄── 京/沪/津/浙/鲁/琼
    │                              │           │
    │                              │           ▼
    │                              │     check_medical_constraints (filter L132)
    │                              │           │
    │                              │           ▼
    │                              │     [max_tuition <= req.max_tuition]
    │                              │
    │                              └──► ──► RecommendResponse
    │                                          │
    │                                          ├── _build_advice (L205)
    │                                          └── _build_strategy_note (L223)
    │                                              │
    │                                              └──► strategy_bonus (strategy L93) [advisory, NOT in sort key]

scripts/ ──fetchers──► data/*.csv  (独立 CLI, 写产物)
                            │
                            └───────────► load_admission_table (cached) ◄─── api_recommend / recommend
```

**关键依赖原则**:
- `core/` 全是纯函数,无 IO,无网络
- `scripts/` 可写 data,可读 _cache
- `api/` 只读 data (via data_loader)
- `tests/` 只通过 `cli_demo` / `recommend` 测试,不直接 mock 内部
- **`strategy_bonus` 不被 `recommend` 调用进入排序** (ADR-005)— 只 advisory text

## 3. 数据流

```
外部源                   抓取脚本                  产物
──────                   ────────                  ────
gk100.com ──────────────► fetch_admission.py ────► hubei_admission_物理_2025.csv
eol.cn ─────────────────► fetch_real_data.py ─────► hubei_rank_*.csv
555edu (135 校) ────────► fetch_555edu_hubei.py ──► hubei_admission_*_2024_real_555edu.csv
dxsbb.com/6261 ─────────► fetch_dxsbb_6261.py ────► hubei_admission_*_2024_real_dxsbb6261.csv
硬编码锚点 ─────────────► fetch_2024_2023_anchors.py (in-script dict)
555edu (2023 校) ───────► fetch_555edu_2023.py ───► hubei_admission_*_2023_real_555edu.csv
555edu (GD/JS 校) ──────► fetch_555edu_guangdong_jiangsu.py ──► {guangdong,jiangsu}_admission_*.csv
锚点 + 插值 ────────────► generate_sample_rank_gd_js.py ─────► {guangdong,jiangsu}_rank_*.csv

合并 ──────────────────► merge_real_2024.py ─────► hubei_admission_*_2024.csv (canonical)

                                  │
                                  ▼
                          core/data_loader
                                  │
                                  ▼
                        core/recommender.recommend
                                  │
                                  ▼
                          RecommendResponse / PDF
```

## 4. API 表面 (7 endpoints)

**codegraph 路由清单** (来自 `codegraph_context` 输出):

| Method | Path | Handler | 位置 |
|---|---|---|---|
| POST | `/api/score-to-rank` | `api_score_to_rank` | `api/main.py:57` |
| POST | `/api/rank-to-score` | `api_rank_to_score` | `api/main.py:80` |
| POST | `/api/equivalent` | `api_equivalent` | `api/main.py:103` |
| GET | `/api/meta` | `api_meta` | `api/main.py:116` |
| POST | `/api/recommend` | `api_recommend` | `api/main.py:131` |
| POST | `/api/recommend/pdf` | `api_recommend_pdf` | `api/main.py:143` |
| GET | `/` | `serve_index` | `api/main.py:179` (仅 frontend/index.html 存在时 mount) |

**请求/响应形状** (从 `codegraph_node` 验证):

| Endpoint | Request | Response |
|---|---|---|
| `score-to-rank` | `ScoreToRankRequest{province, score, subject, year}` | `ScoreToRankResponse{province, score, rank}` |
| `rank-to-score` | `RankToScoreRequest{province, rank, subject, year}` | `RankToScoreResponse{province, rank, score}` |
| `equivalent` | `EquivalentRequest{province, rank, subject}` | `EquivalentResponse{province, rank, subject, equivalent_scores: {year: score}}` (year=2025 硬编码) |
| `meta` | query `?province=` | `{provinces, subjects, years, xuanke_options, current_province}` |
| `recommend` | `RecommendRequest` (17 字段 Pydantic) | `RecommendResponse.model_dump()` (404 with fetch-script hint on FileNotFoundError) |
| `recommend/pdf` | `RecommendRequest` | `application/pdf` (Content-Disposition: `volunteer_report_{prov}_{subj}_{year}.pdf`) |

**CORS**: `allow_origins=["*"]` (dev only — production 应锁定)
**Version**: 硬编码 `version="0.2.0"` in `api/main.py`

**CORS**: `allow_origins=["*"]` (dev only — production should lock down)
**Version**: 硬编码 `version="0.2.0"` in `api/main.py`
**Filename ASCII mapping**: PDF 文件名用 `prov.replace(" ", "_")` 限制 ASCII

## 5. 多省份 / 多模式架构

```
CLI / API 请求
    province="hubei"  →  get_xuanke_mode() → "3+1+2"
                        load_admission_table("hubei", "历史", 2024) → CSV
                        filter_schools(df, xuanke, ti_eye, max_tuition, province="hubei")
                        3+1+2 逻辑: 首选匹配 + 再选任一

    province="beijing" →  get_xuanke_mode() → "3+3"
                        load_admission_table("beijing", "物理", 2024) → CSV (无则 404)
                        filter_schools(df, xuanke, ti_eye, max_tuition, province="beijing")
                        3+3 逻辑: 选考 3 门,专业组要求 "X,Y" (任一) 或 "X+Y" (都需)
```

**省份支持矩阵**:

| 省份 | 模式 | 数据状态 | 备注 |
|---|---|---|---|
| 湖北 | 3+1+2 | ✅ 全 (2023-2025 物理+历史) | 生产 |
| 广东 | 3+1+2 | ⚠️ 2024 锚点级 (~70 行) | |
| 江苏 | 3+1+2 | ⚠️ 2024 锚点级 (~80 行) | |
| 北京 | 3+3 | ❌ 无数据,代码 ready | |
| 上海 | 3+3 | ❌ 无数据,代码 ready | |
| 天津 | 3+3 | ❌ 无数据,代码 ready | |
| 浙江 | 3+3 | ❌ 无数据,代码 ready | |
| 山东 | 3+3 | ❌ 无数据,代码 ready | |
| 海南 | 3+3 | ❌ 无数据,代码 ready | |

加新省 = 加 `{prov}_rank_*.csv` + `{prov}_admission_*.csv` + 校准 fetcher (见 `docs/DATA.md` 4 步 onboarding)。

## 6. 扩展点

### 加新 endpoint
- 在 `api/main.py` 现有 7 个后面加
- 保持 FastAPI 风格 (`@app.post` / `@app.get`)
- `RecommendRequest` 已 17 字段,新增字段加 Pydantic 校验

### 加新模式 (除 3+1+2 / 3+3)
- 在 `core/filter.py` 加 `PROVINCES_NEWMODE` 集合
- 加 `match_xuanke_newmode()` 和 `_match_xuanke_newmode()`
- `filter_schools` 加分支
- 扩展点已存在,无需改 `recommender` / `data_loader`

### 加新省
- 4 步 (见 `docs/DATA.md` 新省 onboarding)

### 加新数据源
- 写新 fetcher 到 `scripts/`
- 若 schema 不同,加新解析器分支到 `merge_real_2024.py` 的 `normalize()`
- 若新源权威更高,调整 `merge_real_2024.py` 的 `_priority` dict

## 7. 排序公式 (核心)

```python
_sort_key = (
    _city_score * 100_000    # 城市偏好 (权重最大,但只 0/1/2)
  + _layer_score * 10_000    # 学校层次 (主导,985=4, 211=3, 普通=2, 专科=1)
  + probability * 10         # 概率 (微调,不影响层次)
)
```

**关键**: `strategy_bonus` **不参与排序** (ADR-005)。它只影响 `VolunteerItem.strategy_note` 文字。

## 8. 概率模型 (核心)

**codegraph 验证**: 函数 `estimate_admission_probability` 在 `core/probability.py:23`。**实际公式**(从 codegraph 拿到的源码,不是文档里的"应该是什么"):

```python
def estimate_admission_probability(student_rank, school_name, group_id, province, subject):
    hist = historical_min_rank(school_name, group_id, province, subject)
    if not hist:
        return {probability: 0.5, category: "稳", warning: "无历史数据"}

    ranks = list(hist.values())
    min_rank = float(min(ranks))                          # ⚠️ 用 min 不是 median (高考"边缘"语义)
    median_rank = float(np.median(ranks))
    std_rank = float(np.std(ranks)) if len(ranks) > 1 else 0

    # 数据 <3 年时 std=0 → 25% min_rank 兜底
    if std_rank < min_rank * 0.05:
        std_rank = min_rank * 0.25

    z = (student_rank - min_rank) / std_rank
    P = 0.5 * (1 + erf((-z + 0.7) / sqrt(2)))              # Gaussian CDF +0.7 偏置
    category = "冲" if P<0.30 else "稳" if P<0.70 else "保"
    return {probability, category, historical_ranks, median_rank, std_rank}
```

**实测概率分布** (来自代码注释):
- 1.0x (student=min_rank) → 0.76 (保)
- 1.1x → 0.62 (稳)
- 1.2x → 0.46 (稳)
- 1.5x → 0.10 (冲)

详见 ADR-004。

## 9. 已知性能/资源约束

- `load_admission_table` 用 `@lru_cache(maxsize=64)` — 适合 CLI/单次 API,但并发高时可能 OOM
- `pdf_report` 一次性加载 96 行 + 渲染,A4 单文件,毫秒级
- fetcher 走 `data/_cache/` GBK 编码,典型 135 校 = 2564 个 HTML 文件 (~200 MB)

## 10. 部署形态

| 形态 | 现状 |
|---|---|
| 本地 CLI (`cli_demo.py`) | ✅ 工作 |
| 本地 FastAPI + 静态前端 | ✅ 工作 (`uvicorn` + `frontend/`) |
| Docker | ❌ 无 Dockerfile |
| 生产部署 (gunicorn/nginx) | ❌ 未配置 |
| 定时数据更新 cron | ✅ `scripts/install_cron_6_25.sh` (6/25 高考出分日) |
