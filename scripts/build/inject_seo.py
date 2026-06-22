#!/usr/bin/env python3
"""
scripts/inject_seo.py — 批量给 public/ 下的 HTML 注入 SEO 标签

注入内容:
  - <link rel="canonical" href="https://majorexplorer.com/{slug}.html">
  - <meta property="og:url" content="...">
  - <meta property="og:site_name" content="Major Explorer">
  - <meta property="og:title" content="...">  ← 复用 <title>
  - <meta property="og:description" content="...">  ← 复用 <meta name="description">
  - <meta property="og:type" content="article">

幂等: 已存在不重复添加。
"""
import re
import sys
from pathlib import Path

BASE_URL = "https://majorexplorer.com"
SITE_NAME = "Major Explorer"
PUBLIC_DIR = Path("public")

# 各种已有标签的检测 regex
DESCRIPTION_RE = re.compile(
    r'<meta\s+name="description"\s+content="([^"]*)"\s*>',
    re.IGNORECASE,
)
CANONICAL_RE = re.compile(r'<link\s+rel="canonical"[^>]*>', re.IGNORECASE)
OG_URL_RE = re.compile(r'<meta\s+property="og:url"[^>]*>', re.IGNORECASE)
OG_SITE_RE = re.compile(r'<meta\s+property="og:site_name"[^>]*>', re.IGNORECASE)
OG_TITLE_RE = re.compile(r'<meta\s+property="og:title"[^>]*>', re.IGNORECASE)
OG_DESC_RE = re.compile(r'<meta\s+property="og:description"[^>]*>', re.IGNORECASE)
OG_TYPE_RE = re.compile(r'<meta\s+property="og:type"[^>]*>', re.IGNORECASE)
TITLE_RE = re.compile(r'<title>([^<]+)</title>', re.IGNORECASE)


def inject_seo(html_path: Path) -> tuple[bool, str]:
    """注入 SEO 标签. 返回 (有改动, 状态消息)."""
    content = html_path.read_text(encoding="utf-8")
    slug = html_path.stem  # 去掉 .html

    # 1. 提取 title 和 description
    title_match = TITLE_RE.search(content)
    title = title_match.group(1).strip() if title_match else f"{slug} | {SITE_NAME}"

    desc_match = DESCRIPTION_RE.search(content)
    description = desc_match.group(1) if desc_match else ""

    # 2. 决定要注入哪些标签
    tags_to_add = []

    if not CANONICAL_RE.search(content):
        tags_to_add.append(f'  <link rel="canonical" href="{BASE_URL}/{slug}.html">')
    if not OG_URL_RE.search(content):
        tags_to_add.append(f'  <meta property="og:url" content="{BASE_URL}/{slug}.html">')
    if not OG_SITE_RE.search(content):
        tags_to_add.append(f'  <meta property="og:site_name" content="{SITE_NAME}">')
    if not OG_TITLE_RE.search(content):
        tags_to_add.append(f'  <meta property="og:title" content="{title}">')
    if not OG_DESC_RE.search(content) and description:
        tags_to_add.append(f'  <meta property="og:description" content="{description}">')
    if not OG_TYPE_RE.search(content):
        tags_to_add.append(f'  <meta property="og:type" content="article">')

    if not tags_to_add:
        return False, "skip (already has SEO)"

    # 3. 构造注入块
    inject_block = "\n  <!-- SEO: canonical + Open Graph -->\n" + "\n".join(tags_to_add) + "\n"

    # 4. 注入位置: <meta name="description"> 后
    if desc_match:
        # 在 <meta name="description" ...> 标签后插入
        insert_pos = desc_match.end()
        new_content = content[:insert_pos] + inject_block + content[insert_pos:]
    elif title_match:
        # 兜底: 在 </title> 后插入
        insert_pos = title_match.end()
        new_content = content[:insert_pos] + inject_block + content[insert_pos:]
    else:
        return False, "skip (no <title> or <meta name=\"description\">)"

    html_path.write_text(new_content, encoding="utf-8")
    return True, f"add {len(tags_to_add)} tags"


def main():
    html_files = sorted(PUBLIC_DIR.glob("*.html"))
    if not html_files:
        print("❌ No HTML files found in public/")
        sys.exit(1)

    changed = 0
    skipped = 0
    print(f"📝 扫描 {len(html_files)} 个 HTML 文件...\n")

    for f in html_files:
        ok, msg = inject_seo(f)
        marker = "✅" if ok else "⏭️ "
        print(f"  {marker} {f.name:40s} {msg}")
        if ok:
            changed += 1
        else:
            skipped += 1

    print(f"\n{'='*60}")
    print(f"✅ 改动: {changed} 个文件")
    print(f"⏭️  跳过: {skipped} 个文件 (已含 SEO 标签或无 title/desc)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
