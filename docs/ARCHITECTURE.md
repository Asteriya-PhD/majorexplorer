# ARCHITECTURE.md — 系统架构

> 给架构师/资深 agent 看的全景。2026-06-22 Phase 3 精简后重写 (FastAPI 栈已删, 详见 DECISIONS.md ADR-021)。
>
> 历史版本描述的 `core/` + `api/` FastAPI 96 志愿推荐 MVP 栈已于 2026-06-22 删除。当前产品形态是**专业 dashboard + LLM 按需合成**, 推荐算法在客户端 JS 跑。

## 1. 系统流图 (文字版)

```
                          ┌──────────────────────────┐
                          │     User (高三生/家长)    │
                          │  PC / Mobile (UA sniff)   │
                          └──────────┬───────────────┘
                                     │ HTTPS
                                     ▼
                ┌──────────────────────────────────────────┐
                │  Cloudflare Pages (海外, 优选 IP 30-100ms) │
                │  ──────────────────────────────────────  │
                │  functions/_middleware.ts                │
                │    └─ UA mobile → 302 /m/                │
                │                                          │
                │  public/ (499 PC HTML + 488 Mobile HTML) │
                │    ├─ index.html (主页, SSR 13 学科门类)  │
                │    ├─ {slug}.html (专业 dashboard)       │
                │    ├─ m/majors/{slug}.html (Mobile)      │
                │    ├─ css/ js/ data/                     │
                │    │   ├─ recommender.js (客户端推荐)     │
                │    │   ├─ major-search.js (搜索)         │
                │    │   ├─ wishlist-store.js (心愿单)     │
                │    │   └─ manifest.json (475 majors)     │
                │    ├─ sitemap.xml (485 URL)              │
                │    └─ 404.html (真静态 404)              │
                │                                          │
                │  functions/api/ (Pages Functions, TS)    │
                │    ├─ synth/generate.ts (入队 D1)        │
                │    ├─ synth/status.ts (查 D1)            │
                │    ├─ synth/[[slug]].ts (查 done)        │
                │    └─ report.js (反馈 → GH Issue)        │
                └─────────────┬────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
       ┌──────────────────┐         ┌──────────────────┐
       │  Cloudflare D1   │         │  GitHub Action   │
       │  (synth-jobs)    │         │  cron */1        │
       │  migrations/     │         │  synth.yml       │
       │  0001_init.sql   │         │  ↓               │
       └──────────────────┘         │  synth_queue_    │
                ▲                   │  worker.py       │
                │                   │  ↓               │
                └───────────────────┤  scf/synth/      │
                                    │  main.py:worker  │
                                    │  (7 步 pipeline) │
                                    │  ↓               │
                                    │  git push → CF   │
                                    │  Pages 自动部署  │
                                    └──────────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  DeepSeek API    │
                                    │  (LLM 合成)      │
                                    └──────────────────┘
```

## 2. 模块依赖图

```
浏览器 (用户)
    │
    ├── public/js/recommender.js ─► public/data/manifest.json (475 majors)
    │                                  │
    │                                  └─► public/data/curated/ (已删, Phase 2)
    │
    ├── public/js/major-search.js ─► public/data/manifest.json + 同义词表
    │
    └── (未收录专业) → fetch /api/synth/generate
                              │
                              ▼
                    functions/api/synth/generate.ts
                              │
                              ▼
                    D1 synth_jobs (INSERT queued)
                              │
                              ▼ (GH Action cron */1 pull)
                    scripts/synth_queue_worker.py
                              │
                              ▼
                    scf/synth/main.py:worker(run_id, title, slug, style)
                              │
                              ├─ scf/synth/validator.py (validate_is_major)
                              ├─ scf/synth/search.py (search_multi, 4 路 web search)
                              ├─ scf/synth/prompts.py (route_style + synthesize prompt)
                              ├─ scf/synth/llm.py (DeepSeek client)
                              ├─ scf/synth/validator.py (score_quality)
                              ├─ scf/synth/render_bridge.py (subprocess generate_dashboard.py)
                              └─ scf/synth/manifest_ops.py (append manifest)
                              │
                              ▼
                    public/{slug}.html + public/m/majors/{slug}.html
                    + public/data/manifest.json (append)
                              │
                              ▼
                    git add + commit + push (GH Action token)
                              │
                              ▼
                    CF Pages 监到 push → 30s 自动重新部署
```

