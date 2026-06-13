# Traditional Batch Plan — 本地定主题 + 并行批量 + 人工审循环 (2026-06-13 拍板)

> **状态**: ✅ 当前路线 (替代已弃用的 Agent 流水线)
> **作者**: Claude (用户决策)
> **决策**: 不再追求自动化 60s, 走"质量优先"传统路线

---

## 0. 为什么走传统路线 (决策已锁)

| Agent 流水线失败点 | 传统路线优势 |
|---|---|
| m3 thinking=ON 慢 140-300s/篇 | 离线跑, 不卡用户 |
| 模板 3 大 schema 怪癖 (what/pitfalls/deep_study) | 人工看, 怪癖可手动修 |
| medicine style 无 v4 render | 人工选其他同 theme 精品 |
| 速览不统一 (overview_v2 5 schema) | 人工对标精品修 |
| Audit 全过但视觉仍崩 | 人工肉眼看 HTML, 不靠分数 |

---

## 1. 路线总览

```
┌─────────────────────────────────────────────────────────────┐
│  Phase A: 主题定版 (本地, 半天)                              │
│  - 按主题分组 (gongan/business/...) 不是 style              │
│  - 每组 5-10 篇, 共享主题色调 + hero 风格                    │
│  - 人工挑 1-2 篇精品作"基准", 后续同主题照着改              │
└────────┬────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase B: 并行批量 (半天/批, 跑 30-50 篇)                   │
│  - batch_synth.py 走现成合成 + normalizer 6+ 轮              │
│  - 不走 agent_batch.py (已弃用)                              │
│  - 每篇独立 .json + .html, 不批量覆盖                        │
└────────┬────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase C: 人工审核 (1 篇 5-10 分钟, 1 批 2-3h)              │
│  - 浏览器逐个开 file:// 看 (不要起本地服务)                  │
│  - 重点: hero / 课程 / 院校 / 速览 / 整体视觉                │
│  - 失败清单: 模板缺失/速览不统一/课程不专/数据陈旧            │
└────────┬────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase D: 修一批 (1-2h)                                     │
│  - 失败项归类: 模板源不对 → 重选 / 速览结构 → 修 overview_v2 │
│  - 重大问题回 Phase B 重跑该篇                                │
└────────┬────────────────────────────────────────────────────┘
         ↓
       循环 (B → C → D) 直到批质量稳定
```

---

## 2. 工具栈 (现成, 不写新代码)

| 工具 | 作用 | 路径 |
|---|---|---|
| `batch_synth.py` | 单篇/批量合成 (m3 + deepseek + normalizer) | `scripts/batch_synth.py` |
| `v4_styles/render.py` | 渲染 HTML | `skills/.../scripts/v4_styles/render.py` |
| `audit.py` | 漂移审计 (参考, 不作决策) | `scf/synth/audit.py` |
| `validator.py` | 字段校验 | `scf/synth/validator.py` |
| **Playwright** | 视觉验证 (`npx playwright screenshot`) | CLI |
| 浏览器 (Chrome/Safari) | 逐篇 file:// 人工审 | 用户本地 |

**禁止再用**:
- ❌ `scripts/agent_batch.py` (Phase 1 失败品, 已清产物)

---

## 3. 主题分组 (Phase A 输入)

按"主题相似"分组, 而不是按 style:

### 现有 12 themes + 70 精品覆盖

| theme | 已有精品数 | 待补 (估) |
|---|---|---|
| cs | 12 | ~10 |
| eng | 10 | ~10 |
| medicine | 8 | ~10 |
| humanities | 4 | ~10 |
| education | 7 | ~5 |
| finance | 7 | ~5 |
| law | 2 | ~10 |
| administration | 4 | ~5 |
| agri | 5 | ~5 |
| arts | 5 | ~10 |
| sci | 4 | ~10 |
| gongan | 2 | ~5 |
| business | 1 | ~5 |

总待补 ~100 篇, 分 5-6 批, 每批 15-20 篇同主题。

---

## 4. 一批的工作流 (具体步骤)

```bash
# 1. 选主题 (e.g. law), 挑 1-2 篇精品作基准
ls skills/gaokao-major-explorer/data/curated/*.json | grep -v insurance | xargs -I {} grep -l '"style": "law"' {}

# 2. 列待合成 list (CSV)
# title,slug,style
# 监狱学,prison-studies,law
# 国际法,international-law,law
# 知识产权,intellectual-property,law
# ...

# 3. 并行批量跑 (不串行!)
python3 -m scripts.batch_synth --file batch_law_v1.csv &
python3 -m scripts.batch_synth --file batch_law_v2.csv &  # 多个 worker 并行
wait

# 4. 浏览器逐篇审 (file:// 直接开)
open skills/gaokao-major-explorer/data/curated/prison-studies.html
open skills/gaokao-major-explorer/data/curated/international-law.html
# ...

# 5. 失败清单入 docs/REVIEW_batch_law.md
# | slug | 问题 | 修法 |
# | prison-studies | 课程不专 | 重跑 + 改 prompt |
# | international-law | 速览不统一 | 改 overview_v2 |
```

