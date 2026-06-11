# DECISIONS.md — 决策记录 (ADR 风格)

> Architecture Decision Records。锁定关键设计选择,防止"为什么这样做"在 6 个月后被改回去。
> 格式: 上下文 → 决定 → 后果。每次重大修改要更新对应 ADR 或加新的。

---

## ADR-001: 3-source merge 策略

**日期**: 2026-06-07
**状态**: ✅ 锁定

### 上下文
2024 历史/物理 真实完整版需要 ~280/~380 行数据,但没有任何单一公开源能完整覆盖 (gk100 只覆盖 1-3 万名,555edu 只覆盖 135 校湖北本地,dxsbb 6261 只覆盖 985/211/重点一本)。

### 决定
3 源合并,优先级:
1. **555edu 逐校抓** (最高优,135 校 × 平均 5 个专业组 = ~600 行,覆盖广)
2. **dxsbb 6261 一本** (中,140 行,985/211 准确)
3. **硬编码锚点** (最低,33 行,作为最后兜底)

代码: `scripts/merge_real_2024.py`,按 `_priority` dict 排序后 `drop_duplicates(subset=["school_name", "group_id"], keep="first")`。

### 后果
- ✅ 254 行物理 / 140 行历史真实本科 (2024 湖北)
- ✅ 优先级明确,改 fetcher 不影响 merge
- ⚠️ 多源 schema 不一致 (`normalize()` 函数处理)
- ⚠️ 同校同 group 跨年可能不一致 (需 `group_id` 跨年稳定)

---

## ADR-002: 555edu per-school 抓取 over gk100 单表

**日期**: 2026-06-07
**状态**: ✅ 锁定

### 上下文
gk100.com/read_38500828.htm 2025 物理 205 行,但 2024 历史只有 33 行 (覆盖前 1-3 万名,普通本科无)。需要更全的数据。

### 决定
555edu.com/hubei/ 列 135 校,每校 `/school-{id}-1-780/{page}` 列文章 (最多 25 页)。对每校找 "2024年湖北{物理/历史}类" 文章,parse 4-schema 通用表。

代码: `scripts/fetch_555edu_hubei.py` + `fetch_555edu_2023.py` + `fetch_555edu_guangdong_jiangsu.py`

### 后果
- ✅ 135 校 × 平均 5 个专业组 = ~600 行,覆盖本地普通本科
- ✅ 4-schema 通用解析 (10-col 本科 / 9-col 高职高专 / 8-col 2023 / 7-col 广东)
- ⚠️ GBK 编码,需 `txt = data.decode("gbk", errors="replace")`
- ⚠️ 每校单独 fetch,~10-15 分钟全量,生产前要 cron 化

---

## ADR-003: 3+3 模式分开 filter 而非合并到 3+1+2

**日期**: 2026-06-07
**状态**: ✅ 锁定

### 上下文
新高考两种模式: 3+1+2 (湖北等 8 省,首选物理/历史必匹配 + 再选任一) / 3+3 (京/沪/津/浙/鲁/琼,6 选 3 无首选概念)。代码里若把 3+3 当 "3+1+2 退化版" 会污染首选概念。

### 决定
`core/filter.py` 分两个函数: `_match_xuanke_3_plus_1_plus_2` / `_match_xuanke_3_plus_3`。`get_xuanke_mode(province)` 按省份集合分发。

```python
def match_xuanke(student_xuanke, required_subjects, mode="3+1+2"):
    if mode == "3+3":
        return _match_xuanke_3_plus_3(student_xuanke, required_subjects)
    return _match_xuanke_3_plus_1_plus_2(student_xuanke, required_subjects)
```

### 后果
- ✅ 概念清晰,无首选污染
- ✅ 3+3 院校要求格式 "X,Y" (任一) 或 "X+Y" (都需) 单独解析
- ⚠️ 加新模式要新加函数 (扩展点已留)

---

## ADR-004: Gaussian CDF 估录取概率

**日期**: 2026-06-06 (Day 1)
**状态**: ✅ 锁定
**代码**: `core/probability.py:23 estimate_admission_probability`

### 上下文
离散分位表 (p10/p50/p90) 需要每年投档表的详细分位,公开数据通常只给最低分/最低位次。Gaussian CDF 可以只用 1 个数 (median rank) 估连续概率。