**关键依赖原则**:
- `public/` 全是静态资源, 客户端 JS 跑推荐算法 (无后端调用)
- `functions/` 只做入队 + 状态查询 + 反馈, 不跑 LLM
- `scf/synth/` 是 Python 模块, 被 GH Action 调, 不部署到 SCF (ADR-022)
- `scripts/` 是工具脚本, build/inject/audit/synth 分类清晰
- `data/` 是 canonical CSV (投档表 + 一分一段表), `*_real_*` 中间产物已归档

## 3. 数据流

```
外部源                   抓取脚本 (已归档)              产物 (canonical)
─────                    ────────────────              ─────────────
gk100.com ──────────────► fetch_admission.py ────────► hubei_admission_物理_2025.csv (已归档脚本)
eol.cn ─────────────────► fetch_real_data.py ────────► hubei_rank_*.csv
555edu (135 校) ────────► fetch_555edu_hubei.py ───► hubei_admission_*_2024.csv
dxsbb.com/6261 ─────────► fetch_dxsbb_6261.py ─────► (合并到 canonical)
硬编码锚点 ─────────────► fetch_2024_2023_anchors.py
555edu (GD/JS 校) ──────► fetch_555edu_guangdong_jiangsu.py

合并 ──────────────────► merge_real_2024.py ─────► {province}_admission_{subject}_{year}.csv (canonical)
                                                       (中间产物 *_real_*.csv 已归档到 data/_archive/)

                                   │
                                   ▼
                           public/data/manifest.json (475 majors)
                           public/data/colleges.json + school_*.json
                                   │
                                   ▼
                         public/js/recommender.js (客户端跑)
                         public/js/major-search.js
                                   │
                                   ▼
                         用户看到的 dashboard + 推荐 + 搜索
```

**LLM 合成数据流** (未收录专业):
```
用户搜 "治安学" → manifest 无 → fetch /api/synth/generate
  → D1 queued → GH Action pull → scf/synth 7 步
  → public/gongzhi-xue.html + manifest append → git push → CF 部署
```

## 4. API 表面 (Cloudflare Pages Functions)

| Method | Path | Handler | 位置 |
|---|---|---|---|
| POST | `/api/synth/generate` | `onRequest` | `functions/api/synth/generate.ts` |
| GET | `/api/synth/status` | `onRequest` | `functions/api/synth/status.ts` |
| GET | `/api/synth/{slug}` | `onRequest` | `functions/api/synth/[[slug]].ts` |
| POST | `/api/report` | `onRequest` | `functions/api/report.js` |
| * | `/*` (UA mobile) | `onRequest` | `functions/_middleware.ts` (302 到 /m/) |

**请求/响应形状**:

| Endpoint | Request | Response |
|---|---|---|
| `synth/generate` | `{title, slug?, style?, email?}` | `{run_id, status_url}` (D1 INSERT queued) |
| `synth/status` | `?run_id=xxx` | `{run_id, status, step, progress, title, slug, output_url?, error?}` |
| `synth/{slug}` | `?slug=xxx` | `{run_id, status, output_url?}` (查 done) |
| `report` | `{type, name?, text?, source}` | `{ok, issue_url, number}` (GH Issue) |

**D1 schema** (`migrations/0001_init.sql`):
```sql
CREATE TABLE synth_jobs (
  run_id TEXT PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'queued',  -- queued|running|done|failed|dead
  step TEXT, progress REAL, title TEXT, slug TEXT, style TEXT, email TEXT,
  error TEXT, attempts INTEGER, output_url TEXT, html_size INTEGER,
  quality_score REAL, cost_cny REAL,
  started_at TEXT, updated_at TEXT, finished_at TEXT, created_at TEXT
);
```

**Rate limit**: in-memory Map (60s/IP), KV 未绑定 (H12 预留)。
**CORS**: `Access-Control-Allow-Origin: *` (synth 端点)。

## 5. 多省份 / 多模式 (客户端 JS)

推荐算法在 `public/js/recommender.js` 客户端跑, 无后端调用。

**省份支持矩阵** (数据在 `public/data/` + `data/`):

