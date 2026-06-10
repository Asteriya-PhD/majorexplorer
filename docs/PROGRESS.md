# PROGRESS.md — 进度 / 状态 / 已知缺口

> 时间戳: 2026-06-10 (最后更新) · 上一版 2026-06-07

## 0. 2026-06-10 里程碑 B — 8 主题清理 + 2 套新 hero ✅

**Commits**: `e5b0aab` rebrand → `af725bf` 8 主题清理 → `80cfc8b` polish (3 commit, 2026-06-10 下午)

### 战报

| 指标 | 6/10 上午 | 6/10 下午 | 变化 |
|---|---|---|---|
| 主题数 | 10 | **8** | -2 (-20%) |
| 学科色主题 | 5 (cs/eng/medicine/education/finance) | 5 + 1 tech | 智 / 工业设计 / 土木 归位 |
| 人文类主题 | 0 (塞在 tech_ruyao) | 1 (**humanities**) | 新名, 视觉用"古籍线装书" |
| 行政类主题 | 0 (塞在 tech_qinghua) | 1 (**administration**) | 新名, 视觉用"国发公文" |
| 文化色硬塞 | tech_ruyao (4) + tech_qinghua (4) = 8 个孤儿 | 0 | 全部按学科色归类 |
| 空主题 | tech_ink (0 专业) | 0 | 删 |

### 8 主题最终分布 (50 套)

```
cs              × 11  (含 智能  ← tech)
eng             × 10  (含 工业设计 工业设计 ← education, 土木 ← cs)
medicine        ×  6
education       ×  5  (工业设计 离)
finance         ×  5
sci             ×  4
humanities      ×  4  (哲学/考古/汉语言/历史) — 古籍线装书视觉
administration  ×  4  (财务/信管/图书馆/行政) — 国发公文视觉
law             ×  1
                ────
                50 ✓
```

### 2 套新 hero 设计 (用户已批准)

