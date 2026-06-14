# Batch 2 Plan — 1 主题扩写 + 4 主题补漏 (2026-06-14 用户拍板)

> **状态**: ⏸️ 待下次 session 启动
> **作者**: Claude (用户决策)
> **基础**: 继承 Batch 1 (law+gongan 12 篇, commit 6123b78~abe6e19) 4 大基础

---

## 0. 为什么这批 (决策已锁)

Batch 1 验证了"传统路线 + pipeline 工具栈"在 12 篇 law/gongan 100% 跑通 (10/10 对齐基准)。
Batch 2 复用同套工具 + 主题特定的 sub-style fillers, 跑新主题扩写 + 补漏, 验证:
- 框架在新主题可移植 (避免单主题硬编码)
- 补漏流程可批量 (4 个主题各 1 篇)

**不动的**: 教育/医学/工商 (本次不碰)

---

## 1. 总目标 (按"专业目录覆盖度"选)

按 **精品数 / 教育部 2026.4.28 目录专业数** 决策, 优先扩写低覆盖主题:

| 类型 | 主题 | 篇数 | 当前覆盖 | 目标覆盖 | 风险 |
|---|---|---|---|---|---|
| **扩写 (1)** | **education** 教育学 | **8 篇** | 3/23 = 13% | 11/23 = 48% | 低 (3 篇精品基准强) |
| **扩写 (2)** | **文学** 文学 | **5-6 篇** | 3/33 = 9% | 8-9/33 = 27% | 低 (3 篇精品基准强) |
| ~~补漏~~ | ~~medicine/finance/humanities/business~~ | **不需要** (实际 0 缺) | | | |

**合计 13-14 篇** (education 8 + 文学 5-6)

**主题选择理由 (按"专业目录覆盖度"倒序)**:
- **教育学 13% (23 目录)** — 选扩写: 师范/学前/特教/教育技术/教育管理/心理学/汉语国际教育 7 子方向可扩
- **文学 9% (33 目录)** — 选扩写: 3 大类 (中国语言文学/外国语言文学/新闻传播学) + 4 套 sub-style, 18 子专业可扩
- **medicine/finance/humanities 不补**: 用户问"已经做过了" 后查 manifest 确认 3 主题 100% 收录 (medicine 8/8, finance 6/6, humanities 5/5), 0 缺
- **business 不补**: 0 精品基准, theme CSS 未验证, 风险高, 留 Batch 3
- **交叉学科 0% 暂不补**: 10 个新专业, theme CSS 完全未验证, 风险最高

**完整覆盖度排行** (按目录数升序):
交叉学科 0%(10) → 文学 9%(33) → 理学 9%(43) → 工学 11%(188) → 艺术学 12%(49) → 教育学 13%(23) → 管理学 13%(53) → 农学 17%(29) → 医学 17%(47) → 经济学 19%(21) → 法学 25%(28) → 历史学 25%(8) → 哲学 25%(4)

---

## 2. 主题特定 sub-style fillers (新写)

复用 Batch 1 框架 (`_law_subkey()` / `_gongan_subkey()` 模式), 新增:
- `_education_subkey(title)` → 8 套
- `_literature_subkey(title)` → 3 套 + 1 default

### education 8 套子风格

```
education_教育学 (师范)        → 师范方向/学科教学论/课程论
education_学前教育            → 学前教育/幼儿园/幼师
education_特殊教育            → 特殊教育/融合教育/手语盲文
education_教育技术学          → 教学设计/教育数字化/AI+教育
education_教育管理/领导       → 教育管理/校长/教育局
education_心理学              → 心理咨询/临床心理/认知科学
education_汉语国际教育        → 对外汉语/海外华文教育/孔子学院
education_default             → 通用教育学
```

### literature 4 套子风格 (扩写 5-6 篇)

按"中国语言文学 / 外国语言文学 / 新闻传播学" 3 大类 + 1 default:
```
literature_中国语言文学      → 汉语言/汉语言文学/汉语国际/古典文献/应用语言
literature_外国语言文学      → 英语/日语/俄语/翻译/商务英语 等
literature_新闻传播学        → 新闻学/广告学/传播学/网络与新媒体
literature_default           → 通用文学
```

**扩写 5-6 篇候选** (从 33 目录里选, sub-style 套数 ≥ 4):
1. 汉语言 (literature_中国语言文学) — 中文专业
2. 商务英语 (literature_外国语言文学) — 应用外语, 就业导向
3. 应用语言学 (literature_中国语言文学) — 跨学科
4. 传播学 (literature_新闻传播学) — 新传基础
5. 网络与新媒体 (literature_新闻传播学) — 数字媒体
6. 古典文献学 (literature_中国语言文学) — 冷门细分

最终 5-6 篇由重开会话时按 manifest 实际可用 slug 选。

---

## 3. 工具栈 (现成, 不写新代码)

