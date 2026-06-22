# 项目精简分析报告 · gaokao-hubei-mvp

**Date**: 2026-06-22
**作者**: Sisyphus (analyze-mode)
**范围**: 上线前精简 — 哪些可删 / 哪些可精简
**状态**: ⏳ 待用户审核, 未做任何代码改动

---

## A. 架构全景 (实际形态 vs. README 描述)

### A.1 实际形态

```
gaokao-hubei-mvp/                       (2,567 git-tracked files, 352M .git)
│
├── 静态站 (生产)                         ← Cloudflare Pages 部署
│   ├── public/                          (96M, 1039 HTML: 504 PC + 493 Mobile + 30 data/curated + 顶级页)
│   │   ├── *.html                       PC 详情页 504 篇
│   │   ├── m/majors/*.html              Mobile 详情页 493 篇 (尺寸 ~55% PC)
│   │   ├── css/ js/ data/               静态资源, 客户端纯 JS 跑推荐
│   │   └── sitemap.xml (485 URL) / robots.txt / 404.html / disclaimer / privacy / terms
│   ├── functions/                       CF Pages Functions (TypeScript)
│   │   ├── _middleware.ts               手机 UA → /m/ 自动跳转
│   │   └── api/synth/{generate,status,[[slug]]}.ts  D1 队列入队 + 状态查询
│   │   └── api/report.js                反馈 → GitHub Issue
│   │   └── api/_synth/d1.ts             D1 客户端封装
│   ├── migrations/0001_init.sql         D1 schema (synth_jobs 队列)
│   └── wrangler.toml                    CF Pages 配置 + D1 binding
│
├── LLM 按需合成 pipeline (生产)             ← GH Action cron */1 跑
│   ├── scf/synth/                       Python 7 步 pipeline (validate→search→route→synth→validate→render→manifest)
│   │   ├── main.py                      worker 入口 (被 GH Action 调)
│   │   ├── llm.py / mock_llm.py / prompts.py / validator.py / search.py / manifest_ops.py / audit.py / render_bridge.py
│   ├── scripts/synth_queue_worker.py    GH Action 跑: 拉 D1 → 调 scf/synth/main.py:worker → push
│   ├── scripts/synth_trigger.py         手动跑 1 篇
│   ├── scripts/synth_monitor.py         队列监控
│   ├── scripts/batch_synth.py           批量入队
│   ├── .github/workflows/synth.yml      cron + repository_dispatch
│   └── scf/deploy.sh / scf/template.yaml  ★ SCF 部署模板 (疑: 是否仍用?)
│
├── 内容质量审计 pipeline (半活跃)           ← 单篇深审仍用, 批量已稳定
│   ├── scripts/smart_audit.py           启发式 L1 + LLM L2 智能路由 (CLAUDE.md 强制用)
│   ├── scripts/batches/content_audit.py 单篇深审 (Tier 2 重写时用)
│   ├── scripts/update_audit_registry.py registry 同步 + 统计
│   ├── scripts/check_major.py / check_schema_gaps.py / mark_irreducible_7.py / variance_*.py
│   ├── data/audit_registry.json         (git tracked, 派生视图)
│   └── test_results/content_audit_*.json (527 个, gitignored)
│
├── 构建 / 渲染 / 注入 (活跃)                ← 改内容时仍调
│   ├── scripts/build_sitemap.py         sitemap 生成 (PRELAUNCH P0-2 已修)
│   ├── scripts/render_mobile.py / render_one.py / render_all_bug3.py
│   ├── scripts/inject_{seo,jsonld,og,og_image,theme_colors,discipline_fields}.py
│   ├── scripts/pwa_inject_theme_color.py
│   ├── scripts/build_og_image.py / render_og_v6*.py / render_og_cards.py / render_og_cover.py
│   ├── scripts/build_hierarchy.py / build_directory.py / build_colleges_v2.py / build_all_majors.py
│   ├── scripts/fix_xuanke_salary_batch.py / fix_top_companies_schema.py / fix_manifest_discipline.py
│   ├── scripts/backfill_manifest_fields.py / backfill_missing_evaluations.py
│   ├── scripts/cleanup_entrepreneur.py / normalize_schema.py / repair_top_schools_rank.py
│   ├── scripts/dedup_17_groups.py / rekey_*.py / add_menjia_to_manifest.py / rebuild_manifest.py
│   ├── scripts/deploy_to_public.py      (⚠ CLAUDE.md 标注 ROOT bug, 不能用于本项目)
│   └── skills/gaokao-major-explorer/    SKILL + 478 JSON + 491 HTML (curated 源)
│
├── 数据抓取 (一次性, 已完成)               ← 数据已落 data/, 脚本可归档
│   ├── scripts/fetch_*.py (10 个: 555edu/dxsbb/eolcn/gk100/2024_2023_anchors)
│   ├── scripts/merge_*.py (5 个)
│   ├── scripts/parse_*.py (5 个)
│   ├── scripts/crawl_*.py (3 个)
│   ├── scripts/calibrate_*.py (2 个)
│   ├── scripts/mineru_eeagd.py / scrub_jiaoyubu.py / clean_merge*.py
│   ├── scrapers/chsi/ (含 .venv, gitignored)  chsi 阳光高考 scraper
│   └── data/ (285M, 大部分 gitignored: _cache/ _logs/ *_raw/; tracked: CSV + audit_registry.json)
│
├── ★ 旧 MVP 栈 (疑: 死代码)                ← v0.2.0 96 志愿推荐, 项目已转向专业 dashboard
│   ├── api/main.py                      FastAPI 7 endpoints (只被 tests/api_pdf_test 引用)
│   ├── api/pdf_report.py                reportlab PDF 生成
│   ├── core/ (7 个 .py)                  纯函数算法 (只被 tests/ + cli_demo 引用)
│   ├── tests/ (10 个 test_*.py)          pytest 回测 (只测 core/)
│   ├── cli_demo.py                       CLI 演示入口 (无代码依赖, 仅 docs 提及)
│   ├── frontend/index.html               v0.1 原型 (无部署引用)
│   ├── Dockerfile / docker-compose.yml / DOCKER.md / requirements-backend.txt
│   └── scripts/recommender.py            (scripts 层副本, 重复 core/recommender.py)
│
├── 文档 (29 active + 15 archived)
│   ├── docs/                             29 个 .md (16 个 PLAN_day*/HANDOFF/day* 历史)
│   │   └── _archive/2026-Q2/             15 个已归档
│   ├── README.md / CLAUDE.md / AGENTS.md (root + docs/ 两份 AGENTS.md)
│   ├── LEGAL.md / TRADEMARK.md / LICENSE  法律
│   └── deploy/cloudflare-pages.md + optimal-cf-ip.sh  部署指南
│
└── 本地工作区 (gitignored, 占盘 ~3.7G)
    ├── .worktrees/ (3.5G, 10 个 day-N worktree)
    ├── .tmp-hero/ (141M)  .playwright-mcp/ (7M)  .wrangler/ (168K)
    ├── 移动端截图/ (2.3M)  ME og card/ (3.3M)  public/_tmp_stats_mock/ (36K)
    └── .pytest_cache/ (24K)  data/_cache/ data/_logs/ data/*_raw/ logs/
```

