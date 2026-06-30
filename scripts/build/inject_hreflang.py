#!/usr/bin/env python3
"""
inject_hreflang.py — Inject hreflang=zh-CN link tags based on canonical href.

For each public/*.html + public/m/*.html + public/m/majors/*.html, this script:

  1. Reads the existing <link rel="canonical" href="..."> from the page.
  2. Builds one hreflang link tag:
        <link rel="alternate" hreflang="zh-CN" href="<canonical-href>">
  3. Inserts / replaces it as a fenced block right after the canonical link.
  4. Idempotent: re-running strips the old block and rewrites it.

Derived from canonical to avoid URL drift between canonical and hreflang.
If a page lacks a canonical link, that page is skipped (it's either a template,
404 page, or PWA offline page — none of which need hreflang).

Usage:
    python3 scripts/build/inject_hreflang.py [--dry-run] [--no-backup]
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from html import escape as _esc
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC = REPO_ROOT / "public"

# Markers — HTML comments fence the injected block for idempotency.
HREFLANG_START = "<!-- BEGIN_SEO_HREFLANG -->"
HREFLANG_END = "<!-- END_SEO_HREFLANG -->"

# Match the entire canonical link tag (including trailing > or />).
# Accepts either attribute order:
#   <link rel="canonical" href="...">
#   <link rel="canonical" href="..."/>
#   <link href="..." rel="canonical">
# Captures href in group 1, full tag (with closing) in group 2.
CANONICAL_RE = re.compile(
    r'(<link\s+(?:rel="canonical"\s+href="([^"]+)"|href="([^"]+)"\s+rel="canonical")\s*/?>)',
    re.IGNORECASE,
)


def list_target_htmls() -> list[Path]:
    """Scan public PC + mobile top-level + mobile majors."""
    targets: list[Path] = []
    targets.extend(sorted(p for p in PUBLIC.glob("*.html") if not p.stem.endswith("-demo")))
    targets.extend(
        sorted(p for p in (PUBLIC / "m").glob("*.html") if p.stem not in {"_template", "sw"})
    )
    targets.extend(
        sorted(p for p in (PUBLIC / "m" / "majors").glob("*.html") if p.stem != "_template")
    )
    return targets


def build_hreflang_block(canonical_href: str) -> str:
    """Build a fenced HTML block with hreflang=zh-CN link tag."""
    tag = f'<link rel="alternate" hreflang="zh-CN" href="{_esc(canonical_href)}">'
    return f"{HREFLANG_START}\n  {tag}\n  {HREFLANG_END}"


def inject_into_html(html: str) -> str | None:
    """Strip old hreflang block, insert new one after canonical. Returns None if no canonical."""
    canonical_m = CANONICAL_RE.search(html)
    if not canonical_m:
        return None  # skip page without canonical

    canonical_href = canonical_m.group(2) or canonical_m.group(3)
    canonical_tag_full = canonical_m.group(1)  # full <link ...> including trailing >
    block = build_hreflang_block(canonical_href)

    # Strip old block (idempotent).
    strip_re = re.compile(
        r"[ \t]*\n?[ \t]*" + re.escape(HREFLANG_START) + r".*?" + re.escape(HREFLANG_END),
        re.DOTALL,
    )
    cleaned = strip_re.sub("", html)

    # Insert immediately after the full canonical tag (preserves closing > or />).
    if canonical_tag_full not in cleaned:
        return None
    return cleaned.replace(
        canonical_tag_full,
        f"{canonical_tag_full}\n  {block}",
        1,
    )


def process_file(html_path: Path, *, dry_run: bool, backup: bool) -> tuple[str, bool, int]:
    """Return (slug, injected?, byte_delta)."""
    slug = html_path.name
    html = html_path.read_text(encoding="utf-8")
    new_html = inject_into_html(html)
    if new_html is None or new_html == html:
        return slug, False, 0
    if backup and not dry_run:
        bak = html_path.with_suffix(html_path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(html_path, bak)
    if not dry_run:
        html_path.write_text(new_html, encoding="utf-8")
    return slug, True, len(new_html) - len(html)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject hreflang=zh-CN link tags.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only.")
    parser.add_argument("--no-backup", action="store_true", help="Skip .bak files.")
    args = parser.parse_args()

    targets = list_target_htmls()
    if not targets:
        print("No target HTML files found.", file=sys.stderr)
        return 1

    injected = 0
    skipped = 0
    failed = 0
    for p in targets:
        try:
            slug, did, delta = process_file(
                p, dry_run=args.dry_run, backup=not args.no_backup
            )
            if did:
                injected += 1
                if args.dry_run:
                    print(f"  {slug}: +{delta} bytes")
            else:
                skipped += 1
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  {p.name}: FAIL — {e}", file=sys.stderr)

    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(f"\n[{mode}] processed={len(targets)} injected={injected} "
          f"skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())