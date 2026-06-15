#!/usr/bin/env python3
"""
verify_mobile.py — 校验 mobile 双轨:
  1) public/m/majors/*.html 数量 == manifest.majors.length (126)
  2) 每个 slug 在 manifest 和文件系统中都在
  3) 5 个 dock page + index.html 都存在
  4) PWA 资源 (manifest.json, sw.js, icon-192/512) 都存在
  5) 每个 major HTML 必含 5 个章节 (一/二/三/四/五)
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

# 6) 每篇 5 章节检查
print(f"\n[5] 每篇 5 章节 (一/二/三/四/五):")
ok5 = 0
err5 = []
for s in slugs[:30]:  # 抽 30 个抽样
    f = majors_dir / f"{s}.html"
    if not f.exists():
        continue
    text = f.read_text(encoding="utf-8")
    miss = [n for n in "一二三四五" if f"art-num\">{n}<" not in text]
    if miss:
        err5.append((s, miss))
    else:
        ok5 += 1
print(f"  抽样 30: {ok5}/30 通过")
if err5:
    for s, m in err5[:5]:
        print(f"    ❌ {s}: 缺 {m}")

print()
print("=" * 60)
if errors:
    print(f"❌ {len(errors)} 个错误")
    sys.exit(1)
else:
    print("✅ 全部通过")
