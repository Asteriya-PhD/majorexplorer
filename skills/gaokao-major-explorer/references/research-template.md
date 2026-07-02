# Major 调研笔记模板

> 借鉴自花叔 `huashu-research`(橙皮书专家 Skill)。
> 用途:每个 major polish / 重写 / audit 前,**先把调研发现写到这里**,再开始动 JSON。
> 价值:可追溯 / 新人接手能直接看 / 多人并发不冲突(每篇独立文件)。

## 路径规范

```
skills/gaokao-major-explorer/references/research/<slug>-<YYYYMMDD>.md
```

例:`references/research/accounting-20260702.md`(2026-07-02 audit 会计学)

**注意**:
- 一个 major 多次 polish 会产生多个文件,**保留历史**(不要覆盖),方便看演变
- 文件名必须包含 slug + 日期,git diff 一眼看到

---

## 模板(复制后填空)

```markdown
# <major 中文名> 调研笔记

调研日期:YYYY-MM-DD
调研者:<agent 名 / 人类>
触发原因:<初始 audit 分数 / 用户反馈 / Day N polish 任务>
当前目标 audit 分:X/10 → 目标 Y/10
相关 commit:见 git log (例: `git log --oneline -- data/curated/<slug>.json`)

## 1. 现状盘点(从 data/curated/<slug>.json 读)

- 字段数:18 / 18 完整?是 / 否(缺哪几个)
- 当前 audit 分:X/10(从 `data/audit_registry.json` 查)
- 历史最高分:Y/10(从 `data/audit_registry.json` 查)
- 历史 audit 轮次:N(从 `data/audit_registry.json` 查)
- 上一版已知问题:<从最近 commit message / REVIEW.md 复制>
- 是否 irreducible 标记?是 / 否(看 `data/audit_registry.json` 的 `flag` 字段)

## 2. m3 audit 5 维度诊断(从 `content_audit_<slug>.json` 读)

| 维度 | 当前分 | 期望分 | 主要问题 |
|------|--------|--------|---------|
| lede | X | 9 | ... |
| who_fits_no | X | 9 | ... |
| pitfalls | X | 9 | ... |
| curriculum | X | 9 | ... |
| top_schools | X | 9 | ... |
| deep_study | X | 9 | ... |
| salary | X | 9 | ... |
| alumni_quotes | X | 9 | ... |

**核心弱点**:<3 个最高 ROI 修法>

## 3. Anti-Pollution 4 自检(写之前必查)

- [ ] lede 不是"X 是研究...的学科"模板
- [ ] who_fits_no 没有跨学科串台
- [ ] deep_study 没有"CS/金融 12%"占位
- [ ] curriculum 公共必修没填专业课

## 4. 同类参考(从 data/curated/ 找 2-3 篇高分同门类)

- <slug1>:<分> 借鉴点:...
- <slug2>:<分> 借鉴点:...
- <slug3>:<分> 借鉴点:...

## 5. 写作计划(本次具体改什么)

- 改 1:<字段> 从 <X 字/格式> → <Y 字/格式> (改的核心理由)
- 改 2:<字段> ...
- 改 3:<字段> ...

## 6. 风险与硬阻塞

- 涉及数据/年份/人名/机构名 → 必查一手源(MOE / 院校官网 / 阳光高考)
- 涉及薪资 → 必对照麦可思 2024 报告
- 涉及选科 → 必查 `references/data-sources.md` 选科要求表

## 7. 完成记录(写完填)

- 改完后 audit 分:X/10
- 实际改的字段:<列表>
- 是否触发 Tier 1 / Tier 2 / Tier 3? <哪种>
- commit hash:<填>

## 8. 调研模式反思(可选,写完思考)

- 这次最大的坑:<一句话>
- 下次同类 polish 可以省下的时间:<一句话>
```

---

## 使用流程

1. **复制模板** → 改文件名为 `<slug>-<YYYYMMDD>.md`
2. **填 1-3 节**(现状盘点 + 5 维度诊断 + 自检),5-10 min
3. **填第 4 节**找 2-3 篇同类参考(读 manifest 同 `discipline` 字段)
4. **填第 5 节**写作计划(具体改什么,1-3 项)
5. **动 JSON** —— 严格按第 5 节执行,不要跑题
6. **改完填第 7 节**(完成记录)
7. **git add** 这个文件 + JSON,一起 commit

## 反模式

- ❌ **不要等改完再写调研笔记** — 写前就建文件,跟 JSON 一起进 commit
- ❌ **不要把调研笔记写得比 JSON 还长** — 5-10 min 写完,不是论文
- ❌ **不要每次都新建** — 同一个 major 第 2 次 polish 应该是 `<slug>-20260702-v2.md`,保留历史
- ❌ **不要忘了填第 7 节** — 没完成记录,后人看不出来你做没做

## 验收标准

- [ ] 文件名格式 `<slug>-<YYYYMMDD>.md`
- [ ] 1-5 节都有内容
- [ ] 跟 JSON 在同一次 commit 里
- [ ] 完成后第 7 节有 audit 分 + commit hash

---

## 引用与起源

本模板借鉴自花叔 `huashu-research`(橙皮书专家 Skill):
- 增量持久化(写前就建文件)
- 调研和写作分离(本文件只做调研,不开始动 JSON)
- 标注可信度(第 6 节硬源 / 一手源要求)

详见 `~/.claude/skills/orange-book-expert/SKILL.md` 和 `references/phase-1-research.md`。