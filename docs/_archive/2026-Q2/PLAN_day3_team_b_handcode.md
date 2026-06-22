# Day 3 Team B Hand-Code Plan (47 篇 ≥ 8/10)

**目标**: 把 m3 content_audit 5.60/10 平均提升到 ≥ 8/10
**当前状态**: 47 篇已 push `day3-team-b` (commit `fc1a9bd`), 3 防线 100% clean, 数据真实但 m3 audit 中位数 5.60
**预计工时**: 47 × 30min = 23.5h serial, 建议分 4-5 个 session 完成
**开始时间**: 下次重开会话

---

## 优先级框架 (按 m3 audit 分)

- **P0 (≤4/10)**: 完全重做, ~9 篇, 估时 6h
- **P1 (5/10)**: 关键字段修复, ~20 篇, 估时 10h
- **P2 (6/10)**: 微调, ~10 篇, 估时 4h
- **P3 (≥7/10)**: 验收/微调, ~8 篇, 估时 2h

---

## P0: ≤ 4/10 必须完全重做 (9 篇)

### 1. 计算语言学 (2/10) — worst, 整篇要重做
**问题**:
- lede:6 (凑数)
- salary:6 (p75 应上修到 18-22 万)
- curriculum:1 (核心课组全空, 5 校特色是公共必修复读)
- top_schools:0 (缺失)
- alumni_quotes:0 (缺失)

**必修**:
- 补全 curriculum: 语言学概论/现代汉语/形式语言学与自动机/语料库语言学/自然语言处理/机器学习/Python 程序设计
- 5 校特色选修按 NLP/语音/数字人文/理论语言学/机器翻译 分流
- 补 top_schools: 北大计算语言学所/清华/南大文学院/哈工大 SCIR/北语/复旦/中科院自动化所
- 补 alumni_quotes 3 条 (含具体课程/项目, e.g. CRF 中文分词毕设)
- 补 deep_study (读研 50-60% NLP PhD, LLM 时代 30-60 万 头部)
- 补 pitfalls (文学学位 vs CS 学位歧视, 特设专业认可度)
- 压缩 summary 到 150 字内, lede 用 "文学门类下半文半理 AI 预备" 这类判断式开头

### 2. 播音与主持艺术 (4/10)
**问题**: lede:1 (整段套外国语言文学模板), who_fits 数学/考证残留
**必修**:
- 重写 lede: "声音训练+镜头表达+即兴反应" 实操定位
- 重写 who_fits/pitfalls: 删数学/考证, 加艺考集训成本/AI 主播冲击/声音衰退/形象内卷
- 删除 deep_study 中的 CS/金融跨学科, 博士压到 3% 以下, 直接就业提到 55%+
- 替换 top_schools: 用北京电影学院/暨南大学替换天津工业/湖南大学

### 3. 文物与博物馆学 (4/10)
**问题**: lede/who_fits:1 (AI 作文/数学经济模板), curriculum:3 (重复), summary/what_you_learn:2 (重复)
**必修**:
- 重写 lede/who_fits: 文博视角 (文物/考古/博物馆策展/文化遗产)
- 重做 curriculum 5 校特色选修: 北大科技考古/吉大边疆考古/复旦文化遗产/南大六朝考古/西大佛教考古
- summary 与 what_you_learn 差异化
- 补 employment_direction
- 重写 pitfalls: 田野体力/编制竞争/器物过眼经验/保护化学门槛

### 4. 思想政治教育 (4/10)
**问题**: who_fits:1 (数学/统计/经济/考证串台)
**必修**:
- 重写 who_fits: 政治理论兴趣/文字功底/表达沟通/体制内发展意愿
- 重写 lede/pitfalls: 体制内通道 (选调/公务员/教师编) / 师范教师编稳定/政策研究入门 / 害处: 市场化弱/跨行难/选科限制
- top_schools 增补 人大/北师大/华东师大/东北师大
- deep_study 跨学科 CS/金融 12% 改 5% 以下, 出国 8% 改 3%, 补 "行政管理/人力资源/教育管理" 真方向

### 5. 卫生健康法学 (4/10)
**问题**: lede:3, who_fits:2 (数学统计经济), xuanke_req:2 (错误: 物理化学生物)
**必修**:
- who_fits: 法学/医学常识/生命伦理/公共政策导向, 删数学统计经济
- xuanke_req: 政治(首选)/不限选科, 删物理化学生物
- pitfalls: 无独立学科评估/医院法务岗集中度/医药反腐影响案源/医学课程广而不深
- 修 lede 截断, 补 民法/刑法/行政法 法学硬核心
- 5 校特色选修: 真实列出 5 所学校具体方向

### 6. 电子科学与技术 (4/10)
**问题**: lede:1, who_fits_no:0 (机械/材料/文本阅读模板)
**必修**:
- 重写 lede/who_fits_no: 强相关电科描述
- curriculum 重归类: 电路原理/模电/数电/电磁场/固体物理/信号与系统 → 核心课
- 量子电子/FinFET 挪到特色选修
- pitfalls: 模拟 vs 数字学历门槛/版图岗被低估/示范性微电子学院资源差距
- top_schools: 电子科大/西电/东南/清华/北大/复旦/上交/北航/哈工大/华科 (按微电子评估)