### A.2 README 与实际严重漂移

| README 说法 | 实际 |
|---|---|
| "70+ 个热门本科专业" | manifest.json 含 **475 个** slug, sitemap 含 485 URL, public/ 有 504 PC HTML |
| "scf/synth/ LLM 后端 (Python 3.11, 待部署)" | 实际由 GH Action cron */1 跑 `synth_queue_worker.py` 调 `scf/synth/main.py:worker`, 不依赖 SCF 部署 |
| 项目结构图未提 `api/ core/ tests/ cli_demo.py Dockerfile docker-compose.yml DOCKER.md` | 这些都还在 repo 里, 但是 v0.2.0 96 志愿 MVP 遗留, 跟当前"专业 dashboard"产品形态不匹配 |
| "core/ 纯函数算法 (filter / probability / strategy)" | 实际 PC 端 `public/js/recommender.js` 是**纯客户端 JS**, 无 `/api/` 调用 — `core/` 算法已不在生产路径 |

---

## B. 多栈混乱分析:三套后端并存

| 栈 | 角色 | 部署位置 | 当前活跃度 | 证据 |
|---|---|---|---|---|
| **A. FastAPI Python** | 96 志愿推荐 API + PDF 报告 | 本地 Docker / 未部署 | **疑似死代码** | `api/main.py` 只被 `tests/test_api_pdf.py` 引用; `frontend/index.html` 未被任何 deploy 脚本引用; `public/js/recommender.js` 无 `fetch('/api/')` 调用 |
| **B. Cloudflare Pages Functions** | D1 队列入队 + 状态查询 + GH Issue 反馈 | 生产 CF Pages | **活跃** | `wrangler.toml` + `migrations/` + `functions/_middleware.ts` UA 跳转已生效 |
| **C. Tencent SCF Python** | LLM 7 步合成 pipeline | **实际在 GH Action 跑, SCF 部署疑弃用** | **代码活跃, SCF 部署死** | `synth_queue_worker.py` 调 `scf/synth/main.py:worker` 作为 Python 模块; ADR-012 说 SCF 部署, 但 ADR-017 改 CF Pages 后未再更新; `scf/deploy.sh` + `scf/template.yaml` 是否仍跑需用户确认 |

