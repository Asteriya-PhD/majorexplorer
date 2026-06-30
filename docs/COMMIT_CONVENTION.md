# Commit Convention — YYYYMMDD 物理日期 + a/b/c session 后缀

> 2026-06-30 启用. 取代历史 "Day N" 虚拟日期表述 (Day N 是 Claude 估算, 不代表真实物理时间).

---

## 格式

```
<type>(<scope>): <YYYYMMDD> [<session>] <任务名>
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `type` | ✓ | fix / chore / docs / feat / refactor / perf / test |
| `scope` | 选 | content / render / deploy / seo / audit / hook |
| `YYYYMMDD` | ✓ | **物理日期** (e.g. `20260630`). commit 实际发生的日期, 不是工程量估算 |
| `[session]` | 当日多 session 时 | `a` / `b` / `c` / `d` / `e` / `f` — 按 commit 时间升序, `a` 最早 |
| 任务名 | ✓ | 中文简短描述, 含数量/影响 |

---

## 当日多 session 排序规则

同一物理日 (e.g. 2026-06-30) 多个 commit session 时:
- 按 **commit 时间升序** 排字母
- `a` = 当天**最早** commit 的 session
- `f` = 当天**最晚** commit 的 session
- 不按工作量 / 重要性排, 只按时间

**反查**:
```bash
# 查 2026-06-30 当天所有 commit + 排序
git log --since="2026-06-30 00:00" --until="2026-06-31 00:00" \
  --format='%h %ai %s' | sort -k2
# 第一个 = a, 第二个 = b, ...
```

---

## 例 (2026-06-30 当天 5 个 session, 按 commit 时间)

| 时间 (实际) | 字母 | commit message |
|---|---|---|
| 13:32 | a | `chore(registry): 20260630 [a] Day 49.1 baseline render_quality 100% clean` |
| 16:29 | b | `fix(content): 20260630 [b] 15 篇 major xuanke 字段名规范化` |
| 16:31 | c | `fix(content): 20260630 [c] 37 篇 major 删 salary 错位 note` |
| 16:39 | d | `fix(content): 20260630 [d] 7 篇 major 修 hero_quote 署名/长度` |
| 16:41 | e | `chore(hook): 20260630 [e] render_quality ERROR-block 切流` |
| 17:35 | f | `docs: 20260630 [f] 5 文档 v1.7 全面瘦身` |

> 上表是回填示例, 实际 2026-06-30 commit message 还用 "Day N" 旧格式. 未来新 commit 全部用 `YYYYMMDD [session]` 格式.

---

## 历史 (2026-06-30 之前)

旧 commit message 沿用 `Day N` 格式, **不重写** (git immutable). 阅读方式:
- `git log --format='%ai %s'` — commit 时间戳是真实物理时间, 用作回溯
- 文档头部 (`CLAUDE.md` / `AGENTS.md` / `PIPELINE_major_quality.md` / `RENDER_QUALITY_RULES.md` / `DEPLOYMENT.md`) 已加 "📅 物理日期映射" 表, 任何 "Day N" 翻表即查

**reviewer 规则**: 看到 2026-06-30 之后 commit message 仍用 "Day N" 前缀 → 拒绝合入, 要求作者改 `YYYYMMDD [session]` 格式.

---

## 反例 (不接受的 commit message)

```
❌ fix(content): Day 50 15 篇 major xuanke 字段名规范化
   (Day N 是估算, 不是 2026-06-30)

❌ fix(content): 修复 xuanke
   (缺日期 + 缺 session + 任务描述太简)

❌ fix(content): 2026-06-30 15 篇 major xuanke 字段名规范化
   (缺 [session] 后缀, 2026-06-30 当天多 commit 会混淆先后)

❌ fix(content): 0630 [a] xuanke 字段名
   (日期应 8 位 YYYYMMDD, 不缩写; 任务名太简)
```

---

## 关联文档

- `CLAUDE.md` 核心铁律 — 新 commit 必用本规则
- `~/.claude/plans/<YYYYMMDD>-<name>.md` — plan 文件命名同步规则
- `docs/PIPELINE_major_quality.md` 头部 — Day N → YYYYMMDD 映射表
