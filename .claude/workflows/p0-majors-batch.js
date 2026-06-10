export const meta = {
  name: 'p0-majors-batch',
  description: '批量为 15 个 P0 热门专业生成精品分析 HTML — 并行搜索 + 编 JSON + 渲染',
  phases: [
    { title: '数据采集', detail: '15 个 agent 同时搜索并写入 JSON + 渲染 HTML' },
    { title: '汇总', detail: '汇总结果, 更新 manifest' },
  ],
}

const BASE = '/Users/zhewenliu/Claude/gaokao-hubei-mvp/skills/canghe-major-explorer'
const renderCmd = (slug, style) =>
  `cd /Users/zhewenliu/Claude/gaokao-hubei-mvp && python3 skills/canghe-major-explorer/scripts/generate_dashboard.py --data skills/canghe-major-explorer/data/curated/${slug}.json --style ${style} --output skills/canghe-major-explorer/data/curated/${slug}.html`

const MAJORS = [
  {
    slug: 'artificial-intelligence', title: '人工智能',
    category: '工学 · 电子信息类', style: 'cs', degree: '工学学士',
    tags: ['高薪', '前沿', '数学要求极高', '博士红利', '算力瓶颈', '算法岗饱和'],
    queries: [
      '人工智能 主要课程 培养方案 大学 学分 2025',
      '人工智能 就业 薪资 算法岗 大厂 2025',
      '人工智能 学科评估 大学排名 教育部 第四轮',
      '人工智能 选科要求 新高考 科目 物理化学',
      '人工智能 学长学姐 知乎 学习体验 就业',
    ],
  },
  {
    slug: 'software-engineering', title: '软件工程',
    category: '工学 · 计算机类', style: 'cs', degree: '工学学士',
    tags: ['高薪', '代码量大', '工程导向', '实习重要'],
    queries: [
      '软件工程 主要课程 培养方案 大学',
      '软件工程 就业 薪资 大厂 招聘 2025',
      '软件工程 学科评估 大学排名 教育部',
      '软件工程 选科要求 新高考 科目',
      '软件工程 学长学姐 知乎 体验',
    ],
  },
  {
    slug: 'data-science-big-data', title: '数据科学与大数据技术',
    category: '工学 · 计算机类', style: 'cs', degree: '工学学士',
    tags: ['高薪', '交叉学科', '数学统计', '数据岗', '热门'],
    queries: [
      '数据科学与大数据技术 主要课程 培养方案',
      '数据科学 就业 薪资 大数据 招聘 2025',
      '数据科学 学科评估 大学排名',
      '数据科学与大数据技术 选科要求 新高考',
      '数据科学 学长学姐 知乎 体验',
    ],
  },
  {
    slug: 'electronic-information-engineering', title: '电子信息工程',
    category: '工学 · 电子信息类', style: 'cs', degree: '工学学士',
    tags: ['硬件软件', '信号处理', '嵌入式', '就业面宽'],
    queries: [
      '电子信息工程 主要课程 培养方案 大学',
      '电子信息工程 就业 薪资 嵌入式 芯片 2025',
      '电子信息工程 学科评估 大学排名 教育部',
      '电子信息工程 选科要求 新高考 物理',
      '电子信息工程 学长学姐 知乎 体验',
    ],
  },
  {
    slug: 'electrical-engineering-automation', title: '电气工程及其自动化',
    category: '工学 · 电气类', style: 'cs', degree: '工学学士',
    tags: ['稳定', '国家电网', '强电弱电', '男女均衡'],
    queries: [
      '电气工程及其自动化 主要课程 培养方案',
      '电气工程 就业 薪资 国家电网 2025',
      '电气工程 学科评估 大学排名 教育部',
      '电气工程及其自动化 选科要求 新高考 物理',
      '电气工程 学长学姐 知乎 体验 电网',
    ],
  },
  {
    slug: 'automation', title: '自动化',
    category: '工学 · 自动化类', style: 'cs', degree: '工学学士',
    tags: ['万金油', '控制理论', '嵌入式', 'AI结合', '实践强'],
    queries: [
      '自动化 主要课程 培养方案 大学',
      '自动化 就业 薪资 控制 工业 2025',
      '自动化 学科评估 大学排名 教育部',
      '自动化 选科要求 新高考 科目',
      '自动化 学长学姐 知乎 学习体验',
    ],
  },
  {
    slug: 'accounting', title: '会计学',
    category: '管理学 · 工商管理类', style: 'finance', degree: '管理学学士',
    tags: ['考证', '稳定', '越老越值钱', '四大', '考公热门'],
    queries: [
      '会计学 主要课程 ACCA CPA 培养方案',
      '会计学 就业 薪资 四大 企业财务 2025',
      '会计学 学科评估 大学排名 教育部',
      '会计学 选科要求 新高考 科目',
      '会计学 学长学姐 知乎 考证 就业体验',
    ],
  },
  {
    slug: 'business-administration', title: '工商管理',
    category: '管理学 · 工商管理类', style: 'finance', degree: '管理学学士',
    tags: ['万金油', '名校红利', '实践导向', 'MBA'],
    queries: [
      '工商管理 主要课程 培养方案 大学',
      '工商管理 就业 薪资 咨询 管培 2025',
      '工商管理 学科评估 大学排名 教育部',
      '工商管理 选科要求 新高考 科目',
      '工商管理 学长学姐 知乎 就业迷茫',
    ],
  },
  {
    slug: 'stomatology', title: '口腔医学',
    category: '医学 · 口腔医学类', style: 'medicine', degree: '医学学士',
    tags: ['高薪', '动手能力', '5+3+X', '诊所创业', '医患纠纷少'],
    queries: [
      '口腔医学 主要课程 培养方案 5+3+X',
      '口腔医学 就业 薪资 诊所 医院 2025',
      '口腔医学 学科评估 大学排名 教育部',
      '口腔医学 选科要求 新高考 物理化学',
      '口腔医学 学长学姐 知乎 学习体验 劝退',
    ],
  },
  {
    slug: 'architecture', title: '建筑学',
    category: '工学 · 建筑类', style: 'cs', degree: '工学学士',
    tags: ['五年制', '设计感', '甲方乙方', '手绘电脑', '行业波动'],
    queries: [
      '建筑学 主要课程 五年制 培养方案',
      '建筑学 就业 薪资 设计院 建筑 2025',
      '建筑学 学科评估 大学排名 教育部',
      '建筑学 选科要求 新高考 科目',
      '建筑学 学长学姐 知乎 劝退 就业前景',
    ],
  },
  {
    slug: 'civil-engineering', title: '土木工程',
    category: '工学 · 土木类', style: 'cs', degree: '工学学士',
    tags: ['基建', '工地', '考证', '稳定', '就业率高'],
    queries: [
      '土木工程 主要课程 培养方案 大学',
      '土木工程 就业 薪资 中建 房地产 2025',
      '土木工程 学科评估 大学排名 教育部',
      '土木工程 选科要求 新高考 科目',
      '土木工程 学长学姐 知乎 工地体验',
    ],
  },
  {
    slug: 'journalism-communication', title: '新闻传播学',
    category: '文学 · 新闻传播学类', style: 'education', degree: '文学学士',
    tags: ['新媒体', '写作表达', '传媒', '短视频', '内卷'],
    queries: [
      '新闻传播学 主要课程 培养方案',
      '新闻传播学 就业 薪资 新媒体 传媒 2025',
      '新闻传播学 学科评估 大学排名 教育部',
      '新闻传播学 选科要求 新高考 科目',
      '新闻传播学 学长学姐 知乎 就业劝退',
    ],
  },
  {
    slug: 'english', title: '英语',
    category: '文学 · 外国语言文学类', style: 'education', degree: '文学学士',
    tags: ['语言', '教学', '翻译', '跨文化交流', '考公考编'],
    queries: [
      '英语专业 主要课程 培养方案 大学',
      '英语 就业 薪资 翻译 教育 外贸 2025',
      '英语 学科评估 大学排名 教育部',
      '英语专业 选科要求 新高考 科目',
      '英语专业 学长学姐 知乎 就业前景',
    ],
  },
  {
    slug: 'psychology', title: '心理学',
    category: '理学 · 心理学类', style: 'education', degree: '理学学士',
    tags: ['交叉学科', '咨询师', '读研比例高', '认知神经科学'],
    queries: [
      '心理学 主要课程 培养方案 大学',
      '心理学 就业 薪资 心理咨询 2025',
      '心理学 学科评估 大学排名 教育部',
      '心理学 选科要求 新高考 科目',
      '心理学 学长学姐 知乎 学习就业体验',
    ],
  },
  {
    slug: 'communication-engineering', title: '通信工程',
    category: '工学 · 电子信息类', style: 'cs', degree: '工学学士',
    tags: ['5G6G', '信号处理', '华为', '物联网', '数学要求高'],
    queries: [
      '通信工程 主要课程 培养方案 大学',
      '通信工程 就业 薪资 华为 运营商 2025',
      '通信工程 学科评估 大学排名 教育部',
      '通信工程 选科要求 新高考 科目',
      '通信工程 学长学姐 知乎 学习就业',
    ],
  },
]

