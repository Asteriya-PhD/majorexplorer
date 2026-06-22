# Day 5 Bug 3 wl-related 修复 Plan — 重开后启动

> 写于 2026-06-18, Day 5 (Bug 1+2 + 5 篇 polish) 完工后.
> **目标**: 修 Bug 3 底部跳转缺失 — 170/338 majors 缺 wl-related, 100% 缺 /majors.html 返回链接.
> **重开后启动**: 1 主控 + render script 改 + 170 篇 re-render + verify.

---

## 📊 现状 (2026-06-18 排查, 3 层细化)

### Bug 3 分层

| 层级 | 问题 | 数量 | 严重度 | 备注 |
|------|------|------|--------|------|
| **L1** | `<section class="wl-related">` body 渲染缺失 | **170/338 (50%)** | 🟡 中 | 用户感知最强: "页面结束就死胡同" |
| **L2** | `href="/majors.html"` 硬链缺失 | **338/338 (100%)** | 🟢 低 | 多数有 `/#majors` 锚链替代 (回主页), 体验 OK 但路径绕 |
| **L3** | 完全无任何 nav 链接 (`/majors` `/wishlist` 都没有) | **~10-20/338 (估)** | 🔴 高 | 真死链, 用户看完页面无任何出口 |
| **CSS 残留** | `.wl-related` CSS 出现但无 body | 336/338 (99%) | - | design 残留, body 缺失才生效 |

### 5 个样本验证 (2026-06-18)

| Major | wl-related body | 返链 |
|-------|----------------|------|
| electronic-science-technology | ❌ 缺 | `/#majors` + `/wishlist.html` ✓ |
| environmental-ecological-engineering | ❌ 缺 | `/#majors` + `/wishlist.html` ✓ |
| applied-linguistics | ❌ 缺 | `/?discipline=05#majors` + `/?discipline=05&sub=0502#majors` + `/#majors` + `/wishlist.html` ✓✓ |
| radiation-medicine | ❌ 缺 | **❌ 完全无 nav (死链)** |
| intelligent-engineering-creative-design | ❌ 缺 | **❌ 完全无 nav (死链)** |

### 缺 wl-related 的 170 篇分布

- **F-C 10 篇 (Agent C 100% 漏)**: acting / drama-film-directing / drama-film-art-design / film-photography-production / recording-arts / music-composition-theory / popular-music / cultural-relics-conservation-restoration / agriculture-resources-environment / veterinary-public-health
- **老 majors 160 篇**: 历史 design drift (half-half 状态)

---

## 🎯 修复目标 (分层, L1+L3 必做, L2 选做)

| 指标 | 之前 | 之后 (L1+L3) | 之后 (L1+L2+L3) |
|------|------|---------------|-------------------|
| wl-related body 渲染 | 168/338 (50%) | 338/338 (100%) | 338/338 (100%) |
| /majors.html 直链 (L2) | 0/338 (0%) | 0/338 (0%) | 338/338 (100%) |
| 完全无 nav 链接 (L3) | ~10-20/338 (估) | **0/338 (0%)** | 0/338 (0%) |
| 至少 1 个返链 (L1+L3 覆盖) | 320/338 (95% 估) | 338/338 (100%) | 338/338 (100%) |

**L1+L3 必做**: 修底部"12 张相关 major 卡" + footer 加 "返回 /majors.html" 链 → 解决"页面结束就死胡同" + L3 死链
**L2 选做**: 把现有 `/#majors` 锚链统一升级为 `href="/majors.html"` 直链 (体验提升微, 可后置)

---

## 🛠️ 流水线 6 步 (L1+L3 必做, L2 选做)

```
1. Render Script 实现 wl-related 模板 (L1)
   - v4_styles/render.py: line ~1100 (footer 前) 加 wl-related body
   - v4_medicine.py: 同位置
   - 模板: 12 张同门类相关 major 卡 + 「返回 /majors.html」CTA + 「去心愿单」CTA

2. 数据查找逻辑
   - 读 data.style + data.category (e.g., arts + 戏剧与影视)
   - 找同 category 11 个其他 major (排除自己)
   - 按 mcount 倒序 / 学科评估排序
   - 不足 11 个就跨门类补 (e.g., 1304 美术学 跨到 1303 戏剧影视)

3. Footer 加 "返回 /majors.html" CTA (L3 必做 + L2 选做)
   - 现有 170 篇 缺 wl-related, footer 也无任何跳转
   - 改 render script: 统一在 footer 加 <a href="/majors.html">返回专业目录</a>
   - 同时保留 #majors 锚链 (双重保障)

4. Re-render 全部 338 majors
   - python3 skills/gaokao-major-explorer/scripts/generate_dashboard.py --data ... --style ... --output ...
   - 4 worker 并行 × 85 majors ≈ 30 min

5. 部署 (手动 re.sub 绕过 ROOT bug)
   - 178 篇 → public/<slug>.html (相对路径 → /绝对)

6. 验证 (3 层检查)
   - L1: 全部 338 HTML 检查 <section class="wl-related"> 存在
   - L2: 全部 338 HTML 检查 <a href="/majors.html"> 存在 (选做)
   - L3: 全部 338 HTML 检查 至少 1 个 nav link (防 L3 死链回归)
   - m3 audit 抽样 5 篇
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

## 📊 Bug 3 完成后覆盖率 (L1+L3 必做, L2 选做)

| 指标 | 之前 | 之后 (L1+L3) | 之后 (L1+L2+L3) |
|------|------|---------------|------------------|
| wl-related 渲染 (L1) | 168/338 (50%) | 338/338 (100%) | 338/338 (100%) |
| /majors.html 直链 (L2) | 0/338 (0%) | 0/338 (0%) | 338/338 (100%) |
| 完全无 nav 死链 (L3) | ~10-20/338 (估) | **0/338 (0%)** | 0/338 (0%) |
| 至少 1 个返链 | 320/338 (95% 估) | 338/338 (100%) | 338/338 (100%) |

---

**Co-Authored-By**: Claude Opus 4.8 <noreply@anthropic.com>
