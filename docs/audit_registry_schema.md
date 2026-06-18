# Audit Registry Schema (v1.0)

> 单一真相: `data/audit_registry.json` (git tracked)
> 替代: `test_results/content_audit_*.json` (gitignore, 跨 session 失同步)
> 写入工具: `scripts/update_audit_registry.py`
> 消费者: `scripts/smart_audit.py` (Layer 2 路由决策依赖此文件)

## 解决的问题

| 旧痛点 | 新方案 |
|--------|--------|
| 审计历史在 `test_results/` (gitignore) | git tracked, 跨 session 同步 |
| 不知道"哪些 slug 从未 audit" | `stats.never_audited` + `totals` 直接给 |
| 不知道"X 篇从 5 改到 8 的全过程" | `majors[slug].audit_history` 时间线 |
| agent 看不到对方 session 的 audit 结果 | pull main 即同步 |
| "当前 8 分以上多少个"要现算 | `stats.currently_8+` 缓存好 |

## Schema

```jsonc
{
  "version": "1.0",
  "updated_at": "2026-06-18T...",

  "totals": {
    "majors": 277,            // manifest 总数
    "audited": 158,            // 有 audit 历史的
    "never_audited": 119,      // manifest 内但从未 audit
    "external_audited": 2      // audit 过但不在 manifest (如 TEMPLATE)
  },

  "stats": {
    "audited_3+": 100,         // 多次 audit
    "audited_once": 58,        // 单次 audit
    "currently_8+": 112,       // 当前 8 分以上 (优秀)
    "currently_7-8": 37,       // 当前 7-8 (合格)
    "currently_6-7": 2,        // 当前 6-7 (可接受)
    "currently_below_6": 2     // 当前 < 6 (需修)
  },

  "majors": {
    "actuarial-science": {
      "title": "精算学",
      "style": "business",
      "discipline": "02",       // 13 门类代码
      "audit_count": 5,
      "current_score": 8.0,
      "current_verdict": "优秀",
      "last_audit_at": "2026-06-18T...",
      "tier_history": ["P0", "P1"],   // 手填, 标记 P0→P1→...
      "audit_history": [         // 按时间倒序, 最新在前
        {
          "date": "2026-06-18T...",
          "timestamp": 1781747659,
          "source_file": "content_audit_1781747659.json",
          "score": 8.0,
          "verdict": "优秀",
          "highlights": ["..."],  // 限 3 条
          "issues": [{"field": "lede", "score": 8, "issue": "..."}],
          "fix_suggestion": "..."
        },
        // 之前的 audit...
      ]
    }
  }
}
```

## Verdict 等级 (基于 overall_score 0-10)

| 分数 | Verdict | 含义 |
|------|---------|------|
| ≥ 8 | 优秀 | ✅ 达标, 不需修 |
| 7-8 | 合格 | ✅ 达标, 可选小修 |
| 6-7 | 可接受 | ⚠️ 有缺陷, 建议改 |
| < 6 | 需修 | ❌ 必修, 走 Tier 1/2 |

## 使用方式

### 1. 任意 agent 跑完 audit 后登记

```bash
# 自动模式: content_audit.py 跑完后
python3 scripts/update_audit_registry.py --from-file test_results/content_audit_xxx.json

# 批量: 整个目录
python3 scripts/update_audit_registry.py --from-dir test_results/

# 全量重建 (初始化或 schema 升级)
python3 scripts/update_audit_registry.py --rebuild
```

### 2. smart_audit.py 路由决策 (已接入)

```
Layer 2 触发条件:
  - L1 warning/error
  - 从未 audit 过 (registry 中无 audit_history)
  - 历史 < 7.0 (registry 中 current_score < 7.0)
  - 上次 audit 后改过 (mtime > last_audit_at)
  - 5% 随机抽样
```

### 3. 查询接口 (CLI)

```bash
# 看当前统计
python3 scripts/update_audit_registry.py --stats

# jq 查 8 分以上但已超过 7 天没 audit 的 (可能 stale)
jq '.majors | to_entries | map(select(.value.current_score >= 8)) | length' data/audit_registry.json

# 查某 slug 历史
jq '.majors["actuarial-science"]' data/audit_registry.json
```

## 集成 checklist

- [x] `data/audit_registry.json` 创建 (从 test_results/ 110 个 content_audit_*.json import)
- [x] `scripts/update_audit_registry.py` 工具 (--rebuild/--from-file/--from-dir/--from-stdin/--stats)
- [x] `scripts/smart_audit.py` 优先读 registry, fallback test_results/
- [ ] `scripts/batches/content_audit.py` 跑完自动调 update_audit_registry (TODO: 下次 PR, 当前手动)
- [ ] CLAUDE.md 引用本文件 (TODO: 下次 PR)
- [ ] 任何 agent 写新 major 后, 跑 `update_audit_registry.py --rebuild` 同步

## 注意事项

- **git tracked**: 任何改动都会进 commit history, 警惕不要 commit 敏感数据 (LLM API key 等)
- **冲突**: 多人同时改 registry 可能冲突, 跟代码一样 git pull/rebase 处理
- **体积**: 110 个 audit + 完整 history = 2.2MB, 277 个全 audit 估 4-5MB, 仍可接受
- **真理性**: registry 是 cache, 真理性在 `public/data/manifest.json` (major 列表) + `test_results/content_audit_*.json` (审计原始数据), registry 是 derived 视图
