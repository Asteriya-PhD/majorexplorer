# Major Explorer — 看清专业,再谈志愿

> 🎓 公益项目 · 给一无所知的 18 岁高三生看的, 不是给已经会算位次的家长看的

**🌐 访问地址**: [https://majorexplorer.com](https://majorexplorer.com)

## 这是什么

湖北高考专业深度分析平台, **70+ 个热门本科专业**的精编 dashboard, 每个专业包含:
- 📚 **学习内容** — 基础课 / 方向分流 / 核心技能
- 👤 **适合人群** — 性格 / 兴趣 / 价值观匹配
- ⚠️ **避坑指南** — 6-7 个常见误区 (基于校友真实反馈)
- 💼 **就业方向** — 真实薪资样本 + 雇主名单
- 🏫 **院校推荐** — 软科 + 教育部学科评估 + 校友会排名
- 💬 **校友自述** — 知乎/小红书 2018-2026 学长学姐真实反馈

## 跟"百度搜" 不同的 5 件事

1. **位次驱动, 不是分数驱动** — 2025 年 580 分和 2024 年 580 分能上的学校完全不同, 真正稳的标尺是全省位次
2. **3+1+2 选科硬过滤** — 物化生 / 史地政 / 各种组合严格匹配
3. **三级冲稳保概率** — Gaussian CDF 估录取概率, 不是简单的"位次段匹配"
4. **96 志愿完整生成** — 不是示例 8 所, 是真能填的 96 个方案
5. **按需生成** — 没收录的专业, LLM 临时合成 (mock 模式可本地运行)

## 项目特点

- ✅ 70+ 个精品专业 dashboard, 13 个主题 (CS / 工程 / 医学 / 教育 / 商科 / 公安 / 农林 / 艺术 / 等)
- ✅ 2024 + 2025 湖北真实投档表 + 一分一段表
- ✅ LLM 按需生成 (SCF 后端, 可选)
- ✅ 心愿单 + 智能推荐 + 搜专业
- ✅ 纯公益, 不变现
- ✅ License: **AGPL-3.0** (允许自用, 禁止商用)
- ✅ 部署: Cloudflare Pages 海外, 国内优选 IP 30-100ms

## 项目结构

```
gaokao-hubei-mvp/                ← 项目根
├── public/                      ← 静态站 (Cloudflare Pages 部署目标)
│   ├── index.html               ← 主页
│   ├── {70+ slug}.html          ← 精品专业 dashboard
│   ├── css/, js/, data/         ← 静态资源
│   ├── sitemap.xml              ← SEO
│   └── robots.txt               ← SEO
├── scf/synth/                   ← LLM 按需生成后端 (Python 3.11, 待部署)
├── data/                        ← 投档表 / 一分一段表
├── core/                        ← 纯函数算法 (filter / probability / strategy)
├── scripts/                     ← 工具脚本 (build_sitemap / inject_seo / fetcher)
├── skills/                      ← Claude skill 化的 prompts + 模板
├── docs/                        ← 文档
├── deploy/                      ← 部署脚本 (Cloudflare Pages 指南 + 优选 IP)
├── LICENSE                      ← AGPL-3.0 全文
├── TRADEMARK.md                 ← 商标政策
└── README.md
```

## 快速开始 (本地预览)

```bash
# 1. 克隆
git clone https://github.com/Asteriya-PhD/majorexplorer.git
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
| 决策记录 | [docs/DECISIONS.md](docs/DECISIONS.md) | 维护者 (19 个 ADR) |
| 进度状态 | [docs/PROGRESS.md](docs/PROGRESS.md) | PM / 任何角色 |
| 架构 | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构师 / 资深工程师 |
| 数据 | [docs/DATA.md](docs/DATA.md) | 数据工程师 |
| AI agent 入口 | [docs/AGENTS.md](docs/AGENTS.md) | AI agent |
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

最后更新: 2026-06-12 · 部署 v2 (ADR-016 ~ 019)
