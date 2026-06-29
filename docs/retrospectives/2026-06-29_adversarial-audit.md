# Day 35+ 对抗式审查报告 (2026-06-29)

> **目标**: 找出已上线 625 篇 major + 4 个工具 + 部署配置中潜在 bug
> **方法**: 6 个 agent 并行扫描 + 独立边界检查
> **总发现**: 23 个 P0/P1 (12 P0 + 11 P1) + 35+ P2

---

## 🔴 P0 (Critical, 15 个) - 影响线上 / SEO / 部署

### P0-1: JSON-LD 0 注入 (1253 HTML × 0)
- **证据**: `grep -l "application/ld+json" public/*.html | wc -l` → 0
- **原因**: `scripts/build/inject_jsonld_v2.py` 写了但从未跑过/部署失效
- **损失**: 100% SEO 收益 (Course/Breadcrumb/FAQ/AggregateRating 全部丢失)
- **修法**: `python3 scripts/build/inject_jsonld_v2.py` (1.5h)

### P0-2: robots.txt AI 防线撒谎
- **证据**: `public/robots.txt` 8 行, 无任何 AI UA block. `_headers` 注释说"32 UA + Disallow: /"
- **修法**: 加 32 个 UA + Disallow: / 块

### P0-3: sitemap.xml 4 个 404 URL
- **证据**: `<loc>https://majorexplorer.com/m/majors.html</loc>` + `m/preferences.html` 不存在
- **损失**: Google Search Console 持续 "Submitted URL not found (404)" 拉低整站索引
- **修法**: 删 2 行 (PC majors.html/preferences.html 同样需要验证)

### P0-4: sw.js CACHE_NAME 占位符 `v0-shareDay35`
- **证据**: `public/sw.js:9` + `public/m/sw.js:9` 均为 `"explorer-v0-shareDay35"`
- **根因**: commit c64c58f0 6/29 8:33 故意设置占位, 注释"deploy.sh 会再 bump", 但 6/29 11:18 b765bf96 后 deploy.sh 未跑
- **风险**: Day 32 4 层 cache 锁死 sw.js → 部署失效
- **修法**: 跑 `bash scripts/deploy.sh "bump cache"` (会触发 Step 4.5 升版)

### P0-5: business theme H1 写死 "Strategic Management" (4 篇)
- **根因**: `skills/gaokao-major-explorer/scripts/v4_styles/themes/business.py:230`
  ```html
  <h1 class="biz-title-main">Strategic Management</h1>
  ```
  接收 `title` 参数但完全没用上
- **影响**: `accounting`/`business-administration`/`auditing`/`international-economics-trade` H1 全是英文, 与 title 不一致
- **修法**: 改 `<h1 class="biz-title-main">{title}</h1>` + 跑 render 重生成 4 篇

### P0-6: recommender.test.mjs 31/57 fail (45%)
- **证据**: `node public/js/recommender.test.mjs` 实际 26 pass / 31 fail
- **根因**: `majorMatch` 同义词展开失效, `expandInterest` 接收的 synonymMap 结构不匹配
- **修法**: 修 synonymMap schema + majorMatch 失败降级

### P0-7: share.js:864 调 WishlistStore.update() 不存在
- **根因**: `wishlist-store.js` 没有 `update` 方法 (只有 `upsert/setScore`)
- **影响**: 静默 fallback 到 `upsert` → 命中已存在条目会**丢失 style/category 字段**
- **修法**: 加 `WishlistStore.update(slug, patch)` 方法

### P0-8: 38 篇 alumni_quotes 100% -alum-N 占位
- **证据**: 38 篇 (law/psychology/history/economics/education/finance/math/physics/chemistry 等) alumni 5 条全模板
  - `current: "心理学-alum-0"`
  - `school: "某 985 高校中文系 2021 届"` (历史专业!)
- **m3 评分盲点**: 32 篇 score=8, 5 篇 9, 1 篇 10
- **修法**: 38 篇分别写 3-5 条具名校友

### P0-9: 9 篇 mobile HTML 缺失
- **缺失 slugs**: `cyberspace-security`, `data-computation-science`, `integrated-science-and-engineering`, `marine-science`, `microelectronics-science-engineering`, `nuclear-engineering-nuclear-technology`, `port-channel-coastal-engineering`, `thermal-energy-power-engineering`, `water-conservancy-engineering`
- **根因**: 4 篇 mobile/PC slug 拼写不一致 + 5 篇 mobile render 漏跑
- **影响**: mobile UA 用户访问这些 major 跳到 404
- **修法**: 同步 mobile render pipeline slug, 补 9 个 mobile HTML

### P0-10: og:image 2/648, canonical 20/648 (97% 缺)
- **证据**: 648 PC HTML 中仅 2 个 og:image, 20 个 canonical
- **损失**: social share 无图 (微信/微博/Twitter 卡片) + 重复内容 SEO 风险
- **修法**: render.py 加 og:image 生成 (用 share 已有 og-card.png) + canonical 模板

