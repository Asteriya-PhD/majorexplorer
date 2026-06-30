# Major Explorer — 看清专业,再谈志愿

> 🎓 公益项目 · 给一无所知的 18 岁高三生看的, 不是给已经会算位次的家长看的

**🌐 访问地址**: [https://majorexplorer.com](https://majorexplorer.com)

## 这是什么

湖北高考专业深度分析平台, **625 个热门本科专业**的精编 dashboard, 每个专业包含:
- 📚 **学习内容** — 基础课 / 方向分流 / 核心技能
- 👤 **适合人群** — 性格 / 兴趣 / 价值观匹配
- ⚠️ **避坑指南** — 6-7 个常见误区 (基于校友真实反馈)
- 💼 **就业方向** — 真实薪资样本 + 雇主名单
- 🏫 **院校推荐** — 软科 + 教育部学科评估 + 校友会排名
- 💬 **校友自述** — 知乎/小红书 2018-2026 学长学姐真实反馈

## 跟"百度搜" 不同的 5 件事

1. **位次驱动, 不是分数驱动** — 2025 年 580 分和 2024 年 580 分能上的学校完全不同, 真正稳的标尺是全省位次
2. **3+1+2 选科硬过滤** — 物化生 / 史地政 / 各种组合严格匹配
3. **智能推荐** — 客户端 JS 跑 (98 志愿) + 心愿单 + 软科/学科评估 综合排序
4. **按需生成** — 没收录的专业, LLM 临时合成 (CF Pages Function + GH Action, mock 模式可本地运行)
5. **完整院校/雇主数据** — 院校 6-10 所 + 雇主 6-10 家 (S/A/B tier), 校友真实反馈 3-5 条

## 项目特点

- ✅ 625 个精品专业 dashboard, 13 个 style (CS / 工程 / 医学 / 教育 / 商科 / 公安 / 农林 / 艺术 / 等)
- ✅ 2024 + 2025 湖北真实投档表 + 一分一段表
- ✅ LLM 按需生成 (CF Pages Function + GH Action, 可选)
- ✅ 心愿单 + 智能推荐 + 搜专业
- ✅ PC + Mobile 双轨 (H 阶段对齐: PC 反馈 + 搜索报告, 移动端 dock 5 tab)
- ✅ Cloudflare Web Analytics 接入 (2026-06-12, Core Web Vitals 监控)
- ✅ 反馈 + 未收录报告闭环 (G 阶段, GH Issue 自动归档)
- ✅ 质量门双保险 (Day 56+, 预 commit 硬阻塞 + 全量 baseline 双零)
- ✅ 纯公益, 不变现
- ✅ License: **AGPL-3.0** (允许自用, 禁止商用)
- ✅ 部署: Cloudflare Pages 海外, 国内优选 IP 30-100ms

## 项目结构

```
gaokao-hubei-mvp/                ← 项目根
├── public/                      ← 静态站 (Cloudflare Pages 部署目标)
│   ├── index.html               ← 主页
│   ├── {625 slug}.html          ← 精品专业 dashboard (PC)
│   ├── m/majors/{slug}.html     ← 精品专业 dashboard (Mobile)
│   ├── css/, js/, data/         ← 静态资源 (客户端纯 JS 跑推荐)
│   ├── sitemap.xml              ← SEO (~640 URL)
│   └── robots.txt               ← SEO
├── functions/                   ← Cloudflare Pages Functions (TypeScript)
│   ├── _middleware.ts           ← 手机 UA → /m/ 自动跳转
│   └── api/                     ← synth 入队 + status 查询 + report 反馈
├── .github/workflows/           ← GH Action cron */1 跑 synth_queue_worker
├── data/                        ← 投档表 / 一分一段表 (canonical CSV)
├── scripts/                     ← 工具脚本 (build_sitemap / inject_* / smart_audit / synth_*)
├── skills/                      ← Claude skill 化的 prompts + 模板
├── docs/                        ← 文档
├── deploy/                      ← 部署脚本 (Cloudflare Pages 指南 + 优选 IP)
├── wrangler.toml                ← CF Pages 配置 + D1 binding
├── CLAUDE.md                    ← 项目指引 (项目入口)
├── AGENTS.md                    ← AI agent 入口 (与 CLAUDE.md 同内容, 别名)
├── LICENSE                      ← AGPL-3.0 全文
├── TRADEMARK.md                 ← 商标政策
└── README.md
```

## 快速开始 (本地预览)

```bash
# 1. 克隆
git clone https://github.com/<your-org>/majorexplorer.git
cd majorexplorer

# 2. 本地预览 (纯静态, 无后端)
cd public
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```

## 文档

| 入口 | 文件 | 给谁看 |
|------|------|--------|
| **🌐 访问** | **https://majorexplorer.com** | **用户 (高三生 / 家长)** |
| 部署方案 | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | 想部署的人 |
| 决策记录 | [docs/DECISIONS.md](docs/DECISIONS.md) | 维护者 (21+ 个 ADR, 含 ADR-021 FastAPI 删除) |
| 架构 | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构师 / 资深工程师 |
| 数据 | [docs/DATA.md](docs/DATA.md) | 数据工程师 |
| 质量流水线 v1.6 | [docs/PIPELINE_major_quality.md](docs/PIPELINE_major_quality.md) | 写/改/批量生成 major JSON 前必读 |
| HTML 渲染质量门 13 规则 | [docs/RENDER_QUALITY_RULES.md](docs/RENDER_QUALITY_RULES.md) | 理解 render_quality.py 规则 |
| 部署方案 | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | 想部署的人 (含 Cache 4 层锁死 SOP) |
| AI agent 入口 | [AGENTS.md](AGENTS.md) (项目根) | AI agent |
| 部署操作 | [deploy/cloudflare-pages.md](deploy/cloudflare-pages.md) | 部署者 |
| 商标政策 | [TRADEMARK.md](TRADEMARK.md) | 想用 MajorExplorer 名字的人 |

## License

**AGPL-3.0** ([LICENSE](LICENSE)) — 自由使用, 禁止商用, 修改需开源

简单说:
- ✅ 你可以 fork / 修改 / 自用 / 做公益
- ❌ 你不能用本项目做付费产品 / 商业服务
- ❌ 你不能注册 "MajorExplorer" 相关商标/域名

详细条款见 [LICENSE](LICENSE) + [TRADEMARK.md](TRADEMARK.md)。

## 致谢

数据来源: 教育部学科评估 / 软科 / 校友会 / 麦可思 / 职友集 / 阳光高考 / 各校培养方案
LLM 后端: DeepSeek API
托管: Cloudflare Pages (海外免备案, 21 接入商国内优选 IP)
CDN + DNS: Cloudflare

## 反馈

在 GitHub Issue 提问题 / 反馈 / 合作意向。

---

最后更新: 2026-06-30 · Day 56 双保险 + 双零 baseline 完工 (625/625 clean)
