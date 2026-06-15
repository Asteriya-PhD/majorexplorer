#!/usr/bin/env python3
"""
deploy_to_public.py — 把 skills/...curated/*.html 同步到 public/*.html (CF Pages 部署版).

为啥需要这个脚本:
  - skills/.../curated/ = **源**, render.py 直接输出, 路径用 ../../js/ (本地 file:// 审稿能加载 js)
  - public/*.html      = **部署镜像**, CF Pages 直接 serve, 路径用 /js/ (浏览器从根 / 加载)
  - 两套不是 "重复", 是不同 deploy target. 路径规则不同必须分开.

操作:
  1. 遍历 skills/.../curated/*.html (排除 .bak)
  2. 路径替换: `(src|href)="../../js/...` → `(src|href)="/js/...`
  3. 路径替换: `(src|href)="../../css/...` → `(src|href)="/css/...`  (如果有)
  4. 写到 public/<basename>.html

用法:
  python3 scripts/deploy_to_public.py                # 同步全部 (skills 多于 public 时安全)
  python3 scripts/deploy_to_public.py --csv path.csv # 只同步 CSV 列的 slug
  python3 scripts/deploy_to_public.py --slugs a b c  # 单跑几个
  python3 scripts/deploy_to_public.py --dry-run      # 只看会改啥, 不写

═══════════════════════════════════════════════════════════════════
⚠️  Mobile 双轨 (2026-06-15+):  /m/ 路径独立, 跟本脚本无关.
    mobile 渲染走  python3 scripts/render_mobile.py  →  public/m/
    校验走  python3 scripts/verify_mobile.py
═══════════════════════════════════════════════════════════════════
"""
import argparse, csv, pathlib, re, sys

ROOT = pathlib.Path("/Users/zhewenliu/Claude/gaokao-hubei-mvp")
SRC = ROOT / "skills/gaokao-major-explorer/data/curated"
DST = ROOT / "public"

# 反转 fix_html_paths.py: 部署版回到绝对路径
PATTERN = re.compile(r'(src|href)="\.\./\.\./((?:js|css)/[^"]+)"')


def transform(html: str) -> tuple[str, int]:
    count = 0
    def repl(m):
        nonlocal count
        count += 1
        return f'{m.group(1)}="/{m.group(2)}"'
    new = PATTERN.sub(repl, html)
    return new, count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="CSV with slug,title,style (only sync listed slugs)")
    ap.add_argument("--slugs", nargs="*", help="单跑 slug 列表")
    ap.add_argument("--dry-run", action="store_true", help="只看不写")
    args = ap.parse_args()

    if args.csv:
        targets = set()
        with open(args.csv) as f:
            for row in csv.DictReader(f):
                if row.get("slug"):
                    targets.add(row["slug"])
    elif args.slugs:
        targets = set(args.slugs)
    else:
        targets = {p.stem for p in SRC.glob("*.html") if not p.stem.endswith(".bak")}

    print(f"📦 准备同步 {len(targets)} 篇 skills → public  (dry-run={args.dry_run})")

    total_synced, total_paths, total_skipped, total_identical = 0, 0, 0, 0
    for slug in sorted(targets):
        src = SRC / f"{slug}.html"
        dst = DST / f"{slug}.html"
        if not src.exists():
            print(f"  ⏭️  {slug}: skills 源缺失")
            total_skipped += 1
            continue
        src_html = src.read_text(encoding="utf-8")
        new_html, path_n = transform(src_html)
        # 同 vs 不同
        if dst.exists():
            dst_html = dst.read_text(encoding="utf-8")
            if dst_html == new_html:
                total_identical += 1
                continue  # 无需同步
        # 写
        if not args.dry_run:
            dst.write_text(new_html, encoding="utf-8")
        size = len(new_html)
        print(f"  ✅ {slug:32s} {size:>7d} B, 路径替换 {path_n} 处")
        total_synced += 1
        total_paths += path_n

    print()
    print(f"汇总: 同步 {total_synced} 篇 ({total_paths} 处路径替换) / 已同 {total_identical} / 跳 {total_skipped}")
    if args.dry_run:
        print("⚠️  dry-run 模式, public/ 未写入")


if __name__ == "__main__":
    main()
