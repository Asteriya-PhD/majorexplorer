# DEPLOY_HYBRID.md — Major Explorer Hybrid Pipeline 部署指南 v1

> **状态**: 实施中 (2026-06-12)
> **架构**: Cloudflare Pages Function (队列入口) + GitHub Action (跑 Python synth) + D1 (队列存储)
> **成本**: **$0/月** (CF Pages 免费层 + GH Actions 公开仓库 unlimited minutes)
> **时延**: 5-20min (1min cron + 5-15min Python + 30s CF 部署)

---

## Context (为什么 Hybrid)

替代了 2 个原方案:
- ❌ **T1 (TypeScript 全端口)**: $5/月 Workers Paid + 4-5 天 + 100% 重写 Python → 0 价值
- ❌ **SCF (腾讯云)**: 香港 0 成本但 15min timeout + 同步卡死 + 出错难查

**Hybrid 的关键洞察**:
- "Git as Queue + GitOps" — synth 完的文件 git commit push → CF Pages 自动重新部署
- 队列持久化用 D1 (CF 自家 SQLite, 免费 5GB)
- 跑 Python synth 复用 GH Action (公开仓库 unlimited minutes, 0 成本)

## 架构 (v1)

```
用户浏览器
  ↓ POST /api/synth/generate
Cloudflare Pages Function (10ms CPU)
  ↓ INSERT (status='queued')
Cloudflare D1 (synth-jobs table)
  ↓ 1 分钟 cron claim
GitHub Action (ubuntu-latest, 20min timeout)
  ↓ SELECT next queued
Python scripts/synth/synth_queue_worker.py
  ↓ subprocess
Python scripts/synth/synth_trigger.py (7 步 pipeline)
  ↓ 写 public/{slug}.html + manifest.json
Git auto-commit + push
  ↓ CF Pages 监到 push → 30s 自动重新部署
用户浏览器
  ↓ GET /{slug}.html
Cloudflare Pages 静态 CDN
```

**接口**:
- `POST /api/synth/generate` (CF Function) — 入队
- `GET /api/synth/status?run_id=xxx` (CF Function) — 查状态
- `GET /api/synth/{slug}` (CF Function) — 动态 fallback (静态未部署时)
- `POST` 内部 GH Action cron — 拉队列跑 worker

## 实施步骤

### ✅ 步骤 0: 准备工作 (2026-06-12 完成)

- [x] 仓库改 public (GH Actions unlimited minutes)
- [x] `requirements.txt` → `requirements-backend.txt` (避免 CF Pages 装 Python deps)
- [x] `.gitignore` 加 `node_modules/`, `.wrangler/`, `dist/`, `.dev.vars`
- [x] CF Dashboard 创建 D1 database `synth-jobs` (ID: `c74a412b-6587-48e5-ae2e-b2cde43acdc7`)
- [x] 4 个凭据存到 GH Secrets: `CF_ACCOUNT_ID`, `CF_API_TOKEN`, `CF_D1_DATABASE_ID`, `DEEPSEEK_API_KEY`
- [x] 4 个凭据存到本地 `.env` (同步)

### ⚠️ 步骤 1: 升级 CF API Token scope (你做)

**问题**: 当前 token `<CF_API_TOKEN>` (在 `.env` / GH Secret) 缺 D1:Edit 权限
- `verify` ✓ 通过
- D1 query ✗ 报 `7403 - account not authorized` / `10000 - Auth error`

**修复** (5 分钟):
1. 打开 https://dash.cloudflare.com/profile/api-tokens
2. 找到刚才那个 token (status: active) → Edit
3. Permissions → Add:
   - **D1:Edit** (account 级)
   - **Account.Workers KV Storage:Edit** (account 级, 备 KV 用)
   - **Pages:Edit** (account 级, 备 Pages binding 改用)
4. (可选) Account Resources 选具体 account `0e16b657...`
5. Continue to summary → Save
6. ⚠️ 旧 token 失效, 复制新 token, 更新:
   - `.env` 的 `CF_API_TOKEN=...`
   - `gh secret set CF_API_TOKEN --body "新token"`

**验证修复** (本地):
```bash
source .env
curl -sS -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/d1/database/$CF_D1_DATABASE_ID/query" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT name FROM sqlite_master"}'
# 期望: {"result":[{"results":[]}],"success":true}
```