**核心问题**:栈 A (FastAPI) 是 v0.2.0 MVP 遗留, 项目已经转型为"专业 dashboard + LLM 按需合成", 96 志愿推荐已移到客户端 JS。栈 A 整体可能可以删除, 但需用户确认是否有任何外部部署/使用。

---

## C. 删除候选 (按风险分级)

### C1. 零风险 — 本地清理 (不进 git, 释放 ~3.7G 磁盘)

| 路径 | 大小 | 说明 |
|---|---|---|
| `.worktrees/` | 3.5G | 10 个 day5/day13/day21/day26 worktree, 已合并的分支副本 |
| `.tmp-hero/` | 141M | hero 图本地 scratch |
| `.playwright-mcp/` | 7M | MCP 会话缓存 |
| `ME og card/` | 3.3M | OG 卡片本地 scratch |
| `移动端截图/` | 2.3M | 本地截图 |
| `.wrangler/` | 168K | CF 本地状态 |
| `public/_tmp_stats_mock/` | 36K | mock 临时数据 |
| `.pytest_cache/` | 24K | 本地 pytest 缓存 |

**操作**: `rm -rf` 即可, 全部已在 `.gitignore`, 不影响 repo。

### C2. 极低风险 — orphan HTML (5 个 slug, PC + Mobile 各一份)

`manifest.json` 没列入, 但 `public/` 仍存在的 5 个 slug (各占 ~100KB PC + ~60KB Mobile = ~160KB × 5 = ~800KB):

| slug | 推测原因 |
|---|---|
| `actuarial-final` | Tier 2 重写后改名 `actuarial-science`, 旧版未删 |
| `arabic` | 改名 `arabic-language`, 旧版未删 |
| `business-administration-demo` | 早期 demo, 正式版是 `business-administration` |
| `criminal-investigation-economics` | 拆分为 `criminal-investigation`, 旧版未删 |
| `cybersecurity` | 改名 (推测 `cyber-space-security-studies`), 旧版未删 |

**注意**:`public-security-demo` 和 `translation-final` 虽然有 `-demo`/`-final` 后缀, 但**在 manifest 里**, 是正式 slug, 不要删 (除非你想做 slug migration, 那是另一个工程)。

**操作**: `git rm public/{slug}.html public/m/majors/{slug}.html` (× 5 个 slug = 10 个文件)。建议同时跑一遍 `linkscanner` 看是否有内部链接指向这些 orphan。

