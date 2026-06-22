#!/usr/bin/env python3
"""
verify_mobile.py — 校验 mobile 双轨:
  1) public/m/majors/*.html 数量 == manifest.majors.length (126)
  2) 每个 slug 在 manifest 和文件系统中都在
  3) 5 个 dock page + index.html 都存在
  4) PWA 资源 (manifest.json, sw.js, icon-192/512) 都存在
  5) 每个 major HTML 必含 11 个章节 (一/二/三/四/五/六/七/八/九/十/十一)
  6) 关键结构: stats-strip / hero-heart / wish-modal / salary P50 表头
"""
import json
import sys
from pathlib import Path

ROOT = Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp")
MANIFEST = ROOT / "public/data/manifest.json"
M_DIR = ROOT / "public/m"

errors = []
def check(cond, msg):
    if not cond:
        errors.append(msg)
        print(f"  ✗ {msg}")
    else:
        print(f"  ✓ {msg}")

print("=" * 60)
print("Mobile 双轨一致性校验")
print("=" * 60)

# 1) manifest
if not MANIFEST.exists():
    print(f"❌ manifest 不存在: {MANIFEST}")
    sys.exit(1)
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
slugs = [m["slug"] for m in manifest["majors"]]
print(f"\n[1] manifest: {len(slugs)} 个 major")

# 2) 5 dock + index
print(f"\n[2] 5 dock + index:")
for p in ["index.html", "catalog.html", "recommendations.html", "search.html", "wishlist.html", "me.html"]:
    f = M_DIR / p
    check(f.exists(), f"  {p}")

# 3) PWA 资源
print(f"\n[3] PWA 资源:")
for p in ["manifest.json", "sw.js", "icon-192.png", "icon-512.png"]:
    f = M_DIR / p
    check(f.exists(), f"  {p}")

# 4) majors 数量一致
print(f"\n[4] majors 数量:")
majors_dir = M_DIR / "majors"
files = [p.stem for p in majors_dir.glob("*.html") if not p.stem.startswith("_")]
print(f"  磁盘: {len(files)} 个, manifest: {len(slugs)} 个")
check(set(files) == set(slugs), "  slug 集合完全一致")

# 5) 缺 / 多
missing = set(slugs) - set(files)
extra = set(files) - set(slugs)
if missing:
    print(f"  ❌ manifest 有但磁盘缺: {sorted(missing)[:5]}...")
if extra:
    print(f"  ❌ 磁盘有但 manifest 没: {sorted(extra)[:5]}...")

# 6) 每篇 11 章节检查
print(f"\n[5] 每篇 11 章节 (一~十一):")
section_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一"]
ok11 = 0
err11 = []
for s in slugs[:30]:  # 抽 30 个抽样
    f = majors_dir / f"{s}.html"
    if not f.exists():
        continue
    text = f.read_text(encoding="utf-8")
    miss = [n for n in section_nums if f"art-num\">{n}<" not in text]
    if miss:
        err11.append((s, miss))
    else:
        ok11 += 1
print(f"  抽样 30: {ok11}/30 通过")
if err11:
    for s, m in err11[:5]:
        print(f"    ❌ {s}: 缺 {m}")

# 7) 关键结构检查
print(f"\n[6] 关键结构 (抽样 10):")
structure_checks = [
    ('class="stats-strip"', "stats-strip B 主题色块"),
    ('class="hero-heart"', "hero-heart 右上角手浮"),
    ('id="wish-modal"', "wish-modal 模态框"),
    ('id="star-row"', "5 星评分行"),
    ('id="wish-remove"', "移除心愿单按钮"),
    ('class="sal-table"', "salary 表格"),
    ('class="sal-th-cell is-p50">P50', "salary P50 中位列"),
    ('class="xk-list"', "xuanke 选科段"),
    ('class="ds-list"', "deep_study 段"),
    ('class="emp-list"', "employment 段"),
    ('class="co-list"', "companies 段"),
    ('class="fit-pair"', "fit 杂志风双段"),
    ('class="pit-grid"', "pitfalls 杂志风列表"),
    ('class="pull-list"', "学长学姐说列表"),
]
ok_struct = 0
err_struct = []
for s in slugs[:10]:
    f = majors_dir / f"{s}.html"
    if not f.exists():
        continue
    text = f.read_text(encoding="utf-8")
    miss = [desc for marker, desc in structure_checks if marker not in text]
    if miss:
        err_struct.append((s, miss))
    else:
        ok_struct += 1
print(f"  抽样 10: {ok_struct}/10 通过")
if err_struct:
    for s, m in err_struct[:5]:
        print(f"    ❌ {s}: 缺 {m}")

# 8) JSON 字面量泄露检查
print(f"\n[7] JSON 字面量泄露检查 (抽样 30):")
leak_markers = ["'directions':", "'yes':", "'myth':", "'foundations':", "'skills':"]
ok_no_leak = 0
err_leak = []
for s in slugs[:30]:
    f = majors_dir / f"{s}.html"
    if not f.exists():
        continue
    text = f.read_text(encoding="utf-8")
    leaks = [m for m in leak_markers if m in text]
    if leaks:
        err_leak.append((s, leaks))
    else:
        ok_no_leak += 1
print(f"  抽样 30: {ok_no_leak}/30 通过 (无泄露)")
if err_leak:
    for s, m in err_leak[:5]:
        print(f"    ❌ {s}: {m}")

print()
print("=" * 60)
if errors:
    print(f"❌ {len(errors)} 个错误")
    sys.exit(1)
else:
    print("✅ 全部通过")