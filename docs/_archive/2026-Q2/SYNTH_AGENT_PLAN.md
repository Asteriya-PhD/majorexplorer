# Synth Agent Plan — 60s 高质量档 ⚠️ **已弃用 (2026-06-13)**

> **状态**: ❌ **弃用** — Phase 1 实测 5 篇后用户判定"质量不达标 + 速度太慢", 改走传统路线
> **作者**: Claude (用户决策确认 → 弃用)
> **决策背景**: 6+ 轮 normalizer 修字段怪癖到顶, LLM 输出 schema 自由发挥是反 normalizer 方向; 模板锁版会批量同质化破坏项目初衷; 改用 **Agent 流水线**让每个 agent 负责一类问题。
> **弃用原因**: 详见 `abandon-agent-pipeline-traditional-route-2026-06-13.md` memory + `docs/TRADITIONAL_BATCH_PLAN.md` 新路线

---

## 0. 设计原则 (决策已锁)

| 原则 | 理由 |
|---|---|
| **不上 normalizer** | LLM 输出多样性是差异化的来源, normalizer 是反方向 |
| **不上模板锁版** | 70 篇模板批量同质化, 项目价值归零 |
| **Agent 分工** | 单一 agent 解决单一问题, 串行流水线 |
| **C 档 60s 高质** | 用户决策: 宁可慢, 也不批量同质化; 后期冷门/长尾再提速 |
| **核心字段 LLM 原创** | 差异化源: summary + hero_quote + curriculum + top_schools + employment + alumni |
| **次要字段模板填补** | 稳定性源: xuanke + salary + deep_study + overview_v2 从同 style 精品拷贝 |

---

## 1. Agent 流水线架构

```
[输入: 专业名 (e.g. 金融数学)]
        ↓
┌─────────────────────────────────────┐
│  Agent 1: 快速合成 (10-15s)            │  m3 thinking=OFF, 5 核心字段
│  → raw JSON (5 fields)                │  不给 schema 自由度
└────────┬────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Agent 2: 漂移审计 (3-5s)             │  deepseek-v4-flash
│  → "OK" 或 "{segment}: 漂到 X"        │  max_tokens=500, 4 字段
└────────┬───────────┬─────────────────┘
         ↓ OK        ↓ drift
         │     ┌─────────────────────────────────────┐
         │     │  Agent 5: 漂移段重写 (10-15s)        │  m3 单字段重写
         │     │  → 1-2 段 (不是全篇)               │  prompt: "X 段, 不要讲其他专业"
         │     │  → 重审 1 轮                       │
         │     └────────┬──────────────────────────┘
         │              ↓
         ↓              ↓
┌─────────────────────────────────────┐
│  Agent 4: 模板填补 (0.5s, 无 LLM)     │  从 70 篇精品按 style 找
│  → xuanke/salary/overview/             │  curriculum 关键词 + category
│    deep_study 拷贝+改专业名            │  相似度匹配最像的 1 篇
└────────┬────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Agent 6: 渲染 (0.5s)                │  v4_styles/render.py
│  → HTML 75-90K bytes                 │  already works
└────────┬────────────────────────────┘
         ↓
[输出: HTML, 总 25s 成功 / 40-60s 漂移重写]
```

**Agent 数字编号说明**:
- 1: 合成 (核心入口)
- 2: 审计
- 3: **(未启用)** 留给未来如果需要第 2 轮审计
- 4: 模板填补
- 5: 漂移重写
- 6: 渲染

---

## 2. Agent 详细设计

### Agent 1: 快速合成 (m3)

**输入**: 目标专业名 (e.g. "金融数学")
**输出**: 5 字段 dict

**核心 prompt**:
```
你是中国高考专业深度分析师. 为 "金融数学" (style=finance) 合成 5 个字段.
输出必须是纯 JSON, 不要任何其他文本.

{
  "title": "金融数学 (标准专业全称)",
  "summary": "1 段话, 80-200 字, 含出口+方向+适合人群",
  "hero_quote": "扉页金句, 1 句 30-50 字",
  "curriculum": {
    "公共必修 (所有院校都开)": [{"name": "课程名", "credit": "4"}, ...] 5-7 门,
    "通用专业核心 (≈ 80% 院校覆盖)": [...] 8-12 门,
    "5 校特色选修 (按方向分流)": [...] 5-7 门
  },
  "top_schools": [{"name": "校名", "rank": "A+", "tag": "..."}, ...] 8-10 所,
  "employment_direction": [
    {"name": "方向名", "dest": "代表公司", "pct": 30, "desc": "起薪/晋升"},
    ... 4-6 条
  ],
  "alumni_quotes": [
    {"name": "某学长", "school": "校+方向+届", "quote": "30-80 字", "tag": "..."},
    ... 2-3 条
  ]
}

【硬约束】
- summary 不要超过 200 字
- curriculum 每块至少 5 门, name 用 8-20 字
- top_schools 至少 8 所, rank 用 A+/A/A-/B+
- employment_direction 至少 4 条, pct 总和 ≈ 100
- alumni_quotes 不要 P8/P9/VP/CTO/CEO
```