function buildPrompt(m) {
  return `你是高考专业数据智能采集专家。请为「${m.title}」制作一套完整的精品分析数据 JSON 并渲染 HTML。

## 专业信息
- slug: ${m.slug}
- title: ${m.title}
- category: ${m.category}
- style: ${m.style}
- degree: ${m.degree}
- duration_years: 4
- tags: [${m.tags.map(t => `"${t}"`).join(', ')}]
- difficulty: 根据内容合理给 (★★★★☆ 或 ★★★★★)

## 搜索任务 (5 路, 全部执行后综合分析)
${m.queries.map((q, i) => `${i+1}. web_search(query: "${q}")`).join('\n')}

## JSON 输出路径
${BASE}/data/curated/${m.slug}.json
## HTML 输出路径
${BASE}/data/curated/${m.slug}.html

## 必须包含的全部字段 (参考 cybersecurity.json 格式)

### 顶层必填
slug, title, category, style, degree, duration_years (4), tags (4-6个), difficulty, updated_at ("2026-06"), data_source (描述来源), summary (1句话Hero), what_you_learn (2-3段), who_fits (1-2段), pitfalls (⚠️❌列点, 每个❌开头, 至少3条)

### curriculum — 3 组
- "公共必修 (所有院校都开)": 5-8 门基础课 {name, credit}
- "通用专业核心 (≈ 80% 院校覆盖)": 5-8 门核心课 {name, credit}
- "5 校特色选修 (按方向分流)": 5 门, name = "学校名 · 课程名", credit
- 可选 curriculumn_note (字符串)

### top_schools — 8-10 所
{name, rank: "A+|A|A-|B+|B", tag: "城市 · 特色"}
城市规则: 校名如不含城市名则 tag 前置「城市 · 」

### top_companies — 6-8 家
{name, tier: "S|A|B", headcount: "★★★~★★★★★", salary: "一句话", sparkline: [5个1-5整数]}

### salary — 3-4 阶段
如 "应届 (0-2年)"/"中级 (3-5年)"/"资深 (6-10年)"/"高管 (10+年)"
每阶段 {p25: 数字, p50: 数字, p75: 数字, yoy: 数字}

### employment_direction — 5-7 项
{name: "方向", pct: 数字} 合计 ≈ 100%

### deep_study — 3-5 条
"路径名": 数字百分比, 合计 ≤100%

### alumni_quotes — 3-4 条
{year: "YYYY 届", current: "职位", source: "知乎/校友访谈", quote: "用「」的实际内容"}
必须有夸有劝退有中立, 不能全夸

### xuanke_req_list
[{name: "物理+化学", pct: 数字}] 合计 ≈ 100%

## 铁律 (必须遵守)
1. **引号全用「」** — 禁止 ASCII "" 和 ''
2. **学校 tag 含城市** — 校名里没城市的就前置「城市 · 」
3. **alumni_quotes.year 格式** — "YYYY 届" (含届字)
4. **top_schools 去重** — 按 name 唯一
5. **百分比合理** — employment≈100%, deep_study≤100%, xuanke≈100%
6. **tags 4-6 个** — 第一个是 primary

## 执行步骤 (严格按顺序)
1. 执行 5 次 web_search, 收集足够多真实数据
2. 综合搜索结果, 按上述 schema 填所有字段
3. 用 Write 工具写入 JSON 到 ${BASE}/data/curated/${m.slug}.json
4. 用 Bash 运行渲染命令: ${renderCmd(m.slug, m.style)}
5. 用 Bash 验证 HTML 文件存在: ls -la ${BASE}/data/curated/${m.slug}.html
6. 返回 { slug: "${m.slug}", success: true/false, error: "如果失败说明原因" }

开始!`
}

phase('数据采集')
const tasks = MAJORS.map(m => () => agent(buildPrompt(m), {
  label: m.slug,
  phase: '数据采集',
  schema: {
    type: 'object',
    properties: {
      slug: { type: 'string' },
      success: { type: 'boolean' },
      error: { type: 'string' },
    },
    required: ['slug', 'success'],
  },
}))

const results = (await parallel(tasks)).filter(Boolean)

phase('汇总')
const ok = results.filter(r => r.success)
const fail = results.filter(r => !r.success)
log(`✅ ${ok.length}/${results.length} 个专业成功完成`)
if (fail.length) {
  log(`❌ 失败 ${fail.length} 个:`)
  fail.forEach(f => log(`  - ${f.slug}: ${f.error || '未知错误'}`))
}
log(`成功列表: ${ok.map(r => r.slug).join(', ')}`)

return { success: ok.map(r => r.slug), failed: fail.map(r => r.slug) }
