# Day 47 Plan: Launch Checklist (SEO final / Cache final / Deploy final)

> **目标**: 上线前必做清单 — 让 majorexplorer 可 production-ready
> **估时**: 5-7h (1-2 session)
> **前置**: Day 46 8+ 比例 98.6% / never_audited 0 / 22 commits pushed / main branch clean

---

## 📊 Day 46 末起点

| 指标 | 数值 |
|------|------|
| 8+ 比例 | **98.6%** (632/641) |
| never_audited | **0** |
| 总 audited | 641 (含 17 external) |
| irreducible flag | 19 篇 (8+7) |
| 主分支 ahead origin | 0 (Day 42-46 22 commits 已 push) |
| CF Pages 自动 deploy | 应已触发 |

---

## 🎯 3 大块 (按 ROI 排)

### **Phase 1: SEO Final (估 2-3h)**

| 任务 | 估时 | 工具/参考 |
|------|------|-----------|
| **1.1** Playwright 全量验证 (主页+13 门类+30 major+search+recommend) | 1h | `npx playwright screenshot`, `playwright-cli` |
| **1.2** meta description / title / og 全 633 页检查 | 30 min | `scripts/build/inject_seo.py` (Day 30 已建) |
| **1.3** sitemap.xml 生成 + 提交 (633 URL) | 15 min | `scripts/build_sitemap.py` |
| **1.4** JSON-LD 检查 (Course + BreadcrumbList + Organization) | 30 min | curl + grep |
| **1.5** 404 闭环 (任何死链) | 15 min | `wrangler pages deploy` + `curl -I` |
| **1.6** robots.txt + Plausible 域 cross-check | 15 min | curl |

**Deliverable**: docs/SEO_FINAL_DAY47.md (验证报告 + 修复列表)

### **Phase 2: Cache Final (估 1.5-2h)**

| 任务 | 估时 | 工具/参考 |
|------|------|-----------|
| **2.1** sw.js CACHE_NAME bump (Day 35+ 4h 兜底 SOP) | 15 min | `public/sw.js` 改版本号 |
| **2.2** _headers 5/5 security headers verify | 15 min | `curl -I` |
| **2.3** Cache-Control 关键资源 (HTML no-store, JS/CSS immutable) | 30 min | `_headers` + deploy.sh Step 5.5 |
| **2.4** CF Pages CDN cache 验证 (HTML/JS/CSS 4 层) | 30 min | `curl -I -H 'Cache-Control: no-cache'` |
| **2.5** deploy.sh 跑 1 次 (验证 4 层锁死 SOP) | 30 min | `bash scripts/deploy.sh "Day 47 cache final"` |

**Deliverable**: docs/CACHE_FINAL_DAY47.md (4 层锁死 evidence)

### **Phase 3: Deploy Final (估 1-1.5h)**

| 任务 | 估时 | 工具/参考 |
|------|------|-----------|
| **3.1** CF Pages Functions 验证 (recommender / search / report) | 30 min | `wrangler pages dev` + curl |
| **3.2** 移动端 UA sniff + /m/ 路径 4 顶层页验证 | 30 min | Playwright iPhone UA |
| **3.3** 桌面端 1280 验证 (12 主题 hero + 详情页) | 30 min | Playwright desktop UA |
| **3.4** 微信分享 / 复制 URL 兜底 (Day 35.7 fix verify) | 15 min | 浏览器实测 |
| **3.5** Final deploy (production) + CF Analytics + Plausible 验证 | 30 min | `bash scripts/deploy.sh` + 24h wait |

**Deliverable**: docs/DEPLOY_FINAL_DAY47.md (launch ready sign-off)

---

## 🛡️ 风险 + 应对

| 风险 | 应对 |
|------|------|
| CF Pages deploy 偶发 fail (Day 32 教训) | `wrangler pages deploy public/` 手动 + curl date |
| Cache 4 层不锁死导致旧 HTML | `deploy.sh` Step 5.5 自动验证, fail = abort |
| Playwright 浏览器未装 | `npx playwright install chromium` 先装 |
| mobile UA sniff 跨 worktree 干扰 | git stash + git pull + 独立 session |
| Plausible 域错 (pro plan endpoint) | 已 Day 23 修, 验证 DOM 即可 |

---

## 🎯 验收标准

| 指标 | 目标 |
|------|------|
| Playwright 桌面 + mobile 截图 | 100% 通过 (无 layout 错位/404/console error) |
| meta description 完整 | 633/633 页 ≥80 字 |
| sitemap.xml | 633 URL, 无 404 |
| _headers security | 5/5 (CSP / X-Frame / X-Content / Referrer / Permissions) |
| Cache-Control | HTML no-store, JS/CSS 1y immutable |
| CF Pages Functions | 3/3 (recommender/search/report) 200 OK |
| Plausible | 17 页 script 注入, 域对 |

---

## 📋 Day 47 启动流程 (新 session)

1. `git pull` (主 session)
2. `cat docs/PLAN_day47.md` (本 plan 复习)
3. Phase 1 SEO: Playwright 全量 → meta/sitemap/JSON-LD/404/robots
4. Phase 2 Cache: sw.js bump → _headers verify → Cache-Control → deploy.sh 跑
5. Phase 3 Deploy: Functions + UA sniff + desktop + 微信 + final deploy
6. 24h 后看 Plausible 访问数据, 验证真上线

---

## 💡 与 Day 42-46 区别

**Day 42-46 是修"内容质量"**:
- 主观 KPI: m3 audit score
- 18 polish + 19 flag + 30 R0 audit
- 8+ 比例 94.0% → 98.6%

**Day 47 是修"上线工程"**:
- 客观 KPI: SEO / cache / deploy 验证
- 1 commit per fix
- 目标 production-ready sign-off

---

## 🚨 不做的事 (避免 scope creep)

- ❌ 改内容 (Day 42-46 已 polish)
- ❌ 新增 major JSON
- ❌ 改 hero 主题 (Day 36 已 ship)
- ❌ 跨 worktree 操作 (Day 32 教训)

---

**生成时间**: 2026-06-29 20:25 (Day 46 push 后)
**Branch**: main (clean, origin 同步)
**前置依赖**: Day 46 22 commits pushed (GitHub verified)