#!/usr/bin/env python3
"""
render_all_bug3.py — Day 5 Bug 3 修复专用: 批量 re-render 全部 majors

读 public/data/manifest.json → 遍历 majors → 调 render_v4 (或 v4_medicine) →
写 skills/gaokao-major-explorer/data/curated/<slug>.html (源)
然后调用 deploy_to_public.py 同步到 public/<slug>.html (部署镜像)

✅ 3 层修复 (2026-06-18):
  - 修 _WL_MANIFEST 路径: curated/ → public/data/ (新 365 majors 包含 Day 5)
  - 加 fallback: _pick_related 返回 [] 时仍渲染最小 section
  - 加 footer-nav: 4 个跳转 (majors.html / wishlist / preferences / #majors)

用法:
  python3 scripts/render_all_bug3.py            # 全部 365
  python3 scripts/render_all_bug3.py --limit 10 # 测前 10 篇
  python3 scripts/render_all_bug3.py --slugs acting radiation-medicine
  python3 scripts/render_all_bug3.py --workers 4 --batch-size 30

性能 (实测):
  - 串行: ~2.5s/major × 365 = ~15min
  - 4 worker (multiprocessing): ~4min
"""
from __future__ import annotations
import argparse
import json
import multiprocessing as mp
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "public" / "data" / "manifest.json"
CURATED = ROOT / "skills" / "gaokao-major-explorer" / "curated" / "data" / "curated" if False else ROOT / "skills" / "gaokao-major-explorer" / "data" / "curated"
PUBLIC = ROOT / "public"


def _render_one(args: tuple[str, str]) -> tuple[str, bool, str]:
    """Worker: 渲染 1 篇 major. 返 (slug, ok, msg)."""
    slug, style = args
    json_path = CURATED / f"{slug}.json"
    if not json_path.exists():
        return (slug, False, f"json not found: {json_path}")
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        # import 必须放 worker 内 (multiprocessing spawn 模式)
        sys.path.insert(0, str(ROOT / "skills" / "gaokao-major-explorer"))
        from scripts.v4_styles.render import render_v4
        from scripts.v4_medicine import render_v4_medicine

        if style == "medicine":
            html = render_v4_medicine(data)
        else:
            html = render_v4(data, style)

        # 写入 curated 源
        html_path = CURATED / f"{slug}.html"
        html_path.write_text(html, encoding="utf-8")

        # 验证 3 层
        l1 = '<section class="wl-related"' in html
        l2 = 'href="/majors.html"' in html
        l3 = any(h in html for h in ['href="/majors.html"', 'href="/wishlist.html"', 'href="/preferences.html"', 'href="/#majors"'])
        flags = f"L1={'✓' if l1 else '✗'} L2={'✓' if l2 else '✗'} L3={'✓' if l3 else '✗'}"
        return (slug, True, flags)
    except Exception as e:
        return (slug, False, f"{type(e).__name__}: {e}")


def deploy_all(slugs: list[str], dry_run: bool = False) -> tuple[int, int]:
    """调 deploy_to_public.py 同步到 public/. 返 (ok, fail)."""
    import subprocess
    ok, fail = 0, 0
    cmd = [
        "python3", str(ROOT / "scripts" / "deploy_to_public.py"),
        "--slugs", *slugs,
    ]
    if dry_run:
        cmd.append("--dry-run")
    print(f"  → deploy {len(slugs)} majors...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"  ❌ deploy failed: {result.stderr[-500:]}")
        return 0, len(slugs)
    print(f"  ✓ deploy stdout: {result.stdout.strip()[-200:]}")
    return len(slugs), 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="只 render 前 N 篇")
    ap.add_argument("--slugs", nargs="*", help="指定 slug 列表")
    ap.add_argument("--workers", type=int, default=4, help="并行 worker 数 (默认 4)")
    ap.add_argument("--skip-deploy", action="store_true", help="跳过 deploy 步骤")
    ap.add_argument("--skip-render", action="store_true", help="只 deploy")
    args = ap.parse_args()

    if not MANIFEST.exists():
        print(f"❌ manifest not found: {MANIFEST}")
        sys.exit(1)

    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)

    majors = manifest.get("majors", [])
    if args.slugs:
        # 过滤指定 slug
        wanted = set(args.slugs)
        majors = [m for m in majors if m["slug"] in wanted]
    elif args.limit:
        majors = majors[:args.limit]

    print(f"📋 Bug 3 fix: 准备 render {len(majors)} majors (workers={args.workers})")

    targets = [(m["slug"], m.get("style", "")) for m in majors]

    rendered_ok = []
    rendered_fail = []

    if not args.skip_render:
        t0 = time.time()
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(_render_one, t): t[0] for t in targets}
            for i, fut in enumerate(as_completed(futures), 1):
                slug, ok, msg = fut.result()
                if ok:
                    rendered_ok.append(slug)
                    if i % 20 == 0 or i == len(targets):
                        print(f"  [{i}/{len(targets)}] ✓ {slug:40s} {msg}")
                else:
                    rendered_fail.append((slug, msg))
                    print(f"  [{i}/{len(targets)}] ❌ {slug:40s} {msg}")
        elapsed = time.time() - t0
        print(f"\n📊 Render 统计: ✓ {len(rendered_ok)} / ❌ {len(rendered_fail)} / 用时 {elapsed:.1f}s")

    # Deploy
    if not args.skip_deploy and rendered_ok:
        print(f"\n🚀 Deploy {len(rendered_ok)} majors → public/")
        ok, fail = deploy_all(rendered_ok)
        print(f"📊 Deploy: ✓ {ok} / ❌ {fail}")

    if rendered_fail:
        print(f"\n⚠️ {len(rendered_fail)} 篇 fail:")
        for slug, msg in rendered_fail[:10]:
            print(f"  - {slug}: {msg}")


if __name__ == "__main__":
    main()