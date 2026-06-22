#!/usr/bin/env python3
"""
Inject <link rel="manifest" href="/manifest.json"> into all PC HTML files.

- Iterates public/*.html and public/majors/*.html (if exists)
- Skips public/m/*.html (mobile has its own manifest)
- Skips files that already have rel="manifest"
- Inserts right after <head> tag

Usage:
  python3 scripts/inject_pwa_manifest.py           # run
  python3 scripts/inject_pwa_manifest.py --dry-run # preview only
"""
import sys
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent / "public"
MANIFEST_LINK = '<link rel="manifest" href="/manifest.json">'
HEAD_RE = re.compile(r"<head[^>]*>", re.IGNORECASE)
MANIFEST_RE = re.compile(r'rel=["\']manifest["\']', re.IGNORECASE)


def targets():
    """Yield all PC HTML files (skip mobile /m/*.html)."""
    for html in sorted(ROOT.glob("*.html")):
        yield html
    majors_dir = ROOT / "majors"
    if majors_dir.is_dir():
        for html in sorted(majors_dir.glob("*.html")):
            yield html


def process(path: pathlib.Path, dry_run: bool) -> str:
    """Return 'inserted', 'skipped-exists', or 'skipped-no-head'."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if MANIFEST_RE.search(text):
        return "skipped-exists"
    m = HEAD_RE.search(text)
    if not m:
        return "skipped-no-head"
    insert_at = m.end()
    new_text = text[:insert_at] + "\n" + MANIFEST_LINK + text[insert_at:]
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return "inserted"


def main():
    dry_run = "--dry-run" in sys.argv
    counts = {"inserted": 0, "skipped-exists": 0, "skipped-no-head": 0}
    paths_by_status = {k: [] for k in counts}
    for p in targets():
        status = process(p, dry_run)
        counts[status] += 1
        paths_by_status[status].append(p)
    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"{prefix}PC manifest injection summary:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
        if k == "skipped-no-head" and v:
            for p in paths_by_status[k]:
                print(f"    - {p.relative_to(ROOT)}")
    print(f"Total scanned: {sum(counts.values())}")


if __name__ == "__main__":
    main()