### C3. 低风险 — 历史 docs 归档 (16 个 PLAN_day* + HANDOFF + day*)

| 文件 | 类型 |
|---|---|
| `docs/PLAN_day{3,4,5,5_bug3,5_gap_fill,6,15_11_leftover,17_cleanup_mobile,18_5_remainder,18_arts_agri_synth,20_30new,21_polish_verify,23}.md` | 13 个 day-specific plan |
| `docs/PLAN_on_demand_synth.md` / `docs/PLAN_pwa_tier1.md` | 阶段性 plan |
| `docs/HANDOFF_day3_team_b_d_e_f.md` | day3 交接 |
| `docs/day9_B_skipped.md` | day9 跳过记录 |

**操作**:`git mv docs/PLAN_day*.md docs/HANDOFF_*.md docs/day*.md docs/_archive/2026-Q2/`。归档而非删除 — 保留历史决策可追溯, 但清出 `docs/` 顶层。`docs/_archive/2026-Q2/` 已经有 15 个同类文件, 加进去一致。

### C4. 中风险 — 历史 scripts 归档 (约 50+ 个 .py)

`scripts/` 顶层 88 个 .py + `batches/` 28 个 + `_archive/2026-Q2/` 15 个 = 131 个。建议按"还会不会再跑"分三类:

**保留 (active, ~25 个)**:
- 部署/构建:`build_sitemap.py`, `inject_{seo,jsonld,og,og_image,theme_colors,discipline_fields}.py`, `pwa_inject_theme_color.py`, `render_mobile.py`, `render_one.py`, `render_all_bug3.py`
- 审计:`smart_audit.py`, `batches/content_audit.py`, `update_audit_registry.py`, `check_major.py`, `check_schema_gaps.py`, `mark_irreducible_7.py`, `variance_median_r1r2.py`, `variance_verify_7boundary.py`
- LLM synth:`batch_synth.py`, `synth_trigger.py`, `synth_queue_worker.py`, `synth_monitor.py`
- Schema 修复 (可能再跑):`backfill_manifest_fields.py`, `backfill_missing_evaluations.py`, `cleanup_entrepreneur.py`, `normalize_schema.py`, `repair_top_schools_rank.py`, `fix_xuanke_salary_batch.py`, `fix_top_companies_schema.py`, `fix_manifest_discipline.py`, `dedup_17_groups.py`, `rekey_by_edu_id.py`, `rekey_groups_latest.py`, `add_menjia_to_manifest.py`, `rebuild_manifest.py`, `build_hierarchy.py`, `build_directory.py`, `build_colleges_v2.py`, `build_all_majors.py`, `inject_discipline_fields.py`
- 其他:`perf_measure.py`, `verify_mobile.py`, `verify_bug3.py`, `push_wechat.py`, `claim.py`, `next_pick.py`

**归档 (historical, 不会再跑, ~50 个)** — 数据已落 `data/`, 脚本本身的历史任务已完成:
- 全部 `fetch_*.py` (10 个):`fetch_real_data.py`, `fetch_admission.py`, `fetch_555edu_*.py` (3), `fetch_dxsbb_6261.py`, `fetch_eolcn_gd_js.py`, `fetch_2024_2023_anchors.py` — 一次性抓取, 已完成
- 全部 `merge_*.py` (5 个):`merge_real_2024.py`, `merge_real_2024_gd_js.py`, `merge_{hubei,guangdong,jiangsu}_2025_gk100.py` — 一次性合并, 已完成
- 全部 `parse_*.py` (5 个):`parse_eeagd.py`, `parse_gk100_*.py` (4), `parse_jseea.py` — 一次性解析, 已完成
- 全部 `crawl_*.py` (3 个):`crawl_admissions.py`, `crawl_info.py`, `crawl_province.py`
- 全部 `calibrate_*.py` (2 个):`calibrate_probability.py`, `calibrate_rank.py`
- 全部 `render_og_*.py` / `build_og_image.py` (5 个):OG 图已生成
- `scrub_jiaoyubu.py`, `clean_merge.py`, `clean_merge_v2.py`, `shoot_mobile.py`, `scf_local_e2e.py`, `regenerate_all.py`, `recommender.py` (scripts 层副本), `parse_gk100_hb_2025_phys_full.py`, `mineru_eeagd.py`, `render_og_cover.py`, `render_og_cards.py`

