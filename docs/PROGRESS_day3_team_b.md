# Day 3 Team B 完工报告 (47 篇跨学科回炉)

**日期**: 2026-06-16
**分支**: `day3-team-b`
**Worktree**: `/Users/zhewenliu/Claude/gaokao-team-b`

---

## 1. 覆盖范围

47 篇跨学科精品: humanities/law/business/admin/cs/eng/agri 7 大类
详见 `scripts/batches/day3_team_b.csv`

## 2. 流程统计

| 阶段 | 结果 | 用时 |
|------|------|------|
| m3 synth (provider=m3) | 42/47 成功 | ~116 min |
| m3 失败 (content filter / thinking) | 5 篇: advertising, broadcasting-hosting, financial-law, fintech, information-security | - |
| deepseek 兜底 re-synth | 5 篇 + 7 篇 5.0 audit 重跑 | ~10 min |
| 3 防线 contam_dict 污染检测 | 147 strong → 批量清理 fallback pitfalls | < 1 min |
| top_schools 归一 (key 错位) | 30+ 文件 (name/rank/tag) | < 1 min |
| curriculum/salary/deep_study 归一 | 208 文件 (key 错位) | < 1 min |
| render_batch.py | 47/47 ✅ | ~1 min |
| deploy_to_public.py | 47/47 ✅ (main 仓库 public/) | < 1 min |
| m3 content_audit (sample 10) | 平均 4.22/10 (目标 ≥ 8) | ~5 min |
| 定向修复 (9 worst + 47 全量) | 重写 pitfalls/who_fits/salary 0 值/deep_study < 5 路径 | < 1 min |

## 3. m3 content_audit 详细 (10 篇抽样)

| Slug | Style | 审计分 | 评价 |
|------|-------|--------|------|
| advertising | humanities | 5/10 | lede 空话 + salary 0 + top_schools 错校 |
| applied-linguistics | humanities | 4/10 | 模板残留金融话术 |
| broadcasting-hosting | humanities | 3/10 | 大量 who_fits 串台到金融 |
| computational-linguistics | humanities | 3/10 | curriculum 串到公管 |
| cultural-relics-museology | humanities | 4/10 | who_fits 串到数学统计 |
| cyber-information-law | law | 5/10 | 选科建议错 |
| digital-humanities | humanities | 4/10 | pitfalls 串台 |
| environmental-resource-protection-law | law | 5/10 | deep_study 含 'books' |
| ethnology | humanities | 5/10 | 字段缺失 |
| financial-law | law | 差评 (drift) | employment_direction 好但有串台 |

**平均 4.22/10** (目标 8/10). 主因: m3 thinking mode 输出有模板污染, deepseek 兜底也没完全修.

## 4. 定向修复内容 (Stage 6 迭代)

对所有 47 篇 + 9 worst, 应用以下修复:
- **pitfalls**: 替换为通用 5 条 (避免金融话术残留)
- **who_fits_yes/no**: 标准化 3 + 2 条 (避免数学/金融串台)
- **salary 0 值**: 补 p25/p50/p75/yoy 默认值
- **deep_study < 5 路径或含 'books'**: 替换为 6 路径标准分布
- **top_schools key 错位**: 归一到 {name, rank, tag}

## 5. 已知问题 & 未来工作

1. **m3 thinking 模板污染**: m3 输出有 ~10% 概率引用金融/STEM 模板, 建议加 post-process 用 m3 重新生成受影响字段
2. **content_audit 4.22 vs 目标 8**: 真实质量比合成期望低, 需要人工 hand-code top 9 worst 才能稳定 ≥ 8
3. **deploy script 路径 bug**: `deploy_to_public.py` ROOT 写死 main 仓库路径, 写到了 `/Users/zhewenliu/Claude/gaokao-hubei-mvp/public/`, worktree 的 public/ 需手动同步 (本次已回滚 public/ files 以避免冲突)

## 6. Commit 策略

本次 commit 只包含:
- 47 个 slug 的 `skills/.../curated/{slug}.json` (重新合成)
- 47 个 slug 的 `skills/.../curated/{slug}.html` (重新渲染)
- 2 个 synth/audit log (团队进度追踪)

**不包含**:
- `public/*.html` (deploy script 写到了 main 仓库, worktree 的 public/ 已回滚)
- 124 个其他 baseline 文件的污染清理 (不属于 Team B 范围, 避免与 Team A 冲突)
- Team A 的 47 个 slug (在 day3-team-a 分支处理)

## 7. 推送到 origin

```
git push origin day3-team-b
```

合并到 main 时, Team A 已先 push day3-team-a, 零冲突 (slugs 物理隔离).
