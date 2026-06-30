# DEPLOYMENT.md — Major Explorer 海外直链部署方案 v2

> **状态**: 方案已定型, 实施进行中

## 📅 物理日期映射 (Day N → YYYYMMDD)

> "Day N" 是历史 Claude 估算日期. 遇 Day N 翻此表即查真实日期.

| Day | 日期 | 备注 |
|---|---|---|
| Day 31 | 20260627 | deploy.sh 7 步定型 |
| Day 32 | 20260625 | Cache 三层陷阱 SOP (Day 32 教训) |
| Day 35-47 | 20260629 | mobile PWA / SEO / 校友脱敏 |

**未来 commit 规则**: 必用 `YYYYMMDD [session]` 格式, 不用 Day N. 详见 `docs/COMMIT_CONVENTION.md`.
> **最后更新**: 2026-06-12
> **对应 ADR**: ADR-011 (过期) → ADR-016/017/018/019
> **对应 plan**: `/Users/zhewenliu/.claude/plans/gentle-stargazing-hartmanis.md` (这份是项目内 mirror)

## Context (为什么重做)

2026-06-12 重新校准后, 部署策略发生 **5 项重大变动**:

| 旧方案 (ADR-011 ~ 015) | 新方案 (v2) | 变化原因 |
|------------------------|-------------|----------|
| `.cn` 双持 (.cn + .com) | `majorexplorer.com` 单持 | 2 字 .cn 全军覆没, 英文 .com 跟 index.html 品牌一致 |
| EdgeOne Pages 两阶段 (海外 → 大陆) | **Cloudflare Pages 单阶段** | 用户明确不做微信/SEO/变现, 备案价值消失 |
| 7-15 天 ICP 备案 (阿里云轻量) | **短期不做** | 错过 6/23 出分高峰, 公益项目无商业化需求 |
| 备案后切到大陆节点 | **永久海外**, 优选 IP 解决 | Cloudflare 国内有 21 接入商, 30-100ms 足够 |
| 备案主体 = 阿里云轻量 2C4G | **不备案**, 留作未来 | — |

**核心场景校准**:
- 100% 国内用户 (高三学生 + 家长)
- 公益, 不变现, 不做微信公众号
- 不做 SEO 长尾积累 (一年流量高峰就几天)
- 海外需求 = 0
- **不备案 = 节省 7-15 天, 抢高考出分流量窗口**

## 项目实际结构 (2026-06-12)

| 模块 | 类型 | 是否可纯静态 | 上线状态 |
|------|------|--------------|----------|
| 68 个 `public/{slug}.html` (专业 dashboard) | 纯静态 | ✅ | 阶段 1 |
| `public/index.html` (主页, 380+ 行, "先专业后志愿"流程) | 纯静态 | ✅ | 阶段 1 |
| `public/css/shared.css` + 各主题 CSS | 纯静态 | ✅ | 阶段 1 |
| `public/js/wishlist-store.js` + UI helpers + 搜索 | 纯静态 | ✅ | 阶段 1 |
| `public/data/manifest.json` (68 精品元数据) | 纯静态数据 | ✅ | 阶段 1 |
| 临时搜索新专业 (LLM 合成) | **必须后端** (API key 保护) | ❌ 需 serverless | **阶段 2 (不阻塞)** |
| `scf/synth/` (后端 LLM 合成代码, 7 模块) | Python serverless | — | 阶段 2 |
| `data/` (投档表/一分一段/校专业关联) | 数据 | — | 阶段 1 (静态快照) |

**关键约束** (没变):
- Cloudflare Pages 是 **纯静态托管** (跟 EdgeOne Pages 一样, 不能跑 Python)
- LLM API key 不能暴露在浏览器 → 临时搜索必须 serverless
- **68 个 dashboard + 主页可以独立上线**, 不依赖 LLM 后端

