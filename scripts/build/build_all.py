#!/usr/bin/env python3
"""
build_all.py — 一键跑全部 build step, 任何新增 major commit 后必跑

顺序:
  1. build_aggregates.py    ← 从 manifest.json 聚合统计
  2. inject_aggregates_meta ← 把数字注入 majors.html / index.html (meta description + lede)
  3. inject_seo.py          ← (可选) SEO tags, 已注入则 noop

用法:
  python3 scripts/build/build_all.py
  python3 scripts/build/build_all.py --skip-seo

效果: 任何 manifest.json 改动 → 跑这条 → aggregates.json + HTML 自动同步
      git commit 时由 pre-commit hook 自动触发 (见 .githooks/pre-commit)
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "build"


def run(cmd: list[str], desc: str) -> None:
    print(f"\n=== {desc} ===")
    print(f"  $ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"❌ {desc} 失败 (exit {r.returncode})")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--skip-seo", action="store_true", help="跳过 inject_seo.py (默认跑)")
    p.add_argument("--skip-aggregates-check", action="store_true",
                   help="跳过 build_aggregates.py 末段 --check (CI 不用)")
    args = p.parse_args()

    # 1. 聚合 (写 aggregates.json)
    run(["python3", str(SCRIPTS / "build_aggregates.py")], "build_aggregates.py")
    if not args.skip_aggregates_check:
        run(["python3", str(SCRIPTS / "build_aggregates.py"), "--check"],
            "build_aggregates.py --check")

    # 2. 注入 meta description / lede 到 HTML
    run(["python3", str(SCRIPTS / "inject_aggregates_meta.py")],
        "inject_aggregates_meta.py")

    # 3. inject_seo (幂等, 已注入 skip)
    if not args.skip_seo:
        run(["python3", str(SCRIPTS / "inject_seo.py")], "inject_seo.py")

    print("\n✅ build_all 完成. 下一步:")
    print("   git add public/data/aggregates.json public/majors.html public/index.html")
    print("   git commit -m 'fix(aggregates): rebuild stats after major batch'")


if __name__ == "__main__":
    main()