### 决定
```python
σ = std_rank if std_rank >= min_rank * 0.05 else min_rank * 0.25  # 浮动 25%
z = (student_rank - min_rank) / σ                                    # ⚠️ 用 min 不是 median
P = 0.5 * (1 + erf((-z + 0.7) / √2))                                  # 偏 +0.7 让稳档更宽
category = "冲" if P<0.30 else "稳" if P<0.70 else "保"
```

`+0.7` 偏置: 让学生排名略好于 median 时也归"稳"档,避免 Gaussian 太严格导致志愿太少。

### 后果
- ✅ 只需 min_rank,数据需求低
- ✅ 概率连续,排序更平滑
- ⚠️ 假设 Gaussian — 真实录取分布可能偏态 (头部厚尾)
- ⚠️ σ=25% 是经验值,未在不同年份校准

---

## ADR-005: `strategy_bonus` 不进 sort key

**日期**: 2026-06-07
**状态**: ✅ 锁定 (重要)
**代码**:
- 排序 key: `core/recommender.py:147` `_sort_key = city·100k + layer·1万 + prob·10`
- strategy 调用: `core/recommender.py:162` `_build_strategy_note()` → `core/strategy.py:93 strategy_bonus()`

### 上下文
`core/strategy.py:93` 算出 `strategy_bonus(student_goal, family_bg, school_type)`(0-40 分)。理论上可加进 sort key 让"考公导向"考生优先看 985/211。

### 决定
**不加**。`strategy_bonus` 只用于 `VolunteerItem.strategy_note` 文字(`_build_strategy_note` 在 `core/recommender.py:223` 调用),排序仍按 `_sort_key`。

### 后果
- ✅ 985/211 主导排序,不会因 family=困难 而把 985 排到普通本科之后
- ✅ 策略建议是"参考",不"颠覆"主排序
- ⚠️ 用户需自己看 `strategy_note` 文字理解差异
- ⚠️ 与典型"个性化推荐"系统期望不符 — 这是有意为之

**为什么**: 让"考公"的差学生也能看到冲档的 985 机会,不会因为"考公加权"把志愿限定在 211/普通。

---

## ADR-006: 2024/2023 数据用合成补普通本科

**日期**: 2026-06-07
**状态**: ⚠️ 临时方案 (生产前必须替换)

### 上下文
真实数据:
- 985 完整 (gk100/今日头条整理)
- 211 部分 (gk100 锚点)
- 本省 重点本科 部分 (555edu 抓)

普通本科 + 专科 公开源几乎没有。

### 决定
`fetch_2024_2023_anchors.py` 用 2025 基础 + ±5/±10 名次 波动合成普通/专科部分。`data_source` 字段标 "合成(基于 2025+波动)" 以明示。

### 后果
- ✅ 96 志愿生成有 足够候选 (~140-250 行)
- ⚠️ 普通本科的位次是估的,可能 ±20% 误差
- ⚠️ 文档必须明示用户这是估算
- ❌ 生产前必须替换为 hbea.edu.cn 官方 PDF/Excel

---

## ADR-007: Guangdong/Jiangsu 投档表 group_id 简化为 "01"

**日期**: 2026-06-07
**状态**: ⚠️ 临时方案 (广东/江苏有完整数据后改)

### 上下文
555edu 广东/江苏 2024 文章 schema 是 7-col: `院校名称 | 年份 | 科类 | 选科要求 | 批次 | 投档线 | 投档线位次 | 备注` — **没有专业组代码字段**。

湖北 schema 是 10-col 含 `院校专业组代码` (如 A14108)。

### 决定
广东/江苏 投档表 `group_id` 全部填 "01" (占位)。

### 后果
- ✅ fetcher 通用,广东/江苏 可用
- ⚠️ 同校多组无法区分 (实际广东 2024 改革无专业组,所以单组合理)
- ❌ 若广东/江苏 改革后恢复专业组,要重新设计

---

## ADR-008: dxsbb 6261 缺位次用 score→rank 一分一段反查

**日期**: 2026-06-07
**状态**: ✅ 锁定

### 上下文
dxsbb 6261 表格只有 投档线 (score),没有 投档线位次 (rank)。其他源 (555edu / 锚点) 都直接给 rank。

### 决定
`scripts/fetch_dxsbb_6261.py` 加载 2024 一分一段表,对每个 score 反查 rank:

```python
def score_to_rank(score, rank_table):
    eligible = rank_table[rank_table["score_int"] <= score]
    return int(eligible.loc[eligible["score_int"].idxmax()]["rank"])
```

### 后果
- ✅ 唯一缺位次的数据源被挽救
- ⚠️ 反查是近似 (同分有多个考生,实际位次是范围)
- ⚠️ 误差约 1-5 名,不影响 96 志愿生成