**关键参数**:
- `enable_thinking=False` (省 token, 提速)
- `max_tokens=4000` (5 字段够用)
- `temperature=0.4` (适度创造)

**耗时**: 8-15s

---

### Agent 2: 漂移审计 (deepseek-v4-flash)

**输入**: Agent 1 输出 + 目标 title
**输出**: 简短审计结果

**核心 prompt**:
```
你是审计员. 检查以下 major JSON 是否真在描述 "{title}" 这个专业.
如果不是, 标出哪段漂到其他专业.

JSON 内容:
{summary, curriculum (前 3 门), top_schools (前 3 所), alumni_quotes (前 1 条), employment_direction (前 2 条)}

输出格式 (严格 JSON, 不超 100 词):
{"passed": true/false, "drift_segments": ["summary"] 或 [], "reason": "一句话"}
```

**关键参数**:
- `max_tokens=500` (简短)
- `temperature=0.0` (确定性)
- deepseek-v4-flash (便宜快速)

**耗时**: 3-5s

---

### Agent 4: 模板填补 (纯 Python, 无 LLM)

**输入**: 目标 title + style + Agent 1 输出
**输出**: 完整 major JSON

**核心算法**:
```python
# 1. 找同 style 精品
candidates = [m for m in curated_70 if m.style == target_style]

# 2. 关键词相似度匹配 (curriculum 课程名 vs 目标专业)
def similarity(cand_curriculum, target_name):
    text = " ".join(c["name"] for c in cand_curriculum[:20])
    common = len(set(target_name) & set(text)) / max(len(target_name), 1)
    return common
candidates.sort(key=lambda c: similarity(c.curriculum, target_name), reverse=True)
template = candidates[0]  # 最像的 1 篇

# 3. 拷贝次要字段
data = {
    "title": agent1["title"],
    "summary": agent1["summary"],
    "hero_quote": agent1["hero_quote"],
    "curriculum": agent1["curriculum"],
    "top_schools": agent1["top_schools"],
    "employment_direction": agent1["employment_direction"],
    "alumni_quotes": agent1["alumni_quotes"],
    # 以下从模板拷贝 + 改专业名
    "xuanke_req_list": copy_and_rename(template.xuanke, target_title),
    "salary": copy_and_rename(template.salary, target_title),
    "deep_study": copy_and_rename(template.deep_study, target_title),
    "overview_v2": copy_and_rename(template.overview_v2, target_title),
    "data_source": f"半精编 (LLM 核心 + 同 style 精品模板)",
    "updated_at": today,
}
```

**改专业名** (5-10 处):
- xuanke_req_list note 里的 "X 专业" 替换
- deep_study 路径名里的 "X" 替换
- overview_v2 lede/what_you_learn 里的 "X" 替换 (LLM 原创的 summary 已有, 这里只补 not-llm 部分)

**耗时**: 0.5s

---

### Agent 5: 漂移段重写 (m3)

**触发条件**: Agent 2 报 drift
**输入**: 漂移段内容 + 目标 title
**输出**: 重写后的内容

**核心 prompt** (单字段, 极简):
```
"{title}" 专业的 {segment_name} 段, 重写. 不要讲其他专业.

原文: "{drift_content}"

输出: 30-50 字, 只讲 {title}
```

**关键参数**:
- `max_tokens=500`
- `temperature=0.3`

**耗时**: 10-15s

---

### Agent 6: 渲染 (现有)

**输入**: 完整 major JSON
**输出**: HTML

**走**: `v4_styles/render.py` 已 work, 直接调

**耗时**: 0.5s

---

## 3. 实施阶段 (5 phases)

### Phase 1: 骨架 + Agent 1+2+4 (1.5-2h)

