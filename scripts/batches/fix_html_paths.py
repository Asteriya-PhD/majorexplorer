#!/usr/bin/env python3
"""
fix_html_paths.py — 把 HTML 里 `/js/...` 绝对路径改成相对 `../../js/...`.

根因: wishlist_inject.py:172-175 + 446-448 用绝对 /js/major-search.js 等.
  - 部署到 https:// 域名时 OK (Cloudflare Pages 根对应 /js/)
  - file:// 打开审稿时, 浏览器找 file:///js/major-search.js → 不存在 → ERR_FILE_NOT_FOUND

修法: 12 篇新精品在 skills/.../curated/ 下, 用相对路径 ../../js/... 找 public/js/
  - file://: ../../public/js/... ✓
  - https:// 部署时需 copy 到 public/ + 改回 /js/... (未来 deploy 脚本处理)

不动 wishlist_inject.py (60+ 老精品仍正常生产部署).
"""
import pathlib, re

CUR = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp/skills/gaokao-major-explorer/data/curated")
TARGETS = {
    "international-law", "economic-law", "criminal-law", "civil-law-jurisprudence",
    "commercial-law", "administrative-law", "civil-procedure", "criminal-procedure",
    "prison-studies", "drug-control", "criminology", "foreign-police",
}

# 匹配 src="/js/xxx" 和 href="/js/xxx"
PATTERN_SRC = re.compile(r'(src|href)="/js/([^"]+)"')


def fix(html: str) -> tuple[str, int]:
    count = 0
    def repl(m):
        nonlocal count
        count += 1
        return f'{m.group(1)}="../../js/{m.group(2)}"'
    new = PATTERN_SRC.sub(repl, html)
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
            print(f"  ✅ {slug:30s} 改 {c} 处 /js/ → ../../js/")
            total += c
    print(f"\n总计 {total} 处")


if __name__ == "__main__":
    main()