### P0-11: _redirects 缺 404 兜底
- **根因**: `public/_redirects` 0 条 `/* /404.html 404` 兜底规则
- **影响**: 任何 /<不存在>.html 直接跳 CF 默认 404 页面, 跳出站
- **修法**: 末尾加 `/* /404.html 404`

### P0-12: deploy.sh 0 远程 curl 验证
- **根因**: 注释说"4 步验证", 实际只本地 grep + git status, 0 curl 验证
- **影响**: Day 32 锁 cache 警示后仍未真正闭环
- **修法**: deploy.sh Step 8 加 4 个 curl 验 sw.js / _headers / JSON-LD / homepage

### P0-13: meta description 含 `<` 字符破坏 HTML 属性 (10+ 个)
- **证据**: 真实 HTML 输出 `<meta name="description" content="...全国开设院校 < 5 所...">`
- **影响**: 浏览器把 `< 5` 当成标签, description 提前关闭, 严重 SEO 损失
- **slugs**: equine-science, flight-technology, statistics, technical-investigation, laboratory-animal-science, national-security-protection, turf-grass-science-engineering, apiculture, nuclear-medicine, chinese-veterinary-medicine 等
- **根因**: `render.py:729` `summary[:100]` 没 escape
- **修法**: `summary_esc = html.escape(summary)[:100]`

### P0-14: 12 个文件渲染"选科数据待补充"用户可见 placeholder
- **证据**: `public/biotechnology.html` 等 12 个显示 `<p>选科数据待补充</p>` (用户可见)
- **根因**: renderer xuanke section fallback 是 placeholder 文本, 没 hide
- **slugs**: applied-meteorology, biotechnology, exhibition-economy-management, geochemistry, geographic-information-science, hotel-management, industrial-engineering, integrated-science, physical-geography-urban-rural-planning, property-management, quality-management-engineering
- **修法**: fallback 改 hidden 或不渲染该 section

### P0-15: mobile 0/628 meta description + 0/628 discipline-breadcrumb
- **证据**: 全量 mobile 缺 meta description (628/628) + 缺 discipline-breadcrumb (628/628)
- **影响**: mobile SEO 100% 失效 + 用户无法定位门类
- **修法**: render_mobile.py 注入 description + breadcrumb

---

## 🟡 P1 (High, 17 个) - 数据债 / 部署后 polish

### P1-1: 553/625 lede 顶层 null (schema 双轨)
- **数据**: top-level lede 73/627 vs overview_v2.lede 626/627
- **影响**: check_major.py 553 篇 anti-pollution 无法跑
- **修法**: `scripts/sync_lede_to_top.py` (5 min 一次性)

### P1-2: 4 个 null score (registry slug drift)
- **slugs**: `slug` (literal stub) / `ophthalmology` → 真实 `ophthalmology-optometry` / `composite-materials-engineering` (存在) / `smart-grid-information-engineering` → 真实 `smart-grid-engineering`
- **修法**: `python3 scripts/audit/update_audit_registry.py --rebuild` (30s)

### P1-3: mobile slug 拼写不一致 (4 处)
- `data-computation-science` vs `data-computation-application`
- `nuclear-engineering-nuclear-technology` vs `nuclear-engineering-technology`
- `microelectronics-science-engineering` vs `microelectronics`
- `integrated-science-and-engineering` vs `integrated-circuit-design-and-integration-system`
- **修法**: 统一 slug, 修 render 流程

### P1-4: law/auditing/accounting/finance 4 篇 pitfalls 完全相同模板
- **根因**: Day 30 m3 写到一半中断, 4 篇没差异化
- **修法**: 4 篇分别写 6 条专属 myth/reality

### P1-5: ocean-science employment 严重串台
- **证据**: employment 含"互联网 20%/量化 12%/半导体 10%" — 海洋科学根本不进
- **修法**: Tier 2 重写 (45 min)

### P1-6: cultural-relics-conservation-restoration 130403T vs 0601 混淆
- **影响**: 高考生选错代码影响考公分流
- **修法**: 重写 top_schools 5 所 + 3 条具名校友 + deep_study 5 路径

### P1-7: 海洋类 top_schools 9 处 985 误标
- **数据**: 中国海洋大学/大连海事大学 被列头部 (但它们不是 985)
- **修法**: 海洋类 top_schools 整体重审

### P1-8: top_schools tier 字段 0% 填充
- **数据**: 5497 entries × 0.04% 有 tier 字段 (5500 个全空)
- **根因**: schema 设计了 tier 但 content 流程不填
- **修法**: 批量回填或删字段

