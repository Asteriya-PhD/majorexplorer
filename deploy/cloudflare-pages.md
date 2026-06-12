# deploy/cloudflare-pages.md — Cloudflare Pages 部署操作指南

> 配套 `docs/DEPLOYMENT.md` v2 阶段 1
> 预计操作时间: 30-45 分钟
> 适用用户: 有 GitHub 账号 + Visa/Mastercard (注册 Cloudflare 域名用)

## 前置条件

- [ ] Cloudflare 账号 (https://dash.cloudflare.com/sign-up)
- [ ] GitHub 仓库: `gaokao-hubei-mvp` (用户已有, gh CLI 可用)
- [ ] Visa/Mastercard/PayPal (注册域名用)
- [ ] 浏览器可访问 Cloudflare 控制台

---

## Step 1: 注册域名 (5 分钟)

**目标**: 在 Cloudflare Registrar 注册 `majorexplorer.com`

1. 打开 https://dash.cloudflare.com
2. 左侧菜单 → **Account Home** → **Add a Site** → 选 **Register Domains** (不是 "Add an existing site")
3. 搜索框输入 `majorexplorer.com` → 加购物车
4. 选注册期: **1 year** (后续可改 2-10 年)
5. 填联系人信息 (姓名/地址/电话, **Cloudflare WHOIS 隐私保护会盖住**)
6. 付款方式: 信用卡 (Visa/Mastercard) 或 PayPal
7. 付款完成 → 域名自动添加到 Cloudflare DNS 管理

**验证**:
- Cloudflare 邮箱收到 "majorexplorer.com is now on Cloudflare"
- Cloudflare Dashboard → 左侧 **Websites** → 看到 `majorexplorer.com`

---

## Step 2: 准备 GitHub 仓库 (1 分钟)

**前置**: 用户已 git push 当前工作树 (含隔壁修复)

```bash
# 1. 进入项目
cd /Users/zhewenliu/Claude/gaokao-hubei-mvp

# 2. 检查 git 状态
git status
# 应该看到 modified + new files (manifest/scf/HTML 等), 隔壁修复完了一起 push

# 3. 提交
git add -A
git commit -m "feat(deploy): Cloudflare Pages 海外直链配置 + 68 精品 + LLM 后端" 
# 跟隔壁对齐 commit message, 不要重写他们的 commit

# 4. 推送到 GitHub
gh repo sync   # 或: git push origin main
```

**验证**:
- GitHub 仓库 → 看到新 commit
- Cloudflare 部署时从这里拉取代码

---

## Step 3: 创建 Cloudflare Pages 项目 (10 分钟)

1. Cloudflare Dashboard → 左侧 **Workers & Pages** → **Create application**
2. 选 **Pages** tab (不是 Workers)
3. 选 **Connect to Git** → 选 **GitHub** → 授权 Cloudflare 访问你的 GitHub
4. 选 **"Only select repositories"** → 选 `gaokao-hubei-mvp`
5. 点 **Install & Authorize**
6. 回到 Cloudflare → 选仓库 `zhewenliu/gaokao-hubei-mvp` → **Begin setup**
7. 项目名: `majorexplorer` (生成 `majorexplorer.pages.dev` 临时 URL)
8. **Build settings**:
   - **Framework preset**: `None` (无框架, 纯静态)
   - **Build command**: **留空** (无构建, public/ 已是产物)
   - **Build output directory**: `public` ← **关键, 必须是 public/**
   - **Root directory**: `/` (项目根)
9. 环境变量: **None** (静态站不需要)
10. 点 **Save and Deploy**

**会发生什么**:
- Cloudflare 自动 git clone 你的仓库
- 30-60 秒后部署完成
- 给你一个临时 URL: `https://majorexplorer.pages.dev`

**验证**:
- 浏览器打开 `https://majorexplorer.pages.dev`
- 看到主页 "看清专业,再谈志愿 · Major Explorer 2026 高考 (湖北)"

---

## Step 4: 绑定自定义域名 `majorexplorer.com` (5 分钟)

1. Cloudflare Dashboard → **Workers & Pages** → 选 `majorexplorer` 项目
2. 顶栏 **Custom domains** → **Set up a custom domain**
3. 输入 `majorexplorer.com` → 点 **Continue**
4. Cloudflare 自动检测 DNS (你已经用 Cloudflare DNS 了, 自动加 CNAME)
5. **会自动签发 SSL 证书** (Let's Encrypt, 1-2 分钟生效)
6. 也可加 `www.majorexplorer.com` 作为别名 (可选)

**验证**:
```bash
# DNS 解析检查
dig majorexplorer.com +short
# 期望: Cloudflare 的 pages.dev CNAME 记录 (104.16.x.x 或 172.64.x.x)

# HTTPS 访问
curl -I https://majorexplorer.com
# 期望: HTTP/2 200, server: cloudflare, ssl: yes

# 浏览器
open https://majorexplorer.com
# 看到主页, 锁头标志绿色 (SSL 生效)
```

---

## Step 5: 配置 GitHub 自动部署 (2 分钟)

**默认行为**: 每次 `git push origin main` 后, Cloudflare 自动重新部署。

**可选配置** (Cloudflare Pages → Settings → Builds):
- **Build watch paths**: 留空 (任何 push 都触发)
- **Deploy triggers**: 选 "All branches" 或只 "main"
- **Branch deploy controls**: 
  - `main` → 生产环境 (majorexplorer.com)
  - 其他分支 → 预览环境 (xxx.majorexplorer.pages.dev)

**推荐配置**:
- 推送 `main` → 自动部署到 `majorexplorer.com`
- 推送 PR → 自动部署到 `pr-123.majorexplorer.pages.dev` (预览)

**手动触发**: Cloudflare Pages → Deployments → 找到某次部署 → **Retry deployment**

---

## Step 6: 优选 IP 配置国内访问加速 (10 分钟)

**目标**: 国内访问从默认 100-300ms 优化到 30-100ms

1. 跑优选 IP 脚本:
   ```bash
   cd /Users/zhewenliu/Claude/gaokao-hubei-mvp/deploy
   chmod +x optimal-cf-ip.sh
   ./optimal-cf-ip.sh
   ```
2. 脚本会:
   - 提示输入 Cloudflare API Token (在 Cloudflare Dashboard → My Profile → API Tokens → Create Token)
   - 提示输入 Zone ID (在域名概览页右下角)
   - 自动测速找出 top 5 IP
   - 调用 Cloudflare API 把 A 记录改成优选 IP
3. DNS TTL 300s, 5 分钟内全球生效

**验证**:
```bash
# 看 DNS 是否变成优选 IP
dig majorexplorer.com A +short
# 期望: 5 个优选 IP (不是默认的 104.16.x.x)

# 国内访问测速
# 让朋友/自己用国内网络访问, 浏览器开发者工具看 TTFB
# 或用 https://itdog.net 测速
# 期望: 国内三网 < 100ms
```

---

## Step 7: 验证清单

部署完成后, **完整跑一遍**:

```bash
# 1. DNS 解析
dig majorexplorer.com A +short
# 期望: 5 个 Cloudflare 优选 IP

# 2. HTTPS 状态
curl -I https://majorexplorer.com
# 期望: HTTP/2 200, server: cloudflare

# 3. 主页内容
curl -s https://majorexplorer.com | grep "Major Explorer"
# 期望: <title>看清专业,再谈志愿 · Major Explorer ...

# 4. 68 个 dashboard 抽样
for slug in accounting auditing clinical-medicine public-order translation; do
    status=$(curl -o /dev/null -s -w "%{http_code}" https://majorexplorer.com/${slug}.html)
    echo "${slug}: ${status}"
done
# 期望: 5 个都是 200

# 5. 静态资源
curl -I https://majorexplorer.com/css/shared.css
# 期望: 200, content-type: text/css

curl -I https://majorexplorer.com/data/manifest.json
# 期望: 200, content-type: application/json

# 6. 浏览器实测
# 打开 https://majorexplorer.com, 验证:
# - 主页 "精品" 区块有 68 个专业卡片
# - 点击任一卡片 → 跳到 /{slug}.html
# - 顶部 12 主题切换
# - 右下 FAB 心意单
# - 顶部 "搜专业" 输入框
```

---

## Step 8 (可选): 配置 Cloudflare Analytics

1. Cloudflare Dashboard → **Workers & Pages** → `majorexplorer` → **Analytics** tab
2. 自动启用, 看:
   - 每日访问量
   - 错误率
   - 出口流量

**额外监控** (可选, 6/25 出分当天用):
- Cloudflare → **Logs** → 实时访问日志
- 国内节点异常告警: Cloudflare 通知中心会推

---

## 故障排查 (Troubleshooting)

### 域名解析不到

```bash
dig majorexplorer.com +short
# 如果返回空:
# → Cloudflare DNS 没配 A 记录, 去 Cloudflare → DNS → Records 检查
# → 或域名注册没成功, 去 Cloudflare → Websites 看状态
```

### SSL 证书没签发

- Cloudflare → Pages → Custom domains → 看证书状态
- 常见原因: DNS 解析没生效 (等 5-10 分钟)
- 强制: Cloudflare → SSL/TLS → 把模式改成 "Full (strict)"

### 部署失败

- Cloudflare → Pages → Deployments → 找失败的部署 → 点进看日志
- 常见: build command 配错 / output directory 不是 public/
- 修正后 → **Retry deployment**

### 国内访问慢 (优选 IP 后仍 > 200ms)

- 重跑 `optimal-cf-ip.sh`, 找出新的最优 IP
- 或手动测试: https://itdog.net → 国内三网测速
- 极端情况: 临时把 DNS 切回 Cloudflare 默认 IP, 等路由恢复

---

## 月度维护清单

| 任务 | 频率 | 时间 |
|------|------|------|
| 重跑优选 IP 脚本 | 每月 1 次 | 5 分钟 |
| 检查 Cloudflare Analytics | 每周 1 次 | 5 分钟 |
| 检查 SSL 证书 (自动续) | 不需要 | 0 |
| 更新 manifest.json (新专业) | 按需 | 看内容 |
| git push 触发新部署 | 按需 | 30 秒 |

---

## 后续: 部署 LLM 搜索后端 (阶段 3, 不阻塞)

**触发**: 用户主动要求, 或真实用户开始搜未收录专业

**简化路径** (跟 v1 几乎一样, 见 ADR-012):
1. 腾讯云控制台 → SCF → 新建函数 → 地域"香港" → 运行时 Python 3.11
2. 上传 `scf/synth/` 整个目录
3. 环境变量注入 `DEEPSEEK_API_KEY` (从 scf/synth/llm.py 看, 用 raw HTTP 调, 0 SDK 依赖)
4. API 网关触发器 → 路径 `/synth/*` → CORS 允许 `https://majorexplorer.com`
5. 前端 `public/js/synth-client.js` 已有轮询逻辑 (commit f494378), base URL 指向新 SCF

**月成本**: SCF 免费层 10万次/月 + DeepSeek API ~0.5 元/月 ≈ **¥0-1**

---

## 关键链接

- Cloudflare Dashboard: https://dash.cloudflare.com
- Cloudflare Pages 文档: https://developers.cloudflare.com/pages
- Cloudflare API Tokens: https://dash.cloudflare.com/profile/api-tokens
- 国内测速: https://itdog.net
- 项目仓库: (用户的 GitHub)
