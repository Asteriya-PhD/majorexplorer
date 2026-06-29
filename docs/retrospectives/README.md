# docs/retrospectives/

复盘和整理类文档。**只放**: 项目复盘、阶段总结、流程 SOP、决策记录、commit 索引、memory 索引。

**不放**: 单篇 major JSON 改动记录(去 `git log`)、短期 scratchpad(去 `~/.claude/.../memory/`)。

---

## 现有文件

| 文件 | 用途 | 读者 | 字数 | 状态 |
|---|---|---|---|---|
| [`2026-06-26_project-retrospective.html`](2026-06-26_project-retrospective.html) **[Internal]** | 项目内完整复盘(developer/dev) | 开发者 / 协作者 | 1016 中文字(纯事实) | 稳定版 |
| [`2026-06-26_wechat-parents-final.html`](2026-06-26_wechat-parents-final.html) **[WeChat 上篇 · 发布版]** | 公众号发布版(预览用) · 微信编辑器友好(黄底框 / banner / 信息卡片) · 9 道关 + 5 案例 · 薄荷绿主色 #0FB880 | 高三家长 / 教育从业者 | 3726 字 | **本周发 · 首选** |
| [`2026-06-26_wechat-parents-push.html`](2026-06-26_wechat-parents-push.html) **[WeChat 上篇 · 推送版]** | 全 inline-style, 可直接调 `draft/add` API | (机器读) | 3656 字 | 由 `scripts/push_wechat/inline_styles.py` 自动生成 |
| [`assets/wechat-cover-final.png`](assets/wechat-cover-final.png) | **已选定封面** · = `public/marketing/1-hero.png` · 900×383 · 深蓝+金 · 12 主题色元素 | — | — | **本公众号头图** |
| [`assets/wechat-cover_001.jpg`](assets/wechat-cover_001.jpg) | 早期 AI 生图候选 1 (mmx image-01, 1024×1024) | — | — | ❌ 已弃用, 保留作废稿参考 |
| [`assets/wechat-cover_002.jpg`](assets/wechat-cover_002.jpg) | 早期 AI 生图候选 2 | — | — | ❌ 已弃用 |
| [`assets/wechat-cover_003.jpg`](assets/wechat-cover_003.jpg) | 早期 AI 生图候选 3 | — | — | ❌ 已弃用 |
| [`2026-06-26_wechat-parents-revised.html`](2026-06-26_wechat-parents-revised.html) **[WeChat 上篇 · 修订版]** | 你手动润色过的版本(中性样式) | (留作对照) | 3370 字 | **留作对照, 不直接发** |
| [`2026-06-26_wechat-parents.html`](2026-06-26_wechat-parents.html) **[WeChat 上篇 · 初版]** | 第一次拆出的版本 | (留作对照) | 3370 字 | **留作对照, 不直接发** |
| [`2026-06-26_wechat-developers.html`](2026-06-26_wechat-developers.html) **[WeChat 下篇]** | 公众号长文 · 产品圈/开发者 | 产品经理 / 开发者 / 创业者 | 3064 字 | **2 周后发** |
| [`2026-06-26_wechat-version.html`](2026-06-26_wechat-version.html) **[⚠️ 已拆分]** | 原始 5000 字混合版, 已拆为上下篇 | (留作参考) | 5000 字 | **不再发布** |
| [`2026-06-26_wechat-version.md`](2026-06-26_wechat-version.md) **[⚠️ 已拆分]** | 原始混合版 .md, 已拆 | (留作参考) | 4983 字 | **不再发布** |
| [`PUBLISHING_PLAN.md`](PUBLISHING_PLAN.md) | 发布日历 + 发文 checklist + 衍生规划 | 复盘者本人 | — | 进行中 |

**如何选**:
- 写文档 / commit msg / 内部 sync → 用 [Internal]
- **公众号发布** (本周出分季):
  - **首选**: 用 [WeChat 上篇 · 发布版] 直接复制粘贴到 135editor / 秀米 / 微信编辑器
  - 排版前必读: 文件头注释里的 `wechat-article-layout` 排版规范
  - 重要: 关键样式已在文件中内联(黄底框用 section+background-color, 不是 div+background)
- 2 周后发产品圈 → 用 [WeChat 下篇]
- 复盘过程对照 → 用 [修订版] 和 [初版] (已留作历史快照)

**⚠️ 已拆分的两份不要用**: 5/5000 字混合版, 已在 6/26 拆为家长/开发者两版。原文件保留仅作历史参考, 不要再发出去。

**版本迭代说明**:
- 初版: 第一次拆出, 中性排版
- 修订版: 开发者手动润色, 仍中性排版
- **发布版**: 适配 wechat-article-layout 微信公众号排版规范, 含 9 步严审 + 打回精修 3 档叙事, 去技术词, 推荐用这个

详见 [PUBLISHING_PLAN.md](PUBLISHING_PLAN.md)。

---

## 命名规范

```
YYYY-MM-DD_<type>-<slug>.html
YYYY-MM-DD_<type>-<slug>.md
```

`<type>` 候选:
- `project-retrospective` — 整体复盘
- `phase-N-retrospective` — 单阶段复盘
- `decision-record` — 重大决策
- `commit-index` — commit 反查索引
- `memory-index` — memory 索引
- `sop` — 流程 SOP

---

## 数据来源(真理性)

| 数据 | 来源 | 备注 |
|---|---|---|
| commit 时间 / 数量 / msg | `git log` | 唯一权威 |
| 阶段命名 / 决策细节 | `~/.claude/projects/.../memory/*.md` | 推断, 标 [memory] |
| 主观判断 / 估值 | 不写 | "我估计" 不进本目录 |
| 数字 / 比例 | 仅写有 commit / memory 证据的 | 没证据的不写 |