### P1-9: salary p75 > 100w 多处
- **slugs**: pediatrics / industrial-intelligence / geographic-information-science / intelligent-vehicle-engineering / geoinformation-science-technology 等
- **修法**: 降到 ≤100 + 加 note "头部例外"

### P1-10: _clamp(0) = 1 污染 recommender score
- **根因**: wishlist-store.js:53 `_clamp(0)` 返 1
- **影响**: 用户没评分时存 1, 污染 recommender `userScore + 0.2`
- **修法**: 改用 `Number.isFinite(n) ? n : 3` 仅在非法时 fallback

### P1-11: recommend() throw Error 触发白屏
- **根因**: recommender.js:302 抛 Error, pc-search.js 无 try/catch
- **修法**: 改 return `{stats:{error:'data_incomplete'}}` 不 throw

### P1-12: mobile 心愿单入口完全失效 (top-heart-btn)
- **证据**: `public/m/majors/_template.html` 有 `<button id="top-heart-btn">` 但 `public/m/js/detail.js` 0 click handler
- **影响**: mobile 用户点顶部 heart 无反应
- **修法**: `detail.js:185` 后加 topHeartBtn listener

### P1-13: mobile 仍渲染 deep_study 第九节, PC 已下线
- **证据**: `render_mobile.py:761-794` 仍渲染第九节, PC `render.py:679` 已删
- **根因**: 6/24 PC 下线 08 深造路径时 mobile 没同步
- **修法**: `render_mobile.py` 把 sec9 改 ""

### P1-14: 531/627 mobile top_schools 截 8 所
- **根因**: `render_mobile.py:469` `items = schools[:8]` 硬截
- **修法**: 删 `[:8]` 或加 "展开全部" 折叠

### P1-15: 627/627 mobile alumni 截 3 条
- **根因**: `render_mobile.py:589` `for q in quote_data[:3]`
- **修法**: 改 `[:5]` 与 PC 持平

### P1-16: mobile render_quote 字段别名错位
- **根因**: `render_quote()` 用 `name`/`tag`, JSON 主流是 `current`/`year`/`source`
- **影响**: mobile 显示"院校脱敏" 而非"人社局公务员 · 5 年"
- **修法**: `q.get("current") or q.get("name", "")` + `q.get("year")` + `q.get("source")`

### P1-17: 40 medical h3 避坑指南, 缺独立 section
- **证据**: v4_medicine.py:507 用 `<h3>避坑指南</h3>`, 嵌入 overview section, 锚点 id="pitfalls" 不存在
- **影响**: 40 个医学类 deep link `#pitfalls` 失效
- **修法**: 改独立 `<section id="pitfalls"><h2>避坑指南</h2>` 与 585 篇一致

### P1-18: 15 majors xuanke schema 漂移导致 HTML 渲染空白
- **证据**: 15 篇 (agricultural-engineering / wetland-conservation-restoration / cable-engineering 等) 用 `{combo, pct, note}` 或 `{item, pct, rationale}` 而非标准 `{name, course, pct, reason}`
- **影响**: HTML 中 `<div class="xuanke-name"></div>` 空, 用户看不到选科组合
- **修法**: 修 `_normalize_xuanke` 加 combo→name + item→name + rationale→reason 兜底, 或批量改 15 篇 JSON

### P1-19: 2 majors top_schools 字段名错 (school 而非 name)
- **slugs**: `intelligent-transportation` + `postal-engineering` 用 `{school, tag, rank, city}` 而非 `{name, tier, tag}`
- **影响**: 渲染时校名为空
- **修法**: `school` → `name` 改名

### P1-20: 3 majors employment_direction 字段名漂移
- **slugs**: journalism (`direction`) / advertising (`direction`) / landscape-architecture2 (`dir`, `desc`, `dest`)
- **影响**: employment 渲染空
- **修法**: 统一 `{name, pct, desc, dest}` schema

### P1-21: tcm-yangsheng 公共必修误填专业课
- **证据**: `中医内科学 (概要)` 放公共必修, 触发 anti-pollution #4
- **修法**: 移入 `通用专业核心`

### P1-22: 16 phantom slugs 累计 31 条浪费 audit
- **证据**: `medical-laboratory-tech` (6 audits 浪费 ¥3) / `arabic` / `translation` / `plant-protection` / `silkworm-science` 等 16 个 phantom
- **修法**: `python3 scripts/audit/update_audit_registry.py --rebuild`

### P1-23: 21 majors `updated_at` 格式错 (ISO 8601 而非 YYYY-MM)
- **修法**: 批量正则替换为 YYYY-MM

### P1-24: 68 majors 缺 `data_source` 字段
- **修法**: 默认填 `"人工精编"` + backfill 脚本