| 工具 | 作用 | Batch 1 状态 |
|---|---|---|
| `scripts/batches/normalize.py` | 单篇/批量归一 (7 字段 + 4 sub-style dispatch) | ✅ 实战验证 |
| `scripts/batches/render_batch.py` | 调 generate_dashboard 渲染 | ✅ 实战验证 |
| `scripts/batches/fix_data_count.py` | post-processor 144 处 data-count | ✅ 实战验证 |
| `scripts/batches/fix_fade_up.py` | post-processor 378 处 fade-up.visible | ✅ 实战验证 |
| `scripts/batches/fix_html_paths.py` | post-processor 72 处 /js/ → ../../js/ | ✅ 实战验证 |
| `scripts/batches/screenshot_batch.py` | Playwright full-page 1440x900 | ✅ 实战验证 |
| `scripts/batches/compare_json.py` | vs 基准 field-by-field 自动评级 | ✅ 实战验证 |
| `scripts/batches/pipeline.sh` | 一键跑 5 步流水线 | ✅ 实战验证 |
| **新加** `scripts/batches/compare_themes.py` | 跨主题 batch 汇总 (e.g. 8 篇 education 全 PASS?) | 复用 compare_json 加 --themes 参数 |

**Provider 选型** (沿用 Batch 1 D 组):
- 合成: **deepseek** (主) — 性价比最高, ¥0.02/M 缓存命中
- 审计: **mimo** (3s/篇, ¥0.003/次) — 内容相关性打标
- 兜底: **m3** (慢, 刑法类 sensitive 过滤, 仅 retry 用)

**质量控制**:
- 死规则 normalize (80% schema 错)
- mimo 审计 (10% 漏网)
- 人工 5min 修 (5% 用户视角的 schema 期望不符)

---

## 4. 工作流 (A→B→C→D 4 阶段)

### Phase A: 主题定版 (半天)

1. **education 基准选择**:
   - 看 `manifest.json` 现有 education 7 篇
   - 挑 1-2 篇**视觉风格最稳**的作基准 (e.g. `education` 或 `psychology`)
   - 打开基准 HTML 截图保存, 同主题后续照着改
2. **medicine/finance/humanities 补漏选题**:
   - medicine: 4 选 1 — 看 manifest 哪些 slug 缺, 选**渲染风险低**的 (中医/药学比口腔医学简单)
   - finance: 4 选 1 — 经济学(更通用) / 保险学(细分) / 税收学(政策)
   - humanities: 4 选 1 — 汉语言文学(最通用) / 哲学(冷门) / 考古学(冷门)
3. **写 batch2 CSV**: `scripts/batches/education_v1.csv` + 3 个补漏 CSV
   - 列 schema: `slug,title,style`
   - 主题行参考 `law_gongan_v1.csv`

### Phase B: 并行批量 (半天/批, 跑 11-13 篇)

```bash
# 1) 单跑 education 8-10 篇 (可以分批, 每批 4-5 篇, 避免 token 超限)
source .env
python3 -m scripts.batch_synth --file scripts/batches/education_v1.csv > scripts/batches/education_v1.log 2>&1
# 2) 3 篇补漏
python3 -m scripts.batch_synth --slug <medicine-missing> &
python3 -m scripts.batch_synth --slug <finance-missing> &
python3 -m scripts.batch_synth --slug <humanities-missing> &
wait
```

**预计 token 成本**:
- education 8-10 篇 × ¥1.5/篇 = ¥12-15
- 3 补漏 × ¥1.5 = ¥4.5
- mimo 审计 11-13 篇 × ¥0.003 = ¥0.04
- **合计: ~¥17**

### Phase C: 人工审 (2-3h/批)

1. 跑 `pipeline.sh` (normalize + render + fix_data_count + fix_html_paths + fix_fade_up)
2. Playwright 截 12 张 PNG (2 基准 + 8 新增 + 2 补漏)
3. vision 4 张代表验证 (基准对齐度 ≥9/10)
4. user 浏览器 `file://` 逐个审, 失败清单入 `docs/REVIEW/education_v1.md`

### Phase D: 修一批 (1-2h)

按 Batch 1 经验, 重点修:
- sub-style fillers 关键词 (e.g. education 8 套各自关键词)
- LLM 瞎给的 pct/quote 强制覆盖
- 新主题的渲染 bug (education theme CSS 可能有未覆盖 case)

---

## 5. 失败模式预案 (从 Batch 1 提炼)