**humanities (古典人文)**:
- 视觉锚: 翻开的线装书 (深棕墨 #1F140A + 茶染宣纸 #F2E8D5 + 皮革棕 #8B5A2B + 朱砂 #9A2A2A)
- 主标题: 思源宋体"历史学" + Cormorant Garamond 英文
- 装饰: 9 孔装订 + 朱砂引首章 + 思源宋体"史"水印 + 校勘式 stats + 壹/貳/參/肆 目录 + 金箔飘落 + 古碑拓片 + 异体字校勘 + 岳麓书院藏版底署
- 字体: Noto Serif SC + Ma Shan Zheng + ZCOOL XiaoWei + Long Cang
- 4 成员: 哲学 / 考古学 / 汉语言文学 / 历史学

**administration (行政事务)**:
- 视觉锚: 国发公文 (政府蓝 #1E3A5F + 米白 #FAFAF6 + 政府红 #C0392B + 金 #D4AF37)
- 主标题: Noto Serif SC"财务管理" + 4 标签 chips (商业文员 / CPA / 万金油 / 稳定 / 中年门槛 / 偏会计)
- 装饰: 国发红头 + 中华人民共和国教育部 + 国徽圆章 (textPath 弧形"教育部·高等教育研究司") + 4 案卷卡 stats + "已归档·内部资料" 骑缝章 (polish 后 10px→16px, 更印章化)
- 字体: IBM Plex Serif / IBM Plex Mono / Noto Serif SC
- 4 成员: 财务管理 / 信息管理与信息系统 / 图书馆学 / 行政管理

### 关键决策

1. **逆向思维** — 之前: 主题(色) → 找匹配的学科 (硬塞). 之后: 看 51 套哪些不适合归类 → 给"孤儿"专门设计学科色. 这是用户拍板的方向.
2. **English 命名** — `grrw` / `xzzw` 拼音不符合其他主题风格, 改 `humanities` / `administration`. 跟 cs/eng/sci/finance/medicine/law/education 统一.
3. **保留 tech** — 用户决定 tech 保留作为"未来感 AI"分支 (智能科技 + 1 个扩展空间).
4. **.tmp-hero/ 入 .gitignore** — 设计样本/Playwright 截图不纳入仓库.

### 技术改动 (3 commit 累计)

- v4_styles.py: 删 TECH_INK_CSS / TECH_RUYAO_CSS / TECH_QINGHUA_CSS (~560 行) + 加 HUMANITIES_CSS (~250 行) + ADMINISTRATION_CSS (~250 行) + 6 处 .path-grid 改 repeat(3, 1fr) + .path-name 移出 nowrap + .gov-seal-strip 印章化
- generate_dashboard.py: STYLE_TOKENS + FONT_URLS 改 + dispatch tuple
- SKILL.md: 10 套 → 8 套风格映射
- manifest.json: 9 styles_used + 50 majors style 字段
- 11+38 = 49 HTML 重渲染 (manifest.json 保留)

### 已知小问题

- `v4_styles.py:1538` `\|` SyntaxWarning (历史遗留, 不影响输出, 单字符修)
- humanities/administration 简化版 hero (引擎 200-400 行) 视觉比 sample (1000+ 行) 略简化, 但核心视觉锚抓到了, 用户已批准

---

## 0.5. 下一阶段目标 — major-explorer (2026-06-10+)

按 ROI 排序, 用户拍板后逐个开.

### ⭐⭐⭐⭐ A. 未覆盖专业审计 + 下一批主题设计 (0.5 天)

**为什么**: 今天的工作找到了"先看 50 套哪些不适合归类, 再给孤儿设计主题"的逆向方法. 把这个流程批量化, 找下一批 2-3 个孤儿主题 + 10-20 个新专业, 一次 ship.

**预期**:
- 审计未覆盖的 700+ 高考专业, 找 2-3 个"大但低频"或"独立类目":
  - **美术** (10+ 子专业, 走艺考路径, 视觉可走"画室/画布/调色盘" 美学)
  - **医学技术** (检验/影像/康复/口腔医学技术, 跟 medicine 主题区分)
  - **农林** (林学/园艺/动物科学, 视觉可走"自然/田野/植物图鉴" 美学)
  - **新闻传播子类** (广告/编辑出版/网络与新媒体, 跟现 education 里的 journalism 区分)
  - **音乐/体育** (走特长生路径, 视觉锚 "五线谱/跑道/球场")
- 选 1-2 个审计出的新主题, 走今天同样流程: Awwwards sample → 用户挑 → 整合 v4_styles.py
- 同时新增 10-20 个精品专业 HTML

**产出**:
- v4_styles.py: 1-2 个新 CSS + hero 函数
- 10-20 个新 JSON + HTML
- 1 个新 commit

---

### ⭐⭐⭐ B. 长尾 700 专业 web search 自动化 (1-2 天)

**为什么**: 当前 50 套是手工精编, 7-8 分钟/套. 剩下 700+ 长尾用同样手工流程太慢. 模板化 + web search 自动化是规模化的必要步骤.

**预期**:
- 1 套共享模板 (data_source 字段标 "自动生成" 区分精品 vs 实时)
- web search 5 query 并行 (5 路 Agent/WebSearch) → 整合 → 模板渲染
- 跟 50 套精品用同一 render_v4() 引擎
- 长尾页 SEO 收录 (用 sitemap 推)

**产出**:
- 长尾渲染脚本 (新)
- 700+ HTML 自动生成

---

### ⭐⭐ C. 首页/SEO 整合 (0.5-1 天)

**为什么**: 50 个精品 HTML 是散点, 缺一个总入口 (gaokao 主页) + sitemap + meta tags. 现在搜索引擎收录不上.

**预期**:
- 主页 1 个 HTML: 50 个精品按主题分组 + 链接
- sitemap.xml 自动生成 (50 + 后续长尾)
- 每个 HTML 加 og:image / twitter:card / description meta
- robots.txt 引导爬虫

**产出**:
- index.html (新)
- sitemap.xml + robots.txt (新)
- 所有 HTML + meta tags (批改)

---

### ⭐⭐ D. 关联志愿引擎接入 (1 天)

**为什么**: 每个专业的 "如何填报" CTA 现在是静态文字, 接 core/recommender.py 后, 用户填分数+选科 → 返回真实学校池 → CTA 跳转志愿推荐.

**预期**:
- 选科+分数表单 UI (前端)
- 调 recommender API (后端已有)
- 渲染返回的学校列表 (新增 section "适合你的学校")
- 用现湖北/广东/江苏 真实投档表 (从 2024/2025 抓的数据)

**产出**:
- HTML 端新增 "志愿推荐" section + 表单
- API 端点 (可能已有, 接通)
- 1 个新 commit

---

### ⭐ E. .tmp-hero/ 清理 + 杂项 (10 分钟)

**为什么**: 11 个 sample HTML (5 个旧 tech_*/3 个新 design sample/2 个 verify) + 10+ PNG/MD 仍在磁盘, 已 gitignore 但占用空间.

**预期**:
- `rm -rf .tmp-hero/` (纯临时, 已 gitignore)
- v4_styles.py:1538 `\|` SyntaxWarning 修 (单字符 r-string)
- PROGRESS.md 时间戳更新

**产出**:
- 1 个微 commit (cleanup + 文档)

---

## 0. 2026-06-10 里程碑 A — gaokao-major-explorer 50 精品专业完整矩阵 ✅

**Commit**: `48c491b feat(skill): gaokao-major-explorer 50 精品专业完整矩阵` (+39,636 / -1,671 lines · 91 files)

### 关键战报

| 指标 | 6/7 状态 | 6/10 状态 | 增量 |
|---|---|---|---|
| 精品专业数 | 21 | **50** | +29 (+138%) |
| 主题 (style) 数 | 5 | **10** | +5 (+100%) |
| sci/eng 主题 | — | sci × 4 / eng × 8 | 新增 |
| 提交 commit 数 | 3 | 6 | +3 |
| 完整 HTML 总大小 | ~1.2 MB | ~3.2 MB | +2.0 MB |

### 新增主题 (5 → 10)

| Style | 数量 | 适用学科 | 视觉气质 |
|---|---|---|---|
| `sci` (米色学术) | 4 | 数理化/大气 | Nature 期刊 + 衬线大字 + 公式 |
| `eng` (浅米工程) | 8 | 工科硬核 | CAD 蓝图 + Inter Condensed + 零件清单表 |
| (其余 5 主题复用) | — | — | — |

### 29 个新专业 (P1 顶级 15 + P2/P3 14)

**批 1 (P1 顶级热门):** 数学与应用数学、物理学、化学、经济学、国际经济与贸易、财务管理、机械工程、材料科学与工程、化学工程与工艺、药学、中医学、汉语言文学、历史学、行政管理、应用心理学

**批 2 (P2+P3):** 微电子科学与工程、集成电路设计与集成系统、信息管理与信息系统、工业设计、车辆工程、食品科学与工程、预防医学、麻醉学、智能科学与技术、哲学、考古学、飞行器设计与工程、大气科学、图书馆学

### 当前主题分布 (50 个)

```
cs           × 11  ▇▇▇▇▇▇▇▇▇▇▇  终端黑客
eng          ×  8  ▇▇▇▇▇▇▇▇      浅米工程
medicine     ×  6  ▇▇▇▇▇▇        手术仪表
education    ×  6  ▇▇▇▇▇▇        暖橙学术
finance      ×  5  ▇▇▇▇▇          烫金
sci          ×  4  ▇▇▇▇            米色学术 (新)
ruyao       ×  4  ▇▇▇▇            鼠尾草 (新)
qinghua     ×  4  ▇▇▇▇            暖白深青 (新)
tech         ×  1  ▇                暗紫青绿
law          ×  1  ▇                羊皮卷宗
```

### 关键技术决策

1. **sci/eng 主题快速集成** — 复用 `EDUCATION_CSS` 框架 + 自定义 body bg + 自定义 hero, 集成仅 ~200 行
2. **p0-majors-batch 硬编码 15 P0** — 不能用自定义参数, 改用直接 spawn 15 + 14 sub-agent
3. **每个 sub-agent 跑 5 路 web search + 编 JSON + 渲染** — 平均 ~2-5 分钟, 成功率 100%
4. **WebSearch 偶发 400** — 6 个 agent 退而用稳定公开数据 (学科评估/麦可思 2024/同档 JSON 薪资) 兜底

### 接下来候选

- A. 跑 50 个视觉批量截图 (Awwwards-grade 提交用)
- B. 长尾模式模板化 (700 个其他专业 web search 自动化)
- C. 首页/SEO 整合 (50 个链接入 gaokao 主页)
- D. 关联志愿引擎接入 (core/recommender.py → cta 真实位次)
- E. 主题继续细化 (医学技术/农林/艺术 等细分)

---

## 1. 当前状态:v0.2.0 (Production-ready for 湖北)

**项目年龄**: ~2 天密集工作 (2026-06-06 ~ 2026-06-07)
**总代码量**: ~7 核心模块 + 10 fetcher 脚本 + 4 测试 + 7 endpoint
**测试**: 20/20 通过 (`pytest tests/`)
**数据 CSV**: 29 个, ~8,273 行
**Git**: 3 commits (全部 2026-06-07)

### Commit 时间线
```
712db05  feat: 广东/江苏 MVP 真实数据
90deed7  feat: 2023 物理/历史 真实数据 + 广东/江苏 适配
243a576  feat: 2024 历史/物理 真实完整版 + 555edu/dxsbb 抓取
```

## 2. 模块完成度

| 模块 | 完成度 | 状态 |
|---|---|---|
| 核心算法 (recommender / probability / filter / strategy / equivalent / rank_utils) | 100% | ✅ 生产可用 |
| 多模式选科 (3+1+2 / 3+3) | 100% | ✅ 湖北/广东/江苏 3+1+2;京/沪/津/浙/鲁/琼 3+3 |
| API 层 (7 endpoints + PDF) | 100% | ✅ 本地可跑 |
| 前端 (单页 HTML) | 80% | ✅ 基本工作,UI 不够 polish |
| 数据抓取 (10 fetcher) | 100% | ✅ 湖北 2025 全真, 2024 合并, 2023 部分真 |
| 测试 (4 文件) | 70% | ✅ 核心 + 回测;3+3 mode / api endpoints / strategy 数值未测 |
| 文档 (5 份) | 100% | ✅ AGENTS/ARCHITECTURE/PROGRESS/DECISIONS/DATA |
| 部署 (Docker / gunicorn / nginx) | 0% | ❌ 仅本地 |
| 监控 / 日志聚合 | 0% | ❌ 仅 stderr |

## 3. 数据真实性矩阵 (按省/科/年)

| 省份 | 科类 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| 湖北 | 物理 | — | ⚠️ 242 (555edu 43 校 + 锚点) | ✅ 324 (4 源合并 = 555edu + dxsbb6261 + dxsbb OCR + 锚点) | ✅ 205 (gk100 全) |
| 湖北 | 历史 | — | ⚠️ 128 (555edu 43 校 + 锚点) | ✅ 194 (4 源合并 = 555edu + dxsbb6261 + dxsbb OCR + 锚点) | ✅ 103 (gk100 全) |
| 广东 | 物理 | — | — | ⚠️ 70 (555edu 锚点级) | — |
| 广东 | 历史 | — | — | ⚠️ 64 (555edu 锚点级) | — |
| 江苏 | 物理 | — | — | ⚠️ 79 (555edu 锚点级) | — |
| 江苏 | 历史 | — | — | ⚠️ 74 (555edu 锚点级) | — |
| 京/沪/津/浙/鲁/琼 | 物理/历史 | — | — | ❌ 无 | — |

**图例**: ✅ 全真(可生产) / ⚠️ 部分真(锚点级,普通本科靠 555edu 抓) / ❌ 无数据 / — 未抓

**一分一段表**:
- 湖北 2023/2024/2025 ✅ 全真 (gxzsxxw / eol.cn / gk100)
- 广东/江苏 2024 ⚠️ 公开锚点插值 (700/600/580/525/400)
- 其他 ❌ 无

## 4. 已完成的关键工作 (近 2 天)

### Day 1 (2026-06-06)
- 初始化: 9 大模块 + CLI + API + 4 测试
- 湖北 2023-2025 样本数据生成器
- `core/recommender.recommend` 主流程 + Gaussian CDF 概率
- `core/filter` 3+1+2 选科过滤
- 张雪峰式 strategy (6 actionable strategies)
- 9 个核心测试通过

### Day 2 (2026-06-07)
- **commit 243a576** — 2024 历史/物理 真实完整版
  - 555edu 逐校抓取器(4 schema 通用解析)
  - dxsbb 6261 一本表 fetcher
  - 3 源合并 (锚点 + dxsbb6261 + 555edu)
  - 254 行物理 / 140 行历史真实本科
- **commit 90deed7** — 2023 物理/历史 真实数据 + 广东/江苏
  - 2023 fetcher 4-schema 支持(含 score→rank 反查)
  - 242/128 行 2023
  - 广东/江苏 一分一段表生成器 (锚点插值)
- **commit 712db05** — 广东/江苏 MVP
  - 555edu 广东/江苏 fetcher (169/170 校)
  - 70/64 (GD) + 79/74 (JS) 行
- **filter.py** 扩展 3+3 模式 (京/沪/津/浙/鲁/琼) 20 种选科 + 选考匹配
- **data_loader.get_all_xuanke_options** 按省份自动选模式
- **recommender** group_id 强转 str 修 pydantic ValidationError
- 20/20 测试通过(含参数化 4 个真实投档表回测)
- **本次 init** — 5 份 docs + README 指针

## 5. 已知缺口 (按优先级)

### 阻塞生产
- ❌ **广东/江苏 数据只锚点级** (64-80 行,远不够 96 志愿)— 需 eol.cn / 考试院 PDF
- ❌ **2022 及以前数据无** — 历史回测至少要 3 年才有意义
- ❌ **招生计划年际变化未量化** — 同校缩招/扩招 5% vs 20% 风险不同,目前当静态

### 功能性
- ❌ **LLM 解释层未做** — 推荐目前只给"985 高校"等短语,无 LLM 解释"为什么"
- ❌ **体检/选科级联过滤 UI 未做** — 选科和体检是 cli 参数,前端 UI 未接
- ❌ **3+3 mode 未真测** — 代码 ready 但无真实 3+3 数据,只有单元测试
- ❌ **2024 广东/江苏** 用 555edu 广东 7-col schema, group_id 简化为 "01" (ADR-007)

### 质量
- ❌ **`core/recommender._sort_key` 不含 `strategy_bonus`** — 已 ADR-005 锁定,但需文档化
- ❌ **`api/pdf_report.py` 省份硬编码 3 个** — 其他省份 PDF 文件名 fallback
- ❌ **`core/filter` 对 555edu 简版 schema 假设 2025 列** — 实际旧版 CSV 可能缺 school_type/xuanke_subjects 等
- ❌ **3 个测试用 `if __name__ == "__main__"` script-style,只 1 个用 pytest** — 不一致

### 部署
- ❌ 无 Dockerfile / gunicorn / nginx 配置
- ❌ 无日志聚合 (只有 stderr)
- ❌ 无监控/告警
- ❌ 无 CI/CD (`.github/workflows/` 不存在)

## 6. 下一里程碑候选

| 候选 | 工作量 | 价值 |
|---|---|---|
| OCR dxsbb 完整 2024 历史 PNG → ~280 行真实 | 0.5 天 | 2024 历史从 140 → ~250 行,接近"完整版" |
| eol.cn 抓 广东/江苏 2024 一分一段 + 投档表 | 1 天 | 锚点级 → 完整级 |
| Docker 化 + gunicorn | 0.5 天 | 可部署 |
| 体检/选科级联过滤前端 UI | 1 天 | UX |
| LLM 解释层 (用 MiniMax / 内部 LLM) | 1-2 天 | 差异化 |
| 历史回测 (用 2024 真实投档表回测 2023 推荐) | 1 天 | 命中率验证 |
| `pdf_report` 省份硬编码修复 | 0.1 天 | 清理 |
| 3+3 mode 真实数据 + 测试 | 1 天 | 真正支持 6 省 |

## 7. 引用

- 决策动机: `docs/DECISIONS.md`
- 数据细节: `docs/DATA.md`
- Agent 入口: `docs/AGENTS.md`
- 架构: `docs/ARCHITECTURE.md`
- README: `/README.md`
- 原始已知限制: `/README.md` 末尾的 7 条