| 省份 | 模式 | 数据状态 | 备注 |
|---|---|---|---|
| 湖北 | 3+1+2 | ✅ 全 (2023-2025 物理+历史) | 生产 |
| 广东 | 3+1+2 | ⚠️ 2024 锚点级 (~70 行) | |
| 江苏 | 3+1+2 | ⚠️ 2024 锚点级 (~80 行) | |
| 北京/上海/天津/浙江/山东/海南 | 3+3 | ❌ 无数据 | 代码 ready |

## 6. 扩展点

### 加新专业 (静态)
- 写 `skills/gaokao-major-explorer/data/curated/{slug}.json` (18 字段 schema)
- 跑 `scripts/render_mobile.py` + `scripts/inject_*.py` 生成 HTML
- 跑 `scripts/build_sitemap.py` 更新 sitemap
- 跑 `scripts/smart_audit.py` 验证 ≥7 分
- git commit + push → CF Pages 自动部署

### 加新专业 (LLM 合成)
- 用户前端搜未收录专业 → POST /api/synth/generate
- D1 入队 → GH Action cron */1 pull → scf/synth 7 步
- 自动 git push → CF 部署

### 加新 Pages Function
- 在 `functions/api/` 加 `.ts` 文件
- 遵循现有 `synth/*.ts` 模式 (D1 binding via env.DB)
- `wrangler.toml` 已配 D1 binding

### 加新数据源
- 写新 fetcher 到 `scripts/` (参考已归档的 `fetch_*.py`)
- 合并到 canonical `data/{prov}_admission_*.csv`
- 跑 `scripts/build_all_majors.py` 重建 manifest

## 7. 排序公式 (客户端 JS)

`public/js/recommender.js` 客户端跑, 逻辑等效于原 `core/recommender.py` (已删):

```javascript
_sortKey = cityScore * 100000 + layerScore * 10000 + probScore * 10
// city: 0/1/2, layer: 985=4/211=3/普通=2/专科=1, prob: 0-1
```

**关键**: `strategyBonus` **不参与排序** (ADR-005), 只影响 `strategyNote` 文字。

## 8. 概率模型 (客户端 JS)

`public/js/recommender.js` 实现等效 Gaussian CDF (ADR-004):

```javascript
σ = stdRank >= minRank * 0.05 ? stdRank : minRank * 0.25
z = (studentRank - minRank) / σ
P = 0.5 * (1 + erf((-z + 0.7) / sqrt(2)))
category = P < 0.30 ? '冲' : P < 0.70 ? '稳' : '保'
```

## 9. 已知性能/资源约束

- `public/data/manifest.json` 432 KB, 客户端 fetch 后缓存
- `public/js/recommender.js` 21 KB, 纯客户端无后端
- CF Pages 免费层: 5 万次访问/月 + 1GB 存储 (够个人站)
- D1 免费层: 5M reads/天 + 100K writes/天 (synth 队列够用)
- GH Action 公开仓库 unlimited minutes (cron */1 跑 synth worker)

## 10. 部署形态

| 形态 | 现状 |
|---|---|
| 静态站 (CF Pages) | ✅ 生产, git push 自动部署, 优选 IP 30-100ms |
| Pages Functions (TS) | ✅ 生产, D1 binding |
| LLM 合成 (GH Action) | ✅ 生产, cron */1 + repository_dispatch |
| SCF 部署 (腾讯云) | ❌ 弃用 (ADR-022), 代码保留在 scf/synth/ 作 GH Action 模块 |
| FastAPI (Docker) | ❌ 删除 (ADR-021), v0.2.0 MVP 遗留 |
| 本地预览 | `cd public && python3 -m http.server 8000` |

## 11. OCR 架构规定 (MinerU SDK 锁定) ⭐⭐⭐

> **2026-06-08 架构升级**: 全部 OCR 走 MinerU SDK, 不再用 PaddleOCR 容器方案.
> 凡是项目里需要 OCR 的地方 (PDF 投档表 / PNG 截图 / JPG 公告) 一律用 MinerU.

### 11.1 选型理由

| 维度 | PaddleOCR (旧) | MinerU SDK (新) |
|---|---|---|
| 安装 | Docker 容器 + paddlepaddle wheel | `pip install mineru` |
| Mac arm64 + Python 3.14 | ❌ 无 wheel, 需容器 | ✅ 原生支持 |
| Token 消耗 | - | Flash 模式免 token, VLM 模式需 |
| 单页速度 | 30-60s (含容器启动) | 15-20s (Flash) |
| 表格识别 | 需后处理 | `enable_table=True` 直接出 HTML |

