# Bot Protection & WAF 配置指南

> **站点**: Major Explorer (gaokao-hubei-mvp)  
> **部署**: Cloudflare Pages  
> **目的**: 拦截 AI 训练爬虫 / 恶意 scraper, 保护 5713 个专业介绍页 + 471+ 篇精编内容 JSON
>
> **重要**: 本指南是 **人工操作** (CF Dashboard 鼠标点击), 不是代码改动. 预计 30 分钟一次完成.

---

## 现状 (2026-06-24 已落地)

| 防线 | 文件 | 状态 |
|---|---|---|
| 1. `robots.txt` 32 个 AI 训练 UA `Disallow: /` | `robots.txt` | ✅ 已部署 |
| 2. `X-Robots-Tag: noai, noimageai` 全站响应头 | `public/_headers` | ✅ 已部署 |
| 3. `llms.txt` 行业协议 | `public/llms.txt` | ✅ 已部署 |
| 4. `terms.html` §3.1 禁止 AI 训练条款 | `terms.html` | ✅ 已部署 |
| 5. **Cloudflare Bot Fight Mode** | CF Dashboard | ⏳ 待启用 |
| 6. **WAF 自定义规则 (UA 黑名单 → Block)** | CF Dashboard | ⏳ 待启用 |
| 7. **WAF 速率限制 (单 IP 60 req/min)** | CF Dashboard | ⏳ 待启用 |

> 前 4 项不需要 CF 账号, 已 git 跟踪. 后 3 项需登录 CF Dashboard, 5 分钟一步.

---

## Step 1: 启用 Bot Fight Mode (5 分钟)

> **免费**, 自动识别已知恶意爬虫. 不影响 Googlebot / Bingbot / 正常用户.

1. 登录 https://dash.cloudflare.com
2. 选中 `majorexplorer` (Pages 项目)
3. 左侧菜单 → **Security** → **Bots**
4. 找到 **Bot Fight Mode** → 点击 **Enable**
5. 弹窗确认 → **Confirm**

**验证**:
```bash
# 模拟已知坏爬虫
curl -I -A "Masscan/0.1" https://majorexplorer.com/

# 预期: HTTP/2 403
# 实际: Cloudflare 在边缘拦截, 返回 403 + cf-mitigated: challenge header
```

---

## Step 2: WAF 自定义规则 — AI 训练 UA 拦截 (15 分钟)

> **免费** (WAF 5 条以内免费规则够用), 直接在边缘 403 AI 训练爬虫.

### 2.1 进入 WAF

1. CF Dashboard → `majorexplorer` → **Security** → **WAF** → **Custom Rules** 标签
2. 点击 **Create rule**

### 2.2 规则 1: AI 训练爬虫黑名单 (核心)

| 字段 | 值 |
|---|---|
| **Rule name** | `Block AI training crawlers` |
| **Expression preview** | 见下 |
| **Action** | Block |

**表达式** (CF Rule Editor 用 AND/OR 拼装, 这里给 raw 形式):

```
(http.user_agent contains "GPTBot") or
(http.user_agent contains "ChatGPT-User") or
(http.user_agent contains "OAI-SearchBot") or
(http.user_agent contains "ClaudeBot") or
(http.user_agent contains "Claude-Web") or
(http.user_agent contains "anthropic-ai") or
(http.user_agent contains "Google-Extended") or
(http.user_agent contains "CCBot") or
(http.user_agent contains "Bytespider") or
(http.user_agent contains "ByteDance") or
(http.user_agent contains "GLM-Spider") or
(http.user_agent contains "PerplexityBot") or
(http.user_agent contains "Meta-ExternalAgent") or
(http.user_agent contains "Meta-ExternalFetcher") or
(http.user_agent contains "Applebot-Extended") or
(http.user_agent contains "Diffbot") or
(http.user_agent contains "Omgilibot") or
(http.user_agent contains "Omgili") or
(http.user_agent contains "DuckAssistBot") or
(http.user_agent contains "PetalBot") or
(http.user_agent contains "Kimi") or
(http.user_agent contains "QihooBot") or
(http.user_agent contains "Sogou-Spider") or
(http.user_agent contains "ImagesiftBot")
```

**UI 操作**: 在 CF Rule Editor 选 `Field = User Agent` → `Operator = contains` → 填 UA 字符串, 不断点 `OR` 加新行. 一次最多 24 个表达式一组.

### 2.3 规则 2: 速率限制 (单 IP)

| 字段 | 值 |
|---|---|
| **Rule name** | `Rate limit single IP` |
| **Expression** | `(ip.src eq 0.0.0.0/0)` 或留空 (默认匹配所有) |
| **Action** | Block (或 Challenge) |
| **Rate limit** | 60 requests per 1 minute |

**注意**: CF WAF 的 Rate limit 是付费功能 (Pro 计划 ¥0 不够, 需要 Business ¥-). 免费替代:
- 用 **Page Rule** 限制单 URL 速率
- 或先不上, 等真有滥用再开

### 2.4 规则 3: `/data/*.json` 额外保护 (可选)