### 7. 风景园林 (4/10)
**问题**: lede:1 (智慧农业/分子育种串台), curriculum:2 (核心课缺)
**必修**:
- 重写 lede: "尺度弹性" + "生态-工程-美学三栖"
- curriculum: 园林植物学/园林工程/园林史/城市绿地系统/园林建筑/城市规划原理 8-10 门
- 5 校特色选修: 设计/工程/植物/规划/生态 分流
- pitfalls/who_fits_no 全部重写风景园林专属
- deep_study 跨学科 CS/数据/金融 从 12% 改 ≤5%

### 8. 水利水电工程 (4/10)
**问题**: lede:4, who_fits_no:1 (人文写作串台), curriculum:4, pitfalls:2
**必修**:
- 修 who_fits_no 和公共必修: 工程力学/水力学 相关
- pitfalls: 项目周期长/抽蓄选址局限/水电移民环保政策/长期野外作业
- 补 employment_direction
- what.foundations/directions 差异化

### 9. 光电信息科学与工程 (4/10)
**问题**: lede:2, who_fits_no/pitfalls:1 (文科残留), deep_study:2
**必修**:
- 重写 who_fits_no/pitfalls: 物理基础差/晕光学装调实验/不愿学 ZEMAX/不读研难进核心岗
- 重写 lede: "光学+电子+信息三栖" 独有视角
- deep_study 重分配: 国内读研 45%/直接就业 25%/出国 15%/读博 10%/跨行 5%

---

## P1: 5/10 关键字段修复 (20 篇)

| Slug | 核心问题 | 必修 |
|------|----------|------|
| 翻译 (5) | who_fits 数学经济串台, deep_study 失真 | who_fits/pitfalls 翻译专属, deep_study 调 PhD 5%/跨学科 5-8% |
| 日语 (5) | who_fits 套话, deep_study 升学率失真 | who_fits 改日语特性, 升学率 40% → 25-30%, 博士 5% |
| 民族学 (5) | salary 0, top_schools 缺 | 补 salary/top_schools/pitfalls 独立字段, curriculum 3 层去重 |
| 数字人文 (5) | deep_study 缺, 特色选修雷同 | 补 deep_study 路径分布, 5 校特色选修按校 (北大/武大/...) 区分, pitfalls DH 专属 |
| 工程力学 (5→6) | top_schools 排错, 缺 what/fit 数组 | 哈工大/大连理工/北航 提前, 补中科大/西工大, tag 填实 |
| 金融法 (5) | salary 严重低估, curriculum 串 | salary p75 25-35 万, curriculum 列银行/证券/保险/信托/金融监管法, pitfalls 金融法专属 |
| 网络与信息法学 (5→6) | curriculum 缺专业课, 选科错 | 加网络安全法/数据法/个人信息保护法/算法治理, 选科政治(首选) |
| 大数据管理与应用 (5) | top_schools 仅 1, 重复课 | 扩 8 校按财经类/理工类分流, 删 3 重复课, 补 employment_direction |
| 信用管理 (5) | 选科错, 5 校特色同 | 删"选考物理", 5 校按校区分, lede 改征信牌照收紧洞察 |
| 跨境电子商务 (5) | who_fits 持证串台, 重复 3 段 | 删"持证上岗/考证", 平台政策/合规/新专业课程坑, 博士 3-5% |
| 文化产业管理 (5) | employment 空, deep_study 失真 | 补 employment, pitfalls "万金油/与传播 MBA 同岗/情怀难变现" |
| 数字经济 (5→6) | lede 截断, 缺宏观/微观/计量 | 补全 lede, 补宏观/微观/计量基础, employment 补全 |
| 金融科技 (5→6) | top_schools 错, alumni 假数据 | 补中国人民大学按金融+CS 实力重排, alumni 标"示例引语" |
| 信息安全 (5→6) | salary 内部矛盾, deep_study 不清 | 统一 salary 锚 2024 招聘, deep_study 明确深造分布, pitfalls 信息安全专属 |
| 物联网工程 (5) | 公共必修串台文科, who_fits 错 | 公共必修改 工科公共课, who_fits 改 IoT 专属 (硬件/调试/协议) |
| 动物科学 (5) | who_fits 串台, pitfalls 通用 | 重写 who_fits/lede 农科专属, pitfalls 写 动物科学≠动物医学/养殖场/配方师门槛/女生偏见 |
| 生物工程 (5) | who_fits 机械串台, top_schools 985 错 | who_fits 改生物工程, 江南大学 985 → 211, curriculum 重组 (微生物/分子生物/生物反应/酶/细胞工程) |
| 数字媒体技术 (5) | who_fits 错, curriculum 串 | 修 who_fits, curriculum 加 计算机图形/数字图像/多媒体/虚拟现实/数字音视频 |
| 机械电子工程 (5) | who_fits 错, top_schools 缺 | who_fits 改机电, 补清华/浙大/天大, pitfalls 机电专属 (口径 vs 自动化/电子) |
| 过程装备与控制工程 (5) | 特色选修同核心, 串台 | 5 校特色按校, 删 who_fits 套话, 补 employment/school |