### 11.2 唯一 API

```python
from mineru import MinerU
client = MinerU(token=None)             # Flash 模式免 token
client.set_source("gaokao-hubei-mvp")   # 标识调用方

# PDF (按页范围)
r = client.flash_extract(
    "input.pdf",
    page_range="1-20",                  # MinerU API 限 20 页/次, 分批
    enable_table=True,
    timeout=600,
)

# PNG / JPG (单图)
r = client.flash_extract(
    "input.png",
    is_ocr=True,                       # 关键! 否则返空
    enable_table=True,
    timeout=300,
)

md = r.markdown                        # 完整 HTML <table>...</table>
```

### 11.3 大 PNG 切 chunk 模板

```python
from PIL import Image
img = Image.open("long.png")             # e.g. 567x7922 投档表
w, h = img.size
chunk_h, overlap = 2000, 50
i, start = 0, 0
while start < h:
    end = min(start + chunk_h, h)
    img.crop((0, start, w, end)).save(f"part{i}.png")
    if end >= h: break
    start = end - overlap
    i += 1
# 每 part 分别 flash_extract → 合并 HTML → dedup (chunk 重叠)
```

### 11.4 反模式 (禁止)

- ❌ 新加 `scripts/*_ocr.py` 用 PaddleOCR / Tesseract / EasyOCR
- ❌ Dockerfile 加 paddleocr target 或 docker-compose ocr service
- ❌ 把 OCR 容器化 (PaddlePaddle 在 Mac 没 wheel, 容器启动慢, 5-10x 慢于 MinerU)
- ❌ 用 `pdfplumber` / `camelot` 解析表格 (对扫描版 PDF 失效, MinerU 内部已含这些)
- ❌ 不切 chunk 直接对 567x7922 大 PNG OCR (返空)

### 11.5 模板脚本 (已归档, 保留参考)

- `scripts/_archive/2026-Q2-prelaunch/mineru_eeagd.py` — PDF 分批模板 (20 页/批)
- `scripts/_archive/2026-Q2-prelaunch/parse_gk100_hb_2025_phys_full.py` — PNG 切 chunk 模板 (5 chunk → 394 行)

### 11.6 实测 (2026-06-08)

- gk100 HB 2025 物理 PNG (567x7922, 1.2MB) 切 5 chunk → 394 行 0 错行
- eea.gd GD 2024 PDF (29/58 页) → 4500 行 0 错行
- 全程 ~110s, Flash 模式免 token

## 12. Phase 3 精简后状态 (2026-06-22)

详见 `PRELAUNCH_CLEANUP_ANALYSIS_2026-06-22.md` + DECISIONS.md ADR-021/022/023。

**删除**:
- FastAPI v0.2.0 MVP 栈 (api/ core/ tests/ + cli_demo.py + Dockerfile + docker-compose.yml + DOCKER.md + requirements-backend.txt + frontend/index.html)
- 5 个 orphan HTML + 30 个 public/data/curated/ + scripts_link 死链
- scripts/deploy_to_public.py (ROOT bug, 不再用)

**归档**:
- 37 个历史 scripts → scripts/_archive/2026-Q2-prelaunch/
- 26 个 data/*_real_*.csv → data/_archive/2026-Q2/
- scf/deploy.sh + template.yaml → scf/_archive/
- 16 个 PLAN_day*/HANDOFF docs → docs/_archive/2026-Q2/
- 2 个 chsi docs + 3 截因子目录 → docs/_archive/2026-Q2/

**保留 (生产路径)**:
- public/ (499 PC + 488 Mobile HTML + 客户端 JS)
- functions/ (CF Pages Functions, TS)
- scf/synth/ (Python 模块, GH Action 跑)
- scripts/ (52 active: build_sitemap / inject_* / smart_audit / synth_* / backfill_* / fix_* 等)
- data/ (canonical CSV + audit_registry.json)
- skills/gaokao-major-explorer/ (478 curated JSON + 491 HTML)
- docs/ (10 active .md)
- migrations/ + wrangler.toml + .github/workflows/

**后续待办** (Phase 4, 上线后):
- D1 scripts/ 子目录重组 (build/audit/synth/schema-fix/deploy/) — 单独立项
- D3 Mobile/PC 双轨 → 响应式单轨 — 1000 文件重构, 不做
