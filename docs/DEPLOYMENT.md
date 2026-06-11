# DEPLOYMENT.md — 个人网站部署方案

> **状态**: 方案已定型,实施延后到前端大改完成
> **最后更新**: 2026-06-11
> **对应 plan**: `/Users/zhewenliu/.claude/plans/gentle-stargazing-hartmanis.md`（同源, 这份是项目内 mirror）

## Context

用户要把项目正式部署到个人网站，但前端还要大改。计划分两阶段：
- **阶段一（无 ICP）**：EdgeOne Pages 选"全球可用区（不含中国大陆）"，先上线
- **阶段二（ICP 完成后）**：EdgeOne Pages 切到"全球可用区（含中国大陆）"

本方案给**已确定的部分**（域名、备案、平台）和**待前端定稿后**的部署要求清单。

## 项目实际结构（已勘探）

| 模块 | 类型 | 是否可纯静态 |
|------|------|--------------|
| 61 个 `curated/*.html`（专业 dashboard） | 纯静态 | ✅ |
| 仪表盘索引 + 推荐 UI（重写后） | 纯静态 + JS | ✅ |
| 临时搜索新专业（LLM 合成） | **必须后端**（API key 保护） | ❌ 需 serverless |
| 纯前端 recommender（推荐志愿组） | 纯静态 + JS | ✅ |
| `data/*.csv`（合成数据） | 数据文件 | — |
| 捐赠（赞赏码/外链） | 纯静态 | ✅ |

**关键约束**：
- EdgeOne Pages **不能** 跑 Python 后端
- LLM API key 不能暴露在浏览器 → **临时搜索能力必须走 serverless 函数**
- **61 个 dashboard + LLM 搜索后端可以一起上阶段一**——两者完全独立、并行部署

## 决策记录

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 域名 TLD | `.cn` | 国内长期运营，DNSPod/阿里云万网购买最顺 |
| 静态托管 | **EdgeOne Pages** | 阶段一区域 = "全球可用区（不含中国大陆）"，无需备案 |
| 临时搜索后端 | **腾讯云 SCF 香港地域** | 境外地域无需备案，10万次/月免费，冷启动 ~1s |
| 备案主体 | **阿里云轻量** | 用户已有 2C4G 轻量，符合阿里云备案主体资格 |
| EdgeOne Pages 区域 | 阶段一："全球可用区（不含中国大陆）" | 无需备案，海外/香港节点 |
| | 阶段二：迁移到"全球可用区（含中国大陆）" | 备案后切换 |
| 捐赠 | **微信赞赏码 + 支付宝收款码 + 爱发电外链** | 纯静态图片 + 外链，0 成本，0 后端 |
| LLM 选型 | **DeepSeek API**（推荐） | 1 元/百万 token，1 次搜索 ~2000 token ≈ 0.002 元 |
| SCF 运行时 | **Python 3.11**（与现有 core/ 一致） | 后续可复用 filter/probability 算法 |

## 实施步骤

### 阶段 0：现在可以做的准备工作（不花钱、不部署）

1. **买域名**
   - 注册商：阿里云万网（便于后续在阿里云备案走一体化）或 腾讯云 DNSPod
   - 域名建议：`你的名字缩写.cn` 或 `gaokao-hubei.cn` 之类短名
   - 实名认证：1-2 天
   - 费用：~30 RMB/年

2. **部署前的代码改造**（前端大改时一并做）
   - `frontend/index.html` 重构为**纯前端 recommender**：
     - 首次加载时 fetch `data.json`（预构建的 admission + rank 数据）
     - `core/recommender.py` 的 filter / probability / strategy 算法**移植到 JS**
     - 移除 `http://localhost:8000` 硬编码，改为同源路径
   - 加 `index.html` 入口页（dashboard 索引、按专业分类、搜索）
   - 准备 `dist/` 构建产物目录：
     ```
     dist/
       index.html
       majors/{slug}.html       # 复制 61 个 curated/
       data/{province}_{subject}_{year}.json   # 预构建的 admission 表
       data/rank/{province}_{subject}.json     # 预构建的 rank 表
       assets/...
     ```
   - 写 `scripts/build_static.py`：把 `data/*.csv` + `core/` 的算法输出 JSON