### ⚠️ 步骤 2: 跑 D1 migration (你做 或 token 修好后我做)

**方式 A — Dashboard Console** (推荐, 不依赖 token scope):
1. 打开 https://dash.cloudflare.com → Workers & Pages → D1 SQL Database → `synth-jobs`
2. 点 **Console** 标签
3. 粘贴下面 SQL → Run

**方式 B — wrangler CLI** (token 修好后):
```bash
npx wrangler d1 execute synth-jobs --file=./migrations/0001_init.sql \
  --account-id=$CF_ACCOUNT_ID \
  --api-token=$CF_API_TOKEN
```

**SQL 内容** (来自 `migrations/0001_init.sql`):
```sql
CREATE TABLE IF NOT EXISTS synth_jobs (
  run_id        TEXT PRIMARY KEY,
  status        TEXT NOT NULL DEFAULT 'queued',
  step          TEXT NOT NULL DEFAULT 'init',
  progress      REAL NOT NULL DEFAULT 0.0,
  title         TEXT NOT NULL,
  slug          TEXT NOT NULL,
  style         TEXT,
  email         TEXT,
  error         TEXT,
  attempts      INTEGER NOT NULL DEFAULT 0,
  output_url    TEXT,
  html_size     INTEGER,
  quality_score REAL,
  cost_cny      REAL,
  started_at    TEXT,
  updated_at    TEXT,
  finished_at   TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_queued ON synth_jobs(status, attempts, created_at);
CREATE INDEX IF NOT EXISTS idx_slug_done ON synth_jobs(slug, status);
```

### 步骤 3: 创建 Cloudflare Pages 项目 (你做)

1. https://dash.cloudflare.com → Workers & Pages → Create application → Pages
2. **Connect to Git** → 选 `<your-org>/majorexplorer`
3. Project name: `majorexplorer`
4. **Build settings**:
   - Build command: **`echo skip`** (静态站, 无需构建)
   - Build output directory: **`public`**
   - Root directory: (留空)
   - Environment variables: (不设, 静态站不需要)
5. Save and Deploy → 等 30s 拿到 `majorexplorer.pages.dev`
6. ⚠️ 这次部署会失败 (因为 functions/ 还没绑定 D1, generate.ts 找不到 env.DB), 但**没事**, 接下来步骤 4 绑 D1 即可

### 步骤 4: 绑定 D1 到 Pages Function (你做)

1. Pages 项目 → Settings → Functions → **D1 database bindings**
2. Variable name: **`DB`** (handler 里 `env.DB`)
3. D1 database: 选 `synth-jobs`
4. Save
5. (可选) KV namespace: 暂时不用, 留空
6. ⚠️ **不写 wrangler.toml** — 之前 commit 8b48acb 删了, 这是对的
   - 原因: wrangler.toml 会让 CF Pages 走 Workers 模式, 改 `pages_build_output_dir` 后仍可能误判
   - 所有 binding 全在 Dashboard 配

### 步骤 5: 触发第一次部署 (我 push 后 CF 自动)

等 commit push 完后, CF Pages 自动:
1. 监到 `main` 分支更新
2. 跑 `echo skip` (无构建)
3. 部署 `public/` 静态 + `functions/` API
4. 30s 后 `https://majorexplorer.pages.dev` 上线

**验证**:
```bash
# 1. 健康检查 (无 endpoint, 用 status 探针)
curl -I https://majorexplorer.pages.dev/
# 期望: HTTP/2 200

# 2. synth API 健康检查
curl -sS https://majorexplorer.pages.dev/api/synth/status?run_id=test
# 期望: {"ok":false,"error":"run_id not found"} (说明函数跑起来了, D1 接通了)

# 3. 静态 70 精品抽样
for slug in accounting translation insurance; do
  status=$(curl -o /dev/null -s -w "%{http_code}" https://majorexplorer.pages.dev/${slug}.html)
  echo "$slug: $status"
done
# 期望: 3 个 200
```

### 步骤 6: E2E 跑 1 篇验证 (我)