| 失败 | Batch 1 踩过的 | 修法 (Batch 2 直接用) |
|---|---|---|
| LLM 瞎给 pct 全相同 | employment 全 16% | normalize "全相同 → fillers 覆盖" 已在 |
| curriculum key 拼写错 | "公共必修（所有院校都开）" vs "公共必修 (所有院校都开)" | key 归一 + fuzzy match 已在 |
| overview_v2 5 keys vs 4 keys | 5 keys → 4 keys 转换已在 | ✅ |
| data-count 0 默认值 | base.py IntersectionObserver 行为 | fix_data_count.py post-processor ✅ |
| fade-up opacity:0 首屏不可见 | 同上 | fix_fade_up.py post-processor ✅ |
| gongan hero 写死 | `<h1>公 安 学 类</h1>` 写死 | 已有 hero.py 改 {title} |
| file:// 绝对路径 | `/js/...` 找不到 | fix_html_paths.py post-processor ✅ |
| xuanke 单科 vs 选科组合 | 用户原话: 选科组合覆盖率 | XUANKE_FILLERS 已有 (按 style 4 套) |
| slug LLM 瞎给 pinyin | `guoji-fa` vs `international-law` | normalize 强制 `slug=filename` ✅ |
| alumni 通用 placeholder | "对学科基础课程有兴趣" 8 篇同源 | 8 套 law + 4 套 gongan sub-style fillers ✅ |
| 同主题 fillers 合并偷懒 | `law_商法/经济法` 合并 → 6 篇同源 | Batch 2 严禁合并, 一律细分 |
| subkey 关键词顺序错 | "刑事" 先于 "诉讼" 匹配 | Batch 2 dispatch 顺序: 专属→通用 |

---

## 6. 关键决策点 (重开会话时拍板) ✅ 2026-06-14 全部已拍

1. **education 扩几篇?** → **8 篇** ✅
2. **education sub-style 套数?** → **8 套** ✅
3. **education 视觉基准?** → **education (教育学)** ✅
4. **第二扩写主题 (按覆盖度)?** → **文学 (覆盖度 9% → 17%)** ✅
5. **第三主题/补漏?** → **不加, 就 education + 文学 2 个** ✅
6. **批量合成 Provider?** → **deepseek (D 组)** ✅
7. **token 成本预算?** → **~¥17** (跟 Batch 1 同)

### 历史 (2026-06-14 用户重拍)
- 原 Q4-Q6 候选 (medicine/finance/humanities 补漏) → 用户指出"已经做过了"
- 查 manifest 确认 3 主题 100% 覆盖 (medicine 8/8, finance 6/6, humanities 5/5)
- 重设计: 按"专业目录覆盖度" (精品数 / 目录数) 选低覆盖主题
- 文学 9% 最低之一 + sub-style 多 (3 大类) → 第二扩写主题
- business / 交叉学科 暂不补 (theme CSS 风险高)

---

## 7. 阶段产物 (commits 节奏)

每批产出 1-2 个 commit (1 主题 1-2 commit, 出问题回滚粒度小):

- `feat(education): education 主题 8 篇精品报告` + 8 个 .json + 8 个 .html + manifest
- `fix(education): education batch 1 visual review` (失败项修改)
- `feat(literature): 文学 主题 5-6 篇精品报告` + 5-6 个 .json + 5-6 个 .html + manifest
- `fix(literature): 文学 batch 1 visual review`

**不批量大 commit, 1 主题 1-2 commit, 出问题回滚粒度小**

**不批量大 commit, 1 主题 1-2 commit, 出问题回滚粒度小**

---

## 8. 时间估算 (保守)

| 阶段 | Batch 2 时间 |
|---|---|
| A: 主题定版 | 1-2h |
| B: 并行批量合成 (11-13 篇) | 1-2h |
| C: 人工审 (含 vision 4 张验证) | 3-4h |
| D: 修一批 | 1-2h |
| **小计** | **6-10h** |

---

## 9. 跟 Batch 1 区别

| 维度 | Batch 1 (law/gongan) | Batch 2 (education + 文学) |
|---|---|---|
| 主题数 | 2 | 2 (education + 文学) |
| sub-style fillers 套数 | 8 law + 4 gongan | **8 education + 4 literature** |
| 选主题逻辑 | 主题精品数 < 8 | **"专业目录覆盖度"低优先** (文学 9% < 教育 13%) |
| 新工具 | 8 个 (scripts/batches/*) | 0 新工具 (复用 Batch 1) |
| 渲染风险 | 低 (law/gongan 已稳定) | 低 (education 7/文学 3 精品基准都强) |
| **Token 成本** | ~¥17 | **~¥17** (同) |
| **预计用时** | 6-8h | **6-10h** (同) |
| **总篇数** | 12 | **13-14** (education 8 + 文学 5-6) |

---

## 10. 启动 checklist (重开会话第一件事)

1. `cat docs/PLAN_batch2.md` (本文件) — 重读 plan
2. `cd /Users/zhewenliu/Claude/gaokao-hubei-mvp` + `source .env`
3. `git log --oneline -10` — 确认 Batch 1 commits + plan 修正 commit 在
4. **5 个决策点已拍 (在 §6)** — 直接复用: education 8/8套/education 基准 + 文学 5-6 + 不加第 3 主题
5. **跑 Phase A 主题定版** — 看 manifest, 选基准, 写 2 个 CSV
6. **跑 Phase B 合成** — pipeline.sh 跑 2 批
7. **跑 Phase C 审** — vision 4 张 + user file:// 审
8. **跑 Phase D 修** — sub-style fillers 关键词
9. **commit + push** — 1 主题 1-2 commit

---

**详细操作见各 batch_synth.py / v4_styles/render.py 注释. 本文档是路线图, 不是实施手册.**