**目标**: 5 篇验证视觉
**交付**:
- `scripts/agent_batch.py` 主入口
- Agent 1 (合成) 实现
- Agent 2 (审计) 实现
- Agent 4 (模板填补) 实现
- 5 篇测试 (5 个 style: finance/medicine/law/humanities/eng)
- 视觉目测

**判断**:
- 视觉 OK → 进 Phase 2
- 视觉崩 (比如模板痕迹明显) → 调整模板挑选策略

### Phase 2: Agent 5 漂移重写 (1h)

**目标**: 通过率 ≥ 90%
**交付**:
- Agent 5 实现
- 接 Agent 2 失败信号
- 30 篇测试

**判断**:
- 通过率 ≥ 90% → 进 Phase 3
- < 90% → 调 Agent 5 prompt 或加第 2 轮重试

### Phase 3: 端到端流水线 (1h)

**目标**: 跑 60 篇, 全自动入库
**交付**:
- batch_synth.py 重构, 调用 agent 流水线
- manifest 自动更新
- 输出报告

**判断**:
- 60 篇入库 + 视觉 OK → 进 Phase 4
- 60 篇有显著问题 → 回 Phase 2 调

### Phase 4: SCF 现场入口接入 (2h)

**目标**: 用户现场搜未收录专业, 25-60s 看到页面
**交付**:
- `scf/synth/main.py` 改用 agent 流水线
- handler 返回 agent 流程结果
- 现场超时 120s (留 buffer)

**判断**:
- 现场 timeout 风险 → 走异步 (POST 返回 run_id, GET 轮询)

### Phase 5: 批量 300 篇 (4-6h, 可后台跑)

**目标**: 收齐 300 篇
**交付**:
- 跑 300 篇, 自动入库
- 输出 Excel 报告
- 失败的标红人工改

**判断**:
- 300 篇完成 → 上线
- 失败率 > 10% → 看质量决定是否暂停

---

## 4. 关键代码路径

### 4.1 Agent 1 prompt 模板 (核心)

文件: `scripts/agent_batch.py`

```python
AGENT1_PROMPT = """你是中国高考专业深度分析师. 为 "{title}" (style={style}) 合成 5 个字段的 JSON.

【硬约束】
1. 字段顺序/类型严格按下面的 schema
2. summary 不超过 200 字
3. curriculum 至少 3 块, 每块至少 5 门课
4. top_schools 至少 8 所, rank 用 A+/A/A-/B+
5. employment_direction 至少 4 条, pct 总和 ≈ 100
6. alumni_quotes 不要 P8/P9/VP/CTO/CEO 高帽

【schema】
{schema}

【输出格式】纯 JSON, 不要 markdown 包装:
{{"title": "...", "summary": "...", "hero_quote": "...", "curriculum": {{...}}, "top_schools": [...], "employment_direction": [...], "alumni_quotes": [...]}}
"""
```

### 4.2 模板选择算法

文件: `scripts/agent_batch.py`

```python
def select_template(target_title: str, target_style: str, manifest: dict) -> dict:
    """从同 style 70 篇精品里挑最像的 1 篇."""
    candidates = [m for m in manifest["majors"] if m["style"] == target_style]
    if not candidates:
        return None
    
    def similarity_score(cand: dict) -> float:
        # 拼 cand 的课程名 + 院校名 + employment 关键词
        cand_text = " ".join([
            c.get("name", "") for c in cand.get("curriculum", {}).values() if isinstance(c, dict) for c in (c if isinstance(c, list) else [])
        ]) + " " + " ".join(s.get("name", "") for s in cand.get("top_schools", []) if isinstance(s, dict))
        cand_text += " " + " ".join(e.get("name", "") for e in cand.get("employment_direction", []) if isinstance(e, dict))
        # 与 target_title 算 jaccard 相似度
        target_words = set(target_title)
        cand_words = set(cand_text)
        if not target_words or not cand_words:
            return 0
        return len(target_words & cand_words) / len(target_words | cand_words)
    
    candidates.sort(key=similarity_score, reverse=True)
    return candidates[0]
```

### 4.3 模板字段拷贝 + 改名

```python
def copy_and_rename(template_field, target_title: str) -> Any:
    """深拷贝模板字段, 把出现的旧专业名替换成 target_title."""
    import copy
    data = copy.deepcopy(template_field)
    if isinstance(data, str):
        # 替换 "X专业" / "X方向" 等
        # 简单实现: 找模板里 "name" 字段对应的旧 title, 然后全局替换
        return data
    # 字典/列表: 递归处理
    # ... 略
```