**操作**:`git mv scripts/<file>.py scripts/_archive/2026-Q2/` (逐个, 或建一个 `scripts/_archive/2026-Q2-prelaunch/` 子目录避免混入已有归档)。**风险**:如果未来要重新抓 2026 年数据, `fetch_*.py` 还要再跑 — 归档前请确认。

**`scripts/batches/`** (28 个 .py):同样大量 `day1_*.csv/.log`、`batch2_retry.csv`、`arts_v1.csv` 等中间产物 + `audit_all.py`、`auto_fix_pipeline.py`、`cleanup_batch30.py`、`compare_json.py`、`contam_dict.py`、`hand_curate_b*.py` 等历史脚本。**只有 `content_audit.py` 是 active (CLAUDE.md 强制单篇深审用它)**。其余可归档。

### C5. 高风险 — 整栈删除 (FastAPI v0.2.0 MVP)

**疑似死代码栈** (8 个顶层条目 + 1 个目录):

| 路径 | 大小 | 死代码证据 |
|---|---|---|
| `api/` (3 个 .py + `__init__.py`) | ~20K | `api/main.py` 只被 `tests/test_api_pdf.py` 引用; 不在 `wrangler.toml` / `deploy_to_public.py` / 任何部署脚本里 |
| `core/` (7 个 .py) | ~35K | 只被 `tests/` + `cli_demo.py` + `scripts/parse_gk100_hb_2025_phys_full.py` (用 `score_to_rank`) 引用; 生产路径是 `public/js/recommender.js` 纯客户端 |
| `tests/` (10 个 test_*.py) | ~70K | 全部测 `core/`, 若 `core/` 删则 tests 无意义 |
| `cli_demo.py` | ~6K | 无代码依赖, 仅 docs 提及 |
| `frontend/index.html` | 单文件 | v0.1 原型, 未被任何部署脚本引用 |
| `Dockerfile` | ~1K | 仅构建 `api` target |
| `docker-compose.yml` | ~1K | 仅 `api` service |
| `DOCKER.md` | ~3K | 仅讲 Docker 跑 `api` |
| `requirements-backend.txt` | 9 行 | fastapi/uvicorn/gunicorn/reportlab — 仅 `api/` 用 |

**删除前必答问题**:
1. `api/main.py` 的 `/api/recommend` 是否有任何外部部署实例 (用户本机 / 阿里云轻量 / OrbStack) 在跑?
2. `core/` 算法是否还作为"参考实现"被任何文档/外部项目引用?
3. `tests/test_*.py` 里的回测代码是否还有保留价值 (作为算法正确性回归)?

**若全部"否"** → 整栈可删, 精简 ~140K 代码 + 4 个根级配置文件 + 1 个目录。`docs/AGENTS.md` + `docs/ARCHITECTURE.md` 需同步修订 (它们大量描述 `core/` / `api/` 入口)。

### C6. 中风险 — SCF 部署相关 (若 SCF 部署已弃用)

| 路径 | 说明 |
|---|---|
| `scf/deploy.sh` | 部署到腾讯云 SCF 的脚本 |
| `scf/template.yaml` | SCF CloudFormation 模板 |

**若 SCF 部署已弃用** (LLM 实际跑在 GH Action, ADR-017 后未再更新 SCF) → 这两个文件可归档。`scf/synth/*.py` (Python 模块) **不能删**, GH Action worker 在用。

**需用户确认**:SCF 是否还有任何线上实例?

---

