#!/usr/bin/env python3
"""
regenerate_all.py — 重渲染 manifest 内所有专业 HTML.

读 skills/gaokao-major-explorer/data/curated/manifest.json,
对 majors[] 中每条 record:
  - 加载 curated/<slug>.json
  - 跑 generate_dashboard(data, style)
  - 写两份:
      skills/.../data/curated/<slug>.html   (原产物)
      public/<slug>.html                     (站点根)

并行 (multiprocessing) 加速。
"""
import json
import sys
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "gaokao-major-explorer"
sys.path.insert(0, str(SKILL_DIR / "scripts"))

MANIFEST_PATH = SKILL_DIR / "data" / "curated" / "manifest.json"
CURATED_DIR = SKILL_DIR / "data" / "curated"
PUBLIC_DIR = ROOT / "public"


def _render_one(rec: dict) -> tuple[str, int, str | None]:
    """子进程内执行: 加载 data JSON → 渲染 → 写 2 处 → 返回 (slug, bytes, error?)"""
    from generate_dashboard import generate_dashboard
    slug = rec["slug"]
    style = rec["style"]
    data_path = SKILL_DIR / rec["data_path"]
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
        # 防 slug 不在 data: 注入
        data.setdefault("slug", slug)
        data.setdefault("style", style)
        html = generate_dashboard(data, style, output_path=None)
        # 写两处
        curated_out = CURATED_DIR / f"{slug}.html"
        public_out = PUBLIC_DIR / f"{slug}.html"
        PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
        curated_out.write_text(html, encoding="utf-8")
        public_out.write_text(html, encoding="utf-8")
        return (slug, len(html), None)
    except Exception as e:
        return (slug, 0, f"{type(e).__name__}: {e}")


def main():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    majors = manifest.get("majors", [])
    print(f"=== regenerate_all: {len(majors)} majors ===")
    t0 = time.time()
    results = []
    # 并行 (8 workers); 子进程更稳, 单专业 ~50-200 ms
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(_render_one, m) for m in majors]
        for f in as_completed(futs):
            slug, size, err = f.result()
            if err:
                print(f"  ❌ {slug:40} {err}")
            else:
                print(f"  ✅ {slug:40} {size:>8,} bytes")
            results.append((slug, size, err))

    elapsed = time.time() - t0
    ok = sum(1 for _, _, e in results if not e)
    fail = sum(1 for _, _, e in results if e)
    print(f"\n=== done: {ok} ok / {fail} fail in {elapsed:.1f}s ===")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