**更智能**: 从 template 的 `title` 字段拿原 title, 然后全文 replace:
```python
old_title = template["title"]
import re
def replace_text(s):
    if isinstance(s, str):
        return s.replace(old_title, target_title)
    return s
```

---

## 5. 速度-质量-差异化三角

| 维度 | 目标 |
|---|---|
| 总耗时 (C 档) | ≤ 60s |
| 通过率 (审计) | ≥ 95% |
| 视觉差异化 (vs 同 style 精品) | 70% 相同 (基础模板) + 30% 不同 (LLM 原创) |

**速度预算**:
- Agent 1: 8-15s
- Agent 2: 3-5s
- Agent 5 (漂移时): 10-15s
- Agent 4: 0.5s
- Agent 6: 0.5s
- **合计**: 12-21s 成功 / 22-36s 重写 + 模板拷贝

---

## 6. 风险与缓解

| 风险 | 缓解 |
|---|---|
| Agent 1 字段还是怪 | 5 字段不复杂, 5 字段约束下 LLM 难出错 |
| Agent 2 误判 | 阈值 ≥ 8 通过, < 8 进 Agent 5 |
| 模板痕迹明显 | LLM 原创的 5 字段 (summary/alumni) 占视觉 60%+, 模板的 4 字段 (xuanke/salary/...) 视觉占比低 |
| 相似度匹配挑错 | 关键词 + style 锁 + 随机种子防重复 |
| Agent 5 重写也漂 | 加 3 轮上限, 失败回 fallback 模板 |
| SCF 现场超时 | 异步化: POST 返回 run_id, GET 轮询 |

---

## 7. 验收标准

**Phase 1 验收** (5 篇测试):
- 5 篇都跑通, 不崩
- 视觉目测: 跟精品 70 篇"明显同源但有差异"
- 模板挑选合理 (e.g. 临床医学类应该挑到临床医学模板, 不是药学)

**Phase 3 验收** (60 篇):
- 60 篇自动入库
- audit 平均分 ≥ 8
- 抽样 5-10 篇目测通过

**Phase 5 验收** (300 篇):
- 300 篇完成
- 失败率 < 10%
- 总耗时 4-6h

---

## 8. 现状快照 (2026-06-13)

**已完成**:
- ✅ 4 大组件 (TEMPLATE/batch_synth/overview_simple/render)
- ✅ 6+ 轮 normalizer 修字段怪癖 (m3 + deepseek 共享 aliases)
- ✅ 5 篇 LLM 组合对比 (deepseek/mimo/m3 单独 + 审计组合)
- ✅ Memory: 6+ 条关键决策记录

**已完成但弃用**:
- ❌ normalizer 字段别名路线 (到顶, 弃用)
- ❌ 模板锁版方案 (用户拍板: 批量同质化, 弃用)
- ❌ 现场 90s 同步模式 (太慢, 改异步)

**待开始**:
- ⏳ Phase 1: Agent 1+2+4 骨架
- ⏳ Phase 2-5: 见上文

---

## 9. 关键文件位置

| 文件 | 路径 | 作用 |
|---|---|---|
| 主入口 (待写) | `scripts/agent_batch.py` | 5 phase 都从这里调 |
| Agent 1 prompt | `scripts/agent_batch.py:AGENT1_PROMPT` | 5 字段合成 |
| Agent 2 prompt | `scripts/agent_batch.py:AGENT2_PROMPT` | 漂移审计 |
| Agent 4 模板 | `scripts/agent_batch.py:select_template()` | 相似度匹配 |
| Agent 5 prompt | `scripts/agent_batch.py:AGENT5_PROMPT` | 漂移重写 |
| 70 篇精品 | `skills/gaokao-major-explorer/data/curated/*.json` | 模板源 |
| Manifest | `skills/gaokao-major-explorer/data/curated/manifest.json` | style 索引 |
| 渲染器 | `skills/gaokao-major-explorer/scripts/v4_styles/render.py` | Agent 6 |
| Validator | `scf/synth/validator.py` | 字段校验 |
| Audit | `scf/synth/audit.py` | 内容审计 |

---

**等用户重开 session 后启动 Phase 1**. 一切代码改动先备份, 5 字段 prompt 设计是核心, 模板选择算法是质量底线.