## D. 精简候选 (结构调整, 不删内容)

### D1. `scripts/` 重组

当前 88 个 .py 平铺在 `scripts/` 顶层, 找东西难。建议按职能分子目录 (归档完成后):

```
scripts/
├── build/          # 构建 + 渲染 + 注入 (build_sitemap, render_*, inject_*)
├── audit/          # 质量审计 (smart_audit, content_audit, check_*, variance_*)
├── synth/          # LLM 合成 (synth_*, batch_synth)
├── schema-fix/     # schema 修复 (backfill_*, fix_*, normalize_*, repair_*, cleanup_*, dedup_*, rekey_*)
├── deploy/         # 部署辅助 (deploy_to_public, push_wechat, pwa_inject_theme_color)
├── batches/        # 批量脚本 (保留, 已存在)
└── _archive/       # 历史归档
```

**风险**:大量脚本之间有 `from <module> import` 互引用 + `docs/` 里有 `scripts/xxx.py` 路径引用, 移动会破坏引用。**建议**:只在归档完成后做, 且需同步改 docs 路径。

### D2. `docs/` 重组

归档 16 个 PLAN_day* 后, `docs/` 顶层剩 ~13 个 active md。建议:

- 保留在顶层:`README.md` (root), `CLAUDE.md` (root), `AGENTS.md` (root + docs/), `ARCHITECTURE.md`, `DECISIONS.md`, `DEPLOYMENT.md`, `DEPLOY_HYBRID.md`, `PIPELINE_major_quality.md`, `audit_registry_schema.md`, `PRELAUNCH_REVIEW_2026-06-21.md`, `DATA.md`, `MAJOR_DIRECTORY.md`, `CHECKLIST_synth_deploy.md`
- 归档:`chsi-scraper-design.md`, `recommender-chsi-ab-report.md` (chsi 阶段性报告)
- 子目录:`docs/mobile-mocks-v5/`, `docs/mobile-bugfix-screenshots/`, `docs/pwa-tier1-screenshots/` — 设计资产, 若不再参考可移 `docs/_archive/` 或删

**两份 AGENTS.md 漂移**:root `AGENTS.md` (177 行, 讲 Major 精品质量流水线) 和 `docs/AGENTS.md` (讲 v0.2.0 96 志愿 MVP) **描述的是两个不同时代的产品**。需用户决定:删 `docs/AGENTS.md`? 还是合并?

### D3. Mobile / PC 双轨

504 PC HTML + 493 Mobile HTML, 每篇 major 维护两份 HTML (~110K + ~60K)。**这是产品决策, 不是清理目标** (移动端有独立 dock/模板/PWA)。但如果未来想做"一套模板响应式适配", 这是 ~1000 文件级别的重构, 应单独立项。

### D4. `public/data/curated/` 部分 mirror

`skills/gaokao-major-explorer/data/curated/` 有 478 JSON + 491 HTML (源)。`public/data/curated/` 只有 30 个 HTML (全是 `0501xx` MOE 代码 slug)。**这 30 个是 MOE 代码命名专业在 public 端的额外副本, 其他 448 个 slug 没有这层副本** — 不一致。推测是早期 MOE 代码 slug 渲染时多输出了一份。建议核实后删除 `public/data/curated/` 整个目录 (sitemap 不引用它, PC HTML 在 `public/{slug}.html` 已经有)。

### D5. `scripts_link/` 自引用 symlink

`scripts_link -> ../gaokao-hubei-mvp/scripts` — 从当前目录解析, 指向 `scripts/` 自己。**死链** (从 worktree 角度才有意义, 但 worktree 路径是 `.worktrees/dayN-X/`, 不在主 repo 里调这个 symlink)。建议 `rm scripts_link` (用 `git rm` 如果 tracked)。

### D6. `data/` 285M — 大部分已 gitignored