## 决策记录 (新, 2026-06-12)

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 域名 TLD | **`.com`** | 英文名 `MajorExplorer` 已根植于 `index.html`/og/sitemap, 单持最一致 |
| 域名注册商 | **Cloudflare Registrar** | 成本价 $9.15/年 (永久不涨价), 跟 Pages 集成最顺 |
| 静态托管 | **Cloudflare Pages** | 21 接入商, 国内节点最广, 优选 IP 后 30-100ms, 免费层够用 |
| 国内访问优化 | **Cloudflare 优选 IP** (民间方案) | 30 分钟跑出 top 5 IP 写入 DNS, 30-100ms |
| DNS 管理 | **Cloudflare DNS** (强制) | 注册即用, 优选 IP 写入最方便 |
| ICP 备案 | **不做** (短期) | 公益不变现, 微信不做, 备案价值不抵时间成本 |
| 微信生态 | **不做** | 公益项目 |
| SEO 长尾 | **不主动做** | 一年几天流量高峰, 长尾 ROI 低 |
| 商业化 | **不做** | 纯公益, 0 变现 |
| LLM 搜索后端 | **SCF 香港** (保留 ADR-012) | 0 成本, 10万次/月免费, 无需备案 |
| SCF 部署时点 | **阶段 2**, 不阻塞阶段 1 | 静态站先上, LLM 搜索后置 |
| 备案 | **保留 ADR-018, 019 备用** | 未来若有需要时启用 |

## 架构 (v2)

```
浏览器 (国内 16-22 岁高三生 / 35-50 岁家长)
  ↓ DNS 解析到 Cloudflare 优选 IP (国内 30-100ms)
majorexplorer.com (HTTPS)
  ↓
Cloudflare Pages (全球 CDN, 国内 21 接入商节点)
  ├── public/index.html (主页, "先专业后志愿" 流程)
  ├── public/{68 个 slug}.html (精品专业 dashboard)
  ├── public/css/ (12 主题 CSS)
  ├── public/js/ (wishlist + 搜索 + UI helpers)
  ├── public/data/manifest.json (68 精品元数据)
  └── public/data/curated/*.json (各专业精编数据)
  
  阶段 2 后端 (不阻塞阶段 1):
  ↓ fetch('/api/search-major?q=...')
  ↓
腾讯云 SCF (香港地域, 无需备案)
  ├── 入口: POST /search-major
  ├── 鉴权: 简单 rate-limit (按 IP)
  ├── 调 DeepSeek API (scf/synth/llm.py, raw HTTP 修复后)
  └── 合成 HTML 片段 + 简单结构化字段
```

**跟 v1 架构的关键差异**:
- ❌ 删了 EdgeOne Pages / 两阶段切换 / 阿里云备案
- ❌ 删了"阶段二迁移到大陆节点"流程
- ✅ 加入 Cloudflare 优选 IP 机制
- ✅ 加入 LLM 后端可后置的解耦设计

## 实施步骤

### 阶段 0: 准备工作 (今天 6/12, 30 分钟)

**0.1 注册域名**
- 平台: Cloudflare Registrar
- URL: https://dash.cloudflare.com → Add a Site → Register Domains
- 搜 `majorexplorer.com` → 加购物车 → 付款 (Visa/Mastercard/PayPal)
- 预计 5 分钟

**0.2 准备 DNS**
- Cloudflare 自动接管域名 DNS
- 暂时加占位 A 记录 → `192.0.2.1` (TEST-NET-1, RFC 5737, 不会真解析)
- 阶段 1 部署后改成 Cloudflare Pages 分配的 IP 或 CNAME

**0.3 准备 git push** (用户做)
- 仓库: GitHub 个人仓库 (已有, gh CLI 可用)
- 当前工作树有未提交改动 (manifest + 8 新 HTML + scf/synth/raw HTTP 修复), 隔壁修复完后一起 push
- 推送后 Cloudflare Pages 自动部署

### 阶段 1: 静态站上线 (今天, 1-2 小时)

**1.1 创建 Cloudflare Pages 项目**
1. Cloudflare Dashboard → Workers & Pages → Create application → Pages
2. 选 "Connect to Git" → 选 GitHub → 授权 → 选 `gaokao-hubei-mvp` 仓库
3. 项目名: `majorexplorer` (生成 `majorexplorer.pages.dev` 临时 URL)
4. 构建配置:
   - Build command: **留空** (无构建, public/ 已是产物)
   - Build output directory: `public`
   - Root directory: `/` (项目根, 不是 public/)
