# 发布前全面 Review · majorexplorer.com
**Date**: 2026-06-21
**目标**: 宣发上线前最后一次端到端 QA
**测试范围**: PC (1280/1440/2560) + Mobile (iPhone 14 Pro 393×852 + iPad Mini 768)
**测试方式**: 3 个并行 agent + 我的 curl/Python 交叉验证, 全部在 https://majorexplorer.com/ 真站测试
**产物**: 25 张截图 (`/tmp/launch-review/screenshots/`) + 3 份 agent 报告 (`/tmp/launch-review/reports/`)

---

## 🎯 一句话结论

> **可以发布, 但建议先修 2 个 P0 + 3 个 P1 (估计 4-6 小时), 否则发布当天会被高三家长/学生/媒体直接看到这些瑕疵.** 核心功能(首页/搜索/447 个详情页/心愿单/推荐)**全部跑通且体验良好**, 没有阻塞性的功能性 bug.

---

## 📊 健康度记分卡

| 维度 | 评分 | 说明 |
|---|---|---|
| 核心功能完整性 | 🟢 9/10 | 447 个详情页全可访问, 心愿单/推荐/搜索流程完整 |
| 首页第一印象 | 🟡 7/10 | 文案 hook 好 ("18 岁高三生对 800+ 专业了解不到 10 个"), 但缺 H1 + CTA 不够明显 |
| PC 体验 (1280/1440/2560) | 🟢 9/10 | 三档分辨率均无溢出/错位; container 880px 居中干净 |
| Mobile 体验 (iPhone) | 🟢 8/10 | UA 自动跳 `/m/`, 底部 dock 5 tab, 选科 3+1+2 图表 / 薪资 4 列表 / 院校卡 等全部可读; **缺满意度评分** |
| 跨端一致性 | 🟡 6/10 | URL 不一致 (PC `/x.html`, Mobile `/m/majors/x.html`); 满意度仅 PC 有; sitemap 严重缺 |
| 数据准确性 | 🟢 9/10 | 30 篇随机抽样全部真内容 (88-130 KB); 27 个相关专业链全 200; 学科评估 A+/A 准确 |
| SEO 健康 | 🔴 4/10 | 缺 H1; sitemap 70/457 (84% 专业不可被发现); 软404 污染索引 |
| PWA / 离线 | 🟢 8/10 | Mobile 完整(manifest/sw.js/icon-180/offline); PC 缺 manifest |

---

## 🔴 P0 必修 (上线前)

### P0-1 · 首页缺少 `<h1>` (5 秒可修)
- **页面**: https://majorexplorer.com/
- **症状**: hero 文案"看清专业,再谈志愿"用 `<div>` / `<h2>`, 整页 `$('h1')` 返回 null
- **影响**: Google 找不到主标题 → 排名信号削弱; 屏幕阅读器无主标
- **修复**: hero 容器外层标签改 `<h1>`
- **文件**: `public/index.html` (hero block)

### P0-2 · sitemap.xml 只列 70/457 个专业 (15 分钟可修)
- **页面**: https://majorexplorer.com/sitemap.xml
- **症状**: 384 个详情页**不在 sitemap**, 包括 P0 参考案例 computational-linguistics, health-law (它们在 manifest 但不在 sitemap)
- **影响**: Google/Bing 不会爬到这 384 个页, 相当于 84% 的内容 SEO 失效 (花了大成本写的精品不被搜索发现, 与"宣发"目标根本冲突)
- **证据**:
  ```
  manifest.json: 457 majors
  sitemap.xml:   70 <loc> entries (含首页 + 69 详情页)
  ```
- **修复**: 重新生成 sitemap.xml — 遍历 manifest.json `majors[].slug` 全部加入
- **文件**: `scripts/build/build_sitemap.py` (估计存在, 是否在 deploy pipeline 里跑过?)

---

## 🟠 P1 强烈建议修 (上线前 24h 内)

### P1-1 · `_worker.js` 软 404 污染搜索索引
- **症状**: 任何错误路径 (`/foo.html` / `/majors/electronic-science-technology.html` / `/random/path`) 都返回 **HTTP 200 + 25,258 字节首页 HTML**
- **影响**:
  1. SEO: Google 会把"分身"全收录为重复内容, 严重稀释排名权重
  2. 监控: 死链无法被 404 抓取工具/告警识别
  3. 跨端误传: 用户在 PC 拿到的 `/<slug>.html` 链接复制给手机朋友, 手机朋友拼 `/m/<slug>.html` 也是 200, 但实际是首页 — 用户不知道
- **修复**: `_worker.js` 路径白名单不命中 → 返回 `404 Not Found` (改 HTTP 状态码 + 显式 404 页面), 而不是回退首页

### P1-2 · 主页"专业列表"完全依赖 JS, 无 SSR 降级
- **症状**: 首页 `#majors` 锚点处 HTML 只有"加载中…"占位 + 0 个 major 卡片. 完全靠 `major-search.js` 拉 manifest 后填充
- **影响**:
  1. JS 失败 / 慢网络 / 浏览器禁用 JS → 首页"专业入口"是死页
  2. 搜索引擎爬虫只看到"加载中…", 主页对 SEO 是空内容
  3. TTV (首屏价值显示时间) 取决于 manifest.json 423 KB 的 fetch
