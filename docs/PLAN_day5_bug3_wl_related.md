# Day 5 Bug 3 wl-related 修复 Plan — 重开后启动

> 写于 2026-06-18, Day 5 (Bug 1+2 + 5 篇 polish) 完工后.
> **目标**: 修 Bug 3 底部跳转缺失 — 170/338 majors 缺 wl-related, 100% 缺 /majors.html 返回链接.
> **重开后启动**: 1 主控 + render script 改 + 170 篇 re-render + verify.

---

## 📊 现状 (2026-06-18 排查)

| 项目 | 数量 |
|------|------|
| 总库 majors | 338 (337 curated + 1 demo) |
| 有 `.wl-related` CSS | 336/338 (99%) — design 残留 |
| 有 `<section class="wl-related">` body 渲染 | **168/338 (50%)** |
| 缺 wl-related body | **170/338 (50%)** |
| 有 `/majors.html` 返回链接 | **0/338 (0%)** |
| 有 `<footer>` 块 | 100% (但只有"权威数据源", 无跳转) |

### 缺 wl-related 的 170 篇分布

- **F-C 10 篇 (Agent C 100% 漏)**: acting / drama-film-directing / drama-film-art-design / film-photography-production / recording-arts / music-composition-theory / popular-music / cultural-relics-conservation-restoration / agriculture-resources-environment / veterinary-public-health
- **老 majors 160 篇**: 历史 design drift (half-half 状态)

---

## 🎯 修复目标

| 指标 | 目标 |
|------|------|
| wl-related body 渲染 | 338/338 (100%) |
| /majors.html 返回链接 | 338/338 (100%) |
| Footer 跳转 (返回主页/相关/心愿单) | 338/338 (100%) |

---

## 🛠️ 流水线 5 步

```
1. Render Script 实现 wl-related 模板
   - v4_styles/render.py: line ~1100 (footer 前) 加 wl-related body
   - v4_medicine.py: 同位置
   - 模板: 12 张同门类相关 major 卡 + 「返回 /majors.html」CTA

2. 数据查找逻辑
   - 读 data.style + data.category (e.g., arts + 戏剧与影视)
   - 找同 category 11 个其他 major (排除自己)
   - 按 mcount 倒序 / 学科评估排序

3. Re-render 全部 338 majors
   - python3 skills/gaokao-major-explorer/scripts/generate_dashboard.py --data ... --style ... --output ...
   - 4 worker 并行 × 85 majors ≈ 30 min

4. 部署 (手动 re.sub 绕过 ROOT bug)
   - 178 篇 → public/<slug>.html (相对路径 → /绝对)

5. 验证
   - 全部 338 HTML 检查 <section class="wl-related"> 存在
   - 全部 338 HTML 检查 <a href="/majors.html"> 存在
   - m3 audit 抽样 5 篇 (bug 1+2 已修 batch 中)
```

---

## 📂 已就绪文件 (重开后直接用)

- **170 篇待修 list**: 脚本生成 (见 §资源)
- **shared context**: `/tmp/day4-shared-context.md` (11 章节 SOP 复用)
- **PIPELINE**: `docs/PIPELINE_major_quality.md` (9 步流水线)
- **v4 render script**: `skills/gaokao-major-explorer/scripts/v4_styles/render.py` + `v4_medicine.py`

---

## ⏱️ 预期

- **Step 1 (改 render script)**: 30-45 min
- **Step 2-3 (re-render 338)**: 30 min (4 worker 并行)
- **Step 4 (部署)**: 10 min (re.sub 批量)
- **Step 5 (验证)**: 15 min
- **总耗时**: 1.5-2h
- **总成本**: ¥0 (无 LLM 介入, 纯模板 + 数据)

---

## 🔑 复用 Day 4+5 经验 (避免重复踩坑)

1. **deploy_to_public.py ROOT 写死** — 手动 re.sub 替代
2. **m3 audit "字段截断" display bug** — 不因此改
3. **m3 ±1 variance** — 7 临界点 6/10 接受度需用户拍板
4. **render script 维护 2 份** — v4_styles/render.py + v4_medicine.py 同步改
5. **CC 不自动 cd worktree** — 本次不用 worktree (改 1 文件 + re-render 338)

---

## 🚀 重开后启动步骤

```bash
# Step 1: 改 render script (主控)
# - v4_styles/render.py: line ~1100 加 wl-related body + 返回链接
# - v4_medicine.py: 同位置

# Step 2: 找同门类 related majors 逻辑
# - 读 data/style + data/category
# - 排序按 mcount/学科评估

# Step 3: 写 1 篇测试 (preventive-medicine, 已修)
# - re-render + deploy
# - Playwright 验证底部跳转

# Step 4: 批量 re-render 338 (4 worker 并行)
python3 scripts/render_all_338.py  # 待写

# Step 5: 批量 deploy
python3 scripts/deploy_all_338.py  # 待写

# Step 6: 验证
python3 scripts/verify_wl_related.py  # 待写

# Step 7: commit + push
git add ... && git commit -m "fix(content): Bug 3 wl-related + 底部跳转 100% 覆盖"
git push origin main
```

---

## 📊 Bug 3 完成后覆盖率

| 指标 | 之前 | 之后 |
|------|------|------|
| wl-related 渲染 | 168/338 (50%) | 338/338 (100%) |
| /majors.html 返回 | 0/338 (0%) | 338/338 (100%) |
| 完整底部导航 | 0/338 (0%) | 338/338 (100%) |

---

**Co-Authored-By**: Claude Opus 4.8 <noreply@anthropic.com>
