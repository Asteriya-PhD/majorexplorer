# 在线按需合成 — 运营手册 (Day 7 v1.4)

> 面向: 运营 / 值班 SRE / 下一 session 的 agent
> 触发: 用户搜未收录专业时, 一键 🔄 实时生成 ~90s 出 HTML

---

## 1. 系统拓扑 (一图秒懂)

```
                    ┌─────────────────┐
                    │  PC/Mobile 浏览器 │
                    └────────┬────────┘
                             │ POST /api/synth/generate
                             ↓
              ┌──────────────────────────────┐
              │  CF Pages Function (HK)       │  ← generate.ts (30s timeout)
              │  • rate limit (60s/IP)        │     status.ts
              │  • body 校验                  │     [[slug]].ts (fallback)
              │  • D1 INSERT job              │
              └──────────────┬────────────────┘
                             │ INSERT synth_jobs (status='queued')
                             ↓
              ┌──────────────────────────────┐
              │  Cloudflare D1 (synth-jobs)   │
              └──────────────┬────────────────┘
                             │ Cron */1 拉队列
                             ↓
              ┌──────────────────────────────┐
              │  GH Action worker            │  ← synth.yml (20min/job)
              │  • claim_next (atomic)       │     synth_queue_worker.py
              │  • subprocess synth_trigger  │     synth_trigger.py (7 步)
              │  • LLM m3 → deepseek         │     scf/synth/*.py
              │  • render HTML + 路径转换    │
              │  • inject og/seo/jsonld      │
              │  • manifest upsert           │
              │  • auto git commit + push    │
              └──────────────┬────────────────┘
                             │ git push
                             ↓
              ┌──────────────────────────────┐
              │  CF Pages (静态)              │
              │  • public/<slug>.html        │  ← 用户下次刷新可见
              └──────────────────────────────┘
```

---

## 2. 日常值班 — 4 个高频问题速查

### Q1: 用户搜了 "X" 没看到 🔄 实时生成按钮?

**原因 1**: 前端缓存未刷新 → 让用户 Ctrl+Shift+R 强刷

**原因 2**: PC/Mobile JS 没同步更新 → 查 `git log public/js/pc-search.js public/m/js/search.js`, 看最近 commit 是否含 `bindSynthCard`

**原因 3**: `_middleware.ts` 拦截了 `/api/synth/*`? → 不会, `/api/` 已在白名单 (`functions/_middleware.ts:21-27`)

### Q2: 用户点按钮后一直转圈, 几分钟后超时?

**排查步骤**:

```bash
# 1. 看 D1 job 状态
curl "https://majorexplorer.com/api/synth/status?run_id=<用户的run_id>"

# 2. 看 GH Action 运行历史
gh run list --workflow=synth.yml --limit=5
gh run view <run_id> --log

# 3. 看是否连续 dead (attempts 满 3)
curl "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/d1/database/$CF_D1_DATABASE_ID/query" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -d '{"sql": "SELECT run_id, title, slug, status, attempts, error, updated_at FROM synth_jobs WHERE status IN ('failed','dead') ORDER BY updated_at DESC LIMIT 10"}'
```

**常见原因**:
- DEEPSEEK_API_KEY 失效 → GH Action 报错, 修 secret
- m3 content sensitive 触发 fail → 看 GH Issue 标签 `synth-dead`, 改 prompt 措辞后手动 re-claim
- 队列积压 (>5 个) → 临时改 `.github/workflows/synth.yml` 的 `--max 3` 提高并发

### Q3: 用户看到 HTML 但 js/css 死链?

**原因 99%**: `render_bridge.py` 没跑路径转换 / 或 inject 改 curated 后没 sync public

**修法**:

```bash
# 重新跑 render 单篇
python3 -c "
import sys; sys.path.insert(0, '.')
from scf.synth.render_bridge import render_html
import json
data = json.loads(open('skills/gaokao-major-explorer/data/curated/<slug>.json').read())
render_html(data, '<slug>', data.get('style', 'humanities'))
print('✓ re-rendered')
"

# 验证 public 路径已转绝对
head -20 public/<slug>.html | grep -E 'src=|href='
# 应该是 /js/... 或 /css/... 而不是 ../../js/...
```

### Q4: 大量用户刷不同 slug, 队列爆了?

**临时方案**:

```bash
# 看队列大小
curl "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/d1/database/$CF_D1_DATABASE_ID/query" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -d '{"sql": "SELECT COUNT(*) as n FROM synth_jobs WHERE status='queued'"}'

# 临时清理 (确认是真垃圾)
curl ... -d '{"sql": "DELETE FROM synth_jobs WHERE status='queued' AND created_at < datetime('now','-1 hour')"}'
```