3. **EdgeOne Pages 项目准备**
   - 注册腾讯云账号（实名认证 1-2 天）
   - 在 EdgeOne Pages 控制台 **不要现在创建项目**（前端没定稿会浪费）
   - 等前端定稿后，建项目 → 选"全球可用区（不含中国大陆）" → Git 仓库或手动上传 `dist/`

4. **备案准备**（域名实名后即可启动）
   - 登录阿里云备案系统（已有阿里云轻量可作主体资格）
   - 资料：身份证 + 域名证书 + 阿里云轻量服务器购买凭证
   - 预计：15-20 天（管局审核）
   - 期间：网站用 EdgeOne Pages 海外区域继续跑

### 阶段 1：前端定稿 → 部署上线（无 ICP，61 dashboard + LLM 搜索同时上）

**整体架构**：
```
浏览器
  ↓
yourname.cn (HTTPS)
  ↓
EdgeOne Pages (全球不含中国大陆)
  ├── 61 个 curated/*.html
  ├── index.html (dashboard 索引 + 搜索 + 推荐 UI)
  ├── recommender.js (纯前端推荐算法)
  ├── search-major.js (调下方 API)
  └── data/*.json (预构建数据)
  ↓ fetch('/api/search-major?q=...')
  ↓
腾讯云 SCF (香港地域，无需备案)
  ├── 入口: POST /search-major
  ├── 鉴权: 简单 rate-limit (按 IP)
  ├── 调 DeepSeek API
  └── 合成 HTML 片段 + 简单结构化字段
```

**实施步骤**：

1. **DNS 解析**
   - 在 DNSPod / 阿里云 DNS 添加 CNAME 记录
   - `yourname.cn` → `yourname.edgeone.app`（EdgeOne Pages 默认域）
   - 或用子域：`www.yourname.cn` / `majors.yourname.cn`

2. **EdgeOne Pages 部署**
   - 项目设置 → 域名管理 → 添加 `yourname.cn`
   - 勾选"免费生成 SSL 证书"
   - 部署 `dist/` 目录（含 61 dashboard + index + JS + 预构建 JSON）

3. **腾讯云 SCF 部署（临时搜索后端）**
   - 创建 SCF 函数，地域选**香港**，运行时 Python 3.11
   - 函数代码：~50 行，接收 `?q=专业名`，调 DeepSeek API，返回结构化 JSON
   - 配置 API 网关触发器，路径 `/search-major`
   - 配置 CORS：允许 `https://yourname.cn`
   - 环境变量注入 `DEEPSEEK_API_KEY`（不要硬编码）

4. **前端集成**
   - `index.html` 搜索框：输入 → fetch SCF → 展示临时合成的 HTML 片段
   - 缓存策略：已搜过的存 localStorage，避免重复调用 LLM
   - rate-limit：前端 1 次/秒，避免刷额度

5. **验证**
   - `curl -I https://yourname.cn` 看 200 + EdgeOne 节点
   - `curl https://yourname.cn/api/search-major?q=核工程` 看返回 JSON
   - `https://itdog.net` 测速，海外/香港节点预期延迟 30-80ms
   - 浏览器实测：搜索 61 个已有专业 + 1 个未收录专业，2 路都能用

**月成本估算**：
| 项 | 用量 | 费用 |
|---|---|---|
| EdgeOne Pages | 1GB 存储 + <10GB 流量 | 0 元（免费层） |
| 腾讯云 SCF 香港 | 1 万次调用 | 0 元（免费层 10万次） |
| DeepSeek API | 1 千次搜索 × 2K token | ~0.5 元/月 |
| 域名 | 1 个 | ~30 元/年 |
| **合计** | | **< 5 元/月（除域名）** |

### 阶段 2：ICP 备案完成后切换大陆节点

