#!/usr/bin/env python3
"""inject_share.py — 全量注入分享 FAB + 修移动端死代码 + 引入 share.js

Step 1 (Mobile, 628 页):
  - 修 <a class="top-btn" href="javascript:navigator.share?..."> →
           <button class="top-btn" data-share-trigger aria-label="分享">↗</button>
  - </body> 前注入 <button class="share-fab" data-share-trigger ...>↗</button>
  - </body> 前注入 <script src="../js/share.js" defer></script>

Step 2 (PC, 648 页):
  - </body> 前注入 <button class="share-fab" data-share-trigger ...>↗</button>
  - </body> 前注入 <script src="/js/share.js" defer></script>

幂等: 已注入的不会重复 (用 data-share-trigger 标记)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

# ── Mobile: 修死代码 + 注入 ──
MOBILE_TOPBTN_OLD = re.compile(
    r'<a class="top-btn" href="javascript:navigator\.share\?navigator\.share\(\{title:document\.title\}\):void\(0\)" aria-label="分享">↗</a>'
)
MOBILE_TOPBTN_NEW = '<button type="button" class="top-btn" data-share-trigger aria-label="分享">↗</button>'

MOBILE_FAB_AND_SCRIPT = (
    '\n\n<!-- 分享 FAB + 长图导出 (Day 35 share 注入) -->\n'
    '<button type="button" class="share-fab" data-share-trigger aria-label="分享">↗</button>\n'
    '<link rel="stylesheet" href="../css/share.css">\n'
    '<script src="../js/share.js" defer></script>\n'
)

# ── PC: 注入 ──
PC_FAB_AND_SCRIPT = (
    '\n\n<!-- 分享 FAB + 长图导出 (Day 35 share 注入) -->\n'
    '<button type="button" class="share-fab" data-share-trigger aria-label="分享">↗</button>\n'
    '<link rel="stylesheet" href="/css/share.css">\n'
    '<script src="/js/share.js" defer></script>\n'
)

def inject_mobile(html: str) -> tuple[str, int]:
    """返回 (新HTML, 修改数)"""
    n = 0
    # 1) 修死代码
    new_html, c1 = MOBILE_TOPBTN_OLD.subn(MOBILE_TOPBTN_NEW, html)
    n += c1
    # 2) 幂等: 已注入则跳过
    if 'data-share-trigger' in new_html and '/js/share.js' in new_html:
        return new_html, n
    # 3) 注入 FAB + script (</body> 前)
    if '</body>' in new_html:
        new_html = new_html.replace('</body>', MOBILE_FAB_AND_SCRIPT + '</body>', 1)
        n += 1
    return new_html, n

def inject_pc(html: str) -> tuple[str, int]:
    """PC: 没有死代码, 只注入 FAB + script"""
    n = 0
    if 'data-share-trigger' in html and '/js/share.js' in html:
        return html, 0
    if '</body>' in html:
        html = html.replace('</body>', PC_FAB_AND_SCRIPT + '</body>', 1)
        n += 1
    return html, n

def run(dry: bool = False):
    mobile_dir = PUBLIC / "m" / "majors"
    mobile_files = sorted(mobile_dir.glob("*.html"))
    pc_files = sorted([f for f in PUBLIC.glob("*.html") if f.is_file()])

    print(f"📱 Mobile pages: {len(mobile_files)}")
    print(f"💻 PC pages:     {len(pc_files)}")
    print()

    total_modified = 0
    total_fixes = 0
    total_injects = 0

    if not dry:
        # Mobile
        for f in mobile_files:
            html = f.read_text(encoding="utf-8")
            new_html, n = inject_mobile(html)
            if n > 0:
                f.write_text(new_html, encoding="utf-8")
                total_modified += 1
                total_fixes += 1 if MOBILE_TOPBTN_OLD.search(html) else 0
                total_injects += 1 if '</body>' in html and 'data-share-trigger' not in html else 0
        # PC
        for f in pc_files:
            html = f.read_text(encoding="utf-8")
            new_html, n = inject_pc(html)
            if n > 0:
                f.write_text(new_html, encoding="utf-8")
                total_modified += 1
                total_injects += 1

    print(f"✅ Modified:     {total_modified} files")
    print(f"🔧 Bug fixes:    {total_fixes} (mobile share 死代码)")
    print(f"💉 Injections:   {total_injects} (FAB + share.js)")
    return total_modified


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    if dry:
        print("🧪 DRY RUN — no files written")
    run(dry=dry)