5. 点 Save and Deploy → Cloudflare 自动 git clone + 部署 → 30 秒拿到 `majorexplorer.pages.dev`

**1.2 绑定自定义域名**
1. Pages 项目 → Custom domains → Set up a custom domain
2. 输入 `majorexplorer.com` → Cloudflare 自动检查 DNS → 一键添加
3. 自动签发 SSL 证书 (Let's Encrypt, 1-2 分钟)
4. 验证: 浏览器打开 `https://majorexplorer.com` → 应该能看到主页

**1.3 验证清单**
```bash
# DNS 解析
dig majorexplorer.com A +short
# 期望: Cloudflare 的 IP 段 (104.16.x.x ~ 172.64.x.x)

# HTTPS 状态
curl -I https://majorexplorer.com
# 期望: HTTP/2 200, server: cloudflare

# 主页
curl -s https://majorexplorer.com | grep "Major Explorer"
# 期望: <title>看清专业,再谈志愿 · Major Explorer ...

# 68 个 dashboard 抽样
for slug in accounting auditing clinical-medicine public-order; do
    status=$(curl -o /dev/null -s -w "%{http_code}" https://majorexplorer.com/${slug}.html)
    echo "${slug}: ${status}"
done
# 期望: 4 个都是 200

# 国内访问速度 (用户/朋友帮忙测)
# https://itdog.net 测速 → 国内三网 < 200ms 可接受 (优选 IP 后 < 100ms)
```

### 阶段 2: 优选 IP 加速 (今天-明天, 30 分钟)

**目的**: 把国内访问从默认 200-300ms 优化到 30-100ms

**步骤**:
1. 跑 `deploy/optimal-cf-ip.sh` (本文档配套脚本)
2. 脚本会:
   - 下载 Cloudflare 公开 IP 段
   - 用 TCP ping 测速找出 top 5
   - 调用 Cloudflare DNS API 写入 A 记录
3. Cloudflare DNS 自动生效 (TTL 300s, 5 分钟内全球生效)
4. 复测国内访问: 应该降到 30-100ms

**长期维护**: IP 偶尔会变, 每月跑一次脚本即可。

### 阶段 3: LLM 搜索后端 (后续, 不阻塞)

**触发条件**: 用户主动说要部署, 或有真实用户开始搜未收录专业。

**部署目标**: 腾讯云 SCF (香港地域, 沿用 ADR-012)

**简化路径** (跟 v1 几乎一样):
1. 腾讯云账号 → SCF → 新建函数 → 地域"香港" → 运行时 Python 3.11
2. 上传 `scf/synth/` 整个目录 + `scf/template.yaml` (略改 trigger 路径)
3. 环境变量注入 `DEEPSEEK_API_KEY` (从 scf/synth/llm.py 看, 用 raw HTTP 调, 0 SDK 依赖)
4. API 网关触发器 → 路径 `/synth/*` → CORS 允许 `https://majorexplorer.com`
5. 前端 `public/js/synth-client.js` 已有轮询逻辑 (commit f494378), 把 base URL 指向新 SCF

**月成本** (按 v1 估算):
- SCF 香港: 1 万次调用 → ¥0 (免费层 10万次/月)
- DeepSeek API: 1 千次搜索 × 2K token → ~0.5 元/月

**重要**: LLM 后端**上线后**前端 `index.html` 的"未收录专业"搜索才能用。**不部署也能正常服务** (68 个 dashboard 全部本地化, 不依赖后端)。

### 阶段 4: 备案 (6 个月后再议, 触发条件驱动)

**当前明确不做**。但保留未来选项:

**触发条件 (任一满足才启动备案)**:
- 微信公众号/小程序嵌入需求 (用户: 当前不做)
- 国内 CDN 大幅提速需求 (用户: 优选 IP 够用)
- 与国内机构合作需要备案号 (出版社/教育局)
- 商业化 (广告/付费/咨询 — 用户: 纯公益不变现)

**备案时主体** (ADR-019): 普通个人身份。

## 关键文件清单

### 阶段 1 必改 (本周末)

| 文件 | 改动 | 说明 |
|------|------|------|
| `public/data/manifest.json` | `site_name` / `og:site_name` → "Major Explorer" | 跟 index.html 品牌统一 |
| `public/index.html` | `<link rel="canonical">` / `<meta property="og:url">` | 改成 `https://majorexplorer.com` |
| `public/data/manifest.json` (每个 major 的 `html_path`) | 不变 | 已经是相对路径, Cloudflare Pages 自动处理 |
| `public/robots.txt` | Sitemap URL 改成 `https://majorexplorer.com/sitemap.xml` | (如有) |
| `public/sitemap.xml` | 所有 URL 改成 `https://majorexplorer.com/...` | (如有) |

### 阶段 1 配套新建

| 文件 | 路径 | 说明 |
|------|------|------|
| Cloudflare Pages 部署操作指南 | `deploy/cloudflare-pages.md` | 阶段 1.1-1.3 详细截图级步骤 |
| 优选 IP + DNS 同步脚本 | `deploy/optimal-cf-ip.sh` | 阶段 2 一键跑出 top 5 IP + 写 DNS |

### 阶段 1 不动

- 68 个 `public/{slug}.html` (已是产物, 直接部署)
- `public/css/` (12 主题 CSS)
- `public/js/` (wishlist + 搜索 + UI)
- `public/data/curated/*.json` (各专业精编数据)
- `scf/synth/` (后端代码, 阶段 3 才用)

### 阶段 3 改 (后置)

- `scf/template.yaml` (改 trigger path + CORS)
- `public/js/synth-client.js` (base URL 改 Cloudflare Pages 子路径)

## 阶段 1 验证清单 (6/12 上线后)

- [ ] `dig majorexplorer.com A +short` 返回 Cloudflare IP
- [ ] `https://majorexplorer.com` 浏览器打开, 看到 "看清专业,再谈志愿 · Major Explorer 2026 高考 (湖北)" 主页
- [ ] 主页 "精品" 区块显示 68 个专业卡片
- [ ] 点击任一专业卡片 → 跳到 `/{slug}.html` → 看到该专业 dashboard
- [ ] 主页 "心愿单" 按钮 + "搜专业" 框可交互
- [ ] 顶部 "12 主题" 切换可工作
- [ ] `curl -I https://majorexplorer.com` 返回 200 + server: cloudflare
- [ ] `https://itdog.net` 国内三网测速 < 300ms (优选 IP 前) / < 100ms (优选 IP 后)
- [ ] 浏览器开发者工具 → Lighthouse 跑分: Performance > 80, SEO > 90, Best Practices > 90
- [ ] `https://majorexplorer.com/sitemap.xml` 可访问 (如有)
- [ ] `https://majorexplorer.com/robots.txt` 可访问 (如有)

## 风险与缓解 (v2 重新评估)

| 风险 | 概率 | 缓解 |
|------|------|------|
| Cloudflare 节点晚高峰跳到美西 | 中 | 优选 IP 5 个, DNS TTL 300s 切换 |
| 国内 ISP 路由偶发拥堵 | 中 | Cloudflare 21 接入商覆盖, 单点故障率低 |
| 域名被抢注 | 极低 | 已在 6/12 注册, 续费不涨价 |
| Cloudflare Pages 流量超额 | 极低 | 免费层 5 万次/月, 出分当天估 1-3k 次 |
| LLM 后端没部署影响搜索 | 低 | 68 个精品已本地化, "搜未收录" 不可用, 但主功能无影响 |
| 突发流量打爆 (某省份家长群传开) | 低 | Cloudflare Pages 免费层 + Workers Limits 兜底 |
| Cloudflare 账号风控 (新注册+无信用卡) | 极低 | 用户用信用卡, 风控概率极低 |
| 国内 GFW 干扰 | 极低 | 纯教育内容, 无政治敏感词 |
| 浏览器 HTTPS 证书失败 | 极低 | Cloudflare 自动 Let's Encrypt, 1-2 分钟 |

## 开放问题 (等用户回 Cloudflare 注册后明确)

1. LLM 搜索后端的部署时点: 阶段 3 一周内 vs 等真实用户触发?
2. 内容更新流程: GitHub push 自动部署 (Cloudflare Pages 默认) vs 手动 approve?
3. 是否需要 Google Analytics / Plausible 埋点? (用户: 公益无变现, 可能不需要)
4. 是否加 favicon? (现 `index.html` 已有 inline SVG, 应该 OK)
5. 6/25 出分当天如何监控? (Cloudflare Analytics 自带)
6. 微信公众号保留作为 "出分日推文引流到 majorexplorer.com" 通道? (用户: 不做)

## 决策记录 (新, 2026-06-12)

- **2026-06-12 上午**: 域名调研, 2 字中文 .cn 全部被注
- **2026-06-12 中午**: 决定 `majorexplorer.com` 单持 (Cloudflare Registrar)
- **2026-06-12 中午**: 决策 Cloudflare Pages (海外免备案, 优选 IP 国内 30-100ms)
- **2026-06-12 中午**: 决策短期不做 ICP 备案 (公益+不变现+不微信)
- **2026-06-12 下午**: 写 v2 部署文档 (本文件) + 优选 IP 脚本 + Cloudflare Pages 操作指南

## 推进节奏 (跟用户对齐)

- **用户**: Cloudflare 注册 + 等隔壁修完前端 + git push
- **AI (我)**: 文档 + 部署指南 + 优选 IP 脚本 ✅
- **联调**: 用户 git push → Cloudflare Pages 自动部署 → 验证 → 优选 IP → 完成
- **目标时间线**: 6/12 当天 `https://majorexplorer.com` 可访问, 抢 6/13-6/25 高考结束-出分空档

---

## ⚠️ 强制必读: Cache 三层陷阱 & 部署 SOP (2026-06-25 Day 32 新增)

**这一节是血泪教训, 任何改 JS/HTML/CSS 的部署前必读.**

### 症状: 代码改了, 用户看不到

部署某次 commit 后, 作者自己看是新版, 用户的浏览器还显示老版. 强刷 (`Cmd+Shift+R`) 才看到. **这不是用户问题, 是部署漏了 cache 失效步骤.**

### 根因: 4 层 cache 同时锁死

| 层 | 谁管 | 怎么失效 |
|---|---|---|
| 1. **CF 边缘 HTML cache** | Cloudflare | cache-bust `?v=<新 hash>` 让 URL 不同 |
| 2. **CF 边缘 JS 静态资源 cache** | Cloudflare | cache-bust `?v=<git SHA>` 永久唯一,不用语义版本 |
| 3. **浏览器 disk cache** | 浏览器 | `Cmd+Shift+R` / Disable cache / 隐身窗口 |
| 4. **Service Worker cache (含 sw.js 自身)** | `public/sw.js` `CACHE_NAME` | **两件事一起**: CACHE_NAME 升版 + `_headers` `/sw.js` 设 `no-store` |

**第 4 层子陷阱 (最隐蔽)**: `/sw.js` 路径被 `_headers` 兜底 `/*` 规则设了 `Cache-Control: public, max-age=14400, must-revalidate`. 浏览器 4 小时内不会感知 sw.js 文件变化,即使 sw.js 改了 CACHE_NAME 浏览器也不知道 → 老 SW 一直运行 → staleWhileRevalidate 锁死老 JS.

**为什么隐身窗口能看**: Safari/Chrome 隐私模式**禁用整个 Service Worker API**,所有 fetch 走网络. 这反而成了**诊断工具** — 隐身能看到 ≠ 真修复.

### 解决: 永远跑 `scripts/deploy.sh` + `_headers` 必备

```bash
# ✅ 正确: 一行部署, 自动 bump cache-bust + sw.js CACHE_NAME
bash scripts/deploy.sh "fix(search): xxx"

# ❌ 错误: 手动 git push 绕过, 漏 SW 升版
git add -A && git commit -m "fix" && git push origin main
```

`scripts/deploy.sh` 自动完成 7 步 (Day 31 + Day 32 增强):
1. 检查 git 状态 (有未提交改动?)
2. 检查 `public/data/` modified files 漏 add (CF Pages serve 老版致命)
3. 生成 cache-bust query (`?v=<git short SHA>` 永久唯一)
4. 替换所有 HTML 的 `?v=老值` → `?v=<新 SHA>` (PC + Mobile 一起)
5. **🆕 Day 32: 升版 `sw.js` CACHE_NAME → `explorer-v?<SHA>`** ← 关键
6. 验证替换完整 (无残留老 query / 老 CACHE_NAME)
7. `git add + commit + push origin main` → CF Pages auto deploy

### 验证部署成功 (4 步)

```bash
# 1. 确认 git push 成功
git log --oneline -3  # 看到自己刚 commit

# 2. 确认 CF sw.js 已升版 (等 1-2 min)
curl -s https://majorexplorer.com/sw.js | grep CACHE_NAME
# 期望: const CACHE_NAME = "explorer-v?-<新 SHA>"

# 3. 确认 cache-bust 已替换
curl -sL https://majorexplorer.com/search.html | grep "pc-search.js"
# 期望: /js/pc-search.js?v=<新 SHA>

# 4. 用户浏览器清 SW (一次性, 部署后第一次访问)
# F12 → Application → Service Workers → 勾 "Update on reload" → 刷新
# 或: 隐身窗口 (Cmd+Shift+N) 打开 → 必看新版
```

### 用户报"看不到新版" 排查 4 步

```bash
# Step 1: CF 有新 file 吗?
curl -sI https://majorexplorer.com/js/pc-search.js | head -3
# 期望: HTTP/2 200

# Step 2: SW CACHE_NAME 升版了吗?
curl -s https://majorexplorer.com/sw.js | grep CACHE_NAME
# 期望: 含最新 SHA, 不含 "explorer-v1-20260622a" 老值

# Step 3: HTML 引用新 cache-bust 吗?
curl -sL https://majorexplorer.com/index.html | grep "pc-search.js"
# 期望: ?v=<新 SHA>

# Step 4: 用户 SW 升级了吗? (DevTools → Application → Service Workers)
# 看到 SW 是 "activated and is running" + 最新 CACHE_NAME → OK
# 看到 SW 还是老 CACHE_NAME → 让用户点 "Unregister" + 刷新
```

### Day 32 真实案例 (2026-06-25, 4 commit 递进)

| Commit | 改了什么 | 修哪层 | 后果 |
|---|---|---|---|
| `804c9568` | v4 同义词卡片 (8px 色块 + emoji 圆徽) | 内容本身 | 仅 Orca 干净环境看到 |
| `0cae3039` | `sw.js` CACHE_NAME → `v2-day32v4` + `deploy.sh` Step 4.5 | 第 4 层 (SW 自身) | 部分用户看到 |
| `ce7dec61` | `?v=day32v4` → `?v=<git SHA>` (永久唯一) | 第 2 层 (CF 边缘 JS) | 更多用户看到 |
| `da74453d` | `_headers` `/sw.js` `/m/sw.js` 设 `no-store` | 第 4 层子陷阱 (4h 兜底) | ✅ Chrome/Firefox 4h 内也能感知 SW 变化 |

**关键 takeaway**: 4 层 cache 必须**同时**失效,缺任一层用户都看不到.

### `_headers` 必备 2 个 no-store 路由

```text
/sw.js
  Cache-Control: no-store
/m/sw.js
  Cache-Control: no-store
```

如果 `_headers` 漏了这两条,所有 v1-v4 的 SW 升级都白搭 — 浏览器 4h 内不感知 sw.js 文件变化.

### 关联

- `~/.claude/projects/.../memory/day32-cache-trap-4layers.md` — 完整 4 层 memory
- `scripts/deploy.sh` — 一键部署脚本 (Step 4/4.5/5 自动 bump + 验证)
- `public/_headers` — 必备 2 个 no-store 路由
- 关联 commit: `804c9568` (内容) + `0cae3039` (SW 升版) + `ce7dec61` (SHA cache-bust) + `da74453d` (_headers no-store)