1. **ICP 备案**（与阶段 1 并行）
   - 阿里云备案系统提交（用现有 2C4G 轻量作主体资格）
   - 管局审核 15-20 天
   - 通过后会发备案号，需在网站底部挂载并链接到 `https://beian.miit.gov.cn`

2. **EdgeOne Pages 区域切换**
   - ⚠️ **不是"开关"**——EdgeOne Pages 的加速区域通常**项目创建时锁定**
   - 实际做法（二选一）：
     - **(A) 推荐**：在 EdgeOne Pages 控制台 → 项目设置 → 找"加速区域"或"迁移"功能（部分计划支持）
     - **(B) 兜底**：新建一个 EdgeOne Pages 项目，区域选"全球可用区（含中国大陆）"，把 `dist/` 部署过去；DNS 切到新项目的 CNAME；老的海外项目保留作 fallback
   - **DNS 解析不动**——这是两阶段方案的核心优势
   - **代码不动**——这是另一大优势

3. **SCF 后端切到境内**
   - 在腾讯云 SCF 控制台把函数克隆到**广州/上海地域**
   - 用境内 API 网关触发器（可绑已备案域名）
   - DNS 加一条 `api.yourname.cn` 指向境内 API 网关
   - 前端切换 API base URL（或保留香港 SCF 作 fallback）

4. **验证**
   - `https://itdog.net` 国内节点测速，预期延迟 10-30ms
   - 浏览器访问 https://yourname.cn 看备案号是否正确显示
   - 临时搜索功能：从国内发起，延迟 < 200ms

## 关键文件清单

需要修改/新建的文件（前端大改时）：

- **新建**：`frontend/index.html`（重写为纯静态 SPA 或多页应用）
- **新建**：`scripts/build_static.py`（数据预构建）
- **新建**：`dist/index.html`（dashboard 索引入口）
- **新建**：`dist/data/*.json`（构建产物，提交到 Git）
- **改造**：`core/recommender.py` → 移植为 `frontend/assets/recommender.js`
- **不动**：`skills/gaokao-major-explorer/data/curated/*.html`（61 个 dashboard 已完工）
- **不动**：`data/*.csv`（保持原样，构建脚本读取）

LLM 搜索后端（新增）：

- **新建**：`scf/search_major/main.py`（~50 行 SCF 入口，Python 3.11）
- **新建**：`scf/search_major/prompt.txt`（DeepSeek prompt 模板，~10 行）
- **新建**：`scf/search_major/scf_bootstrap`（SCF 启动脚本）
- **新建**：`scf/template.yaml`（SCF + API 网关 IaC 定义，Serverless Framework 格式）
- **配置**：腾讯云控制台添加 `DEEPSEEK_API_KEY` 环境变量

捐赠（新增）：

- **新建**：`dist/donate/wechat-qr.png`（微信赞赏码截图）
- **新建**：`dist/donate/alipay-qr.png`（支付宝收款码截图）
- **修改**：`dist/index.html` 加一个"支持作者"链接 → `dist/donate/`

## 阶段切换成本对比

| 操作 | 阶段一 | 阶段二 |
|------|--------|--------|
| EdgeOne Pages 项目创建 | ✅ 一次 | ✅ 一次（或迁移） |
| SCF 香港地域创建 | ✅ 一次 | ✅ 一次（克隆到境内） |
| DNS 解析配置 | ✅ 一次 | ❌ 不动 |
| SSL 证书 | ✅ 自动 | ✅ 自动 |
| 代码部署 | ✅ 一次 | ❌ 不动 |
| DeepSeek API key 注入 | ✅ 一次 | ❌ 同一个 key（切地域） |
| 备案号挂载 | ❌ 不需要 | ✅ 必须 |
| 实际工作量 | 1-2 h（含 SCF 部署） | 2-3 h（迁移 EdgeOne + 克隆 SCF） |

## 验证清单