```bash
# 1. 本地触发 (模拟前端)
curl -sS -X POST https://majorexplorer.pages.dev/api/synth/generate \
  -H "Content-Type: application/json" \
  -d '{"title":"翻译","slug":"translation","style":"humanities"}'
# 期望: {"ok":true,"run_id":"...","status":"queued","status_url":"..."}

# 2. 查状态 (1-15min 后 done)
curl -sS "https://majorexplorer.pages.dev/api/synth/status?run_id=<run_id>"

# 3. 等 GH Action commit push 后, 访问
curl -I https://majorexplorer.pages.dev/translation.html
# 期望: HTTP/2 200
```

### 步骤 7: 跑首批 5 PoC (我)

PoC 名单: 保险 / 知识产权 / 基础医学 / 翻译 / 汉语言

```bash
# 批量触发 (前端模拟, 或直接走 API)
for m in "保险" "知识产权" "基础医学" "翻译" "汉语言"; do
  curl -sS -X POST https://majorexplorer.pages.dev/api/synth/generate \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"$m\"}"
done

# 监控: 看 GH Actions 跑批
# https://github.com/<your-org>/majorexplorer/actions/workflows/synth.yml
```

## 关键文件清单 (本次实施新建)

| 文件 | 行数 | 作用 |
|------|------|------|
| `migrations/0001_init.sql` | 31 | D1 synth_jobs 表 + 2 索引 |
| `functions/api/_synth/d1.ts` | 138 | D1 客户端封装 (7 函数) |
| `functions/api/synth/generate.ts` | 149 | POST /api/synth/generate handler |
| `functions/api/synth/status.ts` | 60 | GET /api/synth/status handler |
| `functions/api/synth/[[slug]].ts` | 63 | GET /api/synth/{slug} 动态 fallback |
| `.github/workflows/synth.yml` | 108 | 1min cron + workflow_dispatch |
| `scripts/synth/synth_queue_worker.py` | ~250 | 拉 D1 → 跑 synth_trigger → 更新状态 |

## 复用 100% 不动

- `scf/synth/*.py` (10 个文件, 2306 行) — 0 重依赖
- `scripts/synth/synth_trigger.py` — 7 步 pipeline, 通过 subprocess 调
- 70 精品 HTML + manifest.json
- `docs/DEPLOYMENT.md` v2 — 原 v2 部署文档, 静态站仍生效

## 凭据存储

| 位置 | 凭据 | 用途 |
|------|------|------|
| `.env` (本地, gitignored) | 4 个 | 本地开发 + 手动 curl |
| GH Secrets (4 个) | 4 个 | CI/CD (synth.yml 用) |
| `~/.claude/projects/.../memory/cf-deepseek-credentials-2026-06-12.md` | 4 个 | 跨会话持久 |

## 风险与缓解 (v1)

| 风险 | 概率 | 缓解 |
|------|------|------|
| 1min cron 队列堆积 | 极低 | 单进程 + max=1, 长尾串行 |
| 2000min/月耗尽 (私有) | 已解决 | **仓库 public** (unlimited) |
| CF Function 10ms CPU 不够 | 极低 | 只做 D1 put, 实测 <5ms |
| 队列任务死 (LLM 3 轮失败) | 中 | D1 attempts 字段, ≥3 标 dead |
| GH Action 20min timeout | 极低 | 单篇 synth 实测 5-10min |
| 仓库改 public 暴露代码 | 已决定 | AGPL-3.0 |
| 用户等 5-20min 不耐烦 | 中 | UX 强调"邮箱通知, 无需在线等" + polling |

## 实施时间表 (1.5 天)

| 时段 | 任务 | 状态 |
|------|------|------|
| Day 1 上午 | 3 个 Pages Function handler + D1 schema + GH Action worker | ✅ 完成 |
| Day 1 下午 | 部署文档 + token 升级 + Pages binding | ⚠️ 等你 |
| Day 1 晚 | E2E 跑 1 篇 (翻译) | 等 binding 后 |
| Day 2 | 5 PoC + 修 bug + 上线 | 等 Day 1 晚过 |

## 相关 ADR

- ADR-020: Hybrid 部署架构
- ADR-021: 按需生成 Pipeline 时延 5-20min 接受
- ADR-022: 仓库 public (AGPL-3.0 + GH Actions 公开仓库)
