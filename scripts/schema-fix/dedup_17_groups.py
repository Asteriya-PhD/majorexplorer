#!/usr/bin/env python3
"""
dedup_17_groups.py — Day 13.5 重复专业去重

17 title 重复组, 删 17 低分/污染 slug, 留 17 高分 slug.
被删 slug 的 HTML 替换为 canonical redirect 页面 (避免 404 + SEO 友好).

用法:
  python3 scripts/dedup_17_groups.py --dry-run   # 预览, 不改文件
  python3 scripts/dedup_17_groups.py              # 真跑

写入:
  - public/data/manifest.json          (移除 17 条)
  - data/audit_registry.json           (移除 17 条)
  - skills/gaokao-major-explorer/data/curated/{slug}.json   (DELETE)
  - public/{slug}.html                 (替换为 redirect HTML, 指向 KEEP slug)
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
MANIFEST = ROOT / "public" / "data" / "manifest.json"
REGISTRY = ROOT / "data" / "audit_registry.json"
CURATED = ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"
PUBLIC_HTML = ROOT / "public"

# 17 组 keep 决策表
DEDUP_PAIRS = [
    # (title, KEEP slug, DELETE slug)
    ("网络空间安全", "network-space-security", "cybersecurity"),
    ("智能交通工程", "intelligent-transportation", "intelligent-transportation-engineering-2"),
    ("智能感知工程", "smart-perception-engineering", "intelligent-perception-engineering"),
    ("工商管理", "business-administration", "business-administration-demo"),
    ("朝鲜语", "korean", "korean-language"),
    ("阿拉伯语", "arabic-language", "arabic"),
    ("蚕学", "sericulture", "silkworm-science"),
    ("植物保护", "plant-protection-science", "plant-protection"),
    ("海洋技术", "marine-technology", "xe9ho9v"),
    ("经济犯罪侦查", "economic-crime-investigation", "criminal-investigation-economics"),
    ("精算学", "actuarial-science", "actuarial-final"),
    ("集成电路设计与集成系统", "integrated-circuit-design", "integrated-circuit-design-systems-cross"),
    ("食品科学与工程", "food-science-engineering", "food-science-and-engineering"),
    ("艺术史论", "art-history", "art-history-theory"),
    ("医学检验技术", "medical-laboratory-science", "medical-laboratory-tech"),
    ("储能科学与工程", "energy-storage-science-engineering", "energy-storage-science-engineering-2"),
    ("翻译", "translation-final", "translation"),  # 翻译组, 第 2 个 delete 在 loop 2
]

# 翻译组有 3 个, translation-final 留, translation + translation-interpreting 都删
EXTRA_DELETES = ["translation-interpreting"]


def make_redirect_html(keep_slug: str, title: str) -> str:
    """生成 redirect HTML 页面: meta refresh + canonical link + JS fallback"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=/{keep_slug}.html">
<title>{title} → 已合并</title>
<link rel="canonical" href="/{keep_slug}.html">
<meta name="robots" content="noindex,follow">
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif;background:#f5f5f0;color:#3a3a3a;margin:0;padding:80px 20px;text-align:center;line-height:1.6}}
.box{{max-width:520px;margin:0 auto;background:#fff;padding:40px 32px;border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,.06)}}
h1{{font-size:22px;margin:0 0 16px;font-weight:600}}
p{{font-size:14px;color:#666;margin:8px 0}}
a{{color:#3a6b35;text-decoration:none;font-weight:500;border-bottom:1.5px solid currentColor}}
a:hover{{opacity:.75}}
.arrow{{font-size:24px;margin:12px 0;color:#999}}
</style>
</head>
<body>
<div class="box">
<h1>📚 {title}</h1>
<div class="arrow">↓</div>
<p>该专业已合并到统一版本</p>
<p><a href="/{keep_slug}.html">点击查看最新内容 →</a></p>
<p style="font-size:12px;color:#999;margin-top:24px">3 秒后自动跳转</p>
</div>
<script>setTimeout(function(){{window.location='/{keep_slug}.html'}},3000);</script>
</body>
</html>
"""


def main():
    dry_run = "--dry-run" in sys.argv

    delete_slugs = []
    for title, keep, delete in DEDUP_PAIRS:
        delete_slugs.append((title, keep, delete))
    for slug in EXTRA_DELETES:
        delete_slugs.append(("翻译", "translation-final", slug))

    print(f"{'[DRY-RUN] ' if dry_run else ''}Dedup 17 groups, {len(delete_slugs)} slugs to delete")
    print(f"{'='*70}")

    # 1. 加载 manifest + registry
    with open(MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open(REGISTRY, "r", encoding="utf-8") as f:
        registry = json.load(f)

    manifest_before = len(manifest["majors"])
    registry_before = len(registry["majors"])

    deleted_files = []
    kept_replaced = []

    for title, keep, delete in delete_slugs:
        # Verify keep slug exists
        keep_entry = next((m for m in manifest["majors"] if m["slug"] == keep), None)
        delete_entry = next((m for m in manifest["majors"] if m["slug"] == delete), None)

        if not keep_entry:
            print(f"⚠️  KEEP missing: {keep} (title={title})")
            continue
        if not delete_entry:
            print(f"⚠️  DELETE missing: {delete} (title={title})")
            continue

        print(f"  【{title}】 {delete} → {keep}")
        print(f"    manifest: {delete_entry['slug']} ({delete_entry.get('sub_discipline','')}) → REMOVE")

        if not dry_run:
            # 1. manifest: remove
            manifest["majors"] = [m for m in manifest["majors"] if m["slug"] != delete]

            # 2. registry: remove
            if delete in registry["majors"]:
                del registry["majors"][delete]

            # 3. curated JSON: delete
            json_path = CURATED / f"{delete}.json"
            if json_path.exists():
                json_path.unlink()
                deleted_files.append(str(json_path.relative_to(ROOT)))

            # 4. public HTML: replace with redirect
            html_path = PUBLIC_HTML / f"{delete}.html"
            if html_path.exists():
                redirect_html = make_redirect_html(keep, title)
                html_path.write_text(redirect_html, encoding="utf-8")
                kept_replaced.append(str(html_path.relative_to(ROOT)))

    # Update totals
    if not dry_run:
        manifest_after = len(manifest["majors"])
        registry_after = len(registry["majors"])
        # manifest 用 'total' (单数), 不是 'totals'
        manifest["total"] = manifest_after
        manifest["count"] = manifest_after
        from datetime import datetime
        manifest["updated_at"] = datetime.now().isoformat()

        # registry totals — 让 update_audit_registry.py --rebuild 完整重算, 这里只更新 majors 数
        registry["totals"]["majors"] = registry_after
        registry["updated_at"] = datetime.now().isoformat()

        # Save
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        with open(REGISTRY, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*70}")
    print(f"manifest: {manifest_before} → {len(manifest['majors']) if not dry_run else manifest_before - len(delete_slugs)} majors")
    print(f"registry: {registry_before} → {len(registry['majors']) if not dry_run else registry_before - len(delete_slugs)} entries")
    print(f"deleted files: {len(deleted_files)} JSON")
    print(f"replaced HTML: {len(kept_replaced)} (now redirect → keep slug)")

    if deleted_files:
        print(f"\nDeleted JSON files (first 5):")
        for f in deleted_files[:5]:
            print(f"  - {f}")
    if kept_replaced:
        print(f"\nReplaced HTML (first 5):")
        for f in kept_replaced[:5]:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