---

## P2: 6/10 微调 (10 篇)

| Slug | 微调项 |
|------|--------|
| 广告学 (6) | deep_study 博士 15% → 3%, top_schools 替换上交/北大 → 浙大/北师大/深大 |
| 俄语 (6) | 重写 lede/pitfalls 含俄语硬核洞察 (六大变格/驻外/对俄贸易), 补 俄罗斯文学/俄语写作/俄汉互译 |
| 园艺 (6) | pitfalls/who_fits 园艺专属, top_schools 补北林, salary 统一万/年 |
| 测控技术与仪器 (6) | lede 测控独一无二洞察, 5 条 pitfalls 测控专属, 补 5 校特色 |
| 体育经济与管理 (6) | lede 100 字内 + 反直觉洞察, pitfalls 体育经管专属, 补华东师大 |
| 体育法 (6) | pitfalls/who_fits 体育法专属 (无独立专业代码), top_schools 区分星级, deep_study 补非研究路径 |
| 材料成型及控制工程 (6) | who_fits 工程语境, curriculum 重构 (公共/通用/特色按方向) |
| 数字经济 (6) | 补 lede/employment, 微观/宏观/计量基础, pitfalls 数字经济专属 |
| 网络与信息法学 (6) | curriculum 补齐专业课, deep_study 博士 5%, 选科政治首选 |
| 大数据管理与应用 (5→6) | (同 P1) |

---

## P3: ≥ 7/10 验收/微调 (5+ 篇)

| Slug | 状态 | 微调项 |
|------|------|--------|
| 制药工程 (7) | 合格 | 课程补工程侧 (制药设备/GMP/药厂洁净), 修 employment 错字, 补生物制药/CDMO |
| 应用语言学 (7) | 合格 | who_fits/pitfalls 改应用语言学 (万金油/AI 替代/学科身份模糊), summary 与 what_you_learn 差异化 |
| 高分子材料与工程 (8) | 优秀 | 压缩 summary 100 字内, curriculum 合并重复, 补截断的 pitfalls, 回填 alumni school |
| 其他 6/7 分 (待确认) | 待审 | 见 audit 报告 |

---

## 执行流程 (每个 major)

1. **读现状** (`json.load` 9 个关键字段)
2. **m3 audit 复核**: 列出该 major 的 issues (field 维度的 score)
3. **hand-code 8 字段** (按 fix_suggestion 优先级):
   - `lede` (主语+独特洞察, ≤100 字)
   - `summary` (≤150 字, 钩子)
   - `what_you_learn` (3-4 段, 与 summary 差异化)
   - `who_fits_yes` / `who_fits_no` (按 style + major 特性)
   - `top_schools` (按真实优势, 6-10 校, 每校 tag 写特色方向)
   - `salary` (4 段 p25/p50/p75/yoy 真实数据)
   - `employment_direction` (6-8 大方向 + 头部公司)
   - `alumni_quotes` (3 条, 含具体课程/项目/公司)
   - `curriculum` (3 块: 公共/通用核心/5 校特色)
   - `deep_study` (5-7 路径 + 百分比)
   - `pitfalls` (3-5 条, 专业独有)
4. **3 防线复核** (`detect_contamination`, 0 strong)
5. **渲染** (`render_batch.py`)
6. **m3 audit 抽样** (验证 ≥ 8)
7. **git commit** (单 major 一个 commit, 便于回滚)

---

## 关键风险 & 兜底

| 风险 | 兜底 |
|------|------|
| Hand-code 估时偏差 | 简单 humanities: 15-20 min/篇, 复杂 medical/law: 30-45 min/篇 |
| m3 audit 主观性 | 7 维度评分, 主要看 lede/salary/curriculum 三个, 其余 4 个小修即可 |
| 数据真实性 vs 模板 | 优先"专业独特" (e.g. 民族学田野调查), 不要"通用洞察" |
| Audit 反复不过 | 退到 P0 重做 curriculum + 5 校特色, 重新 audit |
| 模板串台 | 4 防线扩展: 加 "医学模板" "工科模板" "法学模板" detector |

---

## 验收标准

- m3 content_audit 单篇 ≥ 7/10
- 平均 ≥ 7.5/10 (目标 8, 实际可能 7-7.5, 因为 m3 评分严格)
- 3 防线 100% clean
- Render 47/47
- 每个 commit 单 major, 便于回滚

---

## 启动指令

```bash
cd /Users/zhewenliu/Claude/gaokao-team-b
git checkout day3-team-b
git pull origin day3-team-b
# 从 P0 第一个 (计算语言学) 开始
```

参考文件:
- `scripts/batches/day3_team_b_audit_final.log` (最近一次 audit)
- `test_results/content_audit_1781653657.json` (47 篇全 audit, 含 fix_suggestion)
- `docs/PROGRESS_day3_team_b.md` (上次 session 总结)
