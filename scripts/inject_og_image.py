#!/usr/bin/env python3
"""
scripts/inject_og_image.py — 给 public/ 下所有 HTML 注入 og:image 标签

注入: <meta property="og:image" content="https://majorexplorer.com/og-image.png">
注入位置: 在已有 og:title 后 (或 og:url 后)
幂等: 已存在不重复添加
"""
import re
import sys
from pathlib import Path

BASE_URL = "https://majorexplorer.com"
OG_IMAGE = f"{BASE_URL}/og-image.png"
PUBLIC_DIR = Path("public")

# 各种已有 og 标签检测
OG_IMAGE_RE = re.compile(r'<meta\s+property="og:image"[^>]*>', re.IGNORECASE)
OG_TITLE_RE = re.compile(r'<meta\s+property="og:title"[^>]*>', re.IGNORECASE)
OG_URL_RE = re.compile(r'<meta\s+property="og:url"[^>]*>', re.IGNORECASE)


def inject(html_path: Path) -> tuple[bool, str]:
    content = html_path.read_text(encoding="utf-8")
    slug = html_path.stem

    # 幂等检查
    if OG_IMAGE_RE.search(content):
        return False, "skip (already has og:image)"

    # 构造 og:image 标签
    og_image_tag = f'  <meta property="og:image" content="{OG_IMAGE}">'
    inject_block = f"\n  <!-- OG image for social sharing -->\n{og_image_tag}\n"

    # 注入位置: 在 og:title 后 (优先) 或 og:url 后 (兜底)
    if OG_TITLE_RE.search(content):
        # 在 og:title 标签后插入
        match = OG_TITLE_RE.search(content)
        insert_pos = match.end()
    elif OG_URL_RE.search(content):
        match = OG_URL_RE.search(content)
        insert_pos = match.end()
    else:
        return False, "skip (no og:title or og:url found)"

    new_content = content[:insert_pos] + inject_block + content[insert_pos:]
    html_path.write_text(new_content, encoding="utf-8")
    return True, f"add og:image ({OG_IMAGE})"


def main():
    html_files = sorted(PUBLIC_DIR.glob("*.html"))
    if not html_files:
        print("❌ No HTML files found in public/")
        sys.exit(1)

    # 朋友圈/微信分享只抓分享 URL 的 HTML (默认是 majorexplorer.com/)
    # → 只对 index.html 注入 og:image, 70 个 major HTML 不动
    changed = 0
    skipped = 0
    print(f"📝 注入 og:image 到 index.html (朋友圈分享只抓主页)\n")

    for f in html_files:
        if f.stem != "index":
            skipped += 1
            continue
        ok, msg = inject(f)
        marker = "✅" if ok else "⏭️ "
        print(f"  {marker} {f.name:40s} {msg}")
        if ok:
            changed += 1
        else:
            skipped += 1

    print(f"\n{'='*60}")
    print(f"✅ 改动: {changed} 个文件 (index.html)")
    print(f"⏭️  跳过: {skipped} 个文件 (70 个 major, 朋友圈分享用不到)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
