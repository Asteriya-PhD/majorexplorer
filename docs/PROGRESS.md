# PROGRESS.md — 进度 / 状态 / 已知缺口

> 时间戳: 2026-06-07. 这是快照文档,每次里程碑更新一次。

## 1. 当前状态:v0.2.0 (Production-ready for 湖北)

**项目年龄**: ~2 天密集工作 (2026-06-06 ~ 2026-06-07)
**总代码量**: ~7 核心模块 + 10 fetcher 脚本 + 4 测试 + 7 endpoint
**测试**: 20/20 通过 (`pytest tests/`)
**数据 CSV**: 29 个, ~8,273 行
**Git**: 3 commits (全部 2026-06-07)

### Commit 时间线
```
712db05  feat: 广东/江苏 MVP 真实数据
90deed7  feat: 2023 物理/历史 真实数据 + 广东/江苏 适配
243a576  feat: 2024 历史/物理 真实完整版 + 555edu/dxsbb 抓取
```

## 2. 模块完成度

| 模块 | 完成度 | 状态 |
|---|---|---|
| 核心算法 (recommender / probability / filter / strategy / equivalent / rank_utils) | 100% | ✅ 生产可用 |
| 多模式选科 (3+1+2 / 3+3) | 100% | ✅ 湖北/广东/江苏 3+1+2;京/沪/津/浙/鲁/琼 3+3 |
| API 层 (7 endpoints + PDF) | 100% | ✅ 本地可跑 |
| 前端 (单页 HTML) | 80% | ✅ 基本工作,UI 不够 polish |
| 数据抓取 (10 fetcher) | 100% | ✅ 湖北 2025 全真, 2024 合并, 2023 部分真 |
| 测试 (4 文件) | 70% | ✅ 核心 + 回测;3+3 mode / api endpoints / strategy 数值未测 |
| 文档 (5 份) | 100% | ✅ AGENTS/ARCHITECTURE/PROGRESS/DECISIONS/DATA |
| 部署 (Docker / gunicorn / nginx) | 0% | ❌ 仅本地 |
| 监控 / 日志聚合 | 0% | ❌ 仅 stderr |

## 3. 数据真实性矩阵 (按省/科/年)

| 省份 | 科类 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| 湖北 | 物理 | — | ⚠️ 242 (555edu 43 校 + 锚点) | ✅ 254 (3 源合并) | ✅ 205 (gk100 全) |
| 湖北 | 历史 | — | ⚠️ 128 (555edu 43 校 + 锚点) | ✅ 140 (3 源合并) | ✅ 103 (gk100 全) |
| 广东 | 物理 | — | — | ⚠️ 70 (555edu 锚点级) | — |
| 广东 | 历史 | — | — | ⚠️ 64 (555edu 锚点级) | — |
| 江苏 | 物理 | — | — | ⚠️ 79 (555edu 锚点级) | — |
| 江苏 | 历史 | — | — | ⚠️ 74 (555edu 锚点级) | — |
| 京/沪/津/浙/鲁/琼 | 物理/历史 | — | — | ❌ 无 | — |

**图例**: ✅ 全真(可生产) / ⚠️ 部分真(锚点级,普通本科靠 555edu 抓) / ❌ 无数据 / — 未抓

**一分一段表**:
- 湖北 2023/2024/2025 ✅ 全真 (gxzsxxw / eol.cn / gk100)
- 广东/江苏 2024 ⚠️ 公开锚点插值 (700/600/580/525/400)
- 其他 ❌ 无

## 4. 已完成的关键工作 (近 2 天)

### Day 1 (2026-06-06)
- 初始化: 9 大模块 + CLI + API + 4 测试
- 湖北 2023-2025 样本数据生成器
- `core/recommender.recommend` 主流程 + Gaussian CDF 概率
- `core/filter` 3+1+2 选科过滤
- 张雪峰式 strategy (6 actionable strategies)
- 9 个核心测试通过

