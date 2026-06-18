# 在线按需合成 — 上线 Checklist (Day 7 v1.4)

> 部署到生产 (majorexplorer.com) 前必走 7 步. 已完工项 ✅, 待办 ☐.

## 1. 基础设施 ☐

- [ ] CF Pages D1 database 创建: `npx wrangler d1 create synth-jobs` → 拿 `database_id`
- [ ] wrangler.toml 填 `database_id` (当前已 hardcode `c74a412b-...`, verify 没变)
- [ ] D1 schema 迁移: `npx wrangler d1 execute synth-jobs --file=./migrations/0001_init.sql`
- [ ] verify: `npx wrangler d1 execute synth-jobs --command="SELECT COUNT(*) FROM synth_jobs"`

## 2. Secrets ☐

CF Pages Dashboard → Settings → Environment variables (Production):
- [ ] `GITHUB_TOKEN` (fine-grained, repo: Issues Read+Write)
- [ ] `GITHUB_REPO` (格式 `owner/repo`)

GH Action repo Settings → Secrets:
- [ ] `DEEPSEEK_API_KEY` (LLM 合成用)
- [ ] `CF_ACCOUNT_ID`, `CF_API_TOKEN`, `CF_D1_DATABASE_ID` (D1 REST 写入)
- [ ] `GITHUB_TOKEN` (synth-dead 上报用, 可与上面同一个)

## 3. 推送 + 部署 ☐

- [ ] 确认所有 commit 已 push: `git push origin main`
- [ ] CF Pages 自动 rebuild (~30s): Dashboard → Pages → 查看最新 deployment
- [ ] verify CF Pages Function 加载:
  ```bash
  curl -X POST https://majorexplorer.com/api/synth/generate \
    -H "Content-Type: application/json" \
    -d '{"title": "翻译", "source": "pc"}'
  # 期望: {"ok":true, "run_id":"...", "status":"queued", "status_url":"/api/synth/status?run_id=..."}
  ```
- [ ] verify D1 入队: 上面命令后立刻:
  ```bash
  curl "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/d1/database/$CF_D1_DATABASE_ID/query" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -d '{"sql": "SELECT run_id, title, slug, status FROM synth_jobs ORDER BY created_at DESC LIMIT 3"}'
  ```

## 4. GH Action ☐

- [ ] verify GH Action 启用: `.github/workflows/synth.yml` 已在 main
- [ ] verify cron trigger: GH Action tab → synth-queue-worker → 最新 run 应每分钟跑 1 次
- [ ] 手动 trigger 1 次 (测活):
  ```bash
  gh workflow run synth.yml -f slug=translation -f title=翻译
  ```

## 5. 端到端 (Playwright / curl) ☐

- [ ] PC search: 访问 `https://majorexplorer.com/search.html?q=翻译`
  - 期望: 看到「🔄 实时生成这篇」+「📨 报告给我们」2 个按钮
- [ ] 点「🔄 实时生成这篇」→ 看 4 段进度文案
- [ ] ~90s 后跳到 `/translation.html` → 看 HTML 内容完整 (curriculum/salary/alumni 都有)
- [ ] 移动端同 3 步

## 6. 失败降级 ☐

- [ ] 测 rate limit: 1 分钟内连发 2 次 → 第 2 次返 429
- [ ] 测失败上报: 模拟 DEEPSEEK_API_KEY 删掉 → GH Action 报错 3 次 → 应自动 createIssue 标签 `synth-dead`
- [ ] 测 fallback: 故意改错 m3 client 配置 → 自动降级 deepseek

## 7. 监控 ☐

- [ ] 装 GH Action cron 跑 synth_monitor.py 每天 9:00 (可选)
- [ ] GH Issue 标签 `synth-dead` 关注 (运营每天扫)
- [ ] CF Web Analytics 看 `/api/synth/*` 调用数 (验证真有人在用)

---

## 上线后 24h 监控 checklist

- [ ] GH Action synth.yml 跑了 ≥20 次 (1 分钟 * 60 * 24 / 20min/queue buffer)
- [ ] D1 synth_jobs 表 ≥5 条新 done 记录
- [ ] 失败率 < 15% (synth_monitor.py 输出)
- [ ] 平均耗时 < 120s
- [ ] 累计成本 < ¥20 (按 5 篇 × ¥1.6 + 部分 retry 估)
- [ ] 没有 synth-dead GH Issues 自动创建 (或 < 3 个, 都属可解释范围)
- [ ] 用户提交率 > 0 (有人用按钮了)
- [ ] 前端 polling 没报错 (CF Pages Function 日志)

---

**完成时间**: 2026-06-19 (Day 7)
**关联**: `docs/PIPELINE_major_quality.md` v1.4 + `docs/PLAN_on_demand_synth.md` 运营手册