- [ ] 阶段 1 上线后：`curl -I https://yourname.cn` 返回 200
- [ ] 阶段 1 上线后：https://itdog.net 国内三网测速，海外节点 30-80ms 可接受
- [ ] 阶段 1 上线后：61 个 dashboard 全部能正常打开，站内链接不断
- [ ] 阶段 1 上线后：纯前端 recommender 能跑通（即使数据是合成的也演示完整流程）
- [ ] 阶段 1 上线后：搜索 1 个未收录专业（如"核工程"），< 3s 返回合成 HTML
- [ ] 阶段 1 上线后：localStorage 缓存生效，重复搜索 0 LLM 调用
- [ ] 阶段 1 上线后：rate-limit 生效，前端不会刷额度
- [ ] 阶段 1 上线后：捐赠页能正常打开，微信/支付宝赞赏码显示
- [ ] 阶段 2 备案后：备案号正确显示在网站底部
- [ ] 阶段 2 切换后：https://itdog.net 国内三网测速 < 30ms
- [ ] 阶段 2 切换后：DNS 解析 IP 变成腾讯云大陆节点
- [ ] 阶段 2 切换后：临时搜索 API 切到境内 SCF，延迟 < 200ms
- [ ] 阶段 2 切换后：原海外 EdgeOne Pages 项目（如果新建了）保留作 fallback

## 风险与缓解

| 风险 | 概率 | 缓解 |
|------|------|------|
| EdgeOne Pages 不支持"区域开关" | 中 | 准备"新建项目 + DNS 切换" 兜底方案 |
| 阿里云轻量备案审核超时 | 低 | 提前 1-2 周提交，与阶段 1 并行 |
| `data/*.csv` 太大导致 dist 超限 | 低 | 当前最大 312KB，预构建 JSON 后可能略大；EdgeOne Pages 免费层 1GB 够用 |
| 纯前端 recommender 性能问题 | 中 | 输入空间大，JS 跑 96 推荐可能 2-5s；用 Web Worker + 增量渲染 |
| 域名被墙 / 解析失败 | 极低 | 选主流注册商（DNSPod/万网），不被墙 |
| DeepSeek API 被刷额度 | 中 | SCF 入口加 IP rate-limit (10次/分钟)；前端 1 次/秒 throttle |
| DeepSeek API 输出不稳定 | 中 | prompt 加 schema 约束；返回结构化 JSON 而非裸 HTML |
| SCF 冷启动慢 | 中 | 搜索场景可接受（~1s）；用户预期 1-3s 看到结果 |
| SCF 跨域 CORS 配错 | 低 | API 网关显式返回 `Access-Control-Allow-Origin: https://yourname.cn` |

## 开放问题（等前端定稿后明确）

1. `frontend/index.html` 是保留 recommender 入口，还是只做 dashboard 展示？
2. 预构建数据粒度：按"省份+科目+年份"还是全量打包？
3. 61 个 dashboard 的目录结构：平铺 vs 按学科分类（文科/理科/工科/医科）？
4. 是否需要 SEO（每页 meta description、sitemap.xml、robots.txt）？
5. 是否需要暗色模式（i18n / 主题切换）？
6. LLM 临时搜索的输出格式：返回结构化 JSON 让前端渲染 vs 返回 HTML 片段？推荐前者（更可控）
7. SCF 入口是否需要用户输入验证（防 injection）？推荐用 prompt template 隔离
8. SCF 部署工具链：Serverless Framework（推荐）vs 腾讯云控制台手动 vs Terraform？

## 决策记录

- **2026-06-11 早期**：方案定型，前端大改期间不部署，备案走阿里云
- **2026-06-11 中期**：明确阶段一同时上 61 dashboard + LLM 搜索后端
- **2026-06-11 中期**：LLM 搜索后端选 腾讯云 SCF 香港地域（无需备案）
- **2026-06-11 中期**：LLM 选型 = DeepSeek API（成本最低，~0.002 元/次）
- **2026-06-11 中期**：捐赠方案 = 微信赞赏码 + 支付宝收款码 + 爱发电外链（纯静态）

## 推进节奏

> 用户拍板：**前端大改完后再启动实施**。详见 ADR-015。
> 这份 doc 在前端定稿前是 reference，不催代码生成。