---

## ADR-009 (待写): 3+3 模式真实数据未做

**日期**: —
**状态**: ⏳ pending

### 上下文
京/沪/津/浙 4 省 3+3 模式代码 ready,但无真实一分一段表 / 投档表。

### 决定
(待做) — `eol.cn` 抓 3+3 一分一段表; 3+3 投档表按 2024 新高考 (教育部统一) 抓 hbea 等价源。

---

## ADR-010 (待写): PDF 报告省份硬编码

**日期**: —
**状态**: ⏳ pending

### 上下文
`api/pdf_report.py` 中 `province` 映射只有 湖北/广东/江苏/其他,其他省份 PDF 文件名 fallback。

### 决定
(待做) — 用 `core/data_loader.get_all_provinces()` 替代硬编码。

---

## ADR-011: 两阶段部署策略（EdgeOne Pages 海外 → 大陆）

**日期**: 2026-06-11
**状态**: ✅ 锁定
**对应 plan**: `docs/DEPLOYMENT.md` 阶段 0-2

### 上下文
用户要把项目部署到个人网站,但 ICP 备案需要 15-20 天。期间网站不能停摆。

候选方案:
- (A) 直接等备案完再部署 — 浪费 15-20 天
- (B) 用 Vercel/Netlify 海外节点 — 同上,但国内访问慢
- (C) EdgeOne Pages "全球可用区（不含中国大陆）" + 备案后切到 "全球可用区（含中国大陆）" — 无需备案,流量走香港/海外节点

### 决定
**采用 (C) 两阶段方案**:

| 阶段 | 加速区域 | 备案要求 | 国内访问 |
|------|---------|---------|---------|
| 阶段一 | 全球可用区（不含中国大陆） | 不需要 | 走香港/海外节点 30-80ms |
| 阶段二 | 全球可用区（含中国大陆） | 必须备案 | 国内 2300+ 节点 < 30ms |

**关键优势**: DNS 解析**只配一次**,代码**只部署一次**,阶段二只是把 EdgeOne Pages 项目迁移到新区域(或新建一个项目切 DNS)。

### 后果
- ✅ 备案期间网站正常服务,零中断
- ✅ 阶段二切换零代码改动,零数据迁移
- ⚠️ EdgeOne Pages "加速区域" 通常**项目创建时锁定**,不是开关 → 阶段二可能需要"新建项目+DNS 切换" 而不是 toggle
- ⚠️ 阶段一国内访问比备案后慢 2-3 倍,但比 Vercel/Netlify 直连快很多

---

## ADR-012: LLM 临时搜索后端走腾讯云 SCF（不用 FastAPI 容器）

**日期**: 2026-06-11
**状态**: ✅ 锁定
**对应 plan**: `docs/DEPLOYMENT.md` 阶段一

### 上下文
用户预期上线后: 输入专业名 → 61 个已有专业走静态 HTML,未收录专业临时调 LLM 合成 HTML。LLM API key 不能暴露在浏览器(会被刷额度),必须有后端中转。

候选方案:
- (A) 保留 FastAPI 容器部署在阿里云轻量 — 需常驻服务器,~100 RMB/年
- (B) FastAPI 部署在海外 Render/Railway — 免费层 750h/月,但国内访问慢 + LLM 调用延迟高
- (C) **腾讯云 SCF 香港地域** — serverless,免费层 10万次/月,冷启动 ~1s,无需备案

### 决定
**采用 (C) SCF 香港地域**:
- 函数代码 ~50 行 Python 3.11,接收 `?q=专业名` 调 DeepSeek API
- API 网关触发器,路径 `/search-major`
- CORS 允许 `https://yourname.cn`
- 环境变量注入 `DEEPSEEK_API_KEY`
- 前端 1 次/秒 throttle + SCF 入口按 IP rate-limit (10次/分钟)

### 后果
- ✅ 0 成本(serverless 免费层 10万次/月足够个人站)
- ✅ 无需常驻服务器,无需备案
- ✅ 阶段二 ICP 完成后,函数克隆到广州/上海地域即可,代码不动
- ⚠️ 冷启动 ~1s,搜索场景可接受
- ⚠️ DeepSeek API 输出不稳定 → prompt 加 schema 约束,返回结构化 JSON

---

## ADR-013: 备案主体用阿里云轻量（跨厂商架构）

**日期**: 2026-06-11
**状态**: ✅ 锁定
**对应 plan**: `docs/DEPLOYMENT.md` 阶段二

