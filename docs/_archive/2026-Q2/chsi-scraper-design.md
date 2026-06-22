# chsi 阳光高考 scraper 设计 (POC 已验证)

> Step 1 调研产出. 2026-06-14, plan `~/.claude/plans/plan-chsi-scraper.md`.

## TL;DR

| | |
|---|---|
| **数据源** | https://gaokao.chsi.com.cn |
| **反爬** | 锐安信/Aliyun JS 挑战 (412 + cookie 计算) |
| **工具栈** | patchright + chromium channel (stealth playwright fork) |
| **吞吐** | 100 校 / 14.6s (≈ 7 校/s, 含 JS 挑战开销) |
| **POC 已跑通** | `data/raw/schools_list.json` (100 校, 5/8 字段 100% 覆盖) |
| **法律** | robots.txt 友好 (仅禁 `/zzbm/tjr/`), 2 req/s 远低于普通用户 |

## 反爬现状 (实测)

### 现象
- 所有页面首请求返回 `HTTP 412 Precondition Failed`
- Body 是 ~3KB 的 JS 挑战 (锐安信 / 阿里云 TopSec)
- JS 计算 token 写入 cookie (`goaYXsyEWlxdO`, `goaYXsyEWlxdP`), 然后**自动重定向**到正常页面

### 实测对比

| 工具 | 结果 | 备注 |
|---|---|---|
| `curl` + 真实 UA | 412 拿到挑战 HTML, 卡死 | 无 JS 引擎 |
| Stock `playwright` (Chromium) | 412 → 卡死, body 仅 39 字节 | CDP 指纹被识别, `_$bP()` 不完整执行 |
| `playwright` + 全 stealth headers + `webdriver=undefined` | 412 → 400 (cookie 设了但仍拒) | 进一步指纹检测 |
| **`patchright` + `channel='chromium'`** | **412 → 自动重定向 → 200 ✅** | 挑战自动通过 |

### 关键代码
```python
from patchright.async_api import async_playwright
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True, channel='chromium')
    ctx = await browser.new_context(user_agent=UA, locale='zh-CN', timezone_id='Asia/Shanghai')
    page = await ctx.new_page()
    await page.goto(url, wait_until='domcontentloaded')
    await page.wait_for_timeout(3000)  # 等挑战 JS 完成
    html = await page.content()  # ← 此时已经是真实页面
```

第一次 ~5s (含挑战), 后续同 context 内复用 cookie ~1.5s.

## URL 模板

### 院校列表
`https://gaokao.chsi.com.cn/sch/search--ss-on,option-qg,searchType-1,start-{N}.dhtml`
- `start` = 偏移量, 步长 20 (page size 固定 20)
- 默认按 schId 升序 (北京大学=1 → ...), 1008 校 ≈ 51 页

### 院校详情
`https://gaokao.chsi.com.cn/sch/schoolInfo--schId-{N}.dhtml`
- `N` = chsi 内部 sch_id (1, 2, 3...)
- 不要跟 `edu_id` (10001, 10002 教育部编号) 混

### 子页 (从详情页 link-mining 得到, categoryId 每校不同)

| 子页 | URL 模板 | 备注 |
|---|---|---|
| 招生章程 | `/zsgs/zhangcheng/listZszc--schId-{N}.dhtml` | 列表页, 每年一份 |
| 专业介绍 | `/sch/listzyjs--schId-{N},categoryId-{C},mindex-3.dhtml` | `categoryId` 需先从详情页提取 |
| 录取规则 | `/sch/schoolInfo--schId-{N},categoryId-{C},mindex-4.dhtml` | 同上 |
| 录取结果公示 | `/sch/listlqjggs--schId-{N},categoryId-{C},mindex-8.dhtml` | 含分数线 |
| 选科要求 | `/zyck/xkkm/yxindex?yxdm={edu_id}` | ⚠ 用 edu_id (10001), 非 schId |

### 专业库
- 索引: `https://gaokao.chsi.com.cn/zyk/zybk/`
- 按门类: `/zyk/pub/specInCategory.action?categoryId={门类编号}`
- 详情: 待 Step 4 验证

## 字段 schema (实测 schools_list.json)

```jsonc
{
  "sch_id": 1,                     // chsi 内部 ID, 用于 URL 拼接
  "edu_id": "10001",                // 教育部 5 位编号, 用于跨数据源 join
  "name": "北京大学",
  "province": "北京",              // 注意有前导空格, 用前 strip()
  "governing": "教育部",            // 主管部门
  "degree": "本科",                 // 本科 | 高职(专科)
  "tier": "“双一流”建设高校", // 仅顶尖校有, 其他 None
  "satisfaction": 4.6,             // 浮点, 部分校无
  "detail_url": "https://gaokao.chsi.com.cn/sch/schoolInfo--schId-1.dhtml"
}
```

### 字段覆盖率 (POC 100 校)
| 字段 | 覆盖 |
|---|---|
| sch_id / edu_id / name / province / governing / degree | 100/100 |
| tier (双一流标签) | 39/100 (仅顶尖校) |
| satisfaction | 88/100 (部分校无评分) |

## 工作量估算 (实测 + 推算)

| 阶段 | POC 实测 | 全量推算 |
|---|---|---|
| Step 2 schools_list (1008 校) | 14.6s / 100 校 | ~2.5 min |
| Step 3 单校详情 (4 子页) | (未实测) | 4 子页 × 1.5s × 1008 ≈ 100 min |
| Step 4 专业详情 (893 专业) | (未实测) | ≈ 25 min |
| **全量 scrape 估算** | | **~2-3h** (远小于 plan 16h 估算) |

POC 验证了反爬完全可破解 + 数据 schema 稳定, 全量 scrape 不再需要付费代理.

## 决策点回顾 (拍板时间 2026-06-13)

| # | 决策 | 结论 | POC 验证 |
|---|---|---|---|
| 1 | 代理预算 | 免费慢起 | ✅ 无需代理 |
| 2 | POC 范围 | 100 校 8h | ✅ 14.6s 跑完 |
| 3 | merge 策略 | chsi 覆盖 + report | (Step 5 实施) |
| 4 | 更新频率 | 一次性 | (确认) |
| 5 | 法律 | robots.txt + 2 req/s | ✅ robots 仅禁 `/zzbm/tjr/`, 全站 allowed |

## 下一步 (后续 session)

1. **Step 2 全量**: 跑 `schools_list.py --pages 51` 收 1008 校 (~2.5 min)
2. **Step 3 详情 scraper**: 用 link-mining 自动发现 categoryId, 抓 4 子页
3. **Step 4 专业 scraper**: 893 种专业的课程/就业方向
4. **Step 5 merge**: 合并到 `public/data/school_*.json`, 生成 merge report
5. **Step 6 验证**: 抽样 10 校 (1×985 + 1×211 + 1×双非 + 7 随机)

## 关键文件

| 文件 | 状态 |
|---|---|
| `scrapers/chsi/.venv/` | NEW (patchright + bs4 + lxml) |
| `scrapers/chsi/schools_list.py` | NEW ✅ 跑通 |
| `data/raw/schools_list.json` | NEW (POC 100 校, gitignored) |
| `docs/chsi-scraper-design.md` | NEW (本文) |