`data/` 实际 tracked 的是:`audit_registry.json`, `claimed.json`, `colleges.json`, `groups_latest.json`, `linkage.json`, `major_directory.json`, `province_lines.json`, `schema_drift.json`, `schema_gaps.json`, `school_history.json`, `school_specialties.json`, `target_schools.json`, `yfyd_2025.json`, `cleanup_entrepreneur_report.json`, `irreducible_7_candidates.json`, 各省 `*_admission_*.csv` (非 `*_real_*` / `*_raw`), 各省 `*_rank_*.csv`, `README.md`。其余 `_cache/ _logs/ *_raw/ *.log` 都已 gitignored。

**问题**:`data/` 里多个 `*_real_555edu.csv` / `*_real_dxsbb6261.csv` / `*_real_ocr.csv` / `*_real_mineru.csv` 是中间产物, 是否 tracked? 若 tracked, 可以归档到 `data/_archive/` 或删 (canonical 是 `*_admission_*.csv` 无 `*_real_*` 后缀的)。

---

## E. 文档与代码漂移 (需修订)

| 文档 | 漂移点 | 修订方向 |
|---|---|---|
| `README.md` | "70+ 个热门本科专业" | 改 "475 个专业" (或按学科门类分组表述) |
| `README.md` | 项目结构图未提 `api/ core/ tests/ cli_demo.py Dockerfile docker-compose.yml DOCKER.md` | 若 C5 删除 → 不用改; 若保留 → 补充说明"v0.2.0 96 志愿 MVP, 当前不在生产路径" |
| `docs/AGENTS.md` | 整篇描述 v0.2.0 96 志愿 MVP (core/ api/ cli_demo) | 与 root `AGENTS.md` (讲 Major 精品流水线) 严重不一致 — 删或合并 |
| `docs/ARCHITECTURE.md` | §1-§10 全部描述 FastAPI 栈; §11 OCR 锁定 MinerU 仍有效 | 若 C5 删除 → 整篇重写为 CF Pages + SCF/GH Action 架构; §11 OCR 移到独立文档 |
| `docs/DECISIONS.md` | ADR-011/013 过期, ADR-012 SCF 部署疑弃用, ADR-006/007 临时方案 | 补 ADR-021+ 记录"FastAPI 栈弃用" / "SCF 部署改 GH Action" / "70+ → 475 专业" 决策 |
| `CLAUDE.md` | "scripts/deploy_to_public.py ROOT 写死 gaokao-hubei-mvp, 不能用于本项目" | 这条 trap 应直接修代码而非永久记在 CLAUDE.md; 或彻底删 `deploy_to_public.py` (若不再用) |

---

## F. 上线前必修 vs. 可延后

### F.1 上线前必修 (PRELAUNCH_REVIEW_2026-06-21.md 已记录, 状态需核实)

- ✅ P0-1 首页 H1 — git log 显示 `05a3f576 fix(launch): prelaunch review P0-1/P0-2/P1-1 完工` 已修
- ✅ P0-2 sitemap 485 URL — 已修
- ✅ P1-1 404.html 真静态 404 — git log 显示 `ca115f07 fix(launch): 404.html 真静态 404 (替换无效的 functions/_404.ts)` 已修
- ⚠ `functions/_404.ts` 已删 (git status 显示 D), 但还未 commit

### F.2 上线前可延后 (本报告新增)

- C2 orphan HTML 5 个 — 5 分钟可删, 上线当天删也行
- C1 本地清理 — 不影响 repo, 任何时候都可做
- C3 docs 归档 — 任何时候都可做

### F.3 上线后再做

- C4 scripts 归档 — 改动多, 易出错, 上线后做
- C5 FastAPI 栈删除 — 需用户确认无外部使用, 上线后做
- D1 scripts 子目录重组 — 大改动, 上线后立项
- E 文档修订 — 跟随 C5 决策

---

## G. 需用户确认的关键问题 (决定 C5/C6 去留)