> `/data/*.json` 是聚合数据, 普通用户很少直接访问. 加个 JS challenge 增加爬虫成本.

| 字段 | 值 |
|---|---|
| **Rule name** | `Challenge data JSON access` |
| **Expression** | `(starts_with(http.request.uri.path, "/data/"))` |
| **Action** | Managed Challenge |

**效果**: 人类直接点 manifest.json 链接, CF 弹 5 秒 JS challenge 后放行; 爬虫脚本不解 challenge 拿不到.

---

## Step 3: 验证 (10 分钟)

部署后用 curl 测一遍:

```bash
DOMAIN=https://majorexplorer.com

echo "=== 1. 正常用户 (Mozilla) ==="
curl -sI -A "Mozilla/5.0 (Macintosh)" $DOMAIN/ | head -5
# 预期: 200, 包含 X-Robots-Tag: noai, noimageai

echo ""
echo "=== 2. AI 训练爬虫 (应被 WAF 拦截) ==="
curl -sI -A "GPTBot/1.0" $DOMAIN/ | head -3
# 预期: 403, cf-mitigated 头

echo ""
echo "=== 3. Googlebot (不应拦截) ==="
curl -sI -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" $DOMAIN/ | head -3
# 预期: 200

echo ""
echo "=== 4. llms.txt (应 200) ==="
curl -sI $DOMAIN/llms.txt | head -3
# 预期: 200, text/plain

echo ""
echo "=== 5. robots.txt (应 200) ==="
curl -sI $DOMAIN/robots.txt | head -3
# 预期: 200

echo ""
echo "=== 6. /data/manifest_extras.json (honeypot 应 403) ==="
curl -sI $DOMAIN/data/manifest_extras.json | head -3
# 预期: 403 或 404 (不存在就 404; WAF challenge 也行)
```

---

## Step 4: 监控 (长期)

### 4.1 CF Analytics 看拦截数

CF Dashboard → `majorexplorer` → **Security** → **Events**:
- 过滤 `Action = Block`
- 筛选 `User Agent contains GPTBot` 等
- 每周看一次, 评估爬虫规模

### 4.2 蜜饵触发告警

`/data/manifest_extras.json` 是 honeypot — 没人会访问, 任何访问都视为爬虫:
- CF WAF 加规则: `URI Path = /data/manifest_extras.json` → Action = Log + Block
- 触发后查 IP 段, 手动加 Security → Tools → IP Access Rules

### 4.3 月度复盘

每月 1 号 review:
1. CF Security Events → Blocked by rule 统计
2. 哪些 UA 漏了 (有 Block 但 UA 不在列表) → 加到 WAF 规则
3. 误伤统计 (Googlebot / Bingbot 被拦次数) → 应该 0, 有就是规则写错

---

## 已知坑

### 坑 1: WAF 表达式里 `contains` 大小写敏感

`GPTBot` ≠ `gptbot`. 规则写错会漏掉 50% 流量. 建议**大小写都加**:

```
(http.user_agent contains "GPTBot") or
(http.user_agent contains "gptbot")
```

或者用 CF 提供的 `matches` (regex), 但 5 条免费规则用 contains 已经够.

### 坑 2: 合规爬虫会遵守 robots.txt 但 UA 暴露 (Google-Extended)

`Google-Extended` 是 Google 单独声明的 opt-out 爬虫. 拦截它**不影响** Googlebot 抓 SEO. 但有些 Google 子产品会发奇怪 UA, 拦截前先看 Analytics 确认.

### 坑 3: BitTorrent / Headless Browser 类的爬虫不在 32 个列表内

如 `PhantomJS/1.9` / `HeadlessChrome/120` — 这些是通用 UA, 无法精确拦. 靠 Bot Fight Mode 的 "Verified Bots" 自动识别, 加 WAF 兜底 `HeadlessChrome contains` 规则.

### 坑 4: 不要用 `(not http.user_agent contains "Mozilla")`

经典错误 — 移动端 / 微信 / 各种 App 都不会发 Mozilla 字符串, 误伤率 30%+.

### 坑 5: 速率限制规则会误伤办公室 NAT

公司 / 学校一个公网 IP 100+ 人共用, 60 req/min 太低. 建议:
- 默认 100 req/min / 5 min
- 真有问题再降到 60

---

## 后续可选升级 (Tier 2 / Tier 3)

| 项 | 时机 | 投入 |
|---|---|---|
| KV rate limit (在 Pages Function 里) | Tier 2 数据 fingerprint 之前 | 1 周 |
| 关键字段 (salary / alumni) 服务端签名 | 核心 IP 真被大批盗用时 | 2 周 |
| 登录墙 (核心数据需注册) | 转型 SaaS 时 | 4 周 |

详见对话: 静态站 → 动态后端重构评估.

---

## 联系

- CF 文档: https://developers.cloudflare.com/waf/custom-rules/
- CF Bot Fight Mode: https://developers.cloudflare.com/bots/get-started/bot-fight-mode/
- llms.txt 规范: https://llmstxt.org

最后更新 · 2026-06-24