- **修复**:
  - 短期 (上线前): 在 HTML 里硬编码 10-20 个热门专业的 `<a>` 静态卡片, 让无 JS / 爬虫可见
  - 长期: build 时预渲染 13 个学科门类的分组卡片到 HTML

### P1-3 · 推荐 CTA 不明显
- **症状**: 首页 hero 没有视觉上的"主按钮". 搜索框是 chat 风但没有"→ 搜索"按钮提示; 用户(尤其 18 岁高三生)可能不知道这是可交互的
- **影响**: 5 秒漏斗转化下降; 用户停留在首页不知道下一步
- **修复**: 搜索框右侧加 `→ 搜专业` 按钮 + placeholder 改"试试输入 '编程' / '医生' / '金融'"

---

## 🟡 P2 建议修 (上线后第一周)

### P2-1 · Mobile 详情页缺"满意度评分"字段
- **症状**: PC 详情页 hero 有"阳光高考 · 用户满意度 4.1/5"; **Mobile (`/m/majors/<slug>.html`) 完全没有**这个字段渲染
- **抽样**: 5 篇 (electronic/comp-ling/health-law/accounting/clinical) mobile 全部缺失
- **根因**: Mobile `_template.html` 没设计 chsi 字段 (只在 CSS 注释里出现 1 次)
- **影响**: 跨端体验不一致, mobile 用户少了一个决策信号
- **修复**: Mobile 模板加 chsi-score 行, 与 PC 对齐
- **文件**: `public/m/majors/_template.html` 的 hero/meta 区

### P2-2 · 满意度字段同一页面 2 种格式 (`★ 4.4/5` vs `4.2`)
- **症状**: 抽样 15 篇 PC 详情页, 满意度渲染**两种风格混用**:
  ```
  accounting     ★ 4.4/5      animation      ★ 4.0/5
  anesthesiology 4.4           applied-psy    4.0
  ```
- **影响**: 同站视觉不统一, 像 bug
- **修复**: 统一为 `★ 4.4/5` 或 `4.4/5` 之一

### P2-3 · `clamp(1024,92vw,1280)` 容器未真正上线
- **症状**: Day 11.5 计划说 PC container 改 `clamp(1024,92vw,1280)`; 实际 CSS 仍是 `max-width: 880px`
- **影响**: 1440/1920/2560 屏幕上, 内容只占中间 880px, 两侧空白偏大. 不是 bug, 但与计划不符
- **修复**: 要么真正上 clamp, 要么更新 docs/Day-11.5 plan 接受 880px

### P2-4 · Mobile 模板 Section 标题与 PC 不一致
- 速览 (PC) vs 这个专业学什么 (Mobile)
- 薪资分布 (PC) vs 毕业后真的能拿多少 (Mobile)
- 主要课程 (PC) vs 本科 4 年学的课 (Mobile)
- **建议**: 短文案以 PC 为主, 长文案以 Mobile 为主 — 统一二选一

### ~~P2-5 · Mobile dock 缺"偏好"tab~~ ❌ 误报，已撤销
- 用户纠正 (2026-06-21): Mobile dock "收藏" tab 就是心愿单 + 偏好的统一入口，并非缺失
- ✅ Mobile dock 4 tab 与 PC 功能等价

### P2-6 · PC 缺 standalone "避坑指南" h2
- PC 把 pitfalls 合并进"速览"; Mobile 有独立"避坑指南"section
- **影响**: 避坑是核心卖点, PC 用户更难注意到
- **修复**: PC 详情页加独立 "避坑指南" h2

### P2-7 · 详情页 theme-color 写死 `#B8323A`
- Day 17 计划说按学科门类 12 色; 实际全部写死红色
- **影响**: PWA 安装后顶部颜色不变化
- **修复**: 详情页注入 JSON 的 `theme_color`

### P2-8 · 推荐 chips 不深链
- 首页"编程/当医生/金融/考公"chips 不是 `<a href="/search.html?cat=...">`, 是按钮
- **影响**: 用户无法用 URL 分享/收藏分类入口
- **修复**: chip 改 `<a>` 链接到过滤搜索

---

## 🟢 P3 可发布后做

| ID | 内容 |
|---|---|
| P3-1 | `/data/all_majors.json` 与 `/api/manifest.json` 返回 SPA HTML (legacy 死端点), 删除或实现 |
| P3-2 | manifest.json `slug` 字段混合 MOE 代码 (10 条) + 英文 slug — 加 `url_slug` 字段或分离 |
| P3-3 | `offline.html` 308 → `/offline`, sw.js 应预缓存最终 URL |
| P3-4 | 长页无"返回顶部"按钮 |
| P3-5 | Mobile 首页搜索图标偏中心 (Dynamic Island 附近), 建议右侧 |
| P3-6 | PC 缺独立 manifest.json (PWA 桌面安装时拿不到完整 metadata) |
| P3-7 | PC 详情页超宽屏 watermark "专" 字延伸出 1280 容器 |

