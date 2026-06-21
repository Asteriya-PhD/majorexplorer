# Day 17 Plan: Cleanup Pass + Irreducible-7 Flag + Mobile Sync

> **日期**: 2026-06-21 重开 session  
> **前置**: Day 16 E 完工, 8+ **414/475 (87.2%)** 7-8 50 / 6-7 10 / <6 0  
> **目标**: 3 worker 并行 worktree 隔离, ~4h 总投入, 0¥ API 成本, 单 commit push main

## 🎯 3 选项总览

| 选项 | 任务 | 估时 | ROI |
|------|------|------|-----|
| **A. Cleanup pass** | 414 8+ JSONs 扫 自主创业/其他 + schema 漂移 + 缺失字段 | 2-3h | 极高 (+5-10pp) |
| **B. Mark irreducible-7** | 50 篇 7-8 variance stuck 加 flag + reason | 30min | 中 (省 ¥) |
| **C. Mobile sync** | 20 篇近期 polished 补 mobile | 1h | 高 (mobile 404) |

## 👷 Worker A: Cleanup Pass (~2-3h, wt-cleanup)

3 子任务脚本 (新建, dry-run → 人工 review → apply):

```python
# scripts/cleanup_entrepreneur.py — 扫 employment_direction / deep_study 占位
ENTREPRENEUR_MAP = {
    'agri': '自主创业 (家庭农场/合作社/农资经销)',
    'arts': '自由职业 (画廊签约/独立工作室)',
    'finance': '自主创业 (私募/咨询/家族办公室)',
    'cs': '自主创业 (AI 创业/SaaS/外包)',
    'medicine': '自主创业 (私人诊所/医美机构)',
    'eng': '自主创业 (工程咨询/技术服务)',
    'law': '自主创业 (律所合伙人/法律科技)',
    'humanities': '自主创业 (翻译公司/文化传媒)',
    'administration': '自主创业 (管理咨询/猎头)',
    'gongan': '考公 (公安联考入警, 不算创业)',
    'safety': '自主创业 (EHS 咨询/安全评价)',
    'sci': '自主创业 (科研服务/数据分析)',
}
# scripts/normalize_schema.py — 旧 key → 新 key + list[str] → list[dict]
RENAMES = {'通用专业核心': '通用专业核心 (≈ 80% 院校覆盖)',
           '公共必修': '公共必修 (所有院校都开)',
           '5 校特色选修': '5 校特色选修 (按方向分流)'}
# scripts/check_schema_gaps.py — 只报告 18 字段缺失
# → data/cleanup_entrepreneur_report.json + schema_drift.json + schema_gaps.json
```

## 👷 Worker B: Mark Irreducible-7 (~30min, wt-irred-7)

**`scripts/mark_irreducible_7.py`** (沿用 Day 14.5 irreducible-6 pattern)

```python
# 扫 data/audit_registry.json, 找 current_score=7 + audit_history ≥ 4 次
# flags += ['irreducible-7']
# tier_history: {"irreducible-7": true, "irreducible_reason": "..."}
# 阈值: 7 边界 ±1 多次 variance stuck, 内容已完整
# 输出: registry 50 篇加 flag, variance verify 跳过省 ¥
```

## 👷 Worker C: Mobile Sync (~1h, wt-mobile)

```bash
for slug in intelligent-imaging-art kyrgyz-language safety-engineering commercial-law \
  postal-management breeding-science emergency-equipment-technology-and-engineering \
  real-estate-development-and-management additive-manufacturing-engineering \
  intelligent-interaction-design mechanical-process-technology \
  acting vietnamese logistics-management ocean-science traditional-chinese-medicine \
  business-japanese digital-journalism chinese-veterinary-medicine; do
  python3 skills/gaokao-major-explorer/scripts/render_mobile.py \
    --data skills/gaokao-major-explorer/data/curated/${slug}.json \
    --style $(jq -r '.style' skills/gaokao-major-explorer/data/curated/${slug}.json) \
    --output public/m/${slug}.html
done
# 失败 skip + log
```

## 🛡️ 安全 / 验收

| 风险 | 缓解 |
|------|------|
| Cleanup 改坏 JSON | dry-run → 人工 review → apply |
| Schema 改名 v4 render 失败 | `generate_dashboard.py` 5 篇抽样 |
| Mobile render 失败 | 逐个 try, 失败 skip + log |
| Registry 冲突 | 各自 worktree, 各自 commit 后 merge |
| m3 variance | irreducible-7 标后 1 次 variance verify |

| 指标 | 目标 |
|------|------|
| A 完成 | 414 JSONs 扫过, 占位 0, drift 0, gaps.json 输出 |
| B 完成 | 50 篇 7-8 全部标 irreducible-7 + reason |
| C 完成 | 20 篇 mobile HTML, `/m/${slug}.html` 可访问 |
| **0 regressions** | 8+ 414 (87.2%) ≥ 90% 不能掉 |
| **1 commit** | 单 commit push main |

## 📝 Commit Message

```
fix(cleanup): Day 17 schema cleanup + irreducible-7 flag + mobile sync

Phase A Cleanup (414 8+ JSONs, wt-cleanup):
- 自主创业/其他 占位 N 处替换 (style × slug 映射)
- schema 漂移统一 (旧 key → 新 key, list[str] → list[dict])
- 18 字段缺失报告 (gaps.json, 人工 review)

Phase B Irreducible-7 Flag (50 篇 7-8, wt-irred-7):
- flags += ['irreducible-7'] + tier_history + reason
- 后续 variance verify 跳过这些省 ¥

Phase C Mobile Sync (20 篇 Day 16 polished, wt-mobile):
- intelligent-imaging-art / kyrgyz / safety / commercial / postal /
  breeding / emergency-equipment / real-estate / additive-mfg /
  intelligent-interaction / mechanical-process / acting / vietnamese /
  logistics / ocean-science / tcm / business-japanese / digital-journalism /
  chinese-veterinary
- /m/<slug>.html 全部生成, mobile 404 修复

Registry: 8+ 414 (87.2%) 持, 7-8 50 → irreducible-7 池, <6 0
```

## ⏱️ 时间 (3 路并行 ~4h) / 📁 文件

| 任务 | 估时 |
|------|------|
| A.1-3 自主创业 + schema + gaps | 2-3h (wt-cleanup) |
| B. irreducible-7 flag 50 篇 | 30min (wt-irred-7) |
| C. mobile sync 20 篇 | 1h (wt-mobile) |
| 3 worktree merge + 收尾 commit | 30min (main) |

**新建**: `scripts/cleanup_entrepreneur.py` · `scripts/normalize_schema.py` · `scripts/check_schema_gaps.py` · `scripts/mark_irreducible_7.py`
**修改**: `data/audit_registry.json` (50 篇 flag) · `public/m/<20 slugs>.html` (mobile)
**不修改**: 414 JSONs 字段值 (A 只改 schema key)

## 🔗 关联

`docs/PIPELINE_major_quality.md` § 已知坑 #7 · Day 8.5 polish (cleanup 模式) · Day 11.5 mobile (模板就绪) · Day 14.5 irreducible-6 (B 沿用 pattern)