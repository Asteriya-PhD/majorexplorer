#!/usr/bin/env python3
"""
fix_data_count.py — 把 HTML 里 `<span data-count="X">0</span>` 改成 `<span data-count="X">X</span>`.

根因: base.py 用 IntersectionObserver 触发数字滚动动画, 初始 textContent=0.
       file:// 首屏看不到, 永远停在 0.
修法: 把 textContent 默认设成 data-count 真值, 动画仍然工作 (JS 从 X 滚到 X, 无视觉变化但功能完整).
      不动 base.py, 只 post-process 12 篇 HTML.
"""
import re, pathlib, sys, csv, argparse

CUR = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp/skills/gaokao-major-explorer/data/curated")
PATTERN = re.compile(r'(<span\s+data-count=")([\d.]+)(">)(0|0\.0+)(</span>)')
DEFAULT_TARGETS = [
    "international-law", "economic-law", "criminal-law", "civil-law-jurisprudence",
    "commercial-law", "administrative-law", "civil-procedure", "criminal-procedure",
    "prison-studies", "drug-control", "criminology", "foreign-police",
]


def fix_html(html: str) -> tuple[str, int]:
    """替换 textContent 为 data-count 真值. 返回 (new_html, count)."""
    count = 0

    def repl(m):
        nonlocal count
        count += 1
        return f'{m.group(1)}{m.group(2)}{m.group(3)}{m.group(2)}{m.group(5)}'

    new = PATTERN.sub(repl, html)
    return new, count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="CSV with slug,title,style (覆盖 DEFAULT_TARGETS)")
    ap.add_argument("--all", action="store_true", help="跑 curated/*.html 全部 (除 .bak)")
    args = ap.parse_args()
    if args.csv:
        targets = []
        with open(args.csv) as f:
            for row in csv.DictReader(f):
                if row.get("slug"):
                    targets.append(row["slug"])
    elif args.all:
        targets = sorted(p.stem for p in CUR.glob("*.html") if not p.stem.endswith(".bak"))
    else:
        targets = DEFAULT_TARGETS
    total = 0
    for slug in targets:
        p = CUR / f"{slug}.html"
        if not p.exists():
            print(f"  ⏭️  {slug}: html missing")
            continue
        html = p.read_text(encoding="utf-8")
        new, c = fix_html(html)
        if c > 0:
            p.write_text(new, encoding="utf-8")
            print(f"  ✅ {slug:32s} 修复 {c} 个 data-count")
            total += c
    print(f"\n总计修复 {total} 处")


if __name__ == "__main__":
    main()