### Day 2 (2026-06-07)
- **commit 243a576** — 2024 历史/物理 真实完整版
  - 555edu 逐校抓取器(4 schema 通用解析)
  - dxsbb 6261 一本表 fetcher
  - 3 源合并 (锚点 + dxsbb6261 + 555edu)
  - 254 行物理 / 140 行历史真实本科
- **commit 90deed7** — 2023 物理/历史 真实数据 + 广东/江苏
  - 2023 fetcher 4-schema 支持(含 score→rank 反查)
  - 242/128 行 2023
  - 广东/江苏 一分一段表生成器 (锚点插值)
- **commit 712db05** — 广东/江苏 MVP
  - 555edu 广东/江苏 fetcher (169/170 校)
  - 70/64 (GD) + 79/74 (JS) 行
- **filter.py** 扩展 3+3 模式 (京/沪/津/浙/鲁/琼) 20 种选科 + 选考匹配
- **data_loader.get_all_xuanke_options** 按省份自动选模式
- **recommender** group_id 强转 str 修 pydantic ValidationError
- 20/20 测试通过(含参数化 4 个真实投档表回测)
- **本次 init** — 5 份 docs + README 指针

## 5. 已知缺口 (按优先级)

### 阻塞生产
- ❌ **广东/江苏 数据只锚点级** (64-80 行,远不够 96 志愿)— 需 eol.cn / 考试院 PDF
- ❌ **2022 及以前数据无** — 历史回测至少要 3 年才有意义
- ❌ **招生计划年际变化未量化** — 同校缩招/扩招 5% vs 20% 风险不同,目前当静态

### 功能性
- ❌ **LLM 解释层未做** — 推荐目前只给"985 高校"等短语,无 LLM 解释"为什么"
- ❌ **体检/选科级联过滤 UI 未做** — 选科和体检是 cli 参数,前端 UI 未接
- ❌ **3+3 mode 未真测** — 代码 ready 但无真实 3+3 数据,只有单元测试
- ❌ **2024 广东/江苏** 用 555edu 广东 7-col schema, group_id 简化为 "01" (ADR-007)

### 质量
- ❌ **`core/recommender._sort_key` 不含 `strategy_bonus`** — 已 ADR-005 锁定,但需文档化
- ❌ **`api/pdf_report.py` 省份硬编码 3 个** — 其他省份 PDF 文件名 fallback
- ❌ **`core/filter` 对 555edu 简版 schema 假设 2025 列** — 实际旧版 CSV 可能缺 school_type/xuanke_subjects 等
- ❌ **3 个测试用 `if __name__ == "__main__"` script-style,只 1 个用 pytest** — 不一致

### 部署
- ❌ 无 Dockerfile / gunicorn / nginx 配置
- ❌ 无日志聚合 (只有 stderr)
- ❌ 无监控/告警
- ❌ 无 CI/CD (`.github/workflows/` 不存在)

## 6. 下一里程碑候选

| 候选 | 工作量 | 价值 |
|---|---|---|
| OCR dxsbb 完整 2024 历史 PNG → ~280 行真实 | 0.5 天 | 2024 历史从 140 → ~250 行,接近"完整版" |
| eol.cn 抓 广东/江苏 2024 一分一段 + 投档表 | 1 天 | 锚点级 → 完整级 |
| Docker 化 + gunicorn | 0.5 天 | 可部署 |
| 体检/选科级联过滤前端 UI | 1 天 | UX |
| LLM 解释层 (用 MiniMax / 内部 LLM) | 1-2 天 | 差异化 |
| 历史回测 (用 2024 真实投档表回测 2023 推荐) | 1 天 | 命中率验证 |
| `pdf_report` 省份硬编码修复 | 0.1 天 | 清理 |
| 3+3 mode 真实数据 + 测试 | 1 天 | 真正支持 6 省 |

## 7. 引用

- 决策动机: `docs/DECISIONS.md`
- 数据细节: `docs/DATA.md`
- Agent 入口: `docs/AGENTS.md`
- 架构: `docs/ARCHITECTURE.md`
- README: `/README.md`
- 原始已知限制: `/README.md` 末尾的 7 条