**根因方案**: rate limit 已经 60s/IP, 若仍爆 → 临时改 `functions/api/synth/generate.ts` 的 RATE_LIMIT_MS 到 300_000 (5min)

---

## 3. 手动触发单篇合成 (调试 / 抢救)

```bash
# 设环境变量
source .env
export CF_ACCOUNT_ID=...
export CF_API_TOKEN=...
export CF_D1_DATABASE_ID=...
export DEEPSEEK_API_KEY=...
export GITHUB_TOKEN=...

# 直接调 worker (不走 queue)
python3 scripts/synth_trigger.py --title "翻译" --slug translation --style humanities --skip-search

# 半 pipeline 模式 (已有 JSON, 只想 render + manifest)
python3 scripts/synth_trigger.py --from-json skills/gaokao-major-explorer/data/curated/translation.json --json-style humanities

# 通过 GH Action workflow_dispatch (走完整队列)
gh workflow run synth.yml -f slug=translation -f title=翻译
```

---

## 4. 数据巡检 (每天 1 次)

### D1 健康

```sql
-- 队列深度 (理想 <3)
SELECT COUNT(*) FROM synth_jobs WHERE status='queued';

-- 24h 内失败率 (理想 <15%)
SELECT
  COUNT(CASE WHEN status IN ('done') THEN 1 END) as done,
  COUNT(CASE WHEN status IN ('failed', 'dead') THEN 1 END) as failed,
  ROUND(100.0 * COUNT(CASE WHEN status IN ('failed', 'dead') THEN 1 END) / COUNT(*), 1) as fail_pct
FROM synth_jobs WHERE created_at > datetime('now', '-1 day');

-- 平均耗时 (理想 <120s)
SELECT AVG(
  (julianday(finished_at) - julianday(started_at)) * 86400
) as avg_sec
FROM synth_jobs
WHERE status='done' AND finished_at > datetime('now', '-1 day');

-- 累计成本
SELECT SUM(cost_cny) as total_cost_cny FROM synth_jobs WHERE status='done';
```

### GitHub Issues

- 标签 `synth-dead` 应该有 issue (运营每天扫)
- 标签 `user-request` 增长数 (用户上报未收录的)
- 标签 `synth-dead` 如果 1 周 >5 个 → 提级 session review prompt

---

## 5. 常见调整

### 加新 provider 到 fallback 链

```python
# scf/synth/llm.py:430
def get_client_with_fallback(chain=("m3", "deepseek"), ...):
    # 加 provider: 在 chain 加字符串 + 在下面 if/elif 加分支
    if provider == "新provider":
        client = 新Client(...)
```

### 调整 rate limit

```typescript
// functions/api/synth/generate.ts
const RATE_LIMIT_MS = 60_000;  // 改这里
```

### 调整 polling interval (前端)

```javascript
// public/js/pc-search.js (mobile: m/js/search.js)
}, 3000);  // 改这里, 3s → 5s 减少 serverless 调用
```

---

## 6. 事故回滚

```bash
# 1. 关掉 GH Action (不再拉新队列)
# .github/workflows/synth.yml 加 if: false 到 jobs.drain.if

# 2. CF Pages Function 仍然可以入队 (但没人处理)
# 想完全停: 临时改 functions/api/synth/generate.ts return {ok:false, error:"维护中"}

# 3. 回滚前端 (用户看不到按钮)
git revert <feat(synth) commit>
git push origin main
# CF Pages 自动 rebuild, ~30s 后用户看到旧版
```

---

## 7. 升级 checklist (下次迭代时)

- [ ] 把 rate limit 改 KV 持久化 (H12 KV namespace 已预留 binding, 解开注释即可)
- [ ] 加 `audit_content_relevance` inline 到 worker Step 5 (防 title↔content 漂移, 0 额外代码 scf/synth/audit.py 已就绪)
- [ ] 加 5 篇 smoke fixture 到 `docs/PIPELINE_major_quality.md` §🧪
- [ ] 加前端 progress bar (进度条 0-100% 替代 4 段文字)
- [ ] 加 mimo 到 fallback 链 (待 mimo 配额稳定后)
- [ ] 加 retry_on_transient (HTTP 5xx 时 worker 不算 attempts)

---

**最后更新**: 2026-06-19 (Day 7 v1.4 上线)
**关联 plan**: `/Users/zhewenliu/.claude/plans/moonlit-sleeping-planet.md`
**关联 memory**: 多个 hot memory 关于 synth/audit/D1/manifest 的, 搜 `synth` 即可定位