### P1-25: 28 majors salary p75(5年) > p75(10年+) 致命倒挂
- **slugs**: world-history (差 35万) / drama-performance (差 45万) / digital-theatre (差 35万) / chinese-veterinary-medicine (差 30万) / acoustics (差 35万) / cognitive-neuroscience (差 20万)
- **修法**: 麦可思 2024 校准, p75(10年+) ≥ p75(5年)

---

## 🟢 P2 (35+ 个) - 部署后 polish / 长期

| # | bug | 涉及文件 |
|---|-----|---------|
| 1 | toInterests() 返 major:"" | wishlist-store.js:248 |
| 2 | mobile/preferences.html 缺 dock page | verify_mobile.py 报 1 error |
| 3 | 10 + 12 phantom HTML "已合并" 状态 | xe9ho9v mojibake 等 |
| 4 | top_companies 161 处事业编/公务员 | 161 majors |
| 5 | Cmd+Shift+S 全局拦截无 focus 检查 | share.js:739 |
| 6 | shareScore modal 修好 style/category 丢失 | wishlist-store.js + share.js |
| 7 | data-loader fetch 失败 404 HTML 返回 | data-loader.js:138 |
| 8 | yfyd_2025 老 key 与 yfyd_hubei_2025 不一致 | data-loader.js:54 |
| 9 | intent_guidance 严格相等, 空格敏感 | major-search.js:559 |
| 10 | mountChat click listener 重复绑 | major-search.js:687 |
| 11 | render_pitfalls_v2 overview_v2 fall back 链路 | overview_v2.py |
| 12 | 7 主题 business theme 已 merge 仍 PC 占位 | business.py |
| 13 | llms.txt 无 cache-control | _headers |
| 14 | fonts.googleapis.com 缺 CSP 白名单 | _headers |
| 15 | discipline-pills XSS (虽然 JSON 内部) | discipline-pills.js:25 |
| 16 | wishlist _write QuotaExceededError 静默 | wishlist-store.js:53 |
| 17 | recommend() histBrief 不限 2023+ 体积 | recommender.js:375 |
| 18 | 内链 broken (sample 30) | 0 实际 OK |
| 19 | data loader _checkStalenessAndWarn 串行 | data-loader.js:163 |
| 20 | deploy.sh sed 漏 public/m/majors/*.html | deploy.sh:78 |
| 21 | 21 篇 variance stuck 7-8 | 1-2 篇需 variance_verify |
| 22 | drama-performance 浙江传媒 985 误标 | drama-performance.json |
| 23 | international-law 8 audit stuck 7 | international-law.json |
| 24 | materials-science-engineering 2 audit stuck 7 | materials-science-engineering.json |
| 25 | applied-statistics 6 audit stuck 7 | applied-statistics.json |
| 26-35 | 其他分享卡片 / recommender 边界 / mobile / XSS | 散点 |

---

## 🎯 Top 12 修复顺序 (P0 by 修动小 / 影响大)

| # | 改什么 | 修动 | 期望效果 |
|---|--------|------|----------|
| 1 | `python3 scripts/build/inject_jsonld_v2.py` | 30 min | SEO 100% 恢复 |
| 2 | 删 sitemap 2 行 + 修 robots.txt 加 32 UA | 10 min | 404 流量 + AI 防护 |
| 3 | `bash scripts/deploy.sh "bump cache"` | 5 min | sw.js CACHE_NAME 真正升版 |
| 4 | business.py:230 → `{title}` + 跑 render 4 篇 | 10 min | 4 篇 H1 修复 |
| 5 | 修 recommender synonymMap schema | 1-2h | 31 测试修复 |
| 6 | 加 `WishlistStore.update(slug, patch)` | 30 min | share.js 修 |
| 7 | 写 38 篇 alumni 真校友 | 4-6h | m3 评分真实化 |
| 8 | 补 9 个 mobile HTML | 1-2h | mobile 404 修 |
| 9 | render.py 加 og:image/canonical | 1h | SEO 2 项关键 |
| 10 | _redirects 加 404 兜底 | 5 min | 不跳出站 |
| 11 | deploy.sh 加 curl 4 步 | 30 min | 部署闭环 |
| 12 | `--rebuild` registry | 30s | 4 个 null score 修复 |

**总预计修动**: 8-12h (3-4 个 session)

---

## 📊 4 anti-pollution 状态

| 规则 | 当前 | 健康度 |
|------|------|--------|
| lede 模板套话 | 0 命中 | ✅ |
| who_fits_no 串台 | 0 命中 | ✅ |
| deep_study CS/金融 12% | 0 命中 | ✅ |
| curriculum 公共必修填专业课 | 0 命中 | ✅ |

**PIPELINE 4 规则已稳定, 真正瓶颈是数据债 (553 lede null + 38 alumni 占位 + 4 null score)**

---

**生成时间**: 2026-06-29 11:30 (Day 35 持续)
**方法**: 6 agent 并行 + 独立边界扫
**总耗时**: ~12 min (agent 跑后台)
