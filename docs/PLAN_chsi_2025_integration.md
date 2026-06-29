# chsi 2025 数据接入 Plan (2026-06-29)

> **状态**: Day 40 Phase 4 prep — chsi 2025 数据缓存接入准备
> **数据源**: gaokao.chsi.com.cn (阳光高考) + patchright 破阿里云反爬
> **现状**: public/data/chsi_*.json 是 2026-06-14 fetch (~15 天前), 868 majors, 2950 schools

---

## 📊 当前 chsi 数据现状

| 文件 | 行数 | 大小 | updated_at | 估 |
|------|------|------|-----------|-----|
| `public/data/chsi_majors.json` | 868 | 301KB | 2026-06-14 | Day 14 Phase 2 |
| `public/data/chsi_schools.json` | 2950 | 1.6MB | 2026-06-14 | Day 14 Phase 2 |
| `public/data/chsi_major_details.json` | - | 497KB | 2026-06-15 | Day 14 Phase 2 |
| `public/data/chsi_merge_report.json` | - | 593B | 2026-06-14 | Day 14 |

**当前应用层**: 抓一次后基本未刷新,Day 14 chsi Phase 2 已 ship (commit 6a322ba)

---

## 🎯 Day 40 Phase 4 目标 (1-2h prep)

### 任务清单

| # | 任务 | 估时 | 状态 |
|---|------|------|------|
| 1 | 备份当前 chsi_majors.json (防止 fetch 失败) | 2 min | ✅ do it |
| 2 | 检查 chsi_fetch.py 是否有 `--year 2025` flag | 5 min | TODO |
| 3 | 写 `docs/PLAN_chsi_2025_integration.md` (后续 session 用) | 30 min | ✅ this doc |
| 4 | diff 当前 manifest.json vs chsi_majors.json (是否有专业 rename) | 10 min | TODO |
| 5 | 试探性 fetch 2025 (5 majors 看反爬是否升级) | 30 min | TODO |

---

## 📋 Phase 1-4 行动 (后续 Day 41-42)

### Phase 1 (Day 41): 备份 + fetch 任务
- 备份 `chsi_majors.json` + `chsi_schools.json` 到 `public/data/_backup_chsi_2026-06-29/`
- 跑 `python3 scripts/build/chsi_fetch.py --year 2025` (上半自动)
- 试探 5 majors (哲学/经济学/法学/教育学/文学) 看 patchright 是否仍可用

### Phase 2 (Day 41-42): 完整 fetch
- 抓 868 majors 全量 (~30 min patchright)
- 抓 2950 schools (~5 min)
- diff vs 2024 看新增专业 / 招生代码变更 / 专业合并

### Phase 3 (Day 42): 集成
- 更新 chsi_majors.json 注入 manifest
- 重建 aggregates.json
- 测试聚合页 majors.html + mobile 视图
- 写 commit + deploy

### Phase 4 (Day 42): Verify
- `python3 scripts/build/verify_chsi_integration.py` (新工具, 估 100 行)
- 检查 chsi_majors.json 是否在 public/data/manifest.json 中完整
- 部署后 Playwright 抓聚合页

---

## ⚠️ 风险 + 应对

| 风险 | 概率 | 应对 |
|------|------|------|
| **chsi 反爬升级** | 中 (15 天没动, 阿里云可能更新) | 备份 2024 + 试探 5 majors 才做全量 |
| **patchright 失效** | 中 | 回退到 curl + jina.ai proxy |
| **2025 招生数据延迟公布** | 高 (招生一般 7 月) | 接受 2024 数据为主, 2025 仅 preview |
| **专业代码变更** | 中 | 自动化 diff 报警, 人工审核新增专业 |

---

## 🔧 工具状态 (Day 14 已 ship)

`scripts/build/chsi_*.py` 包括:
- `chsi_fetch.py` (patchright 抓 majors + schools)
- `chsi_parse.py` (raw HTML → JSON)
- `chsi_merge.py` (3 文件合并 + 去重)

**Day 41+ 需检查**: 这些脚本是否仍能跑 (3 周没动)

---

## 📅 Day 40 收工检查

- [ ] `docs/PLAN_chsi_2025_integration.md` 已写 ✅ (本文)
- [ ] 当前 chsi 文件备份
- [ ] chsi_fetch.py 是否有 --year flag (待检查)
- [ ] chsi_fetch.py 仍能跑 (待 Day 41 验)

---

**生成时间**: 2026-06-29 (Day 40 Phase 4 prep)
**起点**: main `7c634654`, branch `fix/day40-variance-polish-chsi`
**起点 commit**: current registry 612 → 595 (after Day 40 phantom cleanup)
**Day 41+ 入口**: 跑 chsi_fetch.py 试探, 验证 patchright + 反爬状态