1. **FastAPI 栈 (api/ + core/ + tests/ + cli_demo.py + frontend/index.html + Dockerfile + docker-compose.yml + DOCKER.md + requirements-backend.txt) 是否还有任何活跃使用?**
   - 本地有跑 `uvicorn api.main:app`?
   - 阿里云轻量 / OrbStack 有跑 `docker compose up`?
   - 是否还想保留作为 96 志愿推荐算法的"参考实现"?

2. **SCF 部署是否还活着?**(`scf/deploy.sh` + `scf/template.yaml`) — 还是 LLM 合成 100% 走 GH Action?

3. **`docs/AGENTS.md` (v0.2.0 MVP 视角) vs. root `AGENTS.md` (Major 精品流水线视角)** — 哪份是真相?另一份删还是归档?

4. **`scripts/deploy_to_public.py`** — CLAUDE.md 标注 "ROOT 写死 gaokao-hubei-mvp, 不能用于本项目", 那它还在 repo 里做什么?删?还是修?

5. **`data/` 里的 `*_real_555edu.csv` / `*_real_dxsbb6261.csv` / `*_real_ocr.csv` / `*_real_mineru.csv`** 中间产物是否要保留 tracked? (canonical 已经是 `*_admission_*.csv` 无后缀版本)

6. **`public/data/curated/` 30 个 MOE 代码 slug HTML** 是否有用? (其他 448 个 slug 没这层副本, 不一致)

---

## H. 精简后的理想终态

如果上述问题全部"可删"答案:

- repo 文件数:2,567 → ~2,000 (减 ~550 个 HTML/Python 归档, 主要靠 C2/C4)
- `scripts/` 顶层:88 → ~25 active (其余归档到 `_archive/`)
- `docs/` 顶层:29 → ~13 active (其余归档)
- 根级冗余:删 `cli_demo.py / Dockerfile / docker-compose.yml / DOCKER.md / requirements-backend.txt / frontend/index.html` + 整个 `api/ core/ tests/` 目录
- 本地磁盘:3.7G → 0 (清 `.worktrees/ .tmp-hero/` 等)
- `.git` 大小:352M → 难减 (历史 commit 已写入), 除非做 `git filter-repo` 重写历史 (不建议上线前做)

**预计可释放**:~140K 代码 + ~800K orphan HTML + ~50 个归档脚本 + ~16 个归档 docs。代码层精简约 15-20%, 文档层精简约 50%。

---

## I. 执行顺序建议 (用户批准后)

```
[Phase 1 - 零风险, 任何时间可做]
  1. C1 本地清理 (rm -rf .worktrees/ .tmp-hero/ 等) — 释放 3.7G
  2. git rm functions/_404.ts (PRELAUNCH P1-1 已删文件, 但未 commit)

[Phase 2 - 低风险, 上线前可做]
  3. C2 orphan HTML 5 个 (git rm public/{slug}.html public/m/majors/{slug}.html)
  4. C3 docs 归档 (git mv docs/PLAN_day*.md docs/_archive/2026-Q2/)

[Phase 3 - 中风险, 上线后做]
  5. C4 scripts 归档 (git mv ~50 个 fetch_*/merge_*/parse_*/crawl_*/calibrate_* 到 _archive/)
  6. C6 SCF 部署文件归档 (若用户确认 SCF 弃用)
  7. D4 public/data/curated/ 删除 (若确认无用)
  8. D5 scripts_link 死链删除
  9. D6 data/ 中间产物 CSV 归档

[Phase 4 - 高风险, 需用户明确批准]
  10. C5 FastAPI 栈整栈删除 (若用户确认无外部使用)
  11. D1 scripts/ 子目录重组 (C4 完成后)
  12. D2 docs/ 重组 + AGENTS.md 合并
  13. E 文档修订 (README/ARCHITECTURE/DECISIONS 同步)
```

---

**等您审核。** 请逐项告知:

- C1-C6 哪些类执行 / 不执行
- D1-D6 哪些调整做 / 不做
- G 的 6 个问题答案
- E 的文档修订是否同步做

我再根据您的决策制定执行计划, 不会在您批准前动任何代码。
