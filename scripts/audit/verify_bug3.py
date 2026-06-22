#!/usr/bin/env python3
"""
verify_bug3.py — Day 5 Bug 3 3 层验证 (2026-06-18)

用法:
  python3 scripts/verify_bug3.py                    # 验证 public/ (部署镜像, CF Pages serve)
  python3 scripts/verify_bug3.py --source           # 验证 skills/curated/ (源, render 输出)
  python3 scripts/verify_bug3.py --fix              # 验证 + 自动 deploy 缺失的
  python3 scripts/verify_bug3.py --csv report.csv   # 输出报告

3 层检查:
  L1: <section class="wl-related"> 存在 (心-愿单 + 12 主题卡 + 兜底 nav)
  L2: href="/majors.html" 存在 (硬链返回专业目录)
  L3: 至少 1 个 nav 链接 (防"页面结束就死胡同"回归)

目标: 全部 365 篇 100% 3 层通过.
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST = ROOT / "public" / "data" / "manifest.json"
CURATED = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"
PUBLIC = ROOT / "public"

L1 = '<section class="wl-related"'
L1_DECIDE = '<section class="wl-decide"'  # wl-related 配对 (心跳主 CTA)
L2_HARD = 'href="/majors.html"'
L3_NAVS = ['href="/majors.html"', 'href="/wishlist.html"', 'href="/preferences.html"', 'href="/#majors"']


def check_one(html_path: Path) -> dict:
    """Return {'slug', 'l1', 'l2', 'l3', 'issues'}"""
    slug = html_path.stem
    if not html_path.exists():
        return {"slug": slug, "exists": False, "l1": False, "l2": False, "l3": False, "issues": ["MISSING_FILE"]}
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    l1 = L1 in text
    l2 = L2_HARD in text
    l3 = any(h in text for h in L3_NAVS)
    issues = []
    if not l1:
        issues.append("L1_FAIL: wl-related section missing")
    if not l2:
        issues.append("L2_FAIL: /majors.html hardlink missing")
    if not l3:
        issues.append("L3_FAIL: no nav link (dead-end)")
    return {"slug": slug, "exists": True, "l1": l1, "l2": l2, "l3": l3, "issues": issues, "size": len(text)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", action="store_true", help="验证 skills/.../curated/ (源)")
    ap.add_argument("--fix", action="store_true", help="自动 deploy 缺失的 (调 deploy_to_public.py)")
    ap.add_argument("--csv", help="报告写到 csv")
    args = ap.parse_args()

    base = CURATED if args.source else PUBLIC
    target_label = "curated (源)" if args.source else "public (部署)"
    print(f"🔍 验证 {target_label}: {base}")
    print(f"   L1: <section class=\"wl-related\">  (Bug 3 主修复)")
    print(f"   L2: href=\"/majors.html\"  (硬链返回专业目录)")
    print(f"   L3: ≥1 个 nav 链接  (防死胡同)")
    print()

    # 加载 manifest, 拿全部 slug
    if not MANIFEST.exists():
        print(f"❌ manifest 不存在: {MANIFEST}")
        sys.exit(1)
    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)
    majors = manifest.get("majors", [])
    print(f"📋 manifest 共 {len(majors)} majors")

    # 验证
    results = []
    missing_files = []
    for m in majors:
        slug = m["slug"]
        r = check_one(base / f"{slug}.html")
        r["style"] = m.get("style", "")
        r["title"] = m.get("title", "")
        results.append(r)
        if not r["exists"]:
            missing_files.append(slug)

    total = len(results)
    l1_pass = sum(1 for r in results if r.get("l1"))
    l2_pass = sum(1 for r in results if r.get("l2"))
    l3_pass = sum(1 for r in results if r.get("l3"))
    all_pass = sum(1 for r in results if r.get("l1") and r.get("l2") and r.get("l3"))

    print()
    print("=" * 60)
    print(f"📊 验证结果 ({target_label}):")
    print(f"   L1 (wl-related section):   {l1_pass:4d}/{total}  ({l1_pass/total*100:.1f}%)")
    print(f"   L2 (/majors.html hard):    {l2_pass:4d}/{total}  ({l2_pass/total*100:.1f}%)")
    print(f"   L3 (≥1 nav 链接):           {l3_pass:4d}/{total}  ({l3_pass/total*100:.1f}%)")
    print(f"   3 层全通过:                  {all_pass:4d}/{total}  ({all_pass/total*100:.1f}%)")
    if missing_files:
        print(f"\n⚠️ {len(missing_files)} 篇 HTML 文件缺失:")
        for s in missing_files[:10]:
            print(f"   - {s}")

    # 列失败篇
    fails = [r for r in results if r.get("issues")]
    if fails:
        print(f"\n⚠️ {len(fails)} 篇 3 层失败 (前 20):")
        for r in fails[:20]:
            print(f"   - {r['slug']:40s} {' / '.join(r['issues'])}")

    # CSV 报告
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["slug", "style", "title", "exists", "l1", "l2", "l3", "size", "issues"])
            w.writeheader()
            for r in results:
                w.writerow({k: (";".join(r[k]) if k == "issues" and isinstance(r[k], list) else r.get(k, "")) for k in w.fieldnames})
        print(f"\n📄 报告写到: {args.csv}")

    # 0/3 全失败 = exit 1
    if all_pass < total:
        sys.exit(1)
    print(f"\n✅ Bug 3 3 层验证 100% 通过 ({total}/{total})")


if __name__ == "__main__":
    main()