### 上下文
ICP 备案必须用大陆注册商+大陆服务器作主体资格。用户已有阿里云 2C4G 轻量,但没腾讯云服务器。

候选方案:
- (A) 新买腾讯云轻量(~100 RMB/年) + 域名迁腾讯云 DNSPod — 跨厂商管理,域名和备案都过腾讯云
- (B) 用现有阿里云轻量作备案主体 + 域名走阿里云万网 — 单厂商管理,备案和落地都在阿里云

### 决定
**采用 (B) 跨厂商架构**:
- 域名: 阿里云万网购买 (`.cn` ~30 RMB/年)
- 备案主体: 现有阿里云 2C4G 轻量(完全够用,纯静态前端部署后这台只作备案用)
- 静态托管: EdgeOne Pages (腾讯云)
- LLM 后端: SCF (腾讯云) — 备案后切到境内地域
- 跨厂商用 API 网关互联,域名 CNAME 指向 EdgeOne Pages

### 后果
- ✅ 不需要新买服务器
- ✅ 域名和备案统一在阿里云,工单/对接顺
- ✅ EdgeOne Pages 和 SCF 跨厂商也完全 OK(都是公开 API)
- ⚠️ DNS 跨厂商,故障排查需要查两边控制台
- ⚠️ 备案期间 EdgeOne Pages 海外区域继续跑,不受影响

---

## ADR-014: 捐赠走纯静态方案（赞赏码 + 外链）

**日期**: 2026-06-11
**状态**: ✅ 锁定

### 上下文
"无须注册账号"的捐赠功能, 3 种实现路径:
- (A) 微信/支付宝商户号 + 后端签名 — 需商户认证,个人难申请
- (B) Stripe Checkout — 海外用户友好,需后端生成 session
- (C) **微信赞赏码 + 支付宝收款码 + 爱发电外链** — 纯静态图片/外链,0 后端

### 决定
**采用 (C) 纯静态方案**:
- 微信赞赏码: 截图存 `dist/donate/wechat-qr.png`
- 支付宝收款码: 截图存 `dist/donate/alipay-qr.png`
- 爱发电/BuyMeACoffee: 加个 `<a href="..." target="_blank">` 外链
- 入口: 主页 footer 放一个"支持作者" 链接 → `dist/donate/index.html`

### 后果
- ✅ 0 成本, 0 后端, 0 维护
- ✅ 国内用户最熟悉的支付方式
- ✅ 5 分钟搞定
- ⚠️ 不显示捐赠进度/排行榜(对个人项目不重要)
- ⚠️ 海外用户走爱发电汇率损耗,小额可以接受

---

## ADR-015: 部署实施延后到前端定型

**日期**: 2026-06-11
**状态**: ✅ 锁定
**用户原话**: "先不急做实际准备工作,等前端真的定型后再开始不迟"

### 上下文
用户说"前端还要大改,届时我会在前端设计时明确部署要求"。意思是:
- 现在 `frontend/index.html` 还是 v0.1 原型(强依赖 FastAPI 后端)
- 改完后 UI/数据契约/调用方式都会变
- 提前写 SCF 函数、IaC 配置、build_static.py 会做无用功

### 决定
**部署实施延后**:
- 阶段 0 准备工作(买域名、注册腾讯云账号、申请阿里云备案)用户自己推进
- 阶段一实施(写 SCF、写 build、写前端) 等用户说"前端定型了"再开始
- 期间 `docs/DEPLOYMENT.md` 作为 reference, **不催代码生成**

### 后果
- ✅ 避免提前做无用功
- ✅ 前端定型后可以一次性把 SCF + 静态构建 + 前端集成做完
- ⚠️ AI agent 看到 "准备部署" 类的请求 → 先问"前端定型了吗?", 引用 ADR-015

---

## 如何添加新 ADR

```bash
# 1. 复制本文件末尾的"待写"模板
# 2. 编号递增
# 3. 状态: 提议 → 锁定 / 弃用 / 过期
# 4. 引用代码路径 (file:line)
# 5. 后果必须列"好处"和"坏处"
```

模板:
```markdown
## ADR-NNN: <一句话>

**日期**: YYYY-MM-DD
**状态**: ⏳ pending / ✅ 锁定 / ❌ 弃用 / 🕐 过期

### 上下文
<为什么做这个决定>

### 决定
<做了什么>

### 后果
- ✅ 好处
- ⚠️ 风险
- ❌ 失败条件
```
