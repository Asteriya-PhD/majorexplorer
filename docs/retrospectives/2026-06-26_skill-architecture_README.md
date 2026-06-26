# 技术架构长图系列 · 发布物清单

> 2026-06-26 完工的「gaokao-major-explorer 30 天技术架构沉淀」一文, 针对不同发布渠道打包了三套产物。

## 📦 三份产物

| 文件 | 大小 | 适用渠道 | 排版特点 |
|---|---|---|---|
| `2026-06-26_skill-architecture.html` | 25 KB | 个人博客 / Hexo / Hugo / 静态站 | 桌面优先 (1280px), 暖橙印刷纸张质感, `@media print` 支持导出 PDF |
| `2026-06-26_skill-architecture_wechat.html` | 23 KB | **微信公众号** | 手机优先 (≤640px), 无 `var()` / `backdrop-filter`, 公众号编辑器零冲突 |
| `2026-06-26_skill-architecture.md` | 154 行 | 知乎 / 掘金 / GitHub / Dev.to | 标准 Markdown, ASCII 图已转 PNG |

## 🖼️ 配套资源

```
docs/retrospectives/
├── 2026-06-26_skill-architecture.html          ← 桌面版 (博客)
├── 2026-06-26_skill-architecture_wechat.html  ← 公众号版
├── 2026-06-26_skill-architecture.md            ← Markdown 版
└── assets/skill-arch-2026-06-26/
    ├── og-card.html                ← OG 分享卡源 (1200×630, 桌面用)
    ├── og-card.png                 ← OG 分享卡图片 (社交平台转发用)
    ├── ascii_1.png                 ← 架构全景图
    ├── ascii_2.png                 ← 模块依赖图
    ├── ascii_3.png                 ← 主题目录
    ├── ascii_4.png                 ← 4 层架构图
    └── ascii_5.png                 ← 端到端时序图
```

## 🚀 发布步骤

### 1. 微信公众号 (推荐首发)

```bash
# Step 1: 把公众号版 HTML 转成 inline-style 版 (微信编辑器可推送)
python3 scripts/push_wechat/inline_styles_v2.py

# Step 2: 推送到公众号草稿箱
python3 scripts/push_wechat/push_draft.py
```

成功后会输出 `✅ 草稿已创建: {media_id}`。登录微信公众平台 → 草稿箱, 检查预览 → 改封面/标题 → **手动点"发布"**。

> **注意**: 公众号 API 标题限 **32 字节 (10 汉字)**。当前推送版标题 `16 天演化 · 质量分 7.0 → 9.05` 27 字节 ✓。

### 2. 个人博客 (Hexo / Hugo)

直接把 `2026-06-26_skill-architecture.html` 拷贝到 `source/_posts/` 或 `content/posts/` 目录, 提交即可。`_headers` 已配置正确 cache 头。

### 3. 知乎 / 掘金 (Markdown 友好)

打开 `2026-06-26_skill-architecture.md` → 全选复制 → 粘贴到知乎/掘金 Markdown 编辑器。5 张架构图自动通过相对路径 `assets/skill-arch-2026-06-26/ascii_N.png` 加载。

### 4. 社交平台转发 (Twitter / 微博 / LinkedIn)

使用 `assets/skill-arch-2026-06-26/og-card.png` (1200×630) 作为配图。`og:title` / `og:description` 已内嵌在 HTML 中。

## ⚠️ 发布前 checklist

- [ ] 标题长度 ≤ 32 字节 (公众号 API 限制)
- [ ] 封面图 900×500 (公众号首图规格) 或 1200×630 (OG 卡规格)
- [ ] 摘要 50-80 字, 用引子段第 1 段即可
- [ ] 段落中无英文术语残留 (polish / variance / gap-fill 等)
- [ ] 表格列名明确标注单位 (如「平均分」而不是「质量」)
- [ ] 章节末有明确过渡 (不要「下面第 7 章展开」)

## 🔄 修订历史

| Commit | 修订内容 |
|---|---|
| `0365f6f9` | 初版: HTML 双版本 |
| `f96be523` | 加 Markdown 版 + 5 PNG |
| `4633a363` | 6 处诚实化修订 |
| `d61a19c4` | 时间线 git 实测日期锚定 |
| `98773f33` | 9 步表英译中 + 智能路由并入步骤 5 |
| `72672c7e` | 时间线改用读者视角 + 删内部声明 |
| `c567bc33` | 时间线改用质量分曲线叙事 + 数据核实修正 |
| `31c7192b` | 删内部交流痕迹 + 时间线加密 + 经验翻译 |
| `c3a3b0e3` | 4 项读者视角修正 |
| `a9fb647f` | 删 6/25 行 — 曲线收尾 |
