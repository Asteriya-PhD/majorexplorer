#!/usr/bin/env python3
"""
fix_fade_up.py — 给 12 篇 HTML 所有 .fade-up 元素加 .visible class,
                  让首屏 / 视口外元素立即可见, 不再依赖 IntersectionObserver.

不动 base.py, 避免破坏 60+ 精品 HTML.
"""
import pathlib

CUR = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp/skills/gaokao-major-explorer/data/curated")
TARGETS = {
    "international-law", "economic-law", "criminal-law", "civil-law-jurisprudence",
    "commercial-law", "administrative-law", "civil-procedure", "criminal-procedure",
    "prison-studies", "drug-control", "criminology", "foreign-police",
}


def fix(html: str) -> tuple[str, int]:
    """class="X fade-up" → class="X fade-up visible"  (X 可空)"""
    count = 0

    def repl(m):
        nonlocal count
        count += 1
        pre = m.group(1)
        return f'class="{pre}fade-up visible"'

    # 匹配 class="..." 含 fade-up
    import re
    new = re.sub(r'class="([^"]*?fade-up)"', repl, html)
    return new, count


def main():
    total = 0
    for slug in TARGETS:
        p = CUR / f"{slug}.html"
        if not p.exists():
            print(f"  ⏭️  {slug}: missing")
            continue
        h = p.read_text(encoding="utf-8")
        new, c = fix(h)
        if c > 0:
            p.write_text(new, encoding="utf-8")
            print(f"  ✅ {slug:30s} 加 visible {c} 处")
            total += c
    print(f"\n总计 {total} 处 fade-up 立即可见")


if __name__ == "__main__":
    main()