---

## 5. 质量标准 (人工审 checklist)

每篇开浏览器后, **10 秒判断**:

- [ ] **hero**: 专业名 + 一句金句, 跟精品同 theme 同档
- [ ] **summary**: 80-200 字, 出口+方向+适合/慎选人群
- [ ] **课程**: 5-7 门/块, 课程名专业专属 (e.g. 国际法有"国际公法/国际私法",不是"法学基础")
- [ ] **院校**: 5-10 所, rank 用 A+/A/B+
- [ ] **薪资**: 4 阶段, p50 数值合理 (应届 8-15, 5年 25-40, 10年 40-80)
- [ ] **校友**: 3 条左右, 严禁 P8/P9/VP/CTO 高帽
- [ ] **速览 (overview_v2)**: lede + what + fit + pitfalls, 跟精品同结构
- [ ] **视觉**: 整体跟同 theme 精品"明显同源但有差异"
- [ ] **数据源**: 不空, 不"基于 2024 公开数据估算"裸跑

---

## 6. 失败模式 (踩坑预案)

| 失败 | 修法 |
|---|---|
| medicine style 无 v4 render | 改用 eng theme 渲染 (e.g. 临床医学 → 用"飞行器设计"模板改字段, 保留 medical 字段数据) |
| LLM 输出 curriculum 是 dict 而非 list | batch_synth.py normalizer 已修, 若还失败 → 重跑 |
| 校友身份太高帽 | 手工 sed 改成"某 985 学长" |
| 模板"保险学原理"残留 | 手工 sed replace old_title → new_title |
| overview_v2.pitfalls 仍是 list[str] | 手工 sed 转 dict |
| 整体风格不对 | 重选模板 (走 batch_synth.py 改 sample_json 参数) |

---

## 7. 阶段产物 (commits 节奏)

每批产出 1-2 个 commit:
- commit A: "feat: law theme batch 1 (15 majors)" — 15 篇新 .json + .html + manifest 更新
- commit B: "fix: law batch 1 visual review (3 majors fixed)" — 失败的 3 篇修改

不批量大 commit, 一个主题一批, 出问题回滚粒度小。

---

## 8. 时间估算 (保守)

| 阶段 | 单批时间 | 5 批总 |
|---|---|---|
| A: 主题定版 | 2-3h | 1 次 |
| B: 并行批量 | 30-60min | 2.5-5h |
| C: 人工审 | 2-3h | 10-15h |
| D: 修一批 | 1-2h | 5-10h |
| **小计** | 6-8h/批 | **20-30h** |

用户决策: 质量优先, 不压缩。可后台跑, 不用一直盯着。

---

## 9. 跟 Agent 流水线对比 (为什么传统好)

| 维度 | Agent 流水线 | 传统本地批量 |
|---|---|---|
| 速度/篇 | 140-300s (不达标) | 离线, 不卡用户 |
| 成功率 | 5/5 OK 但 vision 多 FAIL | 人工目测, 失败率 <10% |
| 失败修复 | 改 prompt + 重跑 | 人工改 HTML/JSON, 1-2min |
| 模板覆盖 | 12/13 (medicine 缺) | 全 13, 失败可手工降级 |
| 速览统一 | overview_v2 5 schema 不一致 | 人工对标精品修 |
| 可观测性 | 黑盒 (用户看不到) | 透明 (file:// 直接看) |
| **成本** | ¥1.5/篇 | ¥1.5/篇 (一样) |
| **人力** | 0 | **5-15h/批** |

**质量 = 投入人力**, 这是用户拍板的核心点。

---

## 10. 现在可以开始 (下一步)

等你下次开 session 时:
1. 选第一个主题 (建议 law, 精品少, 待补多)
2. 列待合成 list (10-15 个)
3. 跑 batch_synth.py 跑一批
4. 浏览器审 + 修
5. commit

或者你想先做其他主题 (gongan/business 精品也少), 告诉我优先级。

---

**详细操作见各 batch_synth.py / v4_styles/render.py 注释。本文档是路线图, 不是实施手册。**