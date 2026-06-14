#!/usr/bin/env python3
"""
渲染 batch CSV/JSON list -> HTML.

用法:
  python3 scripts/batches/render_batch.py <slug,style> [<slug,style> ...]
  python3 scripts/batches/render_batch.py --csv scripts/batches/law_gongan_v1.csv
"""
import sys, json, csv, argparse, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills/gaokao-major-explorer/scripts"))

from generate_dashboard import generate_dashboard  # noqa: E402

CUR = ROOT / "skills/gaokao-major-explorer/data/curated"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="CSV with slug,title,style")
    ap.add_argument("--slugs", nargs="*", help="slug:style pairs (e.g. law:law gongan:law)")
    args = ap.parse_args()

    pairs = []
    if args.csv:
        with open(args.csv) as f:
            for row in csv.DictReader(f):
                pairs.append((row["slug"], row["style"]))
    if args.slugs:
        for s in args.slugs:
            slug, _, style = s.partition(":")
            if not style:
                style = json.loads((CUR / f"{slug}.json").read_text()).get("style", "cs")
            pairs.append((slug, style))

    if not pairs:
        print("❌ no input")
        return

    print(f"🎨 准备渲染 {len(pairs)} 篇")
    ok, fail = [], []
    for slug, style in pairs:
        jp = CUR / f"{slug}.json"
        hp = CUR / f"{slug}.html"
        if not jp.exists():
            print(f"  ⏭️  {slug}: json 不存在, 跳过")
            continue
        try:
            data = json.loads(jp.read_text())
            html = generate_dashboard(data, style, str(hp))
            print(f"  ✅ {slug:30s} style={style:8s} {len(html):,} bytes")
            ok.append(slug)
        except Exception as e:
            print(f"  ❌ {slug}: {type(e).__name__}: {e}")
            fail.append((slug, str(e)))
    print(f"\n完成: {len(ok)}/{len(pairs)} 渲染成功")
    if fail:
        print("失败:")
        for s, e in fail:
            print(f"  ❌ {s}: {e}")


if __name__ == "__main__":
    main()