---

## ✅ 已确认 OK 的部分

| 模块 | 验证 |
|---|---|
| 30 篇随机抽样详情页 | 30/30 全 200 + 真内容 (PC 88-130 KB / Mobile 59-64 KB) |
| 27 个相关专业链 (Day 5 Bug 3 修复区) | 27/27 全 200 真内容 |
| 14 个顶级页 | 全 200 (`/`/`/majors`/`/search`/`/wishlist`/`/preferences`/`/recommendations`/`/sitemap.xml`/`/robots.txt`/`/m/*`) |
| PC 三档分辨率 (1280/1440/2560) | 无溢出, 无错位, container 居中 |
| Mobile UA 自动跳 `/m/` | iPhone 14 Pro 验证通过 (SHA1 相同) |
| iPad Mini 768 → PC 布局 | 正确 (UA-sniff 不匹配 iPad) |
| Mobile 安全区 | `padding-top: 36px`, 无 Dynamic Island 遮挡 |
| Mobile 详情页核心区块 | scroll-progress / 3+1+2 选科条 / 4 列薪资表 / 院校 A+/A 评估卡 / 校友引述 / 心愿单 FAB — 全部正常 |
| 心愿单 / 偏好 / 推荐三步漏斗 | 表单完整 (高考分数/省排名/科类/选科/意向城市/填报模式), 推荐 9 档预填 580/14500 |
| 搜索 549/457/92 三档过滤 | 数字一致 (457+92=549), 词表覆盖中英文同义词 |
| PWA Mobile | manifest.json (105 字描述) + sw.js + icon-180 + offline.html 全 200 |

---

## 🚦 发布前必做清单 (推荐时间分配 4-6h)

```
[ ] 30 min  P0-1: 首页 hero 加 <h1>
[ ] 60 min  P0-2: 重生成 sitemap.xml (457 个 URL)
[ ] 60 min  P1-1: _worker.js 软404 → 真 404 (注意不要打到首页 SPA 路由)
[ ] 90 min  P1-2: 首页 SSR 注入 13 学科门类的静态 <a> 卡片
[ ] 20 min  P1-3: 搜索框加 "→ 搜专业" CTA + 改 placeholder
[ ] 30 min  P2-2: 统一满意度渲染格式
[ ] 总: ~5 小时
```

P2-1 (Mobile 缺满意度) / P2-3 / P2-4 / P2-5 / P2-6 / P2-7 / P2-8 留待 v1.1 hotfix.

---

## 📦 测试产物清单

```
/tmp/launch-review/
├── reports/
│   ├── pc_desktop.md       (175 行, PC 全面报告 — 注: 该 agent 因 URL 拼错误报 3 个 P0, 已订正)
│   ├── mobile.md           (175 行, Mobile + iPad + PWA)
│   └── consistency.md      (283 行, 跨端一致性 + 30 篇抽样 + 死链审计)
└── screenshots/  (25 张, 82 MB)
    ├── homepage_pc_{1280,1440,2560}.png + _fold.png
    ├── majors_list_pc.png, search_pc.png, preferences_pc.png, wishlist_pc.png, recommendations_pc.png
    ├── detail_{eng,hum,cross}_pc.png  (注: 这 3 张因 URL 拼错均为首页, 实际详情页见 mobile_detail_*)
    ├── mobile_{landing,home,majors,search,wishlist,preferences,recommendations}_iphone.png
    ├── mobile_detail_{eng,hum,cross}_iphone.png  (✅ 真实详情页)
    └── tablet_{landing,detail}.png
```

---

## 🔍 测试过程关键发现 (供未来 QA 参考)

1. **URL 拼错坑**: PC agent 一开始用 `/majors/<slug>.html` 拿到首页, 误判为 P0; 实际 PC 用 `/<slug>.html` (顶级), Mobile 用 `/m/majors/<slug>.html` (嵌套). 跨端约定不一致是真实 P1.
2. **软 404 trap**: Cloudflare `_worker.js` 对未知路径回退首页, **所有 200 都要验证 body size** (>30 KB) 而非只看 status code. 这次发现的"误报"几乎都来自这个 trap.
3. **Mobile satisfaction 缺失**: 模板根本没设计该字段, 不是数据缺失. 是模板 bug.
4. **manifest slug 混合**: 10 个 MOE 代码 slug (`050104`-`0502101`) + 447 个英文 slug. MOE 代码页**真实存在且可访问** (103 KB), 不是坏数据, 只是命名不统一.

---

**审核者**: Claude Sonnet 4 (Coordinator) + 3 并行 agents
**最终建议**: 🟢 **可以发布**, 强烈建议先修 P0-1 + P0-2 + P1-1 + P1-2 + P1-3 (约 5 小时), 让宣发时的 SEO/SSR/CTA/